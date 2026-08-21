#!/usr/bin/env python3
# Cross-reference advisor traits against the slot they are assigned to.
# MD keeps chief and high command traits in separate pools that scale
# differently (chiefs 5/10/15%, high command 4/8/12%) and draw from different
# sprite sets. The engine applies either pool's modifiers in either slot, so a
# crossed assignment never errors -- it just ships the wrong icon and tier.
import os
import re
import sys
from typing import Dict, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import extract_block_from_text
from validator_common import BaseValidator, FileOpener, run_validator_main

ADVISOR_TRAIT_FILE = "common/country_leader/01_military_advisor_traits.txt"

# Section comments in ADVISOR_TRAIT_FILE are the authoritative pool boundary.
# A name-prefix rule would misfile the eight vanilla-named air families
# (air_air_superiority_*, air_close_air_support_*, ...): they carry no `chief`
# in the name but sit under the Air Chief header and are used on air_chief 266
# times against 37 on high_command, so the header records the real intent.
SECTION_TO_SLOT = {
    "Military High Command Traits": "high_command",
    "Army Chief Traits": "army_chief",
    "Navy Chief Traits": "navy_chief",
    "Air Chief Traits": "air_chief",
}

# Headers are inconsistently indented, and the trailing ### is required so the
# section-less `### Military Minister Traits` preamble is not treated as one.
# \r is tolerated because a Windows working tree can hold the file as CRLF.
SECTION_RE = re.compile(r"^[ \t]*###[ \t]*(.+?)[ \t]*###[ \t\r]*$", re.MULTILINE)
TRAIT_DEF_RE = re.compile(r"^\t(\w+)\s*=\s*\{", re.MULTILINE)
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

# Guards against reporting the whole database when the trait file is missing or
# its headers were reformatted. The real file classifies 150 traits.
_MIN_CLASSIFIED = 50


def parse_advisor_trait_slots(content: str) -> Dict[str, str]:
    """Map each trait in the shared advisor pool to the slot its section names."""
    sections = [
        (match.start(), SECTION_TO_SLOT.get(match.group(1)))
        for match in SECTION_RE.finditer(content)
    ]
    slots: Dict[str, str] = {}
    for match in TRAIT_DEF_RE.finditer(content):
        slot = None
        for start, section_slot in sections:
            if start > match.start():
                break
            slot = section_slot
        if slot:
            slots[match.group(1)] = slot
    return slots


def _parse_trait_names(mod_path: str, subdir: str) -> Set[str]:
    """Collect every trait defined in a common/<subdir>/ trait file."""
    names: Set[str] = set()
    trait_dir = os.path.join(mod_path, "common", subdir)
    if not os.path.isdir(trait_dir):
        return names

    try:
        trait_files = sorted(os.listdir(trait_dir))
    except OSError:
        return names

    for fname in trait_files:
        if not fname.endswith(".txt"):
            continue
        content = FileOpener.open_text_file(
            os.path.join(trait_dir, fname), lowercase=False, strip_comments_flag=True
        )
        names.update(match.group(1) for match in TRAIT_DEF_RE.finditer(content))
    return names


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

        trait_path = os.path.join(self.mod_path, *ADVISOR_TRAIT_FILE.split("/"))
        trait_slots: Dict[str, str] = {}
        if os.path.isfile(trait_path):
            trait_slots = parse_advisor_trait_slots(
                FileOpener.open_text_file(trait_path, lowercase=False)
            )
        if len(trait_slots) < _MIN_CLASSIFIED:
            self.log(
                f"  Warning: only {len(trait_slots)} advisor traits classified from "
                f"{ADVISOR_TRAIT_FILE}; skipping advisor trait checks",
                "warning",
            )
            return

        # Country files (ENG_traits.txt, CHI_traits.txt, ...) define bespoke
        # advisor traits. They count as defined but stay unclassified, so they
        # never trip the slot check.
        defined = _parse_trait_names(self.mod_path, "country_leader")
        unit_leader_traits = _parse_trait_names(self.mod_path, "unit_leader")

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
                    expected = trait_slots.get(trait)
                    if expected and slot in SECTION_TO_SLOT.values():
                        if expected != slot:
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
