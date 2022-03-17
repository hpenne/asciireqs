"""docparser - Contains functions to scan an asciidoc file for requirements"""

import re
import os
from copy import copy
from typing import Iterable
from typing import Optional
from typing import List
from typing import Tuple
from dataclasses import dataclass
from asciireqs.reqdocument import ReqDocument
from asciireqs.reqdocument import Requirement
from asciireqs.reqdocument import Requirements


@dataclass
class Project:
    root_document: ReqDocument
    requirements: Requirements


Cells = List[str]
Row = Cells
Table = List[Row]


def append_cells(table_rows: Table, num_columns: int, cells: Cells) -> None:
    if not table_rows:
        table_rows.append(cells)
    else:
        for cell in cells:
            if len(table_rows[-1]) == num_columns:
                table_rows.append([cell])
            else:
                table_rows[-1].append(cell)


# ToDo: Use the cols attribute(?) to get the number of columns
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
            cells: Cells = [cell.strip() for cell in line.split('|')]
            if len(cells) < 2:
                print(f'Error on line {line_no}, not table: {line}')
                return None, None
            matches = column_merge.search(cells[0]) if cells[0] else None
            if matches:
                # The line starts with a cell merge specifier, so generate None cells for the unused ones:
                additional_cells: int = int(matches.groups()[0]) - 1
                cells = cells + additional_cells * ['']
            if not num_columns:
                num_columns = len(cells) - 1
            append_cells(table_rows, num_columns, cells[1:])  # Drop the initial non-cell element we got from split()
        else:
            if line.rstrip() == '|===':
                in_table = True
            elif not attributes.match(line):
                print(f'Error on line {line_no}: Expected attributes or table start, but was: {line}')  # f-string
                return None, None
    return None, None


def reqs_from_req_table(heading: Row, table_lines: Table) -> Iterable[Requirement]:
    if table_lines:
        for line in table_lines:
            yield {heading[i]: column for (i, column) in enumerate(line)}


def req_from_single_req_table(table_lines: Table) -> Optional[Requirement]:
    req = {'ID': table_lines[0][0]}  # First cell should be requirement ID
    for cell in sum(table_lines, [])[1:]:
        if cell:
            parts = [part.strip() for part in cell.split(':')]
            if len(parts) == 1:
                if 'Text' in req:
                    print(
                        f"Error in single req. table: Second non-property/value pair found (only one allowed): {cell}")
                    return None
                req['Text'] = cell
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
    else:
        return None


def parse_doc(lines: Iterable[Tuple[int, str]]) -> ReqDocument:
    doc = ReqDocument()
    for _, text in lines:
        text = text.rstrip()
        if text == '[.reqs]':
            heading, rows = get_table(lines)
            if heading and rows:
                doc.add_reqs(reqs_from_req_table(heading, rows))
                doc.add_keys(heading)
        elif text == '[.req]':
            heading, rows = get_table(lines)
            if rows:
                req = req_from_single_req_table(rows)
                if req:
                    doc.add_keys(list(req.keys()))  # ToDo: Keep order?
                    doc.add_req(req)
        else:
            attribute_vale = get_attribute(text, 'req-children')
            if attribute_vale:
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


def read_and_parse_project(file_path: str) -> Project:
    path, file_name = os.path.split(file_path)
    doc = read_and_parse(file_path)
    requirements = copy(doc.get_reqs())
    for sub_file_name in doc.get_child_doc_files():
        child_doc = read_and_parse(os.path.join(path, sub_file_name))
        doc.add_child_doc(child_doc)
        requirements |= child_doc.get_reqs()  # ToDo: Check for duplicates
    return Project(doc, requirements)
