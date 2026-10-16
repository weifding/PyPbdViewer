"""Empirically check: can a PBD global-function entry be parsed into funcs(pcode)?"""
import sys, struct
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
from pcode_vm import VM
from vm2pb import vm_to_pb

pbd = r"D:\ynsoft\dajy-menzhen\bak\190708\dajy.pbd"
targets = {"gf_applog.fun", "gf_midstring.fun", "gf_begin_transaction.fun"}
found = 0
for e in parse_pbd(pbd):
    if e.name not in targets:
        continue
    found += 1
    r = parse_entry(e.raw)
    print(f"=== {e.name} entry_len={len(e.raw)}")
    print(f"  version=0x{r['version']:x} entry_type=0x{r['entry_type']:x} "
          f"total_obj={r['total_obj']} objects={len(r['objects'])} num_inherit={r['num_inherit']}")
    if r['objects']:
        for o in r['objects']:
            print(f"  object={o['name']!r} funcs={len(o['funcs'])}")
            for f in o['funcs']:
                print(f"    func pc_size={f['pc_size']} locals={f['locals']} pcode_len={len(f['pcode_hex'])//2}")
                vm = VM(bytes.fromhex(f['pcode_hex']), variables=f['locals'], string_table=bytes.fromhex(f['str_pool_hex']))
                pseudo = vm.run()
                print("    --- pseudo ---")
                print("\n".join("      " + l for l in pseudo.splitlines()[:20]))
    else:
        print("  NO objects parsed -> global function pcode NOT reachable via parse_entry")
print("found targets:", found)
