#!/usr/bin/env python3
# Flag files the project formatter would rewrite. The standardizers in
# tools/standardization/ define MD's canonical layout for the paths in
# standardize_api.ROUTES, but nothing enforces it: the md-standardize hook is
# disabled and most of the repo predates the current rules. Rather than restate
# those rules, this runs the owning standardizer in memory and compares its
# output to the file on disk, so the check can never drift from the formatter.
#
# Warning-only by design, and scoped to changed files: the full-repo backlog is
# in the hundreds, so gating on it would block every PR that touches a legacy
# file. Pass --all for the backlog sweep.
import os
import sys
from itertools import zip_longest
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "standardization"))

from standardize_api import (
    ROUTES,
    focus_content_changes,
    kind_for_path,
    standardize_text,
)
from validator_common import BaseValidator, Issue, Severity, run_validator_main


def _scan_file(args) -> Optional[Tuple[str, str, str, int]]:
    """Return kind, path, failure, and first changed line without writing the file."""
    filepath, mod_path = args
    rel = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    kind = kind_for_path(rel)
    if kind is None:
        return None
    try:
        with open(filepath, "r", encoding="utf-8", newline="") as handle:
            current = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        return (kind, rel, f"could not read the file: {exc}", 0)
    try:
        standardized = standardize_text(kind, current, mod_root=mod_path)
        if standardized is None or standardized == current:
            return None
        second_pass = standardize_text(kind, standardized, mod_root=mod_path)
        if second_pass is not None and second_pass != standardized:
            return (kind, rel, "the rewrite is not idempotent", 0)
        if kind == "focus":
            changes = focus_content_changes(current, standardized)
            if changes:
                details = "; ".join(message for _, message in changes)
                return (kind, rel, f"unsafe rewrite: {details}", changes[0][0])
    except Exception as exc:  # pylint: disable=broad-except
        # A standardizer raising means the file cannot be checked at all, and
        # running the formatter on it would leave it half-rewritten.
        return (kind, rel, f"{type(exc).__name__}: {exc}", 0)
    first_change = next(
        line
        for line, (before, after) in enumerate(
            zip_longest(
                current.splitlines(keepends=True),
                standardized.splitlines(keepends=True),
            ),
            start=1,
        )
        if before != after
    )
    return (kind, rel, "", first_change)


class Validator(BaseValidator):
    TITLE = "STANDARDIZATION VALIDATION"

    def __init__(self, mod_path: str, **kwargs):
        self.scan_all = kwargs.pop("scan_all", False)
        self.kind = kwargs.pop("kind", None)
        super().__init__(mod_path, **kwargs)
        if self.scan_all:
            self.staged_only = False

    def validate_standardization(self):
        self._log_section("Checking files against the project standardizers...")

        patterns = [
            f"{prefix}**/*.txt"
            for prefix, kind in ROUTES
            if self.kind is None or kind == self.kind
        ]
        files = self._collect_files(patterns)
        self.log(f"  Checking {len(files)} files...")
        scanned = self._pool_map(
            _scan_file, [(f, self.mod_path) for f in files], chunksize=30
        )

        results: List[Issue] = []
        for entry in scanned:
            if entry is None:
                continue
            kind, rel, error, line = entry
            if error:
                results.append(
                    Issue(
                        severity=Severity.ERROR,
                        category="standardizer-error",
                        message=f"the {kind} standardizer cannot process this file: {error}",
                        file=rel,
                        line=line,
                    )
                )
                continue
            results.append(
                Issue(
                    severity=Severity.WARNING,
                    category="not-standardized",
                    message="not standardized - run: python3 "
                    f'tools/standardization/standardize.py {kind} "{rel}"',
                    file=rel,
                    line=line,
                )
            )

        failed = sum(bool(entry[2]) for entry in scanned if entry is not None)
        drifted = len(results) - failed
        self.log(
            f"Files checked: {len(files)}; unchanged: {len(files) - len(results)}; "
            f"drifted: {drifted}; failed: {failed}",
            "always",
        )
        self._report(
            results,
            "All checked files match the project standardizers",
            "Files that the project standardizers would rewrite",
        )

    def run_validations(self):
        self.validate_standardization()


def _add_extra_args(parser):
    parser.add_argument(
        "--kind",
        choices=sorted({kind for _, kind in ROUTES}),
        help="Only check files owned by this standardizer",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="scan_all",
        help="Scan every standardizable file, not just the changed ones",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate Millennium Dawn files against the project standardizers",
        extra_args_fn=_add_extra_args,
    )
