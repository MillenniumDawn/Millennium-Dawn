#!/usr/bin/env python3
"""Validate that every playable country with its own focus tree has an AI path rule.

A focus tree owned by a single tag that holds states at game start is a country the
player can meet from day one, and its AI needs a `TAG_ai_behavior` game rule with at
least a `HISTORICAL` option and a `default = { }` block to steer it. Shared trees
(several owner tags) and tags that only spawn later are out of scope.
"""

import glob
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from validator_common import (
    BaseValidator,
    extract_block_from_text,
    run_validator_main,
    strip_comments,
)

FOCUS_DIR = "common/national_focus"
GAME_RULES_DIR = "common/game_rules"
STATES_DIR = "history/states"
SCOPE_DIRS = (FOCUS_DIR, GAME_RULES_DIR, STATES_DIR)

COUNTRY_BLOCK_RE = re.compile(r"\bcountry\s*=\s*\{")
TAG_ASSIGN_RE = re.compile(r"\b(?:original_)?tag\s*=\s*([A-Z0-9]{3})\b")
STATE_OWNER_RE = re.compile(r"^\s*owner\s*=\s*([A-Z0-9]{3})\b", re.MULTILINE)
RULE_RE = re.compile(r"^([A-Z0-9]{3})_ai_behavior\s*=\s*\{", re.MULTILINE)
OPTION_NAME_RE = re.compile(r"\boption\s*=\s*\{\s*name\s*=\s*(\w+)")
DEFAULT_BLOCK_RE = re.compile(r"\bdefault\s*=\s*\{")


def _tree_owner(text: str) -> Tuple[Optional[str], int]:
    """(tag, line) when the tree's `country = { }` block names exactly one tag."""
    clean = strip_comments(text)
    match = COUNTRY_BLOCK_RE.search(clean)
    if not match:
        return None, 0
    body, _ = extract_block_from_text(clean, match.start())
    tags = set(TAG_ASSIGN_RE.findall(body))
    if len(tags) != 1:
        return None, 0
    return tags.pop(), clean.count("\n", 0, match.start()) + 1


def _state_owners(text: str) -> Set[str]:
    return set(STATE_OWNER_RE.findall(strip_comments(text)))


def _rules(text: str) -> Dict[str, Tuple[int, List[str], bool]]:
    """tag -> (line, option names, has default block) for every `TAG_ai_behavior`."""
    clean = strip_comments(text)
    found: Dict[str, Tuple[int, List[str], bool]] = {}
    for match in RULE_RE.finditer(clean):
        body, _ = extract_block_from_text(clean, match.start())
        found[match.group(1)] = (
            clean.count("\n", 0, match.start()) + 1,
            OPTION_NAME_RE.findall(body),
            bool(DEFAULT_BLOCK_RE.search(body)),
        )
    return found


class Validator(BaseValidator):
    TITLE = "AI PATH RULES"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        mod = Path(self.mod_path)
        focus_files = sorted(glob.glob(str(mod / FOCUS_DIR / "*.txt")))
        if not focus_files:
            return
        if self.staged_only and not self.staged_touches(SCOPE_DIRS):
            return

        owners: Set[str] = set()
        for path in sorted(glob.glob(str(mod / STATES_DIR / "*.txt"))):
            owners |= _state_owners(self._read(path))

        rules: Dict[str, Tuple[str, int, List[str], bool]] = {}
        for path in sorted(glob.glob(str(mod / GAME_RULES_DIR / "*.txt"))):
            rel = Path(path).relative_to(mod).as_posix()
            for tag, (line, options, has_default) in _rules(self._read(path)).items():
                rules[tag] = (rel, line, options, has_default)

        trees = 0
        findings = 0
        for path in focus_files:
            tag, line = _tree_owner(self._read(path))
            if tag is None or tag not in owners:
                continue
            trees += 1
            rel = Path(path).relative_to(mod).as_posix()
            if tag not in rules:
                findings += 1
                self.add_warning(
                    "ai-path-rule-missing",
                    f"tag '{tag}' owns this focus tree and starts with states but has no "
                    f"{tag}_ai_behavior rule in {GAME_RULES_DIR}/",
                    rel,
                    line,
                )
                continue
            rule_file, rule_line, options, has_default = rules[tag]
            missing = []
            if "HISTORICAL" not in options:
                missing.append("a HISTORICAL option")
            if not has_default:
                missing.append("a default = { } block")
            if missing:
                findings += 1
                self.add_warning(
                    "ai-path-rule-incomplete",
                    f"{tag}_ai_behavior lacks {' and '.join(missing)}",
                    rule_file,
                    rule_line,
                )
        self.log(
            f"  Scanned {trees} country focus trees | {len(rules)} rules | "
            f"{findings} findings"
        )

    @staticmethod
    def _read(path: str) -> str:
        try:
            return Path(path).read_text(encoding="utf-8-sig")
        except OSError:
            return ""


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate every playable country with a focus tree has an AI path rule",
    )
