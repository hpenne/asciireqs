"""reporting - functions to output tables etc. to asciidoc reports"""

from typing import List, TextIO
from typing import Optional
from reqdocument import ReqDocument
from reqdocument import Requirement
from docparser import Project


def write_spec_hierarchy(file: TextIO, doc: ReqDocument, preamble: str) -> None:
    preamble = preamble + '*'
    file.write(f'{preamble} {doc.get_name()}\n')
    for sub_doc in doc.get_children():
        write_spec_hierarchy(file, sub_doc, preamble)
    file.write('\n')


def has_element(s: str, sub_str: str) -> bool:
    return s.find(sub_str) >= 0


def split_req_list(s: str) -> List[str]:
    reqs: List[str] = []
    for r in s.split(','):
        req = r.strip()
        reqs.append(req)
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
    except KeyError as e:
        return False  # ToDo: Propagate, location
    except NameError as e:
        print(f'ERROR: Failed to evaluate filter expression: {e}')  # ToDo: Propagate, location
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


def write_table(file: TextIO, project: Project, fields: List[str], filter_expression: str) -> None:
    file.write('|===\n')
    for field in fields:
        file.write(f'|{field} ')
    file.write('\n\n')
    for req in project.requirements.values():
        if evaluate_requirement_against_filter(req, project, filter_expression):
            line = table_line(req, fields)
            if line:
                file.write(line)
    file.write('|===\n')


# ToDo: Tests
