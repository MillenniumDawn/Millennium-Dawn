#!/usr/bin/env python3
# Cross-reference every scientist trait against the medal sprite it resolves to.
# A trait with no sprite draws a missing-texture box on the character panel, and
# the `#TODO: ICON` markers in the trait file are hand-maintained, so they drift
# both ways: a new trait ships unmarked and unnoticed, and a marker outlives the
# art that resolved it.
import os
import re
import sys
from typing import List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import extract_block_from_text
from sprite_index import build_sprite_index
from validate_gfx_references import _load_vanilla_sprite_manifest
from validator_common import BaseValidator, FileOpener, Severity, run_validator_main

TRAIT_PATTERNS = ["common/scientist_traits/*.txt"]

# Traits are top-level, one block each, so the opener is column-anchored.
TRAIT_DEF_RE = re.compile(r"^(\w+)\s*=\s*\{", re.MULTILINE)
ICON_RE = re.compile(r"\bicon\s*=\s*(\S+)")
TODO_ICON_RE = re.compile(r"#.*\bTODO\b.*\bICON\b", re.IGNORECASE)

# MD's interface/unitleaderwindow.gfx replaces vanilla's, and that is the only
# vanilla file defining GFX_scientist_trait_*. Every vanilla name MD's copy does
# not re-declare is dead in game, so the sprite index has to be built MD-only;
# the vanilla manifest is consulted afterwards purely to tell a shadowed sprite
# (art ships, declaration lost) apart from one that exists nowhere.
_MIN_SPRITE_INDEX = 1000


def parse_trait_icons(content: str, raw: str) -> List[Tuple[str, str, int, bool]]:
    """Yield (token, expected_sprite, line, todo_marked) for each trait.

    `content` is comment-stripped for structure; `raw` is the same text with
    comments intact, so the `#TODO: ICON` marker on a trait's opening line can be
    read. `strip_comments` preserves newlines, so line numbers agree in both.

    The engine resolves a trait's icon to `icon = X` when declared and to
    `GFX_<token>` otherwise (common/scientist_traits/_documentation.md).
    """
    raw_lines = raw.split("\n")
    traits = []
    for match in TRAIT_DEF_RE.finditer(content):
        token = match.group(1)
        body, _ = extract_block_from_text(content, match.end() - 1)
        icon = ICON_RE.search(body)
        expected = icon.group(1).strip('"') if icon else f"GFX_{token}"
        line = content.count("\n", 0, match.start()) + 1
        opener = raw_lines[line - 1] if line <= len(raw_lines) else ""
        traits.append((token, expected, line, bool(TODO_ICON_RE.search(opener))))
    return traits


class Validator(BaseValidator):
    TITLE = "SCIENTIST TRAIT VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def _validate_trait_icons(self):
        self._log_section("Checking scientist trait icons...")

        # Built sequentially (no pool_map): a sub-second scan that a 'spawn' pool
        # worker failing to start could otherwise leave empty, which would flag
        # every trait as missing its icon.
        sprites = build_sprite_index(
            self.mod_path, gfx_only=True, include_vanilla=False
        )
        if len(sprites) < _MIN_SPRITE_INDEX:
            self.log(
                f"  Only {len(sprites)} GFX sprites loaded: sprite definitions "
                "did not load; skipping the icon check",
                "warning",
            )
            return
        vanilla = _load_vanilla_sprite_manifest()

        missing: List[Tuple[str, str, int]] = []
        shadowed: List[Tuple[str, str, int]] = []
        stale: List[Tuple[str, str, int]] = []
        checked = 0

        # ignore_staged: a .gfx edit changes what resolves for every trait, so
        # the whole (small) trait database is always re-checked.
        for filepath in self._collect_files(TRAIT_PATTERNS, ignore_staged=True):
            rel = os.path.relpath(filepath, self.mod_path)
            content = FileOpener.open_text_file(filepath, strip_comments_flag=True)
            raw = FileOpener.open_text_file(filepath)
            for token, expected, line, todo_marked in parse_trait_icons(content, raw):
                checked += 1
                if expected in sprites:
                    if todo_marked:
                        stale.append(
                            (
                                f"{token} is marked '#TODO: ICON' but {expected} is "
                                "defined; drop the marker",
                                rel,
                                line,
                            )
                        )
                elif expected in vanilla:
                    shadowed.append(
                        (
                            f"{token} resolves to {expected}, which only vanilla "
                            "interface/unitleaderwindow.gfx defines; MD replaces that "
                            "file, so re-declare the spriteType in MD's copy",
                            rel,
                            line,
                        )
                    )
                else:
                    missing.append(
                        (
                            f"{token} resolves to {expected}, which no "
                            "interface/*.gfx in the mod defines",
                            rel,
                            line,
                        )
                    )

        self.log(f"  Checked {checked} scientist trait icon references")
        self._report(
            missing,
            "✓ All scientist traits have a defined medal sprite",
            "Scientist traits with no medal sprite (draws a missing-texture box):",
            Severity.WARNING,
            category="missing-scientist-trait-icon",
        )
        self._report(
            shadowed,
            "✓ No scientist trait relies on a shadowed vanilla sprite",
            "Scientist traits whose sprite is declared only in the vanilla file MD replaces:",
            Severity.WARNING,
            category="shadowed-scientist-trait-icon",
        )
        self._report(
            stale,
            "✓ No stale '#TODO: ICON' markers",
            "Scientist traits marked '#TODO: ICON' whose sprite is already defined:",
            Severity.WARNING,
            category="stale-scientist-trait-icon-todo",
        )

    def run_validations(self):
        self._validate_trait_icons()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate scientist trait icons")
