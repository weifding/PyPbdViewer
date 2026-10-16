// @ts-nocheck
// PBD global function: gf_splitparm_sms
import { NonVisualObject, Window, Application, PB } from './pb-runtime';

export function gf_splitparm_sms(..._args: any[]): any {
    if (PB.eq(!as_parmstring, "")) {
        // GOTO L0024 not translated
        return -1;
        li_len = len(as_char);
        li_finger = sys185_211(as_parmstring, as_char, li_start);
        if ((!li_finger > 0)) {
              // GOTO L0118 not translated
              // TODO: unparsed: ;
              as_parm[(li_counter) - 1] = sys185_160(as_parmstring, li_start, (li_finger - li_start));
              li_start = (li_finger + li_len);
              li_finger = sys185_211(as_parmstring, as_char, li_start);
              // GOTO L0066 not translated
              if ((!li_start <= len(as_parmstring))) {
                      // GOTO L0186 not translated
                      // TODO: unparsed: ;
                      as_parm[(li_counter) - 1] = sys185_160(as_parmstring, li_start, ((len(as_parmstring) - li_start) + li_len));
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