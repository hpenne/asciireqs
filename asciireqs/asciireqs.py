#!/usr/bin/env python3

import argparse
from reporting import write_spec_hierarchy, write_table
from docparser import read_and_parse_project


# ToDo: Global dictionary for all reqs in project model
# ToDo: Report template
# ToDo: Link parent/child i project model (to allow reporting of reqs. linked only one way, using filters)
# ToDo: Output path and input path
# ToDo: Section and line numbers in requirements attributes
# ToDo: Read project from top doc, but export CVS from child doc
def main() -> None:
    parser = argparse.ArgumentParser(description='Get requirements from an asciidoc file')
    parser.add_argument('reqdoc', help='File to parse')
    parser.add_argument('-report', help='Generate report')
    parser.add_argument('-o', '--outputdir', dest='output_dir', type=str, help='Output directory')
    args = parser.parse_args()

    project = read_and_parse_project(args.reqdoc)

    if args.report:
        with open(args.report, 'w') as report_file:
            report_file.write(f'= Requirements analysis report for {args.reqdoc}\n\n')
            report_file.write('== Requirement document hierarchy\n\n')
            write_spec_hierarchy(report_file, project.root_document, '')
            report_file.write('== Requirements for release 1\n\n')
            write_table(report_file, project, ['ID', 'Text', 'Tags'], 'has_element(req["Tags"], "Rel-1")')
            report_file.write('== Requirements with missing links from parent\n\n')
            write_table(report_file, project, ['ID', 'Text', 'Tags'], 'link_error(req)')


if __name__ == "__main__":
    main()
