# AsciiReqs - Requirements Management using AsciiDoc markdown and git

## What it is

Requirement Management software can be complicated and inconvenient to use.
Support for collaboration and change management can be cumbersome and poor.
What if we could instead store our requirements in git and use that for versioning and use pull requests for review and management of changes?

This project is a (simple) parser for AsciiDoc files written in Python that will identify requirements in AsciiDoc files, and build a requirements project model from this.
It uses this to do reporting and data export, and will also post process the AsciiDoc files to insert cross-links and report data. This can then be turned into HTML or PDF by tools like AsciiDoctor.

The parser supports requirement document hierarchies, and can find and report inconsistencies in requirement cross-links between documents.

This allows complicated sets of product requirements to be managed in AsciiDoc.

AsciiReqs is to some degree inspired by Sphinx-Needs and Doorstop.

## Status

This is a prototype that I wrote out of frustration with an ancient (but common) Requirement Management System.
I also wanted to freshen up my Python skills.
Python is fun, so it ended up with more features than I had originally planned.
It must still be considered a prototype, but it is in a workable state and the current functionality is at a level where it can be quite useful.

## More information

The full Readme is written in AsciiDoc and can be found here:
[Readme.adoc](https://github.com/hpenne/asciireqs/blob/master/README.adoc)