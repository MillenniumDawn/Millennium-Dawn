#!/usr/bin/env python3

"""
Millennium Dawn Standardizer
Unified command-line interface for all HOI4 file standardizers
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common_utils import run_standardizer
from standardize_decisions import DecisionStandardizer
from standardize_events import EventStandardizer
from standardize_focus_tree import standardize_focus_tree
from standardize_ideas import IdeaStandardizer


def main():
    """Main entry point for the unified standardizer"""
    parser = argparse.ArgumentParser(
        description="Millennium Dawn HOI4 File Standardizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 standardize.py focus input.txt -o output.txt
  python3 standardize.py event input.txt --backup --verbose
  python3 standardize.py decision input.txt
  python3 standardize.py idea input.txt -v
        """,
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Type of file to standardize"
    )

    focus_parser = subparsers.add_parser("focus", help="Standardize focus tree files")
    focus_parser.add_argument("input_file", help="Input focus tree file")
    focus_parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    focus_parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    focus_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    event_parser = subparsers.add_parser("event", help="Standardize event files")
    event_parser.add_argument("input_file", help="Input event file")
    event_parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    event_parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    event_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    decision_parser = subparsers.add_parser(
        "decision", help="Standardize decision files"
    )
    decision_parser.add_argument("input_file", help="Input decision file")
    decision_parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    decision_parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    decision_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    idea_parser = subparsers.add_parser("idea", help="Standardize idea files")
    idea_parser.add_argument("input_file", help="Input idea file")
    idea_parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    idea_parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    idea_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' does not exist", file=sys.stderr)
        sys.exit(1)

    sub_argv = [args.input_file]
    if args.output:
        sub_argv += ["--output", args.output]
    if args.backup:
        sub_argv += ["--backup"]
    if args.verbose:
        sub_argv += ["--verbose"]

    if args.command == "focus":
        output_file = args.output if args.output else args.input_file
        standardize_focus_tree(args.input_file, output_file, args.verbose)
    elif args.command == "event":
        run_standardizer(
            EventStandardizer,
            "Standardize HOI4 event files according to Millennium Dawn coding standards",
            argv=sub_argv,
        )
    elif args.command == "decision":
        run_standardizer(
            DecisionStandardizer,
            "Standardize HOI4 decision files according to Millennium Dawn coding standards",
            argv=sub_argv,
        )
    elif args.command == "idea":
        run_standardizer(
            IdeaStandardizer,
            "Standardize HOI4 idea files according to Millennium Dawn coding standards",
            argv=sub_argv,
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
