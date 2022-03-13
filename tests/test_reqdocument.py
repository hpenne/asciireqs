"""test_reqdocument: Tests for the reqdocument module"""

from asciireqs.reqdocument import *


def test_keys() -> None:
    d = ReqDocument()
    d.add_keys(['a', 'b'])
    d.add_keys(['a', 'c'])
    assert d.get_keys() == ['a', 'b', 'c']


def test_reqs() -> None:
    d = ReqDocument()
    r1 = {'ID': 'a', 'Text': 'foo'}
    r2 = {'ID': 'b', 'Text': 'bar'}
    d.add_reqs((r1, r2))
    assert d.get_reqs() == {'a': r1, 'b': r2}


def test_child_files() -> None:
    d = ReqDocument()
    assert not d.get_child_doc_files()
    d.set_child_doc_files(['a', 'b'])
    assert d.get_child_doc_files() == ['a', 'b']


def test_child_docs() -> None:
    d1 = ReqDocument()
    d2 = ReqDocument()
    d2.add_keys(['ID', 'Text'])
    d1.add_child_doc(d2)
    assert d1.get_children() == [d2]
