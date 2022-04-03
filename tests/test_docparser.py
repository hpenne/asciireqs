"""test_docparser: Tests for the docparser modele"""

from typing import List, Tuple
from asciireqs.docparser import (
    Cell,
    Location,
    get_table,
    reqs_from_req_table,
    req_from_single_req_table,
    get_source_block,
    req_from_yaml_lines,
    req_from_yaml_block,
    get_cols_from_attribute,
    validate_requirement,
)
from asciireqs.fields import ID, TEXT, PARENT, CHILD, LINE_NO
from asciireqs.reqdocument import ReqDocument


def row(elements: List[Tuple[str, int]]) -> List[Cell]:
    return [Cell(value, Location(line)) for value, line in elements]


def empty() -> Tuple[str, int]:
    return str(), 0


def doc_with_req_prefix() -> ReqDocument:
    doc = ReqDocument()
    doc.req_prefix = "SR-"
    return doc


def test_table() -> None:
    lines = enumerate(['[cols="1,1,1"]', "|===", "| A | B | C", "|==="], start=1)
    heading, t = get_table(lines)
    assert t
    assert len(t) == 1
    assert t[0] == row([("A", 3), ("B", 3), ("C", 3)])


def test_table_single_element_lines() -> None:
    lines = enumerate(
        ['[cols="1,1,1"]', "|===", "| A | B | C", "| D", "|E", "| F", "|==="], start=1
    )
    heading, rows = get_table(lines)
    assert not heading
    assert rows
    assert len(rows) == 2
    assert rows[0] == row([("A", 3), ("B", 3), ("C", 3)])
    assert rows[1] == row([("D", 4), ("E", 5), ("F", 6)])


def test_table_with_heading() -> None:
    lines = enumerate(
        ["|===", "| 1 | 2 | 3", "", "| A | B | C", "| D", "|E", "| F", "|==="], start=1
    )
    heading, rows = get_table(lines)
    assert heading == [
        Cell("1", Location(2)),
        Cell("2", Location(2)),
        Cell("3", Location(2)),
    ]
    assert rows
    assert len(rows) == 2
    assert rows[0] == row([("A", 4), ("B", 4), ("C", 4)])
    assert rows[1] == row([("D", 5), ("E", 6), ("F", 7)])


def test_table_missing_element() -> None:
    lines = enumerate(
        ['[cols="1,1,1"]', "|===", "| A | B | C", "| D", "|E", "|==="], start=1
    )
    heading, rows = get_table(lines)
    assert not heading
    assert not rows


def test_table_with_incorrect_start() -> None:
    lines = enumerate(
        [
            '[cols="1,1,1"]',
            "This line does not belong here",
            "|===",
            "| A | B | C",
            "| D | E | F",
            "|===",
        ],
        start=1,
    )
    heading, rows = get_table(lines)
    assert not heading
    assert not rows


def test_single_req_table_with_column_widths() -> None:
    lines = enumerate(
        ['[cols="1,1,1"]', "|===", "| A", "| B", "| C", "3+| Merged", "|==="], start=1
    )
    heading, rows = get_table(lines)
    assert not heading
    assert rows
    assert len(rows) == 2
    assert rows[0] == row([("A", 3), ("B", 4), ("C", 5)])
    assert rows[1] == row([("Merged", 6), empty(), empty()])


def test_single_req_table_with_column_count() -> None:
    lines = enumerate(
        ["[cols=3]", "|===", "| A", "| B", "| C", "3+| Merged", "|==="], start=1
    )
    heading, rows = get_table(lines)
    assert not heading
    assert rows
    assert len(rows) == 2
    assert rows[0] == row([("A", 3), ("B", 4), ("C", 5)])
    assert rows[1] == row([("Merged", 6), empty(), empty()])


def test_invalid_cols_attribute() -> None:
    assert not get_cols_from_attribute("[cols=]", 2)


def test_validate_requirement() -> None:
    doc = ReqDocument()
    doc.req_prefix = "SR-"
    assert validate_requirement({ID: "SR-1", TEXT: "Some text"}, doc, 2)


def test_validate_requirement_no_req_prefix_attribute() -> None:
    doc = ReqDocument()
    assert not validate_requirement({ID: "SR-1", TEXT: "Some text"}, doc, 2)


def test_validate_requirement_no_id_field() -> None:
    doc = ReqDocument()
    doc.req_prefix = "SR-"
    assert not validate_requirement({TEXT: "Some text"}, doc, 2)


def test_validate_requirement_wrong_id_prefix() -> None:
    assert not validate_requirement(
        {ID: "S-1", TEXT: "Some text"}, doc_with_req_prefix(), 2
    )


def test_validate_requirement_no_text_field() -> None:
    doc = ReqDocument()
    doc.req_prefix = "SR-"
    assert not validate_requirement({ID: "SR-1"}, doc, 2)


def test_reqs_from_reqtable() -> None:
    heading = row([(ID, 2), (TEXT, 2), ("A", 2)])
    rows = [
        row([("SR-1", 3), ("B", 3), ("C", 3)]),
        row([("SR-2", 4), ("E", 4), ("F", 4)]),
    ]
    reqs = list(reqs_from_req_table(heading, rows, doc_with_req_prefix()))
    assert reqs
    assert len(reqs) == 2
    assert reqs[0] == {ID: "SR-1", TEXT: "B", "A": "C", LINE_NO: "3"}
    assert reqs[1] == {ID: "SR-2", TEXT: "E", "A": "F", LINE_NO: "4"}


def test_req_from_single_req_table() -> None:
    rows = [
        row([("SR-1", 3), ("Parent: ID-2", 3), ("Child: ID-3", 3)]),
        row([("Text", 4), empty(), empty()]),
    ]
    reqs = req_from_single_req_table(rows, doc_with_req_prefix())
    assert reqs
    assert len(reqs) == 5
    assert reqs == {
        ID: "SR-1",
        PARENT: "ID-2",
        CHILD: "ID-3",
        TEXT: "Text",
        LINE_NO: "3",
    }


def test_req_from_single_req_table_with_three_rows() -> None:
    rows = [
        row([("SR-1", 3), ("Parent: ID-2", 3)]),
        row([("Tags: V.1", 3), ("Child: ID-3", 3)]),
        row([("Text", 4), empty(), empty()]),
    ]
    reqs = req_from_single_req_table(rows, doc_with_req_prefix())
    assert reqs
    assert len(reqs) == 6
    assert reqs == {
        ID: "SR-1",
        PARENT: "ID-2",
        CHILD: "ID-3",
        "Tags": "V.1",
        TEXT: "Text",
        LINE_NO: "3",
    }


def test_req_from_single_req_table_with_multiple_text_fields() -> None:
    rows = [
        row([("SR-1", 3), ("Parent: ID-2", 3), ("Child: ID-3", 3)]),
        row([("Text1", 4), empty(), empty()]),
        row([("Text2", 4), empty(), empty()]),
    ]
    assert not req_from_single_req_table(rows, doc_with_req_prefix())


def test_req_from_single_req_table_with_missing_attribute_name() -> None:
    rows = [
        row([("SR-1", 3), ("Parent: ID-2", 3), (": ID-3", 3)]),
        row([("Text", 4), empty(), empty()]),
    ]
    assert not req_from_single_req_table(rows, doc_with_req_prefix())


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
    assert len(req) == 1
    assert req[0] == {ID: "SR-001", TEXT: "Some requirement", LINE_NO: str(2)}


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
