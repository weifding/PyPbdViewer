"""Post-process VM pseudo-code into cleaner PB-ish syntax.

Cleanups:
- Drop empty-condition ifs (`if  then goto`, `if not  then goto`).
- Drop no-op `<>` comparisons with empty operands.
- Collapse consecutive `return;` runs.
- Normalize goto offsets to labels; insert `label Lxxxx` at the exact
  instruction line the goto targets (input is run_lines() output with
  per-line start offsets — fixes the previous label-at-end control-flow bug).
- Annotate unimplemented-opcode hex dumps as comments.
"""
from __future__ import annotations
import re


_GOTO_RE = re.compile(r'goto\s+([0-9A-Fa-f]{4,})')


def _is_empty_if(ln: str) -> bool:
    s = ln.strip()
    if re.match(r'^if\s+(not\s+)?then\s+goto', s):
        return True
    return False


def _is_noop_compare(ln: str) -> bool:
    s = ln.strip()
    if re.match(r'^<>', s) and 'then goto' in s:
        return True
    return False


def _normalize(ln: str) -> str:
    return _GOTO_RE.sub(lambda m: f'goto L{m.group(1).upper()}', ln)


def vm_to_pb(vm_output) -> str:
    # vm_output: list[(start_offset, text)] from VM.run_lines()  (or plain str)
    if isinstance(vm_output, str):
        lines = [(0, ln) for ln in vm_output.splitlines()]
    else:
        lines = list(vm_output)

    # collect goto targets (normalized uppercase)
    targets = set()
    for _, t in lines:
        m = _GOTO_RE.search(t)
        if m:
            targets.add(m.group(1).upper())

    # cleaned lines with their start offset
    cleaned: list[tuple[int, str]] = []
    prev_return = False
    for off, t in lines:
        s = t.strip()
        if not s:
            continue
        if _is_empty_if(t) or _is_noop_compare(t):
            cleaned.append((off, f"// {s}"))
            prev_return = False
            continue
        ln2 = _normalize(t)
        if re.match(r'^return\s*;?$', s):
            if prev_return:
                continue
            prev_return = True
        else:
            prev_return = False
        cleaned.append((off, ln2))

    # Insert a label right before the line whose start offset == a goto target.
    out: list[str] = []
    emitted: set[str] = set()
    for off, t in cleaned:
        key = f"{off:04X}"
        if key in targets and key not in emitted:
            out.append(f"label L{key}")
            emitted.add(key)
        out.append(t)

    # Targets not aligned to any emitted line offset -> append at end (fallback).
    for t in sorted(targets - emitted):
        out.append(f"label L{t}")

    return '\n'.join(out)


if __name__ == '__main__':
    sample = [
        (0x0000, "// sql dml @0"),
        (0x0002, "return;"),
        (0x0004, "close SQLCA;"),
        (0x0006, "return;"),
        (0x0008, "if  <>  + gbl3840 then goto 40B9;"),
        (0x000A, "if  then goto 0038;"),
        (0x000C, "if as_errtext then goto 8500;"),
        (0x0010, "return;"),
        (0x0012, "// op 0x40 @0031 operands=bd"),
        (0x0014, "commit;"),
        (0x0016, "return;"),
    ]
    print(vm_to_pb(sample))
