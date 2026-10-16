"""Re-run specific tsc batches and print the exact error lines."""
import json, os, subprocess, sys
from pathlib import Path
TS = Path(r"E:\ChatGPT\PyPbdViewer\out\ts")
batches = [int(x) for x in sys.argv[1:]]
BATCH = 40
dirs = sorted(d for d in TS.iterdir() if d.is_dir() and d.name != "node_modules")
compiler = {"target":"ES2020","module":"commonjs","strict":False,"noImplicitAny":False,
            "esModuleInterop":True,"skipLibCheck":True,"forceConsistentCasingInFileNames":True,"noEmit":True}
env = {**os.environ, "NODE_OPTIONS": "--max-old-space-size=4096"}
for bi in batches:
    batch = dirs[bi*BATCH:(bi+1)*BATCH]
    cfg = {"compilerOptions":compiler, "include":[f"{d.name}/**/*.ts" for d in batch]}
    (TS/"tsconfig_batch.json").write_text(json.dumps(cfg), encoding="utf-8")
    r = subprocess.run("npx tsc -p tsconfig_batch.json --noEmit", cwd=str(TS),
                       capture_output=True, text=True, shell=True, env=env)
    print(f"=== batch {bi} (dirs {bi*BATCH}-{(bi+1)*BATCH}) exit={r.returncode} ===")
    for l in (r.stdout+r.stderr).splitlines():
        if "error TS" in l:
            print("  ", l)
