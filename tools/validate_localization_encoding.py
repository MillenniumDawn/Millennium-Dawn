#!/usr/bin/env python3
"""
HOI4 Localization Encoding Validator

This script validates and fixes UTF-8 BOM encoding for Hearts of Iron IV localization files.
HOI4 requires localization YAML files to be encoded as UTF-8 with BOM.

Usage:
    python validate_localization_encoding.py [--fix] [files...]

Arguments:
    --fix: Automatically add UTF-8 BOM to files that are missing it
    files: List of files to check (if not provided, checks all English localization files)
"""

import argparse
import codecs
import sys
from pathlib import Path
from typing import List, Tuple


class LocalizationValidator:
    """Validates and fixes UTF-8 BOM encoding for HOI4 localization files."""

    def __init__(self, fix_mode: bool = False):
        self.fix_mode = fix_mode
        self.errors = []
        self.fixed = []
        self.valid = []

    def validate_file(self, file_path: Path) -> bool:
        """
        Validate a single localization file.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid or was fixed, False if errors occurred
        """
        try:
            # Read file in binary mode to check BOM
            with open(file_path, "rb") as f:
                content = f.read()

            has_bom = content.startswith(codecs.BOM_UTF8)

            if not has_bom:
                if self.fix_mode:
                    return self._fix_file(file_path, content)
                else:
                    self.errors.append(
                        f"❌ {file_path}: Missing UTF-8 BOM (required for HOI4 localization)"
                    )
                    return False

            # Verify the file is valid UTF-8
            try:
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    f.read()
                self.valid.append(f"✅ {file_path}: Correct UTF-8 with BOM encoding")
                return True

            except UnicodeDecodeError as e:
                self.errors.append(f"❌ {file_path}: Invalid UTF-8 encoding: {e}")
                return False

        except Exception as e:
            self.errors.append(f"❌ {file_path}: Unexpected error: {e}")
            return False

    def _fix_file(self, file_path: Path, content: bytes) -> bool:
        """
        Fix a file by adding UTF-8 BOM.

        Args:
            file_path: Path to the file to fix
            content: Original file content

        Returns:
            True if file was fixed successfully, False otherwise
        """
        try:
            # Verify content is valid UTF-8 before fixing
            content.decode("utf-8")

            # Add BOM and write back
            with open(file_path, "wb") as f:
                f.write(codecs.BOM_UTF8 + content)

            self.fixed.append(f"🔧 {file_path}: Added UTF-8 BOM")
            return True

        except UnicodeDecodeError as e:
            self.errors.append(f"❌ {file_path}: Cannot fix - invalid UTF-8: {e}")
            return False
        except Exception as e:
            self.errors.append(f"❌ {file_path}: Error while fixing: {e}")
            return False

    def validate_files(self, files: List[Path]) -> bool:
        """
        Validate multiple files.

        Args:
            files: List of file paths to validate

        Returns:
            True if all files are valid or were fixed, False if any errors occurred
        """
        all_valid = True

        for file_path in files:
            if not file_path.exists():
                self.errors.append(f"❌ {file_path}: File not found")
                all_valid = False
                continue

            if not self.validate_file(file_path):
                all_valid = False

        return all_valid

    def print_summary(self):
        """Print a summary of validation results."""
        if self.valid:
            for msg in self.valid:
                print(msg)

        if self.fixed:
            for msg in self.fixed:
                print(msg)

        if self.errors:
            for msg in self.errors:
                print(msg, file=sys.stderr)

        # Print summary counts
        total = len(self.valid) + len(self.fixed) + len(self.errors)
        if total > 1:
            print(
                f"\nSummary: {len(self.valid)} valid, {len(self.fixed)} fixed, {len(self.errors)} errors"
            )


def find_english_localization_files() -> List[Path]:
    """Find all English localization files in the project."""
    patterns = [
        "localisation/english/*.yml",
        "localisation/*_l_english.yml",  # Alternative naming pattern
        "localisation/english/**/*.yml",  # Nested directories
    ]

    files = []
    project_root = Path.cwd()

    for pattern in patterns:
        files.extend(project_root.glob(pattern))

    return sorted(set(files))


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Validate UTF-8 BOM encoding for HOI4 localization files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_localization_encoding.py
  python validate_localization_encoding.py --fix
  python validate_localization_encoding.py file1.yml file2.yml
  python validate_localization_encoding.py --fix localisation/english/*.yml
        """,
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically add UTF-8 BOM to files that are missing it",
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="Files to validate (default: all English localization files)",
    )

    args = parser.parse_args()

    # Determine which files to check
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        files = find_english_localization_files()
        if not files:
            print("❌ No English localization files found", file=sys.stderr)
            print(
                "Expected patterns: localisation/english/*.yml or localisation/*_l_english.yml",
                file=sys.stderr,
            )
            return 1

    # Validate files
    validator = LocalizationValidator(fix_mode=args.fix)
    success = validator.validate_files(files)
    validator.print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
