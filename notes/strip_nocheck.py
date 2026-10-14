from pathlib import Path
root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
n = 0
for f in root.rglob("*.ts"):
    b = f.read_bytes()
    if b[:3] == b"\xef\xbb\xbf":
        b2 = b[3:]
    else:
        b2 = b
    if b2.startswith(b"// @ts-nocheck\n"):
        f.write_bytes(b2[len(b"// @ts-nocheck\n"):])
        n += 1
print(f"stripped from {n} files")
