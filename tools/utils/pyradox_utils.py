from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import cast

import pyradox


def parse_file(file_path: str | Path) -> pyradox.Tree:
    try:
        return cast(pyradox.Tree, pyradox.parse_file(str(file_path)))
    except KeyError:
        text = Path(file_path).read_text(encoding="utf-8")
        return cast(pyradox.Tree, pyradox.parse(text))


def normalize_node(value: object) -> object:
    """Convert pyradox trees into plain Python containers recursively."""
    if isinstance(value, pyradox.Tree):
        return value.to_python()
    if isinstance(value, dict):
        return {str(key): normalize_node(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [normalize_node(item) for item in value]
    return value


def normalize_bool(value: object) -> bool:
    """Coerce common HOI4 boolean spellings into Python booleans."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1", "y", "on"}
    return bool(value)


def normalize_scalar(value: object) -> object:
    """Collapse single-item lists while keeping structured values intact."""
    normalized = normalize_node(value)
    if isinstance(normalized, list):
        return normalized[0] if len(normalized) == 1 else normalized
    return normalized


def normalize_type(value: object) -> list[str]:
    """Treat HOI4 type values as a list of string tokens."""
    normalized = normalize_node(value)
    if normalized is None:
        return []
    if isinstance(normalized, str):
        return [normalized]
    if isinstance(normalized, (list, tuple, set)):
        return [str(item) for item in normalized]
    return [str(normalized)]


def dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    """Deduplicate a sequence while preserving first-seen order."""
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def as_mapping(value: object) -> dict[str, object]:
    """Normalize and validate a value as a string-keyed mapping."""
    normalized = normalize_node(value)
    if isinstance(normalized, dict):
        return {str(key): inner for key, inner in normalized.items()}
    raise TypeError(f"Expected mapping but got {type(value)!r}")


def token_list(value: object) -> list[str]:
    """Flatten nested scalar/list/dict values into a token list of strings."""
    normalized = normalize_node(value)
    if normalized is None:
        return []
    if isinstance(normalized, str):
        return [normalized]
    if isinstance(normalized, (int, float, bool)):
        return [str(normalized)]
    if isinstance(normalized, list):
        tokens: list[str] = []
        for item in normalized:
            tokens.extend(token_list(item))
        return tokens
    if isinstance(normalized, dict):
        tokens = []
        for item in normalized.values():
            tokens.extend(token_list(item))
        return tokens
    return [str(normalized)]


def as_trait_list(value: object) -> list[dict[str, object]]:
    """Normalize trait payloads to a list of trait dictionaries."""
    normalized = normalize_node(value)
    if normalized is None:
        return []
    if isinstance(normalized, dict):
        return [cast(dict[str, object], normalized)]
    if isinstance(normalized, list):
        traits: list[dict[str, object]] = []
        for item in normalized:
            if isinstance(item, dict):
                traits.append(cast(dict[str, object], item))
        return traits
    return []


def stats_value(value: object) -> object:
    """Coerce common script scalar forms into Python bool/int/float values."""
    normalized = normalize_node(value)
    if isinstance(normalized, str):
        lowered = normalized.strip().lower()
        if lowered in {"yes", "true", "on"}:
            return True
        if lowered in {"no", "false", "off"}:
            return False
        try:
            if "." in lowered:
                return float(lowered)
            return int(lowered)
        except ValueError:
            return normalized
    return normalized


__all__ = [
    "as_mapping",
    "as_trait_list",
    "dedupe_preserve_order",
    "normalize_bool",
    "normalize_node",
    "normalize_scalar",
    "normalize_type",
    "parse_file",
    "stats_value",
    "token_list",
]
