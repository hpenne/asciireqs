"""reqdocument - type for holding all information scanned from an asciidoc file"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from typing import Iterable
from typing import List

from asciireqs.fields import ID

Requirement = Dict[str, str]
Requirements = Dict[str, Requirement]


@dataclass
class ReqDocument:
    """This class holds all data about a requirement document"""
    name: str
    attribute_names: List[str]
    reqs: Requirements
    child_doc_files: List[str]
    child_docs: List[ReqDocument]
    req_prefix: str

    def __init__(self) -> None:
        self.name = ''
        self.attribute_names: List[str] = []
        self.reqs: Requirements = {}
        self.child_doc_files: List[str] = []
        self.child_docs: List[ReqDocument] = []
        self.req_prefix: str = ''

    def add_keys(self, keys: List[str]) -> None:
        """Takes a list of requirement attribute names, and adds new ones to 'attribute_names'"""
        for key in keys:
            if key not in self.attribute_names:
                self.attribute_names.append(key)

    def add_req(self, requirement: Requirement) -> None:
        """Adds a new requirement to 'reqs'"""
        req_id = requirement[ID]
        assert req_id
        if req_id in self.reqs:
            print(f'ERROR: Duplicate requirement {req_id}')
        else:
            self.reqs[req_id] = requirement

    def add_reqs(self, requirements: Iterable[Requirement]) -> None:
        """Adds several new requirement to 'reqs'"""
        for requirement in requirements:
            self.add_req(requirement)

    def add_child_doc(self, child_doc: ReqDocument) -> None:
        """Adds a child document to 'child_docs'"""
        self.child_docs.append(child_doc)
