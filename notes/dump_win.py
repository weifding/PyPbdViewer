import sys
from pathlib import Path
p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"E:\ChatGPT\PyPbdViewer\out\decompiled\pbd__190708__dajy\entries\w_dajydr.win")
data = p.read_bytes()
print(f"size: {len(data)}")
for i in range(0, min(len(data), 512), 16):
    chunk = data[i:i+16]
    h = " ".join(f"{b:02x}" for b in chunk)
    a = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in chunk)
    print(f"  {i:06x}  {h:<48}  {a}")
