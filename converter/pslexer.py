"""
PowerScript lexer → flat token stream.

Tokens carry (kind, value, line, col) for diagnostics and fallback.

Design:
- A scanning loop (not regex finditer) so multi-char constructs like `~~`
  escapes in strings, `~r~n`, `::`, `<>`, and multiline `/* */` comments are
  handled cleanly in one pass.
- Keywords are identified case-insensitively: the value keeps original case,
  and the parser does `.lower()` comparisons.  After `.` or `::` (member
  access) the parser treats the next IDENT/KW as an identifier regardless of
  kind.
- `IDENT!` (e.g. `Text!`, `LineMode!`) is emitted as a single ENUM token.
- `:name` host variables in embedded SQL are emitted as HOSTVAR.
- Any byte that does not match a known pattern becomes a single-char JUNK
  token so the lexer never raises; the parser can fall back to M1
  comment-stub behaviour on any JUNK or unexpected token.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

KEYWORDS = {
    "and", "or", "not",
    "if", "then", "elseif", "else", "end",
    "choose", "case", "to", "for", "next", "step",
    "do", "while", "until", "loop", "exit", "continue",
    "return", "throw",
    "create", "destroy", "new",
    "call", "trigger", "post", "event", "on",
    "this", "super", "parent",
    "try", "catch", "finally",
    "goto", "halt",
    "type", "from", "within", "forward", "prototypes",
    "variables", "shared", "constant", "external",
    "global", "local", "private", "public", "protected",
    "function", "subroutine", "library", "alias", "readonly", "ref", "byval",
    "array", "instance", "indirect",
    "setnull",
    "select", "insert", "update", "delete", "declare", "cursor",
    "into", "using", "fetch", "execute", "commit", "rollback", "close",
    "open", "null", "true", "false",
    "like", "between", "exists", "distinct", "union", "all", "any",
    "as", "is", "in", "of", "where", "set", "values", "group", "by",
    "order", "having", "asc", "desc", "inner", "outer", "left", "right",
    "join", "on", "upper", "lower", "max", "min", "sum", "count", "avg",
    "nvl", "sysdate", "trunc", "decode", "substr",
}

# Single-character punctuation → token kind.
_PUNCT_KINDS = {
    '(': 'LPAREN',  ')': 'RPAREN',
    '[': 'LBRACKET', ']': 'RBRACKET',
    '{': 'LBRACE',  '}': 'RBRACE',
    '.': 'DOT',     ',': 'COMMA',
    ';': 'SEMI',    ':': 'COLON',
    '?': 'OP',
}
_OPS_2 = {'<>', '<=', '>=', '=='}
_OPS_1 = set('+-*/^=<>!')


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r}, {self.line}:{self.col})"


def tokenize(text: str) -> List[Token]:
    """Tokenize a PowerScript text block into a flat token list."""
    i = 0
    n = len(text)
    line = 1
    col = 1
    out: List[Token] = []

    def emit(kind, value):
        out.append(Token(kind, value, line, col))

    while i < n:
        c = text[i]

        # whitespace (not newline)
        if c in ' \t\r':
            i += 1; col += 1; continue

        # newline
        if c == '\n':
            emit('NL', '\n')
            i += 1; line += 1; col = 1; continue

        # line comment
        if c == '/' and i + 1 < n and text[i + 1] == '/':
            end = text.find('\n', i)
            if end == -1:
                end = n
            emit('COMMENT', text[i:end])
            col += end - i
            i = end
            continue

        # block comment /* ... */ (may span lines)
        if c == '/' and i + 1 < n and text[i + 1] == '*':
            j = i + 2; lc = line; cc = col + 2
            while j < n:
                if text[j] == '*' and j + 1 < n and text[j + 1] == '/':
                    j += 2; cc += 2; break
                if text[j] == '\n':
                    lc += 1; cc = 1
                else:
                    cc += 1
                j += 1
            emit('COMMENT', text[i:j])
            i = j; line = lc; col = cc
            continue

        # string literals '...' or "..."
        if c in "'\"":
            q = c; j = i + 1
            while j < n and text[j] != q:
                if text[j] == '~' and j + 1 < n:
                    j += 2
                elif text[j] == '\n':
                    break  # PB strings don't span lines
                else:
                    j += 1
            s = text[i + 1:j]
            if j < n and text[j] == q:
                j += 1  # skip closing quote
            emit('STR', s)
            col += j - i; i = j
            continue

        # numbers: 123, 1.5, .5
        if c.isdigit() or (c == '.' and i + 1 < n and text[i + 1].isdigit()):
            j = i
            while j < n and text[j].isdigit():
                j += 1
            if j < n and text[j] == '.':
                j += 1
                while j < n and text[j].isdigit():
                    j += 1
            emit('NUM', text[i:j])
            col += j - i; i = j
            continue

        # identifier / keyword / enum (ident + '!')
        if c.isalpha() or c == '_' or ('\u4e00' <= c <= '\u9fa5'):
            j = i
            while j < n and (text[j].isalnum() or text[j] in '_$'
                              or ('\u4e00' <= text[j] <= '\u9fa5')):
                j += 1
            word = text[i:j]
            # enum suffix: IDENT immediately followed by '!'
            if j < n and text[j] == '!':
                emit('ENUM', word + '!')
                j += 1; col += j - i; i = j
                continue
            kind = 'KW' if word.lower() in KEYWORDS else 'IDENT'
            emit(kind, word)
            col += j - i; i = j
            continue

        # :: (DCOLON for `super::create`) — check before :hostvar
        if c == ':' and i + 1 < n and text[i + 1] == ':':
            emit('DCOLON', '::')
            i += 2; col += 2; continue

        # SQL host variable :name
        if c == ':' and i + 1 < n and (text[i + 1].isalpha() or text[i + 1] == '_'):
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] == '_'):
                j += 1
            emit('HOSTVAR', text[i + 1:j])
            col += j - i; i = j
            continue

        # two-char operators
        if c in '<>=' and i + 1 < n and text[i:i + 2] in _OPS_2:
            emit('OP', text[i:i + 2])
            i += 2; col += 2; continue

        # single-char operators
        if c in _OPS_1:
            emit('OP', c)
            i += 1; col += 1; continue

        # punctuation
        if c in _PUNCT_KINDS:
            emit(_PUNCT_KINDS[c], c)
            i += 1; col += 1; continue

        # anything else is junk
        emit('JUNK', c)
        i += 1; col += 1

    out.append(Token('EOF', '', line, col))
    return out