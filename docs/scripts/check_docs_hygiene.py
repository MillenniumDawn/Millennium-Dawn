#!/usr/bin/env python3
"""Validate docs source hygiene constraints."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


TEXT_EXTENSIONS = {".md", ".html", ".yml", ".yaml", ".scss", ".css", ".js", ".ts", ".astro"}
TEMP_NAME_RE = re.compile(r"-temp", re.IGNORECASE)

# Keep this list short and explicit when an unreferenced asset is intentional.
ALLOW_UNUSED_ASSETS: set[str] = set()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path (default: current directory).",
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Docs directory path relative to repo root (default: docs).",
    )
    return parser.parse_args()


def git_ls_files(repo_root: Path) -> list[str]:
    out = subprocess.check_output(
        ["git", "-C", str(repo_root), "ls-files"],
        text=True,
        encoding="utf-8",
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS


def find_unused_assets(
    repo_root: Path,
    docs_dir: Path,
    tracked_files: list[str],
) -> list[str]:
    issues: list[str] = []
    docs_prefix = docs_dir.as_posix().rstrip("/") + "/"
    tracked_set = set(tracked_files)

    source_files: list[Path] = []
    for rel in tracked_files:
        if not rel.startswith(docs_prefix):
            continue
        path = Path(rel)
        if not is_text_file(path):
            continue
        # Do not treat binary asset source directories as reference sources.
        if rel.startswith(f"{docs_prefix}assets/images/") or rel.startswith(
            f"{docs_prefix}assets/downloads/"
        ):
            continue
        source_files.append(repo_root / rel)

    source_contents: list[str] = []
    for src in source_files:
        if not src.exists():
            # File may be deleted in the current change-set but still present in git index.
            continue
        source_contents.append(src.read_text(encoding="utf-8", errors="replace"))

    asset_roots = (
        docs_dir / "assets" / "images",
        docs_dir / "assets" / "downloads",
    )
    for root in asset_roots:
        root_prefix = root.as_posix().rstrip("/") + "/"
        for rel in tracked_files:
            if rel not in tracked_set or not rel.startswith(root_prefix):
                continue
            web_path = "/" + rel[len(docs_prefix) :]
            if web_path in ALLOW_UNUSED_ASSETS:
                continue
            used = any(web_path in content for content in source_contents)
            if not used:
                issues.append(f"Unused docs asset tracked: {rel}")

    return issues


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    docs_dir = Path(args.docs_dir)
    docs_prefix = docs_dir.as_posix().rstrip("/") + "/"

    tracked_files = git_ls_files(repo_root)
    issues: list[str] = []

    for rel in tracked_files:
        if not rel.startswith(docs_prefix):
            continue
        abs_path = repo_root / rel
        if not abs_path.exists():
            # Ignore files deleted in the current working tree.
            continue
        file_name = Path(rel).name
        if rel.startswith(f"{docs_prefix}.bundle/"):
            issues.append(f"Bundler local config must not be tracked: {rel}")
        if rel.startswith(f"{docs_prefix}assets/") and TEMP_NAME_RE.search(file_name):
            issues.append(f"Temp-named docs asset is tracked: {rel}")

    issues.extend(find_unused_assets(repo_root, docs_dir, tracked_files))

    if issues:
        print("Docs hygiene checks failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Docs hygiene checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
