"""PB 文件，对应 C# PbFile."""

import os
from typing import List
import buffer_helper
from pb_entry import PbEntry


class PbFile:
    def __init__(self, project, file_path: str):
        self.project = project
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.entries: List[PbEntry] = []

        with open(file_path, 'rb') as f:
            data = f.read()

        # 扫描 HDR* 头
        node_offsets = self._get_node_list(data)

        for offset in node_offsets:
            # 读 NOD* 头 32 字节
            us = buffer_helper.get_ushort(data, offset + 20)
            pos = offset + 32
            num = 2 if project.is_unicode else 1
            num2 = 4 + num * 4
            num3 = num2 + 16
            arr = bytearray(num3)

            for i in range(us):
                arr[:] = data[pos:pos + num3]
                magic = arr[0:4].decode('ascii', errors='replace')
                if magic != "ENT*":
                    raise Exception("格式错误")
                type_str = project.get_string(arr[4:4 + num * 4])
                if type_str not in ("0600", "0500"):
                    raise Exception("格式错误")

                data_offset = buffer_helper.get_uint(arr, num2)
                data_size = buffer_helper.get_uint(arr, num2 + 4)
                name_len = buffer_helper.get_ushort(arr, num2 + 14)

                name_bytes = data[pos + num3:pos + num3 + name_len]
                pos = pos + num3 + name_len

                entry_name = project.get_string(name_bytes, 0, name_len - num)
                entry_data = self._read_data(data, data_offset, data_size)
                self.entries.append(PbEntry(self, entry_name, entry_data))

    def _get_node_list(self, data: bytes) -> List[int]:
        result = []
        pos = 0
        found = False

        # 扫描 HDR*
        while pos + 512 <= len(data):
            chunk = data[pos:pos + 512]
            if chunk[0:4].decode('ascii', errors='replace') == "HDR*":
                # ANSI PowerBuilder
                if chunk[4:16].decode('ascii', errors='replace') == "PowerBuilder":
                    if chunk[18:22].decode('ascii', errors='replace') == "0500":
                        self.project.is_pb5 = True
                        found = True
                        break
                    if chunk[18:22].decode('ascii', errors='replace') == "0600":
                        found = True
                        break
                # Unicode PowerBuilder
                try:
                    if chunk[4:28].decode('utf-16-le', errors='replace') == "PowerBuilder" and \
                       chunk[32:40].decode('utf-16-le', errors='replace') == "0600":
                        found = True
                        self.project.is_unicode = True
                        break
                except Exception:
                    pass
            pos += 512

        if not found:
            return result

        pos += 1536 if self.project.is_unicode else 1024
        chunk = data[pos:pos + 512]
        if len(chunk) != 512 or chunk[0:4].decode('ascii', errors='replace') != "NOD*":
            raise Exception("格式错误")

        result.append(pos)
        next1 = buffer_helper.get_uint(chunk, 4)
        next2 = buffer_helper.get_uint(chunk, 12)

        while next1 > 0:
            chunk = data[next1:next1 + 512]
            if len(chunk) != 512 or chunk[0:4].decode('ascii', errors='replace') != "NOD*":
                raise Exception("格式错误")
            result.append(next1)
            next1 = buffer_helper.get_uint(chunk, 4)

        while next2 > 0:
            chunk = data[next2:next2 + 512]
            if len(chunk) != 512 or chunk[0:4].decode('ascii', errors='replace') != "NOD*":
                raise Exception("格式错误")
            result.append(next2)
            next2 = buffer_helper.get_uint(chunk, 12)

        return result

    @staticmethod
    def _read_data(data: bytes, start: int, size: int) -> bytes:
        result = bytearray(size)
        written = 0
        offset = start
        while written < size:
            header = data[offset:offset + 10]
            if len(header) < 10 or header[0:4].decode('ascii', errors='replace') != "DAT*":
                break
            chunk_size = buffer_helper.get_ushort(header, 8)
            result[written:written + chunk_size] = data[offset + 10:offset + 10 + chunk_size]
            written += chunk_size
            offset = buffer_helper.get_uint(header, 4)
        return bytes(result)
