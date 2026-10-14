
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
}

export class Application extends NonVisualObject {
  AppName: string = "";
}

// PB built-in global functions. Each is typed to accept loose args.
export const PB = {
  Pos(s: string, sub: string, start?: number): number { return 0; },
  Left(s: string, n: number): string { return s.slice(0, n); },
  Right(s: string, n: number): string { return s.slice(-n); },
  Mid(s: string, start: number, len?: number): string {
    return len === undefined ? s.slice(start - 1) : s.slice(start - 1, start - 1 + len);
  },
  Trim(s: string): string { return s.trim(); },
  Len(s: string): number { return s.length; },
  Upper(s: string): string { return s.toUpperCase(); },
  Lower(s: string): string { return s.toLowerCase(); },
  Asc(s: string): number { return s.charCodeAt(0); },
  Char(n: number): string { return String.fromCharCode(n); },
  Match(s: string, re: string): boolean { return new RegExp(re).test(s); },
  IsNumber(s: string): boolean { return !isNaN(Number(s)); },
  IsNull(v: any): boolean { return v === null || v === undefined; },
  IsValid(o: any): boolean { return !!o; },
  String(v: any, fmt?: string): string { return String(v); },
  Long(v: any): number { return Number(v); },
  Integer(v: any): number { return parseInt(String(v), 10); },
  Dec(v: any): number { return Number(v); },
  Date(v?: any): Date { return new Date(); },
  Today(): Date { return new Date(); },
  Now(): Date { return new Date(); },
  RelativeDate(d: Date, n: number): Date { const r = new Date(d); r.setDate(r.getDate() + n); return r; },
  Space(n: number): string { return " ".repeat(n); },
  Reverse(s: string): string { return s.split("").reverse().join(""); },
  Yield(): void {},
  Handle(o: any): number { return 1; },
  GetApplication(): Application { return new Application(); },
  FileOpen(_name: string, ..._flags: any[]): number { return 1; },
  FileWrite(_h: number, _data: string): number { return 0; },
  FileClose(_h: number): void {},
  FileExists(_name: string): boolean { return false; },
  FileDelete(_name: string): number { return 1; },
  DirectoryExists(_name: string): boolean { return false; },
  CreateDirectory(_name: string): number { return 1; },
  ProfileString(_f: string, _sec: string, _key: string, _def: string): string { return _def; },
  SetProfileString(_f: string, _sec: string, _key: string, _val: string): number { return 1; },
  OpenWithParm(..._args: any[]): number { return 1; },
};
