"""
Shared text-run extraction utilities for PowerBuilder library files (PBL/PBD).

PBL/PBD source is interleaved with binary markers. Extraction walks raw bytes,
accumulates printable runs (ASCII + GBK byte pairs), and decodes them per run.
Runs are joined with newlines, which splits statements at binary boundaries;
`rejoin_lines` stitches those splits back together using two signals:
  1. an inline `DAT*` marker (its removal leaves a mid-token line break), and
  2. unbalanced quotes / parentheses (a run ended mid-string or mid-argument).
"""
from __future__ import annotations

import re

DAT_MARKER = "DAT*"


def is_text_byte(b: int) -> bool:
    return 0x20 <= b < 0x7F or b in (0x09, 0x0A, 0x0D)


# Printable ASCII run or a GBK lead/trail byte pair, as adjacent matches.
_RUN_RE = re.compile(rb"[\x20-\x7e\x09\x0a\x0d]+|[\x81-\xfe][\x40-\xfe]")


def extract_runs(data: bytes, min_run: int = 6):
    """Return list of (offset, bytes) printable runs; GBK pairs stay intact.

    Equivalent to a byte-by-byte walk (text bytes and GBK pairs continue a
    run; any other byte flushes it) but scanning is done in C via regex.
    """
    runs = []
    cur = bytearray()
    start = 0
    for m in _RUN_RE.finditer(data):
        s, e = m.span()
        if cur and s == start + len(cur):
            cur += m.group()
        else:
            if len(cur) >= min_run:
                runs.append((start, bytes(cur)))
            cur = bytearray(m.group())
            start = s
    if len(cur) >= min_run:
        runs.append((start, bytes(cur)))
    return runs


def decode_run(b: bytes) -> str:
    # Byte-level heuristic: count high-byte patterns.
    # GBK: lead byte 0x81-0xFE, trail byte 0x40-0xFE (excluding 0x7F).
    # UTF-8: 2-byte (110xxxxx 10xxxxxx), 3-byte (1110xxxx 10xxxxxx 10xxxxxx).
    gbk_pairs = 0
    utf8_seq = 0
    i = 0
    while i < len(b):
        c = b[i]
        if 0x81 <= c <= 0xFE and i + 1 < len(b):
            nxt = b[i + 1]
            if 0x40 <= nxt <= 0xFE and nxt != 0x7F:
                gbk_pairs += 1
                i += 2
                continue
        if 0xC2 <= c <= 0xDF and i + 1 < len(b) and 0x80 <= b[i+1] <= 0xBF:
            utf8_seq += 1
            i += 2
            continue
        if 0xE0 <= c <= 0xEF and i + 2 < len(b) and 0x80 <= b[i+1] <= 0xBF and 0x80 <= b[i+2] <= 0xBF:
            utf8_seq += 1
            i += 3
            continue
        i += 1
    # If GBK pairs dominate, decode as GBK; if UTF-8 sequences dominate, decode as UTF-8.
    if gbk_pairs > utf8_seq and gbk_pairs >= 2:
        try:
            return b.decode("gbk")
        except UnicodeDecodeError:
            pass
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        return b.decode("gbk")
    except UnicodeDecodeError:
        pass
    s = b.decode("latin-1", errors="replace")
    if _looks_like_mojibake(s):
        try:
            return s.encode("latin-1", errors="ignore").decode("gbk", errors="replace")
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    return s


def _looks_like_mojibake(s: str) -> bool:
    """Heuristic: >=3 chars in 0xC0-0xFF range in a short string."""
    if not s: return False
    hi = sum(1 for c in s if 0xC0 <= ord(c) <= 0xFF)
    return hi >= 3 and hi / max(1, len(s)) < 0.5


def strip_marker(line: str) -> tuple[str, bool]:
    """Remove `DAT*` binary markers. Returns (cleaned, had_marker)."""
    if DAT_MARKER in line:
        return line.replace(DAT_MARKER, ""), True
    return line, False


def unbalanced(s: str) -> bool:
    """True if the line ends inside a string literal or an open parenthesis."""
    in_str = None
    depth = 0
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "~":  # PB escape char: skip the next char
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
    return in_str is not None or depth > 0


# A line starting with one of these can never be the continuation of a broken
# statement: it is a fresh statement / block boundary. Merging across it would
# swallow terminators like `end on` / `end function` into the previous line.
RE_LINE_KEYWORD = re.compile(
    r"^(?:end|forward|type|event|on|public|private|protected|global|function|subroutine|"
    r"if|elseif|else|choose|case|for|do|while|loop|until|next|step|to|try|catch|throw|"
    r"continue|exit|return|commit|rollback|declare|fetch|open|close|call|create|destroy|"
    r"halt|goto|setnull|this|super|parent)\b",
    re.I,
)


def rejoin_lines(lines: list[str], max_chain: int = 4) -> list[str]:
    """Stitch line breaks introduced at binary-run boundaries back together.

    - Break right after a `DAT*` marker: merge with the *next* line without a
      separator (the break fell mid-token, e.g. `bDAT*` + `oolean` -> `boolean`).
    - Line with unbalanced quotes/parens (and not a comment line): merge with a
      space (the break fell between tokens inside a statement).

    At most `max_chain` lines are merged into one logical line: a stray quote
    in junk text must not swallow the whole file (and re-scanning a growing
    buffer would be quadratic).
    """
    out: list[str] = []
    buf: str | None = None
    buf_from_marker = False
    chain = 0
    for raw in lines:
        s = raw.rstrip("\r")
        s, had_marker = strip_marker(s)
        if buf is None:
            buf, buf_from_marker = s, had_marker
            continue
        is_comment = buf.lstrip().startswith("//") or buf.lstrip().startswith("*")
        starts_fresh = bool(RE_LINE_KEYWORD.match(s))
        if chain < max_chain and not starts_fresh and buf_from_marker:
            buf = buf + s
        elif chain < max_chain and not starts_fresh and unbalanced(buf) and not is_comment:
            buf = buf + " " + s
        else:
            out.append(buf)
            buf, buf_from_marker, chain = s, had_marker, 0
            continue
        # merged: the merged tail may itself end at another marker break
        buf_from_marker = had_marker
        chain += 1
    if buf is not None:
        out.append(buf)
    return out


def clean_line(line: str) -> str:
    """Normalise PB escape sequences for use inside TS comments / literals."""
    s = line
    s = s.replace(DAT_MARKER, "")
    s = s.replace("~r~n", "\\n")
    s = s.replace("~r", "\\r")
    s = s.replace("~n", "\\n")
    s = s.replace("~t", "\\t")
    s = s.replace("~~", "~")
    return s.rstrip()


def extract_text(data: bytes, min_run: int = 8) -> str:
    """Full pipeline: bytes -> runs -> decoded -> split into true lines ->
    rejoined -> one string.

    A run can contain embedded newlines (CR/LF are text bytes), so each run's
    text is split on `\\n` before rejoining; run boundaries without a newline
    are the mid-statement breaks `rejoin_lines` repairs.
    """
    lines: list[str] = []
    for _, r in extract_runs(data, min_run=min_run):
        lines.extend(decode_run(r).split("\n"))
    return "\n".join(rejoin_lines(lines))
