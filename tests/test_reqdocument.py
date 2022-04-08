"""test_reqdocument: Tests for the reqdocument module"""
import pytest

from asciireqs.reqdocument import ReqDocument, add_attribute, ReqParseError
from asciireqs.fields import ID, TEXT, CHILD, PARENT


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


def test_add_req() -> None:
    d1 = ReqDocument()
    r1 = {ID: "a", TEXT: "foo", CHILD: "1"}
    d1.add_req(r1)
    assert d1.attribute_names == [ID, TEXT, CHILD]
    assert d1.reqs == {"a": r1}


def test_add_empty_req() -> None:
    d1 = ReqDocument()
    d1.add_req(None)
    assert not d1.attribute_names
    assert not d1.reqs


def test_add_duplicate_req() -> None:
    d1 = ReqDocument()
    r1 = {ID: "a", TEXT: "foo", CHILD: "1"}
    d1.add_req(r1)
    d1.add_req(r1)
    assert d1.attribute_names == [ID, TEXT, CHILD]
    assert d1.reqs == {"a": r1}


def test_add_reqs() -> None:
    d1 = ReqDocument()
    r1 = {ID: "a", TEXT: "foo", CHILD: "1"}
    r2 = {ID: "b", TEXT: "bar", PARENT: "2"}
    d1.add_reqs([r1, r2])
    assert d1.attribute_names == [ID, TEXT, CHILD, PARENT]
    assert d1.reqs == {"a": r1, "b": r2}


def test_child_docs() -> None:
    d1 = ReqDocument()
    d2 = ReqDocument()
    d1.add_child_doc(d2)
    assert d1.child_docs == [d2]


def test_add_attribute() -> None:
    r = {ID: "a", TEXT: "foo", CHILD: "1"}
    add_attribute(r, PARENT, "2")
    assert r == {ID: "a", TEXT: "foo", CHILD: "1", PARENT: "2"}


def test_add_existing_attribute() -> None:
    r = {ID: "a", TEXT: "foo", CHILD: "1"}
    with pytest.raises(ReqParseError):
        add_attribute(r, CHILD, "2")


def test_add_nameless_attribute() -> None:
    r = {ID: "a", TEXT: "foo", CHILD: "1"}
    with pytest.raises(ReqParseError):
        add_attribute(r, "", "2")
