"""Unit tests for the text-run extraction / rejoin layer."""
from pbltext import extract_runs, rejoin_lines, unbalanced, extract_text, strip_marker


def test_extract_runs_splits_on_binary():
    data = b"hello world\x00\x01\x02more text"
    runs = extract_runs(data, min_run=4)
    assert [r for _, r in runs] == [b"hello world", b"more text"]


def test_extract_runs_keeps_gbk_pairs():
    data = "中文abc".encode("gbk") + b"\x00" + "x".encode("gbk")
    runs = extract_runs(data, min_run=1)
    assert len(runs) == 2
    assert runs[0][1].decode("gbk") == "中文abc"


def test_extract_runs_min_run_filter():
    data = b"abcdef\x00ab\x00abcdefgh"
    runs = extract_runs(data, min_run=4)
    assert [r for _, r in runs] == [b"abcdef", b"abcdefgh"]


def test_rejoin_merges_after_dat_marker():
    # the run break fell mid-token right after a DAT* marker
    out = rejoin_lines(["public function bDAT*", "oolean uf_x (long al)"])
    assert out == ["public function boolean uf_x (long al)"]


def test_rejoin_keeps_terminator_lines_separate():
    # `end on` follows a marker line but starts a fresh statement: never merge
    out = rejoin_lines(["call super::destroyDAT*", "end on", ""])
    assert out == ["call super::destroy", "end on", ""]


def test_rejoin_merges_unbalanced_paren_with_space():
    out = rejoin_lines(["ls_sql = 'select a from t where", "b = 1'"])
    assert out == ["ls_sql = 'select a from t where b = 1'"]


def test_rejoin_skips_unbalanced_comment_lines():
    out = rejoin_lines(["// it's a comment", "x = 1"])
    assert out == ["// it's a comment", "x = 1"]


def test_rejoin_chain_cap_stops_runaway():
    lines = ["don't"] + [f"junk{i}" for i in range(10)]
    out = rejoin_lines(lines, max_chain=3)
    # the stray apostrophe cannot swallow the whole file
    assert len(out) > 1


def test_unbalanced_states():
    assert not unbalanced("f(a, b)")
    assert unbalanced("f(a, b")
    assert unbalanced('ls = "abc')
    assert not unbalanced('ls = "ab" + "c"')
    assert not unbalanced("ls = 'it~'s'")  # PB escape


def test_strip_marker():
    assert strip_marker("abcDAT*def") == ("abcdef", True)
    assert strip_marker("plain") == ("plain", False)


def test_extract_text_joins_run_breaks():
    # one statement split across runs by a binary region carrying a DAT* marker
    data = b"public function bDAT*" + b"\x00\x01" + b"oolean f()"
    text = extract_text(data, min_run=2)
    assert text == "public function boolean f()"
