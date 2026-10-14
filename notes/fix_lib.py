from pathlib import Path
root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts\node_modules\typescript\lib")
for f in root.glob("*.d.ts"):
    b = f.read_bytes()
    # strip BOM + "// @ts-nocheck\n"
    if b[:3] == b"\xef\xbb\xbf":
        b = b[3:]
    if b.startswith(b"// @ts-nocheck\n"):
        b = b[len(b"// @ts-nocheck\n"):]
        f.write_bytes(b)
        print("fixed", f.name)
