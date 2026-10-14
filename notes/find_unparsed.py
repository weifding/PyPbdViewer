"""Find unparsed/truncated function bodies and dump sample."""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "converter"))
from psparser import parse_function_body, ParseError

# scan decompiled PBL text outputs
root = Path(r"E:\ChatGPT\PyPbdViewer\out\decompiled")
samples = []
for ps in root.rglob("*.ps.txt"):
    text = ps.read_text(encoding="utf-8", errors="replace")
    # find function blocks
    for m in re.finditer(r'(?im)^(public|private|protected|forward)\s+.*?\n.*?^\s*(?=\S|\Z)', text):
        body = m.group(0)
        if len(body) < 50: continue
        try:
            parse_function_body(body)
        except Exception as e:
            if len(samples) < 5:
                samples.append((ps.name, str(e), body[:500]))
            break
    if len(samples) >= 5: break

for name, err, body in samples:
    print(f"=== {name}: {err}")
    print(body)
    print()
