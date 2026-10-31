#!/usr/bin/env python3
"""Validate the fast, domain-independent HOI4 scripting mistake checks."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from linting.check_common_mistakes import (
    _files_need_global_refs,
    _init_worker,
    _scan_global_refs,
    check_file,
)
from validator_common import BaseValidator, Severity, run_validator_main


class Validator(BaseValidator):
    TITLE = "COMMON SCRIPTING MISTAKE VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        files = self._collect_files(
            [
                "common/**/*.txt",
                "events/**/*.txt",
                "history/**/*.txt",
                "music/**/*.txt",
            ]
        )
        files = [
            path
            for path in files
            if not any(
                excluded in path.replace("\\", "/")
                for excluded in ("Changelog.txt", "AUTHORS.txt", "/descriptions")
            )
        ]
        if not files:
            self._report(
                [],
                "No common scripting mistakes found",
                "Common scripting mistakes:",
                severity=Severity.ERROR,
                category="common-mistakes",
            )
            return
        if self.staged_only and not _files_need_global_refs(files):
            focuses, decisions, flags = set(), set(), set()
        else:
            focuses, decisions, flags = _scan_global_refs(self.mod_path)
        errors, shadowed = [], []
        for file_errors, file_shadowed in self._pool_map_init(
            check_file,
            files,
            initializer=_init_worker,
            initargs=(focuses, decisions, flags),
            chunksize=20,
        ):
            for found, results in ((file_errors, errors), (file_shadowed, shadowed)):
                results.extend(
                    (message, os.path.relpath(filepath, self.mod_path), line)
                    for filepath, line, message in found
                )
        self._report(
            errors,
            "No common scripting mistakes found",
            "Common scripting mistakes:",
            severity=Severity.ERROR,
            category="common-mistakes",
        )
        self._report(
            shadowed,
            "No shadowed else_if branches found",
            "Shadowed else_if branches:",
            severity=Severity.ERROR,
            category="shadowed-branch",
        )


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate common Millennium Dawn HOI4 scripting mistakes"
    )
