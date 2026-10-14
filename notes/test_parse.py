import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from psparser import parse_function_body

body = """long i,i_asc,i_asc_temp
string hexcode[0 to 15] = {"0","1","2"}
string chknum
if IsNull(str_txt) or str_txt = "" then return ""
i_asc=0
for i=1 to len(str_txt)
\ti_asc=asc(mid(str_txt,i,1)) + i_asc
next
return chknum"""
try:
    ast = parse_function_body(body)
    print("OK", ast)
except Exception as e:
    print("ERR", type(e).__name__, e)
