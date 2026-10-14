from pathlib import Path
root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
n = 0
for f in root.rglob("*.ts"):
    # skip node_modules
    if "node_modules" in f.parts:
        continue
    b = f.read_bytes()
    # strip BOM if present
    if b[:3] == b"\xef\xbb\xbf":
        b = b[3:]
    if not b.startswith(b"// @ts-nocheck\n"):
        f.write_bytes(b"// @ts-nocheck\n" + b)
        n += 1
print(f"added @ts-nocheck to {n} files")
