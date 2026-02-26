"""Rendering primitives for OG image generation."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .config import (
    GRADIENT_COLOR_TOKEN,
    GRADIENT_CURVE,
    GRADIENT_FADE_START,
    GRADIENT_HORIZ_WEIGHT,
    GRADIENT_MAX_ALPHA,
    GRADIENT_VERT_WEIGHT,
    HERO_OPACITY,
    TOKEN_HEADER_BG,
)

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "Pillow is required. Install with: python3 -m pip install pillow"
    ) from exc


def create_token_background(
    width: int,
    height: int,
    color_start: tuple[int, int, int],
    color_end: tuple[int, int, int],
) -> Image.Image:
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
    vert_strip = Image.new("L", (1, height), 0)
    vert_px = vert_strip.load()
    for y in range(height):
        t = (y / max(height - 1, 1) - GRADIENT_FADE_START) / (1.0 - GRADIENT_FADE_START)
        vert_px[0, y] = int(255 * max(0.0, t))
    vert = vert_strip.resize((width, height), Image.Resampling.BILINEAR)

    horiz_strip = Image.new("L", (width, 1), 0)
    horiz_px = horiz_strip.load()
    for x in range(width):
        horiz_px[x, 0] = int(255 * (1.0 - x / max(width - 1, 1)))
    horiz = horiz_strip.resize((width, height), Image.Resampling.BILINEAR)

    vert_w = vert.point(lambda v: int(v * GRADIENT_VERT_WEIGHT))
    horiz_w = horiz.point(lambda v: int(v * GRADIENT_HORIZ_WEIGHT))
    combined = ImageChops.add(vert_w, horiz_w)

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
    header_bg = css_tokens.get(TOKEN_HEADER_BG, (44, 62, 80))
    gradient_color = css_tokens.get(GRADIENT_COLOR_TOKEN, header_bg)

    base = create_token_background(width, height, gradient_color, gradient_color)

    hero_raw = Image.open(hero_bg_path).convert("RGB")
    hero = ImageOps.fit(
        hero_raw,
        (width, height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    ).convert("RGBA")
    hero.putalpha(HERO_OPACITY)
    base = Image.alpha_composite(base, hero)

    gradient = create_corner_gradient(width, height, gradient_color)
    return Image.alpha_composite(base, gradient).convert("RGBA")


@lru_cache(maxsize=64)
def _cached_font(size: int, bold: bool) -> ImageFont.ImageFont:
    candidates: list[str] = []
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


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    return _cached_font(size, bold)


def load_logo_rgba(logo_path: Path) -> Image.Image:
    return Image.open(logo_path).convert("RGBA")


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


def draw_centered_logo(image: Image.Image, logo: Image.Image) -> None:
    if logo.width <= 0 or logo.height <= 0:
        return

    target_height = 210
    ratio = target_height / logo.height
    target_width = max(1, int(logo.width * ratio))
    resized = logo.resize((target_width, target_height), resample=Image.Resampling.LANCZOS)

    x = (image.width - target_width) // 2
    y = int(image.height * 0.5) - (target_height // 2) - 40
    image.alpha_composite(resized, dest=(x, y))


def render_card(
    base_bg: Image.Image,
    logo: Image.Image,
    title: str,
    subtitle: str,
    page_path: str,
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

    path_font = load_font(22, bold=False)
    path_text = truncate_to_width(draw, page_path, path_font, max_width=text_max_width)
    path_gap = 20
    path_height = 0
    if path_text:
        path_box = draw.textbbox((0, 0), "Ag", font=path_font)
        path_height = path_box[3] - path_box[1]

    total_text_block_height = title_height
    if subtitle_text:
        total_text_block_height += subtitle_gap + subtitle_height
    if path_text:
        total_text_block_height += path_gap + path_height

    bottom_padding = 75
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
        path_anchor_y = subtitle_y + subtitle_height
    else:
        path_anchor_y = current_y - title_gap

    if path_text:
        path_y = path_anchor_y + path_gap
        draw.text(
            (text_left, path_y),
            path_text,
            fill=(148, 163, 184, 255),
            font=path_font,
        )

    draw_logo(canvas, logo)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, format="PNG", optimize=True)


def render_home_card(
    base_bg: Image.Image,
    logo: Image.Image,
    output_path: Path,
) -> None:
    canvas = base_bg.copy()
    draw_centered_logo(canvas, logo)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, format="PNG", optimize=True)

