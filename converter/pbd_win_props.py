"""Parse PBD .win entry binary to extract control coordinates/colors.

Format observations (from w_dajydr.win hexdump):
- Header: c1 00 03 00 ...
- Repeating record: [x u16][y u16][flag u8] then properties
- Long color values: 4 bytes little-endian (BGR)
- Control names: null-terminated strings appear later in the file

This is a best-effort extractor; it picks up obvious u16 coordinate pairs
and long colors, and associates them by record order with control names
found in the same entry.
"""
import sys, struct, re, json
from pathlib import Path

def parse_win_binary(data: bytes) -> dict:
    """Extract raw coordinate/color triples from a .win entry."""
    records = []
    i = 0
    # Skip header (first 16 bytes)
    i = 16
    # Walk: look for [x u16][y u16][flag] where x/y are in PBU range (100..10000)
    while i + 4 < len(data):
        x = struct.unpack_from("<H", data, i)[0]
        y = struct.unpack_from("<H", data, i+2)[0]
        flag = data[i+3]
        if 50 <= x <= 10000 and 50 <= y <= 10000 and flag in (0, 1, 0x80, 0x81):
            # Next 4 bytes may be width, height
            w = struct.unpack_from("<H", data, i+4)[0] if i+6 <= len(data) else 0
            h = struct.unpack_from("<H", data, i+6)[0] if i+8 <= len(data) else 0
            records.append({"offset": i, "x": x, "y": y, "w": w, "h": h, "flag": flag})
            i += 8
        else:
            i += 1

    # Extract null-terminated strings (control names)
    names = []
    for m in re.finditer(rb"[a-z][a-z0-9_]{2,30}\x00", data, re.I):
        names.append(m.group()[:-1].decode("ascii", errors="replace"))

    return {"records": records[:50], "names": names[:50]}


if __name__ == "__main__":
    p = Path(sys.argv[1])
    data = p.read_bytes()
    r = parse_win_binary(data)
    print(json.dumps(r, indent=2, ensure_ascii=False))
