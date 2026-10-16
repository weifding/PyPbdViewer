// @ts-nocheck
// PBD global function: gf_replacestr
import { NonVisualObject, Window, Application, PB } from './pb-runtime';

export function gf_replacestr(..._args: any[]): any {
    // TODO: unparsed: = as_replace then goto L003A ;
    return as_str;
    ll_len = len(as_replace);
    if (PB.eq((!ll_pos + ll_len), 0)) {
        // GOTO L008C not translated
        ll_pos = sys185_211(as_str, as_find, 1);
        // GOTO L00B8 not translated
        ll_pos = sys185_211(as_str, as_find, (ll_pos + ll_len));
        if ((!ll_pos > 0)) {
              // GOTO L00F6 not translated
              as_str = sys185_269(as_str, ll_pos, len(as_find), as_replace);
              if ((ll_pos > 0)) {
                      // GOTO L004A not translated
                      return as_str;
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
              }
        }
    }
}