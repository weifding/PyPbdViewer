import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pbd_structured import parse_pbd
from pbd_entry_structured import parse_entry

pbd = r"D:\ynsoft\zyxt\zy_jsmk.pbd"
found = 0
for e in parse_pbd(pbd):
    if e.name != "w_zy_jkgl.win":
        continue
    found += 1
    r = parse_entry(e.raw)
    fs = [f for o in r.get('objects', []) for f in o.get('funcs', [])]
    print("funcs:", len(fs))
    for i, f in enumerate(fs[:15]):
        print(i, repr(f.get('name')), "pc", f.get('pc_size'))
print("found:", found)
