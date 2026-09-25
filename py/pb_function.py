"""PB 函数，对应 C# PbFunction."""

from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from pb_object import PbObject
    from pb_function_definition import PbFunctionDefinition
    from pb_variable import PbVariable


class PbFunction:
    def __init__(self, obj: "PbObject"):
        self.obj = obj
        self.entry = obj.entry
        self.project = obj.entry.project
        self.index: int = 0
        self.definition: Optional["PbFunctionDefinition"] = None
        self.pcode_bytes: bytes = b""
        self.debug_bytes: bytes = b""
        self.buffer: bytes = b""
        self.variables: List["PbVariable"] = []

    def to_string(self) -> str:
        name = self.definition.name if self.definition else f"#{self.index:04X}"
        return f"{self.obj}/{name}"
