"""PB 10.5 PCode 解析器，对应 C# PCodeParser105."""

from pcode_parser100 import PCodeParser100
from code_line import CodeLine


class PCodeParser105(PCodeParser100):
    def __init__(self, pb_function):
        super().__init__(pb_function)

    def _on_parse_pcode(self, pcode_op: int, code_line: CodeLine) -> bool:
        if pcode_op == 0:
            code_line.text = ""
            return True
        if pcode_op == 1:
            code_line.text = ""
            return True
        pcode_op -= 1
        return super()._on_parse_pcode(pcode_op, code_line)
