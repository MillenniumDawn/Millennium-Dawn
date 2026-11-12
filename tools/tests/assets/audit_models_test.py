"""Tests for tools/assets/audit_models.py."""

import pytest

np = pytest.importorskip("numpy")

import audit_models
import pdx_mesh
from shared.suite import MESH_QUAD as _QUAD
from shared.suite import dds_texture, mesh_bytes

_SKIN = {"ix": [[0, 1, -1, -1]] * 4, "w": [[0.5, 0.5, 0, 0]] * 4}
_NAN = float("nan")


def _findings(part, joints=2):
    return dict(
        audit_models.mesh_findings(pdx_mesh.parse(mesh_bytes(part, joints=joints)))
    )


def _rows(base, rows):
    """`base` repeated for four vertices, with some rows replaced."""
    return [rows.get(i, base) for i in range(4)]


# case: (part overrides, joints, findings)
_MESH_CASES = {
    "clean": ({}, 2, {}),
    "clean skinned": (_SKIN, 2, {}),
    "zero normal": (
        {"n": _rows([0, 0, 1], {1: [0, 0, 0]})},
        2,
        {"normal_zero_length": 1},
    ),
    "invalid normal": (
        {"n": _rows([0, 0, 1], {0: [_NAN, 0, 1]})},
        2,
        {"n_invalid_values": 1, "normal_zero_length": 1},
    ),
    "long normal": ({"n": _rows([0, 0, 1], {2: [0, 0, 2]})}, 2, {"normal_not_unit": 1}),
    "zero tangent": (
        {"ta": _rows([1, 0, 0, 1], {3: [0, 0, 0, 1]})},
        2,
        {"tangent_zero_length": 1},
    ),
    "bad handedness": (
        {"ta": _rows([1, 0, 0, 1], {0: [1, 0, 0, 0]})},
        2,
        {"tangent_bad_handedness": 1},
    ),
    "zero-area triangle": ({"tri": [0, 1, 2, 0, 0, 3]}, 2, {"zero_area_triangles": 1}),
    "index out of range": ({"tri": [0, 1, 9]}, 2, {"triangle_index_out_of_range": 1}),
    "short uv array": ({"u0": [[0, 0]] * 3}, 2, {"u0_length_mismatch": 1}),
    "unweighted": (
        {"ix": _rows([0, -1, -1, -1], {}), "w": _rows([1, 0, 0, 0], {1: [0, 0, 0, 0]})},
        2,
        {"skin_unweighted": 1},
    ),
    "weights not normalized": (
        {"ix": _SKIN["ix"], "w": _rows([0.5, 0.5, 0, 0], {0: [0.5, 0.2, 0, 0]})},
        2,
        {"skin_weights_not_normalized": 1},
    ),
    "negative weight": (
        {"ix": _SKIN["ix"], "w": _rows([0.5, 0.5, 0, 0], {0: [1.5, -0.5, 0, 0]})},
        2,
        {"skin_negative_weights": 1},
    ),
    "invalid weight": (
        {"ix": _SKIN["ix"], "w": _rows([0.5, 0.5, 0, 0], {0: [_NAN, 0.5, 0, 0]})},
        2,
        {"skin_invalid_weights": 1},
    ),
    "bone outside skeleton": (
        {"ix": _rows([0, 1, -1, -1], {2: [0, 7, -1, -1]}), "w": _SKIN["w"]},
        2,
        {"skin_bone_index_out_of_range": 1},
    ),
    "skin without skeleton": (_SKIN, 0, {"skin_without_skeleton": 1}),
    "three weight slots": (
        {"ix": _SKIN["ix"], "w": [[1, 0, 0]] * 4},
        2,
        {"skin_not_four_slots": 1},
    ),
}


@pytest.mark.parametrize(
    "overrides, joints, expected", _MESH_CASES.values(), ids=_MESH_CASES.keys()
)
def test_mesh_findings(overrides, joints, expected):
    assert _findings({**_QUAD, **overrides}, joints) == expected


def test_collision_mesh_does_not_count_toward_triangles():
    data = mesh_bytes(_QUAD, {**_QUAD, "shader": "Collision"})
    assert audit_models.rendered_triangles(pdx_mesh.parse(data)) == 2


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_audit_mesh_reports_triangles_over_target(tmp_path, monkeypatch):
    monkeypatch.setattr(
        audit_models.model_standards, "TRIANGLE_TARGETS", (("/weapons/", 1),)
    )
    path = _write(tmp_path / "gun.mesh", mesh_bytes(_QUAD))
    assert audit_models.audit_mesh(path, "gfx/models/units/weapons/gun.mesh") == [
        "triangles 2 over target 1"
    ]
    assert audit_models.audit_mesh(path, "gfx/models/buildings/gun.mesh") == []


# case: (file bytes or None for a missing file, start of the only finding)
_UNREADABLE = {
    "corrupt": (b"junk", "unreadable: missing @@b@ header"),
    "missing": (None, "unreadable: "),
}


@pytest.mark.parametrize("data, start", _UNREADABLE.values(), ids=_UNREADABLE.keys())
def test_audit_mesh_reports_unreadable_file(tmp_path, data, start):
    path = tmp_path / "x.mesh"
    if data is not None:
        path.write_bytes(data)
    (finding,) = audit_models.audit_mesh(path, "x.mesh")
    assert finding.startswith(start)


def _dds(width, height, fourcc=b"DXT1", mipmaps=10):
    return dds_texture(width, height, fourcc, mipmaps)


# case: (file bytes, findings)
_TEXTURE_CASES = {
    "standard": (_dds(512, 512), []),
    "dxt5": (_dds(1024, 512, b"DXT5"), []),
    "tiny without mipmaps": (_dds(4, 4, mipmaps=1), []),
    "uncompressed": (_dds(512, 512, b""), ["uncompressed"]),
    "no mipmaps": (_dds(512, 512, mipmaps=1), ["no_mipmaps"]),
    "odd size": (_dds(500, 512), ["not_power_of_two"]),
    "too large": (_dds(4096, 4096), ["larger_than_2048"]),
    "dx10 header": (_dds(512, 512, b"DX10"), ["dx10_header"]),
    "png data": (b"\x89PNG" + bytes(200), ["not_dds_data"]),
    "short file": (b"DDS ", ["not_dds_data"]),
}


@pytest.mark.parametrize(
    "data, expected", _TEXTURE_CASES.values(), ids=_TEXTURE_CASES.keys()
)
def test_audit_texture(tmp_path, data, expected):
    assert audit_models.audit_texture(_write(tmp_path / "t.dds", data)) == expected


def test_audit_texture_reports_missing_file(tmp_path):
    (finding,) = audit_models.audit_texture(tmp_path / "gone.dds")
    assert finding.startswith("unreadable: ")


def _tree(root):
    models = root / "gfx" / "models"
    _write(models / "good.mesh", mesh_bytes(_QUAD))
    _write(models / "bad.mesh", mesh_bytes({**_QUAD, "tri": [0, 1, 9]}))
    _write(models / "sub" / "flat.dds", _dds(512, 512, b""))
    _write(models / "notes.txt", b"ignored")
    return models


def test_run_reports_only_files_with_findings(tmp_path):
    models = _tree(tmp_path)
    checked, report = audit_models.run([models, models / "good.mesh"], root=tmp_path)
    assert checked == 3
    assert report == {
        "gfx/models/bad.mesh": ["triangle_index_out_of_range x1"],
        "gfx/models/sub/flat.dds": ["uncompressed"],
    }


def test_run_keeps_paths_outside_the_root(tmp_path):
    models = _tree(tmp_path / "mod")
    _, report = audit_models.run([models / "bad.mesh"], root=tmp_path / "elsewhere")
    assert list(report) == [(models / "bad.mesh").as_posix()]


def test_main_prints_findings_and_totals(tmp_path, monkeypatch, capsys):
    _tree(tmp_path)
    monkeypatch.setattr(audit_models, "REPO_ROOT", tmp_path)
    assert audit_models.main([]) == 0
    out = capsys.readouterr().out
    assert "gfx/models/bad.mesh: triangle_index_out_of_range x1" in out
    assert "3 files checked, 2 with findings" in out
    assert "  uncompressed: 1 files" in out


def test_main_rejects_missing_path(tmp_path, capsys):
    assert audit_models.main([str(tmp_path / "nowhere")]) == 2
    assert "Not found" in capsys.readouterr().err
