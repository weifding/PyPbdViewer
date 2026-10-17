import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
from pcode_vm import VM
from vm2pb import vm_to_pb
from psparser import parse_function_body, UnaryOp
from goto_struct import structurize


def _fmt(n):
    if isinstance(n, UnaryOp) and n.op == 'not':
        return f"not({_fmt(n.operand)})"
    return repr(n)

pbd = r"D:\ynsoft\dajy-menzhen\bak\190708\dajy.pbd"
for e in parse_pbd(pbd):
    if e.name not in ("gf_begin_transaction.fun", "gf_commit_transaction.fun"):
        continue
    r = parse_entry(e.raw)
    refs = [o.get('ref_names', []) for o in r.get('objects', [])]
    refs = [x for sub in refs for x in sub]
    for f in [ff for o in r['objects'] for ff in o.get('funcs', [])]:
        vm = VM(bytes.fromhex(f.get("pcode_hex") or ""), variables=f.get("locals", []),
                string_table=bytes.fromhex(f.get("str_pool_hex") or ""),
                ref_names=refs, global_variables=f.get("global_map"))
        ast = parse_function_body(vm_to_pb(vm.run_lines()))
        print("== raw ast", e.name)
        for n in ast:
            if hasattr(n, 'then'):
                print("   If cond=", _fmt(n.cond), "then:", [type(x).__name__ for x in n.then],
                      "elseifs:", len(n.elseifs), "else_:", [type(x).__name__ for x in n.else_])
            else:
                print("   ", type(n).__name__, repr(n)[:70])
        break
