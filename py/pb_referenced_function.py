"""PB 引用函数/事件，对应 C# PbReferencedFunction."""

import buffer_helper


class PbReferencedFunction:
    def __init__(self, index: int = 0, buffer: bytes = None):
        self.index: int = index
        self.name: str = ""
        self.global_index: int = 0
        self.is_global_function: bool = False
        if buffer is not None:
            self.global_index = buffer_helper.get_ushort(buffer, 12)
            self.is_global_function = (buffer[16] == 2)

    def to_string(self, debug: bool = False) -> str:
        prefix = "global " if self.is_global_function else ""
        return f"{prefix}{self.name}"
