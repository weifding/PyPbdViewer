"""Batch-parse all PBD .win entries to JSON control tree."""
import sys, json, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "converter"))
from pbd_entry_structured import parse_entry

def win_to_dict(r):
    out = {"controls": []}
    for i, o in enumerate(r["objects"]):
        d = {"name": o["name"], "type": o["inh_type"], "parent": o["parent_type"]}
        props = {}
        for p in o["props"]:
            props[p["name"]] = p.get("value", p["val_off"])
        d["props"] = props
        out["controls"].append(d)
    return out

def main():
    entries_root = Path(r"E:\ChatGPT\PyPbdViewer\out\decompiled")
    out_root = Path(r"E:\ChatGPT\PyPbdViewer\out\win_tree")
    out_root.mkdir(exist_ok=True)
    ok = 0; err = 0; total = 0
    for entries_dir in entries_root.glob("pbd__*/entries"):
        for f in entries_dir.glob("*.win"):
            total += 1
            try:
                r = parse_entry(f.read_bytes())
                if not r["objects"]:
                    continue
                tree = win_to_dict(r)
                pbd_name = entries_dir.parent.name
                (out_root / pbd_name).mkdir(exist_ok=True)
                (out_root / pbd_name / f.name.replace(".win", ".json")).write_text(
                    json.dumps(tree, ensure_ascii=False), encoding="utf-8")
                ok += 1
            except Exception:
                err += 1
    print(f"total={total} ok={ok} err={err}")

if __name__ == "__main__":
    main()
