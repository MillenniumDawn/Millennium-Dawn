"""Classify changed repository paths for the validation workflow."""

import argparse
import json
import os
import re
import sys
from typing import Dict, Iterable, List

GROUP_PATTERNS = {
    "common": ["common/**"],
    "events": ["events/**"],
    "history": ["history/**"],
    "localisation": ["localisation/**"],
    "ai-strategy": ["common/ai_strategy/**", "common/ai_templates/**"],
    "ai-navy": ["common/ai_navy/**", "common/units/**"],
    "ai-equipment": ["common/ai_equipment/**"],
    "factions": ["common/factions/**"],
    "characters": [
        "common/characters/**",
        "common/unit_leader/**",
        "common/country_leader/**",
        "common/national_focus/**",
        "common/decisions/**",
        "common/scripted_effects/**",
        "common/on_actions/**",
        "events/**",
        "history/countries/**",
    ],
    "scientist-traits": ["common/scientist_traits/**", "interface/**"],
    "oob": [
        "history/units/**",
        "common/units/**",
        "common/ai_templates/**",
        "common/scripted_effects/**",
        "history/countries/**",
        "common/national_focus/**",
        "events/**",
        "common/decisions/**",
        "common/special_projects/**",
        "common/on_actions/**",
        "common/operations/**",
        "common/resistance_compliance_modifiers/**",
        "common/scripted_guis/**",
        "common/ideas/**",
    ],
    "decisions": ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"],
    "scripted-loc": ["common/scripted_localisation/**"],
    "scripted-guis": ["common/scripted_guis/**"],
    "interface": ["interface/**"],
    "national-focus": ["common/national_focus/**"],
    "on-actions": ["common/on_actions/**"],
    "mios": [
        "common/military_industrial_organization/**",
        "common/country_leader/**",
        "common/doctrines/**",
        "common/units/equipment/**",
        "common/equipment_groups/**",
    ],
    "scripted-effects": ["common/scripted_effects/**"],
    "style": [
        "common/**/*.txt",
        "events/**/*.txt",
        "history/**/*.txt",
        "music/**/*.txt",
    ],
    "mod": ["*.mod"],
    "map-adjacency": ["map/adjacency_rules.txt"],
    "content": [
        "common/**",
        "events/**",
        "history/**",
        "localisation/**",
        "interface/**",
        "music/**",
        "map/adjacency_rules.txt",
        "*.mod",
    ],
}

_FULL_SUITE_EXACT = {
    ".pre-commit-config.yaml",
    "pyproject.toml",
    "package.json",
    "bun.lock",
    ".jscpd.json",
    ".claude/docs/typo-watchlist.md",
}
_FULL_SUITE_PREFIXES = (
    "resources/documentation/",
    ".github/actions/",
    ".github/workflows/test-suite.yml",
    ".github/workflows/nightly-pr-validation.yml",
    ".github/workflows/pr-cache-cleanup.yml",
    ".github/workflows/validator-cache.yml",
)
_FILE_PATH_ROOTS = (
    "common",
    "descriptions",
    "events",
    "gfx",
    "history",
    "interface",
    "localisation",
    "map",
    "music",
    "portraits",
    "scenario_tests",
    "sound",
    "tutorial",
)


def _glob_regex(pattern: str) -> re.Pattern:
    parts = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            parts.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            parts.append(".*")
            index += 2
        elif pattern[index] == "*":
            parts.append("[^/]*")
            index += 1
        else:
            parts.append(re.escape(pattern[index]))
            index += 1
    return re.compile(r"^" + "".join(parts) + r"$")


_COMPILED_PATTERNS = {
    group: tuple(_glob_regex(pattern) for pattern in patterns)
    for group, patterns in GROUP_PATTERNS.items()
}


def _matches(path: str, group: str) -> bool:
    return any(pattern.match(path) for pattern in _COMPILED_PATTERNS[group])


def _is_full_suite(path: str) -> bool:
    return (
        path.startswith("tools/")
        or path in _FULL_SUITE_EXACT
        or any(path.startswith(prefix) for prefix in _FULL_SUITE_PREFIXES)
    )


def _needs_file_path_validation(path: str) -> bool:
    return path == "descriptor.mod" or any(
        path == root or path.startswith(f"{root}/") for root in _FILE_PATH_ROOTS
    )


def classify(paths: Iterable[str], dispatch: bool = False) -> Dict[str, object]:
    """Return changed group booleans and the diff-scoped style file list."""
    normalized = [path.replace("\\", "/") for path in paths if path]
    full_suite = dispatch or any(_is_full_suite(path) for path in normalized)
    result: Dict[str, object] = {
        group: any(_matches(path, group) for path in normalized)
        for group in GROUP_PATTERNS
    }
    style_files = sorted(
        {
            path
            for path in normalized
            if path.endswith(".txt") and _matches(path, "style")
        }
    )
    if full_suite:
        for group in GROUP_PATTERNS:
            if group != "style":
                result[group] = True
    result["full_suite"] = full_suite
    result["tools"] = full_suite or any(
        path.startswith("tools/") for path in normalized
    )
    result["file-paths"] = full_suite or any(
        _needs_file_path_validation(path) for path in normalized
    )
    result["style_files"] = style_files
    result["style"] = bool(style_files)
    return result


def _read_paths() -> List[str]:
    return [line.rstrip("\n\r") for line in sys.stdin if line.rstrip("\n\r")]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Classify validation file groups")
    parser.add_argument("--dispatch", action="store_true")
    parser.add_argument("--output", help="GITHUB_OUTPUT destination")
    args = parser.parse_args(argv)
    output_path = args.output or os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        parser.error("--output or GITHUB_OUTPUT is required")
    values = classify(_read_paths(), dispatch=args.dispatch)
    try:
        # GITHUB_OUTPUT is supplied by the Actions runner.
        # pi-lens-ignore: python-path-traversal
        with open(output_path, "w", encoding="utf-8", newline="") as handle:
            for key, value in values.items():
                if key == "style_files":
                    handle.write(f"{key}={json.dumps(value)}\n")
                else:
                    handle.write(f"{key}={str(value).lower()}\n")
    except OSError as error:
        parser.error(f"could not write output file: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
