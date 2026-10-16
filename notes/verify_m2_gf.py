"""Run full VM->vm2pb->psparser->tsbuilder pipeline on gf_applog/gf_midstring."""
import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
from pcode_vm import VM
from vm2pb import vm_to_pb
from psparser import parse_function_body
from tsbuilder import build_function_body

pbd = r"D:\ynsoft\dajy-menzhen\bak\190708\dajy.pbd"
for e in parse_pbd(pbd):
    if e.name not in {"gf_midstring.fun"}:
        continue
    r = parse_entry(e.raw)
    for o in r['objects']:
        for f in o['funcs']:
            vm = VM(bytes.fromhex(f['pcode_hex']), variables=f['locals'], string_table=bytes.fromhex(f['str_pool_hex']))
            pseudo = vm.run()
            pb = vm_to_pb(pseudo)
            print("=== pb_text ===")
            print(pb)
            ast = parse_function_body(pb)
            ts, fell = build_function_body(ast)
            print("=== TS (fell_back=%s) ===" % fell)
            print(ts)
