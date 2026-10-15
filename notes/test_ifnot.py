import sys
sys.path.insert(0, r"E:\ChatGPT\PyPbdViewer\converter")
from psparser import parse_function_body

b = """IF Not wf_loadconfig() Then
	f_poplog(gs_path, "err")
	Close(This)
end if"""
ast = parse_function_body(b)
for s in ast:
    print(s)
