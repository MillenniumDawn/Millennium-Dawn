#!/usr/bin/env python3
# Check the `name =` of every bonus-granting effect against the block that grants
# it. The name is the loc key the engine prints as the *source* of the bonus, so
# the convention is that it identifies the granting object: the focus id in a
# focus reward, the decision token in a decision effect, the event id in an
# event, the trait token in a MIO trait. A technology category token passes a
# bare loc-key test (every CAT_ name is localised) while labelling the row with
# the tech field instead of the source, and two objects sharing one category name
# collapse into one indistinguishable entry.
import os
import re
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import FileOpener
from validate_tech_categories import _TAGS_GLOB, load_known_categories
from validator_common import (
    BaseValidator,
    Issue,
    Severity,
    _child_blocks,
    run_validator_main,
)

# The effects whose `name =` labels the bonus source in-game. Vanilla treats the
# parameter as optional on add_design_template_bonus and add_equipment_bonus (the
# latter can fall back to `project =`); MD wants an explicit source name in every
# case, so all six are required here.
_EFFECTS = frozenset(
    {
        "add_tech_bonus",
        "add_equipment_bonus",
        "add_design_template_bonus",
        "add_doctrine_cost_reduction",
        "add_daily_mastery",
        "add_mastery_bonus",
    }
)

# Blocks that name the object granting the bonus.
_FOCUS_BLOCKS = frozenset({"focus", "shared_focus", "joint_focus"})
_EVENT_BLOCKS = frozenset(
    {
        "country_event",
        "news_event",
        "state_event",
        "unit_leader_event",
        "operative_leader_event",
    }
)

_NAME_FIELD_RE = re.compile(r"\bname\s*=\s*(\S+)")
_ID_FIELD_RE = re.compile(r"\bid\s*=\s*(\S+)")
_TOKEN_FIELD_RE = re.compile(r"\btoken\s*=\s*(\S+)")

_VALIDATE_PATTERNS = [
    "common/**/*.txt",
    "events/**/*.txt",
]

_DECISIONS_DIR = "common/decisions/"
_MIO_DIR = "common/military_industrial_organization/"


def _direct_field(
    text: str,
    body_start: int,
    body_end: int,
    pattern: re.Pattern,
    children: List[Tuple[str, int, int, int]],
) -> Optional[str]:
    """First match of *pattern* in the body that is not inside a nested block.

    A focus body carries `id = X` at its own level but its `available` and
    `completion_reward` children carry unrelated `name =`/`id =` lines, so a
    plain search over the body text reads the wrong token.
    """
    for m in pattern.finditer(text, body_start, body_end):
        if any(ns <= m.start() <= be for _, ns, _, be in children):
            continue
        return m.group(1).strip('"')
    return None


def _owner_for(
    name: str,
    text: str,
    body_start: int,
    body_end: int,
    children: List[Tuple[str, int, int, int]],
    depth: int,
    in_decisions: bool,
    in_mio: bool,
) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
    """(kind, token, accepted names) when this block names a bonus source."""
    if name in _FOCUS_BLOCKS:
        token = _direct_field(text, body_start, body_end, _ID_FIELD_RE, children)
        return ("focus", token, (token,)) if token else None
    if name in _EVENT_BLOCKS:
        token = _direct_field(text, body_start, body_end, _ID_FIELD_RE, children)
        # MD labels an event's bonus with either the event id or its title key.
        return ("event", token, (token, f"{token}.t")) if token else None
    if in_mio and name == "trait":
        token = _direct_field(text, body_start, body_end, _TOKEN_FIELD_RE, children)
        return ("MIO trait", token, (token,)) if token else None
    # A decision id sits one level inside its category block.
    if in_decisions and depth == 1:
        return ("decision", name, (name,))
    return None


def _walk(
    text: str,
    start: int,
    end: int,
    depth: int,
    owner: Optional[Tuple[str, str, Tuple[str, ...]]],
    in_decisions: bool,
    in_mio: bool,
    out: List[
        Tuple[str, Optional[str], Optional[str], Optional[str], Tuple[str, ...], int]
    ],
) -> None:
    """Collect every bonus effect under text[start:end], tagged with its owner.

    Records are (effect, name, owner_kind, owner_token, accepted, offset); the
    innermost enclosing owner wins, and stays None where the block has no id
    convention (scripted effects, faction goals, subdoctrines).
    """
    for name, name_start, body_start, body_end in _child_blocks(text, start, end):
        if name in _EFFECTS:
            value = _direct_field(
                text,
                body_start,
                body_end,
                _NAME_FIELD_RE,
                _child_blocks(text, body_start, body_end),
            )
            kind, token, accepted = owner if owner else (None, None, ())
            out.append((name, value, kind, token, accepted, name_start))
            continue
        children = _child_blocks(text, body_start, body_end)
        found = _owner_for(
            name, text, body_start, body_end, children, depth, in_decisions, in_mio
        )
        _walk(
            text,
            body_start,
            body_end,
            depth + 1,
            found or owner,
            in_decisions,
            in_mio,
            out,
        )


def _scan_file(
    args,
) -> List[
    Tuple[str, Optional[str], Optional[str], Optional[str], Tuple[str, ...], str, int]
]:
    """Worker: every bonus effect in one file, with its owner and line number."""
    filepath, mod_path = args
    try:
        text = FileOpener.open_text_file(filepath, strip_comments_flag=True)
    except (OSError, UnicodeDecodeError):
        return []
    # Cheap prefilter: only ~150 of the ~6000 scanned files grant a bonus.
    if not any(effect in text for effect in _EFFECTS):
        return []
    rel = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    records: List[
        Tuple[str, Optional[str], Optional[str], Optional[str], Tuple[str, ...], int]
    ] = []
    _walk(
        text,
        0,
        len(text),
        0,
        None,
        rel.startswith(_DECISIONS_DIR),
        rel.startswith(_MIO_DIR),
        records,
    )
    return [
        (effect, value, kind, token, accepted, rel, text.count("\n", 0, offset) + 1)
        for effect, value, kind, token, accepted, offset in records
    ]


class Validator(BaseValidator):
    TITLE = "BONUS SOURCE NAME VALIDATION"

    def __init__(self, mod_path: str, **kwargs):
        self.name_not_owner_id = kwargs.pop("name_not_owner_id", False)
        super().__init__(mod_path, **kwargs)

    def validate_bonus_names(self):
        self._log_section("Checking bonus source names...")

        files = self._collect_files(_VALIDATE_PATTERNS)
        self.log(f"  Checking {len(files)} files...")
        batches = self._pool_map(
            _scan_file, [(f, self.mod_path) for f in files], chunksize=30
        )
        loc_keys = self._load_localisation_keys()
        categories = self.cached(
            "tech_categories",
            lambda: load_known_categories(
                self._collect_files([_TAGS_GLOB], ignore_staged=True)
            ),
        )

        results: List[Issue] = []
        for batch in batches:
            for effect, name, kind, token, accepted, rel, line in batch:
                where = f" in {kind} '{token}'" if token else ""
                hint = f" (use name = {accepted[0]})" if accepted else ""
                if name is None:
                    results.append(
                        self._issue(
                            "bonus-name-missing",
                            f"{effect}{where} has no name = parameter — players"
                            f" see no source for the bonus{hint}",
                            rel,
                            line,
                        )
                    )
                elif "[" in name:
                    # Runtime-resolved loc: the value is only known in-game.
                    continue
                elif name in categories:
                    results.append(
                        self._issue(
                            "bonus-name-is-category",
                            f"{effect} name '{name}'{where} is a technology"
                            " category, not a bonus source — the row names the"
                            f" tech field instead of the source{hint}",
                            rel,
                            line,
                        )
                    )
                elif name not in loc_keys:
                    results.append(
                        self._issue(
                            "bonus-name-missing-loc",
                            f"{effect} name '{name}'{where} has no localisation"
                            f" key (typo?){hint}",
                            rel,
                            line,
                        )
                    )
                elif self.name_not_owner_id and accepted and name not in accepted:
                    results.append(
                        self._issue(
                            "bonus-name-not-owner-id",
                            f"{effect} name '{name}'{where} does not name the"
                            f" granting {kind} — intentional only when the bonus"
                            " is deliberately shared across objects",
                            rel,
                            line,
                        )
                    )

        self._report(
            results,
            "All bonus effects name their source",
            "Bonus effects whose name does not identify the granting object:",
            severity=Severity.WARNING,
            category="bonus-name",
        )

    @staticmethod
    def _issue(category: str, message: str, rel: str, line: int) -> Issue:
        return Issue(
            severity=Severity.WARNING,
            category=category,
            message=message,
            file=rel,
            line=line,
        )

    def run_validations(self):
        self.validate_bonus_names()


def _add_extra_args(parser):
    parser.add_argument(
        "--name-not-owner-id",
        action="store_true",
        dest="name_not_owner_id",
        help="Flag bonus names that are localised but do not match the granting"
        " focus/decision/event/MIO trait token",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate bonus source names in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
