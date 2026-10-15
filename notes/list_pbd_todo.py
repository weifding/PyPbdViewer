"""List PBD TODO stub examples."""
from pathlib import Path
import re

ts_root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
samples = []
for f in ts_root.rglob("*.ts"):
    if "node_modules" in f.parts:
        continue
    if not any("pbd__" in p for p in f.parts):
        continue
    try:
        t = f.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    if "TODO" not in t and "body stripped" not in t:
        continue
    samples.append((f.name, f.parent.name, t[:400]))
    if len(samples) >= 5:
        break

for name, parent, body in samples:
    print(f"=== {parent}/{name} ===")
    print(body)
    print()
