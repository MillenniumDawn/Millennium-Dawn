#!/usr/bin/env python3
"""Validate docs source hygiene constraints."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


TEXT_EXTENSIONS = {".md", ".mdx", ".html", ".yml", ".yaml", ".scss", ".css", ".js", ".ts", ".astro"}
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


def tracked_asset_to_web_path(docs_prefix: str, rel_posix: str) -> str | None:
    """Map a tracked path under docs/ to the site URL path used in content or imports."""
    if not rel_posix.startswith(docs_prefix):
        return None
    p = rel_posix[len(docs_prefix) :]
    if p.startswith("public/assets/images/"):
        return "/" + p[len("public/") :]
    if p.startswith("public/assets/downloads/"):
        return "/" + p[len("public/") :]
    if p.startswith("src/assets/images/"):
        return "/assets/images/" + p[len("src/assets/images/") :]
    return None


def reference_needles_for_web_path(web_path: str) -> list[str]:
    """Substrings that indicate this asset is referenced from docs source (Markdown, Astro, TS)."""
    needles = [web_path]
    if web_path.startswith("/assets/images/"):
        rel = web_path[len("/assets/images/") :]
        needles.append("@/assets/images/" + rel)
        needles.append("assets/images/" + rel)
        needles.append("src/assets/images/" + rel)
    return needles


def asset_is_referenced(web_path: str, source_contents: list[str]) -> bool:
    if web_path in ALLOW_UNUSED_ASSETS:
        return True
    needles = reference_needles_for_web_path(web_path)
    return any(n in text for text in source_contents for n in needles)


def find_unused_assets(
    repo_root: Path,
    docs_dir: Path,
    tracked_files: list[str],
) -> list[str]:
    issues: list[str] = []
    docs_prefix = docs_dir.as_posix().rstrip("/") + "/"

    source_files: list[Path] = []
    for rel in tracked_files:
        if not rel.startswith(docs_prefix):
            continue
        path = Path(rel)
        if not is_text_file(path):
            continue
        # Do not treat binary asset directories as reference sources.
        if rel.startswith(f"{docs_prefix}public/assets/images/") or rel.startswith(
            f"{docs_prefix}public/assets/downloads/"
        ) or rel.startswith(f"{docs_prefix}src/assets/images/"):
            continue
        source_files.append(repo_root / rel)

    source_contents: list[str] = []
    for src in source_files:
        if not src.exists():
            # File may be deleted in the current change-set but still present in git index.
            continue
        source_contents.append(src.read_text(encoding="utf-8", errors="replace"))

    for rel in tracked_files:
        web_path = tracked_asset_to_web_path(docs_prefix, rel)
        if web_path is None:
            continue
        if asset_is_referenced(web_path, source_contents):
            continue
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
        tracked_under_assets = rel.startswith(f"{docs_prefix}public/assets/") or rel.startswith(
            f"{docs_prefix}src/assets/images/"
        )
        if tracked_under_assets and TEMP_NAME_RE.search(file_name):
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
