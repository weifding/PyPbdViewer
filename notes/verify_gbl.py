import sys, re
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry
import convert_pbd

pbd = r"D:\ynsoft\dajy-menzhen\bak\190708\dajy.pbd"
for e in parse_pbd(pbd):
    if e.name not in ("w_dajydr.win", "gf_applog.fun", "gf_getpara.fun"):
        continue
    r = parse_entry(e.raw)
    fs = [f for o in r.get('objects', []) for f in o.get('funcs', [])]
    print("==", e.name, "funcs:", len(fs))
    for f in fs:
        body = convert_pbd._vm_transpile_func(f.get("pcode_hex", ""), f.get("locals", []),
                                              f.get("str_pool_hex", ""), e.get("ref_names"),
                                              global_variables=f.get("global_map"))
        gbls = re.findall(r"gbl[0-9]+", body)
        if gbls:
            gm = f.get("global_map") or {}
            print("  func name:", f.get("name"), "gbl hits:", len(gbls),
                  "global_map:", dict(list(gm.items())[:6]))
            for ln in body.splitlines():
                if "gbl" in ln:
                    print("    ", ln.strip())
            break
