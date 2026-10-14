"""
PyPbdViewer — minimal PBD/PBL decompiler.

A PBD/PBL starts with `HDR*PowerBuilder` and contains a directory of entries
like `name.type` where type is one of:
  .dwo  DataWindow object (binary descriptor)
  .win  Window (binary)
  .udo  User Object definition (binary)
  .fun  Global function definition
  .sru/.srf/.srw  source streams (only present in PBL, stripped in PBD)

We don't fully decode the binary; we:
  1. Parse the entry table to enumerate every object name and its kind.
  2. Extract all printable text runs (SQL, messages, comments) so they can be
     emitted as documentation inside the TS stubs.

Outputs a JSON index + a .ps.txt text dump for downstream conversion.
"""
from __future__ import annotations
import os, re, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "converter"))
from pbltext import extract_runs, decode_run as decode, is_text_byte as is_text


MAGIC = b"HDR*PowerBuilder"

# Object suffix -> kind we want to surface in TS.
SUFFIX_KIND = {
    ".dwo": "datawindow",
    ".win": "window",
    ".udo": "userobject",
    ".fun": "globalfunction",
    ".sru": "userobject",
    ".srf": "globalfunction",
    ".srw": "window",
    ".prp": "properties",
    ".bin": "binary",
}


# Recognise an entry name like `w_xxfs.win` or `n_hiscomsys.sru`.
RE_ENTRY = re.compile(r"^([A-Za-z_][A-Za-z0-9_\u4e00-\u9fa5]{0,60})(\.[A-Za-z]{2,4})$")


def parse_entries(runs):
    """Return list of (name, suffix, kind, offset)."""
    entries = []
    seen = set()
    for off, r in runs:
        s = decode(r).strip()
        m = RE_ENTRY.match(s)
        if not m:
            continue
        name, suffix = m.group(1), m.group(2).lower()
        if suffix not in SUFFIX_KIND:
            continue
        key = (name, suffix)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"name": name, "suffix": suffix,
                        "kind": SUFFIX_KIND[suffix], "offset": off})
    return entries


def extract_sql_strings(runs):
    """Pull SQL-looking statements out of text runs."""
    sqls = []
    for off, r in runs:
        s = decode(r)
        if re.search(r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b", s, re.I):
            sqls.append({"offset": off, "text": s.strip()})
    return sqls


def decompile(pbd_path: Path, out_dir: Path):
    data = pbd_path.read_bytes()
    if not data.startswith(MAGIC):
        raise ValueError(f"{pbd_path} is not a PowerBuilder library")

    runs = extract_runs(data)
    entries = parse_entries(runs)
    sqls = extract_sql_strings(runs)

    # Build cleaned text dump.
    text = "\n".join(decode(r) for _, r in runs)

    out_dir.mkdir(parents=True, exist_ok=True)
    txt_path = out_dir / (pbd_path.stem + ".ps.txt")
    txt_path.write_text(text, encoding="utf-8")

    idx = {
        "file": str(pbd_path),
        "size": len(data),
        "version": data[0x12:0x16].decode("ascii", errors="replace"),
        "entries": entries,
        "sql": sqls,
    }
    idx_path = out_dir / (pbd_path.stem + ".json")
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    return idx


def main():
    if len(sys.argv) < 3:
        print("usage: pbdview.py <pbd|pbl> <out_dir>")
        sys.exit(1)
    idx = decompile(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"{Path(sys.argv[1]).name}: size={idx['size']} entries={len(idx['entries'])} sql={len(idx['sql'])}")
    for e in idx["entries"][:30]:
        print(f"  {e['kind']:14s}  {e['name']}{e['suffix']}  @{e['offset']}")


if __name__ == "__main__":
    main()
