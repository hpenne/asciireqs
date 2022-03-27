"""reporting - functions to output tables etc. to asciidoc reports"""

import os
import re
from typing import Dict, Iterable, List, Optional, Tuple

import asciireqs.fields as fields
from asciireqs.docparser import Project
from asciireqs.reqdocument import ReqDocument, Requirement, Requirements


def get_spec_hierarchy(doc: ReqDocument, preamble: str) -> List[str]:
    preamble = preamble + '*'
    text: List[str] = [f'{preamble} {doc.name}\n']
    for sub_doc in doc.child_docs:
        text += get_spec_hierarchy(sub_doc, preamble)
    return text


def has_element(field_text: str, sub_str: str) -> bool:
    for element in field_text.split(','):
        if element.strip() == sub_str:
            return True
    return False


def split_req_list(req_list: str) -> List[str]:
    return [req.strip() for req in req_list.split(',') if req]


def missing_link_from_parent(requirement: Requirement, project: Project) -> bool:
    if 'Parent' not in requirement.keys():
        return False
    for parent_id in split_req_list(requirement['Parent']):
        parent_req = project.requirements[parent_id]
        if 'Child' not in parent_req:
            return True
        parent_children_id = split_req_list(parent_req['Child'])
        if not requirement[fields.ID] in parent_children_id:
            return True
    return False


def evaluate_requirement_against_filter(req: Requirement, project: Project,
                                        filter_expression: str) -> bool:
    def link_error() -> bool:
        return missing_link_from_parent(req, project)
    allowed_names = {'req': req, 'has_element': has_element, 'link_error': link_error}
    code = compile(filter_expression, "<string>", "eval")
    for name in code.co_names:
        if name not in allowed_names:
            raise NameError(f"Use of {name} not allowed")
    return eval(filter_expression, {"__builtins__": {}}, allowed_names) is True


def table_line(req: Requirement, fields: List[str]) -> Optional[str]:
    line: str = ''
    for field in fields:
        if field in req:
            line += f'|{req[field]}\n'
        else:
            line += '|\n'
    line += '\n'
    return line


def get_table(project: Project, requirements: Requirements, fields: List[str],
              filter_expression: str) -> List[str]:
    table: List[str] = ['|===\n']
    for field in fields:
        table.append(f'|{field} ')
    table.append('\n\n')
    try:
        for req in requirements.values():
            if evaluate_requirement_against_filter(req, project, filter_expression):
                line = table_line(req, fields)
                if line:
                    table.append(line)
        table.append('|===\n')
        return table
    except NameError as exception:
        print(f'Name error in expression evaluation: {exception}')
        return []
    except KeyError as exception:
        print(f'Property lookup error in expression evaluation: {exception}')
        return []


def line_numbers_for_requirements(requirements: Requirements) -> Dict[int, str]:
    lines: Dict[int, str] = {}
    for req_id, attributes in requirements.items():
        lines[attributes[fields.LINE_NO]] = req_id
    return lines


def insert_requirement_links(line: str, doc: ReqDocument) -> str:
    line = re.sub(f'({doc.req_prefix}\d+)', f'xref:{doc.name}#\\1[\\1]', line)
    for child_doc in doc.child_docs:
        line = insert_requirement_links(line, child_doc)
    return line


def insert_anchor(line: str, req_id: str, root_document: ReqDocument) -> str:
    req_begin = line.find(req_id)
    req_end = req_begin + len(req_id)
    return line[:req_begin] + '[[' + line[req_begin:req_end] + ']]' \
           + line[req_begin:req_end] \
           + insert_requirement_links(line[req_end:], root_document)


def generate_report_line(input_lines: Iterable[Tuple[int, str]],
                         project: Project,
                         requirements: Requirements,
                         req_lines: Dict[int, str]) -> Iterable[Tuple[int, str]]:
    for line_no, input_line in input_lines:
        stripped_line: str = input_line.strip()
        if stripped_line == '`asciireq-hierarchy`':
            for line in get_spec_hierarchy(project.root_document, ''):
                yield line_no, line
        elif stripped_line.startswith('`asciireq-table:') and stripped_line.endswith('`'):
            field_name_list, filter_expression = [param.strip() for param in
                                                  stripped_line[16:-1].strip().split(';')]
            field_names = [name.strip() for name in field_name_list.strip().split(',')]
            for line in get_table(project, requirements, field_names, filter_expression):
                yield line_no, line
        else:
            if line_no in req_lines:
                # This line contains a requirement definition which we want to make into an anchor:
                yield line_no, insert_anchor(input_line, req_lines[line_no], project.root_document)
            else:
                yield line_no, insert_requirement_links(input_line, project.root_document)


def post_process_hierarchically(project: Project, document: ReqDocument, output_dir: str):
    requirement_lines = line_numbers_for_requirements(document.reqs)
    _, output_file_name = os.path.split(document.name)
    output_path = os.path.join(output_dir, output_file_name)
    with open(document.name, 'r') as input_file:
        with open(output_path, 'w') as output_file:
            for line_no, line in generate_report_line(enumerate(input_file, start=1), project,
                                                      document.reqs, requirement_lines):
                output_file.write(line)
    for sub_doc in document.child_docs:
        post_process_hierarchically(project, sub_doc, output_dir)
