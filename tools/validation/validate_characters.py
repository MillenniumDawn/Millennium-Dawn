#!/usr/bin/env python3
# Cross-reference leader traits against the role or advisor slot they are
# assigned to. Both pools fail the same way: a trait declared for the wrong
# branch (a navy trait on a general, or a navy chief trait in an army chief
# slot) loads silently, so the character quietly ships with fewer traits than
# the script promises, or with the wrong icon and bonus tier.
#
# The two pools are checked together because they cross: a `common/unit_leader/`
# trait is dead on an advisor and a `common/country_leader/` trait is dead on a
# general, so deciding either needs both pools loaded, over the same file walk.
import os
import re
import sys
from typing import Dict, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import extract_block_from_text
from validator_common import (
    LEADER_TRAIT_DEF_RE,
    BaseValidator,
    FileOpener,
    parse_leader_trait_names,
    run_validator_main,
)

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

ADVISOR_TRAIT_DIR = "common/country_leader"

# One file per advisor slot pool: the filename is the classification, so a trait
# is in the pool of the file it lives in. A name-prefix rule would misfile the
# eight vanilla-named air families (air_air_superiority_*, air_close_air_support_*,
# ...) -- they carry no `chief` in the name but are air chief traits.
SLOT_POOL_FILES = {
    "01_high_command_traits.txt": "high_command",
    "01_army_chief_traits.txt": "army_chief",
    "01_navy_chief_traits.txt": "navy_chief",
    "01_air_chief_traits.txt": "air_chief",
}

# Country-specific traits (ENG_mike_jackson_trait, CHI_tank_general_advisor, ...)
# are written for one character and belong to no shared pool, so the slot check
# skips them even when they sit in a pool file.
TAG_TRAIT_RE = re.compile(r"^[A-Z]{3}_")

ADVISOR_BLOCK_RE = re.compile(r"\badvisor\s*=\s*\{")
SLOT_RE = re.compile(r"\bslot\s*=\s*(\w+)")

CONTENT_PATTERNS = [
    "common/characters/*.txt",
    "common/national_focus/*.txt",
    "common/decisions/**/*.txt",
    "common/scripted_effects/*.txt",
    "common/on_actions/*.txt",
    "events/**/*.txt",
    "history/countries/*.txt",
]

# A staged change to either pool reclassifies every use of the traits it moves,
# so the scan widens to the whole repo instead of the staged set.
TRAIT_DEF_PREFIXES = ("common/unit_leader/", "common/country_leader/")


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
        for match in LEADER_TRAIT_DEF_RE.finditer(content):
            body, _ = extract_block_from_text(content, match.end() - 1)
            type_match = TYPE_RE.search(body)
            if not type_match:
                continue
            raw = type_match.group(1)
            declared = set(raw.strip("{} \t").split()) if "{" in raw else {raw}
            traits.setdefault(match.group(1), set()).update(declared)
    return traits


def parse_advisor_trait_slots(mod_path: str) -> Dict[str, str]:
    """Map each pooled advisor trait to the slot its file names."""
    slots: Dict[str, str] = {}
    for fname, slot in SLOT_POOL_FILES.items():
        path = os.path.join(mod_path, *ADVISOR_TRAIT_DIR.split("/"), fname)
        if not os.path.isfile(path):
            continue
        content = FileOpener.open_text_file(
            path, lowercase=False, strip_comments_flag=True
        )
        for match in LEADER_TRAIT_DEF_RE.finditer(content):
            slots[match.group(1)] = slot
    return slots


def missing_pool_files(mod_path: str) -> List[str]:
    """Return the pool files SLOT_POOL_FILES names that are not on disk."""
    return [
        fname
        for fname in SLOT_POOL_FILES
        if not os.path.isfile(
            os.path.join(mod_path, *ADVISOR_TRAIT_DIR.split("/"), fname)
        )
    ]


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


def collect_advisor_uses(content: str) -> List[Tuple[str, str, int]]:
    """Yield (slot, trait, line) for every advisor block that assigns traits.

    Covers `add_advisor_role = { advisor = { ... } }` in focuses and events too,
    since the inner block has the same shape.
    """
    uses = []
    for match in ADVISOR_BLOCK_RE.finditer(content):
        body, _ = extract_block_from_text(content, match.end() - 1)
        slot_match = SLOT_RE.search(body)
        traits_match = TRAITS_RE.search(body)
        if not slot_match or not traits_match:
            continue
        line = content.count("\n", 0, match.end() + traits_match.start(1)) + 1
        for trait in traits_match.group(1).split():
            uses.append((slot_match.group(1), trait, line))
    return uses


class Validator(BaseValidator):
    TITLE = "CHARACTER TRAIT VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def _check_role_uses(
        self,
        content: str,
        rel: str,
        trait_types: Dict[str, Set[str]],
        advisor_traits: Set[str],
    ):
        for role, trait, line in collect_trait_uses(content):
            declared = trait_types.get(trait)
            if declared is None:
                if trait in advisor_traits:
                    self.add_error(
                        "advisor-trait-on-unit-leader",
                        f"{role} uses '{trait}', a {ADVISOR_TRAIT_DIR}/ trait "
                        "that does nothing on a unit leader",
                        rel,
                        line,
                    )
                    continue
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

    def _check_advisor_uses(
        self,
        content: str,
        rel: str,
        trait_slots: Dict[str, str],
        advisor_traits: Set[str],
        unit_leader_traits: Set[str],
    ):
        for slot, trait, line in collect_advisor_uses(content):
            if trait in advisor_traits:
                if TAG_TRAIT_RE.match(trait):
                    continue
                expected = trait_slots.get(trait)
                if expected and slot in SLOT_POOL_FILES.values() and expected != slot:
                    self.add_error(
                        "advisor-trait-slot-mismatch",
                        f"'{trait}' belongs to the {expected} pool but is "
                        f"assigned to slot {slot}",
                        rel,
                        line,
                    )
            elif trait in unit_leader_traits:
                self.add_error(
                    "unit-leader-trait-on-advisor",
                    f"slot {slot} uses '{trait}', a common/unit_leader/ trait "
                    "that does nothing on an advisor",
                    rel,
                    line,
                )
            else:
                self.add_error(
                    "undefined-advisor-trait",
                    f"slot {slot} uses trait '{trait}', which is not defined in "
                    f"{ADVISOR_TRAIT_DIR}/",
                    rel,
                    line,
                )

    def _validate_leader_traits(self):
        self._log_section("Checking unit leader and advisor trait assignment...")

        trait_types = parse_trait_types(self.mod_path)
        unit_leader_traits = parse_leader_trait_names(self.mod_path, "unit_leader")
        # Country files (ENG_traits.txt, CHI_traits.txt, ...) define bespoke
        # advisor traits. They count as defined but stay unclassified, so they
        # never trip the slot check.
        advisor_traits = parse_leader_trait_names(self.mod_path, "country_leader")

        # A renamed or deleted pool file must fail loudly: silently dropping the
        # slot check would hide every mismatch behind a green run.
        missing = missing_pool_files(self.mod_path)
        for fname in missing:
            self.add_error(
                "advisor-pool-file-missing",
                f"{ADVISOR_TRAIT_DIR}/{fname} defines the "
                f"{SLOT_POOL_FILES[fname]} advisor pool but does not exist",
                f"{ADVISOR_TRAIT_DIR}/{fname}",
            )
        trait_slots = {} if missing else parse_advisor_trait_slots(self.mod_path)

        check_roles = bool(trait_types)
        if not check_roles:
            self.log(
                "  Warning: no unit leader traits parsed; skipping trait role checks",
                "warning",
            )
        check_advisors = bool(advisor_traits)
        if not check_advisors:
            self.log(
                "  Warning: no country leader traits parsed; skipping advisor "
                "trait checks",
                "warning",
            )
        if not (check_roles or check_advisors):
            return

        trait_definitions_changed = self.staged_only and any(
            os.path.relpath(filepath, self.mod_path)
            .replace(os.sep, "/")
            .startswith(TRAIT_DEF_PREFIXES)
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
            if check_roles:
                self._check_role_uses(content, rel, trait_types, advisor_traits)
            if check_advisors:
                self._check_advisor_uses(
                    content, rel, trait_slots, advisor_traits, unit_leader_traits
                )

    def run_validations(self):
        self._validate_leader_traits()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate character unit leader and advisor slot traits"
    )
