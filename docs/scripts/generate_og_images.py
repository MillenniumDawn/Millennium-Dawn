#!/usr/bin/env python3
"""Generate per-page Open Graph images for docs content."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "Pillow is required. Install with: python3 -m pip install pillow"
    ) from exc


SITE_DESCRIPTION = (
    "Documentation for the Millennium Dawn: A Modern Day mod for the game Hearts of Iron IV."
)

SECTION_DEFAULT_SUBTITLE = {
    "countries": "National content overview and focus tree information for Millennium Dawn.",
    "tutorials": "Gameplay tutorial for Millennium Dawn.",
    "resources": "Developer resource for Millennium Dawn.",
    "changelogs": "Detailed changelog and release notes for Millennium Dawn.",
}

SOURCE_PATTERNS = (
    "pages/**/*.md",
    "pages/**/*.html",
    "player-tutorials/**/*.md",
    "player-tutorials/**/*.html",
    "dev-resources/**/*.md",
    "dev-resources/**/*.html",
    "misc/**/*.md",
    "misc/**/*.html",
    "_countries/*.md",
    "_countries/*.html",
    "_changelog_sections/*.md",
    "_changelog_sections/*.html",
    "*.md",
    "*.html",
)


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
    return parser.parse_args()


def load_site_description(config_path: Path) -> str:
    if not config_path.exists():
        return SITE_DESCRIPTION

    text = config_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        match = re.match(r"^\s*description:\s*(.+?)\s*$", line)
        if not match:
            continue
        raw_value = match.group(1).strip()
        if (raw_value.startswith('"') and raw_value.endswith('"')) or (
            raw_value.startswith("'") and raw_value.endswith("'")
        ):
            return raw_value[1:-1]
        return raw_value

    return SITE_DESCRIPTION


def parse_front_matter(text: str) -> dict[str, object]:
    if not text.startswith("---"):
        return {}

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}

    front_lines = lines[1:end_idx]
    data: dict[str, object] = {}
    i = 0
    while i < len(front_lines):
        line = front_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue

        match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not match:
            i += 1
            continue

        key = match.group(1)
        raw_value = match.group(2).strip()

        # Multiline YAML block scalars are rare for the fields we need.
        if raw_value in {"|", ">"}:
            i += 1
            while i < len(front_lines):
                next_line = front_lines[i]
                if next_line.startswith(" ") or next_line.startswith("\t"):
                    i += 1
                    continue
                break
            continue

        value: object
        if raw_value.lower() == "false":
            value = False
        elif raw_value.lower() == "true":
            value = True
        elif (raw_value.startswith('"') and raw_value.endswith('"')) or (
            raw_value.startswith("'") and raw_value.endswith("'")
        ):
            value = raw_value[1:-1]
        else:
            value = raw_value

        data[key] = value
        i += 1

    return data


def iter_source_files(docs_dir: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in SOURCE_PATTERNS:
        files.update(path for path in docs_dir.glob(pattern) if path.is_file())
    return sorted(files)


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    normalized = normalized.strip("-")
    return normalized or "page"


def og_id_for_path(rel_path: Path) -> str:
    parts = list(rel_path.with_suffix("").parts)
    normalized_parts: list[str] = []
    for part in parts:
        clean = part.lstrip("_")
        normalized = slugify(clean)
        if normalized:
            normalized_parts.append(normalized)
    if not normalized_parts:
        return "page"
    return "-".join(normalized_parts)


def section_for_path(rel_path: Path) -> str | None:
    first = rel_path.parts[0] if rel_path.parts else ""
    if first == "_countries":
        return "countries"
    if first == "_changelog_sections":
        return "changelogs"
    if first == "player-tutorials":
        return "tutorials"
    if first == "dev-resources":
        return "resources"
    if first == "pages" and len(rel_path.parts) > 1:
        second = rel_path.parts[1]
        if second == "tutorials":
            return "tutorials"
        if second == "resources":
            return "resources"
        if second == "countries":
            return "countries"
        if second == "changelogs":
            return "changelogs"
    return None


def subtitle_for_page(data: dict[str, object], rel_path: Path, site_description: str) -> str:
    description = str(data.get("description") or "").strip()
    if description:
        return description

    kind = str(data.get("kind") or "").strip()
    if kind:
        return kind

    section = section_for_path(rel_path)
    if section and section in SECTION_DEFAULT_SUBTITLE:
        return SECTION_DEFAULT_SUBTITLE[section]

    return site_description


def is_seo_enabled(data: dict[str, object]) -> bool:
    seo = data.get("seo")
    if seo is None:
        return True
    if isinstance(seo, bool):
        return seo
    return str(seo).strip().lower() != "false"


def create_base_background(width: int, height: int) -> Image.Image:
    color_start = (44, 62, 80)  # --color-header-bg
    color_end = (52, 73, 94)  # --color-header-bg-end

    base = Image.new("RGBA", (width, height))
    px = base.load()
    for y in range(height):
        y_ratio = y / max(height - 1, 1)
        for x in range(width):
            x_ratio = x / max(width - 1, 1)
            t = (0.65 * x_ratio) + (0.35 * y_ratio)
            t = max(0.0, min(1.0, t))
            r = int(color_start[0] + (color_end[0] - color_start[0]) * t)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * t)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * t)
            px[x, y] = (r, g, b, 255)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")

    accent_primary = (52, 152, 219, 85)  # --color-primary
    accent_secondary = (52, 152, 219, 45)
    draw.ellipse((-200, -200, 700, 700), fill=accent_primary)
    draw.ellipse((width - 520, 40, width + 260, 760), fill=accent_secondary)
    draw.ellipse((width - 340, -160, width + 120, 300), fill=(255, 255, 255, 26))
    draw.rectangle((0, height - 180, width, height), fill=(0, 0, 0, 56))

    return Image.alpha_composite(base, overlay).convert("RGBA")


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "DejaVuSans-Bold.ttf",
                "Arial Bold.ttf",
                "arialbd.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "DejaVuSans.ttf",
                "Arial.ttf",
                "arial.ttf",
            ]
        )

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def truncate_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> str:
    text = " ".join(text.split())
    if not text:
        return ""
    if text_width(draw, text, font) <= max_width:
        return text

    ellipsis = "..."
    low, high = 0, len(text)
    best = ellipsis
    while low <= high:
        mid = (low + high) // 2
        candidate = text[:mid].rstrip()
        if not candidate:
            low = mid + 1
            continue
        candidate = f"{candidate}{ellipsis}"
        if text_width(draw, candidate, font) <= max_width:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1
    return best


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    words = text.split()
    if not words:
        return []

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = word
    lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = truncate_to_width(draw, lines[-1], font, max_width)
        if not lines[-1].endswith("..."):
            lines[-1] = truncate_to_width(draw, lines[-1] + "...", font, max_width)

    normalized: list[str] = []
    for line in lines:
        normalized.append(truncate_to_width(draw, line, font, max_width))
    return normalized


def choose_title_layout(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_lines: int = 3,
) -> tuple[ImageFont.ImageFont, list[str], int]:
    for size in range(86, 45, -2):
        font = load_font(size, bold=True)
        lines = wrap_text(draw, text, font, max_width=max_width, max_lines=max_lines)
        if not lines:
            continue
        line_box = draw.textbbox((0, 0), "Ag", font=font)
        line_height = line_box[3] - line_box[1]
        total_height = line_height * len(lines) + (len(lines) - 1) * 10
        if total_height <= 290:
            return font, lines, line_height

    font = load_font(44, bold=True)
    lines = wrap_text(draw, text, font, max_width=max_width, max_lines=max_lines)
    line_box = draw.textbbox((0, 0), "Ag", font=font)
    line_height = line_box[3] - line_box[1]
    return font, lines, line_height


def draw_logo(image: Image.Image, logo: Image.Image) -> None:
    if logo.width <= 0 or logo.height <= 0:
        return

    margin_x = 42
    margin_y = 34
    target_height = 72
    ratio = target_height / logo.height
    target_width = max(1, int(logo.width * ratio))
    resized = logo.resize((target_width, target_height), resample=Image.Resampling.LANCZOS)

    x = image.width - target_width - margin_x
    y = margin_y
    image.alpha_composite(resized, dest=(x, y))


def render_card(
    base_bg: Image.Image,
    logo: Image.Image,
    title: str,
    subtitle: str,
    output_path: Path,
) -> None:
    canvas = base_bg.copy()
    draw = ImageDraw.Draw(canvas)

    text_left = 78
    text_right = 78
    title_top = 172
    text_max_width = canvas.width - text_left - text_right

    title_font, title_lines, title_line_height = choose_title_layout(
        draw, title, max_width=text_max_width, max_lines=3
    )
    current_y = title_top
    for line in title_lines:
        draw.text((text_left, current_y), line, fill=(255, 255, 255, 255), font=title_font)
        current_y += title_line_height + 10

    subtitle_font = load_font(34, bold=False)
    subtitle_text = truncate_to_width(draw, subtitle, subtitle_font, max_width=text_max_width)
    if subtitle_text:
        subtitle_y = min(current_y + 28, canvas.height - 94)
        draw.text(
            (text_left, subtitle_y),
            subtitle_text,
            fill=(203, 213, 224, 255),  # --color-footer-text
            font=subtitle_font,
        )

    draw_logo(canvas, logo)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, format="PNG", optimize=True)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    docs_dir = (repo_root / args.docs_dir).resolve()
    output_dir = (repo_root / args.output_dir).resolve()
    logo_path = (repo_root / args.logo_path).resolve()

    if not docs_dir.exists():
        print(f"ERROR: docs directory not found: {docs_dir}")
        return 2
    if not logo_path.exists():
        print(f"ERROR: logo image not found: {logo_path}")
        return 2

    shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    site_description = load_site_description(docs_dir / "_config.yml")

    logo = Image.open(logo_path).convert("RGBA")
    base_bg = create_base_background(width=args.width, height=args.height)

    generated = 0
    skipped_no_title = 0
    skipped_seo_disabled = 0
    seen_ids: dict[str, Path] = {}

    for src in iter_source_files(docs_dir):
        rel = src.relative_to(docs_dir)
        raw = src.read_text(encoding="utf-8", errors="replace")
        data = parse_front_matter(raw)

        if not is_seo_enabled(data):
            skipped_seo_disabled += 1
            continue

        title = str(data.get("title") or "").strip()
        if not title:
            skipped_no_title += 1
            continue

        subtitle = subtitle_for_page(data=data, rel_path=rel, site_description=site_description)
        og_id = og_id_for_path(rel)
        output_path = output_dir / f"{og_id}.png"

        existing = seen_ids.get(og_id)
        if existing and existing != rel:
            print(
                f"WARNING: duplicate og id '{og_id}' for {rel.as_posix()} and {existing.as_posix()}; using latest."
            )
        seen_ids[og_id] = rel

        render_card(base_bg=base_bg, logo=logo, title=title, subtitle=subtitle, output_path=output_path)
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
