import sys, io, contextlib
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from pathlib import Path
from extract_pbl import extract_from_pbl

pbl = r"D:\ynsoft\ljp\源程序\tjxt\lablib9.pbl"
out = Path(r"E:\ChatGPT\PyPbdViewer\out\diag_pbl")
idx = extract_from_pbl(Path(pbl), out)
print("objects:", len(idx["objects"]), "blocks:", len(idx["blocks"]))
from collections import Counter
kinds = Counter(b["kind"] for b in idx["blocks"])
print("kinds:", dict(kinds))

# Take a few function/subroutine bodies and run psparser+tsbuilder.
from psparser import parse_function_body, Fallback, ParseError
from tsbuilder import build_function_body

stat = {"total": 0, "fell_back": 0, "ok": 0}
errs = Counter()
samples = []
for b in idx["blocks"]:
    if b["kind"] not in ("function", "subroutine", "event"):
        continue
    stat["total"] += 1
    body = b["text"].split("\n")[1:]
    if not body:
        stat["fell_back"] += 1
        continue
    try:
        ast = parse_function_body(body)
        ts, fell = build_function_body(ast)
    except Exception as e:
        stat["fell_back"] += 1
        errs[type(e).__name__] += 1
        continue
    if fell or not ts.strip():
        stat["fell_back"] += 1
        # classify why
        fb = [s for s in ast if isinstance(s, Fallback)]
        if fb:
            errs[f"Fallback:{fb[0].text[:30]}"] += 1
        else:
            errs["fell_back(no Fallback)"] += 1
    else:
        stat["ok"] += 1
        if len(samples) < 2:
            samples.append((b["name"], b["kind"], ts[:400]))
print("stat:", stat)
print("err breakdown:", dict(errs.most_common(12)))
for name, kind, ts in samples:
    print(f"\n=== {name} ({kind}) ===")
    print(ts)
