"""
Batch driver: extract + convert PBL/PBD libraries to TypeScript.

  python converter/batch.py --input D:\\ynsoft --out out \\
      [--report notes/convert-report.md] [--no-pbd] [--no-tsc] \\
      [--exclude 作废 --exclude 副本] [--limit N]

- PBL -> extract_pbl.extract_from_pbl + convert.convert
      (signatures typed, bodies preserved as TODO comments)
- PBD -> pbdview.decompile + convert_pbd.emit_for_idx
      (object list + stubs; SQL preserved)

Layout under --out:
  decompiled/<parent>__<stem>/   extracted .ps.txt + .json
  ts/<parent>__<stem>/           generated .ts per object
  ts/                            shared tsconfig.json + node_modules

No hardcoded corpus or toolchain paths: node/npx must be on PATH.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))  # repo root (pbdview.py)
from extract_pbl import extract_from_pbl
from convert import convert, PB_RUNTIME
from pbdview import decompile as decompile_pbd
from convert_pbd import emit_for_idx

DEFAULT_EXCLUDE = ("作废", "副本")


def collect(inputs: list[str], ext: str, exclude: tuple[str, ...]) -> list[Path]:
    out = []
    for raw in inputs:
        p = Path(raw)
        if p.is_file() and p.suffix.lower() == f".{ext}":
            out.append(p)
        elif p.is_dir():
            out.extend(p.rglob(f"*.{ext}"))
    res = []
    for p in out:
        if any(tok in str(p) for tok in exclude):
            continue
        res.append(p)
    return sorted(set(res))


def process_pbl(p: Path, dec_root: Path, ts_root: Path) -> dict:
    row = {"file": str(p), "kind": "pbl", "size": p.stat().st_size}
    sub = f"{p.parent.name}__{p.stem}"
    try:
        idx = extract_from_pbl(p, dec_root / sub)
        stats = convert(dec_root / sub / f"{p.stem}.json", ts_root / sub)
        row.update(stats)
        row["status"] = "ok"
    except Exception as e:
        row["status"] = f"error: {e}"
    return row


def _enrich_pcode(idx: dict, pbd_path: Path) -> None:
    """Attach parsed pcode funcs to each entry so convert_pbd can VM-transpile.

    pbdview.decompile only yields entry metadata; the actual function p-code
    lives in the binary entry payload. Walk the real layout and attach
    per-object funcs (pcode_hex/locals/str_pool_hex) keyed by object name.
    """
    try:
        from pbd_structured import parse_pbd as walk_pbd
        from pbd_entry_structured import parse_entry
    except Exception:
        return
    by_name = {}
    for pe in walk_pbd(pbd_path):
        base = pe.name.rsplit(".", 1)[0]
        by_name.setdefault(base, []).append(pe)
    for e in idx.get("entries", []):
        name = e.get("name")
        for pe in by_name.get(name, []):
            try:
                r = parse_entry(pe.raw)
            except Exception:
                continue
            funcs = []
            refs = []
            for o in r.get("objects", []):
                funcs.extend(o.get("funcs", []))
                refs.extend(o.get("ref_names", []))
            if funcs:
                e["funcs"] = funcs
            if refs:
                e["ref_names"] = refs


def process_pbd(p: Path, dec_root: Path, ts_root: Path) -> dict:
    row = {"file": str(p), "kind": "pbd", "size": p.stat().st_size}
    sub = f"pbd__{p.parent.name}__{p.stem}"
    try:
        idx = decompile_pbd(p, dec_root / sub)
        # Attach real p-code funcs so emit_for_idx can VM-transpile bodies.
        _enrich_pcode(idx, p)
        # Also dump raw per-entry payload (ported from C# PbdViewer PbFile.cs).
        try:
            from pbd_structured import save_entries as _save_structured
            n_raw = _save_structured(p, dec_root / sub / "entries")
            row["raw_entries"] = n_raw
        except Exception:
            pass
        # Structured source dump (ported from C# PbEntry.cs).
        try:
            from pbd_entry import save_source_dump as _save_source
            _save_source_dump = _save_source
            n_src = _save_source_dump(p, dec_root / sub / "source")
            row["source_entries"] = n_src
        except Exception:
            pass
        ts_sub = ts_root / sub
        emit_for_idx(idx, ts_sub)
        (ts_sub / "pb-runtime.ts").write_text(PB_RUNTIME, encoding="utf-8")
        row.update({"entries": len(idx.get("entries", [])),
                    "sql": len(idx.get("sql", [])), "status": "ok"})
    except Exception as e:
        row["status"] = f"error: {e}"
    return row


def run_tsc(ts_root: Path) -> tuple[int, str]:
    """Type-check the whole output tree with one shared tsconfig."""
    (ts_root / "tsconfig.json").write_text(json.dumps({
        "compilerOptions": {
            "target": "ES2020",
            "module": "commonjs",
            "strict": False,
            "noImplicitAny": False,
            "esModuleInterop": True,
            "skipLibCheck": True,
            "forceConsistentCasingInFileNames": True,
            "noEmit": True,
        },
        "include": ["**/*.ts"],
    }, indent=2), encoding="utf-8")
    pkg = ts_root / "package.json"
    if not pkg.exists():
        pkg.write_text(json.dumps({"name": "pbtots-out", "private": True}, indent=2),
                       encoding="utf-8")
    if not (ts_root / "node_modules" / "typescript").exists():
        subprocess.run("npm install --no-audit --no-fund typescript@4.9",
                       cwd=str(ts_root), check=True, shell=True)
    r = subprocess.run("npx tsc --noEmit", cwd=str(ts_root),
                       capture_output=True, text=True, shell=True,
                       env={**os.environ, "NODE_OPTIONS": "--max-old-space-size=12288"})
    return r.returncode, r.stdout + r.stderr


def main():
    ap = argparse.ArgumentParser(description="PBL/PBD -> TypeScript batch converter")
    ap.add_argument("--input", action="append", required=True,
                    help="PBL/PBD file or directory (repeatable)")
    ap.add_argument("--out", required=True, help="output root")
    ap.add_argument("--report", help="markdown report path")
    ap.add_argument("--exclude", action="append", default=list(DEFAULT_EXCLUDE),
                    help="path substrings to skip (default: 作废 副本)")
    ap.add_argument("--no-pbd", action="store_true", help="skip .pbd files")
    ap.add_argument("--no-tsc", action="store_true", help="skip the tsc pass")
    ap.add_argument("--limit", type=int, default=0, help="cap each kind for smoke runs")
    args = ap.parse_args()

    out = Path(args.out)
    dec_root = out / "decompiled"
    ts_root = out / "ts"
    dec_root.mkdir(parents=True, exist_ok=True)
    ts_root.mkdir(parents=True, exist_ok=True)

    pbls = collect(args.input, "pbl", tuple(args.exclude))
    pbds = [] if args.no_pbd else collect(args.input, "pbd", tuple(args.exclude))
    if args.limit:
        pbls, pbds = pbls[:args.limit], pbds[:args.limit]
    print(f"Discovered {len(pbls)} PBLs, {len(pbds)} PBDs")

    rows = []
    for i, p in enumerate(pbls):
        rows.append(process_pbl(p, dec_root, ts_root))
        if (i + 1) % 25 == 0:
            print(f"  PBL [{i+1}/{len(pbls)}]")
    for i, p in enumerate(pbds):
        rows.append(process_pbd(p, dec_root, ts_root))
        if (i + 1) % 500 == 0:
            print(f"  PBD [{i+1}/{len(pbds)}]")

    ok = sum(1 for r in rows if r.get("status") == "ok")
    err = [r for r in rows if r.get("status") != "ok"]
    print(f"done: ok={ok} error={len(err)}")
    for r in err[:20]:
        print(f"  FAIL {r['file']}: {r['status']}")

    if not args.no_tsc:
        print("Running tsc --noEmit ...")
        code, outp = run_tsc(ts_root)
        (out / "tsc_output.txt").write_text(outp, encoding="utf-8")
        errs = [l for l in outp.splitlines() if "error TS" in l]
        print(f"tsc exit={code} errors={len(errs)}")
        for l in errs[:30]:
            print(" ", l)

    if args.report:
        from tools.coverage_report import write_report
        tsc_errs = 0
        if not args.no_tsc and (out / "tsc_output.txt").exists():
            t = (out / "tsc_output.txt").read_text(encoding="utf-8")
            tsc_errs = sum(1 for l in t.splitlines() if "error TS" in l)
        write_report(rows, Path(args.report), tsc_errors=tsc_errs)
        print(f"report: {args.report}")

    (out / "stats.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
