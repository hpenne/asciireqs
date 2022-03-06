"""reqdocument - type for holding all information scanned from an asciidoc file"""

from typing import List
from typing import Dict

Requirement = Dict[str, str]
Requirements = Dict[str, Requirement]


class ReqDocument:
    def __init__(self):
        self._name = '(undefined)'  # ToDo
        self._keys: List[str] = []
        self._reqs: Requirements = {}
        self._child_files: List[str] = []
        self._child_docs: List[ReqDocument] = []

    def set_name(self, name: str):
        self._name = name

    def get_name(self) -> str:
        return self._name

    def get_keys(self) -> List[str]:
        return self._keys

    def add_keys(self, keys: List[str]):
        for key in keys:
            if key not in self._keys:
                self._keys.append(key)

    def get_reqs(self) -> Requirements:
        return self._reqs

    def add_req(self, requirement: Requirement):
        req_id = requirement['ID']
        assert req_id
        self._reqs[req_id] = requirement

    def set_child_doc_files(self, child_docs: List[str]):
        self._child_files = child_docs

    def get_child_doc_files(self) -> List[str]:
        return self._child_files

    def add_child_doc(self, child_doc):  # ToDo: Type hints using "Self"
        self._child_docs.append(child_doc)

    def get_children(self) -> List:  # ToDo: Type hints using "Self"
        return self._child_docs


def test_keys():
    d = ReqDocument()
    d.add_keys(['a', 'b'])
    d.add_keys(['a', 'c'])
    assert d.get_keys() == ['a', 'b', 'c']


def test_reqs():
    d = ReqDocument()
    r1 = {'ID': 'a', 'Text': 'foo'}
    r2 = {'ID': 'b', 'Text': 'bar'}
    d.add_req(r1)
    d.add_req(r2)
    assert d.get_reqs() == {'a': r1, 'b': r2}


def test_child_files():
    d = ReqDocument()
    assert not d.get_child_doc_files()
    d.set_child_doc_files(['a', 'b'])
    assert d.get_child_doc_files() == ['a', 'b']


def test_child_docs():
    d1 = ReqDocument()
    d2 = ReqDocument()
    d2.add_keys(['ID', 'Text'])
    d1.add_child_doc(d2)
    assert d1.get_children() == [d2]
