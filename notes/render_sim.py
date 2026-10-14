"""Generate a simulated UI runtime HTML: parse PBL control tree,
emit JSON, and render with a browser-side PB JS runtime
(real clickable buttons, inputs, DW grids)."""
import os, re, json, html
from pathlib import Path

DECOMPILED = Path(r"E:\ChatGPT\PyPbdViewer\out\decompiled")
OUT_DIR = Path(r"E:\ChatGPT\PyPbdViewer\notes")
OUT = OUT_DIR / "ui-sim.html"

PBU_H = 2.0
PBU_V = 1.5

def _int(v, default=0):
    try: return int(str(v).strip().split()[0])
    except: return default

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

def window_to_json(txt, win_name):
    blocks, children_of = parse_blocks(txt)
    wp = blocks.get(win_name, {})
    controls = []
    seen = set()
    def walk(parent, depth):
        for cn, ca in children_of.get(parent, []):
            if cn in seen: continue
            seen.add(cn)
            p = blocks.get(cn, {})
            controls.append({
                "name": cn, "type": ca, "parent": parent, "depth": depth,
                "x": _int(p.get("x", 0)), "y": _int(p.get("y", 0)),
                "width": _int(p.get("width", 200)), "height": _int(p.get("height", 80)),
                "text": p.get("text", ""), "enabled": p.get("enabled", "true") != "false",
                "facename": p.get("facename", "宋体"),
                "textsize": _int(p.get("textsize", -9)),
                "weight": _int(p.get("weight", 400)),
                "backcolor": p.get("backcolor", ""),
                "textcolor": p.get("textcolor", ""),
                "border": p.get("border", ""),
            })
            if ca == "tab":
                walk(cn, depth+1)
    walk(win_name, 0)
    return {
        "name": win_name,
        "title": wp.get("title", win_name),
        "width": _int(wp.get("width", 4000)),
        "height": _int(wp.get("height", 3000)),
        "menus": _extract_menus(txt),
        "controls": controls,
    }

def _extract_menus(txt):
    menus = []
    for m in re.finditer(r"^type\s+(\w+)\s+from\s+menu\s+within\s+(\w+)\s*\n(.*?)^end\s+type",
                         txt, re.I | re.S | re.M):
        name, parent, body = m.groups()
        tm = re.search(r'string\s+text\s*=\s*"([^"]+)"', body)
        if tm:
            menus.append({"name": name, "text": tm.group(1)})
    return menus[:20]

# Collect top windows
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
            if n >= 10:
                windows.append((p, win, n))
windows.sort(key=lambda x: -x[2])
windows = windows[:30]  # top 30 richest
print(f"top {len(windows)} windows")

WINDOWS_JSON = []
for p, win, n in windows:
    try:
        txt = open(p, encoding="utf-8", errors="replace").read()
        WINDOWS_JSON.append(window_to_json(txt, win))
    except Exception as e:
        print(f"skip {win}: {e}")

DATA_JS = json.dumps(WINDOWS_JSON, ensure_ascii=False)

html_doc = r"""<!doctype html><html><head><meta charset="utf-8"><title>PB UI Simulator</title>
<style>
* { box-sizing:border-box; }
body { margin:0; background:#2b2b2b; font-family:"Microsoft YaHei",sans-serif; overflow-x:hidden; }
.tabs { background:rgba(26,26,26,0.92); padding:6px; display:flex; flex-wrap:wrap; gap:4px; position:fixed; top:0; left:0; right:0; z-index:100; backdrop-filter:blur(4px); max-height:40vh; overflow-y:auto; }
.tab { background:#cce5ff; color:#d00; border:1px solid #99c2ff; padding:4px 8px; cursor:pointer; font-size:11px; }
.tab.active { background:#0a66c2; color:#fff; }
.panel { display:none; padding:60px 20px 20px 20px; overflow-x:auto; }
.panel.active { display:block; }
.pb-window { position:relative; background:#f0f0f0; border:1px solid #555; margin:0 auto; box-shadow:0 8px 32px rgba(0,0,0,.5); }
.pb-titlebar { background:linear-gradient(#0a66c2,#004182); color:#fff; padding:4px 8px; font-size:12px; }
.pb-ctrl { position:absolute; font-size:11px; padding:2px 4px; overflow:hidden; }
.pb-commandbutton { background:linear-gradient(#f5f5f5,#d8d8d8); border:1px solid #888; text-align:center; display:flex; align-items:center; justify-content:center; cursor:pointer; }
.pb-commandbutton:hover { background:linear-gradient(#fff,#e0e0e0); }
.pb-commandbutton:active { background:linear-gradient(#d0d0d0,#b8b8b8); }
.pb-commandbutton.disabled, .pb-commandbutton[disabled] { opacity:0.5; cursor:not-allowed; }
.pb-singlelineedit, .pb-multilineedit, .pb-dropdownlistbox { background:#fff; border:1px solid #7a7a7a; padding:2px 4px; }
.pb-statictext { background:transparent; padding:0; }
.pb-datawindow { background:#fff; border:1px solid #555; overflow:auto; font-size:10px; }
.pb-datawindow table { border-collapse:collapse; width:100%; }
.pb-datawindow th, .pb-datawindow td { border:1px solid #ccc; padding:2px 6px; }
.pb-groupbox { border:1px solid #aaa; }
.pb-groupbox::before { content:attr(data-label); position:absolute; top:-8px; left:8px; background:#f0f0f0; padding:0 4px; font-size:10px; color:#666; }
.pb-checkbox, .pb-radiobutton { background:transparent; }
.pb-listbox, .pb-listview, .pb-treeview { background:#fff; border:1px solid #7a7a7a; }
.pb-tab { border:1px solid #888; background:#e8e8e8; }
.pb-tabpage { border:1px dashed #e8730c; background:#fff; }
.pb-picture { background:#d0d0d0; border:1px dashed #999; display:flex; align-items:center; justify-content:center; color:#666; font-size:10px; }
.pb-menubar { background:#f5f5f5; border-bottom:1px solid #ccc; padding:2px 6px; display:flex; gap:12px; font-size:11px; }
.pb-menu { cursor:pointer; padding:2px 6px; }
.pb-menu:hover { background:#cce5ff; }
</style></head><body>
<div class="tabs" id="tabs"></div>
<div id="panels"></div>
<script>
const PBU_H = 2.0, PBU_V = 1.5;
const WINDOWS = __DATA__;

function ux(v) { return v * PBU_H; }
function uy(v) { return v * PBU_V; }

function renderControl(ctrl) {
  const div = document.createElement("div");
  const cls = "pb-" + ctrl.type;
  div.className = "pb-ctrl " + cls;
  div.style.left = ux(ctrl.x) + "px";
  div.style.top = uy(ctrl.y) + "px";
  div.style.width = ux(ctrl.width) + "px";
  div.style.height = uy(ctrl.height) + "px";
  div.title = ctrl.name + " (" + ctrl.type + ")";
  if (!ctrl.enabled) div.classList.add("disabled");

  // Apply font
  const pt = Math.abs(ctrl.textsize || -9);
  div.style.fontSize = pt + "pt";
  div.style.fontFamily = ctrl.facename || "宋体";
  div.style.fontWeight = (ctrl.weight >= 700) ? "bold" : "normal";

  // PB long color = 0x00BBGGRR; convert to CSS #rrggbb
  function pbColor(v) {
    if (!v) return null;
    try {
      const n = parseInt(v, 10) >>> 0;
      const r = n & 0xff, g = (n >> 8) & 0xff, b = (n >> 16) & 0xff;
      return `rgb(${r},${g},${b})`;
    } catch { return null; }
  }
  const bg = pbColor(ctrl.backcolor);
  const fg = pbColor(ctrl.textcolor);
  if (bg && !["datawindow","checkbox","radiobutton","groupbox"].includes(ctrl.type)) {
    div.style.background = bg;
  }
  if (fg) div.style.color = fg;

  switch (ctrl.type) {
    case "commandbutton":
    case "graphicbutton":
    case "picturebutton":
      div.textContent = ctrl.text || ctrl.name;
      div.addEventListener("click", () => alert("[" + ctrl.name + "] " + (ctrl.text || "click")));
      break;
    case "singlelineedit":
      const inp = document.createElement("input");
      inp.value = ctrl.text || "";
      inp.style.width = "100%"; inp.style.height = "100%";
      inp.style.border = "none"; inp.style.fontSize = "11px";
      div.appendChild(inp);
      break;
    case "multilineedit":
      const ta = document.createElement("textarea");
      ta.value = ctrl.text || "";
      ta.style.width = "100%"; ta.style.height = "100%";
      ta.style.border = "none"; ta.style.fontSize = "11px";
      div.appendChild(ta);
      break;
    case "statictext":
      div.textContent = ctrl.text || "";
      break;
    case "checkbox":
      div.innerHTML = '<input type="checkbox"> ' + (ctrl.text || "");
      break;
    case "radiobutton":
      div.innerHTML = '<input type="radio" name="' + ctrl.parent + '"> ' + (ctrl.text || "");
      break;
    case "dropdownlistbox":
      const sel = document.createElement("select");
      sel.innerHTML = "<option>" + (ctrl.text || "请选择") + "</option>";
      sel.style.width = "100%"; sel.style.height = "100%";
      div.appendChild(sel);
      break;
    case "datawindow":
    case "vu_datawindow":
      div.innerHTML = "<div style='padding:4px;color:#666;font-size:10px'>[DataWindow: " + ctrl.name + "]<br><table><tr><th>列1</th><th>列2</th><th>列3</th></tr><tr><td>数据</td><td>数据</td><td>数据</td></tr></table></div>";
      break;
    case "groupbox":
      div.dataset.label = ctrl.text || ctrl.name;
      break;
    case "tab":
      div.innerHTML = "<div style='padding:4px;color:#333;font-size:10px'>[TabControl: " + ctrl.name + "]</div>";
      break;
    case "tabpage":
      div.innerHTML = "<div style='padding:4px;color:#0a66c2;font-size:10px;font-weight:bold'>[Page: " + ctrl.name + "]</div>";
      break;
    case "picture":
      div.textContent = "[图片]";
      break;
    default:
      div.textContent = ctrl.text || ctrl.name;
  }
  return div;
}

function renderWindow(win) {
  const root = document.createElement("div");
  root.className = "pb-window";
  root.style.width = ux(win.width) + "px";
  root.style.height = uy(win.height) + "px";

  const tb = document.createElement("div");
  tb.className = "pb-titlebar";
  tb.textContent = win.title + " - " + win.name + " (" + win.controls.length + "控件)";
  root.appendChild(tb);

  // Menu bar (if any)
  if (win.menus && win.menus.length) {
    const mb = document.createElement("div");
    mb.className = "pb-menubar";
    win.menus.forEach(m => {
      const item = document.createElement("span");
      item.className = "pb-menu";
      item.textContent = m.text || m.name;
      item.onclick = () => alert("[菜单] " + (m.text || m.name));
      mb.appendChild(item);
    });
    root.appendChild(mb);
  }

  // Position controls
  const byParent = {};
  win.controls.forEach(c => { (byParent[c.parent] = byParent[c.parent] || []).push(c); });

  // Build tab index for switching
  const tabPages = {}; // tab control name -> list of page controls
  (byParent["__tab__"] || []).forEach(() => {});

  function place(parent, xOff, yOff) {
    (byParent[parent] || []).forEach(c => {
      const abs = { ...c, x: c.x + xOff, y: c.y + yOff };
      const el = renderControl(abs);
      root.appendChild(el);
      if (c.type === "tab") {
        // Group pages under this tab
        const pages = (byParent[c.name] || []);
        // Clicking page title switches visibility
        pages.forEach((pg, idx) => {
          if (idx === 0) return; // first visible by default
          const pgEl = root.lastElementChild;
          if (pgEl) pgEl.style.display = "none";
        });
        place(c.name, c.x, c.y + 30);
      }
    });
  }
  place(win.name, 0, 30);
  return root;
}

const tabsEl = document.getElementById("tabs");
const panelsEl = document.getElementById("panels");
WINDOWS.forEach((w, i) => {
  const btn = document.createElement("button");
  btn.className = "tab" + (i === 0 ? " active" : "");
  btn.textContent = (w.title || w.name) + " (" + w.controls.length + ")";
  btn.onclick = () => show(i);
  tabsEl.appendChild(btn);

  const panel = document.createElement("div");
  panel.className = "panel" + (i === 0 ? " active" : "");
  panel.appendChild(renderWindow(w));
  panelsEl.appendChild(panel);
});
function show(i) {
  document.querySelectorAll(".tab").forEach((t,j)=>t.classList.toggle("active", j===i));
  document.querySelectorAll(".panel").forEach((p,j)=>p.classList.toggle("active", j===i));
}
</script>
</body></html>"""

html_doc = html_doc.replace("__DATA__", DATA_JS)
OUT.write_text(html_doc, encoding="utf-8")
print(f"HTML: {OUT}, size: {OUT.stat().st_size//1024}KB")
