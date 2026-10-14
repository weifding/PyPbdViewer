from pathlib import Path
n = 0
for f in Path(r"E:\ChatGPT\PyPbdViewer\out\ts").rglob("recovered-sql.ts"):
    t = f.read_text(encoding="utf-8", errors="replace")
    t2 = t.replace("\n", " ").replace("\r", " ")
    if t != t2:
        f.write_text(t2, encoding="ascii", errors="replace")
        n += 1
print(f"fixed {n} files")
