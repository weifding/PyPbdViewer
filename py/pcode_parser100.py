"""PB 10.0 PCode 解析器，对应 C# PCodeParser100."""

from pcode_parser90 import PCodeParser90
from code_line import CodeLine


class PCodeParser100(PCodeParser90):
    def __init__(self, pb_function):
        super().__init__(pb_function)

    def _on_parse_pcode(self, pcode_op: int, code_line: CodeLine) -> bool:
        if pcode_op >= 29:
            pcode_op -= 2
        return super()._on_parse_pcode(pcode_op, code_line)
