"""Structured PBD entry parser ported from PbEntry.cs.

Entry binary layout (PB 6.0, non-Unicode):
  u16  PdbVersion
  u16  Flag
  u32  EntryType
  u32  Unknown
  u32  ModifiedTime
  u32  (extra if version >= 334)
  u32  CompliedTime
  u32  (extra if version >= 334)
  u32  Unknown
  u16  numSystemLibs
  numSystemLibs * 12 bytes
  VariableBuffer = StructBuffer (u32 size, u32 size2, data, pad)
  Variables[] = ReadVariables()
  u16  totalObjNum
  u16  numInheritRecords
  FunctionBuffer = StructBuffer
  ParamBuffer = StructBuffer
  Types table...
  objrawdata[totalObjNum] * 16 bytes
  inherit_records[numInheritRecords] * 32 bytes

Per-object ReadObject:
  u16  numFunctions
  numFunctions * 4 bytes
  per function: p-code + debug + locals
  ReadBuffer(6 * buffer[24])   // referenced funcs
  ReadBuffer(4 * buffer[22])
  ReferencedFunctions
  ReadVariables(false)  // THIS is where control properties live
  ReadBuffer(8 * buffer[28])
  ReadBuffer(buffer[26] * 16)  // all variables
  function definitions

Variable record (20 bytes):
  +0  flags (bit 0-3 = class, bit 16=64 global, bit 17=shared)
  +4  u32 array info offset into structBuffer
  +8  u32 name offset into structBuffer
  +12 u32 value offset into valueBuffer
  +16 misc (decimal precision)
  +17 u8 access flag
  +18 u16 type index

Type table records (20 bytes):
  +8  u32 name offset into type structBuffer
"""
import struct
from dataclasses import dataclass, field

@dataclass
class PbVar:
    name: str
    type_name: str
    value: str = ""
    is_instance: bool = False

def read_u16(b, off): return struct.unpack_from("<H", b, off)[0]
def read_u32(b, off): return struct.unpack_from("<I", b, off)[0]

def read_cstr(buf, off, is_unicode=False):
    """Read null-terminated string from struct buffer."""
    end = off
    if is_unicode:
        while end + 1 < len(buf) and buf[end] != 0 and buf[end+1] != 0:
            end += 2
        return buf[off:end].decode("utf-16-le", errors="replace")
    else:
        while end < len(buf) and buf[end] != 0:
            end += 1
        try:
            return buf[off:end].decode("gbk", errors="replace")
        except:
            return buf[off:end].decode("latin-1", errors="replace")


def _read_vars(data, pos, is_unicode):
    """ReadVariables: skip 6 + struct buffer + u16 count/20 + 20 each. Returns (pos, vars_list)."""
    pos += 6
    sb_size = read_u32(data, pos); pos += 4
    sb_size2 = read_u32(data, pos); pos += 4
    struct_buf = data[pos:pos+sb_size]; pos += sb_size + sb_size2
    num = read_u16(data, pos); pos += 2
    num //= 20
    out = []
    for _ in range(num):
        rec = data[pos:pos+20]; pos += 20
        name_off = read_u32(rec, 8)
        val_off = read_u32(rec, 12)
        type_idx = read_u16(rec, 18)
        out.append({
            "name": read_cstr(struct_buf, name_off, is_unicode),
            "val_off": val_off,
            "type_idx": type_idx,
            "global_index": read_u16(rec, 12),
            "struct_buf": struct_buf,
            "rec": rec,
        })
    return pos, out


def _resolve_val(v, var_buf, is_unicode):
    """Resolve a variable's value.
    - type t1 (long): val_off IS the int value (signed)
    - type t2 (color): val_off IS the BGR long
    - type t7 (boolean): val_off != 0
    - type t6 (string): val_off & 0x7FFFFFFF = offset into var_buf, null-terminated
    """
    t = v["type_idx"]
    vo = v["val_off"]
    if t == 1:
        # signed 32
        return struct.unpack("<i", struct.pack("<I", vo))[0]
    if t == 2:
        return vo  # BGR color long
    if t == 7:
        return bool(vo)
    if t == 6:
        off = vo & 0x7FFFFFFF
        if off >= len(var_buf):
            return ""
        end = off
        if is_unicode:
            while end + 1 < len(var_buf) and var_buf[end] != 0 and var_buf[end+1] != 0:
                end += 2
            return var_buf[off:end].decode("utf-16-le", errors="replace")
        else:
            while end < len(var_buf) and var_buf[end] != 0:
                end += 1
            try:
                return var_buf[off:end].decode("gbk", errors="replace")
            except:
                return var_buf[off:end].decode("latin-1", errors="replace")
    return vo


def _read_func(data, pos, is_unicode):
    """ReadFunction: u16 pc_size, u16 dbg_size, u16 flag, p-code, debug*4, locals vars, struct buffer.
    Returns (new_pos, func_dict_with_pcode_and_locals)."""
    pc_size = read_u16(data, pos); pos += 2
    dbg_size = read_u16(data, pos); pos += 2
    flag = read_u16(data, pos); pos += 2
    pcode = data[pos:pos+pc_size]; pos += pc_size
    pos += dbg_size * 4
    pos, locals_vars = _read_vars(data, pos, is_unicode)
    locals_names = [v.get("name", "") for v in locals_vars]
    # project-level global variable name table: GlobalIndex -> name.
    global_map = {}
    for v in locals_vars:
        gi = v.get("global_index", 0)
        if gi and gi != 0xFFFF and v.get("name"):
            global_map.setdefault(gi, v["name"])
    # struct buffer (function string pool)
    sb_size = read_u32(data, pos); pos += 4
    sb_size2 = read_u32(data, pos); pos += 4
    str_pool = data[pos:pos+sb_size]; pos += sb_size + sb_size2
    func = {
        "pc_size": pc_size,
        "flag": flag,
        "pcode_hex": pcode.hex(),
        "locals": locals_names,
        "global_map": global_map,
        "str_pool_hex": str_pool.hex(),
    }
    return pos, func


def _read_object(data, pos, inh, is_unicode, type_names, var_buf, func_buf):
    """ReadObject per control. Returns (pos, props_list, funcs, ref_names).
    funcs entries gain a `name` (event/function name) from FunctionDefinitions.
    """
    num_funcs = read_u16(data, pos); pos += 2
    func_idx = []
    for _ in range(num_funcs):
        func_idx.append(data[pos:pos+4]); pos += 4
    funcs = []
    for idx in func_idx:
        pos, fd = _read_func(data, pos, is_unicode)
        funcs.append(fd)

    # ReadBuffer(6 * buffer[24]), ReadBuffer(4 * buffer[22])
    pos += 6 * read_u16(inh, 24)
    pos += 4 * read_u16(inh, 22)

    # ReadReferencedFunctions — this is the call_gf[N] name table.
    pos, ref_vars = _read_vars(data, pos, is_unicode)
    ref_names = [v.get("name", "") for v in ref_vars]

    # **Control properties** = ReadVariables(false)
    pos, props = _read_vars(data, pos, is_unicode)

    pos += 8 * read_u16(inh, 28)
    pos += 16 * read_u16(inh, 26)

    # FunctionDefinitions: 48-byte recs (version>146); rec[0..4] = name offset
    # relative to the FunctionBuffer. These are the real event/function names
    # (open, close, ue_xxx, ...), in the same order as `funcs`.
    num_fndefs = read_u16(inh, 4)
    fndef_names = []
    for _ in range(num_fndefs):
        rec = data[pos:pos+48]; pos += 48
        nm_off = read_u32(rec, 0)
        nm = read_cstr(func_buf, nm_off, is_unicode)
        if nm.startswith("+"):
            nm = nm[1:]
        fndef_names.append(nm)
    for i, f in enumerate(funcs):
        f["name"] = fndef_names[i] if i < len(fndef_names) else None

    # resolve values
    for p in props:
        p["value"] = _resolve_val(p, var_buf, is_unicode)
    return pos, props, funcs, ref_names


def parse_entry(data: bytes, is_unicode: bool = False):
    """Parse a PBD entry, return (version, variables, objects)."""
    pos = 0
    version = read_u16(data, pos); pos += 2
    flag = read_u16(data, pos); pos += 2
    entry_type = read_u32(data, pos); pos += 4
    unknown = read_u32(data, pos); pos += 4
    mod_time = read_u32(data, pos); pos += 4
    if version >= 334: pos += 4
    comp_time = read_u32(data, pos); pos += 4
    if version >= 334: pos += 4
    unknown2 = read_u32(data, pos); pos += 4
    num_sys = read_u16(data, pos); pos += 2
    pos += num_sys * 12

    # VariableBuffer (StructBuffer)
    var_size = read_u32(data, pos); pos += 4
    var_size2 = read_u32(data, pos); pos += 4
    var_buf = data[pos:pos+var_size]; pos += var_size + var_size2

    # ReadVariables
    pos += 6  # header
    sb_size = read_u32(data, pos); pos += 4
    sb_size2 = read_u32(data, pos); pos += 4
    struct_buf = data[pos:pos+sb_size]; pos += sb_size + sb_size2
    num_vars = read_u16(data, pos); pos += 2
    num_vars //= 20
    variables = []
    for i in range(num_vars):
        rec = data[pos:pos+20]; pos += 20
        name_off = read_u32(rec, 8)
        val_off = read_u32(rec, 12)
        type_idx = read_u16(rec, 18)
        name = read_cstr(struct_buf, name_off, is_unicode)
        variables.append(PbVar(name=name, type_name=f"t{type_idx}", value=str(val_off)))

    # totalObjNum + numInheritRecords
    total_obj = read_u16(data, pos); pos += 2
    num_inherit = read_u16(data, pos); pos += 2

    # FunctionBuffer / ParamBuffer (StructBuffer each)
    fb_size = read_u32(data, pos); pos += 4
    fb_size2 = read_u32(data, pos); pos += 4
    func_buf = data[pos:pos+fb_size]; pos += fb_size + fb_size2

    pb_size = read_u32(data, pos); pos += 4
    pb_size2 = read_u32(data, pos); pos += 4
    param_buf = data[pos:pos+pb_size]; pos += pb_size + pb_size2

    # Types: ReadBuffer(6) + StructBuffer + u16 count/20 + 20 each
    pos += 6
    ts_size = read_u32(data, pos); pos += 4
    ts_size2 = read_u32(data, pos); pos += 4
    type_struct_buf = data[pos:pos+ts_size]; pos += ts_size + ts_size2
    num_types = read_u16(data, pos); pos += 2
    num_types //= 20
    type_names = {}
    for i in range(num_types):
        rec = data[pos:pos+20]; pos += 20
        name_off = read_u32(rec, 8)
        type_names[i] = read_cstr(type_struct_buf, name_off, is_unicode)

    # Enums (ReadVariables(false))
    pos += 6
    es_size = read_u32(data, pos); pos += 4
    es_size2 = read_u32(data, pos); pos += 4
    enum_struct = data[pos:pos+es_size]; pos += es_size + es_size2
    num_enums = read_u16(data, pos); pos += 2
    num_enums //= 20
    for i in range(num_enums):
        pos += 20

    # objrawdata: totalObjNum * 16 bytes
    objraw = []
    for i in range(total_obj):
        objraw.append(data[pos:pos+16]); pos += 16

    # inherit records: numInheritRecords * 32 bytes
    inherit_recs = []
    for i in range(num_inherit):
        inherit_recs.append(data[pos:pos+32]); pos += 32

    # Per-object ReadObject
    objects = []
    inh_idx = 0
    cur_pos = pos
    for i in range(total_obj):
        raw = objraw[i]
        type_idx = read_u16(raw, 2)
        flags0 = raw[0]
        sub = flags0 >> 1 & 7
        if sub != 0:
            continue
        inh = inherit_recs[inh_idx] if inh_idx < len(inherit_recs) else None
        inh_idx += 1
        if inh is None:
            continue
        inh_type_idx = read_u16(inh, 0)
        parent_type_idx = read_u16(inh, 2)
        def _tn(t):
            return type_names.get(t & 0x7FFF, type_names.get(t, f"t{t}"))
        obj_name = _tn(type_idx)
        try:
            cur_pos, props, funcs, ref_names = _read_object(data, cur_pos, inh, is_unicode, type_names, var_buf, func_buf)
        except Exception as e:
            props, funcs, ref_names = [], [], []
        objects.append({
            "name": obj_name,
            "type_idx": type_idx,
            "inh_type": _tn(inh_type_idx),
            "parent_type": _tn(parent_type_idx),
            "props": props,
            "funcs": funcs,
            "ref_names": ref_names,
        })

    return {
        "version": version, "flag": flag, "entry_type": entry_type,
        "variables": variables, "var_buf_size": var_size,
        "total_obj": total_obj, "num_inherit": num_inherit,
        "type_names": type_names,
        "objects": objects,
        "pos": cur_pos, "data_len": len(data),
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path
    p = Path(sys.argv[1])
    data = p.read_bytes()
    r = parse_entry(data)
    print(f"version={r['version']:x} flag={r['flag']:x} entry_type={r['entry_type']:x}")
    print(f"variables: {len(r['variables'])}, objects: {r['total_obj']}, inherit_recs: {r['num_inherit']}")
    print(f"pos after parse: {r['pos']} / {r['data_len']}")
    print(f"\nTypes ({len(r['type_names'])}):")
    for k, v in list(r['type_names'].items())[:20]:
        print(f"  [{k}] {v}")
    print(f"\nObjects ({len(r['objects'])}):")
    for o in r['objects']:
        print(f"  {o['name']:25s} inh={o['inh_type']:18s} props={len(o['props'])}")
        for p in o['props']:
            v = p.get("value", p['val_off'])
            print(f"      {p['name']:25s} = {v!r}")
