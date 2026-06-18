#!/usr/bin/env python3
"""Validate dev diary frontmatter and external/in-repo URL uniqueness."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

try:
    from common import CONTENT_ROOT, REPO_ROOT
except ImportError:  # when imported as a package module
    from .common import CONTENT_ROOT, REPO_ROOT

DEV_DIARIES_DIR = CONTENT_ROOT / "devDiaries"
EXTERNAL_YML = CONTENT_ROOT / "devDiaryExternal" / "index.yml"

FRONTMATTER_RE = re.compile(r"^---\r?\n([\s\S]*?)\r?\n---[ \t]*\r?\n?", re.MULTILINE)
VERSION_RE = re.compile(r"^v\d+\.\d+$")
VERSION_TAG_RE = re.compile(r"^v\d+(\.\d+)?$", re.IGNORECASE)


def normalize_compare_url(url: str) -> str:
    """Normalize a permalink or href for collision checks."""
    raw = url.strip()
    if "://" in raw:
        parsed = urlparse(raw)
        path = parsed.path.rstrip("/").lower()
        host = (parsed.netloc or "").lower()
        return f"{parsed.scheme.lower()}://{host}{path}"
    return raw.rstrip("/")


def is_version_like_tag(tag: str) -> bool:
    return bool(VERSION_TAG_RE.match(tag.strip()))


def parse_frontmatter(text: str) -> dict | None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    data = yaml.safe_load(match.group(1))
    return data if isinstance(data, dict) else None


def collect_in_repo_permalinks() -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    permalinks: list[str] = []

    if not DEV_DIARIES_DIR.exists():
        return permalinks, errors, warnings

    for path in sorted(DEV_DIARIES_DIR.glob("*.mdx")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        data = parse_frontmatter(path.read_text(encoding="utf-8"))
        if data is None:
            errors.append(f"{rel}: missing or invalid YAML frontmatter")
            continue

        version = data.get("version")
        if not isinstance(version, str) or not VERSION_RE.match(version):
            errors.append(
                f"{rel}: missing or invalid version (expected vMAJOR.MINOR, got {version!r})"
            )
        else:
            pass

        permalink = data.get("permalink")
        if isinstance(permalink, str) and permalink.strip():
            permalinks.append(normalize_compare_url(permalink))

        tags = data.get("tags") or []
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str) and is_version_like_tag(tag):
                    warnings.append(
                        f"{rel}: tag {tag!r} looks like a version; use version frontmatter instead"
                    )

    return permalinks, errors, warnings


def collect_external_urls() -> list[tuple[str, str]]:
    if not EXTERNAL_YML.exists():
        return []

    data = yaml.safe_load(EXTERNAL_YML.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []

    found: list[tuple[str, str]] = []
    for group in data:
        if not isinstance(group, dict):
            continue
        group_title = str(group.get("title", "unknown group"))
        for entry in group.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            url = entry.get("url")
            if isinstance(url, str) and url.strip():
                found.append((group_title, url))
    return found


def find_duplicate_urls(
    in_repo: list[str], external: list[tuple[str, str]]
) -> list[str]:
    in_repo_set = set(in_repo)
    errors: list[str] = []
    for group_title, url in external:
        normalized = normalize_compare_url(url)
        if normalized in in_repo_set:
            errors.append(
                f"devDiaryExternal ({group_title}): url {url!r} duplicates in-repo permalink"
            )
    return errors


def self_test() -> int:
    assert normalize_compare_url("/a/") == "/a"
    assert is_version_like_tag("v2.0")
    assert not is_version_like_tag("dev diary")
    return 0


def run() -> tuple[bool, str]:
    """Run dev diary checks; return (passed, report)."""
    in_repo, errors, warnings = collect_in_repo_permalinks()
    errors.extend(find_duplicate_urls(in_repo, collect_external_urls()))

    lines: list[str] = []
    if warnings:
        lines.extend(f"WARNING: {w}" for w in warnings)
    if errors:
        lines.extend(f"ERROR: {e}" for e in errors)
        return False, "Dev diary checks failed:\n" + "\n".join(lines)

    summary = "Dev diary checks passed"
    if warnings:
        summary += f" ({len(warnings)} warning(s))"
    if lines:
        return True, summary + "\n" + "\n".join(lines)
    return True, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    passed, report = run()
    print(report)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
