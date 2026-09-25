"""代码行，对应 C# CodeLine."""


class CodeLine:
    def __init__(self, offset: int = 0, text: str = ""):
        self.offset: int = offset
        self.text: str = text
        self.raw_op: int = 0
        self.param: bytes = b""
        self.jmp_type = None  # JmpType
        self.jmp_offset: int = 0
        self.area_start = None  # CodeArea
        self.area_end = None   # CodeArea
        self.indention: int = 0
        self.is_comment: bool = False

    def __repr__(self):
        return f"CodeLine({self.offset}, '{self.text}')"
