import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
from pcode_vm import VM
from vm2pb import vm_to_pb

pbd = r"D:\ynsoft\zyxt\zy_jsmk.pbd"
idx = int(sys.argv[1])
for e in parse_pbd(pbd):
    if e.name != "w_zy_jkgl.fun":
        continue
    r = parse_entry(e.raw)
    fs = []
    for o in r.get('objects', []):
        fs.extend(o.get('funcs', []))
    if idx < len(fs):
        f = fs[idx]
        vm = VM(bytes.fromhex(f['pcode_hex']), variables=f['locals'],
                string_table=bytes.fromhex(f['str_pool_hex']),
                ref_names=o.get('ref_names', []))
        print(f"=== funcs[{idx}] pc_size={f['pc_size']} locals={f['locals']} ===")
        print(vm_to_pb(vm.run_lines()))
