#!/usr/bin/env python3
"""Every MIO equipment group and every token an org lists under `equipment_type`
must resolve to a sprite. The engine draws a group as `GFX_<group>` and an
archetype or type category as `GFX_military_industrial_organization_<token>`;
a missing group sprite logs `GFX key GFX_<group> is missing` on every MIO
refresh and draws a blank icon."""

import os
import re
import sys
from typing import FrozenSet, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import extract_block_from_text
from sprite_index import build_sprite_index
from validate_gfx_references import _load_vanilla_sprite_manifest, _vanilla_gfx_files
from validator_common import BaseValidator, FileOpener, Severity, run_validator_main

GROUP_PATTERNS = ["common/equipment_groups/*.txt"]
ORG_PATTERNS = ["common/military_industrial_organization/organizations/*.txt"]
ICON_FILE = (
    "interface/military_industrial_organization/zMD_military_industrial_icons.gfx"
)
TYPE_SPRITE_PREFIX = "GFX_military_industrial_organization_"

TOP_LEVEL_DEF_RE = re.compile(r"^(\w+)\s*=\s*\{", re.MULTILINE)
# The lookbehind keeps `limit_to_equipment_type` out; trait limits carry no icon.
EQUIPMENT_TYPE_RE = re.compile(r"(?<![A-Za-z0-9_])equipment_type\s*=\s*\{([^{}]*)\}")
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

_MIN_SPRITE_INDEX = 1000


def parse_groups(content: str) -> List[Tuple[str, int]]:
    """(group token, line) for each top-level equipment group."""
    return [
        (m.group(1), content.count("\n", 0, m.start()) + 1)
        for m in TOP_LEVEL_DEF_RE.finditer(content)
    ]


def parse_org_equipment_types(content: str) -> List[Tuple[str, int]]:
    """(token, line) for every token in an org's own `equipment_type` block.

    An org that only carries `include = <org>` lists nothing itself; the
    included org is checked on its own.
    """
    found = []
    for m in TOP_LEVEL_DEF_RE.finditer(content):
        body, _ = extract_block_from_text(content, m.end() - 1)
        block = EQUIPMENT_TYPE_RE.search(body)
        if not block:
            continue
        line = content.count("\n", 0, m.end() + block.start()) + 1
        found.extend((token, line) for token in TOKEN_RE.findall(block.group(1)))
    return found


class Validator(BaseValidator):
    TITLE = "MIO EQUIPMENT ICONS"
    STAGED_EXTENSIONS = [".txt", ".gfx"]

    def _sprite_names(self) -> FrozenSet[str]:
        sprites: Set[str] = set(
            build_sprite_index(self.mod_path, gfx_only=True, pool_map=self._pool_map)
        )
        if not _vanilla_gfx_files():
            sprites.update(_load_vanilla_sprite_manifest())
        return frozenset(sprites)

    def _validate_icons(self):
        self._log_section("Checking MIO equipment group and equipment type icons...")

        sprites = self._sprite_names()
        if len(sprites) < _MIN_SPRITE_INDEX:
            self.log(
                f"  Only {len(sprites)} GFX sprites loaded: sprite definitions "
                "did not load; skipping the icon check",
                "warning",
            )
            return

        # ignore_staged: a .gfx edit changes what resolves for every group and
        # org, so both (small) sets are always re-checked in full.
        groups: List[Tuple[str, str, int]] = []
        for filepath in self._collect_files(GROUP_PATTERNS, ignore_staged=True):
            rel = os.path.relpath(filepath, self.mod_path)
            content = FileOpener.open_text_file(filepath, strip_comments_flag=True)
            groups.extend((token, rel, line) for token, line in parse_groups(content))
        group_tokens = frozenset(token for token, _, _ in groups)

        missing_groups = [
            (
                f"{token} has no GFX_{token} spriteType in any interface/*.gfx "
                f"(mod or vanilla); the engine logs 'GFX key GFX_{token} is "
                f"missing' and draws a blank icon. Add it to {ICON_FILE}",
                rel,
                line,
            )
            for token, rel, line in groups
            if f"GFX_{token}" not in sprites
        ]

        missing_types: List[Tuple[str, str, int]] = []
        checked_tokens = 0
        for filepath in self._collect_files(ORG_PATTERNS, ignore_staged=True):
            rel = os.path.relpath(filepath, self.mod_path)
            content = FileOpener.open_text_file(filepath, strip_comments_flag=True)
            for token, line in parse_org_equipment_types(content):
                checked_tokens += 1
                # A group is reported once at its definition, not per org.
                if token in group_tokens:
                    continue
                sprite = f"{TYPE_SPRITE_PREFIX}{token}"
                if sprite in sprites:
                    continue
                missing_types.append(
                    (
                        f"equipment_type {token} has no {sprite} spriteType in "
                        "any interface/*.gfx (mod or vanilla); the engine draws "
                        f"a blank icon. Add it to {ICON_FILE}",
                        rel,
                        line,
                    )
                )

        self.log(
            f"  Checked {len(groups)} equipment groups and {checked_tokens} "
            "equipment_type tokens"
        )
        self._report(
            missing_groups,
            "✓ Every MIO equipment group has a sprite",
            "MIO equipment groups with no GFX_<group> sprite:",
            Severity.ERROR,
            category="mio-equipment-group-icon",
        )
        self._report(
            missing_types,
            "✓ Every MIO equipment_type token has a sprite",
            "MIO equipment_type tokens with no sprite:",
            Severity.ERROR,
            category="mio-equipment-type-icon",
        )

    def run_validations(self):
        self._validate_icons()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate MIO equipment icons")
