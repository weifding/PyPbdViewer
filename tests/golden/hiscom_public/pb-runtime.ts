
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
