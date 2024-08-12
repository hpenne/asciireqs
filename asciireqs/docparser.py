"""docparser - Contains functions to scan an asciidoc file for requirements"""

import os
import re
from copy import copy
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import yaml
from yaml.scanner import ScannerError

from asciireqs.fields import ID, TEXT, LINE_NO, TITLE
from asciireqs.reqdocument import (
    ReqDocument,
    Requirement,
    Requirements,
    ReqParseError,
    add_attribute,
    add_attributes,
)


@dataclass
class Project:
    """This class holds the complete project data model"""

    root_document: ReqDocument
    requirements: Requirements


@dataclass
class Location:
    """This class hold information about the file location of a requirement"""

    line: int


def get_source_block(lines: Iterable[Tuple[int, str]]) -> Tuple[List[str], int]:
    """
    Takes AsciiDoc lines of text (starting with a source block) and consumes the source block
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
    if not doc.req_regex:
        print("Error: Document has no req_regex attribute")
        return False
    if ID not in req:
        print(f"Error: Missing ID attribute on line {line_no}")
        return False
    if TEXT not in req:
        print(f"Error: Missing Text attribute on line {line_no}")
        return False
    if not re.match(f"{doc.req_regex}", req[ID]):
        print(f"Error: Wrong ID format on line {line_no}")
        return False
    return True


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
    if re.match(f"{doc.req_regex}", next(iter(attributes.keys()))):
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
    :param doc: The current document
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


def parse_term_req_attributes(line: str) -> Optional[Dict[str, str]]:
    """Takes a line of term attribute text and returns the attributes in it"""
    line = line.strip()
    attribute_defs = (part.strip() for part in line.split(";") if part.strip())
    attributes: Dict[str, str] = {}
    for name_value in attribute_defs:
        parts = name_value.split(":")
        if len(parts) != 2:
            raise ReqParseError("Incorrect format for requirement")
        add_attribute(attributes, parts[0], parts[1])
        attributes[parts[0]] = parts[1].strip()
    return attributes


def get_term_attributes(lines: Iterable[Tuple[int, str]]) -> Dict[str, str]:
    """
    Parses lines containing attributes from a requirement defined as an AsciiDoc term,
    and returns the requirements. The last line consumed (if successful) is the
    empty line following the last line of attributes.
    :param lines: The input lines
    :return: Requirement attributes
    """
    all_attributes: Dict[str, str] = {}
    for _, line in lines:
        attributes = parse_term_req_attributes(line)
        if not attributes:
            break
        add_attributes(all_attributes, attributes)
    return all_attributes


def req_from_term(
    first_line: str, line_no: int, lines: Iterable[Tuple[int, str]], doc: ReqDocument
) -> Optional[Requirement]:
    """
    Tests a line of text to see if it is an AsciiDoc term used to define a requirement.
    If it is then the function consumes as many additional lines as necessary to parse the
    requirement and return it
    :param first_line: The line that may contain the start of a requirement as a term
    :param line_no: The document line number of the first parameter
    :param lines: The source for additional lines
    :param doc: The document that is being parsed
    :return: The requirement (or None if not found)
    """
    match = re.fullmatch(f"({doc.req_regex})::", first_line.strip())
    if match:
        req = {ID: match.group(1), LINE_NO: str(line_no)}
        try:
            # The next line is either a title or the first line of requirement text:
            line_iter = iter(lines)
            line = next(line_iter)[1]
            if line.rstrip().endswith(":"):
                # This is the title:
                req[TITLE] = line.rstrip(":")
                line_no, line = next(line_iter)
                if line.strip() != "+":
                    print(f'Error: Expected "+" on line {line_no}')
                    return None
                req[TEXT] = next(line_iter)[1]
            else:
                req[TEXT] = line

            # Next follows one or more lines of requirement text:
            while True:
                line = next(line_iter)[1].strip()
                if line == "+":
                    # The break marks the end of the text. Get the attributes:
                    attributes = get_term_attributes(lines)
                    if not attributes:
                        return None
                    add_attributes(req, attributes)
                    break
                if not line:
                    break
                # More requirement text:
                req[TEXT] = req[TEXT] + "\n" + line
        except StopIteration:
            pass
        except ReqParseError as exception:
            print(f"Error: {exception} on line {line_no}")
            return None
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
            doc.add_req(term_req)
        elif text == "[.reqy]":
            for req in req_from_yaml_block(lines, doc):
                doc.add_req(req)
        else:
            attribute_value = get_attribute(text, "req-children")
            if attribute_value:
                doc.child_doc_files = [
                    file_name.strip() for file_name in attribute_value.split(",")
                ]
            attribute_value = get_attribute(text, "req_regex")
            if attribute_value:
                doc.req_regex = attribute_value
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
