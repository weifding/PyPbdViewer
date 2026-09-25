"""二进制缓冲区读取工具，对应 C# BufferHelper."""

import struct
from typing import Iterable


def _mask_offset(offset: int) -> int:
    """offset 清除最高位，对应 C# offset &= 0x7FFFFFFF."""
    return offset & 0x7FFFFFFF


def get_buffer(buffer: bytes, offset: int, size: int) -> bytes:
    offset = _mask_offset(offset)
    size = min(size, len(buffer) - offset)
    return buffer[offset:offset + size]


def get_hex_string(buffer: bytes, offset: int = None, size: int = None) -> str:
    if offset is not None and size is not None:
        buffer = get_buffer(buffer, offset, size)
    return " ".join(f"{b:02X}" for b in buffer)


def get_ushort(buffer: bytes, offset: int) -> int:
    """大端序无符号 16 位整数."""
    offset = _mask_offset(offset)
    return ((buffer[offset + 1] << 8) | buffer[offset]) & 0xFFFF


def get_uint(buffer: bytes, offset: int) -> int:
    """大端序无符号 32 位整数."""
    offset = _mask_offset(offset)
    return ((buffer[offset + 3] << 24) |
            (buffer[offset + 2] << 16) |
            (buffer[offset + 1] << 8) |
            buffer[offset]) & 0xFFFFFFFF


def get_date(buffer: bytes, offset: int) -> str:
    offset = _mask_offset(offset)
    year = get_ushort(buffer, offset + 4) + 1900
    month = buffer[offset + 6] + 1
    day = buffer[offset + 7]
    return f"{year}-{month:02d}-{day:02d}"


def get_datetime(buffer: bytes, offset: int) -> str:
    return f"datetime({get_date(buffer, offset)},{get_time(buffer, offset)})"


def get_time(buffer: bytes, offset: int) -> str:
    offset = _mask_offset(offset)
    h = buffer[offset + 8]
    m = buffer[offset + 9]
    s = buffer[offset + 10]
    text = f"{h:02d}:{m:02d}:{s:02d}"
    ms = get_uint(buffer, offset) // 1000
    if ms != 0:
        text += f".{ms:03d}"
    return text


def get_escape_string(is_unicode: bool, buffer: bytes, offset: int) -> str:
    s = get_string(is_unicode, buffer, offset)
    s = s.replace("~", "~~").replace("\r", "~r").replace("\n", "~n").replace("\t", "~t").replace('"', '~"')
    return f'"{s}"'


def get_string(is_unicode: bool, buffer: bytes, offset: int) -> str:
    offset = _mask_offset(offset)
    num = offset
    n = len(buffer)
    if is_unicode:
        while num < n:
            if buffer[num] == 0 and buffer[num + 1] == 0:
                break
            num += 2
    else:
        while num < n and buffer[num] != 0:
            num += 1
    if num - offset == 0:
        return ""
    if not is_unicode:
        return buffer[offset:num].decode('mbcs', errors='replace')
    return buffer[offset:num].decode('utf-16-le', errors='replace')


def get_decimal(buffer: bytes, offset: int) -> str:
    """16 字节 decimal: ushort 标志, byte 小数位, 其余 13 字节整数."""
    offset = _mask_offset(offset)
    sign = get_ushort(buffer, offset)
    scale = buffer[offset + 2]
    # 整数部分: offset+4 (4字节) + offset+8 (4字节) + offset+12 (2字节<<64)
    val = (get_uint(buffer, offset + 4) +
           (get_uint(buffer, offset + 8) << 32) +
           (get_ushort(buffer, offset + 12) << 64))
    text = str(val)
    if scale > 0:
        if len(text) <= scale:
            text = text.zfill(scale + 1)
        text = text[:len(text) - scale] + "." + text[len(text) - scale:]
        text = text.rstrip("0")
        if text.endswith("."):
            text += "0"
    if sign > 0:
        text = "-" + text
    return text


def get_real(code: int) -> str:
    """将 uint code 按小端序解释为 float."""
    b = bytes([
        code & 0xFF,
        (code >> 8) & 0xFF,
        (code >> 16) & 0xFF,
        (code >> 24) & 0xFF,
    ])
    return str(struct.unpack('<f', b)[0])


def get_double(buffer: bytes, offset: int) -> str:
    offset = _mask_offset(offset)
    return str(struct.unpack_from('<d', buffer, offset)[0])


def get_long_long(buffer: bytes, offset: int) -> str:
    offset = _mask_offset(offset)
    return str(struct.unpack_from('<q', buffer, offset)[0])


def get_cursor(is_unicode: bool, data: bytes, offset: int, param_list: Iterable[str]) -> str:
    """递归解析 SQL 游标模板，将占位符替换为参数名."""
    num = offset & 0x7FFFFFFF
    if get_uint(data, num + 8) != 0xFFFF:
        return get_cursor(is_unicode, data, get_uint(data, num + 8), param_list)
    sql = get_string(is_unicode, data, get_uint(data, num + 24))
    if param_list is None:
        return sql
    result = ""
    num2 = get_uint(data, num + 16)
    pos = 0
    for arg in param_list:
        mark = get_ushort(data, num2)
        end_pos = get_ushort(data, num2 + 2)
        num2 += 4
        if mark == 0 and end_pos == 0:
            break
        result += sql[pos:mark] + f":{arg}"
        pos = end_pos
    result += sql[pos:]
    return result
