"""PB 11.0 PCode 解析器，对应 C# PCodeParser110."""

from pcode_parser105 import PCodeParser105


class PCodeParser110(PCodeParser105):
    def __init__(self, pb_function):
        super().__init__(pb_function)
