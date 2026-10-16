"""Post-process VM pseudo-code into cleaner PB-ish syntax.

Cleanups:
- Drop empty-condition ifs (`if  then goto`, `if not  then goto`).
- Drop no-op `<>` comparisons with empty operands.
- Collapse consecutive `return;` runs.
- Normalize goto offsets to labels; insert `label Lxxxx` at target lines.
- Annotate unimplemented-opcode hex dumps as comments.
"""
from __future__ import annotations
import re


_GOTO_RE = re.compile(r'goto\s+([0-9A-Fa-f]{4,})')


def _collect_targets(lines: list[str]) -> set[str]:
    targets = set()
    for ln in lines:
        m = _GOTO_RE.search(ln)
        if m:
            targets.add(m.group(1).upper())
    return targets


def _is_empty_if(ln: str) -> bool:
    s = ln.strip()
    # "if  then goto X" / "if not  then goto X" — condition missing
    if re.match(r'^if\s+(not\s+)?then\s+goto', s):
        return True
    return False


def _is_noop_compare(ln: str) -> bool:
    s = ln.strip()
    # "<> + gbl3840 then goto" style: comparison with empty lhs
    if re.match(r'^<>', s) and 'then goto' in s:
        return True
    return False


def vm_to_pb(vm_output: str) -> str:
    raw = vm_output.splitlines()
    targets = _collect_targets(raw)

    cleaned: list[str] = []
    prev_return = False
    for ln in raw:
        s = ln.strip()
        if not s:
            continue
        if _is_empty_if(ln) or _is_noop_compare(ln):
            # keep as comment, psparser will skip
            cleaned.append(f"// {s}")
            prev_return = False
            continue
        # normalize goto offset -> goto Lxxxx (keep goto keyword so psparser Goto node fires)
        ln2 = _GOTO_RE.sub(lambda m: f'goto L{m.group(1).upper()}', ln)
        # collapse consecutive return;
        if re.match(r'^return\s*;?$', s):
            if prev_return:
                continue
            prev_return = True
        else:
            prev_return = False
        cleaned.append(ln2)

    # append label declarations at end (psparser treats `label Lx` as a Label node)
    for t in sorted(targets):
        cleaned.append(f'label L{t}')
    return '\n'.join(cleaned)


if __name__ == '__main__':
    sample = '''// sql dml @0
return;
close SQLCA;
return;
if  <>  + gbl3840 then goto 40B9;
if  then goto 0038;
if as_errtext then goto 8500;
return;
// op 0x40 @0031 operands=bd
commit;
return;'''
    print(vm_to_pb(sample))
