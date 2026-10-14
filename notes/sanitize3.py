"""Brute-force: replace every non-ASCII byte with _ in .ts files."""
from pathlib import Path

def main():
    root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
    n = 0
    for f in root.rglob("*.ts"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        new = "".join(c if ord(c) < 128 else "_" for c in text)
        if new != text:
            f.write_text(new, encoding="ascii")
            n += 1
    print(f"sanitized {n} files")

if __name__ == "__main__":
    main()
