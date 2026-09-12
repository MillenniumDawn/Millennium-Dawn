"""Validate political-party localisation against the MD party standard.

The politics view never reads `TAG.conservatism` directly. It calls
`[conservatism_L]`, which resolves through a per-tag switch in
`common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt`, so
a loc key with no hook there renders the generic label and the written party
name is dead. That pairing, plus the `£sprite (ABBRV) - Party Name` /
`(Ideology Group) - Name (Native: ..., ABBRV)\\n\\nBody` shapes, is the standard
documented in `.claude/docs/party-loc-reference.md`.

Only about a tenth of the 306 tags in the file meet it today, so a repo-wide
report would bury every other finding. The default run therefore audits only the
tags whose keys or hooks the branch touched: touch one `GRE.*` line and all of
Greece is checked, leave it alone and Greece is silent. `--all` sweeps the
backlog and `--tag` audits one country on demand.

Missing tags, missing slots and missing `_desc`/`_icon` keys are deliberately
not reported: an absent slot is supposed to fall through to the generic label
rather than have a party invented for it. `£sprite` resolution is not checked
either — validate_gfx_references.py already scans every `.yml` for undefined and
miscased sprite references.
"""

import os
import re
import subprocess
import sys
from typing import Dict, List, NamedTuple, Optional, Sequence, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import PARTY_SLOT_NAMES, read_text_strict, strip_comments
from validator_common import BaseValidator, Issue, Severity, run_validator_main

LOC_PATH = "localisation/english/MD_politics_view_parties_l_english.yml"
HOOK_PATH = "common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt"

# Longest first, so `Neutral_conservatism` is never truncated to a shorter slot.
_SLOTS: Tuple[str, ...] = tuple(
    sorted(set(PARTY_SLOT_NAMES.values()), key=len, reverse=True)
)
_SLOTS_LOWER: Dict[str, str] = {slot.lower(): slot for slot in _SLOTS}

# Royal houses carry no abbreviation (`GRE.Monarchist`, `MOR.Monarchist`).
_NO_ABBREVIATION_SLOTS = frozenset({"Monarchist"})

_LOC_LINE_RE = re.compile(r'^(\s*)([\w.\-]+):\d*\s*"(.*)"\s*$')
_NAME_RE = re.compile(r"^£[\w.\-]+ \([^()]+\) - .+$")
_NAME_NO_ABBREVIATION_RE = re.compile(r"^£[\w.\-]+ .+$")
_DESC_HEADER_RE = re.compile(r"^\([^()]+\) - ")
_SPRITE_RE = re.compile(r"^£[\w.\-]+")

_HOOK_KEY_RE = re.compile(r"localization_key\s*=\s*([\w.\-]+)")
_DEFINED_TEXT_RE = re.compile(r"defined_text\s*=\s*\{")
# The lookbehind is load-bearing: a bare `text\s*=\s*\{` also matches the
# `defined_text = {` that opens each block, and brace-matching from there
# swallows every entry in it.
_TEXT_ENTRY_RE = re.compile(r"(?<![\w])text\s*=\s*\{")
_TRIGGER_RE = re.compile(r"trigger\s*=\s*\{")
_BLOCK_NAME_RE = re.compile(r"name\s*=\s*(\w+)")
_LONE_ORIGINAL_TAG_RE = re.compile(r"^original_tag\s*=\s*(\w+)$")
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.*) b/(.*)$")


class PartyKey(NamedTuple):
    """One `TAG.slot[variant][_desc|_icon]` line in the party loc file."""

    line: int
    key: str
    tag: str
    slot: str
    variant: str
    kind: str
    value: str


class Hook(NamedTuple):
    """One `localization_key = TAG.something` reference in the scripted loc."""

    line: int
    key: str


def _match_brace(text: str, open_pos: int) -> int:
    """Index just past the `}` closing the `{` at open_pos."""
    depth = 1
    pos = open_pos + 1
    while depth and pos < len(text):
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
        pos += 1
    return pos


def _split_kind(rest: str) -> Tuple[str, str]:
    for suffix, kind in (("_desc", "desc"), ("_icon", "icon")):
        if rest.endswith(suffix):
            return kind, rest[: -len(suffix)]
    return "name", rest


def _match_slot(base: str) -> Optional[Tuple[str, str]]:
    """(slot, variant) for an exact-case slot prefix, else None."""
    for slot in _SLOTS:
        if base.startswith(slot):
            return slot, base[len(slot) :]
    return None


def _match_slot_ignoring_case(base: str) -> Optional[str]:
    lowered = base.lower()
    best: Optional[str] = None
    for slot_lower, slot in _SLOTS_LOWER.items():
        if lowered.startswith(slot_lower) and (best is None or len(slot) > len(best)):
            best = slot
    return best


def parse_party_keys(text: str) -> Tuple[List[PartyKey], List[Tuple[int, str, str]]]:
    """Split the loc file into recognised party keys and miscased ones.

    The second list is `(line, key, intended_slot)` for keys whose slot matches
    only case-insensitively — those are dead, since the hook spells it correctly.
    Keys under no slot at all are bespoke (`ITA.forza_nuova_loc_key`) and are
    returned in neither list.
    """
    keys: List[PartyKey] = []
    miscased: List[Tuple[int, str, str]] = []
    for line_no, line in enumerate(text.split("\n"), 1):
        match = _LOC_LINE_RE.match(line)
        if not match:
            continue
        key, value = match.group(2), match.group(3)
        if "." not in key:
            continue
        tag, rest = key.split(".", 1)
        # The generic.* block is the fallback label set, not a country's parties.
        if tag == "generic":
            continue
        kind, base = _split_kind(rest)
        matched = _match_slot(base)
        if matched is None:
            intended = _match_slot_ignoring_case(base)
            if intended is not None:
                miscased.append((line_no, key, intended))
            continue
        slot, variant = matched
        keys.append(PartyKey(line_no, key, tag, slot, variant, kind, value))
    return keys, miscased


def parse_hooks(text: str) -> List[Hook]:
    return [
        Hook(text.count("\n", 0, m.start()) + 1, m.group(1))
        for m in _HOOK_KEY_RE.finditer(text)
    ]


def find_duplicate_hooks(text: str) -> List[Tuple[int, str, str]]:
    """(line, block_name, tag) for a repeated unconditional `original_tag` gate.

    The switch takes the first match, so a second entry for the same tag in the
    same `defined_text` can never fire.
    """
    duplicates: List[Tuple[int, str, str]] = []
    for block in _DEFINED_TEXT_RE.finditer(text):
        block_end = _match_brace(text, block.end() - 1)
        name_match = _BLOCK_NAME_RE.search(text, block.end(), block_end)
        block_name = name_match.group(1) if name_match else "?"
        seen: Set[str] = set()
        for entry in _TEXT_ENTRY_RE.finditer(text, block.end(), block_end):
            entry_end = _match_brace(text, entry.end() - 1)
            trigger = _TRIGGER_RE.search(text, entry.end(), entry_end)
            if trigger is None:
                continue
            trigger_end = _match_brace(text, trigger.end() - 1)
            tag_match = _LONE_ORIGINAL_TAG_RE.match(
                text[trigger.end() : trigger_end - 1].strip()
            )
            if tag_match is None:
                continue
            tag = tag_match.group(1)
            if tag in seen:
                line = text.count("\n", 0, entry.start()) + 1
                duplicates.append((line, block_name, tag))
            seen.add(tag)
    return duplicates


def _parse_added_lines(diff_text: str) -> Set[int]:
    """Added head-side line numbers from unified diff hunk headers."""
    lines: Set[int] = set()
    for line in diff_text.splitlines():
        hunk = _HUNK_RE.match(line)
        if hunk:
            start = int(hunk.group(1))
            count = int(hunk.group(2)) if hunk.group(2) else 1
            lines.update(range(start, start + count))
    return lines


def _patch_diff_lines(diff_text: str, rel_path: str) -> Optional[Set[int]]:
    """Added head-side line numbers for one path in a multi-file patch."""
    target_hunks: List[str] = []
    current_path: Optional[str] = None
    found_file = False
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            match = _DIFF_HEADER_RE.match(line)
            if match is None:
                return None
            current_path = match.group(2)
            found_file = True
            continue
        if line.startswith("@@"):
            if current_path is None or _HUNK_RE.match(line) is None:
                return None
            if current_path == rel_path:
                target_hunks.append(line)
    if not found_file and diff_text.strip():
        return None
    return _parse_added_lines("\n".join(target_hunks))


def _read_patch(mod_path: str, path: str) -> Optional[str]:
    patch_path = path if os.path.isabs(path) else os.path.join(mod_path, path)
    try:
        return read_text_strict(patch_path)
    except (OSError, UnicodeDecodeError):
        return None


def _git_diff(mod_path: str, args: List[str]) -> Optional[Set[int]]:
    """Added line numbers from one `git diff -U0`, or None if it did not run."""
    try:
        result = subprocess.run(
            ["git", "diff", "-U0"] + args,
            cwd=mod_path,
            capture_output=True,
            check=True,
            timeout=15,
        )
        diff_text = result.stdout.decode("utf-8")
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError):
        return None
    return _parse_added_lines(diff_text)


def _git_diff_lines(mod_path: str, rel_path: str) -> Optional[Set[int]]:
    """Added line numbers for one file, or None when git cannot be reached.

    Mirrors the fallback order in shared_utils.get_staged_files: what is staged
    in a pre-commit run, otherwise the branch diff against main in CI. A repo
    with no `main` ref, such as a fresh checkout of a fork's default branch,
    only means nothing is in scope — it is not a reason to stop reporting.
    """
    staged = _git_diff(mod_path, ["--cached", "--", rel_path])
    if staged is None:
        return None
    if staged:
        return staged
    return _git_diff(mod_path, ["main...HEAD", "--", rel_path])


class Validator(BaseValidator):
    TITLE = "PARTY LOCALISATION VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def __init__(self, mod_path: str, **kwargs):
        self.scan_all: bool = bool(kwargs.pop("scan_all", False))
        self.only_tags: Sequence[str] = tuple(kwargs.pop("tag", None) or ())
        super().__init__(mod_path, **kwargs)

    def _read(self, rel_path: str) -> Optional[str]:
        path = os.path.join(self.mod_path, rel_path)
        if not os.path.isfile(path):
            return None
        try:
            return read_text_strict(path)
        except (OSError, UnicodeDecodeError):
            return None

    def _scoped_tags(
        self, keys: List[PartyKey], hooks: List[Hook]
    ) -> Optional[Set[str]]:
        """Tags to audit, or None to audit everything."""
        if self.scan_all:
            return None
        if self.only_tags:
            return set(self.only_tags)

        supplied_diff = os.environ.get("MD_PARTY_LOC_DIFF")
        if supplied_diff:
            diff_text = _read_patch(self.mod_path, supplied_diff)
            loc_lines = (
                _patch_diff_lines(diff_text, LOC_PATH)
                if diff_text is not None
                else None
            )
            hook_lines = (
                _patch_diff_lines(diff_text, HOOK_PATH)
                if diff_text is not None
                else None
            )
        else:
            loc_lines = hook_lines = None

        if loc_lines is None:
            loc_lines = _git_diff_lines(self.mod_path, LOC_PATH)
        if hook_lines is None:
            hook_lines = _git_diff_lines(self.mod_path, HOOK_PATH)
        if loc_lines is None or hook_lines is None:
            self.log("  diff scope unavailable — auditing all tags", "warning")
            return None

        tags = {key.tag for key in keys if key.line in loc_lines}
        tags.update(
            hook.key.split(".", 1)[0]
            for hook in hooks
            if hook.line in hook_lines and "." in hook.key
        )
        return tags

    def validate_party_localisation(self):
        self._log_section(
            "Checking political-party localisation against the standard..."
        )

        loc_text = self._read(LOC_PATH)
        hook_text = self._read(HOOK_PATH)
        if loc_text is None or hook_text is None:
            self.log("  Party localisation files not present — nothing to check")
            return
        hook_text = strip_comments(hook_text)

        keys, miscased = parse_party_keys(loc_text)
        hooks = parse_hooks(hook_text)
        scope = self._scoped_tags(keys, hooks)
        if scope is not None and not scope:
            self.log("  No party localisation changed — nothing in scope")
            return
        if scope is None:
            self.log(f"  Checking all {len({key.tag for key in keys})} tags...")
        else:
            self.log(
                f"  Checking {len(scope)} changed tag(s): {', '.join(sorted(scope))}"
            )

        in_scope = [key for key in keys if scope is None or key.tag in scope]
        hooked = {hook.key for hook in hooks}
        defined = {key.key for key in keys}
        names = {
            (key.tag, key.slot, key.variant): key for key in keys if key.kind == "name"
        }

        self._report(
            self._check_names(in_scope),
            "All party names use the £sprite (ABBRV) - Name format",
            "Party names that do not follow the naming standard:",
        )
        self._report(
            self._check_descriptions(in_scope),
            "All party descriptions follow the description standard",
            "Party descriptions that do not follow the standard:",
        )
        self._report(
            self._check_key_pairing(in_scope, names),
            "Every party _desc and _icon key has a matching name key",
            "Party keys with no name key to attach to:",
        )
        self._report(
            self._check_hooks(in_scope, hooked),
            "Every party loc key is wired into the politics view",
            "Party loc keys with no scripted-localisation hook:",
        )
        self._report(
            self._check_orphan_hooks(hooks, defined, scope),
            "Every party hook points at a key that exists",
            "Party hooks pointing at a missing loc key:",
        )
        self._report(
            self._check_miscased(miscased, scope),
            "Every party loc key spells its subideology correctly",
            "Party loc keys whose subideology is miscased:",
        )
        self._report(
            self._check_duplicate_hooks(hook_text, scope),
            "No party hook block gates the same tag twice",
            "Party hook blocks that gate the same tag twice:",
        )

    def _warning(self, category: str, message: str, path: str, line: int) -> Issue:
        return Issue(
            severity=Severity.WARNING,
            category=category,
            message=message,
            file=path,
            line=line,
        )

    def _check_names(self, keys: List[PartyKey]) -> List[Issue]:
        results = []
        for key in keys:
            if key.kind != "name":
                continue
            if key.slot in _NO_ABBREVIATION_SLOTS:
                if _NAME_NO_ABBREVIATION_RE.match(key.value):
                    continue
                expected = '"£sprite Name"'
            else:
                if _NAME_RE.match(key.value):
                    continue
                expected = '"£sprite (ABBRV) - Party Name"'
            results.append(
                self._warning(
                    "party-loc-name-format",
                    f"{key.key} should read {expected}",
                    LOC_PATH,
                    key.line,
                )
            )
        return results

    def _check_descriptions(self, keys: List[PartyKey]) -> List[Issue]:
        results = []
        for key in keys:
            if key.kind != "desc":
                continue
            if not key.value.strip():
                results.append(
                    self._warning(
                        "party-loc-empty-desc",
                        f"{key.key} is an empty string, so the party has no"
                        " description in the politics view",
                        LOC_PATH,
                        key.line,
                    )
                )
                continue
            if not _DESC_HEADER_RE.match(key.value):
                results.append(
                    self._warning(
                        "party-loc-desc-header",
                        f"{key.key} should open with"
                        ' "(Ideology Group) - Party Name (Native: Nativename, ABBRV)"',
                        LOC_PATH,
                        key.line,
                    )
                )
            if "\\n\\n" not in key.value:
                results.append(
                    self._warning(
                        "party-loc-desc-body",
                        f"{key.key} has no \\n\\n separating its header from the"
                        " description body",
                        LOC_PATH,
                        key.line,
                    )
                )
        return results

    def _check_key_pairing(
        self, keys: List[PartyKey], names: Dict[Tuple[str, str, str], PartyKey]
    ) -> List[Issue]:
        results = []
        for key in keys:
            if key.kind == "name":
                continue
            name = names.get((key.tag, key.slot, key.variant))
            if name is None:
                results.append(
                    self._warning(
                        "party-loc-key-without-name",
                        f"{key.key} has no {key.tag}.{key.slot}{key.variant} name key",
                        LOC_PATH,
                        key.line,
                    )
                )
                continue
            if key.kind != "icon":
                continue
            sprite = _SPRITE_RE.match(name.value)
            if sprite and key.value.strip() != sprite.group(0):
                results.append(
                    self._warning(
                        "party-loc-icon-sprite-mismatch",
                        f"{key.key} is {key.value.strip()} but {name.key} shows"
                        f" {sprite.group(0)}, so the name and its icon disagree",
                        LOC_PATH,
                        key.line,
                    )
                )
        return results

    def _check_hooks(self, keys: List[PartyKey], hooked: Set[str]) -> List[Issue]:
        suffix = {"name": "_L", "desc": "_L_desc", "icon": "_L_icon"}
        results = []
        for key in keys:
            if key.key in hooked:
                continue
            results.append(
                self._warning(
                    "party-loc-missing-hook",
                    f"{key.key} has no hook in {key.slot}{suffix[key.kind]}, so the"
                    " politics view renders the generic entry instead",
                    LOC_PATH,
                    key.line,
                )
            )
        return results

    def _check_orphan_hooks(
        self, hooks: List[Hook], defined: Set[str], scope: Optional[Set[str]]
    ) -> List[Issue]:
        results = []
        for hook in hooks:
            if "." not in hook.key:
                continue
            tag = hook.key.split(".", 1)[0]
            if tag == "generic" or (scope is not None and tag not in scope):
                continue
            if (
                hook.key in defined
                or _match_slot(_split_kind(hook.key.split(".", 1)[1])[1]) is None
            ):
                continue
            results.append(
                self._warning(
                    "party-loc-orphan-hook",
                    f"{hook.key} is hooked but never defined, so the politics view"
                    " renders the raw key",
                    HOOK_PATH,
                    hook.line,
                )
            )
        return results

    def _check_miscased(
        self, miscased: List[Tuple[int, str, str]], scope: Optional[Set[str]]
    ) -> List[Issue]:
        results = []
        for line, key, intended in miscased:
            if scope is not None and key.split(".", 1)[0] not in scope:
                continue
            results.append(
                self._warning(
                    "party-loc-slot-case",
                    f"{key} spells the subideology differently from {intended} —"
                    " HOI4 is case-sensitive on Linux, so this key is dead",
                    LOC_PATH,
                    line,
                )
            )
        return results

    def _check_duplicate_hooks(
        self, hook_text: str, scope: Optional[Set[str]]
    ) -> List[Issue]:
        results = []
        for line, block_name, tag in find_duplicate_hooks(hook_text):
            if scope is not None and tag not in scope:
                continue
            results.append(
                self._warning(
                    "party-loc-duplicate-hook",
                    f"{block_name} already gates original_tag = {tag} above, so this"
                    " entry can never be reached",
                    HOOK_PATH,
                    line,
                )
            )
        return results

    def run_validations(self):
        self.validate_party_localisation()


def _add_extra_args(parser):
    parser.add_argument(
        "--all",
        action="store_true",
        dest="scan_all",
        help="Audit every tag, not just the ones the branch changed",
    )
    parser.add_argument(
        "--tag",
        action="append",
        metavar="TAG",
        help="Audit this tag regardless of the diff (repeatable)",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate political-party localisation in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
