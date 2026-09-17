#!/usr/bin/env python3
# Check every technology category reference against common/technology_tags/,
# and the tag set itself against the naming, localisation and usage rules.
# An unknown category name compiles silently and grants nothing, so a focus,
# event or idea can promise a research bonus and deliver zero. Two live cases
# motivated this: CAT_encryption (the token is CAT_encryption_tech) sat in eight
# idea research_bonus blocks, and CAT_computer_systems is a real token that
# means armour computer systems, so computing content using it bought tank tech.
# A doctrine's own categories block, directly under common/doctrines/, counts as
# both a reference to check and a carrier that satisfies the unused-tag check.
# Doctrines cannot take a research bonus, so a doctrine-carried tag needs only its
# name loc key, not the _research one.
import difflib
import os
import re
import sys
from typing import Dict, FrozenSet, Iterable, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import FileOpener
from validator_common import BaseValidator, Severity, run_validator_main

# The tag block in common/technology_tags/. Every bare token inside it is a
# category, whatever its case: a wrongly cased token must still load so the
# format check can name it.
_CATEGORIES_BLOCK_RE = re.compile(r"(?i)\btechnology_categories\s*=\s*\{")
_TOKEN_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")

# Every tag is CAT_ followed by lowercase words (#4250).
_TAG_FORMAT_RE = re.compile(r"^CAT_[a-z0-9_]+$")

# `category = CAT_x` in add_tech_bonus / add_doctrine_cost_reduction blocks.
_CATEGORY_ASSIGN_RE = re.compile(r"\bcategory\s*=\s*((?i:cat_)\w+)")

# research_bonus = { CAT_x = 0.05 } — the keys are categories. ai_focuses and
# ai_strategy_plans weight categories the same way in research = { CAT_x = 5.0 }.
_KEYED_BLOCK_RE = re.compile(r"\b(?:research_bonus|research)\s*=\s*\{")
_KEYED_CATEGORY_RE = re.compile(r"((?i:cat_)\w+)\s*=")

# MIO research_categories = { CAT_x CAT_y } and, in tech files only, a tech's
# own categories = { }. Outside common/technologies/ a `categories` block is a
# doctrine or sub-unit category list, not a tech category reference.
_LISTED_BLOCK_RE = re.compile(r"\bresearch_categories\s*=\s*\{")
_TECH_CATEGORIES_RE = re.compile(r"\bcategories\s*=\s*\{")

_TAGS_GLOB = "common/technology_tags/**/*.txt"
_TECH_DIR = "common/technologies/"
_TECH_GLOB = _TECH_DIR + "**/*.txt"
# A doctrine's own categories block sits at depth 2 (doctrine_name = { categories
# = { ... } }); its mastery block nests a sub-unit categories block one level
# deeper, which stays a non-reference like any other categories block.
_DOCTRINE_DIRS = ("common/doctrines/grand_doctrines/", "common/doctrines/subdoctrines/")
_DOCTRINE_GLOB = "common/doctrines/**/*.txt"
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


def _block_bodies(text: str, opener: "re.Pattern") -> Iterable[Tuple[str, int]]:
    """(body, body_offset) of every block *opener* introduces."""
    for m in opener.finditer(text):
        open_idx = text.index("{", m.start())
        end = _brace_span(text, open_idx)
        yield text[open_idx + 1 : end], open_idx + 1


def _doctrine_category_bodies(text: str) -> Iterable[Tuple[str, int]]:
    """(body, body_offset) of every categories block sitting directly inside a doctrine.

    A doctrine's own block is at brace depth 1 when it opens (the doctrine body
    itself), so its `{` lands at depth 2; a mastery block's nested categories
    sit one level deeper and are skipped. Depth is tracked in a single pass so
    it stays linear in the length of *text*.
    """
    matches = list(_TECH_CATEGORIES_RE.finditer(text))
    if not matches:
        return
    depth = 0
    mi = 0
    for i, ch in enumerate(text):
        while mi < len(matches) and matches[mi].start() == i:
            if depth == 1:
                open_idx = text.index("{", matches[mi].start())
                end = _brace_span(text, open_idx)
                yield text[open_idx + 1 : end], open_idx + 1
            mi += 1
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1


def _references(
    text: str, tech_file: bool = False, doctrine_file: bool = False
) -> List[Tuple[str, int]]:
    """Every (category_name, char_offset) this text references.

    Deliberately narrow: `category = CAT_x`, the keys of a research_bonus or
    research block, the tokens of a research_categories block, for tech files
    the tokens of a categories block, and for doctrine files the tokens of a
    doctrine's own depth-2 categories block. A bare CAT_ token elsewhere is not
    a category reference, which is what keeps
    `has_country_flag = CAT_revolted_against_spain` (a Catalonia flag) and
    `name = CAT_tribute` (a tech-bonus name) out of this.
    """
    found: List[Tuple[str, int]] = []
    for m in _CATEGORY_ASSIGN_RE.finditer(text):
        found.append((m.group(1), m.start(1)))
    for body, offset in _block_bodies(text, _KEYED_BLOCK_RE):
        for km in _KEYED_CATEGORY_RE.finditer(body):
            found.append((km.group(1), offset + km.start(1)))
    listed = [_LISTED_BLOCK_RE]
    if tech_file:
        listed.append(_TECH_CATEGORIES_RE)
    for opener in listed:
        for body, offset in _block_bodies(text, opener):
            for tm in _TOKEN_RE.finditer(body):
                found.append((tm.group(0), offset + tm.start()))
    if doctrine_file:
        for body, offset in _doctrine_category_bodies(text):
            for tm in _TOKEN_RE.finditer(body):
                found.append((tm.group(0), offset + tm.start()))
    return found


def _tag_tokens(text: str) -> List[Tuple[str, int]]:
    """Every (token, char_offset) declared inside a technology_categories block."""
    found: List[Tuple[str, int]] = []
    for body, offset in _block_bodies(text, _CATEGORIES_BLOCK_RE):
        for tm in _TOKEN_RE.finditer(body):
            found.append((tm.group(0), offset + tm.start()))
    return found


def load_known_categories(paths: Iterable[str]) -> FrozenSet[str]:
    """Every category token declared in the given technology_tags files."""
    known: Set[str] = set()
    for path in paths:
        try:
            text = FileOpener.open_text_file(path, strip_comments_flag=True)
        except (OSError, UnicodeDecodeError):
            continue
        known.update(name for name, _ in _tag_tokens(text))
    return frozenset(known)


def _check_file(args) -> List[Tuple[str, str, int]]:
    """Worker: return (category, relpath, line) for unknown references."""
    filepath, known, mod_path = args
    try:
        text = FileOpener.open_text_file(filepath, strip_comments_flag=True)
    except (OSError, UnicodeDecodeError):
        return []
    rel = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    out: List[Tuple[str, str, int]] = []
    for name, offset in _references(
        text,
        tech_file=rel.startswith(_TECH_DIR),
        doctrine_file=rel.startswith(_DOCTRINE_DIRS),
    ):
        if name in known:
            continue
        out.append((name, rel, text.count("\n", 0, offset) + 1))
    return out


def _carried_categories(args) -> Set[str]:
    """Worker: every category token a tech or doctrine file carries."""
    filepath, is_doctrine = args
    try:
        text = FileOpener.open_text_file(filepath, strip_comments_flag=True)
    except (OSError, UnicodeDecodeError):
        return set()
    bodies = (
        _doctrine_category_bodies(text)
        if is_doctrine
        else _block_bodies(text, _TECH_CATEGORIES_RE)
    )
    return {tm.group(0) for body, _ in bodies for tm in _TOKEN_RE.finditer(body)}


class Validator(BaseValidator):
    TITLE = "TECHNOLOGY CATEGORY VALIDATION"

    def _load_known_categories(self) -> FrozenSet[str]:
        """Every category token declared under common/technology_tags/."""
        known = load_known_categories(
            self._collect_files([_TAGS_GLOB], ignore_staged=True)
        )
        self.log(f"  Known category set: {len(known)} names")
        return known

    def _declared_tags(self) -> List[Tuple[str, str, int]]:
        """(token, relpath, line) for every declaration, in file order."""
        out: List[Tuple[str, str, int]] = []
        for path in self._collect_files([_TAGS_GLOB], ignore_staged=True):
            try:
                text = FileOpener.open_text_file(path, strip_comments_flag=True)
            except (OSError, UnicodeDecodeError):
                continue
            rel = os.path.relpath(path, self.mod_path).replace(os.sep, "/")
            for name, offset in _tag_tokens(text):
                out.append((name, rel, text.count("\n", 0, offset) + 1))
        return out

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

    def validate_tag_definitions(self, known: FrozenSet[str]):
        """Every declared tag is CAT_lowercase, localised and used by a tech."""
        if not known:
            return
        self._log_section("Checking technology category definitions...")
        declared = self._declared_tags()

        self._report(
            [
                (f"Technology category '{name}' is not CAT_lowercase", rel, line)
                for name, rel, line in declared
                if not _TAG_FORMAT_RE.match(name)
            ],
            "All technology categories are CAT_lowercase",
            "Technology categories not named CAT_lowercase:",
            severity=Severity.ERROR,
            category="tech-category-name-format",
        )

        tech_files = self._collect_files([_TECH_GLOB], ignore_staged=True)
        doctrine_files = [
            f
            for f in self._collect_files([_DOCTRINE_GLOB], ignore_staged=True)
            if os.path.relpath(f, self.mod_path)
            .replace(os.sep, "/")
            .startswith(_DOCTRINE_DIRS)
        ]
        tech_used: Set[str] = set()
        for cats in self._pool_map(
            _carried_categories, [(f, False) for f in tech_files]
        ):
            tech_used.update(cats)
        doctrine_used: Set[str] = set()
        for cats in self._pool_map(
            _carried_categories, [(f, True) for f in doctrine_files]
        ):
            doctrine_used.update(cats)

        loc_keys = self._load_localisation_keys()
        unlocalised = []
        for name, rel, line in declared:
            wanted = (name,) if name in doctrine_used else (name, f"{name}_research")
            missing = [k for k in wanted if k not in loc_keys]
            if missing:
                unlocalised.append(
                    (
                        f"Technology category '{name}' has no English loc key "
                        f"{', '.join(missing)}",
                        rel,
                        line,
                    )
                )
        self._report(
            unlocalised,
            "All technology categories are localised",
            "Technology categories missing a name or _research loc key:",
            severity=Severity.ERROR,
            category="tech-category-unlocalised",
        )

        used = tech_used | doctrine_used
        self._report(
            [
                (
                    f"Technology category '{name}' is not used by any technology or doctrine",
                    rel,
                    line,
                )
                for name, rel, line in declared
                if name not in used
            ],
            "All technology categories are used by a technology or doctrine",
            "Technology categories no technology or doctrine carries:",
            severity=Severity.ERROR,
            category="tech-category-unused",
        )

    def run_validations(self):
        known = self.cached("tech_categories", self._load_known_categories)
        self.validate_category_references(known)
        self.validate_tag_definitions(known)


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate technology category references in Millennium Dawn mod",
    )
