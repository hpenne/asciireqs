"""tests_reporting - Tests for reporting.py"""
from asciireqs.docparser import Project
from asciireqs.fields import ID, LINE_NO, TEXT, PARENT, CHILD
from asciireqs.reporting import (
    get_spec_hierarchy,
    line_numbers_for_requirements,
    insert_requirement_links,
    insert_anchor,
    has_element,
    split_req_list,
    missing_link_from_parent,
    evaluate_requirement_against_filter,
    requirement_as_term,
)
from asciireqs.reqdocument import ReqDocument, Requirements


def doc1_reqs() -> Requirements:
    return {"D1-1": {ID: "D1-1", LINE_NO: 3}, "D1-2": {ID: "D1-2", LINE_NO: 7}}


def docs_with_req_prefix() -> ReqDocument:
    doc = ReqDocument()
    doc.req_prefix = "UR-REQ-"
    doc.name = "ur-reqs.adoc"
    child_doc1 = ReqDocument()
    child_doc1.req_prefix = "SW-REQ-"
    child_doc1.name = "sw-reqs.adoc"
    doc.add_child_doc(child_doc1)
    child_doc2 = ReqDocument()
    child_doc2.req_prefix = "HW-REQ-"
    child_doc2.name = "hw-reqs.adoc"
    doc.add_child_doc(child_doc2)
    return doc


def test_line_numbers_for_requirements() -> None:
    lines = line_numbers_for_requirements(doc1_reqs())
    assert lines == {3: "D1-1", 7: "D1-2"}


def test_get_spec_hierarchy() -> None:
    lines = list(get_spec_hierarchy(docs_with_req_prefix(), ""))
    assert len(lines) == 3
    assert lines[0] == "* ur-reqs.adoc\n"
    assert lines[1] == "** sw-reqs.adoc\n"
    assert lines[2] == "** hw-reqs.adoc\n"


def test_insert_requirement_links() -> None:
    doc = docs_with_req_prefix()
    assert (
        insert_requirement_links("This is the UR-REQ-001 requirement", doc)
        == "This is the xref:ur-reqs.adoc#UR-REQ-001[UR-REQ-001] requirement"
    )
    assert (
        insert_requirement_links("This is the SW-REQ-002 requirement", doc)
        == "This is the xref:sw-reqs.adoc#SW-REQ-002[SW-REQ-002] requirement"
    )


def test_insert_anchor() -> None:
    doc = docs_with_req_prefix()
    assert (
        insert_anchor("| SW-REQ-001", "SW-REQ-001", doc) == "| [[SW-REQ-001]]SW-REQ-001"
    )
    assert (
        insert_anchor("| SW-REQ-001 | UR-REQ-002", "SW-REQ-001", doc)
        == "| [[SW-REQ-001]]SW-REQ-001 | xref:ur-reqs.adoc#UR-REQ-002[UR-REQ-002]"
    )


def test_has_element() -> None:
    s = "One, Two,Three"
    assert has_element(s, "One")
    assert has_element(s, "Three")
    assert not has_element(s, "Four")
    assert not has_element(s, "Two,Three")


def test_split_req_list_empty() -> None:
    assert not split_req_list("")


def test_split_req_list() -> None:
    assert split_req_list("One, Two,Three") == ["One", "Two", "Three"]


def test_missing_link_from_parent_link_ok() -> None:
    ur = ReqDocument()
    ur.reqs["UR-1"] = {ID: "UR-1", CHILD: "SR-1"}
    sr = ReqDocument()
    ur.child_docs = [sr]
    sr1 = {ID: "SR-1", PARENT: "UR-1"}
    sr.reqs["SR-1"] = sr1
    project = Project(ur, {**ur.reqs, **sr.reqs})
    assert not missing_link_from_parent(sr1, project)
    assert not evaluate_requirement_against_filter(sr1, project, "link_error()")


def test_missing_link_from_parent_no_downlink() -> None:
    ur = ReqDocument()
    ur.reqs["UR-1"] = {ID: "UR-1", CHILD: "SR-2"}
    sr = ReqDocument()
    ur.child_docs = [sr]
    sr1 = {ID: "SR-1", PARENT: "UR-1"}
    sr.reqs["SR-1"] = sr1
    project = Project(ur, {**ur.reqs, **sr.reqs})
    assert missing_link_from_parent(sr1, project)
    assert evaluate_requirement_against_filter(sr1, project, "link_error()")


def test_missing_link_from_parent_one_of_two_downlinks_ok() -> None:
    ur = ReqDocument()
    ur.reqs["UR-1"] = {ID: "UR-1", CHILD: "SR-1"}
    ur.reqs["UR-2"] = {ID: "UR-1", CHILD: "SR-2"}
    sr = ReqDocument()
    ur.child_docs = [sr]
    sr1 = {ID: "SR-1", PARENT: "UR-1, UR-2"}
    sr.reqs["SR-1"] = sr1
    project = Project(ur, {**ur.reqs, **sr.reqs})
    assert missing_link_from_parent(sr1, project)


def test_missing_link_from_parent_two_of_two_downlinks_ok() -> None:
    ur = ReqDocument()
    ur.reqs["UR-1"] = {ID: "UR-1", CHILD: "SR-1"}
    ur.reqs["UR-2"] = {ID: "UR-2", CHILD: "SR-1"}
    sr = ReqDocument()
    ur.child_docs = [sr]
    sr1 = {ID: "SR-1", PARENT: "UR-1, UR-2"}
    sr.reqs["SR-1"] = sr1
    project = Project(ur, {**ur.reqs, **sr.reqs})
    assert not missing_link_from_parent(sr1, project)
    assert evaluate_requirement_against_filter(
        sr1, project, 'has_element(req["Parent"], "UR-1")'
    )
    assert not evaluate_requirement_against_filter(
        sr1, project, 'has_element(req["Parent"], "UR-3")'
    )


def test_requirement_as_term() -> None:
    ur = ReqDocument()
    ur.req_prefix = "UR-"
    ur.name = "ur.adoc"
    ur.reqs["UR-1"] = {
        ID: "UR-1",
        CHILD: "SR-1",
        LINE_NO: "100",
    }
    sr = ReqDocument()
    ur.child_docs = [sr]
    sr.reqs["SR-1"] = {
        ID: "SR-1",
        TEXT: "Some requirement",
        PARENT: "UR-1",
        CHILD: "R1, R2",
    }

    lines = list(requirement_as_term(sr.reqs["SR-1"], ur))
    assert len(lines) == 4
    assert lines[0] == "[horizontal]\n"
    assert lines[1] == "[[SR-1]]SR-1:: Some requirement\n"
    assert lines[2] == "+\n"
    assert lines[3] == "Parent: xref:ur.adoc#UR-1[UR-1]; Child: R1, R2\n"


def test_requirement_as_term_with_multiline_text() -> None:
    ur = ReqDocument()
    ur.name = "ur.adoc"
    ur.reqs["UR-1"] = {
        ID: "UR-1",
        TEXT: "This is paragraph one\n\nand this is paragraph two",
        CHILD: "SR-1",
        LINE_NO: "100",
    }

    lines = list(requirement_as_term(ur.reqs["UR-1"], ur))
    assert len(lines) == 4
    assert lines[0] == "[horizontal]\n"
    assert lines[1] == "[[UR-1]]UR-1:: This is paragraph one\n+\nand this is paragraph two\n"
    assert lines[2] == "+\n"
    assert lines[3] == "Child: SR-1\n"
