"""Tests for tools/assets/model_standards.py."""

import model_standards
import pytest

# path -> (triangle target, error ceiling)
_CASES = {
    "weapon": ("gfx/models/units/weapons/G3.mesh", (1000, 0.01)),
    "tank": ("gfx/models/units/tanks/SOV/T72A.mesh", (5000, 0.005)),
    "ship": ("gfx/models/units/ships/USA/LHD.mesh", (8000, 0.005)),
    "plane": ("gfx/models/units/planes/USA/F35.mesh", (6000, 0.005)),
    "windows path": ("gfx\\models\\units\\Vehicles\\M35.mesh", (5000, 0.005)),
    "no target": ("gfx/models/buildings/radar.mesh", (None, 0.005)),
    "leading folder": ("weapons/G3.mesh", (1000, 0.01)),
}


@pytest.mark.parametrize("path, expected", _CASES.values(), ids=_CASES.keys())
def test_settings_follow_the_model_folder(path, expected):
    found = (model_standards.triangle_target(path), model_standards.error_ceiling(path))
    assert found == expected


# path -> mipmap rule
_MIPMAP_CASES = {
    "model texture": ("gfx/models/units/tanks/SOV/T72A.dds", "needed"),
    "particle": ("gfx/particles/smoke.dds", "needed"),
    "focus icon": ("gfx/interface/goals/focus_x.dds", "none"),
    "leader portrait": ("gfx/leaders/USA/portrait.dds", "none"),
    "terrain": ("map/terrain/atlas0.dds", "keep"),
    "font": ("gfx/fonts/hoi_16.dds", "keep"),
    "map arrow": ("gfx/maparrows/railway_pattern.dds", "keep"),
    "outside the game folders": ("docs/picture.dds", "keep"),
}


@pytest.mark.parametrize("path, rule", _MIPMAP_CASES.values(), ids=_MIPMAP_CASES.keys())
def test_mipmap_rule_follows_the_texture_folder(path, rule):
    assert model_standards.mipmap_rule(path) == rule


# path -> texture format
_FORMAT_CASES = {
    "model texture": ("gfx/models/units/tanks/SOV/T72A.dds", "compressed"),
    "event picture": ("gfx/event_pictures/europe/a.dds", "dxt5"),
    "loading screen": ("gfx/loadingscreens/load_1.dds", "compressed"),
    "leader portrait": ("gfx/leaders/USA/portrait.dds", "portrait"),
    "focus icon": ("gfx/interface/goals/focus_x.dds", "icon"),
    "tech icon": ("gfx/interface/technologies/FRA/a.dds", "icon"),
    "idea icon": ("gfx/interface/ideas/FRA/a.dds", "icon"),
    "other gui art": ("gfx/interface/topbar/a.dds", "raw"),
    "terrain": ("map/terrain/atlas0.dds", "keep"),
    "particle": ("gfx/particles/smoke.dds", "keep"),
    "outside the game folders": ("docs/picture.dds", "keep"),
}


@pytest.mark.parametrize(
    "path, expected", _FORMAT_CASES.values(), ids=_FORMAT_CASES.keys()
)
def test_texture_format_follows_the_folder(path, expected):
    assert model_standards.texture_format(path) == expected
