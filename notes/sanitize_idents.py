"""Sanitize non-ASCII identifiers in all generated .ts files.

For each .ts file, find identifiers containing non-ASCII chars (Chinese etc),
assign them a stable ascii alias zh_<md58>, and replace all occurrences.
"""
import re, hashlib
from pathlib import Path

IDENT = re.compile(r'[A-Za-z_$][A-Za-z0-9_$一-鿿]*[一-鿿][A-Za-z0-9_一-鿿]*')

def sanitize_file(p: Path) -> int:
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        return 0
    # skip strings/comments? Simple approach: replace only when identifier-like
    seen = {}
    def repl(m):
        s = m.group(0)
        if all(ord(c) < 128 for c in s):
            return s
        if s not in seen:
            h = hashlib.md5(s.encode("utf-8")).hexdigest()[:8]
            seen[s] = f"zh_{h}"
        return seen[s]
    new = IDENT.sub(repl, text)
    if new != text:
        p.write_text(new, encoding="utf-8")
    return len(seen)

def main():
    root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
    total = 0; files = 0
    for f in root.rglob("*.ts"):
        n = sanitize_file(f)
        if n:
            files += 1
            total += n
    print(f"sanitized {files} files, renamed {total} identifiers")

if __name__ == "__main__":
    main()
