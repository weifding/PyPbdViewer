"""Render all PBD .win entries to a single tab HTML."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "converter"))
from pbd_entry_structured import parse_entry

SCALE = 0.45
def h(v): return int(v * 2 * SCALE)
def v(v): return int(v * 1.5 * SCALE)

def color_to_css(c):
    if c == 67108864: return "#ffffff"
    if c == 33554432: return "#000000"
    b = (c >> 16) & 0xFF; g = (c >> 8) & 0xFF; r = c & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"

def textsize_to_px(ts):
    pt = -ts / 100 if ts < 0 else ts / 100
    return int(pt * 96 / 72 * SCALE)

def render_win(data):
    try:
        r = parse_entry(data)
    except Exception as e:
        return None, f"parse error: {e}"
    if not r["objects"]:
        return None, "no objects"
    win = r["objects"][0]
    wprops = {p["name"]: p.get("value", p["val_off"]) for p in win["props"]}
    W = h(wprops.get("width", 1000))
    H = v(wprops.get("height", 500))
    title = wprops.get("title", win["name"])
    body = [f'<div class="win" style="width:{W}px;height:{H}px;background:{color_to_css(wprops.get("backcolor",67108864))};">']
    body.append(f'<div class="titlebar">{title}</div>')
    for o in r["objects"][1:]:
        p = {x["name"]: x.get("value", x["val_off"]) for x in o["props"]}
        if "x" not in p or "y" not in p: continue
        x, y = h(p["x"]), v(p["y"])
        w, hh = h(p.get("width", 100)), v(p.get("height", 30))
        text = p.get("text", "")
        facename = p.get("facename", "Tahoma")
        fs = textsize_to_px(p.get("textsize", -900))
        fw = "bold" if p.get("weight", 400) >= 600 else "normal"
        fg = color_to_css(p.get("textcolor", 0))
        bg = color_to_css(p.get("backcolor", 67108864))
        ct = o["inh_type"]
        if ct == "commandbutton":
            el = f'<input type="button" value="{text}" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;font-family:{facename};font-size:{fs}px;font-weight:{fw};">'
        elif ct == "statictext":
            el = f'<div style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;font-family:{facename};font-size:{fs}px;font-weight:{fw};color:{fg};line-height:{hh}px;">{text}</div>'
        elif ct in ("singlelineedit", "editmask"):
            el = f'<input type="text" value="{text}" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;font-family:{facename};font-size:{fs}px;">'
        elif ct == "datawindow":
            el = f'<div class="dw" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;background:#e8e8f0;border:1px solid #888;">[DW]</div>'
        elif ct == "groupbox":
            el = f'<fieldset style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;"><legend style="font-size:{fs}px;">{text}</legend></fieldset>'
        else:
            el = f'<div style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;background:#ffe8e8;">[{ct}]</div>'
        body.append(el)
    body.append("</div>")
    return {"title": title, "name": win["name"], "controls": len(r["objects"])-1, "html": "".join(body)}, None

def main():
    entries_root = Path(r"E:\ChatGPT\PyPbdViewer\out\decompiled")
    wins = []
    errors = 0
    for entries_dir in entries_root.glob("pbd__*/entries"):
        for f in entries_dir.glob("*.win"):
            data = f.read_bytes()
            info, err = render_win(data)
            if info is None:
                errors += 1
                continue
            info["file"] = f.name
            info["pbd"] = entries_dir.parent.name
            wins.append(info)
    print(f"rendered {len(wins)} windows, errors={errors}")

    tabs = []
    panes = []
    for i, w in enumerate(wins):
        tabs.append(f'<button class="tab" data-i="{i}">{w["name"]} ({w["controls"]})</button>')
        panes.append(f'<div class="pane" data-i="{i}" style="display:none;">{w["html"]}</div>')

    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>All PBD UIs</title>
<style>
body{{font-family:sans-serif;background:#333;margin:0;}}
.tabs{{position:fixed;top:0;left:0;right:0;background:#cfe6f5;padding:6px;z-index:100;display:flex;flex-wrap:wrap;gap:4px;}}
.tab{{background:#cfe6f5;color:#c00;border:1px solid #9ac;cursor:pointer;padding:3px 8px;font-size:12px;}}
.tab.active{{background:#0078d7;color:#fff;}}
.panes{{padding-top:50px;padding:60px 20px 20px;}}
.win{{position:relative;background:#fff;margin:20px auto;box-shadow:0 0 20px rgba(0,0,0,.5);}}
.titlebar{{height:24px;background:#0078d7;color:#fff;padding:4px 8px;font-size:13px;}}
.win div,.win input,.win fieldset{{position:absolute;box-sizing:border-box;}}
.dw{{line-height:100px;text-align:center;color:#666;}}
</style></head><body>
<div class="tabs">{''.join(tabs)}</div>
<div class="panes">{''.join(panes)}</div>
<script>
const tabs=document.querySelectorAll('.tab');
const panes=document.querySelectorAll('.pane');
tabs.forEach(t=>t.onclick=()=>{{
  tabs.forEach(x=>x.classList.remove('active'));
  panes.forEach(p=>p.style.display='none');
  t.classList.add('active');
  document.querySelector('.pane[data-i="'+t.dataset.i+'"]').style.display='block';
}});
if(tabs.length) tabs[0].click();
</script></body></html>"""
    out = Path(__file__).parent / "ui-pbd-all.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}  ({out.stat().st_size//1024}KB)")

if __name__ == "__main__":
    main()
