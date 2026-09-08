#!/usr/bin/env python3
# Flag files the project formatter would rewrite. The standardizers in
# tools/standardization/ define MD's canonical layout for focus trees, events,
# decisions, ideas and MIOs, but nothing enforces it: the md-standardize hook is
# disabled and most of the repo predates the current rules. Rather than restate
# those rules, this runs the owning standardizer in memory and compares its
# output to the file on disk, so the check can never drift from the formatter.
#
# Warning-only by design, and scoped to changed files: the full-repo backlog is
# in the hundreds, so gating on it would block every PR that touches a legacy
# file. Pass --all for the backlog sweep.
import os
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "standardization"))

from standardize_api import ROUTES, kind_for_path, standardize_text
from validator_common import BaseValidator, Issue, Severity, run_validator_main

_PATTERNS = [f"{prefix}**/*.txt" for prefix, _ in ROUTES]


def _scan_file(args) -> Optional[Tuple[str, str, str]]:
    """Worker: (kind, rel, error) for one file. error is "" when it is only
    unstandardized, and non-empty when the standardizer could not run."""
    filepath, mod_path = args
    rel = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    kind = kind_for_path(rel)
    if kind is None:
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as handle:
            current = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        return (kind, rel, f"could not read the file: {exc}")
    try:
        standardized = standardize_text(kind, current)
    except Exception as exc:  # pylint: disable=broad-except
        # A standardizer raising means the file cannot be checked at all, and
        # running the formatter on it would leave it half-rewritten.
        return (kind, rel, f"{type(exc).__name__}: {exc}")
    if standardized is None or standardized == current:
        return None
    return (kind, rel, "")


class Validator(BaseValidator):
    TITLE = "STANDARDIZATION VALIDATION"

    def __init__(self, mod_path: str, **kwargs):
        self.scan_all = kwargs.pop("scan_all", False)
        super().__init__(mod_path, **kwargs)
        if self.scan_all:
            self.staged_only = False

    def validate_standardization(self):
        self._log_section("Checking files against the project standardizers...")

        files = self._collect_files(_PATTERNS)
        self.log(f"  Checking {len(files)} files...")
        scanned = self._pool_map(
            _scan_file, [(f, self.mod_path) for f in files], chunksize=30
        )

        results: List[Issue] = []
        for entry in scanned:
            if entry is None:
                continue
            kind, rel, error = entry
            if error:
                results.append(
                    Issue(
                        severity=Severity.ERROR,
                        category="standardizer-error",
                        message=f"the {kind} standardizer cannot process this file: {error}",
                        file=rel,
                        line=0,
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
                    line=0,
                )
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
