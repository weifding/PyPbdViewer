"""Render a PBD .win entry to HTML using real binary properties."""
import sys, struct
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "converter"))
from pbd_entry_structured import parse_entry

# PB dialog units -> pixels: H=2px, V=1.5px; scaled to fit ~1200px width
SCALE = 0.45
def h(v): return int(v * 2 * SCALE)
def v(v): return int(v * 1.5 * SCALE)

def color_to_css(c):
    # PB long is BGR
    if c == 67108864: return "#ffffff"  # window default
    if c == 33554432: return "#000000"
    b = (c >> 16) & 0xFF
    g = (c >> 8) & 0xFF
    r = c & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"

def textsize_to_px(ts):
    # PB stores negative = points * 100; -9 = 9pt
    pt = -ts / 100 if ts < 0 else ts / 100
    return int(pt * 96 / 72)

def render(entry_path):
    data = Path(entry_path).read_bytes()
    r = parse_entry(data)
    win = r["objects"][0]
    wprops = {p["name"]: p.get("value", p["val_off"]) for p in win["props"]}
    W = h(wprops.get("width", 1000))
    H = v(wprops.get("height", 500))
    win_title = wprops.get("title", Path(entry_path).stem)

    body = []
    body.append(f'<div class="win" style="width:{W}px;height:{H}px;background:{color_to_css(wprops.get("backcolor", 67108864))};">')
    body.append(f'<div class="titlebar">{win_title}</div>')

    for o in r["objects"][1:]:
        p = {x["name"]: x.get("value", x["val_off"]) for x in o["props"]}
        if "x" not in p: continue
        x, y = h(p["x"]), v(p["y"])
        w, hh = h(p.get("width", 100)), v(p.get("height", 30))
        text = p.get("text", "")
        facename = p.get("facename", "Tahoma")
        fs = int(textsize_to_px(p.get("textsize", -900)) * SCALE)
        fw = "bold" if p.get("weight", 400) >= 600 else "normal"
        fg = color_to_css(p.get("textcolor", 0))
        bg = color_to_css(p.get("backcolor", 67108864))
        ctype = o["inh_type"]
        if ctype == "commandbutton":
            el = f'<input type="button" value="{text}" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;font-family:{facename};font-size:{fs}px;font-weight:{fw};background:{bg};color:{fg};">'
        elif ctype == "statictext":
            el = f'<div style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;font-family:{facename};font-size:{fs}px;font-weight:{fw};color:{fg};line-height:{hh}px;">{text}</div>'
        elif ctype in ("singlelineedit", "editmask"):
            el = f'<input type="text" value="{text}" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;font-family:{facename};font-size:{fs}px;">'
        elif ctype == "datawindow":
            el = f'<div class="dw" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;background:#e8e8f0;border:1px solid #888;">[DataWindow] {text}</div>'
        elif ctype == "groupbox":
            el = f'<fieldset style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;"><legend style="font-family:{facename};font-size:{fs}px;">{text}</legend></fieldset>'
        else:
            el = f'<div style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px;background:#ffe;">[{ctype}] {text}</div>'
        body.append(el)
    body.append("</div>")

    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>{win_title}</title>
<style>
body{{font-family:sans-serif;background:#333;padding:20px;}}
.win{{position:relative;box-shadow:0 0 20px rgba(0,0,0,.5);}}
.titlebar{{height:24px;background:#0078d7;color:#fff;padding:4px 8px;font-size:13px;}}
.win div,.win input,.win fieldset{{position:absolute;box-sizing:border-box;}}
.dw{{line-height:100px;text-align:center;color:#666;}}
</style></head><body>{''.join(body)}</body></html>"""
    out = Path(__file__).parent / "ui-pbd.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}")
    print(f"window: {win_title}  {W}x{H}  controls={len(r['objects'])-1}")

if __name__ == "__main__":
    render(sys.argv[1])
