"""
Block diagnostics for extracted PBL JSON: size distribution, truncation
reasons, and the biggest blocks — the QA view used to tune extract_pbl's
truncation rules (giant blocks are extraction artifacts, not real functions).

CLI:
  python tools/diag_blocks.py <decompiled.json> [<decompiled.json> ...]
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


def diag(idx: dict) -> None:
    blocks = idx.get("blocks", [])
    lens = sorted((len(b["text"].split("\n")), b["kind"], b["object"], b["name"])
                  for b in blocks)
    kinds: dict[str, int] = {}
    reasons: dict[str, int] = {}
    for b in blocks:
        kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
        if b.get("truncated"):
            reasons[b.get("reason") or "?"] = reasons.get(b.get("reason") or "?", 0) + 1
    print(f"objects={len(idx.get('objects', []))} members={len(idx.get('members', []))} "
          f"blocks={len(blocks)}")
    print(f"  kinds: {kinds}")
    print(f"  truncated: {sum(reasons.values())} {reasons}")
    if lens:
        print("  biggest blocks:")
        for n, kind, obj, name in lens[-5:][::-1]:
            print(f"    {n:6d} lines  [{kind}] {obj}.{name}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for arg in sys.argv[1:]:
        p = Path(arg)
        print(f"=== {p}")
        diag(json.loads(p.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
