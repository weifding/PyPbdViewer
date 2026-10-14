"""Batch parse all PBD .dwo / .men / .srj entries to JSON."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "converter"))
from pbd_entry_structured import parse_entry

def main():
    entries_root = Path(r"E:\ChatGPT\PyPbdViewer\out\decompiled")
    out_root = Path(r"E:\ChatGPT\PyPbdViewer\out\win_tree")
    out_root.mkdir(exist_ok=True)
    counts = {}
    for entries_dir in entries_root.glob("pbd__*/entries"):
        pbd = entries_dir.parent.name
        for suffix in ("*.dwo", "*.men", "*.srj", "*.fun", "*.str"):
            for f in entries_dir.glob(suffix):
                try:
                    r = parse_entry(f.read_bytes())
                except Exception:
                    continue
                tree = {"entry": f.name, "objects": []}
                for o in r["objects"]:
                    props = {p["name"]: p.get("value", p["val_off"]) for p in o["props"]}
                    tree["objects"].append({"name": o["name"], "type": o["inh_type"], "props": props})
                (out_root / pbd).mkdir(exist_ok=True)
                outp = out_root / pbd / (f.name.replace(".", "_") + ".json")
                outp.write_text(json.dumps(tree, ensure_ascii=False), encoding="utf-8")
                counts[f.suffix] = counts.get(f.suffix, 0) + 1
    print(counts)

if __name__ == "__main__":
    main()
