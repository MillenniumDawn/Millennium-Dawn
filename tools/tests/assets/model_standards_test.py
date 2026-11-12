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
