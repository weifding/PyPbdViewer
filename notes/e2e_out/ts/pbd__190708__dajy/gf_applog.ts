// @ts-nocheck
// PBD global function: gf_applog
import { NonVisualObject, Window, Application, PB } from './pb-runtime';

export function gf_applog(..._args: any[]): any {
    ls_filename = (((gbl15 + "\\log\\") + sys185_311(sys185_321(), "yyyymmdd")) + ".log");
    ls_errinfo = as_errtext;
    li_filenum = sys185_58(ls_filename, pbEnum[(16405) - 1], pbEnum[(16403) - 1], pbEnum[(16404) - 1], pbEnum[(16478) - 1]);
    sys185_65(li_filenum, (((("// " + sys185_311(sys185_321(), "yyyy.mm.dd")) + " ") + sys185_311(sys185_165(), "hh:mm:ss")) + ls_errinfo));
    sys185_47(li_filenum);
    return;
}