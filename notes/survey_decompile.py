"""Survey current PBD decompile coverage across out/ts pbd__ outputs."""
from pathlib import Path

ts_root = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
dirs = sorted({f.parent for f in ts_root.rglob("*.ts")
               if "node_modules" not in f.parts and any("pbd__" in p for p in f.parts)})

stats = {"dirs": 0, "files": 0, "stub_body": 0, "stub_file": 0,
         "unimpl_op": 0, "warn_stop": 0, "vm_label": 0, "gf_stub": 0,
         "syntax_err_hint": 0}
by = {}

for d in dirs:
    files = [f for f in d.glob("*.ts") if "pb-runtime" not in f.name and "recovered-sql" not in f.name]
    for f in files:
        t = f.read_text(encoding="utf-8", errors="replace")
        stats["files"] += 1
        if "// TODO: body stripped" in t:
            stats["stub_body"] += 1
        if "TODO" in t or "body stripped" in t:
            stats["stub_file"] += 1
        if "// op 0x" in t:
            stats["unimpl_op"] += 1
        if "WARNING: disassembler stopped" in t:
            stats["warn_stop"] += 1
        if "label L" in t:
            stats["vm_label"] += 1
        if "// TODO: PBD global functions" in t or "gf_" in t and "TODO" in t:
            stats["gf_stub"] += 1
        # syntax-error hints emitted by vm2pb or tsbuilder
        if "/*" in t and "op 0x" in t:
            stats["syntax_err_hint"] += 1
    stats["dirs"] += 1

print("=== PBD decompile coverage survey ===")
for k, v in stats.items():
    print(f"{k}: {v}")
print("total files (excl runtime/sql):", stats["files"])
