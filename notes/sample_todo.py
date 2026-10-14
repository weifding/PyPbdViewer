"""Sample TODO stubs and their PB bodies."""
from pathlib import Path
import re

ts_root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
samples = []
for f in ts_root.rglob("*.ts"):
    if "node_modules" in f.parts:
        continue
    try:
        t = f.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    if "TODO: PB body" not in t:
        continue
    # extract the function body comment
    m = re.search(r"public\s+(\w+)\([^)]*\)\s*:\s*\w+\s*\{\s*\n\s*// TODO: PB body[^\n]*\n((?:\s*//[^\n]*\n){3,40})", t)
    if m:
        body = m.group(2)
        # skip trivial
        if "super::" in body and len(body) < 300:
            continue
        samples.append((f.name, m.group(1), body))
        if len(samples) >= 5:
            break

for name, fn, body in samples:
    print(f"=== {name}::{fn} ===")
    print(body[:800])
    print()
