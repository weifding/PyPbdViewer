// @ts-nocheck
// PBD global function: gf_getpara_eas
import { NonVisualObject, Window, Application, PB } from './pb-runtime';

export function gf_getpara_eas(..._args: any[]): any {
    if (!!isvalid(atr_transaction)) {
        // GOTO L001C not translated
        return "";
        ls_paraname = upper(ls_csmc);
        if (PB.eq(!atr_transaction.inst8, 100)) {
              // GOTO L00BE not translated
              if (PB.eq(!atr_transaction.inst8, 0)) {
                      // GOTO L00A4 not translated
                      // TODO: unparsed: ;
                      // GOTO L00AA not translated
                      // TODO: unparsed: ;
                      ls_valule = ls_default;
                      // GOTO L00EA not translated
                      if (PB.eq(!atr_transaction.inst8, -1)) {
                                // GOTO L00EA not translated
                                ls_valule = "";
                                if (!isnull(ls_valule)) {
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
        }
    }
}