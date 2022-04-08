"""test_reqdocument: Tests for the reqdocument module"""

from asciireqs.reqdocument import ReqDocument
from asciireqs.fields import ID, TEXT


def test_reqs() -> None:
    d = ReqDocument()
    r1 = {ID: "a", TEXT: "foo"}
    r2 = {ID: "b", TEXT: "bar"}
    d.add_reqs((r1, r2))
    assert d.attribute_names == [ID, TEXT]
    assert d.reqs == {"a": r1, "b": r2}


def test_child_files() -> None:
    d = ReqDocument()
    assert not d.child_doc_files
    d.child_doc_files = ["a", "b"]
    assert d.child_doc_files == ["a", "b"]


def test_child_docs() -> None:
    d1 = ReqDocument()
    d2 = ReqDocument()
    d1.add_child_doc(d2)
    assert d1.child_docs == [d2]
