"""PB 变量，对应 C# PbVariable."""

from typing import Optional, List, TYPE_CHECKING
import buffer_helper
from pb_variable_flag import PbVariableFlag

if TYPE_CHECKING:
    from pb_entry import PbEntry
    from pb_object import PbObject
    from pb_type import PbType


class PbVariable:
    def __init__(self, pb_entry: "PbEntry", index: int, buffer: bytes,
                 struct_buffer: bytes, delay_parse_type: bool = False):
        self.entry = pb_entry
        self.buffer: bytes = buffer
        self.index: int = index
        self.type: Optional["PbType"] = None
        self.flag: int = buffer[17]
        self.precision_or_size: str = ""
        self.name: str = ""
        self.array_string: str = ""
        self.object = None  # PbObject
        self._sql_declear: Optional[str] = None

        self.access_string = ""
        if PbVariableFlag.has_flag(self.flag, PbVariableFlag.IsPrivate):
            self.access_string = "private "
        elif PbVariableFlag.has_flag(self.flag, PbVariableFlag.IsProtected):
            self.access_string = "protected "

        self.is_shared = PbVariableFlag.has_flag(self.flag, PbVariableFlag.IsShared)
        self.is_referenced_global = (buffer[16] & 64) == 64
        self.is_instance = (buffer[0] & 15) <= 1
        self.is_indirect = (buffer[0] & 2) == 2
        self.is_constant = (buffer[0] & 4) == 4

        if not delay_parse_type:
            self.parse_type()

        self.name = buffer_helper.get_string(
            pb_entry.project.is_unicode, struct_buffer,
            buffer_helper.get_uint(buffer, 8))
        self.array_string = self.get_array_string(
            buffer_helper.get_uint(buffer, 4), struct_buffer)

    @property
    def global_index(self) -> int:
        if not self.is_shared:
            return 0xFFFF
        return buffer_helper.get_ushort(self.buffer, 12)

    def parse_type(self):
        from pb_type import PbType
        self.type = PbType.get_pb_type(self.entry, buffer_helper.get_ushort(self.buffer, 18))
        if self.type.is_value_type:
            if self.type.name == "blob":
                us = buffer_helper.get_ushort(self.buffer, 12)
                self.precision_or_size = "" if us == 0 else f"{{{us}}}"
            elif self.type.name == "decimal":
                n = self.buffer[16] & 63
                self.precision_or_size = "" if n == 62 else f"{{{self.buffer[16] // 2}}}"

    def inherit(self, control: "PbObject") -> "PbVariable":
        import copy
        v = copy.copy(self)
        v.type = control.type
        v.entry = control.entry
        v.object = control
        return v

    @staticmethod
    def get_array_string(offset: int, buffer: bytes) -> str:
        if offset == 0xFFFF:
            return ""
        text = "["
        count = buffer[offset]
        for i in range(count):
            if i != 0:
                text += ","
            low = buffer_helper.get_uint(buffer, offset + 4 + i * 8)
            high = buffer_helper.get_uint(buffer, offset + 8 + i * 8)
            if low == 1:
                text += str(high)
            elif low != high or high != 0:
                text += f"{low} to {high}"
        text += "]"
        return text

    def get_value(self, value_buffer: bytes) -> Optional[str]:
        if not PbVariableFlag.has_flag(self.flag, PbVariableFlag.IsCustom):
            return None
        if not self.type.is_value_type and self.type.enum is None:
            return None
        if self.is_indirect or self.is_referenced_global:
            return None
        if not PbVariableFlag.has_flag(self.flag, PbVariableFlag.IsArray):
            return self._read_value(buffer_helper.get_uint(self.buffer, 12), value_buffer, True)
        if PbVariableFlag.has_flag(self.flag, PbVariableFlag.Invalid):
            return None
        lst = self._get_list(value_buffer)
        result = []
        for off in lst:
            result.append(self._read_value(off, value_buffer, True))
        while result and result[-1] is None:
            result.pop()
        for i in range(len(result)):
            if result[i] is None:
                result[i] = self._read_value(lst[i], value_buffer, False)
        return "new [] {" + ",".join(str(r) for r in result if r is not None) + "}"

    def _read_value(self, code: int, value_buffer: bytes, check_is_default: bool):
        if self.type.enum is None:
            name = self.type.name
            # FAKESHARP 模式类型名映射
            type_map = {
                "integer": "int", "long": "long", "real": "float",
                "double": "double", "decimal": "decimal", "string": "string",
                "boolean": "bool", "any": "dynamic", "uint": "uint",
                "ulong": "ulong", "blob": "blob", "date": "DateOnly",
                "time": "TimeOnly", "datetime": "DateTime",
            }
            name = type_map.get(name, name)

            if name in ("int", "integer"):
                if not check_is_default or (code & 0xFFFF) != 0:
                    return str((code & 0xFFFF) - 0x10000 if code & 0x8000 else code & 0xFFFF)
            elif name == "long":
                if not check_is_default or code != 0:
                    v = code
                    if v & 0x80000000:
                        v = v - 0x100000000
                    return str(v)
            elif name in ("float", "real"):
                if not check_is_default or code != 0:
                    return buffer_helper.get_real(code)
            elif name == "double":
                if not check_is_default or not PbVariableFlag.has_flag(self.flag, PbVariableFlag.Invalid) \
                        or buffer_helper.get_double(value_buffer, code) != "0":
                    return buffer_helper.get_double(value_buffer, code)
            elif name == "decimal":
                if not check_is_default or not PbVariableFlag.has_flag(self.flag, PbVariableFlag.Invalid) \
                        or buffer_helper.get_decimal(value_buffer, code) != "0.0":
                    return buffer_helper.get_decimal(value_buffer, code)
            elif name == "string":
                if not check_is_default or not PbVariableFlag.has_flag(self.flag, PbVariableFlag.Invalid) \
                        or buffer_helper.get_string(self.entry.project.is_unicode, value_buffer, code) != "":
                    return buffer_helper.get_escape_string(self.entry.project.is_unicode, value_buffer, code)
            elif name in ("bool", "boolean"):
                if not check_is_default or (code & 0xFF) != 0:
                    return "true" if (code & 0xFF) > 0 else "false"
            elif name == "byte":
                if not check_is_default or (code & 0xFF) != 0:
                    return str(code & 0xFF)
            elif name == "char":
                if not check_is_default or (code & 0xFFFF) != 0:
                    return f"'{chr(code & 0xFFFF)}'"
            elif name == "uint":
                if not check_is_default or (code & 0xFFFF) != 0:
                    return str(code & 0xFFFF)
            elif name == "ulong":
                if not check_is_default or code != 0:
                    return str(code)
            elif name == "DateOnly":
                if not check_is_default or not PbVariableFlag.has_flag(self.flag, PbVariableFlag.Invalid) \
                        or buffer_helper.get_date(value_buffer, code) != "1900-01-01":
                    return buffer_helper.get_date(value_buffer, code)
            elif name == "TimeOnly":
                if not check_is_default or not PbVariableFlag.has_flag(self.flag, PbVariableFlag.Invalid) \
                        or buffer_helper.get_time(value_buffer, code) != "00:00:00":
                    return buffer_helper.get_time(value_buffer, code)
            elif name == "DateTime":
                if not check_is_default or not PbVariableFlag.has_flag(self.flag, PbVariableFlag.Invalid) \
                        or buffer_helper.get_datetime(value_buffer, code) != "datetime(1900-01-01,00:00:00)":
                    return buffer_helper.get_datetime(value_buffer, code)
            elif name == "longlong":
                if not check_is_default or not PbVariableFlag.has_flag(self.flag, PbVariableFlag.Invalid) \
                        or buffer_helper.get_long_long(value_buffer, code) != "0":
                    return buffer_helper.get_long_long(value_buffer, code)
            return None
        else:
            if not check_is_default or (code & 0xFFFF) != 0:
                return self.type.enum.items.get(code & 0xFFFF, str(code))
            return None

    def _get_list(self, value_buffer: bytes) -> List[int]:
        result = []
        us = buffer_helper.get_ushort(self.buffer, 12)
        us2 = buffer_helper.get_ushort(value_buffer, us + 14)
        n = us + 28 + us2 * 8
        count = buffer_helper.get_uint(value_buffer, n)
        for i in range(count):
            result.append(buffer_helper.get_uint(value_buffer, n + 4 + 8 * i))
        return result

    def to_string(self, value_buffer: bytes = None, debug: bool = False) -> str:
        # FAKESHARP 模式
        def get_fake_type(t: str, size: str) -> str:
            if t == "decimal" and size == "{0}":
                return "Decimal0"
            if t == "decimal" and size == "{1}":
                return "Decimal1"
            if t == "decimal" and size == "{2}":
                return "Decimal2"
            if t == "decimal" and size == "{3}":
                return "Decimal3"
            if t == "decimal" and size == "{4}":
                return "Decimal4"
            return t + size

        if not self.array_string:
            text = f"{self.access_string}{get_fake_type(self.type.name, self.precision_or_size)} {self.name}"
        else:
            text = f"{self.access_string}PBArray<{get_fake_type(self.type.name, self.precision_or_size)}> {self.name}"

        if self._sql_declear is not None:
            text = self._sql_declear
        if self.is_constant:
            text = "constant " + text
        if debug:
            if self.is_referenced_global:
                text = "global " + text
            elif self.is_shared:
                text = "shared " + text
            text = buffer_helper.get_hex_string(self.buffer) + "  " + text
        if value_buffer is not None:
            val = None
            if not self.is_referenced_global:
                val = self.get_value(value_buffer)
            if val is not None:
                text += f" = {val}"
        return text

    def set_cursor_params(self, param_list, sqlca_str: str):
        if self._sql_declear is None:
            self._sql_declear = buffer_helper.get_cursor(
                self.entry.project.is_unicode, self.entry.variable_buffer,
                buffer_helper.get_uint(self.buffer, 12), param_list)
            self._sql_declear = f"declare {self.name} cursor for {self._sql_declear} using {sqlca_str} ;"
