#!/usr/bin/env python3
"""Warn when a country uses an unregistered graphical culture."""

import os
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import blank_quoted_strings  # noqa: E402
from validator_common import (  # noqa: E402
    BaseValidator,
    run_validator_main,
    strip_comments,
)

COUNTRY_DIR = "common/countries"
REGISTRY_FILE = "common/graphicalculturetype.txt"
_TOKEN_RE = re.compile(r"[^\s{}=]+|[{}=]")
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9_]+\Z")


def _country_cultures(text: str) -> List[Tuple[str, int]]:
    """Return bare top-level graphical_culture assignments as (value, line)."""
    clean = blank_quoted_strings(strip_comments(text))
    tokens = list(_TOKEN_RE.finditer(clean))
    cultures: List[Tuple[str, int]] = []
    depth = 0
    index = 0

    while index < len(tokens):
        token = tokens[index]
        value = token.group()
        if value == "{":
            depth += 1
            index += 1
            continue
        if value == "}":
            depth = max(0, depth - 1)
            index += 1
            continue

        if (
            depth == 0
            and value == "graphical_culture"
            and index + 2 < len(tokens)
            and tokens[index + 1].group() == "="
        ):
            culture = tokens[index + 2].group()
            if _IDENTIFIER_RE.fullmatch(culture):
                line = clean.count("\n", 0, token.start()) + 1
                cultures.append((culture, line))
                index += 3
                continue
        index += 1

    return cultures


def _registered_cultures(text: str) -> Set[str]:
    """Read bare identifier entries from graphicalculturetype.txt."""
    cultures = set()
    for line in strip_comments(text).splitlines():
        name = line.strip()
        if _IDENTIFIER_RE.fullmatch(name):
            cultures.add(name)
    return cultures


class Validator(BaseValidator):
    TITLE = "GRAPHICAL CULTURE REGISTRATION"
    STAGED_EXTENSIONS = [".txt"]
    STAGED_INCLUDE_MISSING = True

    def run_validations(self):
        if self.staged_only:
            relevant_change = False
            mod_root = Path(self.mod_path).resolve()
            for staged_path in self.staged_files or []:
                try:
                    relative = (
                        Path(staged_path).resolve().relative_to(mod_root).as_posix()
                    )
                except ValueError:
                    continue
                if relative == REGISTRY_FILE or relative.startswith(f"{COUNTRY_DIR}/"):
                    relevant_change = True
                    break
            if not relevant_change:
                return

        registry_result = self.parse_files_cached(
            [REGISTRY_FILE],
            "graphical_culture_registry",
            lambda text, _path: text,
            ignore_staged=True,
        )
        if not registry_result:
            self.add_warning(
                "graphical-culture-registry-missing",
                f"cannot check country graphical cultures because "
                f"{REGISTRY_FILE} is missing",
                REGISTRY_FILE,
            )
            return
        registered = _registered_cultures(next(iter(registry_result.values())))

        country_cultures = self.parse_files_cached(
            [f"{COUNTRY_DIR}/*.txt"],
            "country_graphical_cultures",
            lambda text, _path: _country_cultures(text),
            ignore_staged=True,
        )
        findings = 0
        for path, cultures in country_cultures.items():
            rel_path = Path(path).relative_to(self.mod_path).as_posix()
            for culture, line in cultures:
                if culture in registered:
                    continue
                findings += 1
                self.add_warning(
                    "graphical-culture-unregistered",
                    f"graphical culture '{culture}' is not listed in {REGISTRY_FILE}",
                    rel_path,
                    line,
                )
        self.log(
            f"  Scanned {len(country_cultures)} country files | "
            f"{len(registered)} registered cultures | {findings} warnings"
        )


if __name__ == "__main__":
    run_validator_main(Validator, "Validate country graphical culture registrations")
