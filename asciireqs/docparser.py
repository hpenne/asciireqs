"""docparser - Contains functions to scan an asciidoc file for requirements"""

import os
import re
from copy import copy
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from asciireqs.reqdocument import ReqDocument, Requirement, Requirements
import asciireqs.fields as fields


@dataclass
class Project:
    root_document: ReqDocument
    requirements: Requirements


@dataclass
class Location:
    line: int


@dataclass
class Cell:
    data: str
    location: Location

    def empty(self) -> bool:
        return not self.data


def empty_cell():
    return Cell('', Location(0))


Cells = List[Cell]
Row = Cells
Table = List[Row]


def append_cells(table_rows: Table, num_columns: int, cells: Cells) -> None:
    if not table_rows and len(cells) > 0:
        table_rows.append(cells)
    else:
        for cell in cells:
            if len(table_rows[-1]) == num_columns:
                table_rows.append([cell])
            else:
                table_rows[-1].append(cell)


def get_cols_from_attribute(line: str, line_no: int) -> Optional[int]:
    # This is crude, but it usually works:
    num_widths = len(line.split(','))
    if num_widths >= 2:
        return num_widths
    else:
        eq_pos = line.find('=')
        bracket_pos = line.find(']')
        if 0 <= eq_pos < bracket_pos:
            num_str = line[eq_pos + 1: bracket_pos]
            return int(num_str)
        else:
            print(f'Error on line {line_no}, failed to parse number of columns: {line}')
            return None


def get_table(lines: Iterable[Tuple[int, str]]) -> Tuple[Optional[Row], Optional[Table]]:
    in_table: bool = False
    num_columns: Optional[int] = None
    table_rows: Table = []
    heading_cells: Optional[Row] = None
    attributes = re.compile(r'\[\w+=.+]')
    column_merge = re.compile(r'(\d+)\+')
    for line_no, line in lines:
        if in_table:
            if line.rstrip() == '|===':
                if len(table_rows[0]) != len(table_rows[-1]):
                    print(f'Error on line {line_no}, table missing cell(s) on last row: {line}')
                    return None, None
                return heading_cells, table_rows
            if not line.strip():
                if len(table_rows) == 1 and not heading_cells:
                    # The first line of cells was the heading:
                    heading_cells = table_rows[0]
                    table_rows = []
                continue
            cells: Cells = [Cell(cell.strip(), Location(line_no)) for cell in line.split('|')]
            matches = column_merge.search(cells[0].data) if cells[0] else None
            if matches:
                # The line starts with a cell merge specifier,
                # so generate None cells for the unused ones:
                additional_cells = int(matches.groups()[0]) - 1
                cells = cells + additional_cells * [empty_cell()]
            # Drop the "cell" before the vertical bar (not a cell):
            cells = cells[1:]
            if not num_columns and len(cells) > 0:
                # If the number of columns has not been set, then this must be the heading row:
                num_columns = len(cells)
            append_cells(table_rows, num_columns, cells)
        else:
            if line.startswith('[cols'):
                num_columns = get_cols_from_attribute(line, line_no)
            if line.rstrip() == '|===':
                in_table = True
            elif not attributes.match(line):
                print(
                    f'Error on line {line_no}: Expected attributes or table start, but was: {line}')
                return None, None
    return None, None


def reqs_from_req_table(heading: Row, table_rows: Table) -> Iterable[Requirement]:
    if table_rows:
        for row in table_rows:
            req = {heading[i].data: cell.data for (i, cell) in enumerate(row)}
            req[fields.LINE_NO] = row[0].location.line
            yield req


def req_from_single_req_table(table_lines: Table) -> Optional[Requirement]:
    # First cell should be requirement ID
    req = {fields.ID: table_lines[0][0].data, fields.LINE_NO: table_lines[0][0].location.line}
    for cell in sum(table_lines, [])[1:]:
        if cell:
            parts = [part.strip() for part in cell.data.split(':')]
            if len(parts) == 1:
                if 'Text' in req:
                    if not cell.empty():
                        print(("Error in single req. table: Second non-property/value pair found"
                               f"(only one allowed): {cell}"))
                        return None
                else:
                    req['Text'] = parts[0]
            else:
                if parts[0]:
                    req[parts[0]] = parts[1]
                else:
                    print(
                        f"Error in single req. table: Property name not found: {cell}")
                    return None
    return req


def get_attribute(line: str, name: str) -> Optional[str]:
    attribute = ':' + name + ':'
    if line.startswith(attribute):
        return line[len(attribute):].strip()
    return None


def parse_doc(lines: Iterable[Tuple[int, str]]) -> ReqDocument:
    doc = ReqDocument()
    for _, text in lines:
        text = text.rstrip()
        if text == '[.reqs]':
            heading, rows = get_table(lines)
            if heading and rows:
                doc.add_reqs(reqs_from_req_table(heading, rows))
                doc.add_keys([cell.data for cell in heading])
        elif text == '[.req]':
            heading, rows = get_table(lines)
            if rows:
                req = req_from_single_req_table(rows)
                if req:
                    doc.add_keys(list(req.keys()))
                    doc.add_req(req)
        else:
            attribute_value = get_attribute(text, 'req-children')
            if attribute_value:
                doc.child_doc_files = [file_name.strip() for file_name in attribute_value.split(',')]
            attribute_value = get_attribute(text, 'req-prefix')
            if attribute_value:
                doc.req_prefix = attribute_value
    return doc


def read_and_parse(file_name: str) -> ReqDocument:
    with open(file_name, 'r') as file:
        doc = parse_doc(enumerate(file, start=1))
        doc.name = file_name
        for req in doc.reqs.values():
            print(req)
        return doc


def read_and_parse_project(file_path: str) -> Project:
    path, _ = os.path.split(file_path)
    doc = read_and_parse(file_path)
    requirements = copy(doc.reqs)
    for sub_file_name in doc.child_doc_files:
        child_doc = read_and_parse(os.path.join(path, sub_file_name))
        doc.add_child_doc(child_doc)
        requirements |= child_doc.reqs  # ToDo: Check for duplicates
    return Project(doc, requirements)
