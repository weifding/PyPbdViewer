"""
IDA Pro 数据库文件解析器
解析 .id0/.id1/.id2/.nam/.til 文件, 提取函数名/类型名/字符串
"""
import struct
import os
from dataclasses import dataclass


@dataclass
class NameEntry:
    address: int
    name: str


@dataclass
class TypeEntry:
    kind: str
    name: str
    details: str


class IdaId0:
    """.id0 主数据库 (B-tree v2)"""
    MAGIC = b'B-tree v2'

    def __init__(self, path: str):
        self.path = path
        self.data = open(path, 'rb').read()
        self._parse_header()

    def _parse_header(self):
        # 偏移 0x13: "B-tree v2"
        assert self.data[0x13:0x1C] == self.MAGIC, "not B-tree v2"
        # 偏移 0x00: 未知
        # 偏移 0x04: 文件大小相关
        pass

    def extract_strings(self, min_len: int = 6) -> list[str]:
        """提取所有可读 ASCII 字符串"""
        result = []
        cur = []
        for b in self.data:
            if 32 <= b <= 126:
                cur.append(chr(b))
            else:
                if len(cur) >= min_len:
                    result.append(''.join(cur))
                cur = []
        if len(cur) >= min_len:
            result.append(''.join(cur))
        return result

    def extract_pbd_strings(self) -> list[str]:
        """提取 PBD 相关字符串"""
        all_strings = self.extract_strings()
        keywords = ['PBD', 'PBL', 'ENT', 'NOD', 'DAT', 'HDR', 'FRE', 'TRL',
                    'PBKiller', 'PowerBuilder', 'pcode', 'opcode', 'decompile',
                    'vm82', 'vm117', 'vm149', 'vm169', 'vm196']
        return [s for s in all_strings if any(k.lower() in s.lower() for k in keywords)]


class IdaVaDb:
    """.id1 / .nam 数据库 (VA* 格式)"""
    MAGIC = b'VA*'

    def __init__(self, path: str):
        self.path = path
        self.data = open(path, 'rb').read()
        assert self.data[:3] == self.MAGIC, f"not VA*: {self.data[:3]}"

    def _read_uint32(self, off: int) -> int:
        return struct.unpack_from('<I', self.data, off)[0]

    def extract_names(self) -> list[NameEntry]:
        """提取名称表 (仅 .nam 适用)"""
        entries = []
        # VA* 格式:
        # 0x00: magic "VA*"
        # 0x03: version
        # 0x04: count
        # 0x08: ???
        # 0x0C: ???
        # 0x10: 名称表起始
        count = self._read_uint32(0x04)
        # 名称表从 0x10 开始, 每项: uint32 address + uint8 name_len + name
        off = 0x10
        for _ in range(count):
            if off + 5 > len(self.data):
                break
            addr = self._read_uint32(off)
            namelen = self.data[off + 4]
            off += 5
            if off + namelen > len(self.data):
                break
            name = self.data[off:off + namelen].decode('ascii', errors='replace')
            entries.append(NameEntry(addr, name))
            off += namelen
        return entries

    def extract_strings(self, min_len: int = 4) -> list[str]:
        result = []
        cur = []
        for b in self.data:
            if 32 <= b <= 126:
                cur.append(chr(b))
            else:
                if len(cur) >= min_len:
                    result.append(''.join(cur))
                cur = []
        if len(cur) >= min_len:
            result.append(''.join(cur))
        return result


class IdaId2:
    """.id2 数据库 (IDAS 格式)"""
    MAGIC = b'IDAS'

    def __init__(self, path: str):
        self.path = path
        self.data = open(path, 'rb').read()
        assert self.data[:4] == self.MAGIC, "not IDAS"

    def extract_strings(self, min_len: int = 6) -> list[str]:
        result = []
        cur = []
        for b in self.data:
            if 32 <= b <= 126:
                cur.append(chr(b))
            else:
                if len(cur) >= min_len:
                    result.append(''.join(cur))
                cur = []
        if len(cur) >= min_len:
            result.append(''.join(cur))
        return result


class IdaTil:
    """.til 类型库 (IDATIL 格式)"""
    MAGIC = b'IDATIL'

    def __init__(self, path: str):
        self.path = path
        self.data = open(path, 'rb').read()
        assert self.data[:6] == self.MAGIC, "not IDATIL"

    def extract_types(self) -> list[TypeEntry]:
        """提取类型定义"""
        result = []
        off = 6  # 跳过 magic
        while off < len(self.data):
            # 格式: uint8 len + string
            if off >= len(self.data):
                break
            slen = self.data[off]
            off += 1
            if off + slen > len(self.data):
                break
            s = self.data[off:off + slen].decode('ascii', errors='replace')
            off += slen
            if len(s) > 3:
                result.append(TypeEntry(kind='unknown', name=s, details=''))
        return result

    def extract_strings(self, min_len: int = 4) -> list[str]:
        result = []
        cur = []
        for b in self.data:
            if 32 <= b <= 126:
                cur.append(chr(b))
            else:
                if len(cur) >= min_len:
                    result.append(''.join(cur))
                cur = []
        if len(cur) >= min_len:
            result.append(''.join(cur))
        return result


def analyze_ida_dir(ida_dir: str) -> dict:
    """分析整个 IDA 数据库目录"""
    result = {
        'id0_strings': [],
        'id0_pbd': [],
        'nam_names': [],
        'nam_strings': [],
        'id2_strings': [],
        'til_types': [],
        'til_strings': [],
    }

    id0_path = os.path.join(ida_dir, 'PBKiller.exe.id0')
    if os.path.exists(id0_path):
        id0 = IdaId0(id0_path)
        result['id0_strings'] = id0.extract_strings(8)
        result['id0_pbd'] = id0.extract_pbd_strings()

    nam_path = os.path.join(ida_dir, 'PBKiller.exe.nam')
    if os.path.exists(nam_path):
        nam = IdaVaDb(nam_path)
        result['nam_names'] = nam.extract_names()
        result['nam_strings'] = nam.extract_strings(6)

    id2_path = os.path.join(ida_dir, 'PBKiller.exe.id2')
    if os.path.exists(id2_path):
        id2 = IdaId2(id2_path)
        result['id2_strings'] = id2.extract_strings(8)

    til_path = os.path.join(ida_dir, 'PBKiller.exe.til')
    if os.path.exists(til_path):
        til = IdaTil(til_path)
        result['til_types'] = til.extract_types()
        result['til_strings'] = til.extract_strings(6)

    return result


if __name__ == '__main__':
    import sys
    ida_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    r = analyze_ida_dir(ida_dir)

    print(f"=== .id0 PBD 相关字符串 ===")
    for s in r['id0_pbd'][:50]:
        print(f"  {s}")

    print(f"\n=== .nam 函数名 (前50) ===")
    for e in r['nam_names'][:50]:
        print(f"  0x{e.address:08X}  {e.name}")

    print(f"\n=== .til 类型 (前30) ===")
    for t in r['til_types'][:30]:
        print(f"  {t.name}")
