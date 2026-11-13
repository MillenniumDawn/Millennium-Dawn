"""Tests for `validate_asset_data.py` (broken 3D model meshes and texture data)."""

import pytest
import validate_asset_data as V
from shared.suite import MESH_QUAD, dds_texture, mesh_bytes
from validator_common import Severity

ERROR, WARNING = Severity.ERROR, Severity.WARNING
MESH = "gfx/models/units/tank.mesh"
TEXTURE = "gfx/models/units/tank_diffuse.dds"
ICON = "gfx/interface/icon.dds"
GOOD_DDS = dds_texture(512, 512, mipmaps=10)
FLAT_DDS = dds_texture(512, 512, b"", mipmaps=10)
PNG = b"\x89PNG\r\n\x1a\n" + bytes(200)
JPEG = b"\xff\xd8\xff\xe0" + bytes(200)

needs_numpy = pytest.mark.skipif(V.audit_models is None, reason="needs numpy")


def _run(tmp_path, monkeypatch, files, staged):
    """Write the files and run; `staged` lists staged paths, None scans the tree.

    A file given as a dict is MESH_QUAD with those overrides.
    """
    for rel_path, data in files.items():
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, dict):
            data = mesh_bytes({**MESH_QUAD, **data})
        path.write_bytes(data)
    if staged is not None:
        monkeypatch.setenv("MD_STAGED_FILES", "\n".join(staged))
    validator = V.Validator(
        str(tmp_path), staged_only=staged is not None, use_colors=False
    )
    validator.run_validations()
    return validator


def _found(validator):
    return sorted((i.file, i.category, i.severity) for i in validator._issues)


# case: (file bytes, what it holds instead of DDS)
_FORMATS = {
    "dds": (GOOD_DDS, None),
    "png": (PNG, "PNG"),
    "jpeg": (JPEG, "JPEG"),
    "truncated dds": (b"DDS " + bytes(20), "TGA, truncated or unknown"),
}


@pytest.mark.parametrize("data, expected", _FORMATS.values(), ids=_FORMATS.keys())
def test_foreign_format(tmp_path, data, expected):
    path = tmp_path / "t.dds"
    path.write_bytes(data)
    assert V.foreign_format(path) == expected


# case: (files, staged paths, expected (file, category, severity))
_DDS_CASES = {
    "dds": ({ICON: GOOD_DDS}, [ICON], []),
    "png under gfx": ({ICON: PNG}, [ICON], [(ICON, "texture-not-dds-data", ERROR)]),
    "under map": (
        {"map/terrain/t.dds": PNG},
        ["map/terrain/t.dds"],
        [("map/terrain/t.dds", "texture-not-dds-data", ERROR)],
    ),
    "upper-case extension": (
        {"gfx/interface/I.DDS": PNG},
        ["gfx/interface/I.DDS"],
        [("gfx/interface/I.DDS", "texture-not-dds-data", ERROR)],
    ),
    "outside gfx and map": ({"resources/r.dds": PNG}, ["resources/r.dds"], []),
    "tree scan": (
        {ICON: PNG, "resources/r.dds": PNG},
        None,
        [(ICON, "texture-not-dds-data", ERROR)],
    ),
}


@pytest.mark.parametrize(
    "files, staged, expected", _DDS_CASES.values(), ids=_DDS_CASES.keys()
)
def test_dds_data(tmp_path, monkeypatch, files, staged, expected):
    assert _found(_run(tmp_path, monkeypatch, files, staged)) == expected


# case: (files, staged paths, expected (file, category, severity))
_MODEL_CASES = {
    "clean": ({MESH: {}, TEXTURE: GOOD_DDS}, [MESH, TEXTURE], []),
    "broken mesh": (
        {MESH: {"tri": [0, 1, 9]}},
        [MESH],
        [(MESH, "mesh-triangle-index-out-of-range", ERROR)],
    ),
    "unreadable mesh": ({MESH: b"junk"}, [MESH], [(MESH, "mesh-unreadable", ERROR)]),
    "triangles over target": (
        {"gfx/models/units/weapons/gun.mesh": {}},
        ["gfx/models/units/weapons/gun.mesh"],
        [("gfx/models/units/weapons/gun.mesh", "mesh-triangles", WARNING)],
    ),
    "texture format": (
        {TEXTURE: FLAT_DDS},
        [TEXTURE],
        [(TEXTURE, "texture-uncompressed", WARNING)],
    ),
    "png model texture": (
        {TEXTURE: PNG},
        [TEXTURE],
        [(TEXTURE, "texture-not-dds-data", ERROR)],
    ),
    "only staged files": (
        {MESH: {"tri": [0, 1, 9]}, TEXTURE: FLAT_DDS},
        [TEXTURE],
        [(TEXTURE, "texture-uncompressed", WARNING)],
    ),
    "mesh outside gfx/models": (
        {"gfx/entities/x.mesh": {"tri": [0, 1, 9]}},
        ["gfx/entities/x.mesh"],
        [],
    ),
    "tree scan": (
        {MESH: {"tri": [0, 1, 9]}, TEXTURE: FLAT_DDS, ICON: FLAT_DDS},
        None,
        [
            (MESH, "mesh-triangle-index-out-of-range", ERROR),
            (TEXTURE, "texture-uncompressed", WARNING),
        ],
    ),
}


@needs_numpy
@pytest.mark.parametrize(
    "files, staged, expected", _MODEL_CASES.values(), ids=_MODEL_CASES.keys()
)
def test_model_findings(tmp_path, monkeypatch, files, staged, expected):
    monkeypatch.setattr(
        V.audit_models.model_standards, "TRIANGLE_TARGETS", (("/weapons/", 1),)
    )
    assert _found(_run(tmp_path, monkeypatch, files, staged)) == expected


def test_without_numpy_only_the_dds_check_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "audit_models", None)

    validator = _run(tmp_path, monkeypatch, {MESH: b"junk", ICON: PNG}, [MESH, ICON])

    assert _found(validator) == [(ICON, "texture-not-dds-data", ERROR)]
    assert any("numpy is not installed" in line for line in validator.output_lines)
