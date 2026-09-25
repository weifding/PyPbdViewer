"""PCode 解析入口和控制流恢复，对应 C# PCodeHelper."""

from typing import List
import buffer_helper
from code_line import CodeLine
from pcode_parser90 import PCodeParser90
from pcode_parser100 import PCodeParser100
from pcode_parser105 import PCodeParser105
from pcode_parser110 import PCodeParser110


class PCodeHelper:
    @staticmethod
    def parse_pcode(func, debug: bool = False) -> List[str]:
        """解析函数的 P-Code，返回代码行列表."""
        pcode_bytes = func.pcode_bytes
        if not pcode_bytes:
            return []

        # 根据版本选择解析器
        version = func.project.version
        if version >= 400:
            parser = PCodeParser110(func)
        elif version >= 350:
            parser = PCodeParser105(func)
        elif version >= 300:
            parser = PCodeParser100(func)
        else:
            parser = PCodeParser90(func)

        # 第一步：逐条解析 P-Code 指令
        lines: List[CodeLine] = []
        pos = 0

        while pos < len(pcode_bytes):
            raw_op = buffer_helper.get_ushort(pcode_bytes, pos)
            pcode_len = parser.get_pcode_len(raw_op)
            if pcode_len == 255:
                break

            param_len = pcode_len * 2
            end = min(pos + 2 + param_len, len(pcode_bytes))
            param = pcode_bytes[pos + 2:end]

            if debug:
                print(f"    pos={pos:#06x} op=0x{raw_op:04X} len={pcode_len} param={param.hex()}")
                for i in range(pcode_len):
                    v = buffer_helper.get_ushort(param, i*2)
                    print(f"      [{i}]={v} (0x{v:04X})")

            line = CodeLine(offset=pos)
            line.raw_op = raw_op
            line.param = param
            line.text = ""
            try:
                parser.parse_pcode(line)
            except Exception as e:
                line.text = f"// 解析失败 opcode {raw_op:04X}: {type(e).__name__}: {e}"
            lines.append(line)
            pos = end

        # 第二步：恢复控制流
        PCodeHelper._restore_control_flow(lines)

        # 第三步：生成文本
        result = []
        indent = 0
        for line in lines:
            text = line.text if line.text else f"// opcode {line.raw_op:03X}"
            result.append("\t" * indent + text)

        return result

    @staticmethod
    def _restore_control_flow(lines: List[CodeLine]):
        """恢复控制流结构."""
        pass
