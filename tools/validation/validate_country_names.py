#!/usr/bin/env python3
"""Validate that every static country tag has a names block.

A tag in common/country_tags/ with no block in common/names/ makes the game log
an error and fall back to `default` names for its aces and generals. Tags after
`dynamic_tags = yes` are civil-war placeholders and are exempt, as are tag aliases.
"""

import glob
import re
from pathlib import Path
from typing import List, Set, Tuple

from validator_common import BaseValidator, run_validator_main, strip_comments

COUNTRY_TAG_DIR = "common/country_tags"
NAMES_DIR = "common/names"

TAG_DEF_RE = re.compile(r'^[ \t]*([A-Z0-9]{3})[ \t]*=[ \t]*"', re.MULTILINE)
DYNAMIC_MARKER_RE = re.compile(r"^[ \t]*dynamic_tags[ \t]*=[ \t]*yes", re.MULTILINE)
NAMES_BLOCK_RE = re.compile(r"^([A-Z0-9]{3})[ \t]*=[ \t]*\{", re.MULTILINE)


def _static_tags(text: str) -> List[Tuple[str, int]]:
    """(tag, line) for every tag defined before any `dynamic_tags = yes`."""
    clean = strip_comments(text)
    marker = DYNAMIC_MARKER_RE.search(clean)
    if marker:
        clean = clean[: marker.start()]
    return [
        (m.group(1), clean.count("\n", 0, m.start()) + 1)
        for m in TAG_DEF_RE.finditer(clean)
    ]


def _names_tags(text: str) -> Set[str]:
    return set(NAMES_BLOCK_RE.findall(strip_comments(text)))


class Validator(BaseValidator):
    TITLE = "COUNTRY NAMES"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        mod = Path(self.mod_path)
        tag_files = sorted(glob.glob(str(mod / COUNTRY_TAG_DIR / "*.txt")))
        if not tag_files:
            return
        if self.staged_only and not self._touches_scope():
            return

        named: Set[str] = set()
        for path in sorted(glob.glob(str(mod / NAMES_DIR / "*.txt"))):
            try:
                named |= _names_tags(Path(path).read_text(encoding="utf-8-sig"))
            except OSError:
                continue

        tags_seen = 0
        findings = 0
        for path in tag_files:
            rel = Path(path).relative_to(mod).as_posix()
            try:
                text = Path(path).read_text(encoding="utf-8-sig")
            except OSError:
                continue
            for tag, line in _static_tags(text):
                tags_seen += 1
                if tag in named:
                    continue
                findings += 1
                self.add_error(
                    "country-names-missing",
                    f"tag '{tag}' has no names block in {NAMES_DIR}/",
                    rel,
                    line,
                )
        self.log(
            f"  Scanned {tags_seen} tags | {len(named)} names blocks | "
            f"{findings} findings"
        )

    def _touches_scope(self) -> bool:
        mod = Path(self.mod_path)
        for f in self.staged_files or []:
            p = Path(f)
            abs_p = p if p.is_absolute() else mod / p
            try:
                rel = abs_p.resolve().relative_to(mod.resolve()).as_posix()
            except ValueError:
                continue
            if rel.startswith((COUNTRY_TAG_DIR + "/", NAMES_DIR + "/")):
                return True
        return False


if __name__ == "__main__":
    run_validator_main(Validator, "Validate every country tag has a names block")
