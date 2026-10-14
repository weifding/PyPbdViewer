"""Post-process VM pseudo-C into legal-ish PB syntax for psparser."""
import re


def vm_to_pb(vm_output: str) -> str:
    lines = vm_output.splitlines()
    # collect goto targets
    targets = set()
    for ln in lines:
        m = re.search(r'goto\s+([0-9A-Fa-f]{4,})', ln)
        if m:
            targets.add(m.group(1).upper())
    # rewrite
    out = []
    for ln in lines:
        # normalize goto offsets to labels
        ln = re.sub(r'goto\s+([0-9A-Fa-f]{4,})', lambda m: f'goto L{m.group(1).upper()}', ln)
        # if not cond then goto → if not cond then goto
        out.append(ln)
    # insert labels at offsets (we don't know real offsets, so just append)
    for t in sorted(targets):
        out.append(f'label L{t}')
    return '\n'.join(out)


if __name__ == '__main__':
    sample = '''if a > b then goto 01A2;
a = b + c;
goto 01A5;
:01A2
return a;
:01A5
return;'''
    print(vm_to_pb(sample))
