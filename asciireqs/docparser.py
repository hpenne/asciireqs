"""docparser - Contains functions to scan an asciidoc file for requirements"""

import os
import re
from copy import copy
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import yaml
from yaml.scanner import ScannerError

from asciireqs.fields import ID, TEXT, LINE_NO
from asciireqs.reqdocument import ReqDocument, Requirement, Requirements


@dataclass
class Project:
    """This class holds the complete project data model"""

    root_document: ReqDocument
    requirements: Requirements


@dataclass
class Location:
    """This class hold information about the file location of a requirement"""

    line: int


@dataclass
class Cell:
    """This class holds the contents of a table cell"""

    data: str
    location: Location

    def empty(self) -> bool:
        """Returns True if the Cell is empty"""
        return not self.data


def empty_cell() -> Cell:
    """Returns an empty Cell"""
    return Cell("", Location(0))


Cells = List[Cell]
Row = Cells
Table = List[Row]


def append_cells(table_rows: Table, num_columns: int, cells: Cells) -> None:
    """Takes a list of cells and appends them to the table, breaking them into rows"""
    if not table_rows and len(cells) > 0:
        table_rows.append(cells)
    else:
        for cell in cells:
            if len(table_rows[-1]) == num_columns:
                table_rows.append([cell])
            else:
                table_rows[-1].append(cell)


def get_cols_from_attribute(line: str, line_no: int) -> Optional[int]:
    """Interprets an AsciiDoc 'cols' attribute to get the number of table columns"""
    # This is crude, but it usually works:
    num_widths = len(line.split(","))
    if num_widths >= 2:
        return num_widths
    eq_pos = line.find("=")
    bracket_pos = line.find("]")
    if 0 <= eq_pos < bracket_pos:
        num_str = line[eq_pos + 1 : bracket_pos]
        try:
            return int(num_str)
        except ValueError:
            pass
    print(f"Error on line {line_no}, failed to parse number of columns: {line}")
    return None


def cells_from_line(line: str, line_no: int) -> Cells:
    """Takes a line of table text and converts it into cells"""
    cells: Cells = [Cell(cell.strip(), Location(line_no)) for cell in line.split("|")]
    column_merge = re.compile(r"(\d+)\+")
    matches = column_merge.search(cells[0].data) if cells[0] else None
    if matches:
        # The line starts with a cell merge specifier,
        # so generate None cells for the unused ones:
        additional_cells = int(matches.groups()[0]) - 1
        cells = cells + additional_cells * [empty_cell()]
    # Drop the "cell" before the vertical bar (not a cell):
    return cells[1:]


def get_table(
    lines: Iterable[Tuple[int, str]]
) -> Tuple[Optional[Row], Optional[Table]]:
    """Takes AsciiDoc lines of text and interprets it to get a Table"""
    in_table: bool = False
    num_columns: Optional[int] = None
    table_rows: Table = []
    heading_cells: Optional[Row] = None
    attributes = re.compile(r"\[\w+=.+]")
    for line_no, line in lines:
        if in_table:
            if line.rstrip() == "|===":
                if len(table_rows[0]) != len(table_rows[-1]):
                    print(
                        f"Error on line {line_no}, table missing cell(s) on last row: {line}"
                    )
                    return None, None
                return heading_cells, table_rows
            if not line.strip():
                if len(table_rows) == 1 and not heading_cells:
                    # The first line of cells was the heading:
                    heading_cells = table_rows[0]
                    table_rows = []
                continue
            cells = cells_from_line(line, line_no)
            if not num_columns and len(cells) > 0:
                # If the number of columns has not been set, then this must be the heading row:
                num_columns = len(cells)
            if num_columns:
                append_cells(table_rows, num_columns, cells)
        else:
            if line.startswith("[cols"):
                num_columns = get_cols_from_attribute(line, line_no)
            if line.rstrip() == "|===":
                in_table = True
            elif not attributes.match(line):
                print(
                    f"Error on line {line_no}: Expected attributes or table start, but was: {line}"
                )
                return None, None
    return None, None


def get_source_block(lines: Iterable[Tuple[int, str]]) -> Tuple[List[str], int]:
    """
    Takes AsciiDoc lines of text (starting with a source block) and consumes the sopurce block
    lines and returns them (not including the '----' start and end lines)
    :param lines: The input lines
    :return: The contents of the source block
    """
    is_first = True
    source: List[str] = []
    first_line_no: int = 0
    for line_no, line in lines:
        if is_first:
            first_line = line.strip(" \n")
            if first_line != "----":
                print(f"Error: Not a YAML block on line {line_no}")
                return [], 0
            first_line_no = line_no + 1
            is_first = False
        else:
            line = line.rstrip(" \n")
            if line == "----":
                return source, first_line_no
            source = source + [line]
    return [], 0


def validate_requirement(req: Requirement, doc: ReqDocument, line_no: int) -> bool:
    """Takes a Requirement and verifies that it contains the required attributes"""
    if not doc.req_prefix:
        print("Error: Document has no req-prefix attribute")
        return False
    if ID not in req:
        print(f"Error: Missing ID attribute on line {line_no}")
        return False
    if TEXT not in req:
        print(f"Error: Missing Text attribute on line {line_no}")
        return False
    if not req[ID].startswith(doc.req_prefix):
        print(f"Error: Wrong ID format on line {line_no}")
        return False
    return True


def reqs_from_req_table(
    heading: Row, table_rows: Table, doc: ReqDocument
) -> Iterable[Requirement]:
    """Takes a table and returns the requirements in it"""
    if table_rows:
        for row in table_rows:
            req = {heading[i].data: cell.data for (i, cell) in enumerate(row)}
            line_no = row[0].location.line
            req[LINE_NO] = str(line_no)
            if validate_requirement(req, doc, line_no):
                yield req


def req_from_single_req_table(
    table_lines: Table, doc: ReqDocument
) -> Optional[Requirement]:
    """Takes a table form and returns the single requirement in it"""
    # First cell should be requirement ID
    line_no = table_lines[0][0].location.line
    req = {
        ID: table_lines[0][0].data,
        LINE_NO: str(line_no),
    }
    for cell in sum(table_lines, [])[1:]:
        if cell:
            parts = [part.strip() for part in cell.data.split(":")]
            if len(parts) == 1:
                if TEXT in req:
                    if not cell.empty():
                        print(
                            (
                                "Error in single req. table: Second non-property/value pair found"
                                f"(only one allowed): {cell}"
                            )
                        )
                        return None
                else:
                    req[TEXT] = parts[0]
            else:
                if parts[0]:
                    req[parts[0]] = parts[1]
                else:
                    print(
                        f"Error in single req. table: Property name not found: {cell}"
                    )
                    return None
    return req if validate_requirement(req, doc, line_no) else None


def req_from_yaml_lines(
    lines: List[str], doc: ReqDocument, line_no: int
) -> List[Requirement]:
    """Takes a list of YAML source lines and returns the requirement therein"""
    try:
        attributes = yaml.safe_load("\n".join(lines))
    except ScannerError:
        print(f"Error: Failed to parse YAML on line {line_no}")
        return []
    if not attributes:
        print(f"Error: Failed to parse YAML on line {line_no}")
        return []

    reqs = []
    if next(iter(attributes.keys())).startswith(doc.req_prefix):
        # This is dict of requirements:
        for req_id, attrs in attributes.items():
            req = {name: str(value).strip(" \n") for name, value in attrs.items()}
            req[ID] = req_id
            if validate_requirement(req, doc, line_no):
                reqs += [req]
    else:
        # This must be a single requirement:
        req = {}
        for name, value in attributes.items():
            req[name] = str(value).strip(" \n")
        if validate_requirement(req, doc, line_no):
            reqs = [req]

    # The line number must be the line the ID is on, so we need to search for it:
    for req in reqs:
        req_id = req[ID]
        for id_line_no, line in enumerate(lines, start=line_no):
            if line.find(req_id) >= 0:
                req[LINE_NO] = str(id_line_no)
    return reqs


def req_from_yaml_block(
    lines: Iterable[Tuple[int, str]], doc: ReqDocument
) -> List[Requirement]:
    """
    Takes AsciiDoc lines of text (starting with a source block), consumes the source block
    lines, converts to YAML and returns the requirements defined by the YAML
    :param lines: The input lines
    :return: The requirements
    """
    yaml_lines, start_line_no = get_source_block(lines)
    if yaml_lines:
        return req_from_yaml_lines(yaml_lines, doc, start_line_no)
    return []


def get_attribute(line: str, name: str) -> Optional[str]:
    """Looks for a specific AsciiDoc attribute in a line and returns the value if found"""
    attribute = ":" + name + ":"
    if line.startswith(attribute):
        return line[len(attribute) :].strip()
    return None


def heading_names(heading: Row) -> List[str]:
    """Takes a list of heading cells and returns the heading names"""
    return [cell.data for cell in heading]


def heading_has_required_fields(heading: Row, line_no: int) -> bool:
    """Takes a list of heading cells and checks it contains columns for ID and Text"""
    names = heading_names(heading)
    if ID not in names:
        print(f"Error: Table must contain a column named '{ID}' on line {line_no}")
        return False
    if TEXT not in names:
        print(f"Error: Table must contain a column named '{TEXT}' on line {line_no}")
        return False
    return True


def parse_term_req_attributes(line: str, line_no: int) -> Optional[Dict[str, str]]:
    """Takes a line of term attribute text and returns the attributes in it"""
    line = line.strip()
    attribute_defs = (part.strip() for part in line.split(";") if part.strip())
    attributes = {}
    for name_value in attribute_defs:
        parts = name_value.split(":")
        if len(parts) != 2 or not parts[0].strip():
            print(f"Error: Incorrect format for requirement in line {line_no}")
            return {}
        if parts[0] in attributes:
            print(
                f"Error: Attribute {parts[0]} already defined for requirement in line {line_no}"
            )
            return {}
        attributes[parts[0]] = parts[1].strip()
    return attributes


def req_from_term(
    first_line: str, line_no: int, lines: Iterable[Tuple[int, str]], doc: ReqDocument
) -> Optional[Requirement]:
    """
    Tests a line of text to see if it is an AsciiDoc term used to define a requirement.
    If it is then the function consumes as many additional lines as necessary to parse the
    reqirement and return it
    :param first_line: The line that may contain the start of a requirement as a term
    :param line_no: The document line number of the first parameter
    :param lines: The source for additional lines
    :param doc: The document that is being parsed
    :return: The requirement (or None if not found)
    """
    match = re.fullmatch(rf"({doc.req_prefix}\d+)::", first_line.strip())
    if match:
        req = {ID: match.group(1), LINE_NO: str(line_no)}
        try:
            req[TEXT] = next(lines)[1]
            if next(lines)[1].strip() == "+":
                attributes = parse_term_req_attributes(next(lines)[1], line_no + 3)
                if not attributes:
                    return None
                for attr_name, _ in attributes.items():
                    if attr_name in req:
                        print(
                            f"Error: Attribute {attr_name} already "
                            "defined for requirement in line {line_no}"
                        )
                        return {}
                req = {**req, **attributes}
        except StopIteration:
            pass
        if validate_requirement(req, doc, line_no):
            return req
    return None


def parse_doc(lines: Iterable[Tuple[int, str]]) -> ReqDocument:
    """Parses lines of AsciiDoc text and returns a ReqDocument with all the requirements etc."""
    doc = ReqDocument()
    for line_no, text in lines:
        text = text.rstrip()
        term_req = req_from_term(text, line_no, lines, doc)
        if term_req:
            doc.add_keys(list(term_req.keys()))
            doc.add_req(term_req)
        elif text == "[.reqs]":
            heading, rows = get_table(lines)
            if heading and rows and heading_has_required_fields(heading, line_no):
                doc.add_reqs(reqs_from_req_table(heading, rows, doc))
                doc.add_keys(heading_names(heading))
        elif text == "[.req]":
            heading, rows = get_table(lines)
            if rows:
                req = req_from_single_req_table(rows, doc)
                if req:
                    doc.add_keys(list(req.keys()))
                    doc.add_req(req)
        elif text == "[.reqy]":
            for req in req_from_yaml_block(lines, doc):
                doc.add_keys(list(req.keys()))
                doc.add_req(req)
        else:
            attribute_value = get_attribute(text, "req-children")
            if attribute_value:
                doc.child_doc_files = [
                    file_name.strip() for file_name in attribute_value.split(",")
                ]
            attribute_value = get_attribute(text, "req-prefix")
            if attribute_value:
                doc.req_prefix = attribute_value
    return doc


def read_and_parse(file_name: str) -> ReqDocument:
    """Parses an AsciiDoc file and returns a ReqDocument with all the requirements etc."""
    with open(file_name, "r", encoding="utf-8") as file:
        doc = parse_doc(enumerate(file, start=1))
        doc.name = file_name
        for req in doc.reqs.values():
            print(req)
        return doc


def read_and_parse_project(file_path: str) -> Project:
    """Takes the path to the to level specification and returns a complete project model"""
    path, _ = os.path.split(file_path)
    doc = read_and_parse(file_path)
    requirements = copy(doc.reqs)
    for sub_file_name in doc.child_doc_files:
        child_doc = read_and_parse(os.path.join(path, sub_file_name))
        doc.add_child_doc(child_doc)
        for req_id, req in child_doc.reqs.items():
            if req_id in requirements:
                print(f"ERROR: Duplicate requirement {req_id}")
            else:
                requirements[req_id] = req
    return Project(doc, requirements)
