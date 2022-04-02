"""test_docparser: Tests for the docparser modele"""

from typing import List, Tuple
from asciireqs.docparser import (
    Cell,
    Location,
    get_table,
    reqs_from_req_table,
    req_from_single_req_table,
    get_source_block,
    req_from_yaml_dict,
    req_from_yaml_lines,
)
from asciireqs.fields import ID, LINE_NO


def row(elements: List[Tuple[str, int]]) -> List[Cell]:
    return [Cell(value, Location(line)) for value, line in elements]


def empty() -> Tuple[str, int]:
    return str(), 0


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


def test_reqs_from_reqtable() -> None:
    heading = row([("1", 2), ("2", 2), ("3", 2)])
    rows = [row([("A", 3), ("B", 3), ("C", 3)]), row([("D", 4), ("E", 4), ("F", 4)])]
    reqs = list(reqs_from_req_table(heading, rows))
    assert reqs
    assert len(reqs) == 2
    assert reqs[0] == {"1": "A", "2": "B", "3": "C", LINE_NO: "3"}
    assert reqs[1] == {"1": "D", "2": "E", "3": "F", LINE_NO: "4"}


def test_req_from_single_req_table() -> None:
    rows = [
        row([("ID-1", 3), ("Parent: ID-2", 3), ("Child: ID-3", 3)]),
        row([("Text", 4), empty(), empty()]),
    ]
    reqs = req_from_single_req_table(rows)
    assert reqs
    assert len(reqs) == 5
    assert reqs == {
        ID: "ID-1",
        "Parent": "ID-2",
        "Child": "ID-3",
        "Text": "Text",
        LINE_NO: "3",
    }


def test_req_from_single_req_table_with_three_rows() -> None:
    rows = [
        row([("ID-1", 3), ("Parent: ID-2", 3)]),
        row([("Tags: V.1", 3), ("Child: ID-3", 3)]),
        row([("Text", 4), empty(), empty()]),
    ]
    reqs = req_from_single_req_table(rows)
    assert reqs
    assert len(reqs) == 6
    assert reqs == {
        ID: "ID-1",
        "Parent": "ID-2",
        "Child": "ID-3",
        "Tags": "V.1",
        "Text": "Text",
        LINE_NO: "3",
    }


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
    assert not req_from_yaml_dict([], 13)


def test_req_from_yaml_block_with_simple_requirement() -> None:
    req = req_from_yaml_dict(["ID: SR-001", "Text: Some requirement"], 13)
    assert req == {"ID": "SR-001", "Text": "Some requirement", LINE_NO: str(13)}


def test_req_from_yaml_block_with_id_on_second_line() -> None:
    req = req_from_yaml_dict(["ID: |", "  SR-001", "Text: Some requirement"], 13)
    assert req == {"ID": "SR-001", "Text": "Some requirement", LINE_NO: str(14)}


def test_req_from_yaml_lines_with_single_requirement() -> None:
    source_input = ["ID: SR-001", "Text: Some requirement"]
    source_block_marker = ["----"]
    req = req_from_yaml_lines(
        enumerate(source_block_marker + source_input + source_block_marker, start=1)
    )
    assert req == {"ID": "SR-001", "Text": "Some requirement", LINE_NO: str(2)}
