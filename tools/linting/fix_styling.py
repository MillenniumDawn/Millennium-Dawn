#!/usr/bin/env python3
"""Auto-fix spacing warnings reported by validate_style.py."""

import os
import re
import subprocess
import sys
import time
from functools import partial

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "validation"))
from shared_utils import (
    Timer,
    atomic_write_text,
    clean_filepath,
    collect_files_by_mode,
    create_linting_parser,
    get_root_dir,
    normalize_spacing,
    print_timing_summary,
    read_text_strict,
    run_with_pool,
)
from validate_style import line_spacing_warnings, split_code_and_comment

__version__ = 3.0

_RE_EQ_SEP = re.compile(r"={3,}")

FIXABLE_LINE_WARNINGS = frozenset(
    {
        "Missing space before or after open brace",
        "Missing space before or after close brace",
        "Two spaces before or after '='",
        "Missing space before or after '='",
    }
)


def fix_line(line, fix_indent=False, collapse_comment_alignment=False):
    """Fix one line and return its replacement and fix count."""
    newline = line[len(line.rstrip("\r\n")) :]
    body = line[: len(line) - len(newline)]
    fixes = 0

    if fix_indent:
        stripped = body.lstrip(" \t")
        leading = body[: len(body) - len(stripped)]
        if " " in leading:
            expanded = leading.replace("\t", "    ")
            num_spaces = len(expanded)
            tabs = num_spaces // 4
            remainder = num_spaces % 4
            new_body = "\t" * tabs + " " * remainder + stripped
            if new_body != body:
                fixes += 1
            body = new_body

    code, comment = split_code_and_comment(body)
    warnings = line_spacing_warnings(body)
    should_fix_spacing = any(warning in FIXABLE_LINE_WARNINGS for warning in warnings)
    if should_fix_spacing:
        gap = code[len(code.rstrip()) :]
        fixed_code = normalize_spacing(code)
        if fixed_code != code.rstrip():
            fixes += 1
        code = fixed_code
    else:
        gap = ""

    if collapse_comment_alignment and comment:
        if code.strip():
            had_alignment = not should_fix_spacing and bool(
                gap or code.rstrip() != code
            )
            code = code.rstrip()
            gap = ""
            comment = " " + comment.strip()
            fixes += int(had_alignment)
        comment, count = _collapse_comment_separators(comment)
        fixes += count
    return code + gap + comment + newline, fixes


def _collapse_comment_separators(comment):
    collapsed = _RE_EQ_SEP.sub(lambda match: "-" * len(match.group()), comment)
    return collapsed, int(collapsed != comment)


class StagedDiffError(RuntimeError):
    pass


def _discovery_env():
    """Environment for repo discovery, with any inherited repo binding dropped.

    Git exports an absolute `GIT_DIR` to its hooks, and in a worktree that makes
    `rev-parse --show-toplevel` answer with the directory it was run from rather
    than the repo root, collapsing every path to its basename.
    """
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    return env


def _repo_path(filepath):
    absolute = os.path.abspath(filepath)
    parent = absolute if os.path.isdir(absolute) else os.path.dirname(absolute)
    discovery_env = os.environ.copy()
    discovery_env.pop("GIT_DIR", None)
    discovery_env.pop("GIT_WORK_TREE", None)
    try:
        result = subprocess.run(
            ["git", "-C", parent, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
            env=_discovery_env(),
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise StagedDiffError(
            f"cannot find Git repository for {filepath}: {error}"
        ) from error
    if result.returncode:
        detail = result.stderr.strip() or "not a Git worktree"
        raise StagedDiffError(f"cannot find Git repository for {filepath}: {detail}")
    root = os.path.realpath(result.stdout.strip())
    try:
        relative = os.path.relpath(os.path.realpath(absolute), root)
    except ValueError as error:
        raise StagedDiffError(f"path is outside Git repository: {filepath}") from error
    if relative == os.pardir or relative.startswith(os.pardir + os.sep):
        raise StagedDiffError(f"path is outside Git repository: {filepath}")
    return root, relative.replace(os.sep, "/")


def staged_changed_lines(filepath):
    """Return added and changed line numbers from the staged diff."""
    root, relative = _repo_path(filepath)
    try:
        result = subprocess.run(
            ["git", "-C", root, "diff", "--cached", "--unified=0", "--", relative],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise StagedDiffError(
            f"cannot read staged diff for {filepath}: {error}"
        ) from error
    if result.returncode:
        detail = result.stderr.strip() or "git diff failed"
        raise StagedDiffError(f"cannot read staged diff for {filepath}: {detail}")
    lines = set()
    for match in re.finditer(
        r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", result.stdout, re.M
    ):
        start = int(match.group(1))
        count = int(match.group(2) or "1")
        lines.update(range(start, start + count))
    return lines


def _worktree_matches_index(filepath):
    root, relative = _repo_path(filepath)
    try:
        result = subprocess.run(
            ["git", "-C", root, "show", f":{relative}"],
            capture_output=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise StagedDiffError(
            f"cannot read staged file for {filepath}: {error}"
        ) from error
    if result.returncode:
        detail = result.stderr.decode(errors="replace").strip() or "path is not staged"
        raise StagedDiffError(f"cannot read staged file for {filepath}: {detail}")
    try:
        with open(filepath, "rb") as handle:
            worktree = handle.read()
    except OSError as error:
        raise StagedDiffError(
            f"cannot read worktree file for {filepath}: {error}"
        ) from error
    if worktree != result.stdout:
        raise StagedDiffError(
            f"worktree differs from staged index for {filepath}; "
            "run this fixer through pre-commit or stage the file first"
        )


def _fix_staged_lines(filepath, **kwargs):
    try:
        _worktree_matches_index(filepath)
        only_lines = staged_changed_lines(filepath)
    except StagedDiffError as error:
        return filepath, 0, [f"  Error: {error}"]
    return fix_file(filepath, only_lines=only_lines, **kwargs)


def fix_file(
    filepath,
    only_lines=None,
    fix_indent=False,
    collapse_comment_alignment=False,
    dry_run=False,
):
    """Fix one file, optionally restricted to *only_lines*."""
    try:
        content = read_text_strict(filepath)

        lines = content.split("\n")
        fixed_lines = []
        total_fixes = 0
        unfixable = []

        for line_num, line in enumerate(lines, 1):
            if only_lines is not None and line_num not in only_lines:
                fixed_lines.append(line)
            else:
                fixed, fixes = fix_line(
                    line,
                    fix_indent=fix_indent,
                    collapse_comment_alignment=collapse_comment_alignment,
                )
                total_fixes += fixes
                fixed_lines.append(fixed)

            if "Odd number of quotation marks" in line_spacing_warnings(line):
                unfixable.append(
                    f"  {clean_filepath(filepath)}:{line_num}: Possible missing quotation mark"
                )

        # Scoped passes must not normalize the untouched tail.
        if only_lines is None:
            while fixed_lines and fixed_lines[-1] == "":
                fixed_lines.pop()
            fixed_lines.append("")

        new_content = "\n".join(fixed_lines)

        if not dry_run and new_content != content:
            atomic_write_text(filepath, new_content)

        return (filepath, total_fixes, unfixable)

    except Exception as e:
        return (filepath, 0, [f"  Error processing {filepath}: {e}"])


def fix_file_dry_run(filepath):
    """Run fix_file without writing."""
    return fix_file(filepath, dry_run=True)


def main():
    def _extra(parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be fixed without writing changes",
        )
        parser.add_argument(
            "--changed-lines",
            action="store_true",
            help="With --mode staged: fix only the lines the staged diff touches",
        )
        parser.add_argument(
            "--fix-indent",
            action="store_true",
            help="Legacy bulk cleanup: convert leading spaces to tabs",
        )
        parser.add_argument(
            "--collapse-comment-alignment",
            action="store_true",
            help="Legacy bulk cleanup: collapse aligned whitespace before inline comments",
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

    kwargs = dict(
        fix_indent=args.fix_indent,
        collapse_comment_alignment=args.collapse_comment_alignment,
        dry_run=args.dry_run,
    )
    if args.changed_lines:
        process_fn = partial(_fix_staged_lines, **kwargs)
    else:
        process_fn = partial(fix_file, **kwargs)

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
    print("\n------")
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

    return (
        1 if any(issue.lstrip().startswith("Error") for issue in all_unfixable) else 0
    )


if __name__ == "__main__":
    sys.exit(main())
