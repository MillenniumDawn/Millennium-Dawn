#!/usr/bin/env python3
# Check every technology category reference against common/technology_tags/.
# An unknown category name compiles silently and grants nothing, so a focus,
# event or idea can promise a research bonus and deliver zero. Two live cases
# motivated this: CAT_encryption (the token is CAT_encryption_tech) sat in eight
# idea research_bonus blocks, and CAT_computer_systems is a real token that
# means armour computer systems, so computing content using it bought tank tech.
import difflib
import os
import re
import sys
from typing import Dict, FrozenSet, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import FileOpener
from validator_common import BaseValidator, Severity, run_validator_main

# Categories are bare tokens inside technology_Categories = { }. CAT_Military is
# mixed case, so this cannot be restricted to lowercase.
_CATEGORY_TOKEN_RE = re.compile(r"\bCAT_\w+")

# `category = CAT_x` in add_tech_bonus / add_doctrine_cost_reduction blocks.
_CATEGORY_ASSIGN_RE = re.compile(r"\bcategory\s*=\s*(CAT_\w+)")

# research_bonus = { CAT_x = 0.05 } — the keys are categories.
_RESEARCH_BONUS_RE = re.compile(r"\bresearch_bonus\s*=\s*\{")

_TAGS_GLOB = "common/technology_tags/**/*.txt"
_VALIDATE_PATTERNS = [
    "common/**/*.txt",
    "events/**/*.txt",
]


def _brace_span(text: str, open_idx: int) -> int:
    """Index just past the block whose opening brace is at *open_idx*."""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(text)


def _references(text: str) -> List[Tuple[str, int]]:
    """Every (category_name, char_offset) this text references.

    Deliberately narrow: only `category = CAT_x` and the keys of a
    research_bonus block. A bare CAT_ token elsewhere is not a category
    reference, which is what keeps `has_country_flag = CAT_revolted_against_spain`
    (a Catalonia flag) and `name = CAT_tribute` (a tech-bonus name) out of this.
    """
    found: List[Tuple[str, int]] = []
    for m in _CATEGORY_ASSIGN_RE.finditer(text):
        found.append((m.group(1), m.start(1)))
    for m in _RESEARCH_BONUS_RE.finditer(text):
        open_idx = text.index("{", m.start())
        end = _brace_span(text, open_idx)
        body = text[open_idx + 1 : end]
        for km in re.finditer(r"(CAT_\w+)\s*=", body):
            found.append((km.group(1), open_idx + 1 + km.start(1)))
    return found


def _check_file(args) -> List[Tuple[str, str, int]]:
    """Worker: return (category, relpath, line) for unknown references."""
    filepath, known, mod_path = args
    try:
        text = FileOpener.open_text_file(filepath, strip_comments_flag=True)
    except (OSError, UnicodeDecodeError):
        return []
    rel = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    out: List[Tuple[str, str, int]] = []
    for name, offset in _references(text):
        if name in known:
            continue
        out.append((name, rel, text.count("\n", 0, offset) + 1))
    return out


class Validator(BaseValidator):
    TITLE = "TECHNOLOGY CATEGORY VALIDATION"

    def _load_known_categories(self) -> FrozenSet[str]:
        """Every category token declared under common/technology_tags/."""
        known: Set[str] = set()
        for path in self._collect_files([_TAGS_GLOB], ignore_staged=True):
            try:
                text = FileOpener.open_text_file(path, strip_comments_flag=True)
            except (OSError, UnicodeDecodeError):
                continue
            known.update(_CATEGORY_TOKEN_RE.findall(text))
        self.log(f"  Known category set: {len(known)} names")
        return frozenset(known)

    def validate_category_references(self, known: FrozenSet[str]):
        self._log_section("Checking technology category references...")
        if not known:
            self._report(
                [
                    (
                        "No technology categories found under common/technology_tags/",
                        "common/technology_tags",
                        0,
                    )
                ],
                "",
                "Technology category set is empty:",
                severity=Severity.ERROR,
                category="tech-category-set-missing",
            )
            return

        # _collect_files already applies should_skip_file against the mod-relative
        # path. Re-filtering on the absolute path here would skip everything when
        # mod_path itself lives under .claude/worktrees/.
        files = self._collect_files(_VALIDATE_PATTERNS)
        self.log(f"  Checking {len(files)} files...")
        batches = self._pool_map(
            _check_file, [(f, known, self.mod_path) for f in files], chunksize=30
        )

        # Report each unknown name once: repeated use is not evidence of validity
        # and would otherwise bury the finding under identical lines.
        first_seen: Dict[str, Tuple[str, int]] = {}
        for batch in batches:
            for name, rel, line in batch:
                first_seen.setdefault(name, (rel, line))

        formatted = []
        for name, (rel, line) in sorted(
            first_seen.items(), key=lambda kv: (kv[1][0], kv[1][1])
        ):
            close = difflib.get_close_matches(name, known, n=1, cutoff=0.6)
            hint = f", did you mean '{close[0]}'?" if close else ""
            formatted.append((f"Unknown technology category '{name}'{hint}", rel, line))

        self._report(
            formatted,
            "No unknown technology categories found",
            "Unknown technology categories (compile silently, grant nothing):",
            severity=Severity.ERROR,
            category="unknown-tech-category",
        )

    def run_validations(self):
        self.validate_category_references(
            self.cached("tech_categories", self._load_known_categories)
        )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate technology category references in Millennium Dawn mod",
    )
