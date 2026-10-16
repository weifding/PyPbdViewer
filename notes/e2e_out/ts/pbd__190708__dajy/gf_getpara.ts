// @ts-nocheck
// PBD global function: gf_getpara
import { NonVisualObject, Window, Application, PB } from './pb-runtime';

export function gf_getpara(..._args: any[]): any {
    ls_paraname = upper(ls_csmc);
    if (PB.eq((!isnull(ls_valule) || ls_valule), "")) {
        // GOTO L00AE not translated
        gf_begin_transaction(gbl16);
        gf_commit_transaction(gbl16);
        ls_valule = ls_default;
        return ls_valule;
        return;
        // TODO: unparsed: ;
        // TODO: unparsed: ;
    }
}