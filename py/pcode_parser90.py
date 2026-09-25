"""PB 9.0 PCode 解析器，对应 C# PCodeParser90."""

import buffer_helper
from pcode_parser_base import PCodeParserBase
from jmp_type import JmpType
from code_line import CodeLine


class PCodeParser90(PCodeParserBase):
    PCODE_LEN_ARRAY = bytes([
        2, 1, 1, 1, 1, 0, 0, 0, 0, 1, 3, 3, 1, 3, 3, 4, 4, 1, 5, 5,
        3, 3, 3, 3, 3, 4, 3, 1, 1, 1, 1, 1, 2, 0, 0, 0, 1, 0, 3, 2,
        3, 4, 2, 3, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2,
        1, 2, 1, 1, 2, 1, 0, 0, 0, 0, 2, 0, 2, 2, 2, 2, 2, 2, 2, 0,
        0, 0, 0, 0, 0, 0, 2, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0,
        0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2,
        2, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 2, 2,
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2,
        2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        0, 2, 1, 0, 3, 3, 2, 2, 3, 3, 4, 4, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2,
        1, 1, 2, 3, 2, 3, 4, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 2, 0, 0,
        0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1,
        1, 0, 1, 1, 1, 1, 1, 5, 1, 4, 1, 0, 2, 3, 3, 5, 3, 5, 1, 4,
        1, 1, 2, 2, 3, 3, 3, 3, 3, 0, 3, 0, 2, 2, 2, 3, 1, 1, 4, 3,
        1, 1, 1, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 2, 1, 1, 1, 1, 1, 1, 1, 2,
        2, 2, 2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 2, 3, 4,
        3, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 2, 2, 1, 2, 2, 2, 0, 0, 0,
        0, 0, 0,
    ])

    def __init__(self, pb_function):
        super().__init__(pb_function)

    @property
    def pcode_len_array(self) -> bytes:
        return self.PCODE_LEN_ARRAY

    def get_pcode_len(self, pcode: int) -> int:
        if self.pb_function.project.version < 193 and pcode == 297:
            return 0
        return super().get_pcode_len(pcode)

    def _on_parse_pcode(self, pcode_op: int, code_line: CodeLine) -> bool:
        p = code_line.param
        f = self.pb_function

        if pcode_op == 0:
            self.return_stmt(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 1:
            self.jump(buffer_helper.get_ushort(p, 0), JmpType.IfTrue)
        elif pcode_op == 2:
            self.jump(buffer_helper.get_ushort(p, 0), JmpType.IfFalse)
        elif pcode_op == 3:
            self.jump(buffer_helper.get_ushort(p, 0), JmpType.Goto)
        elif pcode_op == 4:
            self.sql_operate_transaction("connect")
        elif pcode_op == 5:
            self.sql_operate_transaction("commit")
        elif pcode_op == 6:
            self.sql_operate_transaction("rollback")
        elif pcode_op == 7:
            self.sql_operate_transaction("disconnect")
        elif pcode_op == 8:
            self.sql_close()
        elif pcode_op == 9:
            self.sql_open(buffer_helper.get_ushort(p, 0))
        elif pcode_op in (10, 11, 14):
            self._sql_direct_insert_update_delete(
                buffer_helper.get_uint(p, 0), buffer_helper.get_ushort(p, 4))
        elif pcode_op == 12:
            self._sql_execute(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 13:
            self.sql_fetch(buffer_helper.get_ushort(p, 4))
        elif pcode_op == 15:
            self._sql_direct_select(
                buffer_helper.get_uint(p, 0),
                buffer_helper.get_ushort(p, 4),
                buffer_helper.get_ushort(p, 6))
        elif pcode_op == 16:
            self.destroy_object()
        elif pcode_op == 17:
            self.halt(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 18:
            self._call_super(
                buffer_helper.get_ushort(p, 0),
                buffer_helper.get_ushort(p, 2),
                buffer_helper.get_ushort(p, 4),
                buffer_helper.get_uint(p, 6))
        elif pcode_op == 19:
            self.pop_function()
        elif pcode_op == 20:
            self._sql_execute_sqlsa(buffer_helper.get_ushort(p, 4))
        elif pcode_op == 21:
            self._sql_prepare_sqlsa()
        elif pcode_op == 22:
            self._sql_open_dynamic(buffer_helper.get_uint(p, 0), buffer_helper.get_ushort(p, 4))
        elif pcode_op == 23:
            self._sql_execute_dynamic(buffer_helper.get_uint(p, 0), buffer_helper.get_ushort(p, 4))
        elif pcode_op == 24:
            self._sql_describe()
        elif pcode_op == 25:
            self._sql_direct_select(
                buffer_helper.get_uint(p, 0),
                buffer_helper.get_ushort(p, 4),
                buffer_helper.get_ushort(p, 6))
        elif pcode_op == 26:
            self._sql_direct_insert_update_delete(
                buffer_helper.get_uint(p, 0), buffer_helper.get_ushort(p, 4) + 1)
        elif pcode_op == 27:
            self.push_local_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 28:
            self.push_shared_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 29:
            self.push_instance_variable_name(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 30:
            self.push_this()
        elif pcode_op == 31:
            self.push_parent()
        elif pcode_op == 33:
            self.operate_stack("and")
        elif pcode_op == 34:
            self.operate_stack("or")
        elif pcode_op == 35:
            self.operate_stack_single("not")
        elif pcode_op == 36:
            self.push_instance_variable()
        elif pcode_op in (37, 317, 449):
            pass
        elif pcode_op == 41:
            self.call_function(
                buffer_helper.get_uint(p, 0),
                buffer_helper.get_ushort(p, 4),
                buffer_helper.get_ushort(p, 6))
        elif pcode_op == 42:
            self.create_object(buffer_helper.get_uint(p, 0))
        elif pcode_op == 44:
            self.push_global_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 45:
            self.push_local_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 46:
            self.push_global_shared_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 47:
            self.push_constant(str(buffer_helper.get_ushort(p, 0) - 0x10000 if buffer_helper.get_ushort(p, 0) & 0x8000 else buffer_helper.get_ushort(p, 0)))
        elif pcode_op == 48:
            self.push_constant(str(buffer_helper.get_ushort(p, 0)))
        elif pcode_op == 49:
            v = buffer_helper.get_uint(p, 0)
            if v & 0x80000000:
                v -= 0x100000000
            self.push_constant(str(v))
        elif pcode_op == 50:
            self.push_constant(str(buffer_helper.get_uint(p, 0)))
        elif pcode_op == 51:
            self.push_constant(buffer_helper.get_decimal(f.buffer, buffer_helper.get_uint(p, 0)))
        elif pcode_op == 52:
            self.push_constant(buffer_helper.get_real(buffer_helper.get_uint(p, 0)))
        elif pcode_op == 53:
            self.push_constant(buffer_helper.get_double(f.buffer, buffer_helper.get_uint(p, 0)))
        elif pcode_op == 54:
            self.push_constant(buffer_helper.get_time(f.buffer, buffer_helper.get_uint(p, 0)))
        elif pcode_op == 55:
            self.push_constant(buffer_helper.get_date(f.buffer, buffer_helper.get_uint(p, 0)))
        elif pcode_op == 56:
            self.push_constant(buffer_helper.get_escape_string(f.project.is_unicode, f.buffer, buffer_helper.get_uint(p, 0)))
        elif pcode_op == 57:
            self.push_constant("true" if buffer_helper.get_ushort(p, 0) == 1 else "false")
        elif pcode_op == 58:
            self.push_enum(buffer_helper.get_ushort(p, 2), buffer_helper.get_ushort(p, 0))
        elif 59 <= pcode_op <= 79:
            pass  # cast
        elif 80 <= pcode_op <= 86:
            self.operate_stack("+")
        elif 87 <= pcode_op <= 93:
            self.operate_stack("-")
        elif 94 <= pcode_op <= 100:
            self.operate_stack("*")
        elif 101 <= pcode_op <= 107:
            self.operate_stack("/")
        elif 108 <= pcode_op <= 114:
            self.operate_stack("^")
        elif 115 <= pcode_op <= 121:
            self.operate_stack_single("-")
        elif pcode_op in (122, 123):
            self.operate_stack("+")
        elif pcode_op == 124:
            self.end_assign(True)
        elif 125 <= pcode_op <= 137:
            self.end_assign(False)
        elif 138 <= pcode_op <= 162:
            pass  # cast
        elif 163 <= pcode_op <= 178:
            self.operate_stack("=")
        elif 179 <= pcode_op <= 194:
            self.operate_stack("<>")
        elif 195 <= pcode_op <= 206:
            self.operate_stack(">")
        elif 207 <= pcode_op <= 218:
            self.operate_stack("<")
        elif 219 <= pcode_op <= 230:
            self.operate_stack(">=")
        elif 231 <= pcode_op <= 242:
            self.operate_stack("<=")
        elif 243 <= pcode_op <= 249:
            self.end_assign2("++")
        elif 250 <= pcode_op <= 256:
            self.end_assign2("--")
        elif 257 <= pcode_op <= 263:
            self.end_assign_op("+")
        elif 264 <= pcode_op <= 270:
            self.end_assign_op("-")
        elif 271 <= pcode_op <= 277:
            self.end_assign_op("*")
        elif pcode_op == 278:
            pass  # reset assign
        elif pcode_op == 282:
            self.begin_assign_local_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 283:
            self.begin_assign_shared_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 284:
            self.begin_assign_global_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 285:
            self.begin_assign_local_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 287:
            self.begin_assign_instance_variable()
        elif pcode_op == 293:
            self._pop()
        elif 288 <= pcode_op <= 296:
            pass  # cast
        elif 298 <= pcode_op <= 315:
            pass  # cast
        elif pcode_op in (318, 319):
            self.push_instance_variable()
        elif 320 <= pcode_op <= 323:
            pass  # cast
        elif pcode_op in (330, 331):
            self.call_function(
                buffer_helper.get_uint(p, 0),
                buffer_helper.get_ushort(p, 4),
                buffer_helper.get_ushort(p, 6))
        elif pcode_op in (332, 333):
            self.push_local_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op in (334, 335):
            self.push_shared_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op in (336, 337):
            self.push_global_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 339:
            self.push_local_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 342:
            self.end_assign(False)
        elif 343 <= pcode_op <= 361:
            pass  # cast
        elif pcode_op == 362:
            self.create_object(buffer_helper.get_uint(p, 0))
        elif pcode_op == 366:
            self.call_function(
                buffer_helper.get_uint(p, 0),
                buffer_helper.get_ushort(p, 4),
                buffer_helper.get_ushort(p, 6))
        elif pcode_op == 367:
            self.push_local_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 368:
            self.push_shared_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 369:
            self.push_global_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 372:
            self.operate_stack("+")
        elif pcode_op == 373:
            self.operate_stack("-")
        elif pcode_op == 374:
            self.operate_stack("*")
        elif pcode_op == 375:
            self.operate_stack("/")
        elif pcode_op == 376:
            self.operate_stack("^")
        elif pcode_op == 377:
            self.operate_stack_single("-")
        elif pcode_op == 378:
            self.operate_stack("=")
        elif pcode_op == 379:
            self.operate_stack("<>")
        elif pcode_op == 380:
            self.operate_stack(">")
        elif pcode_op == 381:
            self.operate_stack("<")
        elif pcode_op == 382:
            self.operate_stack(">=")
        elif pcode_op == 383:
            self.operate_stack("<=")
        elif pcode_op == 384:
            self.operate_stack("and")
        elif pcode_op == 385:
            self.operate_stack("or")
        elif pcode_op == 386:
            self.operate_stack_single("not")
        elif pcode_op == 387:
            self.push_instance_variable()
        elif pcode_op in (388, 389):
            pass  # cast
        elif 390 <= pcode_op <= 420:
            builtins = {
                390: "int", 391: "abs", 392: "abs", 393: "asc", 394: "blob",
                395: "ceiling", 396: "cos", 397: "exp", 398: "fact",
                399: "inthigh", 400: "intlow", 401: "isdate", 402: "isnull",
                403: "isnumber", 404: "istime", 405: "isvalid", 406: "lefttrim",
                407: "len", 408: "len", 409: "log", 410: "logten",
                411: "lower", 412: "pi", 413: "rand", 415: "righttrim",
                416: "sin", 417: "sqrt", 418: "tan", 419: "trim", 420: "upper",
            }
            if pcode_op in builtins:
                self.call_builtin_function(builtins[pcode_op], 1)
        elif pcode_op == 422:
            self.push_global_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 425:
            self.push_local_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 426:
            self.push_shared_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 427:
            pass  # cast
        elif pcode_op == 430:
            pass  # cast
        elif pcode_op == 431:
            self.index()
        elif pcode_op == 432:
            self.index()
        elif pcode_op == 433:
            self._pop_stack(2)
            self.index()
        elif pcode_op == 434:
            self.create_array(buffer_helper.get_ushort(p, 4))
        elif pcode_op == 435:
            self.create_array(buffer_helper.get_ushort(p, 4))
        elif pcode_op == 438:
            pass  # cast
        elif pcode_op == 440:
            self.call_builtin_function("lowerbound", 1)
        elif pcode_op == 441:
            self.call_builtin_function("upperbound", 1)
        elif pcode_op == 442:
            self.end_assign2("++")
        elif pcode_op == 443:
            self.end_assign2("--")
        elif pcode_op == 444:
            self.push_global_function_name(
                buffer_helper.get_ushort(p, 2), buffer_helper.get_ushort(p, 0))
        elif pcode_op in (445, 446, 447, 448):
            self.call_global_function(
                buffer_helper.get_ushort(p, 2), buffer_helper.get_ushort(p, 4))
        elif pcode_op == 451:
            self._sql_execute_immediate()
        elif pcode_op == 452:
            self._sql_execute_dynamic_descriptor(buffer_helper.get_uint(p, 0))
        elif pcode_op == 453:
            self._sql_fetch_dynamic_descriptor()
        elif pcode_op == 454:
            self._sql_open_dynamic_descriptor(buffer_helper.get_uint(p, 0))
        elif pcode_op == 456:
            pass  # create using name
        elif pcode_op in (457, 459, 461, 462, 463):
            pass  # cast
        elif pcode_op == 464:
            self.push_instance_variable()
        elif pcode_op == 466:
            self.push_instance_variable_name(buffer_helper.get_ushort(p, 0))
        elif 467 <= pcode_op <= 471:
            self.call_builtin_function("mod", 2)
        elif pcode_op in (472, 473):
            self.call_builtin_function("abs", 1)
        elif pcode_op == 474:
            self.call_builtin_function("ceiling", 1)
        elif 475 <= pcode_op <= 479:
            self.call_builtin_function("min", 2)
        elif 480 <= pcode_op <= 484:
            self.call_builtin_function("max", 2)
        elif pcode_op == 485:
            self.try_stmt(buffer_helper.get_ushort(p, 0), buffer_helper.get_ushort(p, 2))
        elif pcode_op == 486:
            self.end_try()
        elif pcode_op == 487:
            self.catch()
        elif pcode_op == 488:
            self.throw()
        elif pcode_op == 489:
            self.enter_finally(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 490:
            self.leave_finally()
        elif 491 <= pcode_op <= 504:
            pass  # cast
        elif pcode_op == 505:
            self.operate_stack("+")
        elif pcode_op == 506:
            self.operate_stack("-")
        elif pcode_op == 507:
            self.operate_stack("*")
        elif pcode_op == 508:
            self.operate_stack("/")
        elif pcode_op == 509:
            self.operate_stack("^")
        elif pcode_op == 510:
            self.operate_stack_single("-")
        elif pcode_op == 511:
            self.push_constant(buffer_helper.get_long_long(f.buffer, buffer_helper.get_uint(p, 0)))
        elif pcode_op == 512:
            self.push_local_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 513:
            self.push_global_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 515:
            self.push_shared_variable(buffer_helper.get_ushort(p, 0))
        elif pcode_op == 517:
            self.end_assign(False)
        elif pcode_op == 519:
            self.end_assign_op("+")
        elif pcode_op == 520:
            self.end_assign_op("-")
        elif pcode_op == 521:
            self.end_assign_op("*")
        elif pcode_op == 522:
            self.end_assign2("++")
        elif pcode_op == 523:
            self.end_assign2("--")
        elif pcode_op == 524:
            pass  # cast
        elif pcode_op == 525:
            self.call_builtin_function("abs", 1)
        elif pcode_op == 527:
            self.operate_stack("=")
        elif pcode_op == 528:
            self.operate_stack("<>")
        elif pcode_op == 529:
            self.operate_stack(">")
        elif pcode_op == 530:
            self.operate_stack("<")
        elif pcode_op == 531:
            self.operate_stack(">=")
        elif pcode_op == 532:
            self.operate_stack("<=")
        elif pcode_op == 533:
            self.call_builtin_function("mod", 2)
        elif pcode_op == 534:
            self.call_builtin_function("min", 2)
        elif pcode_op == 535:
            self.call_builtin_function("max", 2)
        elif pcode_op == 539:
            self.call_function(
                buffer_helper.get_uint(p, 0),
                buffer_helper.get_ushort(p, 4),
                buffer_helper.get_ushort(p, 6))
        elif pcode_op == 540:
            self.call_global_function(
                buffer_helper.get_ushort(p, 2), buffer_helper.get_ushort(p, 4))
        elif pcode_op == 542:
            self.push_instance_variable()
        elif pcode_op in (543, 546):
            pass  # cast
        elif pcode_op == 544:
            pass  # cast
        else:
            return False
        return True

    # ---- SQL 辅助方法 ----
    def _sql_direct_insert_update_delete(self, cursor_offset: int, param_count: int):
        self._pop()
        args = self._pop_stack(param_count)
        cursor = buffer_helper.get_cursor(
            self.pb_function.project.is_unicode,
            self.pb_function.entry.variable_buffer, cursor_offset,
            [a.str for a in args])
        self._code_line.text = f"// SQL: {cursor}"

    def _sql_direct_select(self, cursor_offset: int, pc1: int, pc2: int):
        self._pop()
        args1 = self._pop_stack(pc1)
        self._pop_stack(pc2)  # fetch into 目标，丢弃
        sql = buffer_helper.get_cursor(
            self.pb_function.project.is_unicode,
            self.pb_function.entry.variable_buffer, cursor_offset,
            [a.str for a in args1])
        self._code_line.text = f"// SELECT: {sql}"

    def _sql_execute(self, paramcount: int):
        self._pop_stack(paramcount)
        self._pop()  # sqlca
        self._pop()  # procedure
        self._code_line.text = "// execute procedure"

    def _sql_execute_sqlsa(self, paramcount: int):
        self._pop_stack(paramcount)
        self._pop()
        self._code_line.text = "// execute sqlsa"

    def _sql_prepare_sqlsa(self):
        self._pop()
        self._pop()
        self._pop()
        self._code_line.text = "// prepare sqlsa"

    def _sql_open_dynamic(self, cursor_offset: int, param_count: int):
        self._pop()
        self._pop()
        self._pop_stack(param_count)
        self._code_line.text = "// open dynamic cursor"

    def _sql_execute_dynamic(self, proc_offset: int, param_count: int):
        self._pop()
        self._pop()
        self._pop_stack(param_count)
        self._code_line.text = "// execute dynamic procedure"

    def _sql_describe(self):
        self._pop()
        self._pop()
        self._code_line.text = "// describe"

    def _sql_execute_immediate(self):
        self._pop()
        self._pop()
        self._code_line.text = "// execute immediate"

    def _sql_open_dynamic_descriptor(self, cursor_offset: int):
        self._pop()
        self._pop()
        self._pop()
        self._code_line.text = "// open dynamic using descriptor"

    def _sql_execute_dynamic_descriptor(self, proc_offset: int):
        self._pop()
        self._pop()
        self._pop()
        self._code_line.text = "// execute dynamic using descriptor"

    def _sql_fetch_dynamic_descriptor(self):
        self._pop()
        self._pop()
        self._pop()
        self._code_line.text = "// fetch using descriptor"

    def _call_super(self, func_index: int, paramcount: int, obj_type: int, name_offset: int):
        for _ in range(paramcount):
            self._pop()
        name = buffer_helper.get_string(
            self.pb_function.project.is_unicode,
            self.pb_function.buffer, name_offset)
        self._push(type('S', (), {'str': f"call super::{name}", 'type': None})())
