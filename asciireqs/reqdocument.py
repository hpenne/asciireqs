"""reqdocument - type for holding all information scanned from an asciidoc file"""

from __future__ import annotations
from typing import Dict
from typing import Iterable
from typing import List

Requirement = Dict[str, str]
Requirements = Dict[str, Requirement]


class ReqDocument:
    def __init__(self) -> None:
        self._name = '(undefined)'  # ToDo
        self._keys: List[str] = []
        self._reqs: Requirements = {}
        self._child_files: List[str] = []
        self._child_docs: List[ReqDocument] = []
        self._req_prefix: str = ""

    def set_name(self, name: str) -> None:
        self._name = name

    def get_name(self) -> str:
        return self._name

    def get_keys(self) -> List[str]:
        return self._keys

    def add_keys(self, keys: List[str]) -> None:
        for key in keys:
            if key not in self._keys:
                self._keys.append(key)

    def get_reqs(self) -> Requirements:
        return self._reqs

    def add_req(self, requirement: Requirement) -> None:
        req_id = requirement['ID']
        assert req_id
        self._reqs[req_id] = requirement

    def add_reqs(self, requirements: Iterable[Requirement]) -> None:
        for requirement in requirements:
            self.add_req(requirement)

    def set_child_doc_files(self, child_docs: List[str]) -> None:
        self._child_files = child_docs

    def get_child_doc_files(self) -> List[str]:
        return self._child_files

    def add_child_doc(self, child_doc: ReqDocument) -> None:
        self._child_docs.append(child_doc)

    def get_children(self) -> List[ReqDocument]:
        return self._child_docs

    def set_req_prefix(self, prefix: str) -> None:
        self._req_prefix = prefix

    def get_req_prefix(self) -> str:
        return self._req_prefix
