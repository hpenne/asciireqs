#!/usr/bin/env python3

import argparse
import os

import sys

from asciireqs.docparser import read_and_parse_project
from asciireqs.reporting import generate_report_line


# ToDo: Section and line numbers in requirements attributes
def main() -> None:
    parser = argparse.ArgumentParser(description='Get requirements from an asciidoc file')
    parser.add_argument('reqdoc', help='File to parse')
    parser.add_argument('-t', '--template', dest='report_template', type=str, help='Report template')
    parser.add_argument('-o', '--outputdir', dest='output_dir', type=str, help='Output directory')
    args = parser.parse_args()

    project = read_and_parse_project(args.reqdoc)

    if args.report_template:
        if not args.output_dir:
            sys.exit('--outputdir required when using --template')
        _, output_file_name = os.path.split(args.report_template)
        output_path = os.path.join(args.output_dir, output_file_name) if args.output_dir else args.report
        with open(args.report_template, 'r') as template_file:
            with open(output_path, 'w') as report_file:
                for line in generate_report_line(enumerate(template_file, start=1), project):
                    report_file.write(line)


if __name__ == "__main__":
    main()
