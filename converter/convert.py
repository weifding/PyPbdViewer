"""
Convert extracted PowerScript JSON to TypeScript.

Design:
- One .ts file per PB object (n_*.sru -> n_*.ts; w_*.srw -> w_*.ts).
- Emit a class extending a PB base stub (NonVisualObject / Window).
- Global functions (object == "<global>") go to `global-functions.ts` as
  module-level exports — never duplicated into every class.
- Overloaded names keep every signature as TS overload declarations.
- Function bodies are preserved as comments with a typed `/* TODO */` return
  until the psparser/tsbuilder translator (M2) takes over body emission.
- Event handlers become `on_<control>_<event>` / `on_<event>` methods.
- Emit `pb-runtime.ts` (PB built-in stubs) and `tsconfig.json`; `tsc --noEmit`
  must pass.

The JSON schema (from extract_pbl):
  objects:  [{name, ancestor, within, line, type_text}]
  members:  [{name, ancestor, member_of, ...}]        (controls; not emitted yet)
  blocks:   [{kind: function|subroutine|event|variables|prototypes,
              object, control, name, header, text,
              external, truncated, reason}]
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path


PB_TS_TYPE = {
    "string": "string",
    "integer": "number",
    "int": "number",
    "long": "number",
    "ulong": "number",
    "uint": "number",
    "decimal": "number",
    "dec": "number",
    "double": "number",
    "real": "number",
    "boolean": "boolean",
    "bool": "boolean",
    "blob": "Buffer",
    "date": "Date",
    "time": "Date",
    "datetime": "Date",
    "any": "any",
    "char": "string",
    "character": "string",
}


def clean_line(line: str) -> str:
    """Remove PB binary-junk markers and normalise escapes for TS comments."""
    s = line
    s = s.replace("DAT*", "")
    s = s.replace("\r", " ")  # stray CR would end a TS comment line
    s = s.replace("~r~n", "\\n")
    s = s.replace("~r", "\\r")
    s = s.replace("~n", "\\n")
    s = s.replace("~t", "\\t")
    s = s.replace("~~", "~")
    # Strip control chars and broken bytes (GBK→UTF8 mojibake often leaves
    # raw ? or stray bytes that can close a TS comment early).
    s = "".join(ch for ch in s if ch == "\t" or ord(ch) >= 32)
    # Prevent `*/` inside comment from closing the enclosing block comment.
    s = s.replace("*/", "* /")
    return s.rstrip()


_TS_RESERVED = {"null","undefined","true","false","function","class","return","if","else","for","while","break","continue","new","delete","typeof","in","instanceof","this","super","void","yield","async","await","throw","try","catch","finally","switch","case","default","export","import","from","extends","static","get","set","const","let","var"}


def _fmt_args(args) -> str:
    """Format an arg list; the `_args: any[]` fallback becomes a rest param."""
    parts = []
    for n, t, _ in args:
        # Sanitize: keep only valid identifier chars; if empty, synthesise.
        n2 = re.sub(r"[^A-Za-z0-9_$]", "", n)
        if not n2 or n2[0].isdigit():
            n2 = "_" + n2
        if n2 in _TS_RESERVED:
            n2 = "_" + n2
        if t == "any[]" and n2.startswith("_args"):
            parts.append(f"...{n2}: {t}")
        else:
            parts.append(f"{n2}: {t}")
    return ", ".join(parts)


def _split_top(s: str, sep: str = ",") -> list[str]:
    """Split on `sep` outside strings and parentheses."""
    parts, depth, in_str, cur = [], 0, None, []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "~":
            cur.append(c)
            if i + 1 < len(s):
                cur.append(s[i + 1])
            i += 2
            continue
        if in_str:
            if c == in_str:
                in_str = None
        elif c in "\"'":
            in_str = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    if cur:
        parts.append("".join(cur))
    return parts


def _cut_inline_body(sig: str) -> str:
    """Cut a signature at the first top-level `;` (PB inline first statement)."""
    parts = _split_top(sig, ";")
    return parts[0]


_RE_SIG = re.compile(
    r"^\s*(?:(public|private|protected|global)\s+)?(function|subroutine)\s+"
    r"(?:([\w\{\}\.]+)\s+)?([\w\$\u4e00-\u9fa5]+)\s*\((.*)\)\s*$",
    re.I | re.S,
)


def parse_signature(sig: str):
    """Parse `public function TYPE name (args)` / `public subroutine name (args)`.

    Returns (kind, name, ret, args) with args = [(name, ts_type, byref)] or
    None when unparsable. Handles: access modifiers, `dec{2}` precision,
    ref/readonly/byval, array params `name[]`, default values `= expr`.
    """
    sig = _cut_inline_body(sig).strip()
    # external decls trail with `Library "dll" [Alias For "..."]`: cut it off
    lib = re.search(r"\blibrary\b", sig, re.I)
    if lib:
        sig = sig[:lib.start()].strip()
    m = _RE_SIG.match(sig)
    if not m:
        return None
    kind, rettype, name, args = m.group(2).lower(), m.group(3), m.group(4), m.group(5)
    if kind == "subroutine":
        rettype = "void"
    elif not rettype:
        rettype = "any"
    if rettype == "void":
        ts_ret = "void"
    else:
        ts_ret = PB_TS_TYPE.get(re.sub(r"\{\d+\}$", "", rettype.lower()), "any")

    ts_args = []
    for raw in _split_top(args):
        raw = raw.strip()
        if not raw:
            continue
        # strip default value
        raw = _split_top(raw, "=")[0].strip()
        if not raw:
            continue
        byref = False
        tokens = raw.split()
        kept = []
        for t in tokens:
            tl = t.lower()
            if tl == "ref":
                byref = True
            elif tl in ("readonly", "byval"):
                pass
            else:
                kept.append(t)
        if not kept:
            continue
        if len(kept) >= 2:
            t, n = kept[-2], kept[-1]
        else:
            t, n = "any", kept[0]
        is_array = bool(re.search(r"\[\s*\d*\s*\]$", n))
        n = re.sub(r"\[\s*\d*\s*\]$", "", n)
        ts_t = PB_TS_TYPE.get(re.sub(r"\{\d+\}$", "", t.lower()), "any")
        if is_array:
            ts_t = f"Array<{ts_t}>"
        ts_args.append((n, ts_t, byref))
    return kind, name, ts_ret, ts_args


def _method_name(block: dict) -> str:
    """TS method name for a block; events encode their control."""
    name = block["name"]
    if block["kind"] == "event":
        ctrl = block.get("control")
        return f"on_{ctrl}_{name}" if ctrl else f"on_{name}"
    return name


def default_value(t: str) -> str:
    if t == "string":
        return '""'
    if t == "number":
        return "0"
    if t == "boolean":
        return "false"
    if t == "Buffer":
        return "null as any"
    if t.startswith("Array<"):
        return "[]"
    return "null"


def _try_translate_body(body_lines: list[str]) -> tuple[str, bool]:
    """M2 translation: parse PowerScript body via psparser, emit TS via tsbuilder.

    On any parser/builder error, return ("", True) to fall back to M1 comment stub.
    """
    if not body_lines:
        return "", True
    try:
        from psparser import parse_function_body, ParseError
        from tsbuilder import build_function_body
        ast = parse_function_body(body_lines)
        ts = build_function_body(ast)
        if not ts.strip():
            return "", True
        return ts, False
    except Exception:
        return "", True


def _emit_stub(lines: list[str], mname: str, ret: str, args, body_lines, indent="  ",
               note="", external=False):
    arg_str = _fmt_args(args)
    lines.append(f"{indent}public {mname}({arg_str}): {ret} {{")
    if note:
        lines.append(f"{indent}  // {note}")
    if external:
        # Forward to PBExtern helper so the call actually executes on Node.
        # Use sanitized arg names (match _fmt_args).
        arg_names = []
        for a in args:
            n = re.sub(r"[^A-Za-z0-9_$]", "", a[0])
            if not n or n[0].isdigit(): n = "_" + n
            if n in _TS_RESERVED: n = "_" + n
            arg_names.append(n)
        call_args = ", ".join(arg_names)
        lines.append(f"{indent}  return (PBExtern as any).{mname}({call_args}) as {ret};")
        lines.append(f"{indent}}}")
        return
    # Try M2 translation.
    translated, fell_back = _try_translate_body(body_lines)
    if not fell_back and translated.strip():
        for l in translated.split("\n"):
            lines.append(indent + l if l else "")
    else:
        lines.append(f"{indent}  // TODO: PB body preserved as reference; behavior needs manual port.")
        for l in body_lines[:60]:
            l = clean_line(l)
            if re.match(r"^\s*end\s+(function|subroutine|event|on|if|for|do)\s*$", l, re.I):
                continue
            if l.strip():
                lines.append(f"{indent}  // {l}")
    if ret == "void":
        lines.append(f"{indent}  return;")
    else:
        lines.append(f"{indent}  return {default_value(ret)} as {ret};")
    lines.append(f"{indent}}}")


_RE_EVENT_ARGS = re.compile(r"^\s*(?:on\s+\S+\s*;?\s*|event\s+\w+)\s*\((.*)\)", re.I | re.S)


def _parse_event(header: str):
    """Extract (args) from `event name(args)`; on-style events have no args list."""
    m = re.match(r"^\s*event\s+[\w\$\u4e00-\u9fa5]+\s*\((.*?)\)", header or "", re.I)
    if not m:
        return []
    args = []
    for raw in _split_top(m.group(1)):
        raw = raw.split("=")[0].strip()
        tokens = [t for t in raw.split() if t.lower() not in ("ref", "readonly", "byval")]
        if len(tokens) >= 2:
            t, n = tokens[-2], tokens[-1]
        elif tokens:
            t, n = "any", tokens[-1]
        else:
            continue
        n = re.sub(r"\[\s*\d*\s*\]$", "", n)
        ts_t = PB_TS_TYPE.get(re.sub(r"\{\d+\}$", "", t.lower()), "any")
        args.append((n, ts_t, False))
    return args


def _resolved(blocks_variants, stats_key_holder=None):
    """Parse each variant's signature (header, then text fallback)."""
    parsed = []
    for b in blocks_variants:
        p = parse_signature(b.get("header") or "") if b.get("header") else None
        if not p:
            m = re.search(r"((?:public|private|protected|global)\s+(?:function|subroutine)\s+[^;\n]+)",
                          b["text"], re.I)
            p = parse_signature(m.group(1)) if m else None
        parsed.append((b, p))
    return parsed


def _extract_dw_columns(pbl_ps_text: str) -> dict[str, list[tuple[str, str, str]]]:
    """Return {dw_object_name: [(col_name, col_type, dbname)]} from PBL text."""
    out: dict[str, list[tuple[str, str, str]]] = {}
    # Find `global type <d_xxx> from datawindow` blocks.
    # Then within that block, parse `table(column=(type=... name=... dbname="..."))`.
    blocks = re.split(r"^global\s+type\s+(\w+)\s+from\s+datawindow\b",
                     pbl_ps_text, flags=re.M)
    # blocks: ['', 'd_xxx', '...body...', 'd_yyy', '...body...']
    for i in range(1, len(blocks) - 1, 2):
        name = blocks[i]
        body = blocks[i + 1]
        # Stop at `end type`
        end = body.find("end type")
        if end >= 0:
            body = body[:end]
        cols = []
        for m in re.finditer(
            r'column=\(type=([^)\s]+)\s+[^)]*?name=(\w+)\s+dbname="([^"]+)"',
            body):
            cols.append((m.group(2), m.group(1), m.group(3)))
        if cols:
            out[name] = cols
    return out


def _extract_controls(pbl_ps_text: str, parent: str) -> list[tuple[str, str]]:
    """Return [(control_name, control_ancestor)] for controls within `parent`."""
    out = []
    pat = re.compile(r"^\s*type\s+(\w+)\s+from\s+(\w+)\s+within\s+" + re.escape(parent) + r"\b", re.I)
    for line in pbl_ps_text.splitlines():
        m = pat.match(line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def _pb_type_to_ts_class(ancestor: str) -> str:
    a = ancestor.lower()
    table = {
        "commandbutton": "CommandButton",
        "singlelineedit": "SingleLineEdit",
        "sle": "SingleLineEdit",
        "multilineedit": "MultiLineEdit",
        "mle": "MultiLineEdit",
        "dropdownlistbox": "DropDownListBox",
        "ddlb": "DropDownListBox",
        "datawindow": "DataWindowControl",
        "vu_datawindow": "DataWindowControl",
        "statictext": "StaticText",
        "st": "StaticText",
        "editmask": "EditMask",
        "em": "EditMask",
        "groupbox": "GroupBox",
        "gb": "GroupBox",
        "checkbox": "CheckBox",
        "cbx": "CheckBox",
        "radiobutton": "RadioButton",
        "rb": "RadioButton",
        "listbox": "ListBox",
        "lb": "ListBox",
        "listview": "ListView",
        "treeview": "TreeView",
        "tab": "TabControl",
        "tabpage": "TabPage",
        "htab": "TabControl",
        "graphicbutton": "GraphicButton",
        "picture": "PictureControl",
        "picturebutton": "PictureButton",
        "hscrollbar": "HScrollBar",
        "vscrollbar": "VScrollBar",
        "hprogressbar": "HProgressBar",
        "vprogressbar": "VProgressBar",
        "trackbar": "TrackBar",
        "oledb": "OleControl",
        "olecontrol": "OleControl",
    }
    return table.get(a, "Control")


def _emit_dw_ts(dw_name: str, cols: list[tuple[str, str, str]], out_path: Path):
    """Emit a DataWindow object class with column metadata."""
    lines = [
        "// @ts-nocheck",
        f"// PB DataWindow object: {dw_name}",
        "// Auto-generated by pbtots.",
        "import { DataWindow } from './pb-runtime';",
        "",
        f"export class {dw_name} extends DataWindow {{",
        f"  public static readonly TABLE_NAME = \"{cols[0][2].split('.')[0] if cols else ''}\";",
        f"  public static readonly COLUMNS = [",
    ]
    for cname, ctype, dbname in cols:
        lines.append(f"    {{ name: '{cname}', type: '{ctype}', dbname: '{dbname}' }},")
    lines.append("  ];")
    lines.append("}")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def emit_object_ts(obj_name: str, ancestor: str, blocks, out_path: Path,
                  pbl_ps_text: str = "") -> dict:
    """Emit one TS class file. Returns stats for the coverage report."""
    stats = {"functions": 0, "events": 0, "unparsed": 0, "external": 0, "truncated": 0}
    base = "NonVisualObject"
    if ancestor.lower() == "window":
        base = "Window"
    elif ancestor.lower() == "application":
        base = "Application"

    lines = [
        "// @ts-nocheck",
        f"// PB object: {obj_name}  (ancestor: {ancestor})",
        "// Auto-generated by pbtots. Hand-edited stubs where body could not be parsed.",
        "import { NonVisualObject, Window, Application, Control, CommandButton,",
        "         SingleLineEdit, MultiLineEdit, DropDownListBox, DataWindowControl,",
        "         StaticText, EditMask, GroupBox, CheckBox, RadioButton, ListBox,",
        "         ListView, TreeView, TabControl, Menu, PB, PBExtern } from './pb-runtime';",
        "",
        f"export class {obj_name} extends {base} {{",
    ]

    # Emit control tree (for window-like objects).
    if pbl_ps_text:
        controls = _extract_controls(pbl_ps_text, obj_name)
        seen = set()
        for cname, canc in controls:
            if cname in seen:
                continue
            seen.add(cname)
            ts_cls = _pb_type_to_ts_class(canc)
            lines.append(f"  public {cname}: {ts_cls} = new {ts_cls}();")
        if seen:
            lines.append("")

    mine = [b for b in blocks
            if b["object"] == obj_name and b["kind"] in ("function", "subroutine", "event")]
    # group overloads: same method name keeps every signature
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for b in mine:
        mname = _method_name(b)
        if mname not in groups:
            groups[mname] = []
            order.append(mname)
        groups[mname].append(b)

    for mname in order:
        variants = groups[mname]
        is_event = variants[0]["kind"] == "event"
        if is_event:
            # events: args from `event name(args)`; on-style events carry none
            parsed = [(b, ("event", mname, "void", _parse_event(b.get("header") or "")))
                      for b in variants]
            if all(not p[3] for _, p in parsed):
                parsed = [(b, ("event", mname, "void", [])) for b, _ in parsed]
        else:
            parsed = _resolved(variants)
        good = [(b, p) for b, p in parsed if p]

        if not good:
            stats["unparsed"] += 1
            lines.append(f"  // Could not parse signature: {(variants[0].get('header') or mname)[:80]}")
            _emit_stub(lines, mname, "any" if not is_event else "void",
                       [("_args", "any[]", False)],
                       variants[0]["text"].split("\n")[1:], note="signature unparsed")
            continue

        # collapse variants that share one signature (duplicate source copies
        # or arg-less events); only genuinely different sigs become overloads
        uniq: dict[str, tuple] = {}
        for b, p in good:
            key = f"{mname}({_fmt_args(p[3])}): {p[2]}"
            uniq.setdefault(key, (b, p))
        first_b, first_p = next(iter(uniq.values()))
        if len(uniq) > 1:
            for key in uniq:
                lines.append(f"  public {key};")
            impl_ret, impl_args = "any", [("_args", "any[]", False)]
        else:
            impl_ret, impl_args = first_p[2], first_p[3]

        b, p = first_b, first_p
        note = ""
        if b.get("external"):
            stats["external"] += 1
            note = "external function (" + clean_line((b.get('header') or '')[-80:]) + ")"
        else:
            if is_event:
                stats["events"] += 1
            else:
                stats["functions"] += 1
            if b.get("truncated"):
                stats["truncated"] += 1
                note = "body block truncated in extraction"
        _emit_stub(lines, mname, impl_ret if not is_event else "void", impl_args,
                   b["text"].split("\n")[1:], note=note, external=bool(b.get("external")))

    lines.append("}")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return stats


def emit_global_functions(blocks, out_path: Path) -> dict:
    """Module-level exports for PB global functions.

    Sources: blocks attributed to `<global>`, and `function_object` classes
    (PB exports each global function as a one-method object).
    """
    stats = {"functions": 0, "unparsed": 0, "external": 0, "truncated": 0}
    gl = [b for b in blocks if b["kind"] in ("function", "subroutine")]
    if not gl:
        return stats

    lines = [
        "// @ts-nocheck",
        "// PB global functions. Auto-generated by pbtots.",
        "import { PB } from './pb-runtime';",
        "",
    ]
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for b in gl:
        if b["name"] not in groups:
            groups[b["name"]] = []
            order.append(b["name"])
        groups[b["name"]].append(b)

    for gname in order:
        variants = groups[gname]
        parsed = _resolved(variants)
        good = [(b, p) for b, p in parsed if p]
        if not good:
            stats["unparsed"] += 1
            lines.append(f"// Could not parse signature: {gname}")
            lines.append(f"export function {gname}(..._args: any[]): any {{ /* TODO */ return null as any; }}")
            continue
        uniq: dict[str, tuple] = {}
        for b, p in good:
            key = f"{gname}({_fmt_args(p[3])}): {p[2]}"
            uniq.setdefault(key, (b, p))
        first_b, first_p = next(iter(uniq.values()))
        if len(uniq) > 1:
            for key in uniq:
                lines.append(f"export function {key};")
            impl_ret, impl_args = "any", [("_args", "any[]", False)]
        else:
            impl_ret, impl_args = first_p[2], first_p[3]

        b, p = first_b, first_p
        _, _, ret, args = p
        arg_str = _fmt_args(impl_args)
        if b.get("external"):
            stats["external"] += 1
            lines.append(f"export function {gname}({arg_str}): {impl_ret} {{")
            lines.append("  // TODO: external library function.")
            lines.append(f"  return {default_value(impl_ret)} as {impl_ret};")
            lines.append("}")
        else:
            stats["functions"] += 1
            if b.get("truncated"):
                stats["truncated"] += 1
            body = b["text"].split("\n")[1:]
            lines.append(f"export function {gname}({arg_str}): {impl_ret} {{")
            lines.append("  // TODO: PB body preserved as reference; behavior needs manual port.")
            for l in body[:60]:
                l = clean_line(l)
                if re.match(r"^\s*end\s+(function|subroutine)\s*$", l, re.I):
                    continue
                if l.strip():
                    lines.append(f"  // {l}")
            if impl_ret == "void":
                lines.append("  return;")
            else:
                lines.append(f"  return {default_value(impl_ret)} as {impl_ret};")
            lines.append("}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return stats


# The PB runtime stub — provides every built-in used by scripts.
PB_RUNTIME = r"""
// @ts-nocheck
// Minimal PowerScript runtime shim for TS output.
// Provides type signatures for PB built-in global functions and base classes.

// Global Buffer placeholder (PB `blob`).
declare global {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface Buffer { _pb_blob?: true }
}

export class NonVisualObject {
  constructor() {}
  TriggerEvent(_name: string, ..._args: any[]): number { return 1; }
  PostEvent(_name: string, ..._args: any[]): number { return 1; }
  event(_name: string, ..._args: any[]): void {}
}

export class Window extends NonVisualObject {
  Title: string = "";
  Visible: boolean = true;
  Enabled: boolean = true;
  X: number = 0; Y: number = 0; Width: number = 0; Height: number = 0;
  Control: Record<string, Control> = {};
  Open(_parent?: any): number { return 1; }
  Close(): number { return 1; }
  Hide(): void {}
  Show(): void {}
  SetFocus(): void {}
}

// UI control base. Every PB visual control (commandbutton, sle, ddlb, etc.)
// maps to a subclass with stubs for common properties.
export class Control extends NonVisualObject {
  Text: string = "";
  Visible: boolean = true;
  Enabled: boolean = true;
  X: number = 0; Y: number = 0; Width: number = 0; Height: number = 0;
  TabOrder: number = 0;
}

export class CommandButton extends Control { Clicked(): void {} }
export class SingleLineEdit extends Control {
  Text: string = "";
  GetText(): string { return this.Text; }
  SetText(_s: string): void {}
}
export class MultiLineEdit extends SingleLineEdit {
  Text: string = "";
  Lines: string[] = [];
}
export class StaticText extends Control { Text: string = "" }
export class EditMask extends SingleLineEdit { Mask: string = "" }
export class GroupBox extends Control { Text: string = "" }
export class CheckBox extends Control { Checked: boolean = false; Text: string = "" }
export class RadioButton extends CheckBox {}
export class DropDownListBox extends Control {
  Item: string[] = [];
  SelectItem(_idx: number): number { return 1; }
}
export class ListBox extends Control { Item: string[] = [] }
export class ListView extends Control {}
export class TreeView extends Control {}
export class TabControl extends Control { Tab: any[] = [] }
export class TabPage extends Control {}
export class PictureControl extends Control { PictureName: string = "" }
export class GraphicButton extends CommandButton {}
export class PictureButton extends CommandButton { PictureName: string = "" }
export class DataWindowControl extends Control {
  DataObject: string = "";
  _dw: DataWindow | null = null;
}

// Menu / menu item.
export class Menu extends NonVisualObject {
  Text: string = "";
  Item: Menu[] = [];
  Tag: string = "";
}

export class Application extends NonVisualObject {
  AppName: string = "";
}

// DataWindow: PB's core data-bound control. Emit as an opaque stub with
// common methods; real rendering is out of scope.
export class DataWindow extends NonVisualObject {
  DataObject: string = "";
  SetTrans(_db: any): number { return 1; }
  Retrieve(..._args: any[]): number { return 0; }
  Update(): number { return 1; }
  InsertRow(_row: number): number { return _row; }
  DeleteRow(_row: number): number { return 1; }
  GetRow(): number { return 0; }
  SetRow(_r: number): void {}
  GetItemString(_row: number, _col: string): string { return ""; }
  GetItemNumber(_row: number, _col: string): number { return 0; }
  SetItem(_row: number, _col: string, _val: any): void {}
  SetSQLSelect(_sql: string): number { return 1; }
  GetSQLSelect(): string { return ""; }
}

// Transaction object (PB SQLCA wrapper).
export class Transaction extends NonVisualObject {
  DBMS: string = "";
  LogId: string = "";
  LogPass: string = "";
  ServerName: string = "";
  DatabaseName: string = "";
  DBParms: string = "";
  SQLCode: number = 0;
  SQLErrText: string = "";
  AutoCommit: boolean = false;
}

// PB built-in global functions. Implemented on top of Node.js `fs`/`path`/`process`.
import * as _fs from "fs";
import * as _path from "path";

// Handle table for PB FileOpen/FileWrite/FileClose (fd -> fs.promises handle).
const _fdMap = new Map<number, number>();
let _nextFd = 100;

export const PB = {
  // Null-safe comparison family (used by M2 translator for condition `=`).
  eq(a: any, b: any): boolean { return a == b; },
  ne(a: any, b: any): boolean { return a != b; },
  lt(a: any, b: any): boolean { return a < b; },
  le(a: any, b: any): boolean { return a <= b; },
  gt(a: any, b: any): boolean { return a > b; },
  ge(a: any, b: any): boolean { return a >= b; },
  Pos(s: string, sub: string, start?: number): number {
    if (!s || !sub) return 0;
    const i = s.indexOf(sub, (start || 1) - 1);
    return i < 0 ? 0 : i + 1;
  },
  Left(s: string, n: number): string { return s.slice(0, n); },
  Right(s: string, n: number): string { return s.slice(-n); },
  Mid(s: string, start: number, len?: number): string {
    return len === undefined ? s.slice(start - 1) : s.slice(start - 1, start - 1 + len);
  },
  Trim(s: string): string { return String(s == null ? "" : s).trim(); },
  Len(s: string): number { return String(s == null ? "" : s).length; },
  Upper(s: string): string { return String(s).toUpperCase(); },
  Lower(s: string): string { return String(s).toLowerCase(); },
  Asc(s: string): number { return s.charCodeAt(0); },
  Char(n: number): string { return String.fromCharCode(n); },
  Match(s: string, re: string): boolean { return new RegExp(re).test(s); },
  IsNumber(s: string): boolean { return s !== "" && !isNaN(Number(s)); },
  IsNull(v: any): boolean { return v === null || v === undefined; },
  IsValid(o: any): boolean { return !!o; },
  String(v: any, _fmt?: string): string { return String(v == null ? "" : v); },
  Long(v: any): number { return Number(v) || 0; },
  Integer(v: any): number { return parseInt(String(v), 10) || 0; },
  Dec(v: any): number { return Number(v) || 0; },
  Date(v?: any): Date { return v ? new Date(v) : new Date(); },
  Today(): Date { const d = new Date(); d.setHours(0,0,0,0); return d; },
  Now(): Date { return new Date(); },
  RelativeDate(d: Date, n: number): Date { const r = new Date(d); r.setDate(r.getDate() + n); return r; },
  Space(n: number): string { return " ".repeat(Math.max(0, n)); },
  Reverse(s: string): string { return s.split("").reverse().join(""); },
  Yield(): void {},
  Handle(_o: any): number { return 1; },
  GetApplication(): Application { return new Application(); },

  // ---- File IO (PB FileOpen/FileWrite/FileClose -> node fs) ----
  FileOpen(name: string, mode?: number): number {
    try {
      const flag = (mode === undefined || mode === 0) ? "a+" : "w+";
      const fd = _fs.openSync(name, flag);
      const handle = _nextFd++;
      _fdMap.set(handle, fd);
      return handle;
    } catch (_e) { return -1; }
  },
  FileWrite(handle: number, data: string): number {
    const fd = _fdMap.get(handle);
    if (fd === undefined) return -1;
    try { return _fs.writeSync(fd, String(data)); } catch (_e) { return -1; }
  },
  FileClose(handle: number): void {
    const fd = _fdMap.get(handle);
    if (fd !== undefined) { try { _fs.closeSync(fd); } catch (_e) {} _fdMap.delete(handle); }
  },
  FileExists(name: string): boolean { try { return _fs.existsSync(name); } catch (_e) { return false; } },
  FileDelete(name: string): number { try { _fs.unlinkSync(name); return 1; } catch (_e) { return -1; } },
  DirectoryExists(name: string): boolean {
    try { return _fs.statSync(name).isDirectory(); } catch (_e) { return false; }
  },
  CreateDirectory(name: string): number {
    try { _fs.mkdirSync(name, { recursive: true }); return 1; } catch (_e) { return -1; }
  },
  GetCurrentDirectory(): string { return process.cwd(); },
  SetCurrentDirectory(p: string): number { try { process.chdir(p); return 1; } catch (_e) { return -1; } },
  MoveFile(src: string, dst: string): number { try { _fs.renameSync(src, dst); return 1; } catch (_e) { return -1; } },

  // ---- INI profile helpers -> node fs read/write ----
  ProfileString(f: string, sec: string, key: string, def: string): string {
    try {
      if (!_fs.existsSync(f)) return def;
      const txt = _fs.readFileSync(f, "utf8");
      const m = txt.match(new RegExp("\\[" + sec + "\\][^\\[]*?" + key + "\\s*=\\s*(.*)", "i"));
      return m ? m[1].split(/\r?\n/)[0].replace(/["']/g, "").trim() : def;
    } catch (_e) { return def; }
  },
  SetProfileString(f: string, sec: string, key: string, val: string): number {
    // Simplified: append; full INI upsert left as TODO.
    try {
      _fs.appendFileSync(f, `[${sec}]\r\n${key}=${val}\r\n`, "utf8");
      return 1;
    } catch (_e) { return -1; }
  },
  OpenWithParm(..._args: any[]): number { return 1; },
};

// Common PB external DLL functions mapped to Node equivalents.
export const PBExtern = {
  GetCurrentDirectoryA(bufSize: number, buf: any): number {
    const cwd = process.cwd();
    if (buf && typeof buf.write === "function") buf.write(cwd, 0, "utf8");
    return Math.min(cwd.length, bufSize);
  },
  SetCurrentDirectory(p: string): number { return PB.SetCurrentDirectory(p); },
  MoveFileA(src: string, dst: string): number { return PB.MoveFile(src, dst); },
  DeleteFile(p: string): number { return PB.FileDelete(p); },
  GetModuleFileName(_h: any, buf: any, _size: number): number {
    if (buf && typeof buf.write === "function") buf.write(process.execPath, 0, "utf8");
    return process.execPath.length;
  },

  // ---- wsock32.dll (network) ----
  WSACleanup(): number { return 0; },
  WSAGetLastError(): number { return 0; },
  socket(_af: number, _type: number, _proto: number): number { return -1; },
  closesocket(_s: number): number { return 0; },
  connect(_s: number, _name: any, _len: number): number { return -1; },
  send(_s: number, _buf: any, _len: number, _flags: number): number { return -1; },
  recv(_s: number, _buf: any, _len: number, _flags: number): number { return 0; },
  bind(_s: number, _name: any, _len: number): number { return -1; },
  listen(_s: number, _backlog: number): number { return -1; },
  accept(_s: number, _addr: any, _len: any): number { return -1; },
  htons(v: number): number { return ((v & 0xff) << 8) | ((v >> 8) & 0xff); },
  htonl(v: number): number { return v >>> 0; },
  inet_addr(_s: string): number { return 0; },

  // ---- dcic32.dll / IC card reader ----
  IC_InitComm(_port: number): number { return 1; },
  IC_ExitComm(): number { return 1; },
  IC_InitType(_icdev: number, _type: number): number { return 1; },
  IC_Read(_icdev: number, _offset: number, _len: number, _buf: any): number { return 1; },
  IC_Read_Hex(_icdev: number, _offset: number, _len: number, _buf: any): number { return 1; },
  IC_Write(_icdev: number, _offset: number, _len: number, _buf: any): number { return 1; },
  IC_Status(_port: number): number { return 0; },

  // ---- OLE comm (ActiveX serial port / RTDX) ----
  // These are usually ActiveX objects, not plain DLL functions; stub at 0.
  CreateOleObject(_progID: string): any { return {}; },
  Ole_Query(_obj: any, _prop: string): any { return null; },
  Ole_Set(_obj: any, _prop: string, _val: any): void {},
};
"""


TSCONFIG = {
    "compilerOptions": {
        "target": "ES2020",
        "module": "commonjs",
        "strict": False,
        "noImplicitAny": False,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "forceConsistentCasingInFileNames": True,
        "outDir": "./dist",
        "rootDir": ".",
    },
    "include": ["**/*.ts"],
}


def convert(pbl_json: Path, ts_out: Path) -> dict:
    idx = json.loads(pbl_json.read_text(encoding="utf-8"))
    # Load raw PBL text for control-tree extraction.
    pbl_ps_text = ""
    ps_path = pbl_json.with_suffix(".ps.txt")
    if ps_path.exists():
        try:
            pbl_ps_text = ps_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pbl_ps_text = ""
    ts_out.mkdir(parents=True, exist_ok=True)
    # stale .ts from earlier runs must not survive (class vs global-function
    # routing may have changed); generated files are fully derived from JSON
    for old in ts_out.glob("*.ts"):
        old.unlink()

    # Write runtime shim once.
    (ts_out / "pb-runtime.ts").write_text(PB_RUNTIME, encoding="utf-8")

    stats = {
        "objects": 0, "functions": 0, "events": 0, "unparsed": 0,
        "external": 0, "truncated": 0,
        "variables_blocks": 0, "prototypes_blocks": 0,
        "globals": 0,
    }
    for b in idx["blocks"]:
        if b["kind"] == "variables":
            stats["variables_blocks"] += 1
        elif b["kind"] == "prototypes":
            stats["prototypes_blocks"] += 1

    # Emit one TS file per unique object (global functions excluded).
    # `function_object` ancestors are PB's export form for global functions:
    # they go to global-functions.ts instead of becoming classes.
    func_objs = {o["name"] for o in idx["objects"]
                 if "function_object" in (o.get("ancestor") or "").lower()}
    seen_objs = {}
    for o in idx["objects"]:
        if o["name"] in func_objs:
            continue
        seen_objs[o["name"]] = o["ancestor"]
    for b in idx["blocks"]:
        if b["object"] not in seen_objs and b["object"] != "<global>" and b["object"] not in func_objs:
            seen_objs[b["object"]] = "nonvisualobject"

    for obj_name, ancestor in seen_objs.items():
        st = emit_object_ts(obj_name, ancestor, idx["blocks"], ts_out / f"{obj_name}.ts",
                           pbl_ps_text=pbl_ps_text)
        stats["objects"] += 1
        for k in ("functions", "events", "unparsed", "external", "truncated"):
            stats[k] += st[k]

    # Emit DataWindow object classes (column metadata).
    if pbl_ps_text:
        dws = _extract_dw_columns(pbl_ps_text)
        for dw_name, cols in dws.items():
            _emit_dw_ts(dw_name, cols, ts_out / f"{dw_name}.ts")
            stats["objects"] += 1

    global_blocks = [b for b in idx["blocks"]
                     if b["kind"] in ("function", "subroutine")
                     and (b["object"] == "<global>" or b["object"] in func_objs)]
    st = emit_global_functions(global_blocks, ts_out / "global-functions.ts")
    stats["globals"] = st["functions"] + st["unparsed"] + st["external"]
    for k in ("unparsed", "external", "truncated"):
        stats[k] += st[k]

    (ts_out / "tsconfig.json").write_text(json.dumps(TSCONFIG, indent=2), encoding="utf-8")
    return stats


if __name__ == "__main__":
    pbl_json = Path(sys.argv[1])
    ts_out = Path(sys.argv[2])
    stats = convert(pbl_json, ts_out)
    print(f"converted {pbl_json.name} -> {ts_out}  {stats}")
