"""Hexdump PBL first bytes."""
import sys
p = sys.argv[1]
with open(p, "rb") as f:
    data = f.read()
print(f"size={len(data)}")
# print first 512 bytes as hex + ascii
for off in range(0, min(512, len(data)), 16):
    chunk = data[off:off+16]
    hexs = " ".join(f"{b:02x}" for b in chunk)
    ascii = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"{off:08x}  {hexs:<48}  {ascii}")
