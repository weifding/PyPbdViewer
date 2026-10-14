import json
data = json.load(open(r"E:\ChatGPT\PyPbdViewer\out\stats.json", encoding="utf-8"))
pbl = [d for d in data if d.get("kind") == "pbl"]
pbd = [d for d in data if d.get("kind") == "pbd"]
print(f"PBL: {len(pbl)}")
print(f"PBD: {len(pbd)}")
print()
# PBL agg
objs = sum(d.get("objects",0) for d in pbl)
fns = sum(d.get("functions",0) for d in pbl)
evts = sum(d.get("events",0) for d in pbl)
unparsed = sum(d.get("unparsed",0) for d in pbl)
trunc = sum(d.get("truncated",0) for d in pbl)
ext = sum(d.get("external",0) for d in pbl)
print(f"PBL objects total: {objs}")
print(f"PBL functions: {fns}, events: {evts}")
print(f"PBL unparsed bodies (M2 fallback): {unparsed}")
print(f"PBL truncated bodies: {trunc}")
print(f"PBL external funcs: {ext}")
print()
# PBD agg
raw = sum(d.get("raw_entries",0) for d in pbd)
src = sum(d.get("source_entries",0) for d in pbd)
ents = sum(d.get("entries",0) for d in pbd)
sql = sum(d.get("sql",0) for d in pbd)
print(f"PBD raw_entries: {raw}, source_entries: {src}, parsed_entries: {ents}")
print(f"PBD SQL strings extracted: {sql}")
print()
# Status
errs = [d for d in data if d.get("status") != "ok"]
print(f"non-ok status: {len(errs)}")
for e in errs[:5]: print(" ", e.get("file"), e.get("status"))
