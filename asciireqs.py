#!/usr/bin/env python3

import argparse
from reqdocument import ReqDocument
from reporting import write_spec_hierarchy, write_table
from docparser import parse_doc


def read_and_parse(file_name: str) -> ReqDocument:
    with open(file_name) as file:
        doc = parse_doc(enumerate(file, start=1))
        doc.set_name(file_name.split('.')[0])
        for req in doc.get_reqs().values():
            print(req)
        return doc


def read_and_parse_hierarchy(file_name: str) -> ReqDocument:
    doc = read_and_parse(file_name)
    for sub_file_name in doc.get_child_doc_files():
        doc.add_child_doc(read_and_parse(sub_file_name))
    return doc


def main():
    parser = argparse.ArgumentParser(description="Get requirements from an asciidoc file")
    parser.add_argument('reqdoc', help="File to parse")
    parser.add_argument('-csv', help="File to export requirements to", type=str)
    parser.add_argument('-report')
    args = parser.parse_args()

    doc = read_and_parse_hierarchy(args.reqdoc)

    if args.csv:
        with open(args.csv, 'w') as csv_file:
            csv_file.write(','.join(doc.get_keys()))
            csv_file.write('\n')
            for req in doc.get_reqs().values():
                csv_file.write(','.join(req[key] if key in req else '' for key in doc.get_keys()))
                csv_file.write('\n')

    if args.report:
        with open(args.report, 'w') as report_file:
            report_file.write(f'= Requirements analysis report for {args.reqdoc}\n\n')
            report_file.write('== Requirement document hierarchy\n\n')
            write_spec_hierarchy(report_file, doc, '')
            report_file.write('== Requirements for release 1\n\n')
            write_table(report_file, doc, ['ID', 'Text', 'Tags'], 'has_element(req["Tags"], "Rel-1")')


if __name__ == "__main__":
    main()
