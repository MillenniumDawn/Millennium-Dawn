"""Tests for tools/assets/optimize_mesh.py."""

import sys
from collections import Counter

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")

import optimize_mesh
import pdx_mesh
from shared.suite import MESH_QUAD as _QUAD
from shared.suite import mesh_bytes

_NAN = float("nan")


def _rows(base, rows):
    return [rows.get(i, base) for i in range(4)]


def _repair(part, joints=2):
    """Repair one part. Returns (fixes, mesh props, skin props)."""
    (found,) = pdx_mesh.mesh_parts(pdx_mesh.parse(mesh_bytes(part, joints=joints)))
    fixes = Counter()
    optimize_mesh.repair_part(found, fixes)
    skin = found.skin.props if found.skin else {}
    return {k: v for k, v in fixes.items() if v}, found.mesh.props, skin


# case: (part overrides, fixes)
_REPAIR_CASES = {
    "clean": ({}, {}),
    "zero normal": ({"n": _rows([0, 0, 1], {1: [0, 0, 0]})}, {"normals_rebuilt": 1}),
    "invalid normal": (
        {"n": _rows([0, 0, 1], {1: [_NAN, 0, 0]})},
        {"normals_rebuilt": 1},
    ),
    "long normal": (
        {"n": _rows([0, 0, 1], {2: [0, 0, 3]})},
        {"normals_renormalized": 1},
    ),
    "zero tangent": (
        {"ta": _rows([1, 0, 0, 1], {0: [0, 0, 0, 1]})},
        {"tangents_rebuilt": 1},
    ),
    "bad handedness": (
        {"ta": _rows([1, 0, 0, 1], {0: [1, 0, 0, -0.2]})},
        {"tangent_handedness_fixed": 1},
    ),
    "zero-area triangle": (
        {"tri": [0, 1, 2, 0, 2, 3, 0, 0, 1]},
        {"zero_area_triangles_removed": 1},
    ),
}


@pytest.mark.parametrize(
    "overrides, expected", _REPAIR_CASES.values(), ids=_REPAIR_CASES.keys()
)
def test_repair_counts_each_fix(overrides, expected):
    fixes, mesh, _ = _repair({**_QUAD, **overrides})
    assert fixes == expected
    np.testing.assert_allclose(mesh["n"][1].reshape(-1, 3), [[0, 0, 1]] * 4, atol=1e-6)
    tangents = mesh["ta"][1].reshape(-1, 4)
    np.testing.assert_allclose(np.linalg.norm(tangents[:, :3], axis=1), 1, atol=1e-6)
    np.testing.assert_allclose(np.abs(tangents[:, 3]), 1)
    assert mesh["tri"][1].size == 6


def test_rebuilt_tangent_follows_the_uv_direction():
    _, mesh, _ = _repair({**_QUAD, "ta": [[0, 0, 0, 1]] * 4})
    np.testing.assert_allclose(
        mesh["ta"][1].reshape(-1, 4), [[1, 0, 0, 1]] * 4, atol=1e-6
    )


def test_rebuilt_tangent_without_uvs_is_perpendicular_to_the_normal():
    part = {k: v for k, v in _QUAD.items() if k != "u0"}
    _, mesh, _ = _repair({**part, "ta": [[0, 0, 0, 1]] * 4})
    tangents = mesh["ta"][1].reshape(-1, 4)[:, :3]
    np.testing.assert_allclose(tangents @ [0, 0, 1], 0, atol=1e-6)
    np.testing.assert_allclose(np.linalg.norm(tangents, axis=1), 1, atol=1e-6)


def test_normal_of_a_flat_spot_falls_back_to_up():
    part = {"p": [[0, 0, 0]] * 3, "tri": [0, 1, 2], "n": [[0, 0, 0]] * 3}
    fixes, mesh, _ = _repair(part)
    assert fixes == {"normals_rebuilt": 3}
    np.testing.assert_allclose(mesh["n"][1].reshape(-1, 3), [[0, 0, 1]] * 3)
    assert mesh["tri"][1].size == 3


_HALF = [0.5, 0.5, 0, 0]
_PAIR = [0, 1, -1, -1]

# case: (ix, w, joints, fixes, expected ix, expected w)
_SKIN_CASES = {
    "clean": ([_PAIR] * 4, [_HALF] * 4, 2, {}, [_PAIR] * 4, [_HALF] * 4),
    "unweighted copies the nearest vertex": (
        _rows(_PAIR, {3: [-1, -1, -1, -1]}),
        _rows(_HALF, {3: [0, 0, 0, 0]}),
        2,
        {"unweighted_vertices_fixed": 1},
        [_PAIR] * 4,
        [_HALF] * 4,
    ),
    "all unweighted binds to the root": (
        [[-1, -1, -1, -1]] * 4,
        [[0, 0, 0, 0]] * 4,
        2,
        {"meshes_bound_to_root_joint": 1},
        [[0, -1, -1, -1]] * 4,
        [[1, 0, 0, 0]] * 4,
    ),
    "all unweighted without a skeleton stays": (
        [[-1, -1, -1, -1]] * 4,
        [[0, 0, 0, 0]] * 4,
        0,
        {},
        [[-1, -1, -1, -1]] * 4,
        [[0, 0, 0, 0]] * 4,
    ),
    "bad slots are cleared then renormalized": (
        _rows(_PAIR, {0: [0, 9, -1, -1], 1: [0, 1, -1, -1]}),
        _rows(_HALF, {0: [0.5, 0.5, 0, 0], 1: [0.5, _NAN, 0, 0], 2: [0.5, -0.5, 0, 0]}),
        2,
        {"bad_weight_slots_cleared": 3, "weights_renormalized": 3},
        _rows(_PAIR, {0: [0, -1, -1, -1], 1: [0, -1, -1, -1], 2: [0, -1, -1, -1]}),
        _rows(_HALF, {0: [1, 0, 0, 0], 1: [1, 0, 0, 0], 2: [1, 0, 0, 0]}),
    ),
    "weights are renormalized": (
        [_PAIR] * 4,
        _rows(_HALF, {2: [0.2, 0.2, 0, 0]}),
        2,
        {"weights_renormalized": 1},
        [_PAIR] * 4,
        [_HALF] * 4,
    ),
}


@pytest.mark.parametrize(
    "ix, w, joints, expected, new_ix, new_w",
    _SKIN_CASES.values(),
    ids=_SKIN_CASES.keys(),
)
def test_repair_skin(ix, w, joints, expected, new_ix, new_w):
    fixes, _, skin = _repair({**_QUAD, "ix": ix, "w": w}, joints)
    assert fixes == expected
    np.testing.assert_array_equal(skin["ix"][1].reshape(-1, 4), new_ix)
    np.testing.assert_allclose(skin["w"][1].reshape(-1, 4), new_w, atol=1e-6)


def test_repair_raises_the_declared_influence_count():
    part = {**_QUAD, "ix": [_PAIR] * 4, "w": [_HALF] * 4, "bones": 1}
    _, _, skin = _repair(part)
    assert skin["bones"][1][0] == 2


def test_repair_skips_a_skin_with_three_weight_slots():
    part = {**_QUAD, "ix": [_PAIR] * 4, "w": [[1, 0, 0]] * 4}
    fixes, _, skin = _repair(part)
    assert fixes == {} and skin["w"][1].size == 12


def _arrays(part):
    positions = np.asarray(part["p"], np.float32)
    attrs = {k: np.asarray(part[k], np.float32) for k in ("n", "ta", "u0") if k in part}
    return positions, np.asarray(part["tri"], np.uint32), attrs


# case: (normal of the duplicate vertex, vertices left after welding)
_WELD_CASES = {
    "close normals merge": ([0, 0.1, 1], 4),
    "a hard edge stays split": ([0, 1, 0], 5),
}


@pytest.mark.parametrize("normal, left", _WELD_CASES.values(), ids=_WELD_CASES.keys())
def test_weld_merges_only_close_normals(normal, left):
    normal = np.array(normal) / np.linalg.norm(normal)
    part = {
        "p": _QUAD["p"] + [_QUAD["p"][2]],
        "tri": [0, 1, 2, 0, 4, 3],
        "n": _QUAD["n"] + [normal],
        "ta": _QUAD["ta"] + [[0, 0, 1, 1]],
        "u0": _QUAD["u0"] + [_QUAD["u0"][2]],
    }
    positions, index, attrs = _arrays(part)
    positions, index, attrs, _ = optimize_mesh._weld_vertices(
        positions, index, attrs, {}
    )
    assert len(positions) == left
    assert set(index.tolist()) == set(range(left))
    np.testing.assert_allclose(np.linalg.norm(attrs["n"], axis=1), 1, atol=1e-6)
    np.testing.assert_allclose(
        np.sum(attrs["ta"][:, :3] * attrs["n"], axis=1), 0, atol=1e-5
    )


_A, _B, _C = (np.array([v], float) for v in ([0, 0, 0], [1, 0, 0], [0, 1, 0]))

# case: (point, distance to the triangle (0,0,0) (1,0,0) (0,1,0))
_DISTANCE_CASES = {
    "above the inside": ([0.2, 0.2, 0.5], 0.5),
    "on the surface": ([0.5, 0.5, 0], 0),
    "past a corner": ([2, 0, 0], 1),
    "off the first edge": ([0.5, -1, 0], 1),
    "off the second edge": ([-1, 0.5, 0], 1),
    "off the long edge": ([1, 1, 0], 0.5**0.5),
}


@pytest.mark.parametrize(
    "point, expected", _DISTANCE_CASES.values(), ids=_DISTANCE_CASES.keys()
)
def test_point_triangle_distance(point, expected):
    found = optimize_mesh._point_triangle_distance(np.array([point], float), _A, _B, _C)
    assert found[0] == pytest.approx(expected)


def test_far_from_surface_settles_suspects_exactly(monkeypatch):
    # Two samples leave most of the triangle unsampled, so only the exact pass
    # can clear the near point.
    monkeypatch.setattr(optimize_mesh, "GUARD_SAMPLES", 2)
    positions = np.array([[0, 0, 0], [10, 0, 0], [0, 10, 0]], float)
    points = np.array([[3, 3, 0.01], [3, 3, 2]], float)
    far = optimize_mesh.far_from_surface(
        points, positions, np.array([[0, 1, 2]]), 0.5, np.random.default_rng(0)
    )
    assert far.tolist() == [False, True]


def test_surface_samples_of_a_degenerate_mesh_are_its_vertices():
    positions = np.zeros((3, 3))
    samples = optimize_mesh._surface_samples(
        positions, np.array([[0, 1, 2]]), 5, np.random.default_rng(0)
    )
    assert samples.shape == (3, 3)


def _plate(cells=23, spike=True, **extra):
    """A flat plate of 2 * cells^2 triangles, with an optional thin spike on it."""
    side = np.arange(cells + 1, dtype=float)
    x, y = np.meshgrid(side, side)
    points = np.c_[x.ravel(), y.ravel(), np.zeros(x.size)]
    corner = np.arange(cells * (cells + 1)).reshape(cells, cells + 1)[:, :-1].ravel()
    first = np.c_[corner, corner + 1, corner + cells + 2]
    second = np.c_[corner, corner + cells + 2, corner + cells + 1]
    triangles = np.vstack([first, second])
    if spike:
        tip = len(points)
        points = np.vstack([points, [[5, 5, 0], [5.2, 5, 0], [5.1, 5, 12]]])
        triangles = np.vstack([triangles, [[tip, tip + 1, tip + 2]]])
    count = len(points)
    part = {
        "p": points,
        "tri": triangles,
        "n": [[0, 0, 1]] * count,
        "ta": [[1, 0, 0, 1]] * count,
        "u0": points[:, :2] / cells,
    }
    return {**part, **extra}


class _FakeBackend:
    """Keeps the first plate row and whatever is locked; records each lock."""

    def __init__(self, obey_locks=True):
        self.obey_locks = obey_locks
        self.locks = []

    def simplify(self, index, positions, attributes, weights, lock, target, error):
        self.locks.append(lock.copy())
        triangles = index.reshape(-1, 3)
        flat = np.abs(positions[triangles][:, :, 2]).max(1) == 0
        keep = flat
        if self.obey_locks:
            keep = flat | lock[triangles].any(1)
        return np.ascontiguousarray(triangles[keep].ravel())

    def reorder(self, index, vertex_count):
        return index, np.arange(vertex_count)


def _optimize(part, backend, monkeypatch, joints=0):
    monkeypatch.setattr(optimize_mesh, "GUARD_SAMPLES", 4000)
    data = mesh_bytes(part, joints=joints)
    result, report = optimize_mesh.optimize_file(data, "gfx/models/x.mesh", backend)
    (found,) = pdx_mesh.mesh_parts(pdx_mesh.parse(result))
    return found, {k: v for k, v in report.items() if v}


def test_guard_locks_a_thin_part_the_simplifier_dropped(monkeypatch):
    backend = _FakeBackend()
    found, report = _optimize(_plate(), backend, monkeypatch)
    assert report["guard_retries"] == 1
    # One spike foot welds into the plate; the other foot and the tip come last.
    assert not backend.locks[0].any() and backend.locks[1][-2:].all()
    assert report["vertices_locked"] == backend.locks[1].sum() < 12
    assert found.triangles == report["triangles_before"] == 2 * 23 * 23 + 1
    assert found.mesh.props["p"][1].reshape(-1, 3)[:, 2].max() == 12


def test_guard_gives_up_and_keeps_the_mesh(monkeypatch):
    monkeypatch.setattr(optimize_mesh.model_standards, "GUARD_ATTEMPTS", 2)
    found, report = _optimize(_plate(), _FakeBackend(obey_locks=False), monkeypatch)
    assert report["guard_gave_up"] == 1 and report["guard_retries"] == 2
    assert found.triangles == report["triangles_after"] == 2 * 23 * 23 + 1


def _skin(count, split, soft=False):
    """Bone 0 left of `split`, bone 1 right of it, on a 24-wide plate."""
    right = (np.arange(count) % 24) >= split
    index = np.c_[right.astype(int), np.full((count, 3), -1)]
    weight = np.tile([1.0, 0, 0, 0], (count, 1))
    if soft:
        index[:, 1] = 1 - index[:, 0]
        weight[:, :2] = [0.6, 0.4]
    return {"ix": index, "w": weight}


# case: (soft skin, vertices locked before the first simplify call)
_SEAM_CASES = {
    "rigid skin locks the seam": (False, 48),
    "soft skin locks nothing": (True, 0),
}


@pytest.mark.parametrize("soft, locked", _SEAM_CASES.values(), ids=_SEAM_CASES.keys())
def test_bone_seams_are_locked_on_rigid_meshes(monkeypatch, soft, locked):
    backend = _FakeBackend()
    part = _plate(spike=False)
    _optimize(
        {**part, **_skin(len(part["p"]), 12, soft)}, backend, monkeypatch, joints=2
    )
    assert backend.locks[0].sum() == locked


def test_small_and_collision_meshes_are_left_alone(monkeypatch):
    backend = _FakeBackend()
    data = mesh_bytes(_QUAD, {**_plate(), "shader": "Collision"})
    result, report = optimize_mesh.optimize_file(data, "gfx/models/x.mesh", backend)
    assert result == data and backend.locks == []
    assert report["triangles_before"] == report["triangles_after"] == 2


def test_repair_only_keeps_the_triangle_count():
    data = mesh_bytes(_plate())
    result, report = optimize_mesh.optimize_file(data, "gfx/models/x.mesh")
    assert result == data
    assert report["triangles_before"] == report["triangles_after"]


def test_triangle_target_is_shared_out_by_part_size(monkeypatch):
    seen = []

    class _Recorder(_FakeBackend):
        def simplify(self, index, positions, attributes, weights, lock, target, error):
            seen.append((target, error))
            return index

    monkeypatch.setattr(optimize_mesh, "GUARD_SAMPLES", 4000)
    data = mesh_bytes(_plate(spike=False), _plate(spike=False))
    optimize_mesh.optimize_file(data, "gfx/models/units/ships/x.mesh", _Recorder())
    assert seen == [(4000, 0.005), (4000, 0.005)]


def test_meshopt_backend_simplifies_and_keeps_the_spike(monkeypatch):
    pytest.importorskip("meshoptimizer")
    found, report = _optimize(_plate(), optimize_mesh.MeshoptBackend(), monkeypatch)
    assert found.triangles < report["triangles_before"] // 2
    points = found.mesh.props["p"][1].reshape(-1, 3)
    assert points[:, 2].max() == 12
    assert found.mesh.props["tri"][1].max() == len(points) - 1


def test_meshopt_backend_explains_a_missing_package(monkeypatch):
    monkeypatch.setitem(sys.modules, "meshoptimizer", None)
    with pytest.raises(SystemExit, match="pip install meshoptimizer"):
        optimize_mesh.MeshoptBackend()


def _broken():
    return mesh_bytes({**_QUAD, "n": _rows([0, 0, 1], {1: [0, 0, 0]})})


# case: (file bytes, extra arguments, exit code, printed state, file rewritten)
_MAIN_CASES = {
    "dry run": (_broken(), [], 0, "would change: normals_rebuilt 1", False),
    "write": (_broken(), ["--write"], 0, "written: normals_rebuilt 1", True),
    "nothing to do": (mesh_bytes(_QUAD), ["--write"], 0, "unchanged: ", False),
    "unreadable": (b"junk", [], 1, "unreadable: missing @@b@ header", False),
}


@pytest.mark.parametrize(
    "data, flags, code, state, rewritten", _MAIN_CASES.values(), ids=_MAIN_CASES.keys()
)
def test_main_repair_only(tmp_path, capsys, data, flags, code, state, rewritten):
    path = tmp_path / "model.mesh"
    path.write_bytes(data)
    assert optimize_mesh.main(["--repair-only", *flags, str(path)]) == code
    captured = capsys.readouterr()
    assert f"{path}: {state}" in captured.out + captured.err
    assert (path.read_bytes() != data) == rewritten


def test_main_refuses_folders(tmp_path, capsys):
    assert optimize_mesh.main(["--repair-only", str(tmp_path)]) == 2
    assert "Name .mesh files, not folders" in capsys.readouterr().err


def test_main_uses_the_repo_relative_path_and_backend(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(optimize_mesh, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(optimize_mesh, "MeshoptBackend", _FakeBackend)
    path = tmp_path / "gfx" / "model.mesh"
    path.parent.mkdir()
    path.write_bytes(_broken())
    assert optimize_mesh.main([str(path)]) == 0
    assert "would change" in capsys.readouterr().out
