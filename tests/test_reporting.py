"""tests_reporting - Tests for reporting.py"""

from asciireqs.reporting import *


def test_missing_link_from_parent() -> None:
    assert True


def test_parse_hierachy_macro() -> None:
    line = 'asciireq-hierarchy'
    name, params = find_report_macro(line)
    assert name == line


def test_table_macro() -> None:
    line = 'asciireq-table:'
    name, params = find_report_macro(line)
    assert name == line
