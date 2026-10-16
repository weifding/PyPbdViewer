"""Verify ref_names maps call_gf[N] to real names."""
import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
from pcode_vm import VM

pbd = r"D:\ynsoft\dajy-menzhen\bak\190708\dajy.pbd"
for e in parse_pbd(pbd):
    if e.name not in {"gf_applog.fun", "gf_midstring.fun", "gf_begin_transaction.fun"}:
        continue
    r = parse_entry(e.raw)
    for o in r['objects']:
        ref = o.get('ref_names', [])
        print(f"=== {e.name}: ref_names({len(ref)}) ===")
        for i, n in enumerate(ref):
            print(f"   [{i}] {n!r}")
        for f in o['funcs']:
            vm = VM(bytes.fromhex(f['pcode_hex']), variables=f['locals'], string_table=bytes.fromhex(f['str_pool_hex']))
            vm.ref_names = ref
            pseudo = vm.run()
            print("   pseudo:")
            print("\n".join("      " + l for l in pseudo.splitlines()))
