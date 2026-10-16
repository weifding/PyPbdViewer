import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
from pcode_vm import VM
from vm2pb import vm_to_pb
from psparser import parse_function_body
from tsbuilder import build_function_body

pbd = r"D:\ynsoft\zyxt\zy_jsmk.pbd"
idx = int(sys.argv[1])
for e in parse_pbd(pbd):
    if e.name != "w_zy_jkgl.win":
        continue
    r = parse_entry(e.raw)
    fs = [f for o in r.get('objects', []) for f in o.get('funcs', [])]
    if idx >= len(fs):
        print("idx", idx, "out of", len(fs)); continue
    f = fs[idx]
    vm = VM(bytes.fromhex(f['pcode_hex']), variables=f['locals'],
            string_table=bytes.fromhex(f['str_pool_hex']))
    pb = vm_to_pb(vm.run_lines())
    ast = parse_function_body(pb)
    ts, fell = build_function_body(ast)
    pl = pb.splitlines()
    tl = ts.splitlines()
    print(f"=== func[{idx}] pseudo={len(pl)} ts={len(tl)} ===")
    for i, p in enumerate(pl):
        if "ldt_zfrq" in p or "create" in p or "new(" in p:
            print(f"P[{i}] {p}")
    for i, t in enumerate(tl):
        if "ldt_zfrq" in t or "new(" in t:
            print(f"T[{i}] {t}")
