import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from psparser import parse_function_body
from tsbuilder import build_function_body

cases = [
    "ldt_zfrq = gf_4();\nreturn;",
    "ldt_zfrq = gf_?4();\nreturn;",
    'ls_jkfs = gf_3(m0276.object.E("jkfs", 1, {ll_row}, true));\nreturn;',
    "ldt_zfrq = gf_4() + 1;\nreturn;",
]
for src in cases:
    try:
        ast = parse_function_body(src)
        ts, fell = build_function_body(ast)
        print("SRC", repr(src)); print("TS", repr(ts)); print("fell", fell)
    except Exception as ex:
        print("SRC", repr(src), "EXC", ex)
    print()
