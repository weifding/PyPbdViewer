"""PCode 解析基类，对应 C# PCodeParserBase."""

from typing import List, Optional
import buffer_helper
from pb_type import PbType
from jmp_type import JmpType
from code_line import CodeLine


class StackObject:
    def __init__(self, str_val: str, ptype: PbType = None):
        self.type = ptype
        self.str: str = str_val
        self.operator: str = ""

    def __str__(self):
        return self.str


class PCodeParserBase:
    def __init__(self, pb_function):
        self.pb_function = pb_function
        self._stack: List[StackObject] = []
        self._code_line: Optional[CodeLine] = None

    @property
    def pcode_len_array(self) -> bytes:
        raise NotImplementedError

    def get_pcode_len(self, pcode: int) -> int:
        if pcode < len(self.pcode_len_array):
            return self.pcode_len_array[pcode]
        return 255

    def parse_pcode(self, code_line: CodeLine):
        self._code_line = code_line
        code_line.text = ""
        if not self._on_parse_pcode(code_line.raw_op, code_line):
            code_line.text = f"//无法解析的pcode-------{code_line.raw_op:04X}"

    # ---- 栈操作 ----
    def _push(self, obj: StackObject):
        self._stack.append(obj)

    def _pop(self) -> StackObject:
        return self._stack.pop()

    def _peek(self) -> StackObject:
        return self._stack[-1]

    def _pop_stack(self, count: int) -> List[StackObject]:
        result = []
        for _ in range(count):
            result.append(self._pop())
        result.reverse()
        return result

    def _push_variable(self, var):
        self._push(StackObject(var.name, var.type))

    def push_local_variable(self, index: int):
        self._push_variable(self.pb_function.variables[index])

    def push_shared_variable(self, index: int):
        self._push_variable(self.pb_function.entry.variables[index])

    def push_global_variable(self, index: int):
        for v in self.pb_function.variables:
            if v.global_index == index:
                self._push_variable(v)
                return

    def push_global_shared_variable(self, index: int):
        for v in self.pb_function.entry.variables:
            if v.global_index == index:
                self._push_variable(v)
                return

    def begin_assign_local_variable(self, index: int):
        self._push_variable(self.pb_function.variables[index])

    def begin_assign_shared_variable(self, index: int):
        self._push_variable(self.pb_function.entry.variables[index])

    def begin_assign_global_variable(self, index: int):
        for v in self.pb_function.variables:
            if v.global_index == index:
                self._push_variable(v)
                return

    def begin_assign_instance_variable(self):
        obj1 = self._pop()
        obj2 = self._pop()
        if obj2.str == "entryobject":
            self._push(StackObject(obj1.str, obj1.type))
        else:
            self._push(StackObject(f"{obj2.str}.{obj1.str}", obj1.type))

    def push_instance_variable(self):
        obj1 = self._pop()
        obj2 = self._pop()
        if obj2.str == "entryobject":
            self._push(StackObject(obj1.str, obj1.type))
        else:
            self._push(StackObject(f"{obj2.str}.{obj1.str}", obj1.type))

    def push_instance_variable_name(self, offset: int):
        if 1 <= offset <= 7:
            self._push(StackObject("entryobject", self.pb_function.entry.entry_object.type))
            return
        name_offset = buffer_helper.get_uint(self.pb_function.buffer, offset)
        var_index = buffer_helper.get_ushort(self.pb_function.buffer, offset + 4)
        top_type = self._peek().type if self._stack else None
        pb_var = None
        if top_type is not None:
            obj = top_type.get_object(self.pb_function.entry)
            if obj is not None and var_index < len(obj.all_variables):
                pb_var = obj.all_variables[var_index]

        if pb_var is None:
            if (name_offset & 0xFFFF) != 0xFFFF:
                text = buffer_helper.get_string(
                    self.pb_function.project.is_unicode,
                    self.pb_function.buffer, name_offset)
            else:
                text = f"{var_index:04X}"
        elif (name_offset & 0xFFFF) != 0xFFFF:
            text = buffer_helper.get_string(
                self.pb_function.project.is_unicode,
                self.pb_function.buffer, name_offset)
        else:
            text = pb_var.name

        self._push(StackObject(text, pb_var.type if pb_var else None))

    def push_constant(self, constant: str):
        self._push(StackObject(constant, None))

    def push_this(self):
        self._push(StackObject("this", self.pb_function.obj.type))

    def push_parent(self):
        parent_obj = self.pb_function.obj.parent_object
        self._push(StackObject("parent", parent_obj.type if parent_obj else None))

    def push_enum(self, enum_index: int, item_index: int):
        items = self.pb_function.project.enums[enum_index].items
        self._push(StackObject(
            items.get(item_index, str(item_index)),
            PbType.get_pb_type(self.pb_function.entry, enum_index)))

    # ---- 运算 ----
    @staticmethod
    def _get_operator_level(op: str) -> int:
        levels = {
            "or": 2, "and": 2, "=": 1, "<>": 1, ">": 1, "<": 1, ">=": 1, "<=": 1,
            "+": 5, "-": 5, "*": 4, "/": 4, "^": 3,
            "$not": 6, "$-": 6,
        }
        return levels.get(op, 0)

    def operate_stack(self, op: str):
        right = self._pop()
        if self._get_operator_level(right.operator) >= self._get_operator_level(op):
            right.str = f"({right.str})"
        left = self._pop()
        if self._get_operator_level(left.operator) > self._get_operator_level(op):
            left.str = f"({left.str})"
        result = StackObject(f"{left.str} {op} {right.str}", None)
        result.operator = op
        self._push(result)

    def operate_stack_single(self, op: str):
        top = self._pop()
        if self._get_operator_level(top.operator) > 0:
            top.str = f"({top.str})"
        result = StackObject(f"{op} {top.str}", None)
        result.operator = "$" + op
        self._push(result)

    # ---- 赋值 ----
    def end_assign(self, is_array: bool = False):
        right = self._pop()
        left = self._pop()
        self._code_line.text = f"{left.str} = {right.str}"

    def end_assign_op(self, operator: str):
        right = self._pop()
        left = self._pop()
        self._code_line.text = f"{left.str} {operator}= {right.str}"

    def end_assign2(self, operator: str):
        top = self._pop()
        self._code_line.text = f"{top.str} {operator}"

    # ---- 控制流 ----
    def return_stmt(self, p1: int = 0):
        if p1 == 1:
            self._code_line.text = f"return {self._pop().str}"
        else:
            self._code_line.text = "return"

    def halt(self, force: int):
        self._code_line.text = "halt" if force == 1 else "halt close"

    def jump(self, pos: int, jmp_type: JmpType):
        self._code_line.jmp_type = jmp_type
        self._code_line.jmp_offset = pos
        if jmp_type == JmpType.Goto:
            self._code_line.text = f"goto {pos:04X}"
        elif jmp_type == JmpType.IfTrue:
            cond = self._pop().str
            self._code_line.text = f"if {cond} then goto {pos:04X}"
        elif jmp_type == JmpType.IfFalse:
            cond = self._pop().str
            self._code_line.text = f"if {cond} then not goto {pos:04X}"

    def try_stmt(self, catchpos: int, endpos: int):
        self._code_line.text = "try"

    def end_try(self):
        self._code_line.text = "end try"

    def catch(self):
        top = self._pop()
        self._push(StackObject(f"catch ({top.type.name} {top.str})", None))

    def throw(self):
        top = self._pop()
        self._code_line.text = f"throw {top}"

    def enter_finally(self, finallypos: int):
        self._code_line.text = "enter finally"
        self._code_line.jmp_offset = finallypos

    def leave_finally(self):
        pass

    # ---- 对象操作 ----
    def create_object(self, offset: int):
        type_name = self._get_type_name(offset)
        self._push(StackObject(f"create {type_name.name}", type_name))

    def destroy_object(self):
        top = self._pop()
        self._code_line.text = f"destroy({top.str})"

    def pop_function(self):
        self._code_line.text = self._pop().str

    def _get_type_name(self, offset: int) -> PbType:
        name_offset = buffer_helper.get_uint(self.pb_function.buffer, offset)
        type_index = buffer_helper.get_ushort(self.pb_function.buffer, offset + 2)
        ptype = PbType.get_pb_type(self.pb_function.entry, type_index)
        name = buffer_helper.get_string(
            self.pb_function.project.is_unicode,
            self.pb_function.buffer, name_offset)
        if ptype.name != name:
            ptype.name = name
        return ptype

    # ---- 函数调用 ----
    def push_global_function_name(self, obj_index: int, function_index: int):
        name = None
        if (obj_index & 0x8000) == 0x8000:
            name = self.pb_function.obj.referenced_functions[function_index].name
        elif (obj_index & 0x4000) == 0x4000:
            sys_entry = self.pb_function.project.system_entry
            if sys_entry is not None and obj_index in sys_entry.objects:
                obj = sys_entry.objects[obj_index]
                if function_index < len(obj.function_definitions):
                    name = obj.function_definitions[function_index].name
            if name is None:
                name = f"({obj_index:04X}{function_index:04X})"
        self._push(StackObject(name or "", None))

    def call_global_function(self, count: int, ftype: int):
        name = self._pop().str
        args = self._pop_stack(count)
        if ftype & 1:
            name = "post " + name
        if ftype & 2:
            name = "dynamic " + name
        if ftype & 4:
            name = "event " + name
        if name == "string":
            name = "ConvertToString"
        elif name == "long":
            name = "ConvertToLong"
        arg_str = ",".join(a.str for a in args)
        self._push(StackObject(f"{name}({arg_str})", None))

    def call_function(self, offset: int, count: int, ftype: int):
        func_index = buffer_helper.get_ushort(self.pb_function.buffer, offset)
        buffer_helper.get_ushort(self.pb_function.buffer, offset + 2)  # obj_type_index，暂未使用
        name_offset = buffer_helper.get_uint(self.pb_function.buffer, offset + 4)
        if (name_offset & 0xFFFF) == 0xFFFF:
            raise Exception("CallFunction funnameoffset==0xFFFF")
        args = self._pop_stack(count)
        obj = self._pop()

        func_name = buffer_helper.get_string(
            self.pb_function.project.is_unicode,
            self.pb_function.buffer, name_offset)

        # 查找函数定义
        fd = None
        if func_index != 0xFFFF and obj.type is not None and obj.type.name != "any":
            pb_obj = obj.type.get_object(self.pb_function.entry)
            if pb_obj is not None and func_index < len(pb_obj.all_function_definitions):
                candidate = pb_obj.all_function_definitions[func_index]
                if candidate is not None and candidate.name.lower() == func_name.lower():
                    fd = candidate

        if ftype & 1:
            func_name = "post " + func_name
        if ftype & 2:
            func_name = "dynamic " + func_name
        if ftype & 4:
            func_name = "event " + func_name

        if obj.str == "this":
            prefix = "super::"
        else:
            prefix = obj.str + "."

        # 参数列表
        if fd is not None:
            arg_strs = []
            for i, a in enumerate(args):
                if i < len(fd.params) and fd.params[i].is_reference:
                    arg_strs.append("ref " + a.str)
                else:
                    arg_strs.append(a.str)
            arg_str = ",".join(arg_strs)
        else:
            arg_str = ",".join(a.str for a in args)

        call_str = f"{prefix}{func_name}({arg_str})"
        ret_type = None
        if obj.type is not None and obj.type.name == "any":
            ret_type = obj.type
        elif fd is not None:
            ret_type = fd.return_type
        self._push(StackObject(call_str, ret_type))

    def call_builtin_function(self, function: str, paramcount: int = 1):
        args = self._pop_stack(paramcount)
        arg_str = ",".join(a.str for a in args)
        self._push(StackObject(f"{function}({arg_str})", None))

    def create_array(self, arraylen: int):
        args = self._pop_stack(arraylen)
        arg_str = ",".join(a.str for a in args)
        self._push(StackObject(f"new [] {{{arg_str}}}", None))

    def index(self):
        idx = self._pop()
        arr = self._pop()
        self._push(StackObject(f"{arr.str}[{idx.str}]", arr.type))

    # ---- SQL 操作 ----
    def sql_operate_transaction(self, function: str):
        top = self._pop()
        self._code_line.text = f"{function} using {top};"

    def sql_open(self, param_count: int):
        self._pop_stack(param_count)  # args
        self._pop()  # sqlca
        cursor = self._pop()
        self._code_line.text = f"open {cursor.str};"

    def sql_fetch(self, paramcount: int):
        self._pop()  # skip
        cursor = self._pop()
        args = self._pop_stack(paramcount)
        self._code_line.text = f"fetch {cursor.str} into {','.join(':' + a.str for a in args)};"

    def sql_close(self):
        self._pop()
        cursor = self._pop()
        self._code_line.text = f"close {cursor.str};"

    # ---- 子类实现 ----
    def _on_parse_pcode(self, pcode_op: int, code_line: CodeLine) -> bool:
        raise NotImplementedError
