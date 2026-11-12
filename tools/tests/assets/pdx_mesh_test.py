"""Tests for tools/assets/pdx_mesh.py."""

import pytest

np = pytest.importorskip("numpy")

import pdx_mesh
from shared.suite import mesh_bytes

_TRIANGLE = {"p": [[0, 0, 0], [1, 0, 0], [0, 1, 0]], "tri": [0, 1, 2]}
_SKINNED = {**_TRIANGLE, "ix": [[1, -1, -1, -1]] * 3, "w": [[1, 0, 0, 0]] * 3}


def test_file_round_trips_byte_for_byte():
    data = mesh_bytes(_SKINNED, {**_TRIANGLE, "shader": "Collision"}, joints=2)
    assert pdx_mesh.write(pdx_mesh.parse(data)) == data


def test_mesh_parts_describe_each_mesh():
    data = mesh_bytes(_SKINNED, {**_TRIANGLE, "shader": "Collision"}, joints=2)
    first, second = pdx_mesh.mesh_parts(pdx_mesh.parse(data))
    assert (first.shader, first.rendered, first.triangles) == (
        "PdxMeshAdvanced",
        True,
        1,
    )
    assert (first.joints, first.root_joint, first.skin is not None) == (2, 0, True)
    assert (second.shader, second.rendered, second.skin) == ("Collision", False, None)


def test_mesh_without_material_or_geometry():
    root = pdx_mesh.parse(mesh_bytes(_TRIANGLE))
    shape = root.children[0].children[0]
    shape.children[0].children.clear()
    shape.children.append(pdx_mesh.Node("mesh", 3))
    (part,) = pdx_mesh.mesh_parts(root)
    assert part.shader == "" and part.joints == 0
    assert shape.child("skeleton") is None


# case: bytes that must not parse
_BROKEN = {
    "no header": b"nope",
    "unknown type": pdx_mesh.HEADER + b"!\x01ax\x00\x00\x00\x00",
    "unexpected byte": pdx_mesh.HEADER + b"?",
    "unterminated name": pdx_mesh.HEADER + b"[abc",
    "truncated values": mesh_bytes(_TRIANGLE)[:40],
    "truncated count": pdx_mesh.HEADER + b"!\x01ai\x05",
    "truncated string": pdx_mesh.HEADER + b"!\x01as\x01\x00\x00\x00\x09\x00\x00\x00ab",
}


@pytest.mark.parametrize("data", _BROKEN.values(), ids=_BROKEN.keys())
def test_broken_file_raises_parse_error(data):
    with pytest.raises(pdx_mesh.MeshParseError):
        pdx_mesh.parse(data)
