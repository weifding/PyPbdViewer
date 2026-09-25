"""代码区域，对应 C# CodeArea."""

from jmp_type import JmpType


class CodeArea:
    def __init__(self, area_type: JmpType = None, start: int = 0, end: int = 0):
        self.area_type = area_type
        self.start: int = start
        self.end: int = end

    def __repr__(self):
        return f"CodeArea({self.area_type}, {self.start}, {self.end})"
