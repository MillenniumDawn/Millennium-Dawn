#!/usr/bin/env python3
"""Validate Military-Industrial Organization definitions in Millennium Dawn.

Rules from .claude/docs/mio-reference.md + AGENTS.md:
  * org ids are TAG_organization_name (3-uppercase tag prefix); the shared
    GENERIC_/generic_ orgs are exempt
  * orgs pin their tag with allowed = { original_tag = TAG }
  * initial traits are named TAG_<...>_trait (or reference a shared
    generic_* trait from MD_generic_organization.txt)
  * trait grid x never exceeds 9 (negative x is the standard organic-layout
    first column; only the upper bound is a finding)
  * on_complete blocks are never empty (they need expenditure_for_mio_upgrade
    = yes or custom effects)
  * tree_header_text uses a localisation key, never a literal quoted string
  * tree header keys and trait/initial_trait names resolve to an English
    localisation key (TAG_<key> fallback included)
"""

import glob
import os
import re
from pathlib import Path
from typing import FrozenSet, List, Optional, Set, Tuple, Union

from validator_common import BaseValidator, run_validator_main

ORG_DIR = "common/military_industrial_organization/organizations"

# Top-level org definition: `TAG_name = {` at column 0.
ORG_DEF_RE = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*\{", re.MULTILINE)
TAG_PREFIX_RE = re.compile(r"^([A-Z]{3})_")
SHARED_PREFIXES = ("GENERIC_", "generic_")

ORIGINAL_TAG_RE = re.compile(r"\boriginal_tag\s*=\s*([A-Z][A-Z0-9_]{1,7})\b")
INITIAL_TRAIT_NAME_RE = re.compile(
    r"initial_trait\s*=\s*\{\s*name\s*=\s*([A-Za-z0-9_]+)"
)
POSITION_X_RE = re.compile(r"position\s*=\s*\{\s*x\s*=\s*(-?\d+)")
ON_COMPLETE_RE = re.compile(r"on_complete\s*=\s*\{([^{}]*)\}")

# The lookbehind keeps `text` from matching `tree_header_text` and `trait`
# from matching `initial_trait`.
HEADER_TEXT_RE = re.compile(r'(?<![A-Za-z0-9_])text\s*=\s*("[^"]*"|[^\s{}]+)')
NAME_RE = re.compile(r"(?<![A-Za-z0-9_])name\s*=\s*([A-Za-z0-9_]+)")
TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_])token\s*=\s*([A-Za-z0-9_]+)")

LocKeys = Union[FrozenSet[str], Set[str]]


def _block_spans(text: str) -> List[Tuple[int, int, str]]:
    """Yield (start, end, key) spans of every top-level `key = {` block."""
    spans = []
    for m in ORG_DEF_RE.finditer(text):
        depth = 1
        i = m.end()
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        spans.append((m.start(), i, m.group(1)))
    return spans


def _sub_blocks(body: str, keyword: str) -> List[Tuple[int, str]]:
    """Yield (start_offset_in_body, inner_text) for each `keyword = { ... }`."""
    pattern = re.compile(r"(?<![A-Za-z0-9_])" + keyword + r"\s*=\s*\{")
    blocks = []
    for m in pattern.finditer(body):
        depth = 1
        i = m.end()
        while i < len(body) and depth > 0:
            if body[i] == "{":
                depth += 1
            elif body[i] == "}":
                depth -= 1
            i += 1
        blocks.append((m.start(), body[m.end() : i - 1]))
    return blocks


class Validator(BaseValidator):
    TITLE = "MIOS"

    def _org_files(self) -> List[str]:
        pattern = str(Path(self.mod_path) / ORG_DIR / "*.txt")
        files = sorted(glob.glob(pattern))
        if not self.staged_only:
            return files
        staged = set(os.path.abspath(f) for f in (self.staged_files or []))
        return [f for f in files if os.path.abspath(f) in staged]

    def run_validations(self):
        files = self._org_files()
        if self.staged_only and not files:
            self.log("No staged MIO files found — skipping MIO validation", "warning")
            return

        loc_keys = self._load_localisation_keys()

        org_count = 0
        for filepath in files:
            try:
                text = Path(filepath).read_text(encoding="utf-8")
            except OSError:
                continue
            rel = Path(filepath).relative_to(self.mod_path).as_posix()
            for start, end, org_id in _block_spans(text):
                org_count += 1
                body = text[start:end]
                body_offset = text.count("\n", 0, start)
                self._check_id(org_id, rel, body_offset)
                self._check_allowed(org_id, body, rel, body_offset)
                self._check_initial_trait(org_id, body, rel, body_offset)
                self._check_positions(body, rel, body_offset)
                self._check_on_complete(body, rel, body_offset)
                self._check_header_text(org_id, body, rel, body_offset, loc_keys)
                self._check_trait_localisation(
                    org_id, body, rel, body_offset, loc_keys
                )

        self.log(f"  Scanned {len(files)} files | {org_count} organizations")

    @staticmethod
    def _is_shared(org_id: str) -> bool:
        return org_id.startswith(SHARED_PREFIXES)

    def _check_id(self, org_id: str, rel: str, body_offset: int):
        if self._is_shared(org_id):
            return
        if not TAG_PREFIX_RE.match(org_id):
            self.add_error(
                "org-id-format",
                f"MIO ID {org_id} must be TAG_organization_name",
                rel,
                body_offset + 1,
            )

    def _check_allowed(self, org_id: str, body: str, rel: str, body_offset: int):
        if self._is_shared(org_id):
            return
        m = TAG_PREFIX_RE.match(org_id)
        if not m:
            return
        tag = m.group(1)
        if not any(m2.group(1) == tag for m2 in ORIGINAL_TAG_RE.finditer(body)):
            self.add_error(
                "org-allowed-tag",
                f"MIO {org_id} must pin its tag with "
                f"allowed = {{ original_tag = {tag} }}",
                rel,
                body_offset + 1,
            )

    def _check_initial_trait(self, org_id: str, body: str, rel: str, body_offset: int):
        m = INITIAL_TRAIT_NAME_RE.search(body)
        if not m:
            return
        name = m.group(1)
        line = body_offset + body.count("\n", 0, m.start()) + 1
        if name.startswith("generic_"):
            return
        prefix = org_id.split("_", 1)[0]
        if not name.startswith(prefix + "_") or not name.endswith("_trait"):
            self.add_warning(
                "initial-trait-name",
                f"initial_trait name '{name}' must be {prefix}_<name>_trait "
                f"(e.g. {prefix}_norinco_trait)",
                rel,
                line,
            )

    def _check_positions(self, body: str, rel: str, body_offset: int):
        for m in POSITION_X_RE.finditer(body):
            x = int(m.group(1))
            if x > 9:
                self.add_warning(
                    "trait-x-bounds",
                    f"trait position x = {x} must stay inside 0..9",
                    rel,
                    body_offset + body.count("\n", 0, m.start()) + 1,
                )

    @staticmethod
    def _owner_tag(org_id: str) -> Optional[str]:
        m = TAG_PREFIX_RE.match(org_id)
        return m.group(1) if m else None

    @staticmethod
    def _resolves(key: str, tag: Optional[str], loc_keys: LocKeys) -> bool:
        """The engine prefers TAG_<key> and falls back to the bare key."""
        return key in loc_keys or (tag is not None and f"{tag}_{key}" in loc_keys)

    def _check_header_text(
        self, org_id: str, body: str, rel: str, body_offset: int, loc_keys: LocKeys
    ):
        tag = self._owner_tag(org_id)
        for start, inner in _sub_blocks(body, "tree_header_text"):
            m = HEADER_TEXT_RE.search(inner)
            if not m:
                continue
            value = m.group(1)
            line = body_offset + body.count("\n", 0, start) + 1
            if value.startswith('"'):
                self.add_error(
                    "header-text-not-tokenized",
                    f"tree_header_text uses a literal string {value}; use a "
                    f"localisation key (e.g. {org_id}_mio_header_<slug>)",
                    rel,
                    line,
                )
            elif not self._resolves(value, tag, loc_keys):
                self.add_error(
                    "header-text-loc-missing",
                    f"tree_header_text key '{value}' has no English "
                    "localisation entry",
                    rel,
                    line,
                )

    def _check_trait_localisation(
        self, org_id: str, body: str, rel: str, body_offset: int, loc_keys: LocKeys
    ):
        tag = self._owner_tag(org_id)
        blocks = _sub_blocks(body, "initial_trait") + _sub_blocks(body, "trait")
        for start, inner in blocks:
            name = NAME_RE.search(inner)
            token = TOKEN_RE.search(inner)
            line = body_offset + body.count("\n", 0, start) + 1
            if name:
                key = name.group(1)
                if self._resolves(key, tag, loc_keys):
                    continue
                message = f"trait name '{key}' has no English localisation entry"
            elif token:
                # Nameless traits fall back to <org_id>_<token>.
                key = f"{org_id}_{token.group(1)}"
                if self._resolves(key, tag, loc_keys):
                    continue
                message = (
                    f"trait '{token.group(1)}' has no name and no '{key}' "
                    f"localisation key; add name = {token.group(1)} plus a loc entry"
                )
            else:
                continue
            self.add_warning("trait-loc-missing", message, rel, line)

    def _check_on_complete(self, body: str, rel: str, body_offset: int):
        for m in ON_COMPLETE_RE.finditer(body):
            if m.group(1).strip():
                continue
            line = body_offset + body.count("\n", 0, m.start()) + 1
            self.add_error(
                "on-complete-empty",
                "on_complete is empty; add expenditure_for_mio_upgrade = yes "
                "or custom effects",
                rel,
                line,
            )


if __name__ == "__main__":
    run_validator_main(Validator, "Validate MIO organization definitions")
