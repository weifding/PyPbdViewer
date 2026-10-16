"""Find which VM instruction produces `new()` in a window event."""
import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
from pcode_vm import VM
from vm2pb import vm_to_pb

pbd = r"D:\ynsoft\zyxt\zy_jsmk.pbd"
for e in parse_pbd(pbd):
    if e.name != "w_zy_jkgl.fun":
        continue
    r = parse_entry(e.raw)
    for o in r.get('objects', []):
        for f in o.get('funcs', []):
            vm = VM(bytes.fromhex(f['pcode_hex']), variables=f['locals'],
                    string_table=bytes.fromhex(f['str_pool_hex']),
                    ref_names=o.get('ref_names', []))
            pb = vm_to_pb(vm.run_lines())
            for ln in pb.splitlines():
                if 'create' in ln.lower() or 'new(' in ln or '= ;' in ln:
                    print("RAW:", ln)
