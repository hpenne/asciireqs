"""reporting - functions to output tables etc. to asciidoc reports"""

from reqdocument import ReqDocument
from reqdocument import Requirement
from typing import List
from typing import Optional


def write_spec_hierarchy(file, doc: ReqDocument, preamble: str):  # Type hint for file
    preamble = preamble + '*'
    file.write(f'{preamble} {doc.get_name()}\n')
    for sub_doc in doc.get_children():
        write_spec_hierarchy(file, sub_doc, preamble)
    file.write('\n')


def has_element(s: str, sub_str: str) -> bool:
    return s.find(sub_str) >= 0


def evaluate_requirement_against_filter(req: Requirement, filter_expression: str):
    try:
        allowed_names = {'req': req, 'has_element': has_element}
        code = compile(filter_expression, "<string>", "eval")
        for name in code.co_names:
            if name not in allowed_names:
                raise NameError(f"Use of {name} not allowed")
        return eval(filter_expression, {"__builtins__": {}}, allowed_names)
    except KeyError as e:
        return False  # ToDo: Propagate, location
    except NameError as e:
        print(f'ERROR: Failed to evaluate filter expression: {e}')  # ToDo: Propagate, location


def table_line(req: Requirement, fields: List[str]) -> Optional[str]:
    line: str = ''
    try:
        for field in fields:
            line += f'|{req[field]}\n'
        line += '\n'
        return line
    except KeyError:
        return None  # ToDo: Propagate, location


def write_table(file, doc: ReqDocument, fields: List[str], filter_expression: str):
    file.write('|===\n')
    for field in fields:
        file.write(f'|{field} ')
    file.write('\n\n')
    for req in doc.get_reqs().values():
        if evaluate_requirement_against_filter(req, filter_expression):
            line = table_line(req, fields)
            if line:
                file.write(line)
    file.write('|===\n')
