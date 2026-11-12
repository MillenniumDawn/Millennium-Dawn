"""Tests for tools/assets/mesh_cap.py and optimize_mesh.py --max-triangles."""

from collections import Counter

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")

import mesh_cap
import optimize_mesh
import pdx_mesh
from shared.suite import mesh_bytes, mesh_plate


class _Thinner:
    """A stand-in simplifier: keeps `target` triangles spread evenly over the input.

    `seam_safe=False` makes the seam-preserving call return its input, so the
    seam-crossing call has to do the work. `head=True` keeps the first
    triangles instead, which makes a part shorter. `bridge=True` moves one
    corner of every kept seam-crossing triangle to the last vertex.
    """

    def __init__(self, seam_safe=True, head=False, bridge=False):
        self.seam_safe, self.head, self.bridge = seam_safe, head, bridge
        self.locks = []

    def simplify(self, index, positions, attributes, weights, lock, target, error):
        self.locks.append(lock.copy())
        triangles = index.reshape(-1, 3)
        if attributes.shape[1] != 2 or (weights.any() and not self.seam_safe):
            return index
        if self.head:
            keep = triangles[:target]
        else:
            keep = triangles[np.linspace(0, len(triangles) - 1, target).astype(int)]
        if self.bridge and not weights.any():
            keep = keep.copy()
            keep[:, 2] = len(positions) - 1
        return np.ascontiguousarray(keep.ravel())

    def reorder(self, index, vertex_count):
        return index, np.arange(vertex_count)


def _cap(parts, cap, backend, joints=0):
    """Cap a file. Returns (rendered parts, report, original bytes)."""
    data = mesh_bytes(*parts, joints=joints)
    result, report = optimize_mesh.optimize_file(
        data, "gfx/models/x.mesh", backend, cap
    )
    rendered = [p for p in pdx_mesh.mesh_parts(pdx_mesh.parse(result)) if p.rendered]
    return rendered, {k: v for k, v in report.items() if v}, data


def _positions(part):
    return part.mesh.props["p"][1].reshape(-1, 3)


def _two_plates():
    far = mesh_plate(spike=False, offset=(100, 0, 0))
    near = mesh_plate(spike=False)
    count = len(near["p"])
    merged = {
        key: np.vstack([np.asarray(near[key], float), np.asarray(far[key], float)])
        for key in ("p", "n", "ta", "u0")
    }
    merged["tri"] = np.vstack([near["tri"], far["tri"] + count])
    return merged


def test_every_part_keeps_its_share():
    (part,), report, _ = _cap([_two_plates()], 600, _Thinner())
    assert report["triangles_before"] == 2 * 1058 and report["triangles_after"] == 600
    x = _positions(part)[:, 0]
    triangles = part.mesh.props["tri"][1].reshape(-1, 3)
    left = (x[triangles] < 50).all(1).sum()
    assert left == 300 and len(triangles) - left == 300


def test_vertices_keep_original_positions_and_uvs():
    (part,), _, data = _cap([mesh_plate(spike=False)], 300, _Thinner())
    (source,) = pdx_mesh.mesh_parts(pdx_mesh.parse(data))
    known = {
        tuple(p): tuple(uv)
        for p, uv in zip(_positions(source), source.mesh.props["u0"][1].reshape(-1, 2))
    }
    for point, uv in zip(_positions(part), part.mesh.props["u0"][1].reshape(-1, 2)):
        assert known[tuple(point)] == tuple(uv)


# case: (height of a tiny triangle above the plate, parts pruned)
_PRUNE_CASES = {
    "a rivet on the plate is dropped": (0.05, 1),
    "a part sticking out is kept": (8.0, 0),
}


@pytest.mark.parametrize(
    "height, pruned", _PRUNE_CASES.values(), ids=_PRUNE_CASES.keys()
)
def test_tiny_parts(height, pruned):
    plate = mesh_plate(spike=False)
    count = len(plate["p"])
    speck = [[10, 10, height], [10.1, 10, height], [10, 10.1, height]]
    plate["p"] = np.vstack([plate["p"], speck])
    plate["tri"] = np.vstack([plate["tri"], [[count, count + 1, count + 2]]])
    for key, row in (("n", [0, 0, 1]), ("ta", [1, 0, 0, 1]), ("u0", [0.5, 0.5])):
        plate[key] = np.vstack([np.asarray(plate[key], float), [row] * 3])
    (part,), report, _ = _cap([plate], 400, _Thinner())
    assert report.get("parts_pruned", 0) == pruned
    assert (_positions(part)[:, 2].max() == pytest.approx(height)) == (pruned == 0)


def test_part_that_would_get_shorter_gets_more_triangles():
    # Keeping only the first rows of the plate makes it shorter, so the share doubles
    # until the kept rows span the plate again.
    (part,), report, _ = _cap([mesh_plate(spike=False)], 300, _Thinner(head=True))
    assert 300 < part.triangles == report["triangles_after"] < 1058
    assert np.ptp(_positions(part)[:, 1]) >= 0.92 * 23


def _two_islands(cells=23):
    """A plate whose right half is a second UV island: the middle column is split."""
    plate = mesh_plate(cells=cells, spike=False)
    points = np.asarray(plate["p"])
    uv = np.asarray(plate["u0"], float)
    middle = np.flatnonzero(points[:, 0] == cells // 2)
    copy = {int(v): len(points) + i for i, v in enumerate(middle)}
    triangles = np.asarray(plate["tri"]).copy()
    right = points[triangles][:, :, 0].mean(1) > cells // 2
    triangles[right] = np.vectorize(lambda v: copy.get(int(v), v))(triangles[right])
    extra = {"p": points[middle], "u0": uv[middle] + 5.0}
    uv[points[:, 0] > cells // 2] += 5.0
    plate["u0"] = uv
    for key in ("p", "n", "ta", "u0"):
        add = extra.get(key, np.asarray(plate[key], float)[middle])
        plate[key] = np.vstack([np.asarray(plate[key], float), add])
    plate["tri"] = triangles
    return plate


def test_seam_crossing_cut_takes_uvs_from_one_island():
    (part,), report, _ = _cap([_two_islands()], 300, _Thinner(seam_safe=False))
    assert report["triangles_after"] == 300
    uv = part.mesh.props["u0"][1].reshape(-1, 2)[
        part.mesh.props["tri"][1].reshape(-1, 3)
    ]
    in_second = uv[:, :, 0] > 2.5
    assert (in_second.all(1) | ~in_second.any(1)).all()


def test_corner_outside_the_island_gets_extended_uvs():
    (part,), report, _ = _cap(
        [_two_islands()], 300, _Thinner(seam_safe=False, bridge=True)
    )
    assert report["triangles_crossing_seams"] > 0
    uv = part.mesh.props["u0"][1].reshape(-1, 2)
    assert np.isfinite(uv).all()
    assert _positions(part)[:, 0].max() == 23


def _skin(count, split):
    right = (np.arange(count) % 24) >= split
    index = np.c_[right.astype(int), np.full((count, 3), -1)]
    return {"ix": index, "w": np.tile([1.0, 0, 0, 0], (count, 1))}


def test_rigid_bone_seams_are_locked():
    backend = _Thinner()
    plate = mesh_plate(spike=False)
    _cap([{**plate, **_skin(len(plate["p"]), 12)}], 300, backend, joints=2)
    cap_locks = [lock for lock in backend.locks if len(lock) and lock.any()]
    assert cap_locks and cap_locks[-1].sum() == 48


def test_cap_returns_its_best_try_when_it_cannot_be_met(monkeypatch):
    monkeypatch.setattr(mesh_cap.model_standards, "CAP_PRUNE_SIZES", (0.01, 0.02))
    (part,), report, _ = _cap([mesh_plate(spike=False)], 300, _Thinner(head=True))
    assert 300 < part.triangles == report["triangles_after"] < 1058


def test_model_under_the_cap_is_not_cut_again():
    backend = _Thinner()
    (part,), report, data = _cap([mesh_plate(spike=False)], 5000, backend)
    assert report["triangles_after"] == 1058
    assert all(lock.shape[0] and len(backend.locks) for lock in backend.locks)


def test_mesh_without_normals_or_triangles_is_left_alone():
    bare = {"p": [[0, 0, 0], [1, 0, 0], [0, 1, 0]], "tri": [0, 1, 2]}
    (found,) = pdx_mesh.mesh_parts(pdx_mesh.parse(mesh_bytes(bare)))
    mesh_cap.cap_part(found, 0.5, 0.1, _Thinner(), Counter())
    assert found.triangles == 1
    flat = {**bare, "tri": [0, 0, 1], "n": [[0, 0, 1]] * 3}
    (found,) = pdx_mesh.mesh_parts(pdx_mesh.parse(mesh_bytes(flat)))
    mesh_cap.cap_part(found, 0.5, 0.1, _Thinner(), Counter())
    assert found.triangles == 1


def test_meshopt_backend_reaches_the_cap_and_keeps_the_spike(monkeypatch):
    pytest.importorskip("meshoptimizer")
    monkeypatch.setattr(optimize_mesh, "GUARD_SAMPLES", 4000)
    (part,), report, _ = _cap(
        [mesh_plate(cells=40)], 400, optimize_mesh.MeshoptBackend()
    )
    assert report["triangles_after"] <= 400
    assert _positions(part)[:, 2].max() == 12


def test_main_passes_the_cap_through(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(optimize_mesh, "MeshoptBackend", _Thinner)
    path = tmp_path / "model.mesh"
    path.write_bytes(mesh_bytes(mesh_plate(spike=False)))
    assert optimize_mesh.main(["--max-triangles", "300", "--write", str(path)]) == 0
    assert "triangles_after 300" in capsys.readouterr().out
    (part,) = pdx_mesh.mesh_parts(pdx_mesh.parse(path.read_bytes()))
    assert part.triangles == 300
