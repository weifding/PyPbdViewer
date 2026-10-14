"""
PBL extractor: bytes -> cleaned PowerScript text + structured block index.

Extraction pipeline (see pbltext.py for the text layer):
  bytes -> printable runs -> per-run GBK decode -> line rejoin -> block scan.

The block scan is a line-level state machine over PowerScript's exported
source layout:

  forward
    global type <obj> from <ancestor> ... end type      <- object header
    type <member> from <ancestor> [within <obj>] ...    <- control/struct member
  end forward
  global type <obj> from <ancestor> [autoinstantiate] ... end type
  type variables ... end variables                      <- instance vars
  shared variables ... end variables
  forward prototypes ... end prototypes                 <- signature list
  public function <type> <name> (<args>)[;<stmt>]       <- function body
  ...
  end function
  on <obj>.[<control>.]<event> ... end on               <- event handler
  event <name>[(<args>)][;<stmt>] ... end event         <- event definition
  function <ret> <name>(<args>) library "<dll>"         <- external decl

Blocks end at their proper `end` keyword; when it never appears (broken
extraction or truncated run), the scanner truncates at the next structural
header or at MAX_BLOCK_LINES and flags the block as truncated.
"""
from __future__ import annotations
import re
import sys
import json
from pathlib import Path

from pbltext import extract_text, clean_line

MAX_BLOCK_LINES = 5000

RE_OBJ = re.compile(
    r"^\s*(global\s+)?type\s+([\w\$\u4e00-\u9fa5]+)\s+from\s+([\w\.]+)"
    r"(?:\s+within\s+([\w\$\u4e00-\u9fa5]+))?",
    re.I,
)
RE_END_TYPE = re.compile(r"^\s*end\s+type\s*$", re.I)
RE_END_FORWARD = re.compile(r"^\s*end\s+forward\s*$", re.I)

RE_VARS = re.compile(r"^\s*(type|shared|global)\s+variables\s*$", re.I)
RE_END_VARS = re.compile(r"^\s*end\s+variables\s*$", re.I)

RE_PROTOTYPES = re.compile(r"^\s*forward\s+prototypes\s*$", re.I)
RE_END_PROTOTYPES = re.compile(r"^\s*end\s+prototypes\s*$", re.I)

RE_ON = re.compile(r"^\s*on\s+([\w\$\u4e00-\u9fa5]+)(?:\.([\w\$\u4e00-\u9fa5]+))?\.([\w\$\u4e00-\u9fa5]+)", re.I)
RE_END_ON = re.compile(r"^\s*end\s+on\s*$", re.I)

RE_EVENT = re.compile(r"^\s*event\s+([\w\$\u4e00-\u9fa5]+)", re.I)
# Def forms: `event name;inline body` or bare `event name`. The `event name(args)`
# form is ambiguous with a trigger call, so it only counts as a def at top level.
RE_EVENT_DEF_TAIL = re.compile(r"^\s*event\s+[\w\$\u4e00-\u9fa5]+\s*(\(|;|$)", re.I)
RE_EVENT_BARE = re.compile(r"^\s*event\s+[\w\$\u4e00-\u9fa5]+\s*(;|$)", re.I)
RE_END_EVENT = re.compile(r"^\s*end\s+event\s*$", re.I)

# access is optional (external decls and some exports omit it);
# return type is optional (subroutines have none).
RE_FUNC = re.compile(
    r"^\s*(?:(public|private|protected|global)\s+)?(function|subroutine)\s+"
    r"(?:([\w\{\}\.]+)\s+)?([\w\$\u4e00-\u9fa5]+)\s*\(",
    re.I,
)
RE_END_FUNC = re.compile(r"^\s*end\s+function\s*$", re.I)
RE_END_SUB = re.compile(r"^\s*end\s+subroutine\s*$", re.I)

RE_LIB_CLAUSE = re.compile(r"\blibrary\b", re.I)


def _paren_balance(s: str) -> int:
    depth = 0
    in_str = None
    i = 0
    while i < len(s):
        c = s[i]
        if c == "~":
            i += 2
            continue
        if in_str:
            if c == in_str:
                in_str = None
        elif c in "\"'":
            in_str = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        i += 1
    return depth


def _is_structural(line: str, patterns) -> bool:
    """A line that can never appear inside the block currently being collected."""
    return any(p.match(line) for p in patterns)


# Truncation triggers per block kind. Content lines of `forward prototypes`
# are signatures and of `variables` are declarations, so RE_FUNC cannot be a
# trigger inside prototypes; everything else recovers on any new header.
TR_FUNC = (RE_OBJ, RE_ON, RE_FUNC, RE_VARS, RE_PROTOTYPES, RE_EVENT_BARE)
TR_EVENT = (RE_OBJ, RE_ON, RE_FUNC, RE_VARS, RE_PROTOTYPES, RE_EVENT_BARE)
TR_PROTOTYPES = (RE_OBJ, RE_ON, RE_VARS)
TR_VARIABLES = (RE_OBJ, RE_ON, RE_FUNC, RE_PROTOTYPES, RE_EVENT_BARE)


def _cut_statement(line: str) -> str:
    """Cut a header at the first `;` outside string literals (PB inline body)."""
    in_str = None
    i = 0
    while i < len(line):
        c = line[i]
        if c == "~":
            i += 2
            continue
        if in_str:
            if c == in_str:
                in_str = None
        elif c in "\"'":
            in_str = c
        elif c == ";":
            return line[:i]
        i += 1
    return line


def _collect_block(lines, i, end_re, patterns, max_lines=MAX_BLOCK_LINES):
    """Collect lines[i:] until end_re; truncate at next structural header.

    Returns (block_text, next_index, truncated, reason).
    """
    start = i
    body = [lines[i]]
    j = i + 1
    n = len(lines)
    while j < n:
        if end_re.match(lines[j]):
            body.append(lines[j])
            j += 1
            return "\n".join(body), j, False, ""
        if _is_structural(lines[j], patterns):
            return "\n".join(body), j, True, "next-structure"
        if j - start >= max_lines:
            return "\n".join(body), j, True, "max-lines"
        body.append(lines[j])
        j += 1
    return "\n".join(body), j, True, "eof"


def _join_header(lines, i, max_lines=10):
    """Accumulate a possibly multi-line signature until parens balance.

    The statement cut (`;` = start of the inline body) is applied before the
    balance check so a `(` inside a trailing comment cannot keep it open.
    """
    parts = []
    j = i
    while j < len(lines) and j - i < max_lines:
        parts.append(lines[j])
        joined = _cut_statement(" ".join(parts))
        if "(" in joined and _paren_balance(joined) <= 0:
            return joined, j + 1
        j += 1
    return _cut_statement(" ".join(parts)), i + 1


def extract_blocks(lines: list[str]) -> dict:
    """Pure step: cleaned PS lines -> {objects, members, blocks}."""
    objects: list[dict] = []
    members: list[dict] = []
    blocks: list[dict] = []
    seen_obj: set[str] = set()
    cur_obj: str | None = None
    cur_member: str | None = None  # last `type X from ...` control/member decl
    i = 0
    n = len(lines)

    def emit(kind, obj, name, text, j_next, truncated, reason, **extra):
        blocks.append({
            "kind": kind,
            "object": obj,
            "name": name,
            "text": text,
            "truncated": truncated,
            "reason": reason,
            **extra,
        })
        return j_next

    while i < n:
        line = lines[i]

        m = RE_OBJ.match(line)
        if m:
            is_global, name, ancestor, within = m.group(1), m.group(2), m.group(3), m.group(4)
            body, j, trunc, reason = _collect_block(lines, i, RE_END_TYPE, TR_VARIABLES)
            entry = {
                "name": name,
                "ancestor": ancestor.lower(),
                "within": within,
                "line": i + 1,
                "type_text": body,
            }
            if is_global and not within:
                if name in seen_obj:
                    # forward + main decl: keep the richer type block
                    prev = next(o for o in objects if o["name"] == name)
                    if len(entry["type_text"]) > len(prev["type_text"]):
                        prev["type_text"] = entry["type_text"]
                else:
                    seen_obj.add(name)
                    objects.append(entry)
                cur_obj = name
                cur_member = None
            else:
                entry["member_of"] = within or cur_obj
                members.append(entry)
                # bare `event` defs that follow belong to this control
                cur_member = name
            i = j
            continue

        m = RE_ON.match(line)
        if m:
            text, j, trunc, reason = _collect_block(lines, i, RE_END_ON, TR_EVENT)
            emit("event", m.group(1), m.group(3), text, j, trunc, reason,
                 control=m.group(2), header=line)
            i = j
            continue

        if RE_EVENT_DEF_TAIL.match(line):
            m = RE_EVENT.match(line)
            text, j, trunc, reason = _collect_block(lines, i, RE_END_EVENT, TR_EVENT)
            # a bare `event` def sits right after its owner's `type ... end type`
            emit("event", cur_obj or "<global>", m.group(1), text, j, trunc, reason,
                 control=cur_member, header=line)
            i = j
            continue

        if RE_FUNC.match(line):
            header, j = _join_header(lines, i)
            m = RE_FUNC.match(header)
            if not m:
                i += 1
                continue
            access, kind, rettype, name = (
                (m.group(1) or "").lower(), m.group(2).lower(), m.group(3), m.group(4)
            )
            common = dict(control=None, header=header, access=access)
            if RE_LIB_CLAUSE.search(_cut_statement(header)):
                # external function/subroutine decl: one line, no body
                emit(kind, cur_obj or "<global>", name, header, j, False, "", external=True, **common)
                i = j
                continue
            end_re = RE_END_FUNC if kind == "function" else RE_END_SUB
            text, j2, trunc, reason = _collect_block(lines, j - 1, end_re, TR_FUNC)
            # _collect_block includes the first line; prepend joined header
            if j - 1 > i:
                text = "\n".join([*lines[i:j - 1], text])
            emit(kind, cur_obj or "<global>", name, text, j2, trunc, reason,
                 external=False, **common)
            i = j2
            continue

        m = RE_VARS.match(line)
        if m:
            text, j, trunc, reason = _collect_block(lines, i, RE_END_VARS, TR_VARIABLES)
            emit("variables", cur_obj or "<global>", m.group(1).lower(), text, j,
                 trunc, reason, control=None, header=line)
            i = j
            continue

        if RE_PROTOTYPES.match(line):
            text, j, trunc, reason = _collect_block(lines, i, RE_END_PROTOTYPES, TR_PROTOTYPES)
            emit("prototypes", cur_obj or "<global>", "prototypes", text, j,
                 trunc, reason, control=None, header=line)
            i = j
            continue

        i += 1

    return _dedupe({"objects": objects, "members": members, "blocks": blocks})


def _dedupe(result: dict) -> dict:
    """A PBL stores each object's text twice (compiled section + source
    stream); collapse the copies, keeping the most complete text.
    Overloaded functions are distinct signatures and both survive."""
    seen_m: dict = {}
    for m in result["members"]:
        k = (m.get("member_of"), m["name"])
        prev = seen_m.get(k)
        if prev is None or len(m.get("type_text", "")) > len(prev.get("type_text", "")):
            seen_m[k] = m
    result["members"] = list(seen_m.values())

    seen_b: dict = {}
    order: list = []
    for b in result["blocks"]:
        if b["kind"] in ("function", "subroutine"):
            hdr = re.sub(r"\s+", " ", (b.get("header") or b["text"].split("\n")[0]).lower())
            k = (b["object"], b["kind"], b["name"], hdr)
        elif b["kind"] == "event":
            k = (b["object"], b.get("control"), b["kind"], b["name"])
        else:
            k = (b["object"], b["kind"], b["name"])
        prev = seen_b.get(k)
        if prev is None:
            seen_b[k] = b
            order.append(k)
        elif len(b["text"]) > len(prev["text"]):
            seen_b[k] = b
    result["blocks"] = [seen_b[k] for k in order]
    return result


def extract_from_pbl(pbl_path: Path, out_dir: Path) -> dict:
    data = pbl_path.read_bytes()
    cleaned = extract_text(data, min_run=10)

    out_dir.mkdir(parents=True, exist_ok=True)
    ps_file = out_dir / (pbl_path.stem + ".ps.txt")
    ps_file.write_text(cleaned, encoding="utf-8")

    result = extract_blocks(cleaned.split("\n"))
    idx = {
        "pbl": str(pbl_path),
        "size": len(data),
        "objects": result["objects"],
        "members": result["members"],
        "blocks": result["blocks"],
    }
    idx_file = out_dir / (pbl_path.stem + ".json")
    idx_file.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    return idx


def main():
    if len(sys.argv) < 3:
        print("usage: extract_pbl.py <pbl> <out_dir>")
        sys.exit(1)
    pbl = Path(sys.argv[1])
    out = Path(sys.argv[2])
    idx = extract_from_pbl(pbl, out)
    kinds: dict[str, int] = {}
    trunc = 0
    for b in idx["blocks"]:
        kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
        trunc += 1 if b["truncated"] else 0
    print(f"pbl={pbl.name} objects={len(idx['objects'])} members={len(idx['members'])} "
          f"blocks={len(idx['blocks'])} truncated={trunc}")
    print(f"  kinds: {kinds}")
    for b in idx["blocks"][:20]:
        flag = " TRUNC" if b["truncated"] else ""
        print(f"  [{b['kind']:11s}] {b['object']}.{b['name']}{flag}")


if __name__ == "__main__":
    main()
