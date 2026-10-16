// @ts-nocheck
// PBD global function: gf_applog
import { NonVisualObject, Window, Application, PB } from './pb-runtime';

export function gf_applog(..._args: any[]): any {
    "yyyymmdd" = ((gf[(311) - 1] + call_gf[(2) - 1]()) + ".log");
    ls_errinfo = as_errtext;
    gf[(58) - 1] = call_gf[(5) - 1]();
    call_gf[(2) - 1]();
    call_gf[(1) - 1]();
    return;
}