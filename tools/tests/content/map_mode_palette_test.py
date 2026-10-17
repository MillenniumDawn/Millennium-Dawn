"""Colorblind separation contracts for the scripted map modes.

Colors are simulated with the Machado et al. (2009) matrices at full severity and
compared with CIEDE2000. Rules: .claude/docs/map-mode-reference.md.
"""

import itertools
import math
import re
from pathlib import Path

import pytest
from shared_utils import iter_statements, read_script

ROOT = Path(__file__).resolve().parents[3]
MAP_MODE_DIR = ROOT / "common/map_modes"
REFRESH_EFFECT_FILE = ROOT / "common/scripted_effects/00_map_mode_palette_effects.txt"
REFRESH_EFFECT = "refresh_palette_map_modes"
LEGEND_FILE = ROOT / "localisation/english/MD_map_modes_l_english.yml"
# Text colors from interface/core.gfx that vanish on the dark tooltip background
UNREADABLE_TEXT_CODES = {"Z", "b"}

STANDARD, RED_GREEN, BLUE_YELLOW = 0, 1, 2
PALETTES = (STANDARD, RED_GREEN, BLUE_YELLOW)

# vision: matrix applied to linear sRGB
MACHADO = {
    "normal": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "protan": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deutan": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritan": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}

# palette: {vision: smallest CIEDE2000 allowed between any two colors of one map mode}
CATEGORICAL_RULES = {
    STANDARD: {"normal": 10, "protan": 10, "deutan": 10, "tritan": 10},
    RED_GREEN: {"protan": 15, "deutan": 15},
    BLUE_YELLOW: {"tritan": 15},
}
# Ramps are ordered worst to best: brightness rises and neighbors stay this far apart.
RAMP_NEIGHBOR_MINIMUM = 10

# mode: kind. "party" has 25 colors, too many to reach the colorblind options' bar, so it
# keeps one palette that clears the Standard bar.
MAP_MODES = {
    "EU_map_mode": "categorical",
    "GCC_map_mode": "categorical",
    "SCO_map_mode": "categorical",
    "influence_map_mode": "categorical",
    "reserve_currency_map_mode": "categorical",
    "subideology_map_mode": "party",
    "gdp_c_map_mode": "ramp",
    "productivity_map_mode": "ramp",
    "energy_consumption_map_mode": "ramp",
    "unemployment_rate_map_mode": "ramp",
    "renewable_energy_hotspot_map_mode": "ramp",
}

_PALETTE_CONDITION = re.compile(r"\bmap_mode_palette\s*=\s*(\d+)")
_RGB = ("red", "green", "blue")


def _linear(channel):
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _lab(rgb, vision):
    matrix = MACHADO[vision]
    linear = [_linear(channel) for channel in rgb]
    r, g, b = (
        min(1.0, max(0.0, sum(matrix[row][col] * linear[col] for col in range(3))))
        for row in range(3)
    )
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def _ciede2000(lab1, lab2):
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2
    c_mean = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    g = 0.5 * (1 - math.sqrt(c_mean**7 / (c_mean**7 + 25**7)))
    a1, a2 = a1 * (1 + g), a2 * (1 + g)
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    h1 = math.degrees(math.atan2(b1, a1)) % 360
    h2 = math.degrees(math.atan2(b2, a2)) % 360
    dh = 0.0 if c1 * c2 == 0 else (h2 - h1 + 180) % 360 - 180
    dh_term = 2 * math.sqrt(c1 * c2) * math.sin(math.radians(dh / 2))
    l_mean, c_mean = (l1 + l2) / 2, (c1 + c2) / 2
    if c1 * c2 == 0:
        h_mean = h1 + h2
    elif abs(h1 - h2) <= 180:
        h_mean = (h1 + h2) / 2
    else:
        h_mean = (h1 + h2 + 360) / 2 if h1 + h2 < 360 else (h1 + h2 - 360) / 2
    t = (
        1
        - 0.17 * math.cos(math.radians(h_mean - 30))
        + 0.24 * math.cos(math.radians(2 * h_mean))
        + 0.32 * math.cos(math.radians(3 * h_mean + 6))
        - 0.20 * math.cos(math.radians(4 * h_mean - 63))
    )
    s_l = 1 + 0.015 * (l_mean - 50) ** 2 / math.sqrt(20 + (l_mean - 50) ** 2)
    s_c = 1 + 0.045 * c_mean
    s_h = 1 + 0.015 * c_mean * t
    r_t = (
        -2
        * math.sqrt(c_mean**7 / (c_mean**7 + 25**7))
        * math.sin(math.radians(60 * math.exp(-(((h_mean - 275) / 25) ** 2))))
    )
    dl, dc, dh_term = (l2 - l1) / s_l, (c2 - c1) / s_c, dh_term / s_h
    return math.sqrt(dl**2 + dc**2 + dh_term**2 + r_t * dc * dh_term)


def _distance(rgb1, rgb2, vision):
    return _ciede2000(_lab(rgb1, vision), _lab(rgb2, vision))


def _condition_palettes(limit):
    match = _PALETTE_CONDITION.search(limit or "")
    return {int(match.group(1))} if match else None


def _leaves(body, palettes, out):
    """Collect (palettes, rgb or partial channels) for every block that sets a color."""
    channels = {}
    chain_taken = set()
    for key, _, block in iter_statements(body):
        if block is None:
            continue
        if key == "set_temp_variable":
            for name, value, _ in iter_statements(block):
                if name in _RGB:
                    channels[name] = value
            continue
        if key == "if":
            chain_taken = set()
        branch = palettes - chain_taken
        if key in ("if", "else_if"):
            limit = next((b for k, _, b in iter_statements(block) if k == "limit"), "")
            condition = _condition_palettes(limit)
            if condition is not None:
                branch &= condition
                chain_taken |= condition
        else:
            chain_taken = set()
        _leaves(block, branch, out)
    if channels:
        out.append((palettes, channels))


def _parse_map_modes():
    modes = {}
    for path in sorted(MAP_MODE_DIR.glob("*.txt")):
        text = read_script(str(path))
        for _, _, root in iter_statements(text):
            for mode, _, body in iter_statements(root or ""):
                leaves = []
                for layer, _, layer_body in iter_statements(body or ""):
                    if layer in ("top", "bottom"):
                        _leaves(layer_body or "", set(PALETTES), leaves)
                modes[mode] = {
                    "leaves": leaves,
                    "palette_aware": "map_mode_palette" in (body or ""),
                }
    return modes


@pytest.fixture(scope="module")
def map_modes():
    return _parse_map_modes()


def _colors(mode_data, palette):
    return [
        tuple(float(channels[name]) for name in _RGB)
        for palettes, channels in mode_data["leaves"]
        if palette in palettes
    ]


def _closest_pair(colors, vision):
    return min(
        (_distance(a, b, vision), a, b) for a, b in itertools.combinations(colors, 2)
    )


# vision: (pair that a correct simulation keeps apart only in normal vision)
_CONFUSION_PAIRS = {
    "protan": ((0.6, 0.5, 0.2), (0.2, 0.55, 0.3)),
    "deutan": ((0.29, 0.788, 0.176), (1.0, 0.439, 0.098)),
    "tritan": ((1.0, 0.55, 0.05), (1.0, 0.5, 0.7)),
}


@pytest.mark.parametrize("vision", _CONFUSION_PAIRS)
def test_simulation_collapses_a_known_confusion_pair(vision):
    first, second = _CONFUSION_PAIRS[vision]
    assert _distance(first, second, "normal") >= 10
    assert _distance(first, second, vision) < 10


def test_every_map_mode_is_classified(map_modes):
    assert set(map_modes) == set(MAP_MODES)


@pytest.mark.parametrize("mode", MAP_MODES)
def test_every_color_sets_all_three_channels(map_modes, mode):
    for _, channels in map_modes[mode]["leaves"]:
        assert set(channels) == set(_RGB), (mode, channels)


@pytest.mark.parametrize("mode", MAP_MODES)
def test_every_palette_colors_every_category(map_modes, mode):
    counts = {p: len(_colors(map_modes[mode], p)) for p in PALETTES}
    assert min(counts.values()) > 1 and len(set(counts.values())) == 1, (mode, counts)


_CATEGORICAL_CASES = [
    (mode, palette, vision)
    for mode, kind in MAP_MODES.items()
    for palette, rules in CATEGORICAL_RULES.items()
    if kind == "categorical" or (kind == "party" and palette == STANDARD)
    for vision in rules
]


@pytest.mark.parametrize("mode,palette,vision", _CATEGORICAL_CASES)
def test_categorical_colors_stay_apart(map_modes, mode, palette, vision):
    distance, first, second = _closest_pair(_colors(map_modes[mode], palette), vision)
    minimum = CATEGORICAL_RULES[palette][vision]
    assert distance >= minimum, f"{first} vs {second}: {distance:.1f} < {minimum}"


_RAMPS = [mode for mode, kind in MAP_MODES.items() if kind == "ramp"]


@pytest.mark.parametrize(
    "mode", [m for m, kind in MAP_MODES.items() if kind != "categorical"]
)
def test_ramps_and_party_colors_have_one_palette(map_modes, mode):
    assert not map_modes[mode]["palette_aware"], mode


@pytest.mark.parametrize("mode", _RAMPS)
def test_ramp_brightness_rises_from_worst_to_best(map_modes, mode):
    lightness = [_lab(rgb, "normal")[0] for rgb in _colors(map_modes[mode], STANDARD)]
    assert lightness == sorted(lightness) and len(set(lightness)) == len(lightness)


@pytest.mark.parametrize("mode", _RAMPS)
@pytest.mark.parametrize("vision", MACHADO)
def test_ramp_neighbors_stay_apart(map_modes, mode, vision):
    colors = _colors(map_modes[mode], STANDARD)
    for first, second in zip(colors, colors[1:]):
        distance = _distance(first, second, vision)
        assert distance >= RAMP_NEIGHBOR_MINIMUM, f"{first} vs {second}: {distance:.1f}"


def test_map_mode_legends_use_readable_text_colors():
    with LEGEND_FILE.open(encoding="utf-8-sig") as handle:
        legends = [line for line in handle if "_map_mode_tooltip" in line]
    codes = {code for line in legends for code in re.findall(r"§(\w)", line)}
    assert legends and not codes & UNREADABLE_TEXT_CODES


def test_palette_setting_refreshes_every_palette_aware_mode(map_modes):
    effects = dict(
        (key, body)
        for key, _, body in iter_statements(read_script(str(REFRESH_EFFECT_FILE)))
    )
    refreshed = set(re.findall(r"\bmapmode\s*=\s*(\w+)", effects[REFRESH_EFFECT]))
    aware = {mode for mode, data in map_modes.items() if data["palette_aware"]}
    assert refreshed == aware
