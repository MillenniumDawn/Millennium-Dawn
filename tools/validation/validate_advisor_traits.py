#!/usr/bin/env python3
# Cross-reference advisor traits against the slot they are assigned to.
# MD keeps chief and high command traits in separate pools that scale
# differently (chiefs 5/10/15%, high command 4/8/12%) and draw from different
# sprite sets. The engine applies either pool's modifiers in either slot, so a
# crossed assignment never errors -- it just ships the wrong icon and tier.
import os
import re
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import extract_block_from_text
from validator_common import (
    LEADER_TRAIT_DEF_RE,
    BaseValidator,
    FileOpener,
    parse_leader_trait_names,
    run_validator_main,
)

TRAIT_DIR = "common/country_leader"

# One file per advisor slot pool: the filename is the classification, so a trait
# is in the pool of the file it lives in. A name-prefix rule would misfile the
# eight vanilla-named air families (air_air_superiority_*, air_close_air_support_*,
# ...) -- they carry no `chief` in the name but are air chief traits.
SLOT_POOL_FILES = {
    "01_high_command_traits.txt": "high_command",
    "02_army_chief_traits.txt": "army_chief",
    "03_navy_chief_traits.txt": "navy_chief",
    "04_air_chief_traits.txt": "air_chief",
}

# Country-specific traits (ENG_mike_jackson_trait, CHI_tank_general_advisor, ...)
# are written for one character and belong to no shared pool, so the slot check
# skips them even when they sit in a pool file.
TAG_TRAIT_RE = re.compile(r"^[A-Z]{3}_")

ADVISOR_BLOCK_RE = re.compile(r"\badvisor\s*=\s*\{")
SLOT_RE = re.compile(r"\bslot\s*=\s*(\w+)")
TRAITS_RE = re.compile(r"\btraits\s*=\s*\{([^}]*)\}")

CONTENT_PATTERNS = [
    "common/characters/*.txt",
    "common/national_focus/*.txt",
    "common/decisions/**/*.txt",
    "common/scripted_effects/*.txt",
    "common/on_actions/*.txt",
    "events/**/*.txt",
    "history/countries/*.txt",
]


def parse_advisor_trait_slots(mod_path: str) -> Dict[str, str]:
    """Map each pooled advisor trait to the slot its file names."""
    slots: Dict[str, str] = {}
    for fname, slot in SLOT_POOL_FILES.items():
        path = os.path.join(mod_path, *TRAIT_DIR.split("/"), fname)
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
        if not os.path.isfile(os.path.join(mod_path, *TRAIT_DIR.split("/"), fname))
    ]


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
    TITLE = "ADVISOR TRAIT SLOT VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def _validate_advisor_traits(self):
        self._log_section("Checking advisor trait slot assignment...")

        # A renamed or deleted pool file must fail loudly: silently dropping the
        # slot check would hide every mismatch behind a green run.
        missing = missing_pool_files(self.mod_path)
        for fname in missing:
            self.add_error(
                "advisor-pool-file-missing",
                f"{TRAIT_DIR}/{fname} defines the "
                f"{SLOT_POOL_FILES[fname]} advisor pool but does not exist",
                f"{TRAIT_DIR}/{fname}",
            )

        trait_slots = {} if missing else parse_advisor_trait_slots(self.mod_path)

        # Country files (ENG_traits.txt, CHI_traits.txt, ...) define bespoke
        # advisor traits. They count as defined but stay unclassified, so they
        # never trip the slot check.
        defined = parse_leader_trait_names(self.mod_path, "country_leader")
        unit_leader_traits = parse_leader_trait_names(self.mod_path, "unit_leader")
        if not defined:
            self.log(
                "  Warning: no country leader traits parsed; skipping advisor "
                "trait checks",
                "warning",
            )
            return

        definitions_changed = self.staged_only and any(
            os.path.relpath(filepath, self.mod_path)
            .replace(os.sep, "/")
            .startswith(("common/country_leader/", "common/unit_leader/"))
            for filepath in self.staged_files or []
        )
        for filepath in self._collect_files(
            CONTENT_PATTERNS, ignore_staged=definitions_changed
        ):
            content = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            rel = os.path.relpath(filepath, self.mod_path)
            for slot, trait, line in collect_advisor_uses(content):
                if trait in defined:
                    if TAG_TRAIT_RE.match(trait):
                        continue
                    expected = trait_slots.get(trait)
                    if (
                        expected
                        and slot in SLOT_POOL_FILES.values()
                        and expected != slot
                    ):
                        self.add_warning(
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
                        "common/country_leader/",
                        rel,
                        line,
                    )

    def run_validations(self):
        self._validate_advisor_traits()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate advisor trait slot assignment")
