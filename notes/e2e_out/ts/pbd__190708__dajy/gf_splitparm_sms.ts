// @ts-nocheck
// PBD global function: gf_splitparm_sms
import { NonVisualObject, Window, Application, PB } from './pb-runtime';

export function gf_splitparm_sms(..._args: any[]): any {
    if (PB.eq(!as_parmstring, "")) {
        // GOTO L0024 not translated
        return -1;
        li_len = as_char;
        gf[(211) - 1] = call_gf[(3) - 1]();
        if ((!li_finger > 0)) {
              // GOTO L0118 not translated
              li_start = (li_start + li_counter);
              gf[(160) - 1] = call_gf[(3) - 1]();
              li_start = (li_finger + li_len);
              gf[(211) - 1] = call_gf[(3) - 1]();
              // GOTO L0066 not translated
              if ((!li_start <= as_parmstring)) {
                      // GOTO L0186 not translated
                      li_start = (li_start + li_counter);
                      gf[(160) - 1] = call_gf[(3) - 1]();
                      return li_counter;
                      return;
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