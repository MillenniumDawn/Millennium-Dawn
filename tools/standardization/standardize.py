#!/usr/bin/env python3

"""
Millennium Dawn Standardizer
Unified command-line interface for all HOI4 file standardizers
"""

import argparse
import os
import sys
from pathlib import Path

# Add the tools directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from standardize_decisions import main as decision_main
from standardize_events import main as event_main
from standardize_focus_tree import main as focus_main
from standardize_ideas import main as idea_main


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

    # Focus tree standardizer
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

    # Event standardizer
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

    # Decision standardizer
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

    # Idea standardizer
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

    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' does not exist", file=sys.stderr)
        sys.exit(1)

    # Route to appropriate standardizer
    if args.command == "focus":
        focus_main()
    elif args.command == "event":
        event_main()
    elif args.command == "decision":
        decision_main()
    elif args.command == "idea":
        idea_main()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
