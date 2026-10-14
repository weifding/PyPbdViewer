import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from psparser import parse_function_body
from tsbuilder import build_function_body

b = """if isvalid(SQLCA) then
	if isvalid(ui_zjk) then
		if not isvalid(ids_sfxm) then
			ids_sfxm=create n_datastorexz_w2
			ids_sfxm.dataobject='d_zjk_zy_lisjk_w2'
		ids_sfxm.SetTransObject(ui_zjk)
	if not isvalid(ids_dz) then
		ids_dz=create n_datastorexz_w2
		if ib_allcode then
			ids_dz.dataobject='d_jy_sg_xmdz_all_w2'
		else
			ids_dz.dataobject='d_jy_sg_xmdz_instr_w2'
	ids_dz.SetTransObject(SQLCA)
	ids_dz.setfilter( "")
	ids_dz.filter( )
	if ids_dz.retrieve(ui_s_destinstrid)<0 then
		f_log(gs_path,'收费项目 对照下载失败重试' + ids_dz.is_sqlerrortext)
		if pos(ids_dz.is_sqlerrortext,'transaction information not available')>0 then
			ids_dz.settransobject(sqlca)
end if"""
ast = parse_function_body(b)
print("AST stmts:", len(ast))
ts, fb = build_function_body(ast)
print("fell_back:", fb)
print("TS:\n" + ts)
