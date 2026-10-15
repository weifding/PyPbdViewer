"""Find a PBL function that fails M2 and print the exception."""
import sys, re
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pathlib import Path
from psparser import parse_function_body
from tsbuilder import build_function_body

# find a TODO stub file
ts_root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
for f in ts_root.rglob("*.ts"):
    if "node_modules" in f.parts:
        continue
    # skip pbd__ paths
    if any("pbd__" in p for p in f.parts):
        continue
    try:
        t = f.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    if "TODO: PB body" not in t:
        continue
    # extract first function body comment
    m = re.search(r"public\s+\w+\([^)]*\)\s*:\s*\w+\s*\{\s*\n\s*// TODO[^\n]*\n((?:\s*//[^\n]*\n){5,30})", t)
    if not m:
        continue
    body_comment = m.group(1)
    # uncomment
    body = re.sub(r"^\s*// ?", "", body_comment, flags=re.M)
    print(f"=== {f.name} ===")
    print(body[:500])
    try:
        ast = parse_function_body(body)
        ts, fb = build_function_body(ast)
        print("fell_back:", fb, "ts_len:", len(ts))
    except Exception as e:
        import traceback; traceback.print_exc()
    break
