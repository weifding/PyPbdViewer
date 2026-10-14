import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from psparser import parse_function_body

bodies = [
    """if isvalid(SQLCA) then
	if isvalid(ui_zjk) then
		if not isvalid(ids_sfxm) then
			ids_sfxm=create n_datastorexz_w2
			ids_sfxm.dataobject='d_zjk'
		ids_sfxm.SetTransObject(ui_zjk)""",
    """ls_filename = space(200)
GetModuleFileName(hnd,ls_filename,200)
return ls_filename""",
]
for b in bodies:
    print("=== PB ===")
    print(b)
    try:
        ast = parse_function_body(b)
        print("AST:", ast)
    except Exception as e:
        print("ERR", type(e).__name__, e)
    print()
