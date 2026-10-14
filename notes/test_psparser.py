import sys
sys.path.insert(0, r'E:\ChatGPT\PyPbdViewer\converter')
from psparser import parse_function_body, ParseError

tests = [
    ['if IsNull(str) or str = "" then return', 'end if'],
    ['choose case li_x', 'case 1', '// one', 'case else', '// other', 'end choose'],
    ['for i = 1 to 10 step 2', '// do', 'next'],
    ['try', '// risky', 'catch (Throwable e)', '// handle', 'end try'],
    ['ll_i = UpperBound(a) + 1', 'a[ll_i] = this'],
    ['i_asc=asc(mid(s,i,1)) + i_asc', 'chknum=hexcode[mod(i_asc,16)] + chknum'],
    ['gf_hiscomlog("", "打开通讯窗口失败:" + opene.text)', 'if gs_rtxserver="" then gs_rtxserver="rtx.fey.com"'],
]
for i, body in enumerate(tests):
    try:
        ast = parse_function_body(body)
        print(f'{i}: OK', ast)
    except Exception as e:
        print(f'{i}: FAIL', type(e).__name__, str(e)[:100])
