"""PB 类型，对应 C# PbType."""

from typing import Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from pb_object import PbObject
    from pb_enum import PbEnum


# 值类型表: index -> PbType
_value_types: Dict[int, "PbType"] = {}


class PbType:
    # FAKESHARP 模式下的类型名
    VALUE_TYPE_NAMES = {
        0: "", 1: "int", 2: "long", 3: "float", 4: "double",
        5: "decimal", 6: "string", 7: "bool", 8: "dynamic",
        9: "uint", 10: "ulong", 11: "blob", 12: "DateOnly",
        13: "TimeOnly", 14: "DateTime", 15: "cursor", 16: "procedure",
        18: "char", 19: "objhandle", 20: "longlong", 21: "byte",
    }

    def __init__(self, entry=None, index: int = 0, name: str = "",
                 is_referenced_object: bool = False, is_system_entry: bool = False):
        self.index: int = index
        self.name: str = name
        self.is_value_type: bool = False
        self.is_system_type: bool = False
        self.is_referenced_object: bool = is_referenced_object
        self.enum: Optional["PbEnum"] = None
        self.entry = entry  # PbEntry
        self.obj = None  # PbObject
        self._is_finded: bool = False

        if entry is not None:
            # 从 entry 构造
            if not is_system_entry:
                if is_referenced_object:
                    # 查找枚举
                    if entry.project.enums:
                        for e in entry.project.enums.values():
                            if e.name == name:
                                self.enum = e
                                break
                self.index = 32768 | index
                entry.on_new_type(self)
            else:
                if is_referenced_object:
                    raise Exception("system entry can't reference other object")
                self.is_system_type = True
                self.index = 16384 | index
                entry.project.on_new_system_type(self)
        else:
            # 值类型构造
            self.is_value_type = True
            self.name = self._get_value_type_name(index)

    def _get_value_type_name(self, low: int) -> str:
        return self.VALUE_TYPE_NAMES.get(low, f"{low:04X}")

    @staticmethod
    def get_pb_type(pb_entry, index: int) -> "PbType":
        """根据类型索引获取 PbType."""
        high = index >> 12
        if high == 0:
            if index not in _value_types:
                _value_types[index] = PbType(entry=None, index=index)
            return _value_types[index]
        elif high == 4:
            return pb_entry.project.system_types[index]
        elif high == 8:
            return pb_entry.types[index]
        elif high == 12:
            return PbType(entry=None, index=0)
        else:
            raise Exception(f"Unknown Type {index:04X}")

    def get_default_value(self) -> str:
        if self.name in ("int", "long", "float", "decimal", "uint", "ulong"):
            return "0"
        elif self.name == "bool":
            return "false"
        elif self.name == "string":
            return '""'
        elif self.name == "DateTime":
            return "DateTime.MinValue"
        elif "PBArray" in self.name:
            return "new()"
        else:
            return "null"

    def get_object(self, pb_entry) -> Optional["PbObject"]:
        if self.obj is not None:
            return self.obj
        if self.is_value_type:
            return self.obj
        if self._is_finded:
            return self.obj
        if '`' in self.name or self.is_system_type or self.is_referenced_object:
            if self.name in pb_entry.project.objects:
                self.obj = pb_entry.project.objects[self.name]
        else:
            e = self.entry if self.entry is not None else pb_entry
            if self.index in e.objects:
                self.obj = e.objects[self.index]
        self._is_finded = True
        return self.obj
