import sys, traceback
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
from pcode_vm import VM
from vm2pb import vm_to_pb

pbd = r"D:\ynsoft\dajy-menzhen\bak\190708\dajy.pbd"
targets = ("gf_begin_transaction.fun", "gf_commit_transaction.fun")
for e in parse_pbd(pbd):
    if e.name not in targets:
        continue
    try:
        r = parse_entry(e.raw)
    except Exception:
        traceback.print_exc()
        continue
    fs = [f for o in r.get('objects', []) for f in o.get('funcs', [])]
    refs = []
    for o in r.get('objects', []):
        refs += o.get('ref_names', [])
    print("==", e.name, "funcs:", len(fs))
    for f in fs:
        pcode = bytes.fromhex(f.get("pcode_hex") or "")
        vm = VM(pcode, variables=f.get("locals", []),
                string_table=bytes.fromhex(f.get("str_pool_hex") or ""),
                ref_names=refs, global_variables=f.get("global_map"))
        try:
            lines = vm.run_lines()
        except Exception as ex:
            print("  VM error:", ex)
            continue
        pseudo = vm_to_pb(lines)
        print(pseudo)
