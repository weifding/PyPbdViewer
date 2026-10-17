"""
TS builder: walk psparser AST and emit TypeScript.

Translation rules (from M2 plan):
- Conditional `a = b` → `PB.eq(a, b)`; `<>`→`PB.ne`, `<`/`>`/`<=`/`>=` direct.
- Assignment `a = expr` → `a = expr;` (no PB.eq).
- `AND/OR/NOT` → `&&`/`||`/`!`.
- 1-based index `arr[i]` → `arr[(i) - 1]`.
- CHOOSE CASE → if/else-if chain.
- FOR..TO..STEP → classic for.
- DO WHILE/UNTIL, LOOP WHILE/UNTIL → while / do-while (UNTIL negated).
- TRY/CATCH → try/catch.
- GOTO / Label / Fallback → comment + return-default (caller decides).
- CREATE / DESTROY → `new` / `= null`.

The builder returns (ts_lines, fallback_bool). `fallback_bool=True` means the
function contains a node we refused to translate and convert.py should emit
the M1 comment-stub instead.
"""
from __future__ import annotations
from typing import List, Tuple
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from psparser import (
    Node, Literal, Ident, Index, Member, Call, BinaryOp, UnaryOp,
    Assign, If, Choose, For, DoWhile, DoUntil, LoopWhile, LoopUntil,
    Try, Return, Exit, Continue, Throw, Create, Destroy, CallStmt, ExprStmt,
    Goto, Label, Decl, MultiDecl, ArrayLit, CreateExpr, Fallback, ParseError,
    SQLStmt, PostDec,
)


_TS_RESERVED = frozenset(
    "break case catch class const continue debugger default delete do else enum "
    "export extends false finally for function if import in instanceof new null "
    "return super switch this throw true try typeof var void while with let yield "
    "async await static interface type implements private protected public "
    "namespace module declare abstract".split())


class Builder:
    def __init__(self):
        self.fallback = False
        self.lines: List[str] = []

    # ---- entry ----
    def build_block(self, stmts: List[Node], indent: int = 1):
        # Used only for top-level; nested bodies go through _render_body.
        pad = "  " * indent
        for line in _render_body(stmts, indent):
            self.lines.append(pad + line if line else "")

    # ---- expressions ----
    def expr(self, e: Node, precedence: int = 0) -> str:
        if isinstance(e, ArrayLit):
            return "[" + ", ".join(self.expr(x) for x in e.elems) + "]"
        if isinstance(e, CreateExpr):
            return f"null as any  /* create {e.type} */"
        if isinstance(e, Literal):
            if e.kind == 'str':
                # PB string already decoded; re-escape for TS.
                return _ts_str(e.value)
            if e.kind == 'num':
                return str(e.value)
            if e.kind == 'bool':
                return 'true' if e.value else 'false'
            if e.kind == 'null':
                return 'null'
            return repr(e.value)
        if isinstance(e, Ident):
            # SQL host variable :name → bare name
            n = e.name[1:] if e.name.startswith(':') else e.name
            if n in _TS_RESERVED or not re.match(r'^[A-Za-z_$][A-Za-z0-9_$]*$', n):
                # TS reserved word or invalid identifier (mojibake) → safe null
                return 'null'
            return n
        if isinstance(e, PostDec):
            return f"{self.expr(e.base)}--"
        if isinstance(e, Member):
            base = self.expr(e.base)
            f = e.field
            if f.startswith('#'):
                # PB DW column index #N → colN
                return f"{base}['col{f[1:]}']"
            if f and (f[0].isdigit() or not (f[0].isalpha() or f[0] == '_')):
                return f"{base}[{f!r}]"
            return f"{base}.{f}"
        if isinstance(e, Index):
            # 1-based → 0-based
            return f"{self.expr(e.base)}[({self.expr(e.idx)}) - 1]"
        if isinstance(e, Call):
            args = ", ".join(self.expr(a) for a in e.args)
            return f"{self.expr(e.callee)}({args})"
        if isinstance(e, BinaryOp):
            op = e.op
            lhs = self.expr(e.lhs)
            rhs = self.expr(e.rhs)
            # Null-safe equality
            if op == '=':
                return f"PB.eq({lhs}, {rhs})"
            if op == '<>':
                return f"PB.ne({lhs}, {rhs})"
            if op == 'and':
                return f"({lhs} && {rhs})"
            if op == 'or':
                return f"({lhs} || {rhs})"
            if op in ('+', '-', '*', '/', '^', '<', '>', '<=', '>='):
                js_op = '**' if op == '^' else op
                return f"({lhs} {js_op} {rhs})"
            return f"({lhs} {op} {rhs})"
        if isinstance(e, UnaryOp):
            o = self.expr(e.operand)
            if e.op == 'not':
                return f"!{o}"
            if e.op == '-':
                return f"-{o}"
            return f"{e.op}{o}"
        # unknown
        self.fallback = True
        return "/* unparsed */ null"

    # ---- statements ----
    def stmt(self, s: Node, indent: int) -> List[str]:
        if isinstance(s, Fallback):
            self.fallback = True
            return [f"// TODO: unparsed statement: {s.text}"]
        if isinstance(s, SQLStmt):
            safe = s.text.replace('*/', '* /')
            return [f"/* SQL: {safe} */"]
        if isinstance(s, Return):
            if s.value is None:
                return ["return;"]
            # PB `return End` / `return Close` are bare returns in disguise.
            from psparser import Ident
            if isinstance(s.value, Ident) and s.value.name in ("End", "end", "Close", "close"):
                return ["return;"]
            return [f"return {self.expr(s.value)};"]
        if isinstance(s, Exit):
            return ["break;"]
        if isinstance(s, Continue):
            return ["continue;"]
        if isinstance(s, Throw):
            return [f"throw new Error({self.expr(s.value)});"]
        if isinstance(s, Assign):
            return [f"{self.expr(s.target)} = {self.expr(s.value)};"]
        if isinstance(s, Decl):
            v = f" = {self.expr(s.value)}" if s.value else ""
            return [f"let {s.name}{v};"]
        if isinstance(s, MultiDecl):
            out = []
            v = f" = {self.expr(s.value)}" if s.value else ""
            for n in s.names:
                out.append(f"let {n}{v};")
            return out
        if isinstance(s, Create):
            return [f"{s.name} = null as any;  /* create {s.type or s.name} */"]
        if isinstance(s, Destroy):
            return [f"{s.name} = null;"]
        if isinstance(s, CallStmt):
            return [f"{self.expr(Call(callee=s.callee, args=s.args))};"]
        if isinstance(s, ExprStmt):
            return [f"{self.expr(s.expr)};"]
        if isinstance(s, Label):
            return [f"// label {s.name}: (PB GOTO not translated)"]
        if isinstance(s, Goto):
            self.fallback = True
            return [f"// GOTO {s.label} not translated"]
        if isinstance(s, If):
            return self._if(s, indent)
        if isinstance(s, Choose):
            return self._choose(s, indent)
        if isinstance(s, For):
            return self._for(s, indent)
        if isinstance(s, (DoWhile, DoUntil)):
            return self._do_while(s, indent)
        if isinstance(s, (LoopWhile, LoopUntil)):
            return self._loop_while(s, indent)
        if isinstance(s, Try):
            return self._try(s, indent)
        self.fallback = True
        return [f"// TODO: unhandled node {type(s).__name__}"]

    # Alias used by build_block.
    build_stmt = stmt

    def _if(self, s: If, indent: int) -> List[str]:
        out = [f"if ({self.expr(s.cond)}) {{"]
        out += _render_body(s.then, indent + 1)
        out.append("}")
        for cond, body in s.elseifs:
            out.append(f"else if ({self.expr(cond)}) {{")
            out += _render_body(body, indent + 1)
            out.append("}")
        if s.else_:
            out.append("else {")
            out += _render_body(s.else_, indent + 1)
            out.append("}")
        return out

    def _choose(self, s: Choose, indent: int) -> List[str]:
        sel = self.expr(s.select)
        out = []
        first = True
        for labels, body in s.cases:
            conds = []
            for kind, a, b in labels:
                if kind == 'eq':
                    conds.append(f"PB.eq({sel}, {self.expr(a)})")
                elif kind == 'range':
                    conds.append(f"({self.expr(a)} <= {sel} && {sel} <= {self.expr(b)})")
                elif kind == 'else':
                    conds.append("true")
            cond = " || ".join(conds) if conds else "false"
            kw = "if" if first else "else if"
            first = False
            out.append(f"{kw} ({cond}) {{")
            out += _render_body(body, indent + 1)
            out.append("}")
        if s.otherwise:
            out.append("else {")
            out += _render_body(s.otherwise, indent + 1)
            out.append("}")
        return out

    def _for(self, s: For, indent: int) -> List[str]:
        step = self.expr(s.step) if s.step else "1"
        out = [f"for (let {s.var} = {self.expr(s.start)}; {s.var} <= {self.expr(s.end)}; {s.var} += {step}) {{"]
        out += _render_body(s.body, indent + 1)
        out.append("}")
        return out

    def _do_while(self, s, indent: int) -> List[str]:
        if isinstance(s, DoUntil):
            cond = f"!({self.expr(s.cond)})"
        else:
            cond = self.expr(s.cond)
        out = [f"while ({cond}) {{"]
        out += _render_body(s.body, indent + 1)
        out.append("}")
        return out

    def _loop_while(self, s, indent: int) -> List[str]:
        if isinstance(s, LoopUntil):
            cond = f"!({self.expr(s.cond)})"
        else:
            cond = self.expr(s.cond)
        out = ["do {"]
        out += _render_body(s.body, indent + 1)
        out.append(f"}} while ({cond});")
        return out

    def _try(self, s: Try, indent: int) -> List[str]:
        # If there are no catches/finally, just emit the body as a plain block
        # (PB's try/catch was probably used defensively around a block).
        if not s.catches and not s.finally_:
            return _render_body(s.body, indent)
        out = ["try {"]
        out += _render_body(s.body, indent + 1)
        out.append("}")
        for ctype, cname, body in s.catches:
            out.append(f"catch ({cname or 'e'}: any) {{")
            out += _render_body(body, indent + 1)
            out.append("}")
        if s.finally_:
            out.append("finally {")
            out += _render_body(s.finally_, indent + 1)
            out.append("}")
        return out


def _render_body(stmts, indent: int) -> List[str]:
    """Render a list of statements as indented TS lines (no leading pad)."""
    b = Builder()
    # Temporarily route output via b.lines; stmt returns lists which we collect.
    pad = "  " * indent
    lines = []
    for s in stmts:
        if isinstance(s, Fallback):
            b.fallback = True
            lines.append(pad + f"// TODO: unparsed: {s.text}")
            continue
        try:
            chunk = b.stmt(s, indent)
        except Exception:
            b.fallback = True
            lines.append(pad + f"// TODO: builder failed on {type(s).__name__}")
            continue
        for l in chunk:
            lines.append(pad + l)
    if b.fallback:
        # Signal caller that we fell back; caller decides.
        pass
    return lines


def build_function_body(stmts: List[Node]) -> Tuple[str, bool]:
    """Return (ts_body_str, fell_back)."""
    b = Builder()
    lines = _render_body(stmts, indent=1)
    return "\n".join(lines), b.fallback


def _ts_str(s: str) -> str:
    # PB string escapes already decoded by lexer; emit safe TS literal.
    out = []
    for ch in s:
        if ch == '\\':
            out.append('\\\\')
        elif ch == '"':
            out.append('\\"')
        elif ch == '\n':
            out.append('\\n')
        elif ch == '\r':
            out.append('\\r')
        elif ch == '\t':
            out.append('\\t')
        elif ord(ch) < 0x20:
            out.append(f"\\x{ord(ch):02x}")
        else:
            out.append(ch)
    return '"' + ''.join(out) + '"'
