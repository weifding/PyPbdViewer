"""PB 9.0 Fake C# 输出，对应 C# PCodeParser90FakeCSharp."""

from pcode_parser90 import PCodeParser90
from code_line import CodeLine


class PCodeParser90FakeCSharp(PCodeParser90):
    """输出伪 C# 语法（&&, ||, !, ==, !=）而非 PowerBuilder 语法."""

    def __init__(self, pb_function):
        super().__init__(pb_function)

    def _on_parse_pcode(self, pcode_op: int, code_line: CodeLine) -> bool:
        result = super()._on_parse_pcode(pcode_op, code_line)
        # 替换操作符为 C# 风格
        if code_line.text:
            code_line.text = (code_line.text
                              .replace(" and ", " && ")
                              .replace(" or ", " || ")
                              .replace(" not ", " !")
                              .replace(" = ", " == ")
                              .replace("<>", "!="))
        return result
