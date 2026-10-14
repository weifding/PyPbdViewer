"""
Python port of PCodeParser90.cs opcode table.

Covers the full 256-entry opcode length table + the common opcode switch.
Uncommon opcodes (SQL variants, casts) fall back to hex-dump comments.
"""
from __future__ import annotations
import struct
import os, sys
from dataclasses import dataclass, field

try:
    from ._len105 import LEN_105
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from _len105 import LEN_105


@dataclass
class StackObject:
    str: str
    opreator: str = ""


# Use PB 10.5 length table (matches PDB version 0xC1=193 in our corpus).
LEN_90 = LEN_105

# Length table overrides: u16-arg opcodes need 2 bytes.
LEN_90[27] = 2
LEN_90[28] = 2
LEN_90[29] = 2
LEN_90[36] = 2
LEN_90[44] = 2
LEN_90[45] = 2
LEN_90[46] = 2
LEN_90[1] = 2
LEN_90[2] = 2
LEN_90[3] = 2


OP_LEVEL = {
    "": 0, "$not": 1, "$-u": 1,
    "*": 3, "/": 3,
    "+": 4, "-": 4,
    ">": 6, ">=": 6, "<": 6, "<=": 6, "=": 6, "<>": 6,
    "and": 9, "or": 10,
}


def _level(op: str) -> int:
    return OP_LEVEL.get(op, 0)


class VM:
    def __init__(self, pcode: bytes, variables: list[str] | None = None,
                 entry_variables: list[str] | None = None,
                 string_table: bytes | None = None):
        self.pcode = pcode
        self.variables = variables or []
        self.entry_variables = entry_variables or []
        self.string_table = string_table or b""
        self.stack: list[StackObject] = []
        self.output: list[str] = []
        self.pos = 0

    def push(self, s: str, op: str = ""):
        self.stack.append(StackObject(s, op))

    def pop(self) -> StackObject:
        return self.stack.pop() if self.stack else StackObject("")

    def operate(self, op: str):
        b = self.pop(); a = self.pop()
        if _level(b.opreator) > _level(op): b.str = f"({b.str})"
        if _level(a.opreator) > _level(op): a.str = f"({a.str})"
        self.push(f"{a.str} {op} {b.str}", op=op)

    def operate_single(self, op: str):
        a = self.pop()
        if _level(a.opreator) > 0: a.str = f"({a.str})"
        self.push(f"{op} {a.str}", op=f"${op}")

    def end_assign(self, op: str = "="):
        b = self.pop(); a = self.pop()
        self.output.append(f"{a.str} {op} {b.str};")

    def read_str(self, off: int) -> str:
        if off >= len(self.string_table):
            return f"/*str@{off}*/"
        # Non-Unicode PB: null-terminated GBK string.
        end = off
        while end < len(self.string_table) and self.string_table[end] != 0:
            end += 1
        return self.string_table[off:end].decode("gbk", errors="replace")

    def _u16(self, operands: bytes, off: int = 0) -> int:
        if len(operands) - off >= 2:
            return struct.unpack_from("<H", operands, off)[0]
        return operands[off] if len(operands) > off else 0

    def run(self) -> str:
        n = len(self.pcode)
        while self.pos < n:
            op = self.pcode[self.pos]
            try:
                self.handle(op)
            except Exception as e:
                self.output.append(f"// op 0x{op:02X} @{self.pos}: error {e}")
                break
        return "\n".join(self.output)

    def handle(self, op: int):
        op_len = LEN_90[op] if op < len(LEN_90) else 0
        start = self.pos
        self.pos += 1
        operands = self.pcode[self.pos:self.pos + op_len]
        self.pos += op_len

        # ---- control flow ----
        if op == 0:  # return
            flag = self._u16(operands, 0) if len(operands) >= 2 else (operands[0] if operands else 0)
            if flag == 1:
                v = self.pop()
                self.output.append(f"return {v.str};")
            else:
                self.output.append("return;")
        elif op == 1:
            off = self._u16(operands, 0)
            cond = self.pop()
            self.output.append(f"if {cond.str} then goto {off:04X};")
        elif op == 2:
            off = self._u16(operands, 0)
            cond = self.pop()
            self.output.append(f"if not {cond.str} then goto {off:04X};")
        elif op == 3:
            off = self._u16(operands, 0)
            self.output.append(f"goto {off:04X};")

        # ---- SQL ----
        elif op == 4: self.output.append("connect;")
        elif op == 5: self.output.append("commit;")
        elif op == 6: self.output.append("rollback;")
        elif op == 7: self.output.append("disconnect;")
        elif op == 8: self.output.append("close SQLCA;")
        elif op == 9:
            c = self._u16(operands, 0)
            self.output.append(f"open {c};")
        elif op == 10 or op == 11 or op == 14 or op == 25 or op == 26:
            off = struct.unpack_from("<I", operands, 0)[0] if len(operands) >= 4 else 0
            self.output.append(f"// sql dml @{off}")
        elif op == 12:
            c = self._u16(operands, 0)
            self.output.append(f"execute {c};")
        elif op == 13:
            c = self._u16(operands, 4) if len(operands) >= 6 else 0
            self.output.append(f"fetch {c};")

        # ---- object lifecycle ----
        elif op == 16:
            v = self.pop()
            self.output.append(f"destroy {v.str};")
        elif op == 17:
            f = self._u16(operands, 0)
            self.output.append(f"halt {'close' if f == 0 else ''};")
        elif op == 18:
            self.output.append(f"super::<fn>();")
        elif op == 19:
            v = self.pop()
            self.output.append(f"{v.str};")
        elif op == 42:
            off = struct.unpack_from("<I", operands, 0)[0] if len(operands) >= 4 else 0
            self.push(f"create /*type@{off}*/")

        # ---- push ----
        elif op == 27 or op == 45:
            idx = self._u16(operands, 0)
            name = self.variables[idx] if idx < len(self.variables) else f"loc{idx}"
            self.push(name)
        elif op == 28:
            idx = self._u16(operands, 0)
            name = self.entry_variables[idx] if idx < len(self.entry_variables) else f"sh{idx}"
            self.push(name)
        elif op == 29:
            off = self._u16(operands, 0)
            self.push(f"inst{off}")
        elif op == 30: self.push("this")
        elif op == 31: self.push("super")
        elif op == 36:
            off = self._u16(operands, 0)
            b = self.pop()
            self.push(f"{b.str}.{off}")
        elif op == 44:
            idx = self._u16(operands, 0)
            self.push(f"gbl{idx}")
        elif op == 46:
            idx = self._u16(operands, 0)
            self.push(f"gsh{idx}")
        elif op == 47:
            v = struct.unpack_from("<h", operands, 0)[0] if len(operands) >= 2 else (operands[0] if operands else 0)
            self.push(str(v))
        elif op == 48:
            v = self._u16(operands, 0)
            self.push(str(v))
        elif op == 49:
            v = struct.unpack_from("<i", operands, 0)[0] if len(operands) >= 4 else 0
            self.push(str(v))
        elif op == 50:
            v = struct.unpack_from("<I", operands, 0)[0] if len(operands) >= 4 else 0
            self.push(str(v))
        elif op == 56:
            off = struct.unpack_from("<I", operands, 0)[0] if len(operands) >= 4 else 0
            self.push(f'"{self.read_str(off)}"')
        elif op == 57:
            v = self._u16(operands, 0)
            self.push("true" if v == 1 else "false")

        # ---- arithmetic / comparison ----
        elif op in (80,81,82,83,84,85,86,122,123): self.operate("+")
        elif op in (87,88,89,90,91,92,93): self.operate("-")
        elif op in (94,95,96,97,98,99,100): self.operate("*")
        elif op in (101,102,103,104,105,106,107): self.operate("/")
        elif op in (108,109,110,111,112,113,114): self.operate("^")
        elif op in (115,116,117,118,119,120,121): self.operate_single("-")
        elif op == 33: self.operate("and")
        elif op == 34: self.operate("or")
        elif op == 35: self.operate_single("not")
        elif 163 <= op <= 178: self.operate("=")
        elif 179 <= op <= 194: self.operate("<>")
        elif 195 <= op <= 206: self.operate(">")
        elif 207 <= op <= 218: self.operate("<")
        elif 219 <= op <= 230: self.operate(">=")
        elif 231 <= op <= 242: self.operate("<=")

        # ---- assignment ----
        elif op == 124: self.end_assign("[] =")
        elif 125 <= op <= 137: self.end_assign("=")
        elif 243 <= op <= 249: self.end_assign("+=")
        elif 250 <= op <= 256: self.end_assign("-=")
        elif 257 <= op <= 263: self.end_assign("+=")
        elif 264 <= op <= 270: self.end_assign("-=")

        # ---- function call ----
        elif op == 41:
            n = struct.unpack_from("<H", operands, 6)[0] if len(operands) >= 8 else 0
            args = [self.pop().str for _ in range(n)]
            args.reverse()
            fn = self.pop()
            self.push(f"{fn.str}({', '.join(args)})")

        # ---- no-op ----
        elif op in (37, 317, 449):
            pass

        else:
            self.output.append(f"// op 0x{op:02X} @{start:04X} operands={operands.hex(' ')}")


def decompile_pcode(pcode: bytes, variables: list[str] | None = None) -> str:
    vm = VM(pcode, variables=variables or [])
    return vm.run()
