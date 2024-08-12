"""reqdocument - type for holding all information scanned from an asciidoc file"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
from typing import Iterable
from typing import List

from asciireqs.fields import ID

Requirement = Dict[str, str]
Requirements = Dict[str, Requirement]


class ReqParseError(Exception):
    """This exception signals an error in requirement parsing"""


@dataclass
class ReqDocument:
    """This class holds all data about a requirement document"""

    name: str
    attribute_names: List[str]
    reqs: Requirements
    child_doc_files: List[str]
    child_docs: List[ReqDocument]
    req_regex: str

    def __init__(self) -> None:
        self.name = ""
        self.attribute_names: List[str] = []
        self.reqs: Requirements = {}
        self.child_doc_files: List[str] = []
        self.child_docs: List[ReqDocument] = []
        self.req_regex: str = ""

    def _add_keys(self, keys: List[str]) -> None:
        """Takes a list of requirement attribute names, and adds new ones to 'attribute_names'"""
        for key in keys:
            if key not in self.attribute_names:
                self.attribute_names.append(key)

    def add_req(self, requirement: Optional[Requirement]) -> None:
        """Adds a new requirement to 'reqs' and the keys to 'keys'"""
        if not requirement:
            return
        req_id = requirement[ID]
        assert req_id
        if req_id in self.reqs:
            print(f"ERROR: Duplicate requirement {req_id}")
        else:
            self.reqs[req_id] = requirement
            self._add_keys(list(requirement.keys()))

    def add_reqs(self, requirements: Iterable[Requirement]) -> None:
        """Adds several new requirement to 'reqs'"""
        for requirement in requirements:
            self.add_req(requirement)

    def add_child_doc(self, child_doc: ReqDocument) -> None:
        """Adds a child document to 'child_docs'"""
        self.child_docs.append(child_doc)

    def get_attribute_names_recursive(self) -> List[str]:
        """Finds all attribute names used in this and all child/sub specifications"""
        names: List[str] = []
        _add_attribute_names(self, names)
        for child_doc in self.child_docs:
            _add_attribute_names(child_doc, names)
        return names


def _add_attribute_names(doc: ReqDocument, names: List[str]) -> None:
    for name in doc.attribute_names:
        if name not in names:
            names.append(name)


def add_attribute(req: Requirement, name: str, value: str) -> None:
    """Adds an attribute name/value pair to a requirement"""
    name = name.strip()
    if not name:
        raise ReqParseError("Empty attribute name")
    if name in req:
        raise ReqParseError(f"Attribute {name} already defined")
    req[name] = value


def add_attributes(req: Requirement, attributes: Dict[str, str]) -> None:
    """Adds a dictionary of attributes to a requirement"""
    for name, value in attributes.items():
        add_attribute(req, name, value)
