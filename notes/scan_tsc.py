"""Batch type-check out/ts in slices to avoid a single-process OOM.

The whole 12k-file tree blows node's heap in one tsc run; checking ~40
library dirs per process keeps each under a few GB. Each generated .ts
carries `// @ts-nocheck` (suppresses type errors), so only syntax errors
(TS10xx) surface here — that is exactly the decompiler's remaining risk.
"""
import json, os, subprocess, sys
from pathlib import Path

TS = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
BATCH = int(sys.argv[1]) if len(sys.argv) > 1 else 40
HEAP = sys.argv[2] if len(sys.argv) > 2 else "4096"

dirs = sorted(d for d in TS.iterdir() if d.is_dir() and d.name != "node_modules")
if not dirs:
    print("no dirs"); sys.exit(0)

compiler = {
    "target": "ES2020", "module": "commonjs", "strict": False,
    "noImplicitAny": False, "esModuleInterop": True, "skipLibCheck": True,
    "forceConsistentCasingInFileNames": True, "noEmit": True,
}
env = {**os.environ, "NODE_OPTIONS": f"--max-old-space-size={HEAP}"}

total_err = 0
total_syntax = 0
by_batch = []
for i in range(0, len(dirs), BATCH):
    batch = dirs[i:i + BATCH]
    cfg = {"compilerOptions": compiler,
           "include": [f"{d.name}/**/*.ts" for d in batch]}
    (TS / "tsconfig_batch.json").write_text(json.dumps(cfg), encoding="utf-8")
    r = subprocess.run("npx tsc -p tsconfig_batch.json --noEmit",
                       cwd=str(TS), capture_output=True, text=True, shell=True, env=env)
    lines = (r.stdout + r.stderr).splitlines()
    errs = [l for l in lines if "error TS" in l]
    syntax = [l for l in errs if "TS1" in l.split("error")[1][:4] or "TS1" in l]
    total_err += len(errs)
    total_syntax += len(syntax)
    by_batch.append((len(batch), r.returncode, len(errs)))
    print(f"batch {i//BATCH}: dirs={len(batch)} exit={r.returncode} errors={len(errs)}", flush=True)

print("=== SUMMARY ===")
print(f"batches: {len(by_batch)}  dirs total: {len(dirs)}  total errors: {total_err}  syntax: {total_syntax}")
fails = [b for b in by_batch if b[2] > 0]
print(f"batches with errors: {len(fails)}")
