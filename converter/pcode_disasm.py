"""
Minimal p-code disassembler.

The full C# PCodeParserBase.cs is a 51KB stack-machine emulator that reconstructs
pseudocode from p-code. Porting it 1:1 is a multi-day job. This module provides
the practical subset:
  - Walk p-code bytes using the per-version opcode-length table.
  - Dump each instruction as `offset: OP nn [operands]`.
  - Extract embedded string literals (SQL, messages, button text).

For higher-fidelity pseudocode, see the reference C# sources in
reference/CsharpPbdViewer/Uitils/PCode/.
"""
from __future__ import annotations
import re
from pathlib import Path


# Opcode length tables (bytes after the opcode) for PB 9.0.
# Truncated to 64 entries; unknown opcodes default to 0 (skip operands).
LEN_90 = [
    2,1,1,1,0,0,0,0,0,1,3,3,1,3,3,4,
    0,1,5,0,3,0,3,3,0,4,3,1,1,2,0,0,
    0,0,0,0,1,0,3,2,3,4,2,0,0,3,2,2,
    2,0,0,3,2,2,3,2,0,3,3,0,3,0,3,2,
]

# Versions 100/105/110 have their own tables; we reuse 90 as a rough default
# (opcodes are stable in the low range; unknown ones fall back to 0).


def disasm(data: bytes, base: int = 0, table: list[int] = LEN_90) -> list[str]:
    lines = []
    pos = 0
    n = len(data)
    while pos < n:
        op = data[pos]
        op_len = table[op] if op < len(table) else 0
        if pos + 1 + op_len > n:
            lines.append(f"  {base+pos:04X}: OP {op:02X} <truncated>")
            break
        operands = data[pos+1:pos+1+op_len]
        lines.append(f"  {base+pos:04X}: OP {op:02X} {operands.hex(' ')}")
        pos += 1 + op_len
    return lines


_STRING_RE = re.compile(rb"[\x20-\x7e\x80-\xff]{4,}")


def extract_strings(data: bytes) -> list[str]:
    """Pull printable ASCII/GBK runs >= 4 chars."""
    out = []
    for m in _STRING_RE.finditer(data):
        b = m.group()
        try:
            s = b.decode("utf-8", errors="replace")
        except Exception:
            s = b.decode("gbk", errors="replace")
        if any(c.isalpha() for c in s):
            out.append(s)
    return out


def disasm_file(pcode_path: str | Path) -> str:
    data = Path(pcode_path).read_bytes()
    lines = [f"// p-code dump ({len(data)} bytes)"]
    lines += disasm(data)
    strs = extract_strings(data)
    if strs:
        lines.append("// embedded strings:")
        for s in strs[:50]:
            lines.append(f"//   {s!r}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("usage: python pcode_disasm.py <pcode.bin>")
        sys.exit(1)
    print(disasm_file(sys.argv[1]))
