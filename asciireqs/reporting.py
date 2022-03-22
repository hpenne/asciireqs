"""reporting - functions to output tables etc. to asciidoc reports"""

import os
from typing import Iterable, List, Optional, Tuple
from asciireqs.docparser import Project
from asciireqs.reqdocument import ReqDocument, Requirement, Requirements


def get_spec_hierarchy(doc: ReqDocument, preamble: str) -> List[str]:
    preamble = preamble + '*'
    text: List[str] = [f'{preamble} {doc.get_name()}\n']
    for sub_doc in doc.get_children():
        text += get_spec_hierarchy(sub_doc, preamble)
    return text


def has_element(field_text: str, sub_str: str) -> bool:
    return field_text.find(sub_str) >= 0


def split_req_list(req_list: str) -> List[str]:
    reqs: List[str] = []
    for req in req_list.split(','):
        reqs.append(req.strip())
    return reqs


def missing_link_from_parent(requirement: Requirement, project: Project) -> bool:
    if 'Parent' not in requirement.keys():
        return False
    for parent_id in split_req_list(requirement['Parent']):
        parent_req = project.requirements[parent_id]
        if 'Child' not in parent_req:
            return True
        parent_req = project.requirements[parent_id]
        if 'Child' not in parent_req:
            return True
        parent_children_id = split_req_list(parent_req['Child'])
        if not requirement['ID'] in parent_children_id:
            return True
    return False


def evaluate_requirement_against_filter(req: Requirement, project: Project,
                                        filter_expression: str) -> bool:
    try:
        def missing_down_link(requirement: Requirement) -> bool:
            return missing_link_from_parent(requirement, project)

        allowed_names = {'req': req, 'has_element': has_element, 'link_error': missing_down_link}
        code = compile(filter_expression, "<string>", "eval")
        for name in code.co_names:
            if name not in allowed_names:
                raise NameError(f"Use of {name} not allowed")
        return eval(filter_expression, {"__builtins__": {}}, allowed_names) is True
    except KeyError as _:
        return False  # ToDo: Propagate, location
    except NameError as exception:
        print(
            f'ERROR: Failed to evaluate filter expression: {exception}')  # ToDo: Propagate, location
        return False


def table_line(req: Requirement, fields: List[str]) -> Optional[str]:
    line: str = ''
    try:
        for field in fields:
            line += f'|{req[field]}\n'
        line += '\n'
        return line
    except KeyError:
        return None  # ToDo: Propagate, location


def get_table(project: Project, requirements: Requirements, fields: List[str],
              filter_expression: str) -> List[str]:
    table: List[str] = ['|===\n']
    for field in fields:
        table.append(f'|{field} ')
    table.append('\n\n')
    for req in requirements.values():
        if evaluate_requirement_against_filter(req, project, filter_expression):
            line = table_line(req, fields)
            if line:
                table.append(line)
    table.append('|===\n')
    return table


def generate_report_line(input_lines: Iterable[Tuple[int, str]], project: Project,
                         requirements: Requirements) -> Iterable[str]:
    for _, input_line in input_lines:
        stripped_line: str = input_line.strip()
        if stripped_line == '`asciireq-hierarchy`':
            for line in get_spec_hierarchy(project.root_document, ''):
                yield line
        elif stripped_line.startswith('`asciireq-table:') and stripped_line.endswith('`'):
            # ToDo: Error handling
            field_name_list, filter_expression = [param.strip() for param in
                                                  stripped_line[16:-1].strip().split(';')]
            field_names = [name.strip() for name in field_name_list.strip().split(',')]
            for line in get_table(project, requirements, field_names, filter_expression):
                yield line
        else:
            yield input_line


def post_process_hierarchically(project: Project, document: ReqDocument, output_dir: str):
    _, output_file_name = os.path.split(document.get_name())
    output_path = os.path.join(output_dir, output_file_name)
    with open(document.get_name(), 'r') as input_file:
        with open(output_path, 'w') as output_file:
            for line in generate_report_line(enumerate(input_file, start=1), project,
                                             document.get_reqs()):
                output_file.write(line)
    for sub_doc in document.get_children():
        post_process_hierarchically(project, sub_doc, output_dir)

# ToDo: Tests
