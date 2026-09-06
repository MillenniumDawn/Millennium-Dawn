"""Migrate startup defaults into country and state history files."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[1]
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))
if str(THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(THIS_DIR.parent))

from shared_utils import (
    blank_quoted_strings,
    extract_block_from_text,
    flat_block_text,
    iter_direct_child_blocks,
    iter_flat_offsets,
    read_text_strict,
    strip_comments,
    strip_inline_comment,
)

CONTINENT_DEFAULTS = {
    "africa": 550,
    "middle_east": 550,
    "north_america": 550,
    "south_america": 550,
    "asia": 650,
    "australia": 650,
    "oceania": 650,
    "europe": 1000,
}
BACKING_IDEAS = {
    "gold_standard_back",
    "silver_standard",
    "bi_metal_standard",
    "no_currency_backing",
}
_DATE_RE = re.compile(r"2000\.1\.1\s*=\s*\{")
_TAG_BLOCK_RE = re.compile(r"\b[A-Z0-9]{3}\s*=\s*\{")
_NUMBER_RE = r"[-+]?\d+(?:\.\d+)?"


class MigrationError(ValueError):
    """Raised when history cannot be migrated without guessing."""


def _comment_mask(text: str) -> str:
    """Blank comments without changing offsets used for source edits."""
    result: List[str] = []
    for line in text.splitlines(keepends=True):
        code = strip_inline_comment(line)
        result.append(
            code + "".join("\n" if char == "\n" else " " for char in line[len(code) :])
        )
    return "".join(result)


def _direct_blocks(
    text: str, opener: re.Pattern[str]
) -> Iterator[Tuple[str, int, int]]:
    masked = blank_quoted_strings(_comment_mask(text))
    for _match, open_pos, close_pos in iter_direct_child_blocks(masked, opener):
        _, end_pos = extract_block_from_text(masked, open_pos)
        if end_pos < 0:
            raise MigrationError("unbalanced history block")
        yield text[open_pos + 1 : close_pos], open_pos, close_pos


def _first_direct_block(text: str, opener: re.Pattern[str]) -> Tuple[str, int, int]:
    return next(_direct_blocks(text, opener), ("", -1, -1))


def _initial_date_block(text: str) -> Tuple[str, int, int]:
    return _first_direct_block(text, _DATE_RE)


def _named_blocks(text: str, name: str) -> List[Tuple[str, int, int]]:
    return list(_direct_blocks(text, re.compile(rf"\b{re.escape(name)}\s*=\s*\{{")))


def _country_tag(path: Path) -> str:
    match = re.match(r"([A-Z0-9]{3})\s+-\s+", path.name)
    if match is None:
        raise MigrationError(f"{path}: filename does not begin with a three-letter tag")
    return match.group(1)


def _load_continents(root: Path) -> Dict[int, str]:
    text = strip_comments(read_text_strict(str(root / "map" / "continent.txt")))
    body, _, _ = _first_direct_block(text, re.compile(r"\bcontinents\s*=\s*\{"))
    if not body:
        raise MigrationError("map/continent.txt has no continents block")
    names = re.findall(r"\b[a-z_]+\b", body)
    if not names:
        raise MigrationError("map/continent.txt has no continent names")
    return {index + 1: name for index, name in enumerate(names)}


def _load_province_continents(root: Path) -> Dict[int, str]:
    names = _load_continents(root)
    result: Dict[int, str] = {}
    definition = root / "map" / "definition.csv"
    with open(definition, "r", encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle, delimiter=";"):
            if len(row) < 8:
                continue
            try:
                province, continent = int(row[0]), int(row[7])
            except ValueError:
                continue
            if continent in names:
                result[province] = names[continent]
    return result


def _state_history(text: str, path: Path) -> Tuple[str, int, int]:
    body, open_pos, close_pos = _first_direct_block(
        text, re.compile(r"\bhistory\s*=\s*\{")
    )
    if open_pos < 0:
        raise MigrationError(f"{path}: missing history block")
    return body, open_pos, close_pos


def _initial_scopes(text: str) -> List[Tuple[str, int, int]]:
    """Return the undated root and, when present, the 2000 startup scope."""
    dated, open_pos, close_pos = _initial_date_block(text)
    if open_pos < 0:
        return [(text, -1, len(text))]
    return [(text, -1, len(text)), (dated, open_pos, close_pos)]


def _direct_values(body: str, name: str, value_re: str = r"[A-Za-z0-9_]+") -> List[str]:
    masked = blank_quoted_strings(_comment_mask(body))
    flat = "".join(inner[index] for inner, index in iter_flat_offsets(masked))
    return re.findall(
        rf"(?m)(?<![A-Za-z0-9_]){re.escape(name)}\s*=\s*({value_re})\b", flat
    )


def _direct_value(
    body: str, name: str, value_re: str = r"[A-Za-z0-9_]+"
) -> Optional[str]:
    values = _direct_values(body, name, value_re)
    return values[-1] if values else None


def _variable_names(body: str) -> set[str]:
    names: set[str] = set()
    for block, _, _ in _named_blocks(body, "set_variable"):
        clean = strip_comments(flat_block_text(block))
        direct = list(iter_flat_offsets(clean))
        flat = "".join(clean[index] for _, index in direct)
        fields = dict(
            re.findall(r"(?<![A-Za-z0-9_])(var|name)\s*=\s*([A-Za-z0-9_]+)\b", flat)
        )
        names.update(value for key, value in fields.items() if key in {"var", "name"})
        names.update(
            re.findall(
                r"(?m)^\s*(overall_productivity|cb_policy_rate|productivity_state_var)\s*=",
                flat,
            )
        )
    return names


def _initial_variable(scopes: List[Tuple[str, int, int]], name: str) -> bool:
    return any(name in _variable_names(body) for body, _, _ in scopes)


def _idea_names(scopes: List[Tuple[str, int, int]]) -> set[str]:
    names: set[str] = set()
    for scope, _, _ in scopes:
        names.update(_direct_values(scope, "add_ideas"))
        for block, _, _ in _named_blocks(scope, "add_ideas"):
            clean = strip_comments(flat_block_text(block))
            names.update(re.findall(r"\b[A-Za-z0-9_]+\b", clean))
    return names


def _state_data(path: Path, province_continents: Dict[int, str]) -> Dict[str, Any]:
    text = read_text_strict(str(path))
    state_body, state_body_open, _ = _first_direct_block(
        text, re.compile(r"\bstate\s*=\s*\{")
    )
    if state_body_open < 0:
        raise MigrationError(f"{path}: missing state block")
    state_id = _direct_value(state_body, "id", r"\d+")
    if state_id is None:
        raise MigrationError(f"{path}: missing state id")
    province_body, _, _ = _first_direct_block(
        state_body, re.compile(r"\bprovinces\s*=\s*\{")
    )
    provinces = [
        int(value) for value in re.findall(r"\b\d+\b", strip_comments(province_body))
    ]
    if not provinces:
        raise MigrationError(f"{path}: missing state provinces")
    history_body, history_open, history_close = _state_history(state_body, path)
    history_open += state_body_open + 1
    history_close += state_body_open + 1
    history_scopes = _initial_scopes(history_body)
    selected = None
    for scope, _, _ in history_scopes:
        selected = _direct_value(scope, "owner") or selected
        selected = _direct_value(scope, "controller") or selected
    if selected is None:
        raise MigrationError(f"{path}: missing initial owner")
    controllers = dict.fromkeys(provinces, selected)
    for scope, _, _ in history_scopes:
        masked = _comment_mask(scope)
        for match, open_pos, close_pos in iter_direct_child_blocks(
            masked, _TAG_BLOCK_RE
        ):
            block = scope[open_pos + 1 : close_pos]
            tag = match.group(0).split("=", 1)[0].strip()
            for value in _direct_values(block, "set_province_controller", r"\d+"):
                province = int(value)
                if province in controllers:
                    controllers[province] = tag
    continent = province_continents.get(provinces[0])
    if continent is None:
        raise MigrationError(f"{path}: no continent for province {provinces[0]}")
    return {
        "path": path,
        "text": text,
        "id": int(state_id),
        "controllers": controllers,
        "provinces": set(provinces),
        "continent": continent,
        "history_open": history_open,
        "history_close": history_close,
    }


def _insert_at_scope_end(
    text: str, open_pos: int, close_pos: int, additions: List[str]
) -> str:
    insertion = "\n".join(additions) + "\n"
    if open_pos < 0:
        return text.rstrip("\n") + "\n" + insertion
    line_start = text.rfind("\n", 0, close_pos) + 1
    if not text[line_start:close_pos].strip():
        return text[:line_start] + insertion + text[line_start:]
    opening_line = text[text.rfind("\n", 0, open_pos) + 1 : open_pos]
    indent = opening_line[: len(opening_line) - len(opening_line.lstrip())]
    return text[:close_pos] + "\n" + insertion + indent + text[close_pos:]


def _insert_country_defaults(
    text: str, path: Path, overall: Optional[int], add_cb: bool, add_idea: bool
) -> str:
    dated, dated_open, dated_close = _initial_date_block(text)
    if dated_open < 0:
        scope_open, scope_close = -1, len(text)
        scope = text
    else:
        scope_open, scope_close = dated_open, dated_close
        scope = dated
    indent = "\t" if scope_open >= 0 else ""
    additions = []
    if overall is not None:
        additions.append(
            f"{indent}set_variable = {{ overall_productivity = {overall} }}"
        )
    if add_cb:
        additions.append(f"{indent}set_variable = {{ cb_policy_rate = 3 }}")
    if additions:
        text = _insert_at_scope_end(text, scope_open, scope_close, additions)
        if dated_open >= 0:
            dated, dated_open, dated_close = _initial_date_block(text)
            scope = dated
            scope_close = dated_close
    if not add_idea:
        return text
    ideas = _named_blocks(scope, "add_ideas")
    if ideas:
        _, idea_open, idea_close = ideas[0]
        offset = scope_open + 1 if scope_open >= 0 else 0
        return _insert_at_scope_end(
            text,
            idea_open + offset,
            idea_close + offset,
            [f"{indent}\tno_currency_backing"],
        )
    return _insert_at_scope_end(
        text,
        scope_open,
        scope_close,
        [f"{indent}add_ideas = {{", f"{indent}\tno_currency_backing", f"{indent}}}"],
    )


def _replace_variable_value(block: str, name: str, value: int) -> Optional[str]:
    masked = _comment_mask(block)
    direct = re.search(
        rf"(?m)(?<![A-Za-z0-9_]){re.escape(name)}\s*=\s*({_NUMBER_RE})", masked
    )
    if direct:
        return block[: direct.start(1)] + str(value) + block[direct.end(1) :]
    fields = list(
        re.finditer(rf"(?<![A-Za-z0-9_])(var|name)\s*=\s*{re.escape(name)}\b", masked)
    )
    if not fields:
        return None
    number = re.search(rf"(?<![A-Za-z0-9_])value\s*=\s*({_NUMBER_RE})", masked)
    if not number:
        return None
    return block[: number.start(1)] + str(value) + block[number.end(1) :]


def _replace_or_insert_state(text: str, state: Dict[str, Any], value: int) -> str:
    history_open = state["history_open"]
    history_close = state["history_close"]
    body = text[history_open + 1 : history_close]
    scopes = _initial_scopes(body)
    for scope, scope_open, _ in reversed(scopes):
        for block, open_pos, _ in reversed(_named_blocks(scope, "set_variable")):
            replacement = _replace_variable_value(
                block, "productivity_state_var", value
            )
            if replacement is None:
                continue
            absolute = history_open + 1 + scope_open + 1 + open_pos + 1
            return text[:absolute] + replacement + text[absolute + len(block) :]
    _, scope_open, scope_close = scopes[-1]
    indent = "\t\t\t" if scope_open >= 0 else "\t\t"
    return _insert_at_scope_end(
        text,
        history_open + 1 + scope_open,
        history_open + 1 + scope_close,
        [f"{indent}set_variable = {{ productivity_state_var = {value} }}"],
    )


def plan_migration(root: Path) -> Dict[str, str]:
    countries_dir = root / "history" / "countries"
    states_dir = root / "history" / "states"
    province_continents = _load_province_continents(root)
    states = [
        _state_data(path, province_continents)
        for path in sorted(states_dir.glob("*.txt"))
    ]
    state_by_province = {
        province: state for state in states for province in state["provinces"]
    }
    country_data = []
    for path in sorted(countries_dir.glob("*.txt")):
        tag = _country_tag(path)
        text = read_text_strict(str(path))
        scopes = _initial_scopes(text)
        capital_value = next(
            (
                value
                for scope, _, _ in reversed(scopes)
                if (value := _direct_value(scope, "capital", r"\d+"))
            ),
            None,
        )
        if capital_value is None:
            raise MigrationError(f"{path}: missing capital")
        capital = next(
            (state for state in states if state["id"] == int(capital_value)), None
        )
        if capital is None:
            raise MigrationError(f"{path}: capital state {capital_value} not found")
        default = CONTINENT_DEFAULTS.get(capital["continent"])
        has_overall = _initial_variable(scopes, "overall_productivity")
        if not has_overall and default is None:
            raise MigrationError(
                f"{path}: unsupported capital continent {capital['continent']}"
            )
        overall = None if has_overall else default
        add_idea = not _idea_names(scopes).intersection(BACKING_IDEAS)
        country_data.append(
            (
                tag,
                path,
                text,
                scopes,
                overall,
                not _initial_variable(scopes, "cb_policy_rate"),
                add_idea,
            )
        )
    for tag, _, _, scopes, _, _, _ in country_data:
        for scope, _, _ in scopes:
            for value in _direct_values(scope, "set_province_controller", r"\d+"):
                state = state_by_province.get(int(value))
                if state is not None:
                    state["controllers"][int(value)] = tag
    tag_defaults = {
        tag: overall
        for tag, _, _, _, overall, _, _ in country_data
        if overall is not None
    }
    missing_tags = set(tag_defaults)
    changes: Dict[str, str] = {}
    for tag, path, text, _, overall, add_cb, add_idea in country_data:
        updated = _insert_country_defaults(text, path, overall, add_cb, add_idea)
        if updated != text:
            changes[str(path)] = updated
    for state in states:
        affected = set(state["controllers"].values()).intersection(missing_tags)
        if not affected:
            continue
        values = {tag_defaults[tag] for tag in affected}
        if len(values) != 1:
            names = ", ".join(sorted(affected))
            raise MigrationError(
                f"{state['path']}: controllers {names} have different startup defaults"
            )
        original = changes.get(str(state["path"]))
        if original is None:
            original = state["text"]
        updated = _replace_or_insert_state(original, state, values.pop())
        if updated != original:
            changes[str(state["path"])] = updated
    return changes


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        changes = plan_migration(args.root.resolve())
        if args.write:
            for filename, text in changes.items():
                with open(filename, "w", encoding="utf-8", newline="") as handle:
                    handle.write(text)
    except (OSError, UnicodeError, MigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"{'would change' if args.dry_run else 'changed'} {len(changes)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
