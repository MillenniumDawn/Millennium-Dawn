"""Tab icons and strip previews for add_international_system.py.

Premade icons reuse existing mod art: ledger icons already in the tab style,
including icons used elsewhere in the UI, and generic decision-category icons
recoloured to match. Custom images need transparency around their artwork.
"""

import base64
import io
import os
import re

from PIL import Image

ART_DIR = "gfx/interface/scripted_gui/missiles"
CATEGORY_DIR = "gfx/interface/decisions/decision_categories"
ICON_SIZE = (28, 27)
# The tab icons shade from light gold at the top to dark bronze at the bottom.
GOLD_TOP = (196, 166, 108)
GOLD_BOTTOM = (122, 68, 22)
STRIP_BACKGROUND = (38, 38, 38, 255)
STRIP_X = 10

# name: (source image, already in the tab style)
PREMADE_ICONS = {
    "missile": (f"{ART_DIR}/ledger_icon_small_missile.dds", True),
    "gear": (f"{ART_DIR}/ledger_icon_small_production.dds", True),
    "satellite": (f"{ART_DIR}/ledger_icon_small_satellite.dds", True),
    "space_station": (f"{ART_DIR}/ledger_icon_small_spaceorbit.dds", True),
    "caduceus": (f"{ART_DIR}/ledger_icon_small_ga.dds", True),
    "globe_wreath": (f"{ART_DIR}/ledger_icon_small_sc.dds", True),
    "masks": (f"{ART_DIR}/ledger_icon_small_sr.dds", True),
    "hands": (f"{ART_DIR}/ledger_icon_small_unaid.dds", True),
    "handshake": (
        f"{CATEGORY_DIR}/decision_category_generic_foreign_policy.dds",
        False,
    ),
    "industry": (f"{CATEGORY_DIR}/decision_category_generic_industry.dds", False),
    "arms_trade": (f"{CATEGORY_DIR}/decision_category_generic_arms_trade.dds", False),
    "propaganda": (f"{CATEGORY_DIR}/decision_category_generic_propaganda.dds", False),
    "resources": (
        f"{CATEGORY_DIR}/decision_category_generic_prospect_for_resources.dds",
        False,
    ),
    "naval": (f"{CATEGORY_DIR}/decision_category_naval_treaties.dds", False),
    "intervention": (
        f"{CATEGORY_DIR}/decision_category_intervention_overseas.dds",
        False,
    ),
}

SPRITE_RE = re.compile(r'name\s*=\s*"(\w+)"\s*texturefile\s*=\s*"([^"]+)"')
TAB_RE = re.compile(
    r'name\s*=\s*"(\w+)_gui_ledger_button"\s*position\s*=\s*\{\s*x\s*=\s*(\d+)'
)
ICON_RE = re.compile(
    r'name\s*=\s*"(\w+)"\s*spriteType\s*=\s*"(\w+)"\s*position\s*=\s*\{\s*x\s*=\s*(\d+)\s*y\s*=\s*(\d+)'
)


def restyle(image):
    """Fit an image into the tab icon box and shade it in the tab gold."""
    image = image.convert("RGBA")
    box = image.getchannel("A").point(lambda alpha: 255 if alpha > 16 else 0).getbbox()
    image = image.crop(box or (0, 0, *image.size))
    width, height = ICON_SIZE
    scale = min((width - 2) / image.size[0], (height - 2) / image.size[1])
    size = (max(1, round(image.size[0] * scale)), max(1, round(image.size[1] * scale)))
    fitted = Image.new("RGBA", ICON_SIZE)
    fitted.paste(
        image.resize(size, Image.Resampling.LANCZOS),
        ((width - size[0]) // 2, (height - size[1]) // 2),
    )
    out = Image.new("RGBA", ICON_SIZE)
    for y in range(height):
        mix = y / (height - 1)
        gold = [
            top + (bottom - top) * mix for top, bottom in zip(GOLD_TOP, GOLD_BOTTOM)
        ]
        for x in range(width):
            red, green, blue, alpha = fitted.getpixel((x, y))
            shade = 0.35 + 0.65 * (0.3 * red + 0.59 * green + 0.11 * blue) / 255
            out.putpixel(
                (x, y), tuple(int(channel * shade) for channel in gold) + (alpha,)
            )
    return out


def centred(image):
    """Place already-styled art on the tab icon canvas without recolouring it."""
    if image.size[0] > ICON_SIZE[0] or image.size[1] > ICON_SIZE[1]:
        image.thumbnail(ICON_SIZE, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", ICON_SIZE)
    offset = ((ICON_SIZE[0] - image.size[0]) // 2, (ICON_SIZE[1] - image.size[1]) // 2)
    canvas.paste(image, offset)
    return canvas


def tab_icon(repo, source):
    """Return the 28x27 tab icon for a premade name or an image path."""
    if source in PREMADE_ICONS:
        path, styled = PREMADE_ICONS[source]
        path = os.path.join(repo, path)
    else:
        path, styled = os.path.join(repo, source), False
    with Image.open(path) as image:
        image = image.convert("RGBA")
        if source not in PREMADE_ICONS:
            alpha = image.getchannel("A")
            if alpha.getextrema()[0] == 255:
                raise ValueError(
                    "custom icon has no transparency; use a PNG with a transparent background"
                )
            if alpha.point(lambda value: 255 if value > 16 else 0).getbbox() is None:
                raise ValueError("custom icon has no visible pixels")
        if styled:
            return centred(image)
        return restyle(image)


def narrow_frames(repo, wide, narrow):
    """Cut the middle out of each wide tab frame, keeping both ends."""
    with Image.open(
        os.path.join(repo, ART_DIR, "missiles_gui_ledger_btn.dds")
    ) as image:
        image = image.convert("RGBA")
    edge = narrow // 2
    height = image.size[1]
    out = Image.new("RGBA", (narrow * 2, height))
    for frame in range(2):
        left = frame * wide
        out.paste(image.crop((left, 0, left + edge, height)), (frame * narrow, 0))
        out.paste(
            image.crop((left + wide - (narrow - edge), 0, left + wide, height)),
            (frame * narrow + edge, 0),
        )
    return out


def render_strip(repo, menu, gfx, frames, frame_width, new_key, new_icon):
    """Draw the ledger strip `menu` as the game lays it out, the new tab selected."""
    textures = dict(SPRITE_RE.findall(gfx))
    tabs = TAB_RE.findall(menu)
    icons = [icon[1:] for icon in ICON_RE.findall(menu) if icon[0] != "trade_divider"]
    height = frames.size[1]
    strip = Image.new("RGBA", (550, height + 8), STRIP_BACKGROUND)
    for (key, x), (sprite, icon_x, icon_y) in zip(tabs, icons):
        selected = key == new_key
        left = frame_width if selected else 0
        strip.alpha_composite(
            frames.crop((left, 0, left + frame_width, height)), (STRIP_X + int(x), 4)
        )
        if selected:
            icon = new_icon
        elif sprite in textures and os.path.exists(
            os.path.join(repo, textures[sprite])
        ):
            with Image.open(os.path.join(repo, textures[sprite])) as image:
                icon = image.convert("RGBA")
        else:
            continue
        strip.alpha_composite(icon, (STRIP_X + int(icon_x), 4 + int(icon_y)))
    return strip


def png_base64(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def icon_catalog(repo):
    """Every premade icon that exists in this repo, as tab-styled PNG data."""
    return [
        {"name": name, "source": path, "png": png_base64(tab_icon(repo, name))}
        for name, (path, _) in PREMADE_ICONS.items()
        if os.path.exists(os.path.join(repo, path))
    ]
