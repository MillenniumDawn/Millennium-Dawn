#!/usr/bin/env python3
"""Publish the current release changelog into the docs content collection.

This script is intended to run in CI after a tag is pushed. It:
  1. Ensures ``Changelog.md`` is up to date by invoking the formatter.
  2. Extracts the markdown block for the requested version.
  3. Writes that block to ``docs/src/content/changelogSections/`` with the
     frontmatter required by the Astro docs site.

The changelog archive page already indexes that collection, so no separate
index file needs to be generated.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys


def run_cmd(cmd: list[str], cwd: pathlib.Path | None = None) -> str:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def get_current_tag(explicit_tag: str | None) -> str:
    if explicit_tag:
        return explicit_tag

    ref_name = os.environ.get("GITHUB_REF_NAME")
    if ref_name:
        return ref_name

    github_ref = os.environ.get("GITHUB_REF")
    if github_ref and github_ref.startswith("refs/tags/"):
        return github_ref.split("/", 2)[2]

    return run_cmd(["git", "describe", "--tags", "--exact-match"])


def ensure_changelog_md(repo_root: pathlib.Path) -> None:
    formatter = repo_root / "tools" / "changelog" / "format_changelog.py"
    run_cmd(["python3", str(formatter)], cwd=repo_root)


def extract_version_block(changelog_md: pathlib.Path, version: str) -> str:
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\].*?(?=^## \[|\Z)", re.MULTILINE | re.DOTALL
    )
    content = changelog_md.read_text(encoding="utf-8")
    match = pattern.search(content)
    if not match:
        raise RuntimeError(f"Version block for {version} not found in {changelog_md}")
    return match.group(0).rstrip() + "\n"


def extract_release_date(block: str) -> str | None:
    match = re.search(
        r"^## \[[^\]]+\](?: - (\d{4}-\d{2}-\d{2}))?$", block, re.MULTILINE
    )
    if match:
        return match.group(1)
    return None


_SAFE_SLUG = re.compile(r"[a-z0-9][a-z0-9\-]*")


def version_to_slug(version: str) -> str:
    slug = version.lower().replace(".", "-")
    # Guard against path traversal if an unexpected tag ever slips past the refname filter.
    if not _SAFE_SLUG.fullmatch(slug):
        raise RuntimeError(f"Refusing unsafe slug derived from tag: {version!r}")
    return slug


def get_existing_order(dest_file: pathlib.Path) -> int | None:
    if not dest_file.exists():
        return None

    match = re.search(
        r"^order:\s*(\d+)\s*$", dest_file.read_text(encoding="utf-8"), re.MULTILINE
    )
    if match:
        return int(match.group(1))
    return None


def compute_next_order(dest_dir: pathlib.Path) -> int:
    max_order = 0
    for path in dest_dir.glob("*.md"):
        match = re.search(
            r"^order:\s*(\d+)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE
        )
        if match:
            max_order = max(max_order, int(match.group(1)))
    return max_order + 1


def render_doc_page(version_tag: str, order: int, block: str) -> str:
    slug = version_to_slug(version_tag)
    release_date = extract_release_date(block)
    frontmatter_lines = [
        "---",
        f"title: {version_tag} Release Notes",
        f"description: Release notes for Millennium Dawn {version_tag}.",
        f"page_id: changelog-{slug}",
        f"order: {order}",
    ]
    if release_date:
        frontmatter_lines.append(f"last_updated: {release_date}")
    frontmatter_lines.append("---")

    return "\n".join(frontmatter_lines) + "\n\n" f"{block}"


def write_version_file(
    dest_dir: pathlib.Path, version_tag: str, block: str
) -> pathlib.Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    slug = version_to_slug(version_tag)
    dest_file = dest_dir / f"{slug}.md"
    order = get_existing_order(dest_file)
    if order is None:
        order = compute_next_order(dest_dir)

    dest_file.write_text(render_doc_page(version_tag, order, block), encoding="utf-8")
    print(f"Wrote changelog for {version_tag} to {dest_file}")
    return dest_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish changelog for a new tag into the docs content collection."
    )
    parser.add_argument(
        "--tag",
        help="Git tag (e.g. v2.0.0). If omitted, read from GITHUB_REF_NAME, GITHUB_REF, or git.",
    )
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    version_tag = get_current_tag(args.tag)
    if not version_tag.startswith("v"):
        version_tag = f"v{version_tag}"
    version = version_tag[1:]

    print(f"Publishing changelog for version {version_tag}")

    ensure_changelog_md(repo_root)

    changelog_md = repo_root / "Changelog.md"
    block = extract_version_block(changelog_md, version)

    dest_dir = repo_root / "docs" / "src" / "content" / "changelogSections"
    write_version_file(dest_dir, version_tag, block)
    return 0


if __name__ == "__main__":
    sys.exit(main())
