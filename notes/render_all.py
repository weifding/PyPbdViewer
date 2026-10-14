"""Render all PB windows into a single tabbed HTML page.
PB units: 1 H PBU ≈ 2px, 1 V PBU ≈ 1.5px at 96 DPI default font.
Controls' x/y are absolute relative to their immediate parent (GroupBox/TabPage),
NOT to the window. We only walk the declared tree for nesting.
"""
import os, re, html
from pathlib import Path

DECOMPILED = Path(r"E:\ChatGPT\PyPbdViewer\out\decompiled")
OUT = Path(r"E:\ChatGPT\PyPbdViewer\notes\ui-all.html")

PBU_H = 2.0
PBU_V = 1.5

def parse_blocks(txt):
    blocks = {}
    children_of = {}
    for m in re.finditer(
        r"^type\s+(\w+)\s+from\s+([^\n]+?)\s+within\s+(\w+)\s*\n(.*?)^end\s+type",
        txt, re.I | re.S | re.M):
        name, anc_raw, parent, body = m.groups()
        anc = anc_raw.split()[-1].lower() if anc_raw.split() else "control"
        props = {}
        for pm in re.finditer(r"^\s*(?:integer|long|boolean|string|windowtype|fontcharset|fontpitch|fontfamily)\s+(\w+)\s*=\s*(.+?)\s*$",
                              body, re.I | re.M):
            k, v = pm.group(1), pm.group(2).strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            props[k] = v
        if name in blocks:
            old = blocks[name]
            if len(old) >= len(props):
                props = {**props, **old}
        blocks[name] = props
        children_of.setdefault(parent, []).append((name, anc))
    for m in re.finditer(
        r"^global\s+type\s+(\w+)\s+from\s+(\w+)\s*\n(.*?)^end\s+type",
        txt, re.I | re.S | re.M):
        name, anc, body = m.groups()
        props = {}
        for pm in re.finditer(r"^\s*(?:integer|long|boolean|string|windowtype|fontcharset|fontpitch|fontfamily)\s+(\w+)\s*=\s*(.+?)\s*$",
                              body, re.I | re.M):
            k, v = pm.group(1), pm.group(2).strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            props[k] = v
        blocks[name] = props
    return blocks, children_of

CSS = {"commandbutton":"button","graphicbutton":"button","picturebutton":"button",
       "singlelineedit":"sle","sle":"sle","editmask":"sle",
       "multilineedit":"mle","mle":"mle","statictext":"st","st":"st",
       "datawindow":"dw","vu_datawindow":"dw",
       "dropdownlistbox":"ddlb","ddlb":"ddlb",
       "checkbox":"cbx","cbx":"cbx","radiobutton":"rb",
       "groupbox":"gb","listbox":"lb","listview":"lv",
       "treeview":"tv","tab":"tab","tabpage":"tabpage",
       "picture":"pic"}

def render_window(txt, win_name):
    blocks, children_of = parse_blocks(txt)
    wp = blocks.get(win_name, {})
    title = wp.get("title", win_name)
    ww = int(wp.get("width", 4000))
    wh = int(wp.get("height", 3000))

    def ux(v):
        try: return int(v) * PBU_H
        except: return 0
    def uy(v):
        try: return int(v) * PBU_V
        except: return 0

    # Collect all controls, with absolute positions.
    # Top-level controls (within win_name) use absolute win coords.
    # Nested controls (within a container) add container's position.
    all_ctrls = []
    seen = set()
    def walk(parent, x_off, y_off, depth):
        for cn, ca in children_of.get(parent, []):
            if cn in seen: continue
            seen.add(cn)
            p = blocks.get(cn, {})
            cx = int(p.get("x", 0)); cy = int(p.get("y", 0))
            cw = int(p.get("width", 200)); ch = int(p.get("height", 80))
            all_ctrls.append((cn, ca, x_off+cx, y_off+cy, cw, ch, p, depth))
            # Only recurse into real containers (TabControl).
            # GroupBox in PB does NOT reposition children visually.
            if ca == "tab":
                walk(cn, cx, cy + 30, depth+1)
    walk(win_name, 0, 30, 0)

    inner = [f'<div class="win" style="width:{ux(ww)}px;height:{uy(wh)}px">']
    inner.append(f'<div class="tb">{html.escape(title)} - {win_name} ({len(all_ctrls)}控件)</div>')
    for cn, ca, ax, ay, cw, ch, p, d in all_ctrls:
        cls = CSS.get(ca, "ctrl")
        text = p.get("text", cn)
        if "datawindow" in ca:
            inner.append(f'<div class="ctrl {cls}" style="left:{ux(ax)}px;top:{uy(ay)}px;width:{ux(cw)}px;height:{uy(ch)}px">[DW:{cn}]</div>')
        elif ca == "tab":
            inner.append(f'<div class="ctrl {cls}" style="left:{ux(ax)}px;top:{uy(ay)}px;width:{ux(cw)}px;height:{uy(ch)}px">[Tab:{cn}]</div>')
        elif ca == "tabpage":
            inner.append(f'<div class="ctrl {cls}" style="left:{ux(ax)}px;top:{uy(ay)}px;width:{ux(cw)}px;height:{uy(ch)}px">[Page:{cn}]</div>')
        else:
            inner.append(f'<div class="ctrl {cls}" title="{cn}" style="left:{ux(ax)}px;top:{uy(ay)}px;width:{ux(cw)}px;height:{uy(ch)}px">{html.escape(text)}</div>')
    inner.append('</div>')
    return title, len(all_ctrls), "\n".join(inner)

# Collect all windows
windows = []
for root, dirs, files in os.walk(DECOMPILED):
    for f in files:
        if not f.endswith(".ps.txt"): continue
        p = os.path.join(root, f)
        try: txt = open(p, encoding="utf-8", errors="replace").read()
        except: continue
        for m in re.finditer(r"^global\s+type\s+(w_\w+)\s+from\s+window\b", txt, re.I | re.M):
            win = m.group(1)
            n = len(set(re.findall(r"type\s+\w+\s+from\s+\w+\s+within\s+" + win, txt, re.I)))
            if n >= 5:
                windows.append((p, win, n))

windows.sort(key=lambda x: -x[2])
print(f"found {len(windows)} windows")

tab_btns = []
tab_panels = []
for i, (p, win, n) in enumerate(windows):
    try:
        txt = open(p, encoding="utf-8", errors="replace").read()
        title, nctrl, body = render_window(txt, win)
    except Exception as e:
        title, nctrl, body = win, 0, f"<div>error: {e}</div>"
    tab_btns.append(f'<button class="tab{" active" if i==0 else ""}" onclick="show({i})">{html.escape(title) or html.escape(win)} ({nctrl})</button>')
    tab_panels.append(f'<div class="panel{" active" if i==0 else ""}" id="p{i}">{body}</div>')

html_doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>PB UI All Windows</title>
<style>
body {{ margin:0; background:#2b2b2b; font-family:"Microsoft YaHei",sans-serif; overflow-x:hidden; }}
.tabs {{ background:rgba(26,26,26,0.9); padding:6px; display:flex; flex-wrap:wrap; gap:4px; position:fixed; top:0; left:0; right:0; z-index:100; backdrop-filter:blur(4px); max-height:40vh; overflow-y:auto; }}
.tab {{ background:#cce5ff; color:#d00; border:1px solid #99c2ff; padding:4px 8px; cursor:pointer; font-size:11px; }}
.tab.active {{ background:#0a66c2; color:#fff; }}
.panel {{ display:none; padding:60px 20px 20px 20px; overflow-x:auto; }}
.panel.active {{ display:block; }}
.win {{ position:relative; background:#f0f0f0; border:1px solid #555; margin:0 auto; }}
.tb {{ background:linear-gradient(#0a66c2,#004182); color:#fff; padding:4px 8px; font-size:11px; }}
.ctrl {{ position:absolute; font-size:11px; padding:2px 4px; overflow:hidden; box-sizing:border-box; }}
.button {{ background:linear-gradient(#f5f5f5,#d8d8d8); border:1px solid #888; text-align:center; display:flex; align-items:center; justify-content:center; }}
.sle,.mle,.ddlb {{ background:#fff; border:1px solid #7a7a7a; }}
.st {{ background:transparent; padding:0; }}
.dw {{ background:#fff; border:1px solid #555; }}
.gb {{ border:1px solid #aaa; }}
.cbx,.rb {{ background:transparent; }}
.lb,.lv,.tv {{ background:#fff; border:1px solid #7a7a7a; }}
.tab {{ border:1px solid #888; background:#e8e8e8; }}
.tabpage {{ border:1px dashed #e8730c; background:#fff; }}
</style></head><body>
<div class="tabs">{''.join(tab_btns)}</div>
{''.join(tab_panels)}
<script>
function show(i){{
  document.querySelectorAll('.tab').forEach((t,j)=>t.classList.toggle('active',j===i));
  document.querySelectorAll('.panel').forEach((p,j)=>p.classList.toggle('active',j===i));
}}
</script>
</body></html>"""

OUT.write_text(html_doc, encoding="utf-8")
print(f"HTML: {OUT}, size: {OUT.stat().st_size//1024}KB")
