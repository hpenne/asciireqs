#!/usr/bin/env python3

import argparse
import re
from reqdocument import ReqDocument
from reporting import write_spec_hierarchy, write_table

from typing import Iterable
from typing import Optional
from typing import Tuple


# ToDo: Modularize table parsing

def append_cells(table_rows, num_columns, cells):
    if not table_rows:
        table_rows.append(cells)
    else:
        for cell in cells:
            if len(table_rows[-1]) == num_columns:
                table_rows.append([cell])
            else:
                table_rows[-1].append(cell)


# ToDo: Use the cols attribute(?) to get the number of columns
def get_table(lines):
    in_table = False
    num_columns = None
    table_rows = []
    heading_cells = None
    attributes = re.compile(r'\[\w+=.+]')
    column_merge = re.compile(r'(\d+)\+')
    for line_no, line in lines:
        if in_table:
            if line.rstrip() == '|===':
                if len(table_rows[0]) != len(table_rows[-1]):
                    print(f'Error on line {line_no}, table missing cell(s) on last row: {line}')
                    return [None, None]
                return [heading_cells, table_rows]
            if not line.strip():
                if len(table_rows) == 1 and not heading_cells:
                    # The first line of cells was the heading:
                    heading_cells = table_rows[0]
                    table_rows = []
                continue
            cells = [cell.strip() for cell in line.split('|')]
            if len(cells) < 2:
                print(f'Error on line {line_no}, not table: {line}')
                return [None, None]
            if matches := column_merge.search(cells[0]):
                # The line starts with a cell merge specifier, so generate None cells for the unused ones:
                additional_cells = int(matches.groups()[0]) - 1
                cells = cells + additional_cells * [None]
            if not num_columns:
                num_columns = len(cells) - 1
            append_cells(table_rows, num_columns, cells[1:])  # Drop the initial non-cell element we got from split()
        else:
            if line.rstrip() == '|===':
                in_table = True
            elif not attributes.match(line):
                print(f'Error on line {line_no}: Expected attributes or table start, but was: {line}')  # f-string
                return [None, None]


def reqs_from_req_table(heading, table_lines):
    if table_lines:
        for line in table_lines:
            yield {heading[i]: column for (i, column) in enumerate(line)}


def req_from_single_req_table(table_lines):
    req = {'ID': table_lines[0][0]}  # First cell should be requirement ID
    for cell in sum(table_lines, [])[1:]:
        if cell:
            parts = [part.strip() for part in cell.split(':')]
            if len(parts) != 2 or not parts[0] or not parts[1]:
                if 'Text' in req:
                    print(
                        f"Error in single req. table: Second non-property/value pair found (only one allowed): {cell}")
                    return None
                req['Text'] = cell
            else:
                req[parts[0]] = parts[1]
    return req


def get_attribute(line: str, name: str) -> Optional[str]:
    attribute = ':' + name + ':'
    if line.startswith(attribute):
        return line[len(attribute):].strip()
    else:
        return None


def parse_doc(lines: Iterable[Tuple[int, str]]) -> ReqDocument:
    doc = ReqDocument()
    for _, text in lines:
        text = text.rstrip()
        if text == '[.reqs]':
            heading, rows = get_table(lines)
            reqs = reqs_from_req_table(heading, rows)
            doc.add_keys(heading)
            for req in reqs:
                doc.add_req(req)
        elif text == '[.req]':
            heading, rows = get_table(lines)
            if req := req_from_single_req_table(rows):
                doc.add_keys(list(req.keys()))  # ToDo: Keep order?
                doc.add_req(req)
        elif attribute_vale := get_attribute(text, 'req-children'):
            doc.set_child_doc_files([file_name.strip() for file_name in attribute_vale.split(',')])
            print(f"Children: {doc.get_child_doc_files()}")
    return doc


def read_and_parse(file_name: str) -> ReqDocument:
    with open(file_name) as file:
        doc = parse_doc(enumerate(file, start=1))
        doc.set_name(file_name.split('.')[0])
        for req in doc.get_reqs().values():
            print(req)
        return doc


def read_and_parse_hierarchy(file_name: str) -> ReqDocument:
    doc = read_and_parse(file_name)
    for sub_file_name in doc.get_child_doc_files():
        doc.add_child_doc(read_and_parse(sub_file_name))
    return doc


def main():
    parser = argparse.ArgumentParser(description="Get requirements from an asciidoc file")
    parser.add_argument('reqdoc', help="File to parse")
    parser.add_argument('-csv', help="File to export requirements to", type=str)
    parser.add_argument('-report')
    args = parser.parse_args()

    doc = read_and_parse_hierarchy(args.reqdoc)

    if args.csv:
        with open(args.csv, 'w') as csv_file:
            csv_file.write(','.join(doc.get_keys()))
            csv_file.write('\n')
            for req in doc.get_reqs().values():
                csv_file.write(','.join(req[key] if key in req else '' for key in doc.get_keys()))
                csv_file.write('\n')

    if args.report:
        with open(args.report, 'w') as report_file:
            report_file.write(f'= Requirements analysis report for {args.reqdoc}\n\n')
            report_file.write('== Requirement document hierarchy\n\n')
            write_spec_hierarchy(report_file, doc, '')
            report_file.write('== Requirements for release 1\n\n')
            write_table(report_file, doc, ['ID', 'Text', 'Tags'], 'has_element(req["Tags"], "Rel-1")')


if __name__ == "__main__":
    main()


def test_table():
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A | B | C', '|==='], start=1)
    heading, t = get_table(lines)
    assert t
    assert len(t) == 1
    assert t[0] == ['A', 'B', 'C']


def test_table_single_element_lines():
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A | B | C', '| D', '|E', '| F', '|==='], start=1)
    heading, rows = get_table(lines)
    assert not heading
    assert rows
    assert len(rows) == 2
    assert rows[0] == ['A', 'B', 'C']
    assert rows[1] == ['D', 'E', 'F']


def test_table_with_heading():
    lines = enumerate(['|===', '| 1 | 2 | 3', '', '| A | B | C', '| D', '|E', '| F', '|==='], start=1)
    heading, rows = get_table(lines)
    assert heading == ['1', '2', '3']
    assert rows
    assert len(rows) == 2
    assert rows[0] == ['A', 'B', 'C']
    assert rows[1] == ['D', 'E', 'F']


def test_table_missing_element():
    lines = enumerate(['[cols="1,1,1"]', '|===', '| A | B | C', '| D', '|E', '|==='], start=1)
    heading, rows = get_table(lines)
    assert not heading
    assert not rows


def test_table_merged_cells():
    lines = enumerate(['|===', '| A | B | C', '3+| Merged', '|==='], start=1)
    heading, rows = get_table(lines)
    assert rows
    assert len(rows) == 2
    assert rows[0] == ['A', 'B', 'C']
    assert rows[1] == ['Merged', None, None]


def test_table_cols_inside():
    lines = enumerate(['|===', '[cols="1,1,1"]', '| A | B | C |', '|==='], start=1)
    heading, rows = get_table(lines)
    assert not rows


def test_reqs_from_reqtable():
    heading = ['1', '2', '3']
    rows = [['A', 'B', 'C'],
            ['D', 'E', 'F']]
    reqs = list(reqs_from_req_table(heading, rows))
    assert reqs
    assert len(reqs) == 2
    assert reqs[0] == {'1': 'A', '2': 'B', '3': 'C'}
    assert reqs[1] == {'1': 'D', '2': 'E', '3': 'F'}
