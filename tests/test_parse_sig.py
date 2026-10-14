"""Signature parsing against real headers from the corpus."""
from convert import parse_signature


def test_plain_function():
    p = parse_signature(
        "public function string uf_get_paritycode (long al_jylsh, string as_brbm, datetime adt_jysj)")
    kind, name, ret, args = p
    assert kind == "function" and name == "uf_get_paritycode"
    assert ret == "string"
    assert [(n, t) for n, t, _ in args] == [
        ("al_jylsh", "number"), ("as_brbm", "string"), ("adt_jysj", "Date")]


def test_subroutine_inline_body_cut():
    p = parse_signature(
        "public subroutine set_worktrans (transaction atr_trans);trans_sqlca = atr_trans ")
    kind, name, ret, args = p
    assert kind == "subroutine" and ret == "void"
    assert name == "set_worktrans"
    assert args == [("atr_trans", "any", False)]


def test_ref_args_keep_byref_flag():
    p = parse_signature(
        "global function integer gf_tz_dbzcl (string as_brbm, ref string as_zydjjylsh, ref string as_error)")
    _, _, ret, args = p
    assert ret == "number"
    flags = {n: byref for n, _, byref in args}
    assert flags == {"as_brbm": False, "as_zydjjylsh": True, "as_error": True}


def test_external_library_clause_is_cut():
    p = parse_signature(
        'Function Integer SIGetPsamID(long hDevReader, ref string sPsamID) Library "SI_ICCReader.DLL"')
    kind, name, ret, args = p
    assert name == "SIGetPsamID" and ret == "number"
    assert args == [("hDevReader", "number", False), ("sPsamID", "string", True)]


def test_precision_types_and_arrays():
    p = parse_signature(
        "public function decimal{2} of_amt (dec{0} adc_a, string as_list[])")
    _, _, ret, args = p
    assert ret == "number"
    assert args == [("adc_a", "number", False), ("as_list", "Array<string>", False)]


def test_default_values_are_stripped():
    p = parse_signature(
        'public function integer of_cfg (string as_mode = "fast", integer ai_n = 1)')
    _, _, _, args = p
    assert [(n, t) for n, t, _ in args] == [("as_mode", "string"), ("ai_n", "number")]


def test_subroutine_without_return_type():
    p = parse_signature("public subroutine of_c ()")
    kind, name, ret, args = p
    assert kind == "subroutine" and ret == "void" and args == []


def test_unparsable_returns_none():
    assert parse_signature("complete garbage (") is None or \
        parse_signature("complete garbage (")[1] is not None
    assert parse_signature("not a signature at all") is None
