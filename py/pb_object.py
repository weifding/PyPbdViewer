"""PB 对象，对应 C# PbObject."""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pb_entry import PbEntry
    from pb_type import PbType
    from pb_function import PbFunction
    from pb_variable import PbVariable
    from pb_referenced_function import PbReferencedFunction
    from pb_function_definition import PbFunctionDefinition


class PbObject:
    def __init__(self, entry: "PbEntry", index: int, ptype: "PbType"):
        self.entry = entry
        self.project = entry.project
        self.index: int = index
        self.type: "PbType" = ptype
        self.inherit_type: Optional["PbType"] = None
        self.inherit_object: Optional["PbObject"] = None
        self.parent_type: Optional["PbType"] = None
        self.parent_object: Optional["PbObject"] = None
        self.functions: List["PbFunction"] = []
        self.variables: List["PbVariable"] = []
        self.referenced_functions: List["PbReferencedFunction"] = []
        self.function_definitions: List["PbFunctionDefinition"] = []
        self.all_variables: List[Optional["PbVariable"]] = []
        self.all_function_definitions: List[Optional["PbFunctionDefinition"]] = []
        self.controls: List["PbObject"] = []
        self._parsed_inherit: bool = False

    def parse_inherit(self):
        if self._parsed_inherit:
            return
        if self.inherit_type is not None:
            self.inherit_object = self.inherit_type.get_object(self.entry)
        if self.parent_type is not None:
            self.parent_object = self.parent_type.get_object(self.entry)

        if self.inherit_object is not None:
            self.inherit_object.parse_inherit()
            n = min(len(self.inherit_object.all_variables), len(self.all_variables))
            for i in range(n):
                self.all_variables[i] = self.inherit_object.all_variables[i]
            for fd in self.inherit_object.all_function_definitions:
                if fd is not None:
                    self.all_function_definitions[fd.global_index] = fd

        # 实例变量反转后填充到 all_variables 末尾
        inst_vars = [v for v in self.variables if v.is_instance]
        inst_vars.reverse()
        for k, v in enumerate(inst_vars):
            self.all_variables[len(self.all_variables) - 1 - k] = v

        for fd in self.function_definitions:
            self.all_function_definitions[fd.global_index] = fd

        # 控件
        self.controls = [
            o for o in self.entry.objects.values()
            if o.parent_type == self.type
        ]

        for i in range(len(self.all_variables)):
            v = self.all_variables[i]
            if v is not None:
                match = next((c for c in self.controls if c.type.name == v.name), None)
                if match is not None and match.type != v.type:
                    self.all_variables[i] = v.inherit(match)

        self._parsed_inherit = True

    def to_string(self) -> str:
        return f"{self.entry}/{self.type.name}"

    def get_name_with_parent(self) -> str:
        parent_name = self.parent_object.type.name if self.parent_object else ""
        return f"{self.type.name}->{parent_name}"
