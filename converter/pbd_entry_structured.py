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

    return {
        "version": version, "flag": flag, "entry_type": entry_type,
        "variables": variables, "var_buf_size": var_size,
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path
    p = Path(sys.argv[1])
    data = p.read_bytes()
    r = parse_entry(data)
    print(f"version={r['version']:x} flag={r['flag']:x} entry_type={r['entry_type']:x}")
    print(f"variables: {len(r['variables'])}")
    for v in r["variables"][:30]:
        print(f"  {v.name:30s} type={v.type_name} val_off={v.value}")
