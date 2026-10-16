// @ts-nocheck
// PBD global function: gf_getpara_eas
import { NonVisualObject, Window, Application, PB } from './pb-runtime';

export function gf_getpara_eas(..._args: any[]): any {
    if (!!atr_transaction) {
        // GOTO L001C not translated
        return "";
        ls_paraname = ls_csmc;
        // TODO: unparsed: .0 = 100 then goto L00BE ;
        // TODO: unparsed: .0 = 0 then goto L00A4 ;
        // TODO: unparsed: ;
        // GOTO L00AA not translated
        // TODO: unparsed: ;
        ls_valule = ls_default;
        // GOTO L00EA not translated
        // TODO: unparsed: .0 = - 1 then goto L00EA ;
        ls_valule = "";
        if (!ls_valule) {
              // GOTO L0106 not translated
              ls_valule = "";
              return ls_valule;
              return;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
              // TODO: unparsed: ;
        }
    }
}