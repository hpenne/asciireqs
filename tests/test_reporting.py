"""tests_reporting - Tests for reporting.py"""

from asciireqs.fields import LINE_NO
from asciireqs.reporting import *


def doc1_reqs() -> Requirements:
    return {'D1-1': {fields.ID: 'D1-1', LINE_NO: 3}, 'D1-2': {fields.ID: 'D1-2', LINE_NO: 7}}


def test_line_numbers_for_requirements() -> None:
    lines = line_numbers_for_requirements(doc1_reqs())
    assert lines == {3: 'D1-1', 7: 'D1-2'}
