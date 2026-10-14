import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from psparser import parse_function_body
from tsbuilder import Builder as TsBuilder

bodies = [
    """if isnull(argTypeName) then argTypeName = ""
wi_s_DocFilter = argFilter
wi_s_DocTypeName = argTypeName
return""",
    """Yield()
if mle_msg.LineCount() > wi_i_linecount then
	mle_msg.text = ""
mle_msg.Text += msg + char(13) + char(10)
mle_msg.Scroll(mle_msg.LineCount())
return""",
    """choose case wparam
	case 200
		return Handle(This)
	case 300
		event ue_exit()
	case 399
		event ue_exit()
		halt close
end choose""",
]
for b in bodies:
    print("=== PB ===")
    print(b)
    try:
        ast = parse_function_body(b)
        print("AST:", ast)
        tb = TsBuilder()
        for stmt in ast:
            print("  TS:", tb.stmt(stmt))
    except Exception as e:
        print("ERR", type(e).__name__, e)
    print()
