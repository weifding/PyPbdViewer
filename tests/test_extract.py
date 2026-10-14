"""Block-scanner tests on synthetic PowerScript source (no PBL needed)."""
from extract_pbl import extract_blocks

SRC_ON_BLOCK_TERMINATES = """
global type w_demo from window
end type

on w_demo.create
call super::create
TriggerEvent( this, "constructor" )
end on

public function integer wf_one (string as_x)
return 1
end function
""".strip().split("\n")

SRC_EVENT_DEF = """
global type u_demo from nonvisualobject
end type

event constructor;lu_x = create u_x
end event

event destructor;destroy lu_x
end event
""".strip().split("\n")

SRC_PROTOTYPES = """
forward prototypes
public function string of_a (long al_id)
public function boolean of_b (string as_x, ref string as_y)
public subroutine of_c ()
end prototypes

public function string of_a (long al_id)
return ""
end function
""".strip().split("\n")

SRC_EXTERNAL = """
global type u_ext from nonvisualobject
end type

public subroutine SIGetErrMessage (int nErrNo, ref string sErrMessage) Library "SI_ICCReader.DLL"
end type
""".strip().split("\n")

SRC_MEMBER_EVENT = """
global type w_ctrls from window
end type

type cb_ok from commandbutton within w_ctrls
integer x = 10
end type

event clicked;close(parent)
end event

type cb_cancel from commandbutton within w_ctrls
integer x = 100
end type

event clicked;close(parent)
end event
""".strip().split("\n")

SRC_TRUNCATED_FUNC = """
global type w_trunc from window
end type

public function integer wf_broken (string as_x)
// missing end function
ls_tmp = as_x

public function integer wf_next (string as_y)
return 2
end function
""".strip().split("\n")


def kinds(blocks):
    out = {}
    for b in blocks:
        out[b["kind"]] = out.get(b["kind"], 0) + 1
    return out


def test_on_block_terminates_at_end_on():
    # the historic bug: `on ... create` swallowed everything looking for `end event`
    r = extract_blocks(SRC_ON_BLOCK_TERMINATES)
    ev = [b for b in r["blocks"] if b["kind"] == "event"]
    assert len(ev) == 1
    assert ev[0]["name"] == "create"
    assert not ev[0]["truncated"]
    fn = [b for b in r["blocks"] if b["kind"] == "function"]
    assert len(fn) == 1 and fn[0]["name"] == "wf_one"


def test_bare_event_defs():
    r = extract_blocks(SRC_EVENT_DEF)
    ev = [b for b in r["blocks"] if b["kind"] == "event"]
    assert sorted(b["name"] for b in ev) == ["constructor", "destructor"]
    assert all(not b["truncated"] for b in ev)
    assert "lu_x = create u_x" in ev[0]["text"] or "lu_x = create u_x" in ev[1]["text"]


def test_prototypes_block_not_split_into_functions():
    r = extract_blocks(SRC_PROTOTYPES)
    assert kinds(r["blocks"]) == {"prototypes": 1, "function": 1}
    proto = next(b for b in r["blocks"] if b["kind"] == "prototypes")
    assert not proto["truncated"]
    fn = next(b for b in r["blocks"] if b["kind"] == "function")
    assert fn["name"] == "of_a"


def test_external_library_decl():
    r = extract_blocks(SRC_EXTERNAL)
    fns = [b for b in r["blocks"] if b["kind"] in ("function", "subroutine")]
    assert len(fns) == 1
    assert fns[0]["name"] == "SIGetErrMessage"
    assert fns[0]["external"] is True


def test_member_event_attribution():
    r = extract_blocks(SRC_MEMBER_EVENT)
    ev = [b for b in r["blocks"] if b["kind"] == "event"]
    assert [b["control"] for b in ev] == ["cb_ok", "cb_cancel"]
    mems = [m["name"] for m in r["members"]]
    assert mems == ["cb_ok", "cb_cancel"]


def test_missing_end_function_truncates_at_next_header():
    r = extract_blocks(SRC_TRUNCATED_FUNC)
    fns = [b for b in r["blocks"] if b["kind"] == "function"]
    assert len(fns) == 2
    broken = next(b for b in fns if b["name"] == "wf_broken")
    assert broken["truncated"]
    ok = next(b for b in fns if b["name"] == "wf_next")
    assert not ok["truncated"]


def test_max_lines_cap():
    from extract_pbl import _collect_block, RE_END_SUB, TR_FUNC
    lines = ["public subroutine of_big ()"] + [f"x = {i}" for i in range(30)]
    text, j, trunc, reason = _collect_block(lines, 0, RE_END_SUB, TR_FUNC, max_lines=10)
    assert trunc and reason == "max-lines"
    assert len(text.split("\n")) == 10
