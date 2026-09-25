"""PB 条目（对象），对应 C# PbEntry."""

from typing import List, Dict, Optional
import buffer_helper
from pb_type import PbType
from pb_variable import PbVariable
from pb_function_param import PbFunctionParam
from pb_function_definition import PbFunctionDefinition
from pb_referenced_function import PbReferencedFunction
from pb_function import PbFunction
from pb_object import PbObject


class PbEntry:
    def __init__(self, pb_file, entry_name: str, entry_data: bytes):
        self._entry_data = entry_data
        self.file = pb_file
        self.entry_name = entry_name
        self.project = pb_file.project

        dot_pos = entry_name.rfind('.')
        self.name = entry_name[:dot_pos] if dot_pos >= 0 else entry_name
        self.suffix = entry_name[dot_pos + 1:] if dot_pos >= 0 else ""

        self.variable_buffer: bytes = b""
        self._function_buffer: bytes = b""
        self._param_buffer: bytes = b""
        self.types: Dict[int, PbType] = {}
        self.variables: List[PbVariable] = []
        self.objects: Dict[int, PbObject] = {}
        self.entry_object: Optional[PbObject] = None
        self.source: str = ""
        self.modified_time = None
        self.complied_time = None

        self._is_parsed = False
        self._flag: int = 0
        self._indent: int = 0
        self._data_buffer: bytes = b""
        self._position: int = 0
        self._sb: List[str] = []
        self._is_debug: bool = True

        # 根据后缀名处理特殊类型
        suffix = self.suffix
        if suffix in ("win", "apl", "udo", "str", "fun", "men"):
            # 库文件类型
            self.project.on_system_library(buffer_helper.get_ushort(entry_data, 0))
        elif suffix == "grp":
            self.project.on_system_entry(self)
            self.parse_object(True)
        elif suffix == "exe":
            self._parse_exe()
            self._is_parsed = True
        elif suffix == "dwo":
            self.source = "DataWindow可以通过PB接口函数导出"
            self._is_parsed = True
        elif suffix == "srj":
            self._parse_srj()
            self._is_parsed = True
        elif suffix in ("bmp", "png", "ico", "jpg"):
            self._is_parsed = True
        else:
            self.source = self.project.get_string(entry_data)
            self._is_parsed = True

    # ---- 打印辅助 ----
    def _print_string(self, s: str):
        self._sb.append("\t" * self._indent + s + "\n")

    def _print_buffer(self, buff: bytes, step: int):
        n = len(buff) // step
        for i in range(n):
            self._print_string(f"{i:04X}:{i*step:04X}   " + buffer_helper.get_hex_string(buff, i * step, step))
        rem = len(buff) - n * step
        if rem > 0:
            self._print_string(f"{n:04X}:{n*step:04X}   " + buffer_helper.get_hex_string(buff, n * step, rem))

    class _IndentBlock:
        def __init__(self, entry, name: str):
            self.entry = entry
            entry._print_string(name + " {")
            entry._indent += 1

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.entry._indent -= 1
            self.entry._print_string("}")

    # ---- 二进制读取 ----
    def _read_ushort(self) -> int:
        self._position += 2
        return buffer_helper.get_ushort(self._data_buffer, self._position - 2)

    def _read_uint(self) -> int:
        self._position += 4
        return buffer_helper.get_uint(self._data_buffer, self._position - 4)

    def _read_buffer(self, size: int) -> bytes:
        self._position += size
        return buffer_helper.get_buffer(self._data_buffer, self._position - size, size)

    def _read_struct_buffer(self) -> bytes:
        size = self._read_uint()
        size2 = self._read_uint()
        result = self._read_buffer(size)
        self._read_buffer(size2)
        return result

    @staticmethod
    def _get_time(timestamp: int):
        import datetime
        return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=timestamp)

    # ---- 对象解析 ----
    def parse_object(self, is_system: bool = False):
        if self._is_parsed:
            return
        self._sb.clear()
        self._data_buffer = self._entry_data
        self._position = 0

        self._print_string(f"Pdb Version: {self._read_ushort():X}")
        self._flag = self._read_ushort()
        self._print_string(f"Flag: {self._flag:X}")
        entry_type = self._read_uint()
        self._print_string(f"EntryType: {entry_type:X}")
        unk = self._read_uint()
        self._print_string(f"Unkown: {unk:X}")

        self.modified_time = self._get_time(self._read_uint())
        if self.project.version >= 334:
            self._read_uint()
        self._print_string(f"Last Modify Time: {self.modified_time}")

        self.complied_time = self._get_time(self._read_uint())
        if self.project.version >= 334:
            self._read_uint()
        self._print_string(f"Last Complied Time: {self.complied_time}")

        unk2 = self._read_uint()
        self._print_string(f"Unkown: {unk2:X}")

        num_entries = self._read_ushort()
        for _ in range(num_entries):
            self._read_buffer(12)

        self.variable_buffer = self._read_struct_buffer()
        self.variables = self._read_variables(True)

        total_obj_num = self._read_ushort()
        num6 = self._read_ushort()

        self._function_buffer = self._read_struct_buffer()
        self._param_buffer = self._read_struct_buffer()

        with self._IndentBlock(self, "Types"):
            self._read_types(is_system)

        for v in self.variables:
            v.parse_type()

        with self._IndentBlock(self, "Global and Shared Variables"):
            for k, v in enumerate(self.variables):
                self._print_string(f"{k:02X}:  " + v.to_string(self.variable_buffer, self._is_debug))

        enum_vars = self._read_variables(False)
        with self._IndentBlock(self, "Enums"):
            for l, v in enumerate(enum_vars):
                self._print_string(f"{l:02X}:  " + v.to_string(None, self._is_debug))
                idx = buffer_helper.get_ushort(v.buffer, 12)
                self.project.on_new_enum_item(v.type, idx, v.name)

        # 对象原始数据
        size = 8 if self.project.is_pb5 else 16
        obj_raw_data = [self._read_buffer(size) for _ in range(total_obj_num)]
        array4 = [self._read_buffer(32) for _ in range(num6)]

        num7 = 0
        with self._IndentBlock(self, f"Objects: {total_obj_num}"):
            index = 0
            while index < total_obj_num:
                raw = obj_raw_data[index]
                ptype = PbType.get_pb_type(self, buffer_helper.get_ushort(raw, 2))
                obj = PbObject(self, index, ptype)
                num9 = (raw[0] >> 1) & 7
                if num9 == 0:
                    info = array4[num7]
                    num7 += 1
                    obj.inherit_type = PbType.get_pb_type(self, buffer_helper.get_ushort(info, 0))
                    obj.parent_type = PbType.get_pb_type(self, buffer_helper.get_ushort(info, 2))
                    self.objects[obj.type.index] = obj

                    if is_system:
                        self.project.on_new_object(obj, None)
                    elif ptype.name == self.name:
                        self.entry_object = obj
                        self.project.on_new_object(obj, None)
                    elif '`' not in ptype.name:
                        self.project.on_new_object(obj, self.name + "`" + ptype.name)

                    with self._IndentBlock(self, f"Object[{index}] {ptype.name}:{obj.inherit_type.name}"):
                        self._print_buffer(raw, 16)
                        self._print_buffer(info, len(info))
                        self._read_object(obj, info)
                index += 1

        self.source = "".join(self._sb)
        self._sb.clear()
        if self._position != len(self._data_buffer):
            raise Exception("读取错误")
        self._is_parsed = True

    def _read_object(self, obj: PbObject, info: bytes):
        num = self._read_ushort()
        obj.functions = [None] * num
        with self._IndentBlock(self, f"Functions: {num}"):
            arr = [self._read_buffer(4) for _ in range(num)]
            for j in range(num):
                obj.functions[j] = PbFunction(obj)
                self._read_function(obj.functions[j], arr[j])

        num = buffer_helper.get_ushort(info, 24)
        self._read_buffer(6 * num)
        num = buffer_helper.get_ushort(info, 22)
        self._read_buffer(4 * num)
        obj.referenced_functions = self._read_referenced_functions()

        with self._IndentBlock(self, f"Referenced Functions And Events: {len(obj.referenced_functions)}"):
            for k, rf in enumerate(obj.referenced_functions):
                self._print_string(f"{k:02X}:  " + rf.to_string(self._is_debug))

        obj.variables = self._read_variables(False)
        with self._IndentBlock(self, f"Properties Or Controls: {len(obj.variables)}"):
            for l, v in enumerate(obj.variables):
                v.object = obj
                self._print_string(f"{l:02X}:  " + v.to_string(self.variable_buffer, self._is_debug))

        us = buffer_helper.get_ushort(info, 28)
        self._read_buffer(8 * us)
        obj.all_variables = [None] * us

        num2 = 12 if self.project.is_pb5 else 16
        num = buffer_helper.get_ushort(info, 26)
        buff = self._read_buffer(num2 * num)
        self._print_buffer(buff, num2)

        num = buffer_helper.get_ushort(info, 4)
        num3 = 48 if self.project.version > 146 else (32 if self.project.is_pb5 else 44)
        obj.function_definitions = [None] * num
        obj.all_function_definitions = [None] * buffer_helper.get_ushort(info, 16)

        with self._IndentBlock(self, "Events And Functions"):
            for num4 in range(num):
                arr2 = self._read_buffer(num3)
                self._print_buffer(arr2, num3)
                fd = PbFunctionDefinition()
                obj.function_definitions[num4] = fd
                fd.obj = obj
                fd.index = num4
                fd.flag = arr2[27 if self.project.is_pb5 else 31]
                fd.return_type = PbType.get_pb_type(
                    self, buffer_helper.get_ushort(arr2, 24 if self.project.is_pb5 else 28))
                fd.name = buffer_helper.get_string(
                    self.project.is_unicode, self._function_buffer,
                    buffer_helper.get_uint(arr2, 0))
                if fd.name.startswith("+"):
                    fd.name = fd.name[1:]
                fd.global_index = buffer_helper.get_ushort(arr2, 16 if self.project.is_pb5 else 20)
                fd.ref_index = buffer_helper.get_ushort(arr2, 18 if self.project.is_pb5 else 22)
                fd.event_code = buffer_helper.get_ushort(arr2, 28 if self.project.is_pb5 else 32)

                fd.params = []
                param_offset = buffer_helper.get_uint(arr2, 4 if self.project.is_pb5 else 8)
                if param_offset != 0xFFFF:
                    param_count = arr2[26 if self.project.is_pb5 else 30]
                    for m in range(param_count):
                        p = PbFunctionParam()
                        pb = buffer_helper.get_buffer(
                            self._param_buffer, param_offset + m * 12, 12)
                        if (pb[10] & 4) == 4:
                            p.is_read_only = True
                        elif (pb[10] & 2) == 2:
                            p.is_reference = True
                        p.type = PbType.get_pb_type(self, buffer_helper.get_ushort(pb, 8))
                        p.name = buffer_helper.get_string(
                            self.project.is_unicode, self._function_buffer,
                            buffer_helper.get_uint(pb, 0))
                        p.array_string = PbVariable.get_array_string(
                            buffer_helper.get_uint(pb, 4), self._function_buffer)
                        fd.params.append(p)

                alias_offset = buffer_helper.get_uint(arr2, 8 if self.project.is_pb5 else 12)
                if alias_offset != 0xFFFF:
                    lib_offset = buffer_helper.get_uint(arr2, 12 if self.project.is_pb5 else 16)
                    fd.library = buffer_helper.get_string(
                        self.project.is_unicode, self._function_buffer, lib_offset)
                    fd.alias = buffer_helper.get_string(
                        self.project.is_unicode, self._function_buffer, alias_offset)

                if self.project.version > 146:
                    us2 = buffer_helper.get_ushort(arr2, 44)
                    if us2 != 0xFFFF:
                        fd.throws_type = PbType.get_pb_type(
                            self, buffer_helper.get_ushort(self._function_buffer, us2))

                self._print_string(fd.to_string())

    def _read_function(self, func: PbFunction, index: bytes):
        with self._IndentBlock(self, f"Function :{' '.join(f'{b:04X}' for b in index)}"):
            func.index = buffer_helper.get_ushort(index, 2)
            pcode_size = self._read_ushort()
            debug_size = self._read_ushort()
            self._print_string(f"{pcode_size:04X} {debug_size:04X} {self._read_ushort():04X}")
            func.pcode_bytes = self._read_buffer(pcode_size)
            func.debug_bytes = self._read_buffer(debug_size * 4)

            from pcode_helper import PCodeHelper
            with self._IndentBlock(self, "PCodes"):
                for line in PCodeHelper.parse_pcode(func, False):
                    self._print_string(line)

            func.variables = self._read_variables(False)
            func.buffer = self._read_struct_buffer()
            with self._IndentBlock(self, "Stack"):
                self._print_buffer(func.buffer, 16)
            with self._IndentBlock(self, f"Variable {len(func.variables)}"):
                for i, v in enumerate(func.variables):
                    v.object = func.obj
                    self._print_string(f"{i:04X}: {v.to_string(func.buffer, self._is_debug)}")

    def _read_types(self, is_system_entry: bool) -> List[PbType]:
        self._read_buffer(6)
        buff = self._read_struct_buffer()
        num = self._read_ushort() // 20
        result = []
        for i in range(num):
            arr = self._read_buffer(20)
            t = PbType(
                self, i,
                buffer_helper.get_string(
                    self.project.is_unicode, buff,
                    buffer_helper.get_uint(arr, 8)),
                arr[16] == 64, is_system_entry)
            self._print_string(f"{i:04X} {buffer_helper.get_hex_string(arr)} {t.name}")
            result.append(t)
        return result

    def _read_variables(self, delay_parse_type: bool = False) -> List[PbVariable]:
        self._read_buffer(6)
        struct_buff = self._read_struct_buffer()
        num = self._read_ushort() // 20
        result = []
        for i in range(num):
            buff = self._read_buffer(20)
            result.append(PbVariable(self, i, buff, struct_buff, delay_parse_type))
        return result

    def _read_referenced_functions(self) -> List[PbReferencedFunction]:
        self._read_buffer(6)
        buff = self._read_struct_buffer()
        num = self._read_ushort() // 20
        result = []
        for i in range(num):
            arr = self._read_buffer(20)
            rf = PbReferencedFunction(i, arr)
            rf.name = buffer_helper.get_string(
                self.project.is_unicode, buff, buffer_helper.get_uint(arr, 8))
            result.append(rf)
        return result

    def _parse_srj(self):
        self.source = self.project.get_string(self._entry_data)
        for line in self.source.replace('\r', '\n').split('\n'):
            line = line.strip()
            if line.startswith("PBD:"):
                self.project.on_new_library(line[4:].split(',')[0], True)

    def _parse_exe(self):
        libs = []
        entries = []
        if self.project.is_unicode:
            pos = 0
            count = buffer_helper.get_ushort(self._entry_data, 0)
            pos = 2
            for _ in range(count):
                while self._entry_data[pos] != 0 or self._entry_data[pos + 1] != 0:
                    pos += 2
                pos += 2
            count = buffer_helper.get_ushort(self._entry_data, pos)
            pos += 2
            start = pos
            for _ in range(count):
                while self._entry_data[pos] != 0 or self._entry_data[pos + 1] != 0:
                    pos += 2
                libs.append(self._entry_data[start:pos].decode('utf-16-le', errors='replace'))
                pos += 2
                start = pos
            count = buffer_helper.get_ushort(self._entry_data, pos)
            pos += 2
            start = pos
            for _ in range(count):
                while self._entry_data[pos] != 0 or self._entry_data[pos + 1] != 0:
                    pos += 2
                entries.append(self._entry_data[start:pos].decode('utf-16-le', errors='replace'))
                pos += 2
                start = pos
        else:
            if self.project.is_pb5:
                pos = 0
                count = 1
            else:
                pos = 1
                count = self._entry_data[0]
            for _ in range(count):
                while self._entry_data[pos] != 0:
                    pos += 1
                pos += 1
            count = buffer_helper.get_ushort(self._entry_data, pos)
            pos += 2
            start = pos
            for _ in range(count):
                while self._entry_data[pos] != 0:
                    pos += 1
                libs.append(self._entry_data[start:pos].decode('mbcs', errors='replace'))
                pos += 1
                start = pos
            count = buffer_helper.get_ushort(self._entry_data, pos)
            pos += 2
            start = pos
            for _ in range(count):
                while self._entry_data[pos] != 0:
                    pos += 1
                entries.append(self._entry_data[start:pos].decode('mbcs', errors='replace'))
                pos += 1
                start = pos

        for lib in libs:
            self.project.on_new_library(lib, False)

        lib_str = "\n\t".join(f"{i:04X}:\t{l}" for i, l in enumerate(libs))
        ent_str = "\n\t".join(f"{i:04X}:\t{e}" for i, e in enumerate(entries))
        self.source = f"Libraries {len(libs):04X}:\n\t{lib_str}\nEntries {len(entries):04X}:\n\t{ent_str}"

    def on_new_type(self, t: PbType):
        self.types[t.index] = t

    def parse_inherit(self):
        for obj in self.objects.values():
            obj.parse_inherit()

    def to_string(self) -> str:
        return f"{self.file.file_path}/{self.entry_name}"
