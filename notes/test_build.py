import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from psparser import parse_function_body
from tsbuilder import build_function_body

b = """if isvalid(SQLCA) then
	if isvalid(ui_zjk) then
		if not isvalid(ids_sfxm) then
			ids_sfxm=create n_datastorexz_w2
			ids_sfxm.dataobject='d_zjk'
		ids_sfxm.SetTransObject(ui_zjk)
end if"""
ast = parse_function_body(b)
print("AST stmts:", len(ast))
try:
    ts = build_function_body(ast)
    print("TS:\n" + ts)
except Exception as e:
    import traceback; traceback.print_exc()
