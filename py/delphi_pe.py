"""
Delphi PE 文件 DFM 资源提取器
从 Delphi 编译的 EXE 中提取窗体资源 (.dfm)
"""
import struct
import os
from dataclasses import dataclass


@dataclass
class DfmForm:
    form_name: str
    class_name: str
    properties: dict


class DelphiPeParser:
    """解析 PE 文件, 提取 Delphi DFM 资源"""

    def __init__(self, path: str):
        self.path = path
        self.data = open(path, 'rb').read()
        self._parse_pe()

    def _parse_pe(self):
        # DOS header
        e_lfanew = struct.unpack_from('<I', self.data, 0x3C)[0]
        # PE signature
        assert self.data[e_lfanew:e_lfanew+4] == b'PE\0\0', "not PE"
        # COFF header
        coff = e_lfanew + 4
        self.num_sections = struct.unpack_from('<H', self.data, coff+2)[0]
        self.opt_hdr_size = struct.unpack_from('<H', self.data, coff+16)[0]
        # Optional header
        opt = coff + 20
        self.image_base = struct.unpack_from('<I', self.data, opt+28)[0]
        # Section table
        sec_off = opt + self.opt_hdr_size
        self.sections = []
        for i in range(self.num_sections):
            s = sec_off + i * 40
            name = self.data[s:s+8].rstrip(b'\0').decode('ascii', errors='replace')
            vsize = struct.unpack_from('<I', self.data, s+8)[0]
            vaddr = struct.unpack_from('<I', self.data, s+12)[0]
            rawsize = struct.unpack_from('<I', self.data, s+16)[0]
            rawptr = struct.unpack_from('<I', self.data, s+20)[0]
            self.sections.append({
                'name': name, 'vaddr': vaddr, 'vsize': vsize,
                'rawptr': rawptr, 'rawsize': rawsize
            })

    def rva_to_offset(self, rva: int) -> int:
        for s in self.sections:
            if s['vaddr'] <= rva < s['vaddr'] + s['vsize']:
                return rva - s['vaddr'] + s['rawptr']
        return rva

    def extract_resources(self) -> dict:
        """提取 PE 资源目录"""
        # 找 .rsrc section
        rsrc = None
        for s in self.sections:
            if s['name'] == '.rsrc':
                rsrc = s
                break
        if not rsrc:
            return {}

        result = {}
        base = rsrc['rawptr']

        def read_dir(off: int, level: int = 0):
            if level > 3:
                return
            char, ts, maj, minv, named, ids = struct.unpack_from('<IIHHHH', self.data, off)
            for i in range(named + ids):
                entry_off = off + 16 + i * 8
                name_or_id, data_off = struct.unpack_from('<II', self.data, entry_off)
                if name_or_id & 0x80000000:
                    # name string
                    noff = base + (name_or_id & 0x7FFFFFFF)
                    slen = struct.unpack_from('<H', self.data, noff)[0]
                    name = self.data[noff+2:noff+2+slen*2].decode('utf-16-le', errors='replace')
                else:
                    name = str(name_or_id)
                if data_off & 0x80000000:
                    read_dir(base + (data_off & 0x7FFFFFFF), level+1)
                else:
                    data_entry = base + data_off
                    rva, size, codepage = struct.unpack_from('<III', self.data, data_entry)
                    file_off = self.rva_to_offset(rva)
                    result[name] = self.data[file_off:file_off+size]

        read_dir(base)
        return result

    def extract_dfm(self) -> list[bytes]:
        """提取所有 DFM 窗体资源"""
        res = self.extract_resources()
        dfms = []
        for name, data in res.items():
            # Delphi DFM 资源以 'TPF0' 开头
            if data[:4] == b'TPF0':
                dfms.append(data)
        return dfms

    def extract_strings(self, min_len: int = 8) -> list[str]:
        """提取所有可读字符串"""
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

    def find_pbd_related(self) -> list[str]:
        """找 PBD 反编译相关字符串"""
        all_s = self.extract_strings(6)
        keywords = ['PBD', 'PBL', 'ENT*', 'NOD*', 'DAT*', 'HDR*', 'FRE*',
                    'vm82', 'vm117', 'vm149', 'vm169', 'vm196',
                    'PBKiller', 'PowerBuilder', 'pcode', 'opcode',
                    'decompile', 'srw', 'sru', 'srm', 'srf', 'srs', 'sra']
        return [s for s in all_s if any(k in s for k in keywords)]


if __name__ == '__main__':
    import sys
    pe_path = sys.argv[1] if len(sys.argv) > 1 else ''
    if not pe_path:
        print("usage: python delphi_pe.py <exe>")
        sys.exit(1)

    pe = DelphiPeParser(pe_path)
    print(f"Sections: {[s['name'] for s in pe.sections]}")

    dfms = pe.extract_dfm()
    print(f"\nDFM forms: {len(dfms)}")
    for i, d in enumerate(dfms):
        print(f"  [{i}] {len(d)} bytes, head={d[:20]}")

    pbd = pe.find_pbd_related()
    print(f"\nPBD related strings ({len(pbd)}):")
    for s in pbd[:50]:
        print(f"  {s}")
