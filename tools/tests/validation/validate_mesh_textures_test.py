"""Tests for `validate_mesh_textures.py` (textures a 3D model renders with)."""

import struct

import pytest
import validate_mesh_textures as V
from shared.suite import initialize_git_repository, run_git, write_under

ENTITY = "gfx/entities/test.gfx"
MESH = "gfx/models/units/test.mesh"
FULL = {"diff": "a_diffuse.dds", "n": "a_normal.dds", "spec": "a_specular.dds"}


def _prop(key, kind, values):
    head = (
        b"!" + bytes([len(key)]) + key.encode() + kind + struct.pack("<I", len(values))
    )
    if kind == b"s":
        return head + b"".join(
            struct.pack("<I", len(v) + 1) + v.encode() + b"\0" for v in values
        )
    fmt = "<i" if kind == b"i" else "<f"
    return head + b"".join(struct.pack(fmt, v) for v in values)


def _mesh(*shapes):
    """shapes: (shape name, [(shader, {prop: texture}), ...]) per shape."""
    data = b"@@b@" + _prop("pdxasset", b"i", [1, 0]) + b"[object\0"
    for shape, meshes in shapes:
        data += b"[[" + shape.encode() + b"\0"
        for shader, textures in meshes:
            data += b"[[[mesh\0" + _prop("p", b"f", [0.0, 1.0])
            data += b"[[[[material\0" + _prop("shader", b"s", [shader])
            for key, texture in textures.items():
                data += _prop(key, b"s", [texture])
    return data


def _pdxmesh(settings="", name="test_mesh"):
    return (
        "objectTypes = {\n"
        "\tpdxmesh = {\n"
        f'\t\tname = "{name}"\n'
        f'\t\tfile = "{MESH}"\n'
        f"{settings}"
        "\t}\n"
        "}\n"
    )


def _setting(index, name=None, **textures):
    lines = [f'\t\t\tname = "{name}"'] if name else []
    lines.append(f"\t\t\tindex = {index}")
    lines += [f'\t\t\ttexture_{k} = "{v}"' for k, v in textures.items()]
    return "\t\tmeshsettings = {\n" + "\n".join(lines) + "\n\t\t}\n"


@pytest.fixture
def run(tmp_path, monkeypatch):
    """Write a model and return the issues; `install` fakes a vanilla root."""

    def build(mesh, entity=None, textures=(), install=None):
        path = tmp_path / MESH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(mesh)
        write_under(tmp_path, ENTITY, entity or _pdxmesh())
        for texture in textures:
            write_under(tmp_path, texture, "")
        monkeypatch.setattr(V, "find_hoi4_install", lambda: install)
        validator = V.Validator(str(tmp_path), use_colors=False)
        validator.run_validations()
        return validator._issues

    return build


def test_parser_reads_shapes_meshes_and_textures():
    data = _mesh(
        ("hull", [("Collision", {"diff": ""})]),
        ("body", [("PdxMeshAdvanced", FULL), ("PdxMeshAdvanced", {"diff": "b.dds"})]),
    )

    materials = V.parse_mesh_materials(data)

    assert [(m.shape, m.index, m.shader) for m in materials] == [
        ("hull", 0, "Collision"),
        ("body", 0, "PdxMeshAdvanced"),
        ("body", 1, "PdxMeshAdvanced"),
    ]
    assert materials[1].textures["texture_normal"] == "a_normal.dds"
    assert materials[2].textures == {"texture_diffuse": "b.dds"}


def test_parser_rejects_a_file_without_the_header():
    with pytest.raises(V.MeshParseError):
        V.parse_mesh_materials(b"not a mesh")


def test_empty_texture_name_is_reported_at_the_pdxmesh(run):
    issues = run(_mesh(("body", [("PdxMeshAdvanced", dict(FULL, n="", spec=""))])))

    assert [i.category for i in issues] == ["mesh-texture-empty"]
    assert issues[0].file == ENTITY
    assert issues[0].line == 2
    assert "texture_normal, texture_specular" in issues[0].message


def test_collision_and_absent_slots_are_not_reported(run):
    mesh = _mesh(
        ("hull", [("Collision", {"diff": "", "n": "", "spec": ""})]),
        ("dummy", [("PdxMeshStandard", {})]),
    )

    assert run(mesh) == []


def test_named_meshsettings_fills_only_its_shape_and_index(run):
    mesh = _mesh(("body", [("PdxMeshAdvanced", FULL), ("PdxMeshAdvanced", {"n": ""})]))

    assert run(mesh, _pdxmesh(_setting(1, "body", normal="x.dds"))) == []
    wrong_shape = run(mesh, _pdxmesh(_setting(1, "hull", normal="x.dds")))
    assert [i.category for i in wrong_shape] == ["mesh-texture-empty"]


def test_unnamed_meshsettings_counts_rendered_materials(run):
    mesh = _mesh(
        ("hull", [("Collision", {"diff": ""})]),
        ("body", [("PdxMeshAdvanced", {"diff": ""})]),
    )

    assert run(mesh, _pdxmesh(_setting(0, diffuse="x.dds"))) == []


def test_commented_pdxmesh_is_ignored(run):
    entity = "\n".join("#" + line for line in _pdxmesh().splitlines())

    assert run(_mesh(("body", [("PdxMeshAdvanced", {"diff": ""})])), entity) == []


def test_texture_name_resolves_anywhere_under_gfx(run, tmp_path):
    vanilla = tmp_path / "vanilla"
    (vanilla / "gfx" / "models").mkdir(parents=True)
    (vanilla / "gfx" / "models" / "a_specular.dds").write_bytes(b"")
    textures = ["gfx/models/other/a_diffuse.dds", "gfx/interface/A_NORMAL.dds"]

    assert (
        run(_mesh(("body", [("PdxMeshAdvanced", FULL)])), None, textures, vanilla) == []
    )


def test_unresolved_texture_name_is_reported(run, tmp_path):
    textures = ["gfx/models/a_diffuse.dds", "gfx/models/a_normal.dds"]
    mesh = _mesh(("body", [("PdxMeshAdvanced", FULL)]))

    issues = run(mesh, None, textures, tmp_path / "vanilla")

    assert [i.category for i in issues] == ["mesh-texture-missing"]
    assert "'a_specular.dds'" in issues[0].message


def test_unresolved_names_are_skipped_without_an_install(run):
    assert run(_mesh(("body", [("PdxMeshAdvanced", FULL)]))) == []


# case: (texture files and their bytes, expected categories)
_CLASH_CASES = {
    "one file": ({"gfx/models/a_diffuse.dds": b"model"}, []),
    "same name, different content": (
        {"gfx/models/a_diffuse.dds": b"model", "gfx/interface/A_DIFFUSE.dds": b"icon"},
        ["mesh-texture-name-clash"],
    ),
    "same name, same content": (
        {"gfx/models/a_diffuse.dds": b"same", "gfx/interface/a_diffuse.dds": b"same"},
        [],
    ),
    "name no model uses": (
        {"gfx/models/z.dds": b"model", "gfx/interface/z.dds": b"icon"},
        [],
    ),
}


@pytest.mark.parametrize(
    "textures, expected", _CLASH_CASES.values(), ids=_CLASH_CASES.keys()
)
def test_texture_name_clash(run, tmp_path, textures, expected):
    for rel_path, data in textures.items():
        write_under(tmp_path, rel_path, "").write_bytes(data)
    mesh = _mesh(("body", [("PdxMeshAdvanced", {"diff": "a_diffuse.dds"})]))

    issues = run(mesh)

    assert [i.category for i in issues] == expected
    assert all(i.severity == "warning" for i in issues)


def test_unreadable_mesh_is_reported(run):
    issues = run(b"@@b@?")

    assert [i.category for i in issues] == ["mesh-read-error"]


# case: (staged path, expected categories)
_STAGED_CASES = {
    "outside gfx": ("interface/x.dds", []),
    "mesh": (MESH, ["mesh-texture-empty"]),
    "texture": ("gfx/interface/x.dds", ["mesh-texture-empty"]),
    "mixed-case texture": ("gfx/interface/x.Dds", ["mesh-texture-empty"]),
    "other gfx file": ("gfx/interface/x.txt", ["mesh-texture-empty"]),
}


@pytest.mark.parametrize(
    "staged, expected", _STAGED_CASES.values(), ids=_STAGED_CASES.keys()
)
def test_staged_mode_runs_only_for_gfx_paths(tmp_path, monkeypatch, staged, expected):
    path = tmp_path / MESH
    path.parent.mkdir(parents=True)
    path.write_bytes(_mesh(("body", [("PdxMeshAdvanced", {"diff": ""})])))
    write_under(tmp_path, ENTITY, _pdxmesh())
    monkeypatch.setattr(V, "find_hoi4_install", lambda: None)

    if staged != MESH:
        write_under(tmp_path, staged, "")
    monkeypatch.setenv("MD_STAGED_FILES", staged)
    validator = V.Validator(str(tmp_path), staged_only=True)
    validator.run_validations()
    assert [i.category for i in validator._issues] == expected


def test_staged_rename_checks_texture_clashes(run, tmp_path, monkeypatch):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    run(
        _mesh(("body", [("PdxMeshAdvanced", {"diff": "a_diffuse.dds"})])),
        textures=["gfx/models/a_diffuse.dds"],
    )
    write_under(tmp_path, "source.dds", "different content")
    initialize_git_repository(tmp_path, ".")
    (tmp_path / "gfx/interface").mkdir()
    run_git(tmp_path, "mv", "source.dds", "gfx/interface/a_diffuse.DDS")

    validator = V.Validator(str(tmp_path), staged_only=True)
    validator.run_validations()

    assert [i.category for i in validator._issues] == ["mesh-texture-name-clash"]
    assert validator._issues[0].severity == "warning"


def test_empty_tree_is_clean(tmp_path):
    validator = V.Validator(str(tmp_path))
    validator.run_validations()

    assert validator._issues == []
