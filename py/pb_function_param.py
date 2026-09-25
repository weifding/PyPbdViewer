"""PB 函数参数，对应 C# PbFunctionParam."""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pb_type import PbType


class PbFunctionParam:
    def __init__(self):
        self.is_read_only: bool = False
        self.is_reference: bool = False
        self.type: Optional["PbType"] = None
        self.name: str = ""
        self.array_string: str = ""
