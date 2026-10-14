"""
PowerScript parser: token stream → AST.

Scope (M2): parse function bodies — statements and expressions. Anything we
cannot parse cleanly raises `ParseError`; the caller (convert.py) falls back to
the M1 comment-stub path. This keeps the pipeline robust on real PBL text.

AST nodes are plain dataclasses. They intentionally mirror the rules listed
in the M2 plan:
  IF/ELSEIF/ELSE  → If
  CHOOSE CASE     → Choose
  FOR..NEXT STEP  → For
  DO WHILE/UNTIL  → DoWhile / DoUntil
  LOOP WHILE/UNTIL→ WhileDo / UntilDo (do-while)
  TRY/CATCH/FINALLY
  RETURN / EXIT / CONTINUE / THROW
  CREATE / DESTROY
  CALL super::foo / TriggerEvent / PostEvent
  GOTO / label       → Goto / Label (tsbuilder emits TODO)
  variable decl     → Decl
  expression stmt   → ExprStmt
  anything else      → Fallback (carries raw text)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Any
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pslexer import Token, tokenize


class ParseError(Exception):
    pass


# ---------- AST nodes ----------

@dataclass
class Node:
    pass

@dataclass
class Literal(Node):
    value: Any
    kind: str  # 'str' | 'num' | 'bool' | 'null'

@dataclass
class Ident(Node):
    name: str

@dataclass
class Index(Node):
    base: Node
    idx: Node

@dataclass
class Member(Node):
    base: Node
    field: str

@dataclass
class Call(Node):
    callee: Node
    args: List[Node] = field(default_factory=list)
    is_ref_args: List[bool] = field(default_factory=list)

@dataclass
class BinaryOp(Node):
    op: str
    lhs: Node
    rhs: Node

@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

@dataclass
class Assign(Node):
    target: Node
    value: Node

@dataclass
class If(Node):
    cond: Node
    then: List[Node]
    elseifs: List[Any] = field(default_factory=list)   # list of (cond, body)
    else_: List[Node] = field(default_factory=list)

@dataclass
class Choose(Node):
    select: Node
    cases: List[Any] = field(default_factory=list)      # list of (labels, body); labels are list of (kind, expr[, to_expr])
    otherwise: List[Node] = field(default_factory=list)

@dataclass
class For(Node):
    var: str
    start: Node
    end: Node
    step: Optional[Node]
    body: List[Node]

@dataclass
class DoWhile(Node):
    cond: Node
    body: List[Node]

@dataclass
class DoUntil(Node):
    cond: Node
    body: List[Node]

@dataclass
class LoopWhile(Node):
    body: List[Node]
    cond: Node

@dataclass
class LoopUntil(Node):
    body: List[Node]
    cond: Node

@dataclass
class Try(Node):
    body: List[Node]
    catches: List[Any] = field(default_factory=list)    # (type, name, body)
    finally_: List[Node] = field(default_factory=list)

@dataclass
class Return(Node):
    value: Optional[Node] = None

@dataclass
class Exit(Node): pass

@dataclass
class Continue(Node): pass

@dataclass
class Throw(Node):
    value: Node

@dataclass
class Create(Node):
    name: str
    type: Optional[Node] = None

@dataclass
class Destroy(Node):
    name: str

@dataclass
class CallStmt(Node):
    callee: Node
    args: List[Node] = field(default_factory=list)

@dataclass
class Goto(Node):
    label: str

@dataclass
class Label(Node):
    name: str

@dataclass
class Decl(Node):
    type: str
    name: str
    array: bool = False
    value: Optional[Node] = None

@dataclass
class MultiDecl(Node):
    type: str
    names: list
    array: bool = False
    value: Optional[Node] = None

@dataclass
class ArrayLit(Node):
    elems: list

@dataclass
class CreateExpr(Node):
    type: str

@dataclass
class Fallback(Node):
    """A statement we could not parse — tsbuilder preserves it as a comment."""
    text: str


# ---------- Parser ----------

class Parser:
    def __init__(self, tokens: List[Token]):
        self.toks = tokens
        self.i = 0

    # --- basic helpers ---
    def peek(self, off=0) -> Token:
        j = self.i + off
        return self.toks[j] if j < len(self.toks) else Token('EOF', '', 0, 0)

    def next(self) -> Token:
        t = self.toks[self.i]
        if t.kind != 'EOF':
            self.i += 1
        return t

    def skip_noise(self):
        while self.peek().kind in ('NL', 'COMMENT'):
            self.next()

    def expect(self, kind, value=None) -> Token:
        self.skip_noise()
        t = self.peek()
        if t.kind != kind:
            raise ParseError(f"expected {kind} got {t}")
        if value is not None and t.value.lower() != value.lower():
            raise ParseError(f"expected {value!r} got {t.value!r}")
        return self.next()

    def accept(self, kind, value=None) -> Optional[Token]:
        self.skip_noise()
        t = self.peek()
        if t.kind != kind:
            return None
        if value is not None and t.value.lower() != value.lower():
            return None
        return self.next()

    def accept_kw(self, word: str) -> bool:
        self.skip_noise()
        t = self.peek()
        if t.kind == 'KW' and t.value.lower() == word:
            self.next()
            return True
        return False

    def expect_kw(self, word: str):
        if not self.accept_kw(word):
            raise ParseError(f"expected keyword {word}")

    # --- entry point ---
    def parse_block_until(self, terminators) -> List[Node]:
        """Parse statements until a KW in terminators (or EOF)."""
        stmts = []
        while True:
            self.skip_noise()
            t = self.peek()
            if t.kind == 'EOF':
                break
            if t.kind == 'KW' and t.value.lower() in terminators:
                break
            if t.kind == 'KW' and t.value.lower() == 'end':
                break
            try:
                stmts.append(self.parse_statement())
            except ParseError:
                # Fallback: consume tokens until next NL/SEMI and emit Fallback.
                stmts.append(self._fallback_stmt())
            self.accept('SEMI')
        return stmts

    def _fallback_stmt(self) -> Node:
        start_i = self.i
        # Eat until NL or SEMI or EOF.
        while True:
            t = self.peek()
            if t.kind in ('EOF', 'NL', 'SEMI'):
                break
            self.next()
        raw = ' '.join(tok.value for tok in self.toks[start_i:self.i]
                       if tok.kind not in ('NL', 'COMMENT'))
        return Fallback(text=raw)

    def parse_statement(self) -> Node:
        self.skip_noise()
        t = self.peek()
        if t.kind == 'EOF':
            return Fallback(text='')
        try:
            return self._parse_statement_inner(t)
        except (ParseError, AttributeError, IndexError, KeyError) as e:
            # Consume rest of line and fall back.
            start_i = self.i
            while self.i < len(self.toks) and self.toks[self.i].kind != 'NL':
                self.i += 1
            raw = ' '.join(tok.value if isinstance(tok.value, str) else str(tok.value)
                           for tok in self.toks[start_i:self.i]
                           if tok.kind not in ('NL', 'COMMENT'))
            return Fallback(text=raw)

    def _parse_statement_inner(self, t) -> Node:
        if t.kind in ('KW', 'IDENT'):
            w = t.value.lower() if isinstance(t.value, str) else ''
            if w == 'if':      return self.parse_if()
            if w == 'choose':  return self.parse_choose()
            if w == 'for':     return self.parse_for()
            if w == 'do':      return self.parse_do()
            if w == 'try':     return self.parse_try()
            if w == 'return':  return self.parse_return()
            if w == 'exit':    self.next(); return Exit()
            if w == 'continue':self.next(); return Continue()
            if w == 'throw':   self.next(); return Throw(self.parse_expr())
            if w == 'create':  return self.parse_create()
            if w == 'destroy':  return self.parse_destroy()
            if w == 'call':    return self.parse_call()
            if w == 'goto':
                self.next()
                lbl = self.expect('IDENT')
                return Goto(label=lbl.value)
            if w == 'constant' or w == 'string' or w == 'integer' or w == 'long' \
               or w == 'ulong' or w == 'uint' or w == 'boolean' or w == 'blob' \
               or w == 'decimal' or w == 'date' or w == 'time' or w == 'datetime' \
               or w == 'dec' or w == 'real' or w == 'double':
                return self.parse_decl()
            if w in ('shared', 'global', 'local', 'instance', 'variables',
                     'forward', 'prototypes', 'end', 'type', 'from', 'within'):
                raise ParseError(f"block-level keyword: {w}")
            if w == 'halt':
                self.next()
                return Fallback(text='halt')

        # Label: IDENT followed by ':'
        if t.kind == 'IDENT' and self.peek(1).kind == 'COLON':
            self.next(); self.next()
            return Label(name=t.value)

        # Expression or assignment
        return self.parse_expr_or_assign()

    # --- statements ---

    def parse_if(self) -> If:
        self.expect_kw('if')
        cond = self.parse_cond_expr()
        self.expect_kw('then')
        then = self.parse_block_until({'elseif', 'else'})
        elseifs = []
        while self.accept_kw('elseif'):
            ec = self.parse_cond_expr()
            self.expect_kw('then')
            eb = self.parse_block_until({'elseif', 'else'})
            elseifs.append((ec, eb))
        else_ = []
        if self.accept_kw('else'):
            else_ = self.parse_block_until({'end'})
        self.accept_kw('end')
        self.accept_kw('if')
        return If(cond=cond, then=then, elseifs=elseifs, else_=else_)

    def parse_choose(self) -> Choose:
        self.expect_kw('choose')
        self.expect_kw('case')
        sel = self.parse_expr()
        cases = []
        otherwise = []
        while True:
            self.skip_noise()
            if self.accept_kw('case'):
                labels = self.parse_case_labels()
                body = self.parse_block_until({'case'})
                cases.append((labels, body))
            elif self.accept_kw('case') and self.accept_kw('else'):
                otherwise = self.parse_block_until({'end'})
                break
            else:
                # try `case else`
                if self.peek().kind == 'KW' and self.peek().value.lower() == 'case':
                    self.next()
                    if self.accept_kw('else'):
                        otherwise = self.parse_block_until({'end'})
                        break
                    else:
                        labels = self.parse_case_labels()
                        body = self.parse_block_until({'case'})
                        cases.append((labels, body))
                else:
                    break
        self.accept_kw('end')
        self.accept_kw('choose')
        return Choose(select=sel, cases=cases, otherwise=otherwise)

    def parse_case_labels(self):
        labels = []
        while True:
            self.skip_noise()
            # CASE ELSE
            if self.peek().kind == 'KW' and self.peek().value.lower() == 'else':
                self.next()
                labels.append(('else', None, None))
                break
            e = self.parse_expr()
            if self.accept_kw('to'):
                e2 = self.parse_expr()
                labels.append(('range', e, e2))
            else:
                labels.append(('eq', e, None))
            if not self.accept('COMMA'):
                break
        return labels

    def parse_for(self) -> For:
        self.expect_kw('for')
        v = self.expect('IDENT').value
        self.expect('OP', '=')
        start = self.parse_expr()
        self.expect_kw('to')
        end = self.parse_expr()
        step = None
        if self.accept_kw('step'):
            step = self.parse_expr()
        body = self.parse_block_until({'next'})
        self.accept_kw('next')
        return For(var=v, start=start, end=end, step=step, body=body)

    def parse_do(self):
        self.expect_kw('do')
        self.skip_noise()
        t = self.peek()
        if t.kind == 'KW' and t.value.lower() == 'while':
            self.next()
            cond = self.parse_cond_expr()
            body = self.parse_block_until({'loop'})
            self.accept_kw('loop')
            return DoWhile(cond=cond, body=body)
        if t.kind == 'KW' and t.value.lower() == 'until':
            self.next()
            cond = self.parse_cond_expr()
            body = self.parse_block_until({'loop'})
            self.accept_kw('loop')
            return DoUntil(cond=cond, body=body)
        # plain do ... loop while/until
        body = self.parse_block_until({'loop'})
        self.accept_kw('loop')
        self.skip_noise()
        t = self.peek()
        if t.kind == 'KW' and t.value.lower() == 'while':
            self.next()
            return LoopWhile(body=body, cond=self.parse_expr())
        if t.kind == 'KW' and t.value.lower() == 'until':
            self.next()
            return LoopUntil(body=body, cond=self.parse_expr())
        return LoopWhile(body=body, cond=Literal(value='true', kind='bool'))

    def parse_try(self) -> Try:
        self.expect_kw('try')
        body = self.parse_block_until({'catch', 'finally'})
        catches = []
        while self.accept_kw('catch'):
            self.expect('LPAREN')
            ctype = self.expect('IDENT').value
            cname = None
            if self.peek().kind in ('IDENT',):
                cname = self.next().value
            self.expect('RPAREN')
            cbody = self.parse_block_until({'catch', 'finally'})
            catches.append((ctype, cname, cbody))
        finally_ = []
        if self.accept_kw('finally'):
            finally_ = self.parse_block_until({'end'})
        self.accept_kw('end')
        self.accept_kw('try')
        return Try(body=body, catches=catches, finally_=finally_)

    def parse_return(self) -> Return:
        self.expect_kw('return')
        self.skip_noise()
        if self.peek().kind in ('NL', 'SEMI', 'EOF'):
            return Return(value=None)
        try:
            return Return(value=self.parse_expr())
        except ParseError:
            return Return(value=None)

    def parse_create(self) -> Create:
        self.expect_kw('create')
        name = self.expect('IDENT').value
        type_ = None
        if self.accept_kw('using'):
            try:
                type_ = self.parse_expr()
            except ParseError:
                type_ = None
        return Create(name=name, type=type_)

    def parse_destroy(self) -> Destroy:
        self.expect_kw('destroy')
        name = self.expect('IDENT').value
        return Destroy(name=name)

    def parse_call(self) -> CallStmt:
        self.expect_kw('call')
        # callee like super::create or obj.foo
        base = self.parse_postfix()
        args = []
        if self.accept('LPAREN'):
            args = self.parse_args()
            self.expect('RPAREN')
        return CallStmt(callee=base, args=args)

    def parse_decl(self) -> Node:
        # leading constant
        is_const = self.accept_kw('constant')
        # modifiers shared/global/local/instance
        while self.peek().kind == 'KW' and self.peek().value.lower() in (
                'shared', 'global', 'local', 'instance', 'variables'):
            self.next()
        t = self.next().value.lower()
        # optional dec precision
        if self.peek().kind == 'LBRACE':
            self.next(); self.expect('RBRACE')
        names = [self.expect('IDENT').value]
        array = False
        if self.peek().kind == 'LBRACKET':
            self.next()
            while self.peek().kind != 'RBRACKET':
                self.next()
            self.expect('RBRACKET')
            array = True
        # comma-separated names
        while self.peek().kind == 'COMMA' or (self.peek().kind == 'OP' and self.peek().value == ','):
            self.next()
            names.append(self.expect('IDENT').value)
        value = None
        if self.accept('OP', '='):
            value = self.parse_expr()
        if len(names) == 1:
            return Decl(type=t, name=names[0], array=array, value=value)
        return MultiDecl(type=t, names=names, array=array, value=value)

    def parse_expr_or_assign(self) -> Node:
        # lookahead for compound assign += before parse_expr (else + gets swallowed as binary op)
        nxt = self.peek(1)
        if self.peek().kind == 'OP' and self.peek().value == '+' and nxt.kind == 'OP' and nxt.value == '=':
            pass  # let it fall through
        target = self.parse_expr()
        self.skip_noise()
        # compound assign: +=
        if self.peek().kind == 'OP' and self.peek().value == '+':
            nxt2 = self.peek(1)
            if nxt2.kind == 'OP' and nxt2.value == '=':
                self.next(); self.next()
                value = self.parse_expr()
                return Assign(target=target, value=BinaryOp(op='+', lhs=target, rhs=value))
        if self.peek().kind == 'OP' and self.peek().value == '=':
            self.next()
            value = self.parse_expr()
            return Assign(target=target, value=value)
        if isinstance(target, Call):
            return CallStmt(callee=target.callee, args=target.args)
        return Fallback(text=';')

    # --- expressions ---

    def parse_args(self):
        args = []
        self.skip_noise()
        if self.peek().kind == 'RPAREN':
            return args
        while True:
            self.skip_noise()
            is_ref = bool(self.accept_kw('ref'))
            e = self.parse_expr()
            args.append(e)
            if not self.accept('COMMA'):
                break
        return args

    def parse_cond_expr(self) -> Node:
        """Parse an expression in condition position where `=` means equality."""
        lhs = self.parse_expr()
        self.skip_noise()
        if _is_eq_op(self.peek()):
            self.next()
            rhs = self.parse_expr()
            return BinaryOp(op='=', lhs=lhs, rhs=rhs)
        return lhs

    def parse_expr(self, min_prec=0) -> Node:
        left = self.parse_unary()
        while True:
            self.skip_noise()
            t = self.peek()
            # compound assignment: stop before +=
            if t.kind == 'OP' and t.value in ('+', '-', '*', '/'):
                nxt = self.peek(1)
                if nxt.kind == 'OP' and nxt.value == '=':
                    break
            if t.kind == 'OP':
                prec = _BIN_PREC.get(t.value)
                if prec is None or prec < min_prec:
                    break
                self.next()
                right = self.parse_unary()
                left = BinaryOp(op=t.value, lhs=left, rhs=right)
            elif t.kind == 'KW' and t.value.lower() in ('and', 'or'):
                prec = 1 if t.value.lower() == 'or' else 2
                if prec < min_prec:
                    break
                self.next()
                rhs = self.parse_unary()
                left = BinaryOp(op=t.value.lower(), lhs=left, rhs=rhs)
            else:
                break
        return left

    def parse_unary(self) -> Node:
        self.skip_noise()
        t = self.peek()
        if t.kind == 'OP' and t.value in ('-', '+', '!'):
            self.next()
            return UnaryOp(op=t.value, operand=self.parse_unary())
        if t.kind in ('KW', 'IDENT') and t.value.lower() == 'not':
            self.next()
            return UnaryOp(op='not', operand=self.parse_unary())
        if t.kind in ('KW', 'IDENT') and t.value.lower() == 'create':
            self.next()
            # next ident is the type
            self.skip_noise()
            tt = self.peek()
            if tt.kind in ('IDENT', 'KW'):
                self.next()
                return CreateExpr(type=tt.value)
            return CreateExpr(type='')
        return self.parse_postfix()

    def parse_postfix(self) -> Node:
        node = self.parse_primary()
        while True:
            self.skip_noise()
            t = self.peek()
            if t.kind == 'DOT':
                self.next()
                f = self.next()
                node = Member(base=node, field=f.value)
            elif t.kind == 'DCOLON':
                self.next()
                f = self.next()
                node = Member(base=node, field=f.value)
            elif t.kind == 'LBRACKET':
                self.next()
                idx = self.parse_expr()
                self.expect('RBRACKET')
                node = Index(base=node, idx=idx)
            elif t.kind == 'LPAREN':
                self.next()
                args = self.parse_args()
                self.expect('RPAREN')
                node = Call(callee=node, args=args)
            else:
                break
        return node

    def parse_primary(self) -> Node:
        self.skip_noise()
        t = self.peek()
        if t.kind == 'NUM':
            self.next()
            try:
                v = int(t.value)
            except ValueError:
                v = float(t.value)
            return Literal(value=v, kind='num')
        if t.kind == 'STR':
            self.next()
            return Literal(value=t.value, kind='str')
        if t.kind == 'ENUM':
            self.next()
            return Literal(value=t.value, kind='enum')
        if t.kind == 'KW' and t.value.lower() == 'true':
            self.next(); return Literal(value=True, kind='bool')
        if t.kind == 'KW' and t.value.lower() == 'false':
            self.next(); return Literal(value=False, kind='bool')
        if t.kind == 'KW' and t.value.lower() == 'null':
            self.next(); return Literal(value=None, kind='null')
        if t.kind == 'LPAREN':
            self.next()
            e = self.parse_expr()
            self.expect('RPAREN')
            return e
        if t.kind == 'LBRACE':
            self.next()
            elems = []
            self.skip_noise()
            if self.peek().kind != 'RBRACE':
                elems.append(self.parse_expr())
                while self.peek().kind == 'COMMA' or (self.peek().kind == 'OP' and self.peek().value == ','):
                    self.next()
                    self.skip_noise()
                    if self.peek().kind == 'RBRACE': break
                    elems.append(self.parse_expr())
            self.skip_noise()
            self.expect('RBRACE')
            return ArrayLit(elems=elems)
        if t.kind == 'IDENT' or t.kind == 'KW':
            self.next()
            return Ident(name=t.value)
        if t.kind == 'HOSTVAR':
            self.next()
            return Ident(name=':' + t.value)
        raise ParseError(f"unexpected token {t}")


_BIN_PREC = {
    # NOTE: '=' is intentionally excluded here. In statement position it is an
    # assignment; in condition position it is equality. The caller decides.
    '<>': 3, '<': 3, '>': 3, '<=': 3, '>=': 3,
    '+': 5, '-': 5,
    '*': 6, '/': 6, '^': 7,
}


def _is_eq_op(t: Token) -> bool:
    return t.kind == 'OP' and t.value == '='


# ---------- convenience ----------

def parse_function_body(body_lines) -> List[Node]:
    text = "\n".join(body_lines) if isinstance(body_lines, list) else body_lines
    # line continuation: trailing & joins next line
    text = text.replace("&\n", " ").replace("& \n", " ")
    try:
        tokens = tokenize(text)
        p = Parser(tokens)
        return p.parse_block_until({'end'})
    except Exception:
        return [Fallback(text=text)]


if __name__ == '__main__':
    src = sys.stdin.read()
    for stmt in parse_function_body(src):
        print(stmt)
