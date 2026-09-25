"""PbdViewer Python 版主入口.

用法:
    python main.py <pbd文件路径>
    python main.py <pbd文件路径> --object <对象名>
    python main.py <pbd文件路径> --list
"""

import sys
import os
import argparse

# 确保可以从当前目录导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pb_project import PbProject


def main():
    parser = argparse.ArgumentParser(description="PowerBuilder PBD/PBL 反编译器")
    parser.add_argument("file", help="PBD/PBL/EXE/DLL 文件路径")
    parser.add_argument("--list", action="store_true", help="只列出对象，不反编译")
    parser.add_argument("--object", "-o", help="指定要反编译的对象名")
    parser.add_argument("--debug", action="store_true", help="输出调试信息")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"文件不存在: {args.file}")
        sys.exit(1)

    print(f"正在解析: {args.file}")
    project = PbProject(args.file)

    print(f"版本: {project.version}")
    print(f"Unicode: {project.is_unicode}")
    print(f"PB5: {project.is_pb5}")
    print(f"对象数: {len(project.objects)}")

    if args.list:
        print("\n=== 对象列表 ===")
        for name, obj in sorted(project.objects.items()):
            print(f"  {name} ({obj.type.name})")
        return

    # 反编译所有对象或指定对象
    for pb_file in project.files:
        for entry in pb_file.entries:
            if args.object and args.object.lower() not in entry.name.lower():
                continue
            if entry.source and not entry.entry_object:
                continue
            print(f"\n{'='*60}")
            print(f"文件: {pb_file.file_name}")
            print(f"条目: {entry.entry_name}")
            print(f"{'='*60}")

            if entry.source:
                print(entry.source[:2000])
                continue

            if entry.entry_object is None:
                continue

            obj = entry.entry_object
            print(f"对象类型: {obj.type.name}")
            if obj.inherit_type:
                print(f"继承: {obj.inherit_type.name}")

            print("\n--- 函数定义 ---")
            for fd in obj.function_definitions:
                print(f"  {fd.to_string()}")

            print("\n--- 变量 ---")
            for v in obj.variables:
                print(f"  {v.to_string(None, args.debug)}")

            print("\n--- 函数代码 ---")
            for func in obj.functions:
                print(f"\n  // Function: {func}")
                if func.definition:
                    print(f"  {func.definition.to_string()}")
                try:
                    from pcode_helper import PCodeHelper
                    lines = PCodeHelper.parse_pcode(func, args.debug)
                    for line in lines:
                        print(f"    {line}")
                except Exception as e:
                    print(f"    // 解析失败: {e}")


if __name__ == "__main__":
    main()
