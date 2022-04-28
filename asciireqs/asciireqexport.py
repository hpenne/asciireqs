#!/usr/bin/env python3
"""Export requirements to CVS format"""

import argparse
import os
from typing import List, Dict, Iterable
import sys
import openpyxl

from asciireqs.docparser import read_and_parse_project


def export_to_csv(
    outputpath: str, attributes: List[str], reqs: Iterable[Dict[str, str]]
) -> None:
    """Exports the requirements to a CSV file"""
    with open(outputpath, "w", encoding="utf-8") as csv_file:
        csv_file.write(",".join(attributes))
        csv_file.write("\n")
        for req in reqs:
            csv_file.write(
                ",".join(req[key] if key in req else "" for key in attributes)
            )
            csv_file.write("\n")


def export_to_excel(
    outputpath: str, attributes: List[str], reqs: Iterable[Dict[str, str]]
) -> None:
    """Exports the requirements to an XSLX Excel file"""
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(attributes)
    for req in reqs:
        worksheet.append([req[key] if key in req else "" for key in attributes])
    workbook.save(outputpath)
    workbook.close()


def create_arg_parser() -> argparse.ArgumentParser:
    """
    Creates a command line argument parser.
    The return value has variables named reqdoc and outputpath.
    """
    parser = argparse.ArgumentParser(
        description="Get requirements from an asciidoc file"
    )
    parser.add_argument("reqdoc", help="File to parse")
    parser.add_argument("outputpath", help="Path for the output file")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        dest="recursive",
        help="Parse specifications recursively and output all requirements",
    )
    return parser


def main() -> None:
    """main - main function"""

    # Parse and validate arguments:
    args = create_arg_parser().parse_args()
    extension = os.path.splitext(args.outputpath)[1]
    if extension not in [".cvs", ".xlsx"]:
        sys.exit(
            f"Supported output formats are CVS and XLSX, but {extension} was specified"
        )

    # Parse the requirements and select the data for export:
    project = read_and_parse_project(args.reqdoc)
    reqs = (
        project.requirements.values()
        if args.recursive
        else project.root_document.reqs.values()
    )
    attributes = project.root_document.attribute_names

    # Export to the correct format:
    if extension == ".cvs":
        export_to_csv(args.outputpath, attributes, reqs)
    elif extension == ".xlsx":
        export_to_excel(args.outputpath, attributes, reqs)


if __name__ == "__main__":
    main()
