"""Render a PB window as full-page HTML with proper nested layout."""
import re
from pathlib import Path

import sys
PS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"E:\ChatGPT\PyPbdViewer\out\decompiled\mzsf_cx20241128__gy_feedbackdev\gy_feedbackdev.ps.txt")
WIN_NAME = sys.argv[2] if len(sys.argv) > 2 else "w_test_feedback"
OUT = Path(r"E:\ChatGPT\PyPbdViewer\notes\ui-preview.html")

txt = PS.read_text(encoding="utf-8", errors="replace")

# Parse all `type NAME from ANCESTOR within PARENT ... end type` blocks.
blocks = {}
children_of = {}
for m in re.finditer(
    r"^type\s+(\w+)\s+from\s+(\w+)\s+within\s+(\w+)\s*\n(.*?)^end\s+type",
    txt, re.I | re.S | re.M):
    name, anc, parent, body = m.groups()
    props = {}
    for pm in re.finditer(r"^\s*(?:integer|long|boolean|string|windowtype|fontcharset|fontpitch)\s+(\w+)\s*=\s*(.+?)\s*$",
                          body, re.I | re.M):
        k, v = pm.group(1), pm.group(2).strip()
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        props[k] = v
    blocks.setdefault(name, props)
    children_of.setdefault(parent, []).append((name, anc.lower()))

# Also parse window's own global type block
for m in re.finditer(
    r"^global\s+type\s+(\w+)\s+from\s+(\w+)\s*\n(.*?)^end\s+type",
    txt, re.I | re.S | re.M):
    name, anc, body = m.groups()
    props = {}
    for pm in re.finditer(r"^\s*(?:integer|long|boolean|string|windowtype|fontcharset|fontpitch)\s+(\w+)\s*=\s*(.+?)\s*$",
                          body, re.I | re.M):
        k, v = pm.group(1), pm.group(2).strip()
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        props[k] = v
    if name == WIN_NAME:
        blocks[name] = props

win_props = blocks.get(WIN_NAME, {})
win_title = win_props.get("title", WIN_NAME)
win_w = int(win_props.get("width", 4000))
win_h = int(win_props.get("height", 3000))

# Scale: PB units -> px (1 unit ≈ 4 px), fit 1400x900
RAW_W = win_w * 4
RAW_H = win_h * 4
SCALE = min(1400 / RAW_W, 900 / RAW_H)
SCALE = max(SCALE, 0.25)

def u(v):
    try: return int(v) * 4 * SCALE
    except: return 0

CSS = {"commandbutton":"button","graphicbutton":"button","picturebutton":"button",
       "singlelineedit":"sle","sle":"sle","editmask":"sle",
       "multilineedit":"mle","mle":"mle",
       "statictext":"st","st":"st",
       "datawindow":"dw","vu_datawindow":"dw",
       "dropdownlistbox":"ddlb","ddlb":"ddlb",
       "checkbox":"cbx","cbx":"cbx","radiobutton":"rb",
       "groupbox":"gb","listbox":"lb","listview":"lv",
       "treeview":"tv","tab":"tab","tabpage":"tabpage"}

# Collect all controls with absolute positions (walk hierarchy)
all_controls = []  # (name, ancestor, x_abs, y_abs, w, h, props)
seen_names = set()
def walk(parent_name, parent_anc, x_off, y_off, depth):
    for cname, canc in children_of.get(parent_name, []):
        if cname in seen_names:
            continue
        seen_names.add(cname)
        p = blocks.get(cname, {})
        cx = int(p.get("x", 0))
        cy = int(p.get("y", 0))
        cw = int(p.get("width", 200))
        ch = int(p.get("height", 80))
        abs_x = x_off + cx
        abs_y = y_off + cy
        all_controls.append((cname, canc, abs_x, abs_y, cw, ch, p, depth))
        if canc == "tab":
            walk(cname, canc, cx, cy + 30, depth + 1)
        else:
            walk(cname, canc, cx, cy, depth + 1)

# Start from window
walk(WIN_NAME, "window", 0, 30, 0)  # 30 = titlebar height

# Build HTML
parts = [f"""<!doctype html><html><head><meta charset="utf-8"><title>{WIN_NAME}</title>
<style>
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#2b2b2b; font-family:"Microsoft YaHei",sans-serif;
       display:flex; align-items:center; justify-content:center; min-height:100vh; }}
.win {{ position:relative; background:#f0f0f0; border:1px solid #555;
       box-shadow:0 8px 32px rgba(0,0,0,.6); }}
.titlebar {{ background:linear-gradient(#0a66c2,#004182); color:#fff; padding:6px 10px;
             font-size:13px; }}
.ctrl {{ position:absolute; font-size:{max(10, int(12*SCALE))}px; padding:2px 6px;
        overflow:hidden; }}
.button {{ background:linear-gradient(#f5f5f5,#d8d8d8); border:1px solid #888;
           text-align:center; display:flex; align-items:center; justify-content:center; }}
.sle,.mle,.ddlb {{ background:#fff; border:1px solid #7a7a7a; }}
.mle {{ white-space:pre-wrap; }}
.st  {{ background:transparent; padding:0; }}
.dw  {{ background:#fff; border:1px solid #555; }}
.gb  {{ border:1px solid #aaa; }}
.cbx,.rb {{ background:transparent; }}
.lb,.lv,.tv {{ background:#fff; border:1px solid #7a7a7a; }}
.tab {{ border:1px solid #888; background:#e8e8e8; }}
.tabpage {{ border:1px solid #888; background:#fff; }}
.d0 {{ z-index:1; }}
.d1 {{ z-index:2; border:1px dashed #0a66c2; }}
.d2 {{ z-index:3; border:1px dashed #e8730c; }}
</style></head><body>
<div class="win" style="width:{u(win_w)}px;height:{u(win_h)}px">
<div class="titlebar">{win_title} - {WIN_NAME} ({len(all_controls)} controls, scale={SCALE:.2f}x)</div>
"""]

for cname, canc, ax, ay, cw, ch, p, depth in all_controls:
    cls = CSS.get(canc, "ctrl")
    x = u(ax)
    y = u(ay)
    w = u(cw)
    h = u(ch)
    text = p.get("text", cname)
    if "datawindow" in canc:
        inner = f"<div style='padding:4px;color:#666'>[DW:{cname}]</div>"
    elif canc in ("checkbox","radiobutton"):
        inner = f"&#9744; {text}"
    elif canc == "tab":
        inner = f"<div style='padding:4px;color:#333'>[TabControl: {cname}]</div>"
    elif canc == "tabpage":
        inner = f"<div style='padding:4px;color:#0a66c2;font-weight:bold'>[TabPage: {cname}]</div>"
    else:
        inner = text
    parts.append(
        f'<div class="ctrl {cls} d{depth}" title="{cname} (depth={depth})" '
        f'style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
        f'{inner}</div>')

parts.append("</div></body></html>")
OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"window: {WIN_NAME}, title: {win_title}, controls: {len(all_controls)}")
print(f"raw: {RAW_W}x{RAW_H}, scale: {SCALE:.2f}x")
print("HTML:", OUT)
