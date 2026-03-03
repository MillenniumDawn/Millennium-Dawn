#!/usr/bin/env python3
"""Generate per-page Open Graph images for docs content."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from og.content import (
    is_seo_enabled,
    iter_source_files,
    load_css_hex_tokens,
    load_site_description,
    og_id_for_path,
    page_path_for_og,
    parse_front_matter,
    subtitle_for_page,
)
from og.render import create_base_background, load_logo_rgba, render_card, render_home_card


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--docs-dir", default="docs", help="Docs directory relative to repo-root")
    parser.add_argument(
        "--output-dir",
        default="docs/assets/images/seo/generated",
        help="Output directory for generated PNG files",
    )
    parser.add_argument("--width", type=int, default=1200, help="Image width")
    parser.add_argument("--height", type=int, default=630, help="Image height")
    parser.add_argument(
        "--logo-path",
        default="docs/assets/images/branding/main-menu.png",
        help="Path to logo image",
    )
    parser.add_argument(
        "--hero-bg-path",
        default="docs/assets/images/branding/hero.jpeg",
        help="Path to hero background image",
    )
    return parser.parse_args()


def _resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    repo_root = Path(args.repo_root).resolve()
    docs_dir = (repo_root / args.docs_dir).resolve()
    output_dir = (repo_root / args.output_dir).resolve()
    logo_path = (repo_root / args.logo_path).resolve()
    hero_bg_path = (repo_root / args.hero_bg_path).resolve()
    return docs_dir, output_dir, logo_path, hero_bg_path


def _is_home_page(page_path: str, data: dict[str, object]) -> bool:
    return page_path == "/" or str(data.get("page_id") or "").strip().lower() == "home"


def main() -> int:
    args = parse_args()
    docs_dir, output_dir, logo_path, hero_bg_path = _resolve_paths(args)

    if not docs_dir.exists():
        print(f"ERROR: docs directory not found: {docs_dir}")
        return 2
    if not logo_path.exists():
        print(f"ERROR: logo image not found: {logo_path}")
        return 2
    if not hero_bg_path.exists():
        print(f"ERROR: hero background image not found: {hero_bg_path}")
        return 2

    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    site_description = load_site_description(docs_dir / "_config.yml")
    css_tokens = load_css_hex_tokens(docs_dir / "_sass" / "_variables.scss")

    logo = load_logo_rgba(logo_path)
    base_bg = create_base_background(
        width=args.width,
        height=args.height,
        hero_bg_path=hero_bg_path,
        css_tokens=css_tokens,
    )

    generated = 0
    skipped_no_title = 0
    skipped_seo_disabled = 0
    seen_ids: dict[str, Path] = {}

    for source_file in iter_source_files(docs_dir):
        rel_path = source_file.relative_to(docs_dir)
        raw = source_file.read_text(encoding="utf-8", errors="replace")
        front_matter = parse_front_matter(raw)

        if not is_seo_enabled(front_matter):
            skipped_seo_disabled += 1
            continue

        page_path = page_path_for_og(rel_path, front_matter)
        is_home = _is_home_page(page_path, front_matter)
        title = str(front_matter.get("title") or "").strip()
        if not title and not is_home:
            skipped_no_title += 1
            continue

        subtitle = subtitle_for_page(
            data=front_matter,
            rel_path=rel_path,
            site_description=site_description,
        )
        og_id = og_id_for_path(rel_path)
        output_path = output_dir / f"{og_id}.png"

        existing = seen_ids.get(og_id)
        if existing and existing != rel_path:
            print(
                f"WARNING: duplicate og id '{og_id}' for {rel_path.as_posix()} "
                f"and {existing.as_posix()}; using latest."
            )
        seen_ids[og_id] = rel_path

        if is_home:
            render_home_card(
                base_bg=base_bg,
                logo=logo,
                output_path=output_path,
            )
        else:
            render_card(
                base_bg=base_bg,
                logo=logo,
                title=title,
                subtitle=subtitle,
                page_path=page_path,
                output_path=output_path,
            )
        generated += 1

    print(
        "OG generation complete: "
        f"generated={generated} "
        f"skipped_seo_disabled={skipped_seo_disabled} "
        f"skipped_no_title={skipped_no_title}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
