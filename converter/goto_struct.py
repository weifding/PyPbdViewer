"""Goto elimination for pseudo-PB.

Turns flat psparser statement lists containing the conditional-goto form
    if <cond> then goto L;   (<- If(cond, then=[Goto(L)]) from psparser)
into structured if blocks.  Semantic identity:
    `if (cond) goto L;  <stmts up to L>`
is equivalent to
    `if (!cond) { <stmts up to L> }`
because when cond is true we jump over those stmts (L is the jump target /
else endpoint), and when cond is false we execute them.

So a forward conditional goto is replaced by an If whose condition is the
inversion of the original, and whose body is the skipped region (recursively
structured).  Unconditional Gotos and any shape we cannot prove stay as-is
(tsbuilder renders them as comments), so a wrong guess can never corrupt
generated TS.
"""

from __future__ import annotations
from typing import List

from psparser import Node, If, Goto, Label, UnaryOp


def _invert(cond: Node) -> Node:
    """Return !cond. `not X` -> X; anything else -> `not (...)`."""
    if isinstance(cond, UnaryOp) and cond.op == 'not':
        return cond.operand
    return UnaryOp(op='not', operand=cond)


def _region(stmts: List[Node], label_idx: dict, a: int, b: int) -> List[Node]:
    """Process stmts[a:b] (absolute indices into `stmts`, matching label_idx)."""
    out: List[Node] = []
    i = a
    while i < b:
        s = stmts[i]
        is_cond_goto = (
            isinstance(s, If)
            and len(s.then) == 1 and isinstance(s.then[0], Goto)
            and not s.elseifs and not s.else_
        )
        if is_cond_goto:
            T = s.then[0].label
            ti = label_idx.get(T, -1)
            if ti > i and ti < b:
                # target inside this region: skipped body is stmts[i+1..ti]
                body = stmts[i + 1:ti]
                out.append(If(cond=_invert(s.cond),
                              then=_region(stmts, label_idx, i + 1, ti)))
                i = ti + 1
                continue
            if ti > i:
                # target beyond this region: whole rest of region is skipped
                out.append(If(cond=_invert(s.cond),
                              then=_region(stmts, label_idx, i + 1, b)))
                i = b
                continue
        # unresolved / unconditional goto / label / anything else: keep verbatim
        out.append(s)
        i += 1
    return out


def structurize(stmts: List[Node]) -> List[Node]:
    if not any(isinstance(s, (Goto, Label)) for s in stmts):
        return stmts
    label_idx = {s.name: k for k, s in enumerate(stmts) if isinstance(s, Label)}
    return _region(stmts, label_idx, 0, len(stmts))
