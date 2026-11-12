#!/usr/bin/env python3
"""Validate the fast, domain-independent HOI4 scripting mistake checks."""

import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import disk_cache
from linting.check_common_mistakes import (
    _files_need_global_refs,
    _init_worker,
    _scan_global_refs,
    check_file,
)
from shared_utils import get_root_dir
from validator_common import BaseValidator, Severity, run_validator_main

# What check_file reads besides the file it checks, under get_root_dir().
_SHARED_INPUTS = (
    "events",
    "common/buildings",
    "common/decisions",
    "common/idea_tags",
    "common/modifiers",
    "common/opinion_modifiers",
    "common/script_enums.txt",
    "common/units/equipment",
)

_W_MOD_PATH = ""
_W_DIGEST = ""


def _shared_digest(focuses, decisions, flags) -> str:
    """Digest of every input a file's findings can depend on besides the file."""
    digest = hashlib.sha256(
        repr((sorted(focuses), sorted(decisions), sorted(flags))).encode("utf-8")
    )
    root = get_root_dir()
    for entry in _SHARED_INPUTS:
        top = os.path.join(root, entry)
        paths = [top] if os.path.isfile(top) else []
        for dirpath, _dirnames, filenames in os.walk(top):
            paths.extend(os.path.join(dirpath, name) for name in filenames)
        for path in sorted(paths):
            digest.update(os.path.relpath(path, root).encode("utf-8") + b"\0")
            try:
                with open(path, "rb") as handle:
                    digest.update(handle.read())
            except OSError:
                digest.update(b"\1")
    return digest.hexdigest()


def _init_cached_worker(focuses, decisions, flags, mod_path, digest):
    global _W_MOD_PATH, _W_DIGEST
    _init_worker(focuses, decisions, flags)
    _W_MOD_PATH = mod_path
    _W_DIGEST = digest


def _check_file_cached(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError:
        return check_file(filepath)
    return disk_cache.per_file_cached_by_content(
        _W_MOD_PATH,
        "common_mistakes",
        filepath,
        f"{text}\x00{_W_DIGEST}",
        lambda: check_file(filepath),
    )


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
        errors, shadowed, warnings = [], [], []
        digest = _shared_digest(focuses, decisions, flags)
        for file_errors, file_shadowed, file_warnings in self._pool_map_init(
            _check_file_cached,
            files,
            initializer=_init_cached_worker,
            initargs=(focuses, decisions, flags, self.mod_path, digest),
            chunksize=20,
        ):
            for found, results in (
                (file_errors, errors),
                (file_shadowed, shadowed),
                (file_warnings, warnings),
            ):
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
        self._report(
            warnings,
            "No idea logs beside tooltips only",
            "Idea logs that are not needed:",
            severity=Severity.WARNING,
            category="unneeded-idea-log",
        )


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate common Millennium Dawn HOI4 scripting mistakes"
    )
