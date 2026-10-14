"""
Structured PBD/PBL reader, ported from PbdViewer/Uitils/PbClass/PbFile.cs (C#).

Instead of regex-scanning text runs, this walks the real binary layout:
  1. Find HDR*PowerBuilder magic; detect version (0500 / 0600 / Unicode).
  2. Walk the NOD* linked list.
  3. Each NOD* has ushort entry-count at offset 20.
  4. Each entry is ENT* + version + 16 bytes + name-length-prefixed name.
  5. Entry payload is a DAT* chunk linked list.

Output: list of entries {name, raw_bytes}. Callers decide how to render
each entry as source text.
"""
from __future__ import annotations
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class PbEntry:
    name: str           # e.g. "w_nb_dzwj.win"
    offset: int         # NOD* offset
    raw: bytes = field(repr=False)


def _get_u16(b: bytes, off: int) -> int:
    return struct.unpack_from("<H", b, off)[0]


def _get_u32(b: bytes, off: int) -> int:
    return struct.unpack_from("<I", b, off)[0]


def _read_data(f, start: int, size: int) -> bytes:
    """DAT* chunk linked list reader."""
    out = bytearray()
    offset = start
    remaining = size
    while remaining > 0:
        f.seek(offset)
        hdr = f.read(10)
        if len(hdr) < 10 or hdr[:4] != b"DAT*":
            break
        chunk_size = _get_u16(hdr, 8)
        n = min(chunk_size, remaining)
        out += f.read(n)
        remaining -= n
        offset = _get_u32(hdr, 4)
    return bytes(out)


def _get_node_list(data: bytes) -> tuple[list[int], bool, bool]:
    """Return (nod_offsets, is_pb5, is_unicode)."""
    is_pb5 = False
    is_unicode = False
    nod_offsets: list[int] = []

    i = 0
    n = len(data)
    while i + 32 < n:
        if data[i:i+4] == b"HDR*":
            if data[i+4:i+16] == b"PowerBuilder":
                ver = data[i+18:i+22]
                if ver == b"0500":
                    is_pb5 = True
                    break
                if ver == b"0600":
                    break
            # Unicode variant: "PowerBuilder" as UTF-16LE starting at i+4.
            try:
                if data[i+4:i+28].decode("utf-16-le", errors="replace") == "PowerBuilder":
                    if data[i+32:i+40].decode("utf-16-le", errors="replace") == "0600":
                        is_unicode = True
                        break
            except Exception:
                pass
        i += 512  # scan in 512-byte strides (matches C# logic)

    # Walk NOD* linked list.
    stride = 1536 if is_unicode else 1024
    pos = i + stride
    if pos + 512 > n or data[pos:pos+4] != b"NOD*":
        return nod_offsets, is_pb5, is_unicode

    nod_offsets.append(pos)
    next1 = _get_u32(data, pos + 4)
    next2 = _get_u32(data, pos + 12)

    while next1 and next1 + 512 <= n and data[next1:next1+4] == b"NOD*":
        nod_offsets.append(next1)
        next1 = _get_u32(data, next1 + 4)

    while next2 and next2 + 512 <= n and data[next2:next2+4] == b"NOD*":
        nod_offsets.append(next2)
        next2 = _get_u32(data, next2 + 12)

    return nod_offsets, is_pb5, is_unicode


def _decode_str(b: bytes, is_unicode: bool) -> str:
    if is_unicode:
        return b.decode("utf-16-le", errors="replace").rstrip("\x00")
    # GBK first (legacy PB), fall back to UTF-8.
    try:
        return b.decode("gbk", errors="replace").rstrip("\x00")
    except Exception:
        return b.decode("utf-8", errors="replace").rstrip("\x00")


def parse_pbd(path: str | Path) -> Iterator[PbEntry]:
    """Yield PbEntry objects from a PBD/PBL file."""
    path = Path(path)
    data = path.read_bytes()
    n = len(data)
    nod_list, _is_pb5, is_unicode = _get_node_list(data)

    n_unit = 2 if is_unicode else 1
    entry_hdr_size = 4 + n_unit * 4
    name_block_size = entry_hdr_size + 16

    for nod_off in nod_list:
        count = _get_u16(data, nod_off + 20)
        pos = nod_off + 32
        for _ in range(count):
            if pos + name_block_size > n:
                break
            hdr = data[pos:pos + name_block_size]
            if hdr[:4] != b"ENT*":
                break
            ver = hdr[4:4 + n_unit * 4]
            ver_str = _decode_str(ver, is_unicode)
            if ver_str not in ("0600", "0500"):
                break
            start = _get_u32(hdr, entry_hdr_size)
            size = _get_u32(hdr, entry_hdr_size + 4)
            name_len = _get_u16(hdr, entry_hdr_size + 14)
            pos += name_block_size
            if pos + name_len > n:
                break
            name_bytes = data[pos:pos + name_len]
            pos += name_len
            # name_bytes has trailing padding of n_unit bytes (per C#).
            name = _decode_str(name_bytes[:len(name_bytes) - n_unit], is_unicode)
            raw = _read_data(open(path, "rb"), start, size)
            yield PbEntry(name=name, offset=nod_off, raw=raw)


def save_entries(path: str | Path, out_dir: str | Path) -> int:
    """Decompile a PBD/PBL and write each entry's raw payload as <out_dir>/<name>."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for entry in parse_pbd(path):
        # Sanitize name for filesystem.
        safe = entry.name.replace("/", "_").replace("\\", "_")
        p = out_dir / safe
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(entry.raw)
        count += 1
    return count


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("usage: python pbd_structured.py <pbd|pbl> <out_dir>")
        sys.exit(1)
    n = save_entries(sys.argv[1], sys.argv[2])
    print(f"extracted {n} entries to {sys.argv[2]}")
