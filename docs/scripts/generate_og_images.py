#!/usr/bin/env python3
"""Generate per-page Open Graph images for docs content."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
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

# ── Visual tuning ────────────────────────────────────────────────────
# Hero background
HERO_OPACITY = 150  # 0-255  (~83 %).  Lower = more transparent hero.

# Corner gradient (bottom-left → top-right) for text legibility
GRADIENT_FADE_START = 0.35  # Vertical fade begins at 35 % from top
GRADIENT_VERT_WEIGHT = 0.78  # How much the vertical axis contributes
GRADIENT_HORIZ_WEIGHT = 0.22  # How much the horizontal axis contributes
GRADIENT_CURVE = 1.2  # Power-curve exponent (>1 = darker near corner)
GRADIENT_MAX_ALPHA = 235  # Peak darkness at the corner (0-255)
# Token used to tint the legibility gradient.
GRADIENT_COLOR_TOKEN = "color-header-bg"
TOKEN_HEADER_BG = "color-header-bg"
TOKEN_HEADER_BG_END = "color-header-bg-end"


# ── CLI ──────────────────────────────────────────────────────────────


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


# ── Front-matter / config helpers ────────────────────────────────────


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


def load_css_hex_tokens(variables_scss_path: Path) -> dict[str, tuple[int, int, int]]:
    tokens: dict[str, tuple[int, int, int]] = {}
    if not variables_scss_path.exists():
        return tokens

    pattern = re.compile(r"^\s*--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;")
    for line in variables_scss_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        name = match.group(1)
        hex_value = match.group(2).lstrip("#")
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)
        tokens[name] = (r, g, b)
    return tokens


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
        if second in SECTION_DEFAULT_SUBTITLE:
            return second
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


# ── Background composition ──────────────────────────────────────────


def create_token_background(
    width: int,
    height: int,
    color_start: tuple[int, int, int],
    color_end: tuple[int, int, int],
) -> Image.Image:
    """Subtle diagonal gradient using the site header colours."""

    bg = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    px = bg.load()
    for y in range(height):
        y_ratio = y / max(height - 1, 1)
        for x in range(width):
            x_ratio = x / max(width - 1, 1)
            t = max(0.0, min(1.0, 0.62 * x_ratio + 0.38 * y_ratio))
            r = int(color_start[0] + (color_end[0] - color_start[0]) * t)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * t)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * t)
            px[x, y] = (r, g, b, 255)
    return bg


def create_corner_gradient(
    width: int,
    height: int,
    gradient_rgb: tuple[int, int, int],
) -> Image.Image:
    """Dark gradient radiating from the bottom-left corner.

    Strongest where text is rendered (bottom / bottom-left), fading
    diagonally towards the top-right so the hero image stays visible.
    Built from two 1-D strips resized to full canvas – O(W+H) Python
    work instead of O(W×H).
    """
    # ── vertical strip: transparent at top, opaque at bottom ────────
    vert_strip = Image.new("L", (1, height), 0)
    vert_px = vert_strip.load()
    for y in range(height):
        t = (y / max(height - 1, 1) - GRADIENT_FADE_START) / (1.0 - GRADIENT_FADE_START)
        vert_px[0, y] = int(255 * max(0.0, t))
    vert = vert_strip.resize((width, height), Image.Resampling.BILINEAR)

    # ── horizontal strip: opaque at left, transparent at right ──────
    horiz_strip = Image.new("L", (width, 1), 0)
    horiz_px = horiz_strip.load()
    for x in range(width):
        horiz_px[x, 0] = int(255 * (1.0 - x / max(width - 1, 1)))
    horiz = horiz_strip.resize((width, height), Image.Resampling.BILINEAR)

    # ── weighted blend (vertical-dominant) ──────────────────────────
    vert_w = vert.point(lambda v: int(v * GRADIENT_VERT_WEIGHT))
    horiz_w = horiz.point(lambda v: int(v * GRADIENT_HORIZ_WEIGHT))
    combined = ImageChops.add(vert_w, horiz_w)

    # ── apply easing curve → alpha channel ──────────────────────────
    lut = [min(255, int((v / 255.0) ** GRADIENT_CURVE * GRADIENT_MAX_ALPHA)) for v in range(256)]
    alpha_channel = combined.point(lut)

    layer = Image.new("RGBA", (width, height), (gradient_rgb[0], gradient_rgb[1], gradient_rgb[2], 255))
    layer.putalpha(alpha_channel)
    return layer


def create_base_background(
    width: int,
    height: int,
    hero_bg_path: Path,
    css_tokens: dict[str, tuple[int, int, int]],
) -> Image.Image:
    """Compose the card background: token base → hero overlay → corner gradient."""
    header_bg = css_tokens.get(TOKEN_HEADER_BG, (44, 62, 80))
    gradient_color = css_tokens.get(GRADIENT_COLOR_TOKEN, header_bg)

    # 1. Base color behind hero matches the gradient color token exactly.
    base = create_token_background(width, height, gradient_color, gradient_color)

    # 2. Hero photograph with reduced opacity
    hero_raw = Image.open(hero_bg_path).convert("RGB")
    hero = ImageOps.fit(
        hero_raw,
        (width, height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    ).convert("RGBA")
    hero.putalpha(HERO_OPACITY)
    base = Image.alpha_composite(base, hero)

    # 3. Corner gradient overlay for text legibility
    gradient = create_corner_gradient(width, height, gradient_color)
    return Image.alpha_composite(base, gradient).convert("RGBA")


# ── Typography helpers ───────────────────────────────────────────────


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


# ── Card rendering ───────────────────────────────────────────────────


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
    text_max_width = canvas.width - text_left - text_right

    title_font, title_lines, title_line_height = choose_title_layout(
        draw, title, max_width=text_max_width, max_lines=3
    )

    title_gap = 10
    title_height = title_line_height * len(title_lines)
    if len(title_lines) > 1:
        title_height += title_gap * (len(title_lines) - 1)

    subtitle_font = load_font(34, bold=False)
    subtitle_text = truncate_to_width(draw, subtitle, subtitle_font, max_width=text_max_width)
    subtitle_gap = 24
    subtitle_height = 0
    if subtitle_text:
        sub_box = draw.textbbox((0, 0), "Ag", font=subtitle_font)
        subtitle_height = sub_box[3] - sub_box[1]

    total_text_block_height = title_height
    if subtitle_text:
        total_text_block_height += subtitle_gap + subtitle_height

    bottom_padding = 86
    min_top_padding = 116
    block_top = canvas.height - bottom_padding - total_text_block_height
    if block_top < min_top_padding:
        block_top = min_top_padding

    current_y = block_top
    for line in title_lines:
        draw.text((text_left, current_y), line, fill=(255, 255, 255, 255), font=title_font)
        current_y += title_line_height + title_gap

    if subtitle_text:
        subtitle_y = current_y - title_gap + subtitle_gap
        draw.text(
            (text_left, subtitle_y),
            subtitle_text,
            fill=(203, 213, 224, 255),
            font=subtitle_font,
        )

    draw_logo(canvas, logo)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, format="PNG", optimize=True)


# ── Entry point ──────────────────────────────────────────────────────


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    docs_dir = (repo_root / args.docs_dir).resolve()
    output_dir = (repo_root / args.output_dir).resolve()
    logo_path = (repo_root / args.logo_path).resolve()
    hero_bg_path = (repo_root / args.hero_bg_path).resolve()

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

    logo = Image.open(logo_path).convert("RGBA")
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
                f"WARNING: duplicate og id '{og_id}' for {rel.as_posix()} "
                f"and {existing.as_posix()}; using latest."
            )
        seen_ids[og_id] = rel

        render_card(
            base_bg=base_bg,
            logo=logo,
            title=title,
            subtitle=subtitle,
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
