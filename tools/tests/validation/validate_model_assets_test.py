"""Tests for `validate_model_assets.py` (warnings on 3D model meshes and textures)."""

import pytest

pytest.importorskip("numpy")

import validate_model_assets as V
from shared.suite import MESH_QUAD, dds_texture, mesh_bytes
from validator_common import Severity

MESH = "gfx/models/units/tank.mesh"
TEXTURE = "gfx/models/units/tank_diffuse.dds"
GUI_TEXTURE = "gfx/interface/flat.dds"


def _run(tmp_path, monkeypatch, files, staged):
    """Write `{path: bytes}`; `staged` lists the staged paths, None scans the folder."""
    for rel_path, data in files.items():
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if staged is not None:
        monkeypatch.setenv("MD_STAGED_FILES", "\n".join(staged))
    validator = V.Validator(
        str(tmp_path), staged_only=staged is not None, use_colors=False
    )
    validator.run_validations()
    return validator


_BROKEN_MESH = mesh_bytes({**MESH_QUAD, "tri": [0, 1, 9]})
_FLAT_TEXTURE = dds_texture(512, 512, b"", mipmaps=10)

# case: (files, staged paths or None, expected (file, category) pairs)
_CASES = {
    "clean": (
        {MESH: mesh_bytes(MESH_QUAD), TEXTURE: dds_texture(512, 512, mipmaps=10)},
        [MESH, TEXTURE],
        [],
    ),
    "broken mesh": (
        {MESH: _BROKEN_MESH},
        [MESH],
        [(MESH, "model-triangle-index-out-of-range")],
    ),
    "unreadable mesh": ({MESH: b"junk"}, [MESH], [(MESH, "model-unreadable")]),
    "texture": ({TEXTURE: _FLAT_TEXTURE}, [TEXTURE], [(TEXTURE, "model-uncompressed")]),
    "only staged files": (
        {MESH: _BROKEN_MESH, TEXTURE: _FLAT_TEXTURE},
        [TEXTURE],
        [(TEXTURE, "model-uncompressed")],
    ),
    "outside gfx/models": ({GUI_TEXTURE: _FLAT_TEXTURE}, [GUI_TEXTURE], []),
    "folder scan": (
        {MESH: _BROKEN_MESH, TEXTURE: _FLAT_TEXTURE, GUI_TEXTURE: _FLAT_TEXTURE},
        None,
        [
            (MESH, "model-triangle-index-out-of-range"),
            (TEXTURE, "model-uncompressed"),
        ],
    ),
}


@pytest.mark.parametrize("files, staged, expected", _CASES.values(), ids=_CASES.keys())
def test_findings_are_warnings_on_model_files(
    tmp_path, monkeypatch, files, staged, expected
):
    issues = _run(tmp_path, monkeypatch, files, staged)._issues

    assert sorted((i.file, i.category) for i in issues) == expected
    assert all(i.severity == Severity.WARNING for i in issues)


def test_without_numpy_logs_a_notice_and_skips(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "audit_models", None)

    validator = _run(tmp_path, monkeypatch, {MESH: _BROKEN_MESH}, [MESH])

    assert validator._issues == []
    assert any("numpy is not installed" in line for line in validator.output_lines)
