#!/usr/bin/env python3
"""Rename country focus IDs and their known references."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FOCUS_OPEN_RE = re.compile(r"^\s*(?:focus|shared_focus|joint_focus)\s*=\s*\{")
ID_RE = re.compile(r"^\s*id\s*=\s*([A-Za-z0-9_?]+)")
REF_RE = re.compile(
    r"((?:relative_position_id|has_completed_focus|activate_shine_on_focus|FOCUS|shared_focus|complete_national_focus|uncomplete_national_focus)\s*=\s*)([A-Za-z0-9_?]+)(?![A-Za-z0-9_.])"
)
ID_REF_RE = re.compile(r"(\bid\s*=\s*)([A-Za-z0-9_?]+)(?![A-Za-z0-9_.])")
FOCUS_REF_RE = re.compile(r"(\bfocus\s*=\s*)([A-Za-z0-9_?]+)(?![A-Za-z0-9_.])")
FOCUS_EFFECT_RE = re.compile(
    r"((?:complete_national_focus|uncomplete_national_focus)\s*=\s*(?:\{\s*)?)([A-Za-z0-9_?]+)(?![A-Za-z0-9_.])"
)
NAME_RE = re.compile(r"(\bname\s*=\s*)([A-Za-z0-9_?]+)(?![A-Za-z0-9_.])")
LOG_RE = re.compile(r"(\bFocus\s+)([A-Za-z0-9_?]+)(?![A-Za-z0-9_.])")


def _read(path: Path, encoding: str) -> str:
    with path.open("r", encoding=encoding, newline="") as handle:
        return handle.read()


def _write(path: Path, text: str, encoding: str) -> None:
    with path.open("w", encoding=encoding, newline="") as handle:
        handle.write(text)


def _code(line: str) -> str:
    return line.split("#", 1)[0]


def _brace_delta(line: str) -> int:
    code = re.sub(r'"(?:\\.|[^"\\])*"', '""', _code(line))
    return code.count("{") - code.count("}")


def _canonical_id(old_id: str, tag: str) -> str:
    prefix = f"{tag}_"
    if old_id.startswith(f"{prefix}ast_"):
        return prefix + old_id[len(prefix) + 4 :]
    if old_id.startswith(prefix):
        return old_id
    if old_id.startswith("ast_"):
        return prefix + old_id[4:]
    return prefix + old_id


def extract_focus_ids(text: str, tag: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    new_ids: set[str] = set()
    depth = 0
    focus_depth: int | None = None

    for line in text.splitlines(keepends=True):
        if focus_depth is None and FOCUS_OPEN_RE.match(line):
            focus_depth = depth + 1
        elif focus_depth is not None and depth == focus_depth:
            match = ID_RE.match(line)
            if match:
                old_id = match.group(1)
                new_id = _canonical_id(old_id, tag)
                if new_id in new_ids:
                    raise ValueError(f"Duplicate normalized focus ID: {new_id}")
                new_ids.add(new_id)
                mapping[old_id] = new_id
                if old_id.startswith(f"{tag}_ast_"):
                    mapping[old_id[len(tag) + 1 :]] = new_id

        depth += _brace_delta(line)
        if focus_depth is not None and depth < focus_depth:
            focus_depth = None

    return mapping


def _replace_ids(
    line: str,
    mapping: dict[str, str],
    *,
    localization: bool = False,
    focus_file: bool = False,
) -> str:
    if localization:
        pattern = re.compile(
            r"(?<![A-Za-z0-9_])("
            + "|".join(map(re.escape, mapping))
            + r")(?=_desc\b|\b)"
        )
        return pattern.sub(lambda match: mapping[match.group(1)], line)

    def replace_match(match: re.Match[str]) -> str:
        return f"{match.group(1)}{mapping.get(match.group(2), match.group(2))}"

    if focus_file:
        line = ID_REF_RE.sub(replace_match, line)
        line = NAME_RE.sub(replace_match, line)
        line = LOG_RE.sub(replace_match, line)
    line = REF_RE.sub(replace_match, line)
    line = FOCUS_REF_RE.sub(replace_match, line)
    return FOCUS_EFFECT_RE.sub(replace_match, line)


def rename_focus_ids(
    root: Path, focus_file: Path, localisation_file: Path, tag: str
) -> tuple[dict[str, str], list[Path]]:
    root = root.resolve()
    focus_file = focus_file.resolve()
    localisation_file = localisation_file.resolve()
    focus_text = _read(focus_file, "utf-8")
    mapping = extract_focus_ids(focus_text, tag)
    if not mapping:
        raise ValueError(f"No focus IDs found in {focus_file}")

    changed: list[Path] = []
    focus_output = "".join(
        _replace_ids(line, mapping, focus_file=True)
        for line in focus_text.splitlines(keepends=True)
    )
    if focus_output != focus_text:
        _write(focus_file, focus_output, "utf-8")
        changed.append(focus_file)

    for base_name in ("common", "events", "history", "interface"):
        base = root / base_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if (
                path == focus_file
                or not path.is_file()
                or path.suffix not in {".txt", ".gui", ".gfx", ".mod"}
            ):
                continue
            text = _read(path, "utf-8")
            output = "".join(
                _replace_ids(line, mapping) for line in text.splitlines(keepends=True)
            )
            if output != text:
                _write(path, output, "utf-8")
                changed.append(path)

    localisation_text = _read(localisation_file, "utf-8-sig")
    localisation_output = _replace_ids(localisation_text, mapping, localization=True)
    if localisation_output != localisation_text:
        _write(localisation_file, localisation_output, "utf-8-sig")
        changed.append(localisation_file)

    return mapping, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--focus-file", type=Path, required=True)
    parser.add_argument("--localisation-file", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()

    mapping, changed = rename_focus_ids(
        args.root, args.focus_file, args.localisation_file, args.tag
    )
    print(f"Renamed {len(mapping)} focus IDs")
    for path in changed:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
