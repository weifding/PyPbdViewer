"""Probe: where do global-function indexes (gf[N]/call_gf[N]) map to names?
Dump parse_entry internals incl. ReferencedFunctions region + inherited func names."""
import sys, struct
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import (read_u16, read_u32, read_cstr,
                                  _read_vars, _read_object)

pbd = r"D:\ynsoft\dajy-menzhen\bak\190708\dajy.pbd"

def probe(e):
    data = e.raw
    pos = 0
    version = read_u16(data, pos); pos += 2
    flag = read_u16(data, pos); pos += 2
    entry_type = read_u32(data, pos); pos += 4
    pos += 4  # unknown
    mod_time = read_u32(data, pos); pos += 4
    if version >= 334: pos += 4
    comp_time = read_u32(data, pos); pos += 4
    if version >= 334: pos += 4
    pos += 4  # unknown2
    num_sys = read_u16(data, pos); pos += 2
    pos += num_sys * 12
    var_size = read_u32(data, pos); pos += 4
    var_size2 = read_u32(data, pos); pos += 4
    var_buf = data[pos:pos+var_size]; pos += var_size + var_size2
    pos += 6
    sb = read_u32(data, pos); pos += 4
    sb2 = read_u32(data, pos); pos += 4
    struct_buf = data[pos:pos+sb]; pos += sb + sb2
    num_vars = read_u16(data, pos); pos += 2; num_vars //= 20
    pos += num_vars*20
    total_obj = read_u16(data, pos); pos += 2
    num_inherit = read_u16(data, pos); pos += 2
    fb = read_u32(data, pos); pos += 4; fb2 = read_u32(data, pos); pos += 4
    func_buf = data[pos:pos+fb]; pos += fb + fb2
    pb = read_u32(data, pos); pos += 4; pb2 = read_u32(data, pos); pos += 4
    param_buf = data[pos:pos+pb]; pos += pb + pb2
    pos += 6
    ts = read_u32(data, pos); pos += 4; ts2 = read_u32(data, pos); pos += 4
    type_struct = data[pos:pos+ts]; pos += ts + ts2
    num_types = read_u16(data, pos); pos += 2; num_types //= 20
    type_names = {}
    for i in range(num_types):
        rec = data[pos:pos+20]; pos += 20
        type_names[i] = read_cstr(type_struct, read_u32(rec, 8))
    pos += 6
    es = read_u32(data, pos); pos += 4; es2 = read_u32(data, pos); pos += 4
    enum_struct = data[pos:pos+es]; pos += es + es2
    num_enums = read_u16(data, pos); pos += 2; num_enums //= 20
    pos += num_enums*20
    objraw = [data[pos+i*16:pos+i*16+16] for i in range(total_obj)]; pos += total_obj*16
    inherit_recs = [data[pos+i*32:pos+i*32+32] for i in range(num_inherit)]; pos += num_inherit*32

    print(f"=== {e.name} entry_type=0x{entry_type:x} total_obj={total_obj} num_inherit={num_inherit}")
    print(f"type_names({num_types}):")
    for k, v in list(type_names.items())[:40]:
        print(f"   [{k}] {v!r}")
    print(f"variables at entry-level: {num_vars} (skipped, no names parsed here)")

    # per object: dump inherited + ReferencedFunctions region
    inh_idx = 0
    for i in range(total_obj):
        raw = objraw[i]
        type_idx = read_u16(raw, 2)
        sub = raw[0] >> 1 & 7
        if sub != 0: continue
        inh = inherit_recs[inh_idx]; inh_idx += 1
        # dump inherit_rec 32 bytes
        h = inh.hex(' ')
        nf = read_u16(inh, 4)
        # named fields from _read_object
        print(f"  obj{i} type_idx={type_idx} inh_raw={h} num_fndefs(inh4)={nf} "
              f"u16@22={read_u16(inh,22)} u16@24={read_u16(inh,24)} u16@26={read_u16(inh,26)} u16@28={read_u16(inh,28)}")
        # walk read_object to reach ReferencedFunctions then dump it
        try:
            p2 = pos  # this is wrong for later objs; only valid for i==0 multi-func
            num_funcs = read_u16(data, p2); p2 += 2
            p2 += num_funcs*4
            for _ in range(num_funcs):
                pc = read_u16(data, p2); p2 += 2
                dbg = read_u16(data, p2); p2 += 2
                fl = read_u16(data, p2); p2 += 2
                p2 += pc + dbg*4
                p2 += 6
                lsb = read_u32(data, p2); p2 += 4; lsb2 = read_u32(data, p2); p2 += 4
                p2 += lsb + lsb2
                ls = read_u32(data, p2); p2 += 4; ls2 = read_u32(data, p2); p2 += 4
                p2 += ls + ls2
            # ReferencedFunctions (ReadVariables(false)) after skip buffers
            p2 += 6*read_u16(inh, 24)
            p2 += 4*read_u16(inh, 22)
            # it's a ReadVariables block
            p2 += 6
            rb = read_u32(data, p2); p2 += 4; rb2 = read_u32(data, p2); p2 += 4
            ref_struct = data[p2:p2+rb]; p2 += rb + rb2
            nref = read_u16(data, p2); p2 += 2; nref //= 20
            print(f"  ReferencedFunctions count={nref}")
            for k in range(nref):
                rec = data[p2+k*20:p2+k*20+20]; 
                nm = read_cstr(ref_struct, read_u32(rec, 8))
                print(f"     ref[{k}] name={nm!r} type_idx={read_u16(rec,18)}")
        except Exception as ex:
            print(f"  ref walk error: {ex}")
        # only dump first object to keep output small
        if i >= 0: pass

for e in parse_pbd(pbd):
    if e.name in {"gf_applog.fun"}:
        probe(e)
