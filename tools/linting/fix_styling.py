#!/usr/bin/env python3
"""Auto-fix styling issues detected by check_basic_style.py."""

import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from path_utils import clean_filepath
from shared_utils import (
    Timer,
    collect_files_by_mode,
    create_linting_parser,
    get_root_dir,
    print_timing_summary,
    run_with_pool,
)

__version__ = 2.0

_RE_EQ_SEP = re.compile(r"={3,}")
_RE_MULTI_SP_BEFORE_EQ = re.compile(r"  +=")
_RE_MULTI_SP_AFTER_EQ = re.compile(r"=  +")
_RE_TAB_BEFORE_EQ = re.compile(r"\t+(=)")
_RE_NO_SP_BEFORE_EQ = re.compile(r"([^\s!<>=])=")
_RE_NO_SP_AFTER_EQ = re.compile(r"=([^\s=>{])")
_RE_NO_SP_BEFORE_OPEN = re.compile(r"([^\s])\{")
_RE_NO_SP_AFTER_OPEN = re.compile(r"\{([^\s\n])")
_RE_NO_SP_BEFORE_CLOSE = re.compile(r"([^\s])\}")
_RE_NO_SP_AFTER_CLOSE = re.compile(r"\}([^\s\n}])")
_RE_MULTI_SP_BEFORE_OPEN = re.compile(r"  +\{")
_RE_MULTI_SP_AFTER_OPEN = re.compile(r"\{  +")
_RE_MULTI_SP_BEFORE_CLOSE = re.compile(r"  +\}")
_RE_MULTI_SP_AFTER_CLOSE = re.compile(r"\}  +")
_RE_MULTI_SP = re.compile(r"  +")


def fix_line(line):
    """Fix styling issues in a single line. Returns (fixed_line, fix_count)."""
    original = line
    fixes = 0

    # Step 1: Fix leading indentation (spaces -> tabs) on all lines
    stripped = line.lstrip(" \t")
    leading = line[: len(line) - len(stripped)]
    if " " in leading:
        # Expand existing tabs to 4 spaces, then convert back to tabs
        expanded = leading.replace("\t", "    ")
        num_spaces = len(expanded)
        tabs = num_spaces // 4
        remainder = num_spaces % 4
        new_leading = "\t" * tabs + " " * remainder
        line = new_leading + stripped
        if line != original:
            fixes += 1

    # Step 2: Handle comment-only lines
    stripped_content = line.lstrip("\t ")
    if stripped_content.startswith("#"):
        # Fix === separator lines in comments (validators flag these as = issues)
        if _RE_EQ_SEP.search(line):
            line = _RE_EQ_SEP.sub(lambda m: "-" * len(m.group()), line)
            if line != original:
                fixes += 1
        # Remove trailing whitespace on comment lines
        rstripped = line.rstrip(" \t")
        if rstripped != line.rstrip("\n"):
            line = rstripped + "\n" if original.endswith("\n") else rstripped
            fixes += 1
        return line, fixes

    # Step 3: Split into code and comment parts
    comment_pos = line.find("#")
    if comment_pos > 0:
        code_part = line[:comment_pos]
        comment_part = line[comment_pos:]
        # Fix === in inline comments too
        if _RE_EQ_SEP.search(comment_part):
            comment_part = _RE_EQ_SEP.sub(lambda m: "-" * len(m.group()), comment_part)
            fixes += 1
    else:
        code_part = line
        comment_part = ""

    # Step 4: Fix equal sign spacing in code part
    if "=" in code_part:
        # Fix double+ spaces before =
        new_code = _RE_MULTI_SP_BEFORE_EQ.sub(" =", code_part)
        new_code = _RE_MULTI_SP_AFTER_EQ.sub("= ", new_code)
        new_code = _RE_TAB_BEFORE_EQ.sub(r" \1", new_code)
        new_code = _RE_NO_SP_BEFORE_EQ.sub(r"\1 =", new_code)
        new_code = _RE_NO_SP_AFTER_EQ.sub(r"= \1", new_code)
        if new_code != code_part:
            code_part = new_code
            fixes += 1

    # Step 5: Fix brace spacing in code part
    if "{" in code_part or "}" in code_part:
        new_code = code_part
        # Add space before { if missing (not at line start)
        new_code = _RE_NO_SP_BEFORE_OPEN.sub(r"\1 {", new_code)
        new_code = _RE_NO_SP_AFTER_OPEN.sub(r"{ \1", new_code)
        new_code = _RE_NO_SP_BEFORE_CLOSE.sub(r"\1 }", new_code)
        new_code = _RE_NO_SP_AFTER_CLOSE.sub(r"} \1", new_code)
        # Handle }} -> } } (add space between consecutive closing braces)
        while "}}" in new_code:
            new_code = new_code.replace("}}", "} }")
        # Fix double+ spaces around braces
        new_code = _RE_MULTI_SP_BEFORE_OPEN.sub(" {", new_code)
        new_code = _RE_MULTI_SP_AFTER_OPEN.sub("{ ", new_code)
        new_code = _RE_MULTI_SP_BEFORE_CLOSE.sub(" }", new_code)
        new_code = _RE_MULTI_SP_AFTER_CLOSE.sub("} ", new_code)
        if new_code != code_part:
            code_part = new_code
            fixes += 1

    # Step 6: Collapse multiple spaces to single in code part (not leading indent)
    code_stripped = code_part.lstrip("\t")
    code_indent = code_part[: len(code_part) - len(code_stripped)]
    if "    " in code_stripped:
        new_stripped = _RE_MULTI_SP.sub(" ", code_stripped)
        if new_stripped != code_stripped:
            code_part = code_indent + new_stripped
            fixes += 1

    # Reassemble line
    line = code_part + comment_part

    # Step 7: Remove trailing whitespace (preserve newline)
    if line.endswith("\n"):
        rstripped = line.rstrip(" \t\n") + "\n"
    else:
        rstripped = line.rstrip(" \t")
    if rstripped != line:
        line = rstripped
        fixes += 1

    return line, fixes


def fix_file(filepath):
    """Fix all styling issues in a single file.

    Returns (filepath, fixes_count, unfixable_issues).
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        lines = content.split("\n")
        fixed_lines = []
        total_fixes = 0
        unfixable = []

        for line_num, line in enumerate(lines, 1):
            # Preserve newlines for processing (add back for fix_line)
            fixed, fixes = fix_line(line)
            total_fixes += fixes
            fixed_lines.append(fixed)

            # Report unfixable: odd number of quotes
            if '"' in line and not line.strip().startswith("#"):
                code = line.split("#")[0] if "#" in line else line
                if code.count('"') % 2 == 1:
                    unfixable.append(
                        f"  {clean_filepath(filepath)}:{line_num}: Possible missing quotation mark"
                    )

        # Remove excessive trailing blank lines, ensure single newline at end
        while fixed_lines and fixed_lines[-1] == "":
            fixed_lines.pop()
        fixed_lines.append("")

        new_content = "\n".join(fixed_lines)

        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)

        return (filepath, total_fixes, unfixable)

    except Exception as e:
        return (filepath, 0, [f"  Error processing {filepath}: {e}"])


def fix_file_dry_run(filepath):
    """Check what would be fixed without writing.

    Returns (filepath, fixes_count, unfixable_issues).
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_fixes = 0
        unfixable = []

        for line_num, line in enumerate(lines, 1):
            _, fixes = fix_line(line)
            total_fixes += fixes

            if '"' in line and not line.strip().startswith("#"):
                code = line.split("#")[0] if "#" in line else line
                if code.count('"') % 2 == 1:
                    unfixable.append(
                        f"  {clean_filepath(filepath)}:{line_num}: Possible missing quotation mark"
                    )

        return (filepath, total_fixes, unfixable)

    except Exception as e:
        return (filepath, 0, [f"  Error processing {filepath}: {e}"])


def main():
    def _extra(parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be fixed without writing changes",
        )

    parser = create_linting_parser(
        "Fix styling issues in HOI4 mod files", extra_args_fn=_extra
    )
    args = parser.parse_args()

    timings = []
    start_time = time.time()
    print(f"Fix Styling v{__version__} (Mode: {args.mode}, Dry run: {args.dry_run})")

    with Timer("file collection") as t:
        existing_files = collect_files_by_mode(
            args, get_root_dir(), include_interface=True
        )
    timings.append(("file collection", t.elapsed))

    if not existing_files:
        print("No files to process")
        return 0

    print(f"Processing {len(existing_files)} files...")

    process_fn = fix_file_dry_run if args.dry_run else fix_file
    with Timer("processing") as t:
        results = run_with_pool(process_fn, existing_files, args.workers)
    timings.append(("processing", t.elapsed))

    # Summarize results
    files_fixed = sum(1 for _, fixes, _ in results if fixes > 0)
    total_fixes = sum(fixes for _, fixes, _ in results)
    all_unfixable = []
    for _, _, unfixable in results:
        all_unfixable.extend(unfixable)

    action = "Would fix" if args.dry_run else "Fixed"
    print(f"\n------")
    print(f"Processed {len(existing_files)} files")
    print(f"{action} {total_fixes} issues in {files_fixed} files")

    if all_unfixable:
        print(f"\n{len(all_unfixable)} issues need manual attention:")
        for issue in all_unfixable[:50]:
            print(issue)
        if len(all_unfixable) > 50:
            print(f"  ... and {len(all_unfixable) - 50} more")

    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.1f}s")
    print_timing_summary(timings)

    return 0


if __name__ == "__main__":
    sys.exit(main())
