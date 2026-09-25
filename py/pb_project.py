"""PB 项目入口，对应 C# PbProject."""

import os
from typing import List, Dict, Optional
from pb_file import PbFile
from pb_type import PbType
from pb_object import PbObject
from pb_enum import PbEnum


class PbProject:
    def __init__(self, file_path: str):
        self.files: List[PbFile] = []
        self.objects: Dict[str, PbObject] = {}
        self.system_types: Dict[int, PbType] = {}
        self.enums: Dict[int, PbEnum] = {}
        self.system_entry = None
        self.is_unicode: bool = False
        self.is_pb5: bool = False
        self.version: int = 0
        self.is_debug: bool = False

        self._file_path = file_path
        self._dir = os.path.dirname(file_path)

        pb_file = PbFile(self, file_path)
        self.files.insert(0, pb_file)

        for pf in self.files:
            for entry in pf.entries:
                entry.parse_object(False)

        if self.system_entry is not None:
            self.system_entry.parse_inherit()

        for pf in self.files:
            for entry in pf.entries:
                entry.parse_inherit()

    def get_string(self, data: bytes, offset: int = 0, size: int = None) -> str:
        if size is not None:
            data = data[offset:offset + size]
        if not self.is_unicode:
            return data.decode('mbcs', errors='replace')
        return data.decode('utf-16-le', errors='replace')

    def on_new_library(self, libpath: str, is_full_path: bool):
        if not is_full_path:
            libpath = os.path.join(self._dir, libpath)
        if os.path.normpath(self._file_path).lower() != os.path.normpath(libpath).lower() and \
                os.path.exists(libpath):
            self.files.append(PbFile(self, libpath))

    def on_system_library(self, version: int) -> Optional[PbFile]:
        if self.version == 0:
            self.version = version
            # 系统库需要内置资源文件，这里返回 None 表示跳过
            return None
        if self.version != version:
            raise Exception("two version library in one project??")
        return None

    def on_system_entry(self, entry):
        self.system_entry = entry

    def on_new_system_type(self, t: PbType):
        self.system_types[t.index] = t

    def on_new_object(self, obj: PbObject, name: str = None):
        key = name if name is not None else obj.type.name
        self.objects[key] = obj

    def on_new_enum_item(self, t: PbType, index: int, item_name: str):
        if t.index not in self.enums:
            self.enums[t.index] = PbEnum()
            self.enums[t.index].index = t.index
            self.enums[t.index].name = t.name
        self.enums[t.index].items[index] = item_name + "!"

    @property
    def file_path(self) -> str:
        return self._file_path
