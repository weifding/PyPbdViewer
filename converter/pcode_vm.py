"""
Python port of PCodeParser90.cs + PCodeParserBase.cs opcode semantics.

PDB version 0xC1 (193) uses PCodeParser90. The pcode instruction format is:
  - opcode: uint16 (2 bytes, little-endian)
  - operands: LEN[opcode] * 2 bytes

The length table (_len105.py) gives the operand length in 16-bit units;
multiply by 2 to get byte count.

This ports the full opcode switch from PCodeParser90.cs and the stack
semantics from PCodeParserBase.cs (BeginAssign/EndAssign/Call*/Push*).
Where a name table (instance variables, project-level global function
symbols) is not resolvable in the single-entry context, we emit a readable
placeholder instead of crashing.

run_lines() emits (start_offset, text) pairs so vm2pb can place `goto` labels
at the exact instruction line (problem: label-at-end breaks control flow).
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


LEN = LEN_105


@dataclass
class StackObject:
    str: str
    opreator: str = ""
    type_name: str | None = None


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
                 global_variables: list[str] | None = None,
                 string_table: bytes | None = None,
                 buffer: bytes | None = None,
                 ref_names: list[str] | None = None):
        self.pcode = pcode
        self.variables = variables or []
        self.entry_variables = entry_variables or []
        # global variable name table: GlobalIndex -> name (list is kept for
        # backward callers; indexed as-is).
        if isinstance(global_variables, dict):
            self.global_variables = global_variables
        else:
            self.global_variables = {i: n for i, n in enumerate(global_variables or [])}
        self.string_table = string_table or b""
        # function struct buffer (string pool) — same backing store as string_table
        self.buffer = buffer if buffer is not None else self.string_table
        self.ref_names = ref_names or []
        self.stack: list[StackObject] = []
        # output lines: list of (start_offset, text)
        self.output: list[tuple[int, str]] = []
        self.pos = 0

    # ---- stack ----
    def push(self, s: str, op: str = "", type_name: str | None = None):
        self.stack.append(StackObject(s, op, type_name))

    def pop(self) -> StackObject:
        if not self.stack:
            return StackObject("")
        return self.stack.pop()

    def pop_n(self, n: int) -> list[StackObject]:
        out = []
        for _ in range(int(n)):
            out.append(self.pop())
        out.reverse()
        return out

    def operate(self, op: str):
        b = self.pop(); a = self.pop()
        if _level(b.opreator) >= _level(op): b.str = f"({b.str})"
        if _level(a.opreator) > _level(op): a.str = f"({a.str})"
        self.push(f"{a.str} {op} {b.str}", op=op)

    def operate_single(self, op: str):
        a = self.pop()
        if _level(a.opreator) > 0: a.str = f"({a.str})"
        self.push(f"{op} {a.str}", op=f"${op}")

    def emit(self, text: str):
        self.output.append((self.last_start, text))

    def end_assign(self, op: str = "="):
        b = self.pop(); a = self.pop()
        self.emit(f"{a.str} {op} {b.str};")

    def end_assign2(self, op: str = "++"):
        a = self.pop()
        self.emit(f"{a.str} {op};")

    def call_builtin(self, name: str, paramcount: int):
        args = self.pop_n(paramcount)
        self.push(f"{name}({', '.join(o.str for o in args)})")

    # ---- string / buffer reads ----
    def read_str(self, off: int) -> str:
        buf = self.buffer
        if off < 0 or off >= len(buf):
            return f"/*str@{off}*/"
        end = off
        while end < len(buf) and buf[end] != 0:
            end += 1
        try:
            s = buf[off:end].decode("gbk", errors="replace")
        except Exception:
            s = buf[off:end].decode("latin-1", errors="replace")
        # Guard: mojibake / control bytes would become invalid TS (TS1127).
        if "\ufffd" in s or any(ord(c) < 32 for c in s):
            return f"pstr@{off}"
        return s

    def _safe_name(self, raw: str, fallback: int) -> str:
        """Return a valid, non-keyword identifier from a raw name, or a placeholder.

        `new` (PB constructor) and other TS keywords must not leak through or
        `x = new();` would be a TS1025 syntax error that @ts-nocheck can't hide.
        """
        import re as _re
        _kw = {"new", "class", "function", "return", "if", "else", "for", "while",
               "do", "switch", "case", "default", "break", "continue", "try",
               "catch", "finally", "throw", "this", "super", "typeof", "instanceof",
               "delete", "in", "of", "var", "let", "const", "import", "export",
               "extends", "interface", "enum", "null", "true", "false", "void",
               "yield", "await", "async", "static", "get", "set", "as"}
        if raw and _re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', raw) and raw not in _kw:
            return raw
        return f"m{fallback:04X}"

    def _u16(self, operands: bytes, off: int = 0) -> int:
        if len(operands) - off >= 2:
            return struct.unpack_from("<H", operands, off)[0]
        return operands[off] if len(operands) > off else 0

    def _u32(self, operands: bytes, off: int = 0) -> int:
        if len(operands) - off >= 4:
            return struct.unpack_from("<I", operands, off)[0]
        return self._u16(operands, off)

    # ---- run ----
    def run(self) -> str:
        return "\n".join(t for _, t in self.run_lines())

    def run_lines(self) -> list[tuple[int, str]]:
        n = len(self.pcode)
        while self.pos < n:
            start = self.pos
            op = struct.unpack_from("<H", self.pcode, self.pos)[0]
            self.pos += 2
            oplen_units = LEN[op] if op < len(LEN) else 0
            operands = self.pcode[self.pos:self.pos + oplen_units * 2]
            self.pos += oplen_units * 2
            self.last_start = start
            try:
                self.handle(op, operands, start)
            except Exception as e:
                self.output.append((start, f"// op 0x{op:04X} @{start:04X}: error {e}"))
                break
        if self.pos != n:
            self.output.append((self.pos, f"// WARNING: disassembler stopped at {self.pos:04X}/{n:04X}"))
        return self.output

    def handle(self, op: int, operands: bytes, start: int):
        # ---- control flow ----
        if op == 0:
            flag = self._u16(operands, 0)
            if flag == 1:
                self.emit(f"return {self.pop().str};")
            else:
                self.emit("return;")
        elif op == 1:
            self.emit(f"if {self.pop().str} then goto {self._u16(operands, 0):04X};")
        elif op == 2:
            self.emit(f"if not {self.pop().str} then goto {self._u16(operands, 0):04X};")
        elif op == 3:
            self.emit(f"goto {self._u16(operands, 0):04X};")

        # ---- SQL ----
        elif op == 4: self.emit("connect;")
        elif op == 5: self.emit("commit;")
        elif op == 6: self.emit("rollback;")
        elif op == 7: self.emit("disconnect;")
        elif op == 8: self.emit("close SQLCA;")
        elif op == 9: self.emit(f"open {self._u16(operands, 0)};")
        elif op in (10, 11, 14, 26):
            off = self._u32(operands, 0)
            sql = self.read_str(off)
            if sql and not sql.startswith("/*str@"):
                self.emit(f"// SQL: \"{sql}\"")
            else:
                self.emit(f"// sql dml @{off}")
        elif op == 12: self.emit(f"execute {self._u16(operands, 0)};")
        elif op == 13: self.emit(f"fetch {self._u16(operands, 4)};")
        elif op == 20: self.emit(f"execute {self._u16(operands, 4)};")  # SqlExecuteSqlsa
        elif op == 21: self.emit("prepare SQLSA;")
        elif op in (22, 23):
            off = self._u32(operands, 0)
            self.emit(f"// dynamic sql @{off}")
        elif op == 24: self.emit("describe;")
        elif op == 25: self.emit("// sql select @0")

        # ---- object lifecycle ----
        elif op == 16: self.emit(f"destroy({self.pop().str});")
        elif op == 17:
            self.emit(f"halt {'close' if self._u16(operands, 0) == 0 else ''};")
        elif op == 18:
            # CallSuper(functionIndex, paramcount, objType, nameoffset)
            pc = self._u16(operands, 0); pn = self._u16(operands, 2)
            name = self.read_str(self._u32(operands, 6)) if len(operands) >= 8 else f"super_evt_{pc}"
            self.pop_n(pn)
            self.push(f"super::{name}()")
        elif op == 19: self.emit(f"{self.pop().str};")  # PopFunction
        elif op == 42:
            off = self._u32(operands, 0)
            tn = self.read_str(off) or f"/*type@{off}*/"
            self.push(f"create {tn}")
        elif op == 362:  # CreateObject
            off = self._u32(operands, 0)
            self.push(f"create {self.read_str(off) or f'/*type@{off}*/'}")
        elif op == 456:  # CreateObjectUsingName
            self.push(f"create using {self.pop().str}")

        # ---- push variable references ----
        elif op in (27, 45):
            idx = self._u16(operands, 0)
            name = self.variables[idx] if idx < len(self.variables) else f"loc{idx}"
            self.push(name)
        elif op == 28:
            idx = self._u16(operands, 0)
            name = self.entry_variables[idx] if idx < len(self.entry_variables) else f"sh{idx}"
            self.push(name)
        elif op == 29:
            # PushInstanceVariableName(offset): `off` is a buffer offset; at
            # buffer[off] sits u32 name-string offset, at buffer[off+4] u16 inst index.
            off = self._u16(operands, 0)
            if 1 <= off <= 7:
                self.push("entryobject")
                return
            name_off = 0xFFFF
            inst_idx = off
            if off + 4 <= len(self.buffer):
                name_off = struct.unpack_from("<I", self.buffer, off)[0]
                inst_idx = self._u16(self.buffer, off + 4) if off + 6 <= len(self.buffer) else off
            if (name_off & 0xFFFF) != 0xFFFF and name_off < len(self.buffer):
                self.push(self._safe_name(self.read_str(name_off), start))
            else:
                self.push(f"inst{inst_idx}")
        elif op == 30: self.push("this")
        elif op == 31: self.push("parent")
        elif op == 36:
            # PushInstanceVariable(unknown): combine obj.var from stack
            off = self._u16(operands, 0)
            b = self.pop(); a = self.pop()
            if a.str == "entryobject":
                self.push(self._safe_name(b.str, start))
            else:
                self.push(f"{self._safe_name(a.str, start)}.{self._safe_name(b.str, start)}")
        elif op in (318, 319):  # PushInstanceVariable
            b = self.pop(); a = self.pop()
            if a.str == "entryobject":
                self.push(self._safe_name(b.str, start))
            else:
                self.push(f"{self._safe_name(a.str, start)}.{self._safe_name(b.str, start)}")
        elif op == 44:
            idx = self._u16(operands, 0)
            self.push(self.global_variables.get(idx, f"gbl{idx}"))
        elif op == 46: self.push(f"gsh{self._u16(operands, 0)}")
        elif op in (332, 333, 339, 367, 425, 512):
            idx = self._u16(operands, 0)
            name = self.variables[idx] if idx < len(self.variables) else f"loc{idx}"
            self.push(name)
        elif op in (334, 335, 368, 426, 515):
            idx = self._u16(operands, 0)
            name = self.entry_variables[idx] if idx < len(self.entry_variables) else f"sh{idx}"
            self.push(name)
        elif op in (336, 337, 369, 422, 513):
            idx = self._u16(operands, 0)
            self.push(self.global_variables.get(idx, f"gbl{idx}"))
        elif op == 387:
            b = self.pop(); a = self.pop()
            self.push(f"{self._safe_name(a.str, start)}.{self._safe_name(b.str, start)}")
        elif op == 464: self.push("this")
        elif op == 466:
            off = self._u16(operands, 0)
            self.push(self._safe_name(self.read_str(off), off) if off < len(self.buffer) and (self._u32(operands, 0) & 0xFFFF) != 0xFFFF else f"inst{off}")
        elif op == 542:
            b = self.pop(); a = self.pop()
            self.push(f"{self._safe_name(a.str, start)}.{self._safe_name(b.str, start)}")

        # ---- assignment target markers (push LHS) ----
        elif op in (282, 285):
            idx = self._u16(operands, 0)
            name = self.variables[idx] if idx < len(self.variables) else f"loc{idx}"
            self.push(name)
        elif op == 283:
            idx = self._u16(operands, 0)
            name = self.entry_variables[idx] if idx < len(self.entry_variables) else f"sh{idx}"
            self.push(name)
        elif op == 284:
            idx = self._u16(operands, 0)
            self.push(self.global_variables.get(idx, f"gbl{idx}"))
        elif op == 287:  # BeginAssignInstanceVariable
            b = self.pop(); a = self.pop()
            if a.str == "entryobject":
                self.push(b.str, b.opreator)
            else:
                self.push(f"{a.str}.{b.str}")

        # ---- push constants ----
        elif op == 47: self.push(str(struct.unpack_from("<h", operands, 0)[0] if len(operands) >= 2 else 0))
        elif op == 48: self.push(str(self._u16(operands, 0)))
        elif op == 49:
            v = struct.unpack_from("<i", operands, 0)[0] if len(operands) >= 4 else self._u16(operands, 0)
            self.push(str(v))
        elif op == 50: self.push(str(self._u32(operands, 0)))
        elif op in (51, 52, 53, 54, 55):  # decimal/real/double/time/date const (need buffer)
            off = self._u32(operands, 0)
            self.push(f"{('dec' if op == 51 else 'real' if op == 52 else 'dbl' if op == 53 else 'time' if op == 54 else 'date')}@{off}")
        elif op == 56:
            off = self._u32(operands, 0)
            self.push(f'"{self.read_str(off)}"')
        elif op == 57:
            self.push("true" if self._u16(operands, 0) == 1 else "false")
        elif op == 58:
            self.push(f"pbEnum[{self._u16(operands, 2)}]")
        elif op == 511: self.push(f"long@{self._u32(operands, 0)}")

        # ---- logic ----
        elif op == 33: self.operate("and")
        elif op == 34: self.operate("or")
        elif op == 35: self.operate_single("not")
        elif op == 384: self.operate("and")
        elif op == 385: self.operate("or")
        elif op == 386: self.operate_single("not")

        # ---- arithmetic ----
        elif op in (80,81,82,83,84,85,86,122,123,372,505): self.operate("+")
        elif op in (87,88,89,90,91,92,93,373,506): self.operate("-")
        elif op in (94,95,96,97,98,99,100,374,507): self.operate("*")
        elif op in (101,102,103,104,105,106,107,375,508): self.operate("/")
        elif op in (108,109,110,111,112,113,114,376,509): self.operate("^")
        elif op in (115,116,117,118,119,120,121,377,510): self.operate_single("-")

        # ---- compare ----
        elif 163 <= op <= 178 or op == 378 or op == 527: self.operate("=")
        elif 179 <= op <= 194 or op == 379 or op == 528: self.operate("<>")
        elif 195 <= op <= 206 or op == 380 or op == 529: self.operate(">")
        elif 207 <= op <= 218 or op == 381 or op == 530: self.operate("<")
        elif 219 <= op <= 230 or op == 382 or op == 531: self.operate(">=")
        elif 231 <= op <= 242 or op == 383 or op == 532: self.operate("<=")

        # ---- assignment ----
        elif op == 124: self.end_assign("[] =")
        elif 125 <= op <= 137 or op == 342 or op == 517: self.end_assign("=")
        elif op in (243,244,245,246,247,248,249): self.end_assign2("++")
        elif op in (250,251,252,253,254,255,256): self.end_assign2("--")
        elif op in (257,258,259,260,261,262,263,519): self.end_assign("+=")
        elif op in (264,265,266,267,268,269,270,520): self.end_assign("-=")
        elif op in (271,272,273,274,275,276,277,521): self.end_assign("*=")
        elif op in (522, 442): self.end_assign2("++")
        elif op in (523, 443): self.end_assign2("--")
        elif op == 278:  # ResetAssign: swap top two
            item = self.pop(); item2 = self.pop()
            self.push(item.str, item.opreator); self.push(item2.str, item2.opreator)

        # ---- casts (no stack effect) ----
        elif (59 <= op <= 79) or (138 <= op <= 162) or (288 <= op <= 296) \
             or (298 <= op <= 315) or (320 <= op <= 323) or (338 <= op <= 361) \
             or (343 <= op <= 361) or (388 <= op <= 389) or (427 <= op <= 427) \
             or op in (430, 438, 457, 459, 461, 462, 463, 491, 492, 493, 494,
                       495, 496, 497, 498, 499, 500, 501, 502, 503, 504,
                       524, 543, 544, 546):
            pass

        # ---- array / index ----
        elif op == 431:  # Index
            b = self.pop(); a = self.pop()
            self.push(f"{a.str}[{b.str}]")
        elif op in (432, 433):  # Index2/Index3
            b = self.pop(); a = self.pop()
            self.push(f"{a.str}[{b.str}]")
        elif op in (434, 435):  # CreateArray
            n = self._u16(operands, 4)
            items = self.pop_n(n)
            self.push(f"{{{', '.join(o.str for o in items)}}}")

        # ---- builtin calls ----
        elif op == 390: self.call_builtin("int", 1)
        elif op in (391, 392): self.call_builtin("abs", 1)
        elif op == 393: self.call_builtin("asc", 1)
        elif op == 394: self.call_builtin("blob", 1)
        elif op == 395: self.call_builtin("ceiling", 1)
        elif op == 396: self.call_builtin("cos", 1)
        elif op == 397: self.call_builtin("exp", 1)
        elif op == 398: self.call_builtin("fact", 1)
        elif op == 399: self.call_builtin("inthigh", 1)
        elif op == 400: self.call_builtin("intlow", 1)
        elif op == 401: self.call_builtin("isdate", 1)
        elif op == 402: self.call_builtin("isnull", 1)
        elif op == 403: self.call_builtin("isnumber", 1)
        elif op == 404: self.call_builtin("istime", 1)
        elif op == 405: self.call_builtin("isvalid", 1)
        elif op == 406: self.call_builtin("lefttrim", 1)
        elif op in (407, 408): self.call_builtin("len", 1)
        elif op == 409: self.call_builtin("log", 1)
        elif op == 410: self.call_builtin("logten", 1)
        elif op == 411: self.call_builtin("lower", 1)
        elif op == 412: self.call_builtin("pi", 1)
        elif op == 413: self.call_builtin("rand", 1)
        elif op == 415: self.call_builtin("righttrim", 1)
        elif op == 416: self.call_builtin("sin", 1)
        elif op == 417: self.call_builtin("sqrt", 1)
        elif op == 418: self.call_builtin("tan", 1)
        elif op == 419: self.call_builtin("trim", 1)
        elif op == 420: self.call_builtin("upper", 1)
        elif op == 440: self.call_builtin("lowerbound", 1)
        elif op == 441: self.call_builtin("upperbound", 1)
        elif op in (467,468,469,470,471): self.call_builtin("mod", 2)
        elif op in (472, 473): self.call_builtin("abs", 1)
        elif op == 474: self.call_builtin("ceiling", 1)
        elif op in (475,476,477,478,479): self.call_builtin("min", 2)
        elif op in (480,481,482,483,484): self.call_builtin("max", 2)
        elif op == 525: self.call_builtin("abs", 1)
        elif op == 533: self.call_builtin("mod", 2)
        elif op == 534: self.call_builtin("min", 2)
        elif op == 535: self.call_builtin("max", 2)

        # ---- global function refs ----
        elif op == 444:
            # PushGlobalFunctionName(objIndex=u16@2, functionIndex=u16@0)
            fn_idx = self._u16(operands, 0)
            obj_idx = self._u16(operands, 2)
            if obj_idx & 0x8000:
                name = self._safe_name(self.ref_names[fn_idx], fn_idx) if fn_idx < len(self.ref_names) else f"gf_{fn_idx}"
            elif obj_idx & 0x4000:
                name = f"sys{obj_idx & 0x3FFF}_{fn_idx}"
            else:
                # project-level global function symbol (unknown here) -> readable placeholder
                name = f"gf_{fn_idx}"
            self.push(name)
        elif op in (445, 446, 447, 448, 540):
            # CallGlobalFunction(count=u16@2, type=u16@4)
            count = self._u16(operands, 2)
            typ = self._u16(operands, 4)
            fname = self.pop().str
            args = self.pop_n(count)
            if typ & 1: fname = "post " + fname
            if typ & 2: fname = "dynamic " + fname
            if typ & 4: fname = "event " + fname
            self.push(f"{fname}({', '.join(o.str for o in args)})")

        # ---- object method call ----
        elif op == 41:
            # CallFunction(offset=u32@0, count=u16@4, type=u16@6)
            off = self._u32(operands, 0)
            count = self._u16(operands, 4)
            args = self.pop_n(count)
            obj = self.pop()
            name = self._safe_name(self.read_str(off + 4) if off + 4 < len(self.buffer) else "", off)
            if obj.str == "this":
                self.push(f"super::{name}({', '.join(o.str for o in args)})")
            else:
                self.push(f"{obj.str}.{name}({', '.join(o.str for o in args)})")
        elif op in (330, 331, 366, 539):
            # CallFunction variant (same operands as 41)
            off = self._u32(operands, 0)
            count = self._u16(operands, 4)
            args = self.pop_n(count)
            obj = self.pop()
            name = self._safe_name(self.read_str(off + 4) if off + 4 < len(self.buffer) else "", off)
            if obj.str == "this":
                self.push(f"super::{name}({', '.join(o.str for o in args)})")
            else:
                self.push(f"{obj.str}.{name}({', '.join(o.str for o in args)})")

        # ---- exception handling (best-effort; emit as comments since the
        # TS builder has no try/catch structuring — a bare `catch(x);` is TS1025) ----
        elif op == 485: self.emit("// try")
        elif op == 486: self.emit("// end try")
        elif op == 487: self.emit(f"// catch ({self.pop().str})")
        elif op == 488: self.emit(f"throw {self.pop().str};")
        elif op == 489: self.emit("// enter finally")
        elif op == 490: self.emit("// leave finally")
        elif op == 451: self.emit("execute immediate;")
        elif op == 452: self.emit(f"// execute dynamic @{self._u32(operands, 0)}")
        elif op == 453: self.emit("fetch dynamic;")
        elif op == 454: self.emit(f"// open dynamic @{self._u32(operands, 0)}")

        # ---- no-op ----
        elif op in (37, 317, 449, 20):
            pass

        else:
            self.output.append((start, f"// op 0x{op:04X} @{start:04X} operands={operands.hex(' ')}"))


def decompile_pcode(pcode: bytes, variables: list[str] | None = None) -> str:
    vm = VM(pcode, variables=variables or [])
    return vm.run()
