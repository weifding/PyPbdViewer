import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
from convert_pbd import _vm_transpile_func
from pcode_vm import VM
from vm2pb import vm_to_pb

pbd = r"D:\ynsoft\zyxt\zy_jsmk.pbd"
for e in parse_pbd(pbd):
    if e.name != "w_zy_jkgl.win":
        continue
    r = parse_entry(e.raw)
    funcs = [f for o in r.get('objects', []) for f in o.get('funcs', [])]
    refs = [n for o in r.get('objects', []) for n in o.get('ref_names', [])]
    print("total funcs:", len(funcs), "refs:", len(refs), "refs head:", refs[:8])
    f = funcs[33]
    vm = VM(bytes.fromhex(f['pcode_hex']), variables=f['locals'],
            string_table=bytes.fromhex(f['str_pool_hex']), ref_names=refs)
    pb = vm_to_pb(vm.run_lines())
    print("=== PSEUDO (with refs) ldt_zfrq lines ===")
    for ln in pb.splitlines():
        if 'ldt_zfrq' in ln:
            print("  ", ln)

