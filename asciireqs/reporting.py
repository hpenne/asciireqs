"""reporting - functions to output tables etc. to asciidoc reports"""

import os
import re
from typing import Dict, Iterable, List, Optional, Tuple

from asciireqs.fields import ID, LINE_NO, TEXT, PARENT, CHILD
from asciireqs.docparser import Project, req_from_yaml_lines
from asciireqs.reqdocument import ReqDocument, Requirement, Requirements


def get_spec_hierarchy(doc: ReqDocument, preamble: str) -> List[str]:
    """Takes a ReqDocument and a hierarchical document list for that document and its children"""
    preamble = preamble + "*"
    text: List[str] = [f"{preamble} {doc.name}\n"]
    for sub_doc in doc.child_docs:
        text += get_spec_hierarchy(sub_doc, preamble)
    return text


def has_element(field_text: str, sub_str: str) -> bool:
    """Takes a string of comma separated values and returns True if the specified value was found"""
    for element in field_text.split(","):
        if element.strip() == sub_str:
            return True
    return False


def split_req_list(req_list: str) -> List[str]:
    """Takes a string of comma separated requirement IDs and returns each ID"""
    return [req.strip() for req in req_list.split(",") if req]


def missing_link_from_parent(requirement: Requirement, project: Project) -> bool:
    """
    Checks if the parent-child links for a requirement goes both ways consistently.
    For each parent of the requirement, checks if there is a child requirement pointing back.
    :param requirement: The requirement to check
    :param project: The project data model
    :return: True if each parent has a link back to the child
    """
    if "Parent" not in requirement.keys():
        return False
    for parent_id in split_req_list(requirement["Parent"]):
        parent_req = project.requirements[parent_id]
        if "Child" not in parent_req:
            return True
        parent_children_id = split_req_list(parent_req["Child"])
        if not requirement[ID] in parent_children_id:
            return True
    return False


def evaluate_requirement_against_filter(
    req: Requirement, project: Project, filter_expression: str
) -> bool:
    """
    Evaluate a requirement against a (very limited) Python expression.
    :param req: The requirement
    :param project: The project data model
    :param filter_expression: The Python expression to evaluate
    :return: The result of the expression
    """

    def link_error() -> bool:
        return missing_link_from_parent(req, project)

    allowed_names = {"req": req, "has_element": has_element, "link_error": link_error}
    code = compile(filter_expression, "<string>", "eval")
    for name in code.co_names:
        if name not in allowed_names:
            raise NameError(f"Use of {name} not allowed")
    # pylint: disable=W0123
    return eval(filter_expression, {"__builtins__": {}}, allowed_names) is True


def table_line(req: Requirement, attribute_names: List[str]) -> Optional[str]:
    """
    Generates a single table row of AsciiDoc text  for one requirement.
    Columns are generated only for the specified requirement attribute names
    :param req: The requirement
    :param attribute_names: The attribute names to generate columns for
    :return: AsciiDoc text for the table row
    """
    line: str = ""
    for field in attribute_names:
        if field in req:
            line += f"|{req[field]}\n"
        else:
            line += "|\n"
    line += "\n"
    return line


def get_table(
    project: Project,
    requirements: Requirements,
    attribute_names: List[str],
    filter_expression: str,
) -> List[str]:
    """
    Generates AsciiDoc table text for a list of requirements, filtered using a Python expression
    :param project: The project data model
    :param requirements: The requirements to put in the table
    :param attribute_names: The attribute names to generate columns for
    :param filter_expression: The Python expression to evaluate
    :return: AsciiDoc text for the table
    """
    table: List[str] = ["|===\n"]
    for field in attribute_names:
        table.append(f"|{field} ")
    table.append("\n\n")
    try:
        for req in requirements.values():
            if evaluate_requirement_against_filter(req, project, filter_expression):
                line = table_line(req, attribute_names)
                if line:
                    table.append(line)
        table.append("|===\n")
        return table
    except NameError as exception:
        print(f"Name error in expression evaluation: {exception}")
        return []
    except KeyError as exception:
        print(f"Property lookup error in expression evaluation: {exception}")
        return []


def line_numbers_for_requirements(requirements: Requirements) -> Dict[int, str]:
    """Takes requirements and returns the line numbers for each requirement, and their IDs"""
    lines: Dict[int, str] = {}
    for req_id, attributes in requirements.items():
        lines[int(attributes[LINE_NO])] = req_id
    return lines


def insert_requirement_links(line: str, doc: ReqDocument) -> str:
    """Takes a line of AsciiDoc text and adds cross-links to requirement IDs"""
    line = re.sub(rf"({doc.req_prefix}\d+)", f"xref:{doc.name}#\\1[\\1]", line)
    for child_doc in doc.child_docs:
        line = insert_requirement_links(line, child_doc)
    return line


def insert_anchor(line: str, req_id: str, root_document: ReqDocument) -> str:
    """Takes a line of AsciiDoc text and adds cross-link anchors where requirements are defined"""
    req_begin = line.find(req_id)
    req_end = req_begin + len(req_id)
    return (
        line[:req_begin]
        + "[["
        + line[req_begin:req_end]
        + "]]"
        + line[req_begin:req_end]
        + insert_requirement_links(line[req_end:], root_document)
    )


# ToDo: Unit test and doc
def requirement_as_term(req: Requirement) -> Iterable[str]:
    yield "[horizontal]\n"
    yield req[ID] + ":: " + req[TEXT] + "\n"
    yield "+\n"
    attr_line = ""
    first = True
    for attribute, value in req.items():  # ToDo: Comprehension with join
        if attribute not in (ID, TEXT, LINE_NO):
            if first:
                first = False
            else:
                attr_line = attr_line + "; "
            attr_line = attr_line + attribute + ": " + value
    attr_line += "\n"
    yield attr_line  # ToDo: Anchors and links


def generate_report_line(
    input_lines: Iterable[Tuple[int, str]],
    project: Project,
    requirements: Requirements,
    req_lines: Dict[int, str],
) -> Iterable[str]:
    """
    Takes lines of AsciiDoc text and parses it to generate lines of AsciiDoc output.
    The parsing will insert cross-links and expand report generating macros,
    like document hierarchy and tables to generate
    :param input_lines: The input text
    :param project: The project data model
    :param requirements: The requirements of the current document
    :param req_lines: The lines numbers where the document's requirements are defined
    :return: The generated AsciiDoc text
    """
    for line_no, input_line in input_lines:
        stripped_line: str = input_line.strip()
        if stripped_line == "`asciireq-hierarchy`":
            for line in get_spec_hierarchy(project.root_document, ""):
                yield line
        elif stripped_line.startswith("`asciireq-table:") and stripped_line.endswith(
            "`"
        ):
            field_name_list, filter_expression = [
                param.strip() for param in stripped_line[16:-1].strip().split(";")
            ]
            field_names = [name.strip() for name in field_name_list.strip().split(",")]
            for line in get_table(
                project, requirements, field_names, filter_expression
            ):
                yield line
        elif stripped_line.startswith("[.reqy]"):
            # Consume the listing block of YAML:
            req_from_yaml = req_from_yaml_lines(input_lines)
            if req_from_yaml and ID in req_from_yaml and req_from_yaml[ID] in requirements:
                # Replace with formatting using "Term":
                req = requirements[req_from_yaml[ID]]
                yield from requirement_as_term(req)
        else:
            if line_no in req_lines:
                # This line contains a requirement definition which we want to make into an anchor:
                yield insert_anchor(
                    input_line, req_lines[line_no], project.root_document
                )
            else:
                yield insert_requirement_links(input_line, project.root_document)


def post_process_hierarchically(
    project: Project, document: ReqDocument, output_dir: str
) -> None:
    """
    Performs post-processing of all the project requirement files, by post processing
    the specified document, then all its children hierarchically.
    The parsing will insert cross-links and expand report generating macros,
    like document hierarchy and tables to generate
    :param project: The project data model
    :param document: The document to process
    :param output_dir: The folder to write output files to
    """
    requirement_lines = line_numbers_for_requirements(document.reqs)
    _, output_file_name = os.path.split(document.name)
    output_path = os.path.join(output_dir, output_file_name)
    with open(document.name, "r", encoding="utf-8") as input_file:
        with open(output_path, "w", encoding="utf-8") as output_file:
            for line in generate_report_line(
                enumerate(input_file, start=1),
                project,
                document.reqs,
                requirement_lines,
            ):
                output_file.write(line)
    for sub_doc in document.child_docs:
        post_process_hierarchically(project, sub_doc, output_dir)
