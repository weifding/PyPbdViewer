"""
Golden end-to-end tests against the real corpus (skipped when absent).

Two comparison modes:
- "full":  every generated .ts must match tests/golden/<stem>/ exactly.
- "stats": only the conversion stat counters are pinned (heavy PBLs whose
  full output would be thousands of files).

Regenerate snapshots:  UPDATE_GOLDEN=1 pytest tests/test_golden.py
Corpus location:       PBTOTS_CORPUS env var, default D:\\ynsoft
"""
from __future__ import annotations
import json
import os
import shutil
from pathlib import Path

import pytest

from extract_pbl import extract_from_pbl
from convert import convert

CORPUS = Path(os.environ.get("PBTOTS_CORPUS", r"D:\ynsoft"))
GOLDEN = Path(__file__).parent / "golden"
UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"

FIXTURES = [
    ("hiscom_public", r"ljp\源程序\tjxt\hiscom_public.pbl", "full"),
    ("rf", r"mzsf_cx20241128\rf.pbl", "full"),
    ("mz_ghcl", r"mzsf_cx20241128\mz_ghcl.pbl", "full"),
    ("gy_pyybjk", r"mzsf_cx20241128\gy_pyybjk.pbl", "stats"),
    ("sb_ywcl", r"mzsf_cx20241128\sb_ywcl.pbl", "stats"),
]


def _run(pbl: Path, work: Path):
    dec = work / "dec"
    ts = work / "ts"
    idx = extract_from_pbl(pbl, dec)
    stats = convert(dec / f"{pbl.stem}.json", ts)
    return stats, ts


def _stat_view(stats: dict) -> dict:
    """Pin only counters; free-form fields (file paths) excluded."""
    return {k: v for k, v in sorted(stats.items())}


@pytest.mark.parametrize("stem,rel,mode", FIXTURES,
                         ids=[f[0] for f in FIXTURES])
def test_golden(stem, rel, mode, tmp_path):
    pbl = CORPUS / rel
    if not pbl.exists():
        pytest.skip(f"corpus missing: {pbl}")

    stats, ts = _run(pbl, tmp_path)
    gdir = GOLDEN / stem

    if mode == "stats":
        gfile = gdir / "stats.json"
        if UPDATE or not gfile.exists():
            gdir.mkdir(parents=True, exist_ok=True)
            gfile.write_text(json.dumps(_stat_view(stats), indent=2), encoding="utf-8")
            pytest.skip("golden snapshot written")
        expected = json.loads(gfile.read_text(encoding="utf-8"))
        assert _stat_view(stats) == expected, f"stats drift for {stem}"
        return

    # full mode: compare every generated file
    if UPDATE or not gdir.exists():
        if gdir.exists():
            shutil.rmtree(gdir)
        shutil.copytree(ts, gdir)
        pytest.skip("golden snapshot written")

    expected_files = {p.name for p in gdir.glob("*.ts")}
    actual_files = {p.name for p in ts.glob("*.ts")}
    assert actual_files == expected_files, (
        f"file set drift for {stem}: "
        f"missing={sorted(expected_files - actual_files)} "
        f"extra={sorted(actual_files - expected_files)}")
    for name in sorted(expected_files):
        got = (ts / name).read_text(encoding="utf-8")
        want = (gdir / name).read_text(encoding="utf-8")
        assert got == want, f"content drift in {stem}/{name}"
