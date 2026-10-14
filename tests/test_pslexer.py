"""PowerScript lexer unit tests."""
from pslexer import tokenize, Token


def kinds(tokens):
    return [(t.kind, t.value) for t in tokens if t.kind not in ('NL', 'COMMENT', 'EOF')]


def test_identifiers_and_keywords():
    ts = kinds(tokenize("if x = 1 then return"))
    assert ts == [
        ('KW', 'if'), ('IDENT', 'x'), ('OP', '='), ('NUM', '1'),
        ('KW', 'then'), ('KW', 'return'),
    ]


def test_keyword_case_insensitive():
    ts = kinds(tokenize("RETURN"))
    assert ts == [('KW', 'RETURN')]


def test_numbers():
    ts = kinds(tokenize("123 4.5 .7"))
    assert ts[:3] == [('NUM', '123'), ('NUM', '4.5'), ('NUM', '.7')]


def test_string_with_escapes():
    ts = kinds(tokenize("'hello~~world'"))
    assert ts == [('STR', 'hello~~world')]


def test_double_quoted_string():
    ts = kinds(tokenize('"abc~"def"'))
    assert ts == [('STR', 'abc~"def')]


def test_enum():
    ts = kinds(tokenize("Text! LineMode!"))
    assert ts == [('ENUM', 'Text!'), ('ENUM', 'LineMode!')]


def test_hostvar():
    ts = kinds(tokenize("WHERE id = :ll_id"))
    assert ('HOSTVAR', 'll_id') in ts


def test_dcolon():
    ts = kinds(tokenize("call super::create"))
    assert ('DCOLON', '::') in ts
    # after DCOLON, 'create' is still keyword kind but parser treats it as name
    assert ('KW', 'create') in ts


def test_two_char_ops():
    ts = kinds(tokenize("a <> b <= c >= d == e = f"))
    ops = [v for k, v in ts if k == 'OP']
    assert ops == ['<>', '<=', '>=', '==', '=']


def test_multiline_comment():
    code = """before /* comment
multi */ after"""
    ts = kinds(tokenize(code))
    vals = [v for _, v in ts]
    assert 'before' in vals and 'after' in vals


def test_line_col_tracking():
    ts = tokenize("a\nb")
    assert ts[0] == Token('IDENT', 'a', 1, 1)
    assert ts[1] == Token('NL', '\n', 1, 2)
    assert ts[2] == Token('IDENT', 'b', 2, 1)


def test_empty_input():
    ts = tokenize("")
    assert ts == [Token('EOF', '', 1, 1)]


def test_junk_byte():
    ts = kinds(tokenize("a \x01 b"))
    assert any(k == 'JUNK' and v == '\x01' for k, v in ts)
    assert ('IDENT', 'b') in ts


def test_not_bang_as_op():
    ts = kinds(tokenize("!x"))
    assert ts[0] == ('OP', '!')


def test_multiline_comment_line_counting():
    code = "a /*\n\n*/ b"
    ts = tokenize(code)
    b_tok = next(t for t in ts if t.kind == 'IDENT' and t.value == 'b')
    assert b_tok.line == 3  # after two newlines in block comment


def test_semi_as_separator():
    ts = kinds(tokenize("x = 1; y = 2"))
    assert ('SEMI', ';') in ts


def test_chinese_identifier():
    ts = kinds(tokenize("门诊数量 = 10"))
    assert ('IDENT', '门诊数量') in ts


def test_brackets_and_braces():
    ts = kinds(tokenize("a[1] = {1,2}"))
    assert ('LBRACKET', '[') in ts
    assert ('RBRACE', '}') in ts