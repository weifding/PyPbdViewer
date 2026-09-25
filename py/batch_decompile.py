"""批量反编译目录下所有 PB 库文件。

用法:
    python batch_decompile.py <输入目录> <输出目录> [--debug]
    python batch_decompile.py D:\\PB\\Source D:\\PB\\Output
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pb_project import PbProject
from pcode_helper import PCodeHelper


PB_EXTENSIONS = ('.pbd', '.pbl', '.dll', '.exe')


def decompile_entry(entry, debug: bool) -> str:
    """生成单个条目的反编译文本。"""
    lines = []

    if entry.source:
        lines.append(entry.source)
        return '\n'.join(lines)

    if entry.entry_object is None:
        return ""

    obj = entry.entry_object
    lines.append(f"// 对象类型: {obj.type.name}")
    if obj.inherit_type:
        lines.append(f"// 继承: {obj.inherit_type.name}")

    lines.append("")
    lines.append("// === 函数定义 ===")
    for fd in obj.function_definitions:
        lines.append(f"  {fd.to_string()}")

    lines.append("")
    lines.append("// === 变量 ===")
    for v in obj.variables:
        lines.append(f"  {v.to_string(None, debug)}")

    lines.append("")
    lines.append("// === 函数代码 ===")
    for func in obj.functions:
        lines.append(f"")
        lines.append(f"  // Function: {func}")
        if func.definition:
            lines.append(f"  {func.definition.to_string()}")
        try:
            plines = PCodeHelper.parse_pcode(func, debug)
            for line in plines:
                lines.append(f"    {line}")
        except Exception as e:
            lines.append(f"    // 解析失败: {e}")

    return '\n'.join(lines)


def decompile_library(lib_path: str, out_dir: str, debug: bool):
    """反编译单个 PB 库文件到输出目录。"""
    lib_name = os.path.splitext(os.path.basename(lib_path))[0]
    lib_out = os.path.join(out_dir, lib_name)
    os.makedirs(lib_out, exist_ok=True)

    print(f"解析: {lib_path}")
    try:
        project = PbProject(lib_path)
    except Exception as e:
        print(f"  [错误] 解析失败: {e}")
        return

    print(f"  版本: {project.version}, Unicode: {project.is_unicode}, 对象数: {len(project.objects)}")

    count = 0
    for pb_file in project.files:
        for entry in pb_file.entries:
            # 跳过纯资源/图片/系统库
            if entry.suffix in ('bmp', 'png', 'ico', 'jpg'):
                continue
            if entry.source and not entry.entry_object:
                continue

            text = decompile_entry(entry, debug)
            if not text.strip():
                continue

            out_file = os.path.join(lib_out, entry.entry_name.replace('/', '_').replace('\\', '_') + '.pb')
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(text)
            count += 1

    print(f"  输出 {count} 个对象到 {lib_out}")


def main():
    parser = argparse.ArgumentParser(description="批量反编译目录下所有 PB 库文件")
    parser.add_argument("input_dir", help="包含 .pbd/.pbl/.dll 文件的目录")
    parser.add_argument("output_dir", help="反编译输出目录")
    parser.add_argument("--debug", action="store_true", help="输出调试信息")
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        print(f"输入目录不存在: {args.input_dir}")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # 扫描库文件
    libs = []
    for f in sorted(os.listdir(args.input_dir)):
        if f.lower().endswith(PB_EXTENSIONS):
            libs.append(os.path.join(args.input_dir, f))

    if not libs:
        print(f"目录中未找到 {PB_EXTENSIONS} 文件")
        sys.exit(1)

    print(f"找到 {len(libs)} 个库文件\n")

    for lib in libs:
        decompile_library(lib, args.output_dir, args.debug)
        print()

    print("完成。")


if __name__ == "__main__":
    main()
