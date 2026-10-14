"""Find readable PowerScript text regions inside a PBL."""
import sys, re
p = sys.argv[1]
data = open(p, "rb").read()
# Extract printable/GBK text runs >= 12 bytes
# GBK lead byte 0x81-0xfe, trail byte 0x40-0xfe.
def is_print(b):
    return 0x20 <= b < 0x7f or b >= 0x80

runs = []
cur = bytearray()
start = 0
for i, b in enumerate(data):
    if is_print(b):
        if not cur:
            start = i
        cur.append(b)
    else:
        if len(cur) >= 24:
            runs.append((start, bytes(cur)))
        cur = bytearray()
if len(cur) >= 24:
    runs.append((start, bytes(cur)))

print(f"runs={len(runs)}")
for off, r in runs[:80]:
    try:
        s = r.decode("gbk", errors="replace")
    except Exception:
        s = repr(r)
    s = s.replace("\r", "\\r").replace("\n", "\\n")
    if len(s) > 200:
        s = s[:200] + "..."
    print(f"@{off:08x}  {s}")
