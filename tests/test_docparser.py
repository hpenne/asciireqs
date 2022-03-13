"""test_docparser: Tests for the docparser modele"""

from asciireqs.docparser import *


def test_table() -> None:
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A | B | C', '|==='], start=1)
    heading, t = get_table(lines)
    assert t
    assert len(t) == 1
    assert t[0] == ['A', 'B', 'C']


def test_table_single_element_lines() -> None:
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A | B | C', '| D', '|E', '| F', '|==='], start=1)
    heading, rows = get_table(lines)
    assert not heading
    assert rows
    assert len(rows) == 2
    assert rows[0] == ['A', 'B', 'C']
    assert rows[1] == ['D', 'E', 'F']


def test_table_with_heading() -> None:
    lines = enumerate(['|===', '| 1 | 2 | 3', '', '| A | B | C', '| D', '|E', '| F', '|==='], start=1)
    heading, rows = get_table(lines)
    assert heading == ['1', '2', '3']
    assert rows
    assert len(rows) == 2
    assert rows[0] == ['A', 'B', 'C']
    assert rows[1] == ['D', 'E', 'F']


def test_table_missing_element() -> None:
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A | B | C', '| D', '|E', '|==='], start=1)
    heading, rows = get_table(lines)
    assert not heading
    assert not rows


def test_table_merged_cells() -> None:
    lines = enumerate(['|===', '| A | B | C', '3+| Merged', '|==='], start=1)
    heading, rows = get_table(lines)
    assert rows
    assert len(rows) == 2
    assert rows[0] == ['A', 'B', 'C']
    assert rows[1] == ['Merged', '', '']


def test_table_cols_inside() -> None:
    lines = enumerate(['|===', '[cols="1,1,1"]', '| A | B | C |', '|==='], start=1)
    heading, rows = get_table(lines)
    assert not rows


def test_reqs_from_reqtable() -> None:
    heading = ['1', '2', '3']
    rows = [['A', 'B', 'C'],
            ['D', 'E', 'F']]
    reqs = list(reqs_from_req_table(heading, rows))
    assert reqs
    assert len(reqs) == 2
    assert reqs[0] == {'1': 'A', '2': 'B', '3': 'C'}
    assert reqs[1] == {'1': 'D', '2': 'E', '3': 'F'}
