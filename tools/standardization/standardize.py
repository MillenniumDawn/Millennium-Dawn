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
from shared_utils import add_standard_file_arguments
from standardize_decisions import DecisionStandardizer
from standardize_events import EventStandardizer
from standardize_focus_tree import add_check_naming_argument, standardize_focus_tree
from standardize_history import HistoryStandardizer
from standardize_ideas import IdeaStandardizer
from standardize_localisation import LocalisationStandardizer, _detect_mod_root
from standardize_mio import MIOStandardizer

_SUBCOMMANDS = (
    ("focus", "Standardize focus tree files", "Input focus tree file"),
    ("event", "Standardize event files", "Input event file"),
    ("decision", "Standardize decision files", "Input decision file"),
    ("idea", "Standardize idea files", "Input idea file"),
    (
        "mio",
        "Standardize military industrial organization files",
        "Input MIO file",
    ),
    (
        "history",
        "Standardize history/countries files (dated blocks)",
        "Input history file",
    ),
    (
        "localisation",
        "Standardize localisation files by content category",
        "Input .yml localisation file",
    ),
)

_RUN_STANDARDIZERS = {
    "event": (
        EventStandardizer,
        "Standardize HOI4 event files according to Millennium Dawn coding standards",
    ),
    "decision": (
        DecisionStandardizer,
        "Standardize HOI4 decision files according to Millennium Dawn coding standards",
    ),
    "idea": (
        IdeaStandardizer,
        "Standardize HOI4 idea files according to Millennium Dawn coding standards",
    ),
    "mio": (
        MIOStandardizer,
        "Standardize HOI4 military industrial organization files according to Millennium Dawn coding standards",
    ),
    "history": (
        HistoryStandardizer,
        "Standardize HOI4 history/countries files according to Millennium Dawn coding standards",
    ),
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="Millennium Dawn HOI4 File Standardizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 standardize.py focus input.txt -o output.txt
  python3 standardize.py event input.txt --backup --verbose
  python3 standardize.py decision input.txt
  python3 standardize.py idea input.txt -v
  python3 standardize.py mio input.txt
  python3 standardize.py history "history/countries/CHI - China.txt"
  python3 standardize.py localisation input.yml --mod-root /path/to/mod
        """,
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Type of file to standardize"
    )
    for command, help_text, input_help in _SUBCOMMANDS:
        subparser = subparsers.add_parser(command, help=help_text)
        add_standard_file_arguments(subparser, input_help=input_help)
        if command == "focus":
            add_check_naming_argument(subparser)
        elif command == "localisation":
            subparser.add_argument(
                "--mod-root", help="Path to mod root (auto-detected if omitted)"
            )

    return parser


def _forward_common_argv(args):
    sub_argv = [args.input_file]
    if args.output:
        sub_argv += ["--output", args.output]
    if args.backup:
        sub_argv += ["--backup"]
    if args.verbose:
        sub_argv += ["--verbose"]
    return sub_argv


def main():
    """Main entry point for the unified standardizer"""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' does not exist", file=sys.stderr)
        sys.exit(1)

    sub_argv = _forward_common_argv(args)

    if args.command == "focus":
        output_file = args.output if args.output else args.input_file
        if args.backup:
            from shared_utils import create_backup

            if not create_backup(args.input_file):
                sys.exit(1)
        if not standardize_focus_tree(
            args.input_file, output_file, args.verbose, args.check_naming
        ):
            sys.exit(1)
    elif args.command == "localisation":
        input_path = Path(args.input_file)
        output_path = Path(args.output) if args.output else input_path

        if args.mod_root:
            mod_root = Path(args.mod_root)
        else:
            mod_root = _detect_mod_root(input_path)
            if not mod_root:
                print(
                    "Error: could not detect mod root. Use --mod-root.",
                    file=sys.stderr,
                )
                sys.exit(1)

        if args.backup:
            from shared_utils import create_backup

            if not create_backup(str(input_path)):
                sys.exit(1)

        standardizer = LocalisationStandardizer(mod_root, verbose=args.verbose)
        if not standardizer.standardize_file(input_path, output_path):
            sys.exit(1)
    elif args.command in _RUN_STANDARDIZERS:
        standardizer_class, description = _RUN_STANDARDIZERS[args.command]
        run_standardizer(standardizer_class, description, argv=sub_argv)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
