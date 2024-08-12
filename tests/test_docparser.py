"""test_docparser: Tests for the docparser modele"""

from typing import Tuple
from asciireqs.docparser import (
    get_source_block,
    req_from_yaml_lines,
    req_from_yaml_block,
    validate_requirement,
    req_from_term,
)
from asciireqs.fields import ID, TEXT, PARENT, CHILD, LINE_NO, TITLE
from asciireqs.reqdocument import ReqDocument


def empty() -> Tuple[str, int]:
    return str(), 0


def doc_with_req_prefix() -> ReqDocument:
    doc = ReqDocument()
    doc.req_regex = r"SR-\d+"
    return doc


def test_validate_requirement() -> None:
    doc = ReqDocument()
    doc.req_regex = r"SR-\d+"
    assert validate_requirement({ID: "SR-1", TEXT: "Some text"}, doc, 2)


def test_validate_requirement_no_req_prefix_attribute() -> None:
    doc = ReqDocument()
    assert not validate_requirement({ID: "SR-1", TEXT: "Some text"}, doc, 2)


def test_validate_requirement_no_id_field() -> None:
    doc = ReqDocument()
    doc.req_regex = r"SR-\d+"
    assert not validate_requirement({TEXT: "Some text"}, doc, 2)


def test_validate_requirement_wrong_id_prefix() -> None:
    assert not validate_requirement(
        {ID: "S-1", TEXT: "Some text"}, doc_with_req_prefix(), 2
    )


def test_validate_requirement_no_text_field() -> None:
    doc = ReqDocument()
    doc.req_prefix = r"SR-\d+"
    assert not validate_requirement({ID: "SR-1"}, doc, 2)


def test_get_source_block_with_empty_input() -> None:
    assert get_source_block(enumerate([])) == ([], 0)


def test_get_source_block_not_starting_correctly() -> None:
    assert get_source_block(enumerate(["foo", "----", "bar", "----"], start=1)) == (
        [],
        0,
    )


def test_get_source_block() -> None:
    source_input = ["Line 1", "Line 2", "   Line 3"]
    source_block_marker = ["----"]
    source = get_source_block(
        enumerate(source_block_marker + source_input + source_block_marker, start=1)
    )
    assert source == (source_input, 2)


def test_req_from_yaml_block_with_empty_input() -> None:
    assert not req_from_yaml_lines([], doc_with_req_prefix(), 13)


def test_req_from_yaml_block_with_simple_requirement() -> None:
    req = req_from_yaml_lines(
        ["ID: SR-001", "Text: Some requirement"], doc_with_req_prefix(), 13
    )
    assert len(req) == 1
    assert req[0] == {ID: "SR-001", TEXT: "Some requirement", LINE_NO: str(13)}


def test_req_from_invalid_yaml_block() -> None:
    assert not req_from_yaml_lines(
        ["ID SR-001", "Text: Some requirement"], doc_with_req_prefix(), 13
    )


def test_req_from_yaml_block_with_id_on_second_line() -> None:
    req = req_from_yaml_lines(
        ["ID: |", "  SR-001", "Text: Some requirement"], doc_with_req_prefix(), 13
    )
    assert len(req) == 1
    assert req[0] == {ID: "SR-001", TEXT: "Some requirement", LINE_NO: str(14)}


def test_req_from_yaml_lines_with_single_requirement() -> None:
    source_input = ["ID: SR-001", "Text: Some requirement"]
    source_block_marker = ["----"]
    req = req_from_yaml_block(
        enumerate(source_block_marker + source_input + source_block_marker, start=1),
        doc_with_req_prefix(),
    )
    assert req == [{ID: "SR-001", TEXT: "Some requirement", LINE_NO: str(2)}]


def test_req_from_yaml_with_multi_line_text() -> None:
    assert not req_from_yaml_lines(["ID: SR-001"], doc_with_req_prefix(), 13)
    source_input = [
        "ID: SR-001",
        "Text: |",
        "  Some requirement",
        "",
        "  This is the second paragraph",
    ]
    source_block_marker = ["----"]
    req = req_from_yaml_block(
        enumerate(source_block_marker + source_input + source_block_marker, start=1),
        doc_with_req_prefix(),
    )
    assert req == [{ID: "SR-001", TEXT: "Some requirement\n\nThis is the second paragraph", LINE_NO: str(2)}]


def test_req_from_yaml_lines_with_two_requirement() -> None:
    source_input = [
        "SR-001:",
        "  Text: Some requirement",
        "SR-002:",
        "  Text: Some other requirement",
    ]
    source_block_marker = ["----"]
    reqs = req_from_yaml_block(
        enumerate(source_block_marker + source_input + source_block_marker, start=1),
        doc_with_req_prefix(),
    )
    assert reqs == [
        {ID: "SR-001", TEXT: "Some requirement", LINE_NO: str(2)},
        {ID: "SR-002", TEXT: "Some other requirement", LINE_NO: str(4)},
    ]


def test_req_from_yaml_with_missing_id() -> None:
    assert not req_from_yaml_lines(
        ["Text: Some requirement"], doc_with_req_prefix(), 13
    )


def test_req_from_yaml_with_missing_text() -> None:
    assert not req_from_yaml_lines(["ID: SR-001"], doc_with_req_prefix(), 13)


def test_req_from_term_with_text_only() -> None:
    req = req_from_term(
        "SR-001::", 2, enumerate(["Req. text"], start=3), doc_with_req_prefix()
    )
    assert req == {ID: "SR-001", TEXT: "Req. text", LINE_NO: "2"}


def test_req_from_term_with_multi_line_text() -> None:
    req = req_from_term(
        "SR-001::",
        2,
        enumerate(["Req. text1", "Req. text2"], start=3),
        doc_with_req_prefix(),
    )
    assert req == {ID: "SR-001", TEXT: "Req. text1\nReq. text2", LINE_NO: "2"}


def test_req_from_term_with_attributes() -> None:
    req = req_from_term(
        "SR-001::",
        2,
        enumerate(
            ["Req. text1", "Req. text2", "+", "Child: R-01, R-02; Parent: UR-01"],
            start=3,
        ),
        doc_with_req_prefix(),
    )
    assert req == {
        ID: "SR-001",
        TEXT: "Req. text1\nReq. text2",
        PARENT: "UR-01",
        CHILD: "R-01, R-02",
        LINE_NO: "2",
    }


def test_req_from_term_with_title_and_attributes() -> None:
    req = req_from_term(
        "SR-001::",
        2,
        enumerate(
            ["Some title:", "+", "Req. text", "+", "Child: R-01, R-02; Parent: UR-01"],
            start=3,
        ),
        doc_with_req_prefix(),
    )
    assert req == {
        ID: "SR-001",
        TITLE: "Some title",
        TEXT: "Req. text",
        PARENT: "UR-01",
        CHILD: "R-01, R-02",
        LINE_NO: "2",
    }


def test_req_from_term_with_multi_line_attributes() -> None:
    req = req_from_term(
        "SR-001::",
        2,
        enumerate(["Req. text", "+", "Child: R-01, R-02;", "Parent: UR-01"], start=3),
        doc_with_req_prefix(),
    )
    assert req == {
        ID: "SR-001",
        TEXT: "Req. text",
        PARENT: "UR-01",
        CHILD: "R-01, R-02",
        LINE_NO: "2",
    }


def test_req_from_term_with_doubly_defined_attribute() -> None:
    assert not req_from_term(
        "SR-001::",
        2,
        enumerate(["Req. text", "+", "Text: Text"], start=3),
        doc_with_req_prefix(),
    )


def test_req_from_term_not_a_req_term() -> None:
    assert not req_from_term(
        "Some term::", 2, enumerate([], start=3), doc_with_req_prefix()
    )


def test_req_from_term_not_a_term() -> None:
    assert not req_from_term(
        "SR-001:", 2, enumerate([], start=3), doc_with_req_prefix()
    )


def test_req_from_term_empty_lines() -> None:
    assert not req_from_term(
        "SR-001::", 2, enumerate([], start=3), doc_with_req_prefix()
    )
