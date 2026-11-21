"""Tests for `validate_asset_data.py` (broken 3D model meshes and texture data)."""

import struct

import pytest
import validate_asset_data as V
from shared.suite import (
    MESH_QUAD,
    dds_texture,
    initialize_git_repository,
    mesh_bytes,
    run_git,
    run_tool_script,
)
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
def test_foreign_format(data, expected):
    assert V.foreign_format(data) == expected


# case: (files, staged paths, expected (file, category, severity))
_DDS_CASES = {
    "dds": ({ICON: dds_texture(16, 16, b"")}, [ICON], []),
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
    "mixed-case extension": (
        {"gfx/interface/I.Dds": PNG},
        ["gfx/interface/I.Dds"],
        [("gfx/interface/I.Dds", "texture-not-dds-data", ERROR)],
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
    "mixed-case mesh": (
        {"gfx/models/tank.Mesh": b"junk"},
        ["gfx/models/tank.Mesh"],
        [("gfx/models/tank.Mesh", "mesh-unreadable", ERROR)],
    ),
    "unrelated model file": (
        {"gfx/models/model.asset": b"junk"},
        ["gfx/models/model.asset"],
        [],
    ),
    "triangles over target": (
        {"gfx/models/units/weapons/gun.mesh": {}},
        ["gfx/models/units/weapons/gun.mesh"],
        [("gfx/models/units/weapons/gun.mesh", "mesh-triangles", WARNING)],
    ),
    "png model texture": (
        {TEXTURE: PNG},
        [TEXTURE],
        [(TEXTURE, "texture-not-dds-data", ERROR)],
    ),
    "only staged files": (
        {MESH: {"tri": [0, 1, 9]}, TEXTURE: FLAT_DDS},
        [TEXTURE],
        [(TEXTURE, "texture-art-standard", ERROR)],
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
            (ICON, "texture-art-standard", WARNING),
            (MESH, "mesh-triangle-index-out-of-range", ERROR),
            (TEXTURE, "texture-art-standard", WARNING),
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


def test_without_numpy_dds_checks_still_run(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "audit_models", None)

    validator = _run(
        tmp_path, monkeypatch, {MESH: b"junk", TEXTURE: FLAT_DDS}, [MESH, TEXTURE]
    )

    assert _found(validator) == [(TEXTURE, "texture-art-standard", ERROR)]
    assert any("numpy is not installed" in line for line in validator.output_lines)


def test_staged_rename_checks_destination(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    _run(tmp_path, monkeypatch, {"source.png": PNG}, None)
    initialize_git_repository(tmp_path, ".")
    (tmp_path / "gfx/interface").mkdir(parents=True)
    run_git(tmp_path, "mv", "source.png", ICON)

    validator = V.Validator(str(tmp_path), staged_only=True, use_colors=False)
    validator.run_validations()

    assert _found(validator) == [(ICON, "texture-not-dds-data", ERROR)]


def _set_u32(data, offset, value):
    head = bytearray(data)
    struct.pack_into("<I", head, offset, value)
    return bytes(head)


RAW_DDS = dds_texture(99, 120, b"")
DXT1_DDS = dds_texture(100, 120)
DXT5_DDS = dds_texture(100, 120, b"DXT5")

# case: (folder, header, expected guidance or None)
_ART_CASES = {
    "technology rejects DXT": ("gfx/interface/technologies", DXT1_DDS, V.RAW),
    "goal rejects DXT": ("gfx/interface/goals", DXT5_DDS, V.RAW),
    "idea rejects DXT": ("gfx/interface/ideas", DXT1_DDS, V.RAW),
    "icon accepts raw": ("gfx/interface/ideas", RAW_DDS, None),
    "GUI compression stays eligible": ("gfx/interface", DXT1_DDS, None),
    "legacy DXT3 GUI background": (
        "gfx/interface",
        dds_texture(120, 120, b"DXT3"),
        None,
    ),
    "GUI mipmaps": ("gfx/interface", GOOD_DDS, "remove mipmaps"),
    "bad channel masks": ("gfx/interface", _set_u32(RAW_DDS, 92, 0xFF), V.RAW),
    "missing alpha flag": ("gfx/interface", _set_u32(RAW_DDS, 80, 0x40), V.RAW),
    "DX10": ("gfx/interface", dds_texture(16, 16, b"DX10"), "legacy DDS header"),
    "16-bit": ("gfx/interface", dds_texture(16, 16, b"", bits=16), V.RAW),
    "24-bit": ("gfx/interface", dds_texture(16, 16, b"", bits=24), V.RAW),
    "8-bit": ("gfx/interface", dds_texture(16, 16, b"", bits=8), V.RAW),
    "zero-sized template": ("gfx/interface", dds_texture(42, 0), "image dimensions"),
    "malformed header": ("gfx/interface", _set_u32(RAW_DDS, 4, 0), "header size"),
    "small portrait": ("gfx/leaders/TAG", dds_texture(120, 99), V.RAW),
    "100 px portrait": ("gfx/leaders", DXT1_DDS, None),
    "flat large portrait": ("gfx/leaders", dds_texture(120, 100, b""), None),
    "DXT1 event art": ("gfx/event_pictures", DXT1_DDS, "use DXT5"),
    "DXT5 event art": ("gfx/event_pictures", DXT5_DDS, None),
    "flat event art": ("gfx/event_pictures", RAW_DDS, None),
    "loading screen DXT5": ("gfx/loadingscreens", DXT5_DDS, None),
    "raw main menu": ("gfx/main_menu", RAW_DDS, "use DXT1 or DXT5"),
    "model without mipmaps": ("gfx/models", DXT1_DDS, "add mipmaps"),
    "particle without mipmaps": ("gfx/particles", RAW_DDS, "add mipmaps"),
    "particle format left alone": ("gfx/particles", FLAT_DDS, None),
    "tiny texture": ("gfx/models", dds_texture(4, 4), None),
    "terrain left alone": ("map/terrain", dds_texture(16, 16, b"DX10"), None),
    "fonts left alone": ("gfx/fonts", GOOD_DDS, None),
    "map arrows left alone": ("gfx/maparrows", GOOD_DDS, None),
}


@pytest.mark.parametrize(
    "folder, header, guidance", _ART_CASES.values(), ids=_ART_CASES.keys()
)
def test_texture_standard(tmp_path, monkeypatch, folder, header, guidance):
    monkeypatch.setattr(V, "audit_models", None)
    name = f"{folder}/test icon.DdS"
    validator = _run(tmp_path, monkeypatch, {name: header}, [name])
    if guidance is None:
        assert not validator._issues
    else:
        (issue,) = validator._issues
        assert (issue.file, issue.category, issue.severity) == (
            name,
            "texture-art-standard",
            ERROR,
        )
        assert guidance in issue.message
        assert f"python3 tools/assets/dds_standardize.py '{name}'" in issue.message


def test_explicit_pr_scope_is_strict(tmp_path, monkeypatch):
    bad = "gfx/interface/ideas/bad icon.DDS"
    untouched = "gfx/interface/goals/backlog.dds"
    missing = "gfx/interface/missing.dds"
    _run(tmp_path, monkeypatch, {bad: DXT1_DDS, untouched: DXT1_DDS}, None)
    paths = tmp_path / "changed-dds.nul"
    paths.write_bytes(f"{bad}\0{missing}\0".encode())
    result = run_tool_script(
        "validation/validate_asset_data.py",
        "--path",
        tmp_path,
        "--texture-paths-from",
        paths,
        "--strict",
        "--no-color",
    )
    assert result.returncode == 1, result.stderr
    assert bad in result.stderr
    assert missing in result.stderr
    assert untouched not in result.stderr


# case: (target relative to mod, staged mode)
_LINK_CASES = {
    "renamed target": ("image.png", True),
    "outside root": ("../image.png", True),
    "tree scan": ("image.png", False),
}


@pytest.mark.parametrize("target, staged", _LINK_CASES.values(), ids=_LINK_CASES.keys())
def test_dds_symlink_keeps_asset_name(tmp_path, monkeypatch, target, staged):
    mod = tmp_path / "mod"
    path = mod / ICON
    path.parent.mkdir(parents=True)
    source = mod / target
    source.write_bytes(PNG)
    try:
        path.symlink_to(source)
    except OSError:
        pytest.skip("symlinks unavailable")
    if staged:
        monkeypatch.setenv("MD_STAGED_FILES", ICON)
    validator = V.Validator(str(mod), staged_only=staged, use_colors=False)
    validator.run_validations()

    assert _found(validator) == [(ICON, "texture-not-dds-data", ERROR)]


# case: (asset name, target name, data, category, severity)
_MODEL_LINK_CASES = {
    "mesh error": (
        MESH,
        "source.bin",
        {"tri": [0, 1, 9]},
        "mesh-triangle-index-out-of-range",
        ERROR,
    ),
    "texture size warning": (
        TEXTURE,
        "source.mesh",
        dds_texture(384, 512, mipmaps=9),
        "texture-not-power-of-two",
        WARNING,
    ),
}


@needs_numpy
@pytest.mark.parametrize(
    "asset, target, data, category, severity",
    _MODEL_LINK_CASES.values(),
    ids=_MODEL_LINK_CASES.keys(),
)
def test_model_symlink_keeps_severity(
    tmp_path, monkeypatch, asset, target, data, category, severity
):
    _run(tmp_path, monkeypatch, {target: data}, None)
    path = tmp_path / asset
    path.parent.mkdir(parents=True)
    try:
        path.symlink_to(tmp_path / target)
    except OSError:
        pytest.skip("symlinks unavailable")
    monkeypatch.setenv("MD_STAGED_FILES", asset)
    validator = V.Validator(str(tmp_path), staged_only=True, use_colors=False)
    validator.run_validations()

    assert _found(validator) == [(asset, category, severity)]
