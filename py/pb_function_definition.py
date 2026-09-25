"""PB 函数定义，对应 C# PbFunctionDefinition."""

from typing import List, Optional, TYPE_CHECKING
from pb_function_flag import PbFunctionFlag

if TYPE_CHECKING:
    from pb_object import PbObject
    from pb_type import PbType
    from pb_function_param import PbFunctionParam


class PbFunctionDefinition:
    def __init__(self):
        self.obj: Optional["PbObject"] = None
        self.index: int = 0
        self.flag: int = 0
        self.return_type: Optional["PbType"] = None
        self.name: str = ""
        self.global_index: int = 0
        self.ref_index: int = 0
        self.event_code: int = 0
        self.params: List["PbFunctionParam"] = []
        self.library: str = ""
        self.alias: str = ""
        self.throws_type: Optional["PbType"] = None

    def to_string(self) -> str:
        flags = []
        if PbFunctionFlag.has_flag(self.flag, PbFunctionFlag.IsPrivate):
            flags.append("private")
        if PbFunctionFlag.has_flag(self.flag, PbFunctionFlag.IsPublic):
            flags.append("public")
        if PbFunctionFlag.has_flag(self.flag, PbFunctionFlag.IsProtected):
            flags.append("protected")
        if PbFunctionFlag.has_flag(self.flag, PbFunctionFlag.IsEvent):
            flags.append("event")
        flag_str = " ".join(flags)

        param_strs = []
        for p in self.params:
            ref = "ref " if p.is_reference else ("readonly " if p.is_read_only else "")
            param_strs.append(f"{ref}{p.type.name}{p.array_string} {p.name}")

        ret = self.return_type.name if self.return_type else "?"
        return f"{flag_str} function {ret} {self.name}({', '.join(param_strs)})"
