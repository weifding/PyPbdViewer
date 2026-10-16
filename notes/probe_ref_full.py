"""Precisely dump ReferencedFunctions for gf_applog using C#-aligned offsets."""
import sys, struct
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import (read_u16, read_u32, read_cstr, _read_vars)

pbd = r"D:\ynsoft\dajy-menzhen\bak\190708\dajy.pbd"

def refs(e):
    data = e.raw
    pos = 0
    version = read_u16(data, pos); pos += 2
    flag = read_u16(data, pos); pos += 2
    entry_type = read_u32(data, pos); pos += 4
    pos += 4
    mod = read_u32(data, pos); pos += 4
    if version >= 334: pos += 4
    comp = read_u32(data, pos); pos += 4
    if version >= 334: pos += 4
    pos += 4
    nsys = read_u16(data, pos); pos += 2; pos += nsys*12
    vs = read_u32(data, pos); pos += 4; vs2 = read_u32(data, pos); pos += 4
    var_buf = data[pos:pos+vs]; pos += vs+vs2
    pos += 6
    sb = read_u32(data, pos); pos += 4; sb2 = read_u32(data, pos); pos += 4
    struct_buf = data[pos:pos+sb]; pos += sb+sb2
    nvars = read_u16(data, pos); pos += 2; nvars//=20; pos += nvars*20
    total_obj = read_u16(data, pos); pos += 2
    num_inherit = read_u16(data, pos); pos += 2
    fb = read_u32(data, pos); pos += 4; fb2 = read_u32(data, pos); pos += 4; pos += fb+fb2
    pb = read_u32(data, pos); pos += 4; pb2 = read_u32(data, pos); pos += 4; pos += pb+pb2
    pos += 6
    ts = read_u32(data, pos); pos += 4; ts2 = read_u32(data, pos); pos += 4
    type_struct = data[pos:pos+ts]; pos += ts+ts2
    ntypes = read_u16(data, pos); pos += 2; ntypes//=20; pos += ntypes*20
    pos += 6
    es = read_u32(data, pos); pos += 4; es2 = read_u32(data, pos); pos += 4
    enum_struct = data[pos:pos+es]; pos += es+es2
    nenums = read_u16(data, pos); pos += 2; nenums//=20; pos += nenums*20
    objraw = [data[pos+i*16:pos+i*16+16] for i in range(total_obj)]; pos += total_obj*16
    inherit_recs = [data[pos+i*32:pos+i*32+32] for i in range(num_inherit)]; pos += num_inherit*32
    print(f"{e.name}: entry_type=0x{entry_type:x} total_obj={total_obj}")
    # read object[0]: funcs
    p2 = pos
    nfunc = read_u16(data, p2); p2 += 2
    p2 += nfunc*4
    for _ in range(nfunc):
        pc = read_u16(data, p2); p2 += 2
        dbg = read_u16(data, p2); p2 += 2
        fl = read_u16(data, p2); p2 += 2
        p2 += pc + dbg*4
        # locals vars
        p2 += 6
        ls = read_u32(data, p2); p2 += 4; ls2 = read_u32(data, p2); p2 += 4
        lsb = data[p2:p2+ls]; p2 += ls+ls2
        nloc = read_u16(data, p2); p2 += 2; nloc//=20; p2 += nloc*20
        # str_pool
        ss = read_u32(data, p2); p2 += 4; ss2 = read_u32(data, p2); p2 += 4
        p2 += ss+ss2
    inh = inherit_recs[0]
    print(f"  inh: n24={read_u16(inh,24)} n22={read_u16(inh,22)} n28={read_u16(inh,28)} n26={read_u16(inh,26)} n4={read_u16(inh,4)}")
    p2 += 6*read_u16(inh,24)
    p2 += 4*read_u16(inh,22)
    # ReferencedFunctions
    p2 += 6
    rbs = read_u32(data, p2); p2 += 4; rbs2 = read_u32(data, p2); p2 += 4
    ref_struct = data[p2:p2+rbs]; p2 += rbs+rbs2
    nref = read_u16(data, p2); p2 += 2; nref//=20
    print(f"  ReferencedFunctions count={nref} (struct_size={rbs})")
    for k in range(nref):
        rec = data[p2+k*20:p2+k*20+20]
        nm_off = read_u32(rec, 8)
        gidx = read_u16(rec, 12)
        isgf = rec[16] == 2
        nm = read_cstr(ref_struct, nm_off)
        print(f"     [{k}] name={nm!r} nameoff={nm_off} globalidx={gidx} isgf={isgf} rec={rec.hex(' ')}")
    # Control properties
    p2 += nref*20
    p2 += 6
    cs = read_u32(data, p2); p2 += 4; cs2 = read_u32(data, p2); p2 += 4
    c_struct = data[p2:p2+cs]; p2 += cs+cs2
    nctrl = read_u16(data, p2); p2 += 2; nctrl//=20
    print(f"  ControlProperties count={nctrl}")
    for k in range(min(nctrl, 30)):
        rec = data[p2+k*20:p2+k*20+20]
        print(f"     [{k}] name={read_cstr(c_struct, read_u32(rec,8))!r}")

for e in parse_pbd(pbd):
    if e.name in {"gf_applog.fun"}:
        refs(e)
