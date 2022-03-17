#!/usr/bin/env python3

import argparse
import os
from asciireqs.docparser import read_and_parse_project


def main() -> None:
    parser = argparse.ArgumentParser(description='Get requirements from an asciidoc file')
    parser.add_argument('reqdoc', help='File to parse')
    parser.add_argument('-r', '--recursive', action='store_true', dest='recursive',
                        help='Parse specifications recursively and output all requirements')
    parser.add_argument('-o', '--outputdir', dest='output_dir', help='Output directory', type=str)
    args = parser.parse_args()

    project = read_and_parse_project(args.reqdoc)
    reqs = project.requirements.values() if args.recursive else project.root_document.get_reqs().values()
    path, base = os.path.split(args.reqdoc)
    if args.output_dir:
        path = args.output_dir
    csv_file_name = os.path.join(path, os.path.splitext(base)[0] + '.csv')
    with open(csv_file_name, 'w') as csv_file:
        csv_file.write(','.join(project.root_document.get_keys()))
        csv_file.write('\n')
        for req in reqs:
            csv_file.write(','.join(
                req[key] if key in req else '' for key in project.root_document.get_keys()))
            csv_file.write('\n')


if __name__ == "__main__":
    main()
