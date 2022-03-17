"""reporting - functions to output tables etc. to asciidoc reports"""

from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from asciireqs.docparser import Project
from asciireqs.reqdocument import ReqDocument
from asciireqs.reqdocument import Requirement


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


def evaluate_requirement_against_filter(req: Requirement, project: Project, filter_expression: str) -> bool:
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
        print(f'ERROR: Failed to evaluate filter expression: {exception}')  # ToDo: Propagate, location
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


def get_table(project: Project, fields: List[str], filter_expression: str) -> List[str]:
    table: List[str] = ['|===\n']
    for field in fields:
        table.append(f'|{field} ')
    table.append('\n\n')
    for req in project.requirements.values():
        if evaluate_requirement_against_filter(req, project, filter_expression):
            line = table_line(req, fields)
            if line:
                table.append(line)
    table.append('|===\n')
    return table


def find_report_macro(line: str) -> Tuple[Optional[str], List[str]]:
    if line.startswith('asciireq-hierarchy'):
        return 'asciireq-hierarchy', []
    if line.startswith('asciireq-table:'):
        params = [param.strip() for param in line[15:].strip().split(';')]
        return 'asciireq-table:', params
    return None, []


def generate_report_line(input_lines: Iterable[Tuple[int, str]], project: Project) -> Iterable[str]:
    for _, input_line in input_lines:
        stripped_line: str = input_line.strip()
        if stripped_line == '`asciireq-hierarchy`':
            for line in get_spec_hierarchy(project.root_document, ''):
                yield line
        elif stripped_line.startswith('`asciireq-table:') and stripped_line.endswith('`'):
            # ToDo: Error handling
            field_name_list, filter_expression = [param.strip() for param in stripped_line[16:-1].strip().split(';')]
            field_names = [name.strip() for name in field_name_list.strip().split(',')]
            for line in get_table(project, field_names, filter_expression):
                yield line
        else:
            yield input_line


# ToDo: Tests
