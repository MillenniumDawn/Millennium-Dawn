#!/usr/bin/env python3
"""Validate the fast, domain-independent HOI4 scripting mistake checks."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from linting.check_common_mistakes import (
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
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
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
        focuses, decisions, flags = _scan_global_refs(self.mod_path)
        results = []
        for file_results in self._pool_map_init(
            check_file,
            files,
            initializer=_init_worker,
            initargs=(focuses, decisions, flags),
            chunksize=20,
        ):
            for filepath, line, message in file_results:
                results.append(
                    (message, os.path.relpath(filepath, self.mod_path), line)
                )
        self._report(
            results,
            "No common scripting mistakes found",
            "Common scripting mistakes:",
            severity=Severity.ERROR,
            category="common-mistakes",
        )


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate common Millennium Dawn HOI4 scripting mistakes"
    )
