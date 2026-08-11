#!/usr/bin/env python3
# Cross-reference unit leader traits against the role they are assigned to.
# A trait declared for the wrong branch (a navy trait on a general) loads
# silently and never applies, so the leader quietly ships with fewer traits
# than the script promises.
import os
import re
import sys
from typing import Dict, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import extract_block_from_text
from validator_common import BaseValidator, FileOpener, run_validator_main

TRAIT_DEF_RE = re.compile(r"^\t(\w+)\s*=\s*\{", re.MULTILINE)
TYPE_RE = re.compile(r"(?<!trait_)\btype\s*=\s*(\{[^}]*\}|\w+)")
TRAITS_RE = re.compile(r"\btraits\s*=\s*\{([^}]*)\}")

# Roles that carry unit leader traits, and the trait `type` values each accepts.
# `all` is universal, so it never mismatches. Only the branch is checked: land
# leaders share one trait pool, and vanilla itself puts corps_commander traits
# on field marshals and back, so that split is not an error.
LAND_TYPES = {"land", "corps_commander", "field_marshal"}
ROLE_TYPES: Dict[str, Set[str]] = {
    "field_marshal": LAND_TYPES,
    "corps_commander": LAND_TYPES,
    "navy_leader": {"navy"},
    "operative": {"operative"},
}

# Effect forms that build a leader inline instead of via common/characters/.
CREATE_ROLES = {
    "create_field_marshal": "field_marshal",
    "create_corps_commander": "corps_commander",
    "create_navy_leader": "navy_leader",
    "create_operative_leader": "operative",
}

ROLE_BLOCK_RE = re.compile(
    r"\b(" + "|".join(list(ROLE_TYPES) + list(CREATE_ROLES)) + r")\s*=\s*\{"
)

CONTENT_PATTERNS = [
    "common/characters/*.txt",
    "common/national_focus/*.txt",
    "common/decisions/**/*.txt",
    "common/scripted_effects/*.txt",
    "common/on_actions/*.txt",
    "events/**/*.txt",
    "history/countries/*.txt",
]


def parse_trait_types(mod_path: str) -> Dict[str, Set[str]]:
    """Map every unit leader trait to the role types it declares."""
    traits: Dict[str, Set[str]] = {}
    trait_dir = os.path.join(mod_path, "common", "unit_leader")
    if not os.path.isdir(trait_dir):
        return traits

    try:
        trait_files = sorted(os.listdir(trait_dir))
    except OSError:
        return traits

    for fname in trait_files:
        if not fname.endswith(".txt"):
            continue
        content = FileOpener.open_text_file(
            os.path.join(trait_dir, fname), lowercase=False, strip_comments_flag=True
        )
        for match in TRAIT_DEF_RE.finditer(content):
            body, _ = extract_block_from_text(content, match.end() - 1)
            type_match = TYPE_RE.search(body)
            if not type_match:
                continue
            raw = type_match.group(1)
            declared = set(raw.strip("{} \t").split()) if "{" in raw else {raw}
            traits.setdefault(match.group(1), set()).update(declared)
    return traits


def collect_trait_uses(content: str) -> List[Tuple[str, str, int]]:
    """Yield (role, trait, line) for every leader block that assigns traits."""
    uses = []
    for match in ROLE_BLOCK_RE.finditer(content):
        keyword = match.group(1)
        role = CREATE_ROLES.get(keyword, keyword)
        body, _ = extract_block_from_text(content, match.end() - 1)
        traits_match = TRAITS_RE.search(body)
        if not traits_match:
            continue
        line = content.count("\n", 0, match.end() + traits_match.start(1)) + 1
        for trait in traits_match.group(1).split():
            uses.append((role, trait, line))
    return uses


class Validator(BaseValidator):
    TITLE = "CHARACTER TRAIT VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def _validate_trait_roles(self):
        self._log_section("Checking unit leader trait roles...")

        trait_types = parse_trait_types(self.mod_path)
        if not trait_types:
            self.log(
                "  Warning: no unit leader traits parsed; skipping trait role checks",
                "warning",
            )
            return

        trait_definitions_changed = self.staged_only and any(
            os.path.relpath(filepath, self.mod_path)
            .replace(os.sep, "/")
            .startswith("common/unit_leader/")
            for filepath in self.staged_files or []
        )
        files = self._collect_files(
            CONTENT_PATTERNS, ignore_staged=trait_definitions_changed
        )
        for filepath in files:
            content = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            rel = os.path.relpath(filepath, self.mod_path)
            for role, trait, line in collect_trait_uses(content):
                declared = trait_types.get(trait)
                if declared is None:
                    self.add_warning(
                        "undefined-unit-leader-trait",
                        f"{role} uses trait '{trait}', which is not defined in common/unit_leader/",
                        rel,
                        line,
                    )
                elif not declared & (ROLE_TYPES[role] | {"all"}):
                    self.add_error(
                        "trait-role-mismatch",
                        f"{role} uses trait '{trait}' (type = {' '.join(sorted(declared))}), "
                        "which that role cannot take",
                        rel,
                        line,
                    )

    def run_validations(self):
        self._validate_trait_roles()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate character unit leader traits")
