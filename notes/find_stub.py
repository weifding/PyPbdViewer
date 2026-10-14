"""Find functions that still produce TODO stubs in TS output."""
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
    # find TODO stubs with actual PB body comments
    for m in re.finditer(r"public\s+(\w+)\([^)]*\)\s*:\s*\w+\s*\{\s*\n\s*// TODO: PB body[^\n]*\n((?:\s*//[^\n]*\n)+)", t):
        body = m.group(2)
        # only keep bodies with real code (not just super::)
        if "super::" in body and len(body) < 200:
            continue
        samples.append((f.name, m.group(1), body[:600]))
        if len(samples) >= 5:
            break
    if len(samples) >= 5:
        break

for name, fn, body in samples:
    print(f"=== {name}::{fn} ===")
    print(body)
    print()
