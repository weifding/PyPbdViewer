"""
PBKiller vm*.dat 解析器
分析不同 PB 版本的 P-Code opcode 表
"""
import struct
import os
from dataclasses import dataclass


@dataclass
class OpcodeEntry:
    opcode: int
    name: str
    operand_len: int
    handler_offset: int


class VmDat:
    """解析 PBKiller 的 vm*.dat"""

    def __init__(self, path: str):
        self.path = path
        self.data = open(path, 'rb').read()
        self._parse_header()

    def _parse_header(self):
        d = self.data
        # 0x00-0x01: opcode table count
        self.opcode_count = struct.unpack_from('<H', d, 0)[0]
        # 0x02-0x03: version major
        self.version_major = struct.unpack_from('<H', d, 2)[0]
        # 0x0C-0x0F: float timestamp
        self.timestamp = struct.unpack_from('<f', d, 0x0C)[0]
        # 0x18-0x19: actual opcode count
        self.real_count = struct.unpack_from('<H', d, 0x18)[0]

    def parse_opcode_table(self) -> list[OpcodeEntry]:
        """解析 opcode 表"""
        entries = []
        # 表从 0x20 开始? 每条目格式待确认
        # 先扫描所有 4 字节对齐的指针
        off = 0x20
        for i in range(self.real_count):
            if off + 8 > len(self.data):
                break
            # 尝试读取: uint16 opcode + uint16 len + uint32 handler
            opcode = struct.unpack_from('<H', self.data, off)[0]
            op_len = struct.unpack_from('<H', self.data, off+2)[0]
            handler = struct.unpack_from('<I', self.data, off+4)[0]
            entries.append(OpcodeEntry(opcode, f'op_{opcode:04X}', op_len, handler))
            off += 8
        return entries

    def extract_strings(self, min_len: int = 5) -> list[str]:
        """提取字符串（opcode 名称）"""
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


def analyze_vm_dir(vm_dir: str):
    """分析整个 vm 目录"""
    print(f"{'File':<16} {'Size':>8} {'Ver':>6} {'Count':>6} {'Strings':>8}")
    print("-" * 60)

    for f in sorted(os.listdir(vm_dir)):
        if not f.startswith('vm') or not f.endswith('.dat'):
            continue
        path = os.path.join(vm_dir, f)
        vm = VmDat(path)
        strings = vm.extract_strings()
        print(f"{f:<16} {len(vm.data):>8} {vm.real_count:>6} {vm.real_count:>6} {len(strings):>8}")

    # 打印 vm169 (PB9, 我们用的版本) 的字符串
    print(f"\n=== vm169.dat 字符串 (opcode 名称?) ===")
    vm169 = VmDat(os.path.join(vm_dir, 'vm169.dat'))
    for s in vm169.extract_strings(4)[:100]:
        print(f"  {s}")


if __name__ == '__main__':
    import sys
    vm_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    analyze_vm_dir(vm_dir)
