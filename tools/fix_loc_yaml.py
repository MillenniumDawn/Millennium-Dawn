#!/usr/bin/env python3
"""
HOI4 Localisation YAML Fixer

Auto-fixes common YAML issues in HOI4 localisation files that cause
check-yaml to fail. Runs as a pre-commit hook with --fix to auto-correct,
or without --fix to report errors and exit non-zero.

Fixes applied:
  1. Unescaped double quotes inside quoted values
  2. Missing space after colon (key:"val" -> key: "val")
  3. Version-number keys (key:0 "val" -> key: "val")
  4. Tab characters replaced with spaces (YAML disallows tabs)
  5. Curly/smart quotes replaced with escaped straight quotes

Usage:
    python fix_loc_yaml.py [--fix] [files...]
"""

import argparse
import codecs
import re
import sys
from pathlib import Path

# Curly quote pairs to normalize
SMART_QUOTES = {
    "\u201c": '"',  # left double curly quote
    "\u201d": '"',  # right double curly quote
    "\u2018": "'",  # left single curly quote
    "\u2019": "'",  # right single curly quote
}


def check_line(line: str, line_num: int) -> list:
    """Check a single line for all fixable issues.

    Returns list of (line_num, issue_type, description) tuples.
    """
    problems = []
    stripped = line.strip()

    # Tab characters — check ALL lines including comments
    if "\t" in line:
        problems.append((line_num, "tab", "tab character found"))

    # Smart/curly quotes — check ALL lines including comments
    for char in SMART_QUOTES:
        if char in line:
            problems.append(
                (line_num, "smart_quote", f"smart quote {repr(char)} found")
            )
            break  # one report per line is enough

    if not stripped or stripped.startswith("#"):
        return problems

    # key:0 "value" format (version numbers)
    if re.match(r'^\s*\S+:\d+\s+"', line):
        problems.append((line_num, "version_key", "version-number key format"))

    # key:"value" (missing space after colon)
    if re.match(r'^\s*\S+:"', line):
        problems.append((line_num, "colon_space", "missing space after colon"))

    # Inconsistent indentation (2+ spaces instead of 1)
    indent_match = re.match(r"^( +)\S", line)
    if indent_match and len(indent_match.group(1)) > 1:
        problems.append(
            (line_num, "indent", f"{len(indent_match.group(1))} spaces instead of 1")
        )

    # Missing closing quote — value starts with " but line has odd number of
    # unescaped quotes (meaning one is unclosed)
    key_match = re.match(r'^\s*\S+:[\d\s]*"', line)
    if key_match:
        # Count unescaped quotes after the colon
        after_colon = line[line.index(":") + 1 :]
        quote_count = 0
        j = 0
        while j < len(after_colon):
            if (
                after_colon[j] == "\\"
                and j + 1 < len(after_colon)
                and after_colon[j + 1] == '"'
            ):
                j += 2
                continue
            if after_colon[j] == '"':
                quote_count += 1
            j += 1
        if quote_count % 2 != 0:
            problems.append(
                (line_num, "missing_close_quote", "value has no closing quote")
            )

    # Unescaped quotes inside value
    match = re.match(r'^(\s*\S+:\s*)"', line)
    if not match:
        # Also handle key:0 "value" and key:"value" patterns for quote checking
        match = re.match(r'^(\s*\S+:\d*\s*)"', line)
    if match:
        prefix_end = match.end() - 1
        rest = line[prefix_end:]
        if len(rest) >= 2:
            last_quote = rest.rfind('"')
            if last_quote > 0:
                inner = rest[1:last_quote]
                i = 0
                while i < len(inner):
                    if inner[i] == "\\" and i + 1 < len(inner) and inner[i + 1] == '"':
                        i += 2
                        continue
                    if inner[i] == '"':
                        context_start = max(0, i - 20)
                        context_end = min(len(inner), i + 20)
                        context = inner[context_start:context_end]
                        problems.append(
                            (line_num, "unescaped_quote", f"...{context}...")
                        )
                        # Only report once per line for unescaped quotes
                        break
                    i += 1

    return problems


def fix_line(line: str) -> str:
    """Apply all fixes to a single line."""
    stripped = line.strip()

    # Fix tab characters -> spaces (ALL lines including comments)
    if "\t" in line:
        line = line.replace("\t", " ")

    # Fix smart/curly quotes (ALL lines including comments)
    for char, replacement in SMART_QUOTES.items():
        if char in line:
            line = line.replace(char, replacement)

    if not stripped or stripped.startswith("#"):
        return line

    # Fix indentation (2+ leading spaces -> 1 space for loc keys)
    indent_match = re.match(r"^( +)\S", line)
    if indent_match and len(indent_match.group(1)) > 1:
        line = " " + line.lstrip()

    # Fix key:0 "value" -> key: "value" (remove version number)
    m = re.match(r'^(\s*\S+):\d+(\s+")', line)
    if m:
        line = m.group(1) + ":" + m.group(2)

    # Fix key:"value" -> key: "value" (add space after colon)
    m = re.match(r'^(\s*\S+):"', line)
    if m:
        line = m.group(1) + ': "' + line[m.end() :]

    # Fix unescaped quotes inside value
    match = re.match(r'^(\s*\S+:\s*)"', line)
    if match:
        prefix = line[: match.end()]
        rest = line[match.end() :]
        last_quote = rest.rfind('"')
        if last_quote >= 0:
            inner = rest[:last_quote]
            suffix = rest[last_quote:]

            fixed_inner = []
            i = 0
            while i < len(inner):
                if inner[i] == "\\" and i + 1 < len(inner) and inner[i + 1] == '"':
                    fixed_inner.append('\\"')
                    i += 2
                    continue
                if inner[i] == '"':
                    fixed_inner.append('\\"')
                else:
                    fixed_inner.append(inner[i])
                i += 1

            line = prefix + "".join(fixed_inner) + suffix

    return line


def process_file(file_path: Path, fix_mode: bool) -> tuple:
    """Process a single file. Returns (problems_found, problems_fixed)."""
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
    except OSError as e:
        print(f"  Error reading {file_path}: {e}", file=sys.stderr)
        return (0, 0)

    has_bom = raw.startswith(codecs.BOM_UTF8)
    content = raw.decode("utf-8-sig")
    lines = content.split("\n")

    all_problems = []
    for i, line in enumerate(lines):
        problems = check_line(line, i + 1)
        all_problems.extend(problems)

    if not all_problems:
        return (0, 0)

    if not fix_mode:
        for line_num, issue_type, desc in all_problems:
            print(f"  {file_path}:{line_num}: [{issue_type}] {desc}")
        return (len(all_problems), 0)

    # Fix mode
    fixed_lines = [fix_line(line) for line in lines]
    fixed_content = "\n".join(fixed_lines)

    write_bytes = (codecs.BOM_UTF8 if has_bom else b"") + fixed_content.encode("utf-8")
    with open(file_path, "wb") as f:
        f.write(write_bytes)

    # Summarize by issue type
    counts = {}
    for _, issue_type, _ in all_problems:
        counts[issue_type] = counts.get(issue_type, 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    print(f"  Fixed {file_path}: {summary}")
    return (len(all_problems), len(all_problems))


def main():
    parser = argparse.ArgumentParser(
        description="Fix common YAML issues in HOI4 localisation files"
    )
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues in place")
    parser.add_argument(
        "files", nargs="*", help="Files to check (default: all English loc files)"
    )
    args = parser.parse_args()

    if args.files:
        files = [Path(f) for f in args.files]
    else:
        files = sorted(Path("localisation/english").glob("*_l_english.yml"))

    total_problems = 0
    total_fixed = 0

    for f in files:
        if not f.exists():
            continue
        problems, fixed = process_file(f, args.fix)
        total_problems += problems
        total_fixed += fixed

    if total_problems > 0 and not args.fix:
        print(f"\nFound {total_problems} issue(s). Run with --fix to auto-fix.")
        sys.exit(1)
    elif total_fixed > 0:
        print(f"\nFixed {total_fixed} issue(s).")


if __name__ == "__main__":
    main()
