"""Inspect DAT* binary segments in a PBL."""
import sys, re
from pathlib import Path

pbl = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"D:\ynsoft\tjxt\his_cx_object9.pbl")
data = pbl.read_bytes()
print(f"size: {len(data)}")

# Find all DAT* markers
for m in re.finditer(rb"DAT\*", data):
    off = m.start()
    # Show 64 bytes before and 128 bytes after
    start = max(0, off - 16)
    end = min(len(data), off + 128)
    chunk = data[start:end]
    print(f"\n--- DAT* at offset {off} (0x{off:x}) ---")
    # Hex dump
    for i in range(0, len(chunk), 16):
        hex_part = " ".join(f"{b:02x}" for b in chunk[i:i+16])
        ascii_part = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in chunk[i:i+16])
        print(f"  {start+i:08x}  {hex_part:<48}  {ascii_part}")
    if off > 0x10000:
        break
