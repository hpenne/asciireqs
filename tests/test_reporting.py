"""tests_reporting - Tests for reporting.py"""

from asciireqs.fields import LINE_NO
from asciireqs.reporting import *


def doc1_reqs() -> Requirements:
    return {'D1-1': {fields.ID: 'D1-1', LINE_NO: 3}, 'D1-2': {fields.ID: 'D1-2', LINE_NO: 7}}


def docs_with_req_prefix() -> ReqDocument:
    doc = ReqDocument()
    doc.set_req_prefix('UR-REQ-')
    doc.set_name('ur-reqs.adoc')
    child_doc = ReqDocument()
    child_doc.set_req_prefix('SW-REQ-')
    child_doc.set_name('sw-reqs.adoc')
    doc.add_child_doc(child_doc)
    return doc


def test_line_numbers_for_requirements() -> None:
    lines = line_numbers_for_requirements(doc1_reqs())
    assert lines == {3: 'D1-1', 7: 'D1-2'}


def test_insert_requirement_links() -> None:
    doc = docs_with_req_prefix()
    assert insert_requirement_links('This is the UR-REQ-001 requirement', doc)\
           == 'This is the xref:ur-reqs.adoc#UR-REQ-001[UR-REQ-001] requirement'
    assert insert_requirement_links('This is the SW-REQ-002 requirement', doc) \
           == 'This is the xref:sw-reqs.adoc#SW-REQ-002[SW-REQ-002] requirement'


def test_insert_anchor() -> None:
    doc = docs_with_req_prefix()
    assert insert_anchor('| SW-REQ-001', 'SW-REQ-001', doc) == '| [[SW-REQ-001]]SW-REQ-001'
    assert insert_anchor('| SW-REQ-001 | UR-REQ-002', 'SW-REQ-001', doc)\
           == '| [[SW-REQ-001]]SW-REQ-001 | xref:ur-reqs.adoc#UR-REQ-002[UR-REQ-002]'
