"""
Coverage / conversion report generator.

Consumes the per-library stat rows produced by converter/batch.py (or
converter.convert) and writes a markdown summary: object and function counts,
how many bodies are still TODO stubs, unparsed/truncated blocks, and tsc
errors. Extend with statement-level translation rates once tsbuilder (M2)
lands.

CLI:
  python tools/coverage_report.py --stats out/stats.json --out notes/convert-report.md
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def write_report(rows: list[dict], out_path: Path, tsc_errors: int = 0) -> None:
    pbl_rows = [r for r in rows if r.get("kind") == "pbl"]
    pbd_rows = [r for r in rows if r.get("kind") == "pbd"]
    failed = [r for r in rows if r.get("status") != "ok"]

    def total(key):
        return sum(r.get(key, 0) for r in pbl_rows)

    objs = total("objects")
    funcs = total("functions")
    events = total("events")
    externals = total("external")
    globals_ = total("globals")
    unparsed = total("unparsed")
    truncated = total("truncated")
    stubs = funcs + events + globals_  # bodies needing manual port (M2 target)

    lines = [
        "# pbtots 转换覆盖率报告",
        "",
        f"- 输入库：PBL {len(pbl_rows)} 个（成功 {sum(1 for r in pbl_rows if r.get('status') == 'ok')}），"
        f"PBD {len(pbd_rows)} 个",
        f"- 生成对象类：**{objs}**；全局函数：**{globals_}**",
        f"- 函数/子例程体（TODO 桩）：**{funcs}**；事件体（TODO 桩）：**{events}**；外部库声明：**{externals}**",
        f"- 签名未解析（全回退桩）：**{unparsed}**",
        f"- 抽取截断的块（源文本受损）：**{truncated}**",
        f"- `tsc --noEmit` 错误：**{tsc_errors}**",
        "",
        f"待人工/M2 翻译的函数体总量：**{stubs}**",
        "",
        "## 各库明细（按函数体数排序）",
        "",
        "| PBL | 对象 | 函数 | 事件 | 全局 | 外部 | 未解析 | 截断 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(pbl_rows, key=lambda r: -(r.get("functions", 0) + r.get("events", 0))):
        name = Path(r["file"]).name
        lines.append(
            f"| {name} | {r.get('objects', 0)} | {r.get('functions', 0)} | "
            f"{r.get('events', 0)} | {r.get('globals', 0)} | {r.get('external', 0)} | "
            f"{r.get('unparsed', 0)} | {r.get('truncated', 0)} |"
        )

    if pbd_rows:
        lines += [
            "",
            "## PBD（无源码）",
            "",
            f"- 目录项 {sum(r.get('entries', 0) for r in pbd_rows)} 个，"
            f"恢复 SQL 语句 {sum(r.get('sql', 0) for r in pbd_rows)} 条（仅存档，未翻译）",
        ]

    if failed:
        lines += ["", "## 失败", ""]
        for r in failed[:50]:
            lines.append(f"- `{r['file']}`: {r['status']}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Write pbtots conversion report")
    ap.add_argument("--stats", required=True, help="stats.json from batch.py")
    ap.add_argument("--out", required=True, help="markdown output path")
    ap.add_argument("--tsc-errors", type=int, default=0)
    args = ap.parse_args()
    rows = json.loads(Path(args.stats).read_text(encoding="utf-8"))
    write_report(rows, Path(args.out), tsc_errors=args.tsc_errors)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
