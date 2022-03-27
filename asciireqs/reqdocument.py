"""reqdocument - type for holding all information scanned from an asciidoc file"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from typing import Iterable
from typing import List

import asciireqs.fields as fields

Requirement = Dict[str, str]
Requirements = Dict[str, Requirement]


@dataclass
class ReqDocument:
    name: str
    keys: List[str]
    reqs: Requirements
    child_doc_files: List[str]
    child_docs: List[ReqDocument]
    req_prefix: str

    def __init__(self) -> None:
        self.name = ''
        self.keys: List[str] = []
        self.reqs: Requirements = {}
        self.child_doc_files: List[str] = []
        self.child_docs: List[ReqDocument] = []
        self.req_prefix: str = ''

    def add_keys(self, keys: List[str]) -> None:
        for key in keys:
            if key not in self.keys:
                self.keys.append(key)

    def add_req(self, requirement: Requirement) -> None:
        req_id = requirement[fields.ID]
        assert req_id
        self.reqs[req_id] = requirement

    def add_reqs(self, requirements: Iterable[Requirement]) -> None:
        for requirement in requirements:
            self.add_req(requirement)

    def add_child_doc(self, child_doc: ReqDocument) -> None:
        self.child_docs.append(child_doc)
