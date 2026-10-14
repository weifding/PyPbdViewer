import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from psparser import parse_function_body
from tsbuilder import build_function_body

b = '''String   ls_ErrInfo
u_Transaction lo_Transaction
ls_ErrInfo = "1." + String(Error.Number) + "\\n" + &
			 "2." + Error.Text + "\\n" + &
			 "3." + Error.WindowMenu + "\\n" + &
			 "4." + Error.Object + "\\n" + &
			 "5." + Error.ObjectEvent + "\\n" + &
			 "6." + String(Error.Line) + " "
ls_ErrInfo = ls_ErrInfo + "\\n7." + GetCurrentDirectory()'''
ast = parse_function_body(b)
print("AST stmts:", len(ast))
for s in ast:
    print(" ", s)
