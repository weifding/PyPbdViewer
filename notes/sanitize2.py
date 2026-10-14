"""Aggressive sanitize: any non-ASCII char in an identifier -> _."""
import re
from pathlib import Path

IDENT = re.compile(r'[A-Za-z_$][A-Za-z0-9_$]*[^\x00-\x7F][A-Za-z0-9_$\x80-\xff]*')

def sanitize_file(p: Path):
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return
    seen = {}
    def repl(m):
        s = m.group(0)
        if s not in seen:
            out = []
            for c in s:
                if ord(c) < 128 and (c.isalnum() or c in "_$"):
                    out.append(c)
                else:
                    out.append("_")
            seen[s] = "".join(out)
        return seen[s]
    new = IDENT.sub(repl, text)
    if new != text:
        p.write_text(new, encoding="utf-8")

def main():
    root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
    n = 0
    for f in root.rglob("*.ts"):
        sanitize_file(f); n += 1
    print(f"processed {n} files")

if __name__ == "__main__":
    main()
