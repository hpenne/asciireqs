"""test_docparser: Tests for the docparser modele"""

from asciireqs.docparser import *


def row(elements: List[Tuple[str, int]]) -> List[Cell]:
    return [Cell(value, Location(line)) for value, line in elements]


def empty() -> Tuple[str, int]:
    return str(), 0


def test_table() -> None:
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A | B | C', '|==='], start=1)
    heading, t = get_table(lines)
    assert t
    assert len(t) == 1
    assert t[0] == row([('A', 3), ('B', 3), ('C', 3)])


def test_table_single_element_lines() -> None:
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A | B | C', '| D', '|E', '| F', '|==='],
                      start=1)
    heading, rows = get_table(lines)
    assert not heading
    assert rows
    assert len(rows) == 2
    assert rows[0] == row([('A', 3), ('B', 3), ('C', 3)])
    assert rows[1] == row([('D', 4), ('E', 5), ('F', 6)])


def test_table_with_heading() -> None:
    lines = enumerate(['|===', '| 1 | 2 | 3', '', '| A | B | C', '| D', '|E', '| F', '|==='],
                      start=1)
    heading, rows = get_table(lines)
    assert heading == [Cell('1', Location(2)), Cell('2', Location(2)), Cell('3', Location(2))]
    assert rows
    assert len(rows) == 2
    assert rows[0] == row([('A', 4), ('B', 4), ('C', 4)])
    assert rows[1] == row([('D', 5), ('E', 6), ('F', 7)])


def test_table_missing_element() -> None:
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A | B | C', '| D', '|E', '|==='], start=1)
    heading, rows = get_table(lines)
    assert not heading
    assert not rows


def test_table_cols_inside() -> None:
    lines = enumerate(['|===', '[cols="1,1,1"]', '| A | B | C |', '|==='], start=1)
    heading, rows = get_table(lines)
    assert not rows


def test_table_merged_cells() -> None:
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A', '| B', '| C', '3+| Merged', '|==='],
                      start=1)
    heading, rows = get_table(lines)
    assert rows
    assert len(rows) == 2
    assert rows[0] == row([('A', 3), ('B', 4), ('C', 5)])
    assert rows[1] == row([('Merged', 6), empty(), empty()])


def test_reqs_from_reqtable() -> None:
    heading = row([('1', 2), ('2', 2), ('3', 2)])
    rows = [row([('A', 3), ('B', 3), ('C', 3)]),
            row([('D', 4), ('E', 4), ('F', 4)])]
    reqs = list(reqs_from_req_table(heading, rows))
    assert reqs
    assert len(reqs) == 2
    assert reqs[0] == {'1': 'A', '2': 'B', '3': 'C', fields.LINE_NO: 3}
    assert reqs[1] == {'1': 'D', '2': 'E', '3': 'F', fields.LINE_NO: 4}
