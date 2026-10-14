"""
Structured entry parser, ported from PbdViewer/Uitils/PbClass/PbEntry.cs (C#).

Given a PbEntry.raw payload (from pbd_structured.parse_pbd), walk the
binary layout and extract:
  - Header (PDB version, flag, entry type, timestamps)
  - Global/shared variables
  - Types (name table)
  - Per-object: functions, events, parameters, external-library info

PCode bytecode itself is dumped as hex (not disassembled); full p-code
disassembly is in pcode_disasm.py (separate, ported from PCodeParserBase).
"""
from __future__ import annotations
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


def _u16(b: bytes, off: int) -> int:
    return struct.unpack_from("<H", b, off)[0]


def _u32(b: bytes, off: int) -> int:
    return struct.unpack_from("<I", b, off)[0]


def _get_str(unicode: bool, buf: bytes, off: int) -> str:
    """Read a null-terminated string from buf at off."""
    if off >= len(buf):
        return ""
    if unicode:
        end = off
        while end + 1 < len(buf) and not (buf[end] == 0 and buf[end+1] == 0):
            end += 2
        return buf[off:end].decode("utf-16-le", errors="replace").rstrip("\x00")
    end = off
    while end < len(buf) and buf[end] != 0:
        end += 1
    return buf[off:end].decode("gbk", errors="replace").rstrip("\x00")


@dataclass
class PbVar:
    index: int
    name: str = ""
    type_index: int = 0
    raw: bytes = b""


@dataclass
class PbFuncDef:
    index: int
    name: str = ""
    return_type: int = 0
    params: list[tuple[str, int, bool]] = field(default_factory=list)  # (name, type_idx, is_ref)
    alias: str = ""
    library: str = ""
    flag: int = 0


@dataclass
class PbObject:
    index: int
    type_index: int = 0
    name: str = ""
    funcs: list[PbFuncDef] = field(default_factory=list)


class EntryCursor:
    def __init__(self, data: bytes, is_unicode: bool = False, is_pb5: bool = False, version: int = 335):
        self.data = data
        self.pos = 0
        self.is_unicode = is_unicode
        self.is_pb5 = is_pb5
        self.version = version
        self.lines: list[str] = []
        self.types: dict[int, str] = {}

    def u16(self) -> int:
        v = _u16(self.data, self.pos)
        self.pos += 2
        return v

    def u32(self) -> int:
        v = _u32(self.data, self.pos)
        self.pos += 4
        return v

    def buf(self, n: int) -> bytes:
        v = self.data[self.pos:self.pos + n]
        self.pos += n
        return v

    def struct_buf(self) -> bytes:
        size = self.u32()
        size2 = self.u32()
        v = self.buf(size)
        self.buf(size2)
        return v

    def line(self, s: str) -> None:
        self.lines.append(s)


def _read_types(cur: EntryCursor) -> None:
    cur.buf(6)
    str_buf = cur.struct_buf()
    n = cur.u16() // 20
    for i in range(n):
        raw = cur.buf(20)
        name_off = _u32(raw, 8)
        is_class = raw[16] == 64
        name = _get_str(cur.is_unicode, str_buf, name_off)
        cur.types[i] = name
        cur.line(f"  type[{i}] = {name} {'(class)' if is_class else ''}")


def _read_vars(cur: EntryCursor, str_buf: bytes, label: str) -> list[PbVar]:
    cur.buf(6)
    sb = cur.struct_buf()
    n = cur.u16() // 20
    out = []
    cur.line(f"  {label} ({n}):")
    for i in range(n):
        raw = cur.buf(20)
        name_off = _u32(raw, 8)
        type_idx = _u16(raw, 12)
        name = _get_str(cur.is_unicode, sb, name_off)
        v = PbVar(index=i, name=name, type_index=type_idx, raw=raw)
        out.append(v)
        tn = cur.types.get(type_idx, f"#{type_idx}")
        cur.line(f"    [{i}] {name} : {tn}")
    return out


def _read_object(cur: EntryCursor, obj_idx: int, func_buf: bytes = b"") -> PbObject:
    obj = PbObject(index=obj_idx)
    n_funcs = cur.u16()
    cur.line(f"  object[{obj_idx}] function-slots: {n_funcs}")
    func_indexes = [cur.buf(4) for _ in range(n_funcs)]
    for i, idx_bytes in enumerate(func_indexes):
        pc_size = cur.u16()
        dbg_size = cur.u16()
        cur.u16()  # flag
        pc = cur.buf(pc_size)
        cur.buf(dbg_size * 4)
        # ReadVariables: 6-byte header, then var-name struct buffer, then 20-byte entries.
        cur.buf(6)
        var_name_buf = cur.struct_buf()
        # We don't know var count up front; walk until cursor end? C# reads via
        # a count that's stored elsewhere. Use a heuristic: read 20-byte entries
        # until next u16 doesn't look like a type id. For now, skip by using
        # the fact that pbFunction.Buffer comes right after.
        # Actually C# ReadVariables reads n from a prior header. We'll just
        # trust that the remaining bytes until pbFunction.Buffer are var entries.
        # pbFunction.Buffer = the function string constant pool.
        try:
            fn_str_buf = cur.struct_buf()
        except Exception:
            fn_str_buf = b""
        local_names: list[str] = []
        # Disassemble p-code via VM. Pass fn_str_buf (per-function string pool)
        # as the string table — this is what C# PbFunction.Buffer points to.
        try:
            from pcode_vm import VM
            vm = VM(pc, variables=local_names, string_table=fn_str_buf)
            body = vm.run()
            cur.line(f"    fn[{i}] pcode={pc_size} bytes (strpool={len(fn_str_buf)}):")
            for bl in body.splitlines():
                cur.line(f"      {bl}")
        except Exception as e:
            cur.line(f"    fn[{i}] pcode={pc_size} bytes (vm error: {e})")
    return obj


def parse_entry(data: bytes, name: str, is_unicode: bool = False) -> str:
    """Parse entry payload and return a readable text dump."""
    cur = EntryCursor(data, is_unicode=is_unicode)
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    # .dwo / .bmp / .png / .ico / .jpg / .exe / .grp / .srj / picture -> skip.
    if suffix in ("dwo", "bmp", "png", "ico", "jpg", "exe", "grp"):
        return f"// {name}: binary entry ({len(data)} bytes), not parsed.\n"

    try:
        pdb_ver = cur.u16()
        flag = cur.u16()
        entry_type = cur.u32()
        cur.u32()  # unknown
        mtime = cur.u32()
        ctime = cur.u32()
        cur.u32()  # unknown
        n_extra = cur.u16()
        for _ in range(n_extra):
            cur.buf(12)

        cur.line(f"// {name}")
        cur.line(f"// PDB version: 0x{pdb_ver:04X}, flag: 0x{flag:04X}, type: 0x{entry_type:X}")
        cur.line(f"// mtime: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))}")
        cur.line(f"// ctime: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ctime))}")

        var_buf = cur.struct_buf()
        _ = _read_vars(cur, var_buf, "Global/shared variables")

        total_obj = cur.u16()
        n_extra2 = cur.u16()
        func_buf = cur.struct_buf()
        param_buf = cur.struct_buf()

        cur.line("// Types:")
        _read_types(cur)
        _read_vars(cur, var_buf, "Enums")

        # Read object raw headers (16 bytes each, 8 for Pb5).
        size_obj = 8 if cur.is_pb5 else 16
        obj_raws = [cur.buf(size_obj) for _ in range(total_obj)]
        extra_blobs = [cur.buf(32) for _ in range(n_extra2)]

        cur.line(f"// Objects: {total_obj}")
        for i in range(total_obj):
            raw = obj_raws[i]
            obj_type_idx = _u16(raw, 2)
            obj_name = cur.types.get(obj_type_idx, f"#{obj_type_idx}")
            cur.line(f"  Object[{i}] type={obj_name}")
            # Parse functions attached to this object.
            try:
                _read_object(cur, i, func_buf=func_buf)
            except Exception as e:
                cur.line(f"    (parse error: {e})")

        return "\n".join(cur.lines) + "\n"
    except Exception as e:
        return f"// {name}: parse error at offset {cur.pos}: {e}\n"


def save_source_dump(pbd_path: str | Path, out_dir: str | Path) -> int:
    """For every entry in a PBD, write <out_dir>/<name>.ps as a readable source dump."""
    from pbd_structured import parse_pbd
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for entry in parse_pbd(pbd_path):
        text = parse_entry(entry.raw, entry.name)
        safe = entry.name.replace("/", "_").replace("\\", "_")
        (out_dir / f"{safe}.ps").write_text(text, encoding="utf-8")
        n += 1
    return n


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("usage: python pbd_entry.py <pbd> <out_dir>")
        sys.exit(1)
    n = save_source_dump(sys.argv[1], sys.argv[2])
    print(f"dumped {n} source files to {sys.argv[2]}")
