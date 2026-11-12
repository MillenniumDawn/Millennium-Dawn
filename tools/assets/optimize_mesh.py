#!/usr/bin/env python3
"""Repair and simplify the 3D model meshes you name. One model at a time.

Usage:
    python3 tools/assets/optimize_mesh.py gfx/models/units/tanks/SOV/T72A.mesh
    python3 tools/assets/optimize_mesh.py --write A.mesh B.mesh
    python3 tools/assets/optimize_mesh.py --repair-only --write A.mesh

Without --write it only prints what would change. It takes mesh files, never
folders: a bulk pass over the model tree is not supported, because every
result needs a look in game.

Repair rebuilds zero-length or invalid normals and tangents, drops zero-area
triangles, gives unweighted vertices the bones of their nearest weighted
neighbour, and renormalizes bone weights.

Simplification removes triangles until the mesh reaches the triangle target or
the error ceiling in model_standards.py. Kept vertices keep their position,
UVs and bone weights. A guard measures how far the result strays from the
original and locks the vertices involved until the model stays inside the
guard tolerance, so thin parts such as antennas survive.

Needs numpy and scipy (`pip install --group analysis`). Simplification also
needs `pip install meshoptimizer==0.2.30a0`.
"""

import argparse
import ctypes
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import model_standards
import pdx_mesh

REPO_ROOT = Path(__file__).resolve().parents[2]
UV_SETS = ("u0", "u1", "u2", "u3")
# Normals and the first UV set steer the simplifier next to the positions.
NORMAL_WEIGHT = 0.5
UV_WEIGHT = 1.0
GUARD_SAMPLES = 150_000


class MeshoptBackend:
    """The two meshoptimizer calls the optimizer needs."""

    def __init__(self):
        try:
            import meshoptimizer
            from meshoptimizer._loader import lib
        except ImportError as exc:
            raise SystemExit(
                "Simplification needs the meshoptimizer package: "
                "pip install meshoptimizer==0.2.30a0 (or pass --repair-only)"
            ) from exc
        pointer = ctypes.POINTER
        # The 0.2.30a0 binding leaves this function untyped, which corrupts
        # the float argument.
        lib.meshopt_simplifyWithAttributes.argtypes = [
            pointer(ctypes.c_uint),
            pointer(ctypes.c_uint),
            ctypes.c_size_t,
            pointer(ctypes.c_float),
            ctypes.c_size_t,
            ctypes.c_size_t,
            pointer(ctypes.c_float),
            ctypes.c_size_t,
            pointer(ctypes.c_float),
            ctypes.c_size_t,
            pointer(ctypes.c_ubyte),
            ctypes.c_size_t,
            ctypes.c_float,
            ctypes.c_uint,
            pointer(ctypes.c_float),
        ]
        lib.meshopt_simplifyWithAttributes.restype = ctypes.c_size_t
        self._meshopt = meshoptimizer

    def simplify(self, index, positions, attributes, weights, lock, target, error):
        """Indices of the simplified mesh. Locked vertices are never removed."""
        out = np.zeros_like(index)
        count = self._meshopt.simplify_with_attributes(
            out,
            index,
            positions,
            attributes,
            weights,
            vertex_lock=np.ascontiguousarray(lock.astype(np.uint8)),
            target_index_count=3 * target,
            target_error=error,
        )
        return out[:count].copy() if count else index

    def reorder(self, index, vertex_count):
        """Indices in vertex-cache order and the old vertex for each new slot."""
        cached = np.zeros_like(index)
        self._meshopt.optimize_vertex_cache(cached, index, vertex_count=vertex_count)
        remap = np.zeros(vertex_count, np.uint32)
        used = self._meshopt.optimize_vertex_fetch_remap(
            remap, cached, vertex_count=vertex_count
        )
        kept = remap != 0xFFFFFFFF
        order = np.empty(used, np.int64)
        order[remap[kept]] = np.flatnonzero(kept)
        return remap[cached], order


def _unit(vectors):
    return vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-30)


def _perpendicular(normals):
    axis = np.where(np.abs(normals[:, :1]) < 0.9, [[1.0, 0, 0]], [[0, 1.0, 0]])
    return _unit(np.cross(normals, axis))


def _face_cross(positions, triangles):
    a, b, c = (positions[triangles[:, k]] for k in range(3))
    return np.cross(b - a, c - a)


def _drop_zero_area(positions, triangles):
    """Triangles with real area. An all-degenerate mesh is returned unchanged."""
    area = np.linalg.norm(_face_cross(positions, triangles), axis=1)
    diagonal = float(np.linalg.norm(positions.max(0) - positions.min(0))) or 1.0
    keep = area > (diagonal * 1e-6) ** 2
    return triangles[keep] if keep.any() else triangles


def _sum_at(indices, values, size):
    total = np.zeros((size, 3))
    for corner in range(3):
        np.add.at(total, indices[:, corner], values)
    return total


def _repair_normals(props, positions, triangles, fixes):
    normals = props["n"][1].reshape(-1, 3).astype(np.float64)
    length = np.linalg.norm(normals, axis=1)
    bad = ~(length >= 1e-6)
    if bad.any():
        # Area-weighted face normals, shared across vertices at one position.
        faces = _sum_at(triangles, _face_cross(positions, triangles), len(normals))
        _, same = np.unique(props["p"][1].reshape(-1, 3), axis=0, return_inverse=True)
        same = same.ravel()
        merged = np.zeros((int(same.max()) + 1, 3))
        np.add.at(merged, same, faces)
        rebuilt = merged[same]
        flat = np.linalg.norm(rebuilt, axis=1) < 1e-12
        rebuilt[flat] = [0.0, 0.0, 1.0]
        normals[bad] = rebuilt[bad]
        fixes["normals_rebuilt"] += int(bad.sum())
    off = np.abs(np.linalg.norm(normals, axis=1) - 1) > 0.01
    fixes["normals_renormalized"] += int((off & ~bad).sum())
    normals = _unit(normals)
    props["n"] = ("f", normals.astype(np.float32).ravel())
    return normals


def _repair_tangents(props, positions, triangles, normals, fixes):
    tangents = props["ta"][1].reshape(-1, 4).astype(np.float64)
    length = np.linalg.norm(tangents[:, :3], axis=1)
    bad = ~(length >= 1e-6)
    if bad.any():
        direction = np.zeros((len(tangents), 3))
        if "u0" in props:
            uv = props["u0"][1].reshape(-1, 2).astype(np.float64)
            edge1 = positions[triangles[:, 1]] - positions[triangles[:, 0]]
            edge2 = positions[triangles[:, 2]] - positions[triangles[:, 0]]
            uv1 = uv[triangles[:, 1]] - uv[triangles[:, 0]]
            uv2 = uv[triangles[:, 2]] - uv[triangles[:, 0]]
            det = uv1[:, 0] * uv2[:, 1] - uv2[:, 0] * uv1[:, 1]
            usable = np.abs(det) > 1e-12
            face = edge1 * uv2[:, 1:2] - edge2 * uv1[:, 1:2]
            face = np.where(
                usable[:, None], face / np.where(usable, det, 1)[:, None], 0
            )
            direction = _sum_at(triangles, face, len(tangents))
        direction -= normals * np.sum(direction * normals, axis=1, keepdims=True)
        weak = np.linalg.norm(direction, axis=1) < 1e-9
        direction = np.where(weak[:, None], _perpendicular(normals), _unit(direction))
        tangents[bad, :3] = direction[bad]
        fixes["tangents_rebuilt"] += int(bad.sum())
    handed = ~np.isfinite(tangents[:, 3]) | (np.abs(np.abs(tangents[:, 3]) - 1) > 0.01)
    if handed.any():
        tangents[handed, 3] = np.where(tangents[handed, 3] < 0, -1.0, 1.0)
        fixes["tangent_handedness_fixed"] += int(handed.sum())
    props["ta"] = ("f", tangents.astype(np.float32).ravel())


def _repair_skin(part, positions, fixes):
    from scipy.spatial import cKDTree

    props = part.skin.props
    count = len(positions)
    index = props["ix"][1].reshape(count, 4).copy()
    weight = props["w"][1].reshape(count, 4).astype(np.float64)
    invalid = ~np.isfinite(weight) | (weight < 0)
    if part.joints:
        invalid |= (weight > 0) & ((index < 0) | (index >= part.joints))
    fixes["bad_weight_slots_cleared"] += int(invalid.any(1).sum())
    weight[invalid] = 0
    index[weight <= 0] = -1
    total = weight.sum(1)
    empty = total <= 1e-6
    if empty.all() and part.joints:
        # Nothing to copy from: bind the whole mesh to the root joint.
        index[:, 0] = part.root_joint
        weight[:, 0] = 1.0
        fixes["meshes_bound_to_root_joint"] += 1
    elif empty.any() and not empty.all():
        source = np.flatnonzero(~empty)
        nearest = source[cKDTree(positions[source]).query(positions[empty])[1]]
        index[empty] = index[nearest]
        weight[empty] = weight[nearest]
        fixes["unweighted_vertices_fixed"] += int(empty.sum())
    total = weight.sum(1)
    off = (total > 1e-6) & (np.abs(total - 1) > 1e-3)
    weight[off] /= total[off, None]
    fixes["weights_renormalized"] += int(off.sum())
    used = int((weight > 0).sum(1).max()) if count else 0
    if used > int(props.get("bones", ("i", [4]))[1][0]):
        props["bones"] = ("i", np.array([used], np.int32))
    props["ix"] = ("i", index.astype(np.int32).ravel())
    props["w"] = ("f", weight.astype(np.float32).ravel())


def repair_part(part, fixes):
    """Fix broken vertex and skin data of one mesh in place."""
    props = part.mesh.props
    positions = props["p"][1].reshape(-1, 3).astype(np.float64)
    count = len(positions)
    triangles = props["tri"][1].reshape(-1, 3)
    kept = _drop_zero_area(positions, triangles)
    if len(kept) != len(triangles):
        fixes["zero_area_triangles_removed"] += len(triangles) - len(kept)
        triangles = kept
        props["tri"] = ("i", np.ascontiguousarray(kept.ravel()).astype(np.int32))
    if "n" in props and props["n"][1].size == count * 3:
        normals = _repair_normals(props, positions, triangles, fixes)
        if "ta" in props and props["ta"][1].size == count * 4:
            _repair_tangents(props, positions, triangles, normals, fixes)
    skin = part.skin
    if skin is not None and all(
        k in skin.props and skin.props[k][1].size == count * 4 for k in ("ix", "w")
    ):
        _repair_skin(part, positions, fixes)


def _weld(key, normals, cos_limit):
    """Group vertices with equal key rows whose normals are within the limit.

    Returns (group of each vertex, first vertex of each group, group normals).
    """
    key = np.ascontiguousarray(key)
    rows = key.view(np.dtype((np.void, key.dtype.itemsize * key.shape[1]))).ravel()
    _, same = np.unique(rows, return_inverse=True)
    order = np.argsort(same, kind="stable")
    starts = np.flatnonzero(np.r_[True, same[order][1:] != same[order][:-1]])
    group = np.empty(len(normals), np.int64)
    first, total = [], []
    for start, stop in zip(starts, np.r_[starts[1:], len(order)]):
        local = []
        for vertex in order[start:stop]:
            for candidate in local:
                if float(normals[vertex] @ normals[first[candidate]]) >= cos_limit:
                    group[vertex] = candidate
                    total[candidate] = total[candidate] + normals[vertex]
                    break
            else:
                group[vertex] = len(first)
                local.append(len(first))
                first.append(vertex)
                total.append(normals[vertex].astype(np.float64))
    return group, np.array(first), _unit(np.array(total)).astype(np.float32)


def _weld_vertices(positions, index, attrs, skin):
    """Merge split vertices that differ only by a small normal angle."""
    key = [positions.view("<u4")]
    key += [attrs[k].view("<u4") for k in UV_SETS if k in attrs]
    key += [values.view("<u4") for values in skin.values()]
    cos_limit = np.cos(np.radians(model_standards.WELD_ANGLE_DEGREES))
    group, first, normals = _weld(np.hstack(key), attrs["n"], cos_limit)
    if len(first) == len(positions):
        return positions, index, attrs, skin
    attrs = {k: values[first] for k, values in attrs.items()}
    attrs["n"] = normals
    if "ta" in attrs:
        tangents = attrs["ta"].astype(np.float64)
        along = tangents[:, :3] - normals * np.sum(
            tangents[:, :3] * normals, axis=1, keepdims=True
        )
        weak = np.linalg.norm(along, axis=1) < 1e-6
        tangents[:, :3] = np.where(weak[:, None], _perpendicular(normals), _unit(along))
        attrs["ta"] = tangents.astype(np.float32)
    skin = {k: values[first] for k, values in skin.items()}
    index = np.ascontiguousarray(group[index].astype(np.uint32))
    return np.ascontiguousarray(positions[first]), index, attrs, skin


def _point_triangle_distance(points, a, b, c):
    """Distance from each point to the nearest of the triangles (a, b, c)."""
    out = np.full(len(points), np.inf)
    ab, ac, bc = b - a, c - a, c - b
    step = max(1, 1_500_000 // max(len(a), 1))

    def on_segment(start, direction, numerator, denominator):
        safe = np.where(np.abs(denominator) < 1e-30, 1e-30, denominator)
        return (
            start[None] + direction[None] * np.clip(numerator / safe, 0, 1)[..., None]
        )

    for begin in range(0, len(points), step):
        p = points[begin : begin + step][:, None, :]
        d1, d2 = (
            (ab[None] * (p - a[None])).sum(-1),
            (ac[None] * (p - a[None])).sum(-1),
        )
        d3, d4 = (
            (ab[None] * (p - b[None])).sum(-1),
            (ac[None] * (p - b[None])).sum(-1),
        )
        d5, d6 = (
            (ab[None] * (p - c[None])).sum(-1),
            (ac[None] * (p - c[None])).sum(-1),
        )
        va, vb, vc = d3 * d6 - d5 * d4, d5 * d2 - d1 * d6, d1 * d4 - d3 * d2
        total = va + vb + vc
        total = np.where(np.abs(total) < 1e-30, 1e-30, total)
        inside = (
            a[None]
            + ab[None] * (vb / total)[..., None]
            + ac[None] * (vc / total)[..., None]
        )
        candidates = [
            np.where(
                (va >= 0) & (vb >= 0) & (vc >= 0), ((p - inside) ** 2).sum(-1), np.inf
            ),
            ((p - on_segment(a, ab, d1, d1 - d3)) ** 2).sum(-1),
            ((p - on_segment(a, ac, d2, d2 - d6)) ** 2).sum(-1),
            ((p - on_segment(b, bc, d4 - d3, (d4 - d3) + (d5 - d6))) ** 2).sum(-1),
        ]
        out[begin : begin + step] = np.sqrt(np.minimum.reduce(candidates).min(1))
    return out


def _surface_samples(positions, triangles, count, rng):
    a, b, c = (positions[triangles[:, k]] for k in range(3))
    area = np.linalg.norm(np.cross(b - a, c - a), axis=1)
    if area.sum() <= 0:
        return positions[np.unique(triangles)]
    pick = rng.choice(len(triangles), count, p=area / area.sum())
    u, v = rng.random(count), rng.random(count)
    flip = u + v > 1
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    points = (
        a[pick] + u[:, None] * (b[pick] - a[pick]) + v[:, None] * (c[pick] - a[pick])
    )
    return np.vstack([points, positions[np.unique(triangles)]])


def far_from_surface(points, positions, triangles, tolerance, rng):
    """True for each point farther than the tolerance from the triangle mesh."""
    from scipy.spatial import cKDTree

    samples = _surface_samples(positions, triangles, GUARD_SAMPLES, rng)
    far = cKDTree(samples).query(points)[0] > tolerance
    if far.any():
        # The sampled distance only overestimates, so settle these exactly.
        suspects = np.flatnonzero(far)
        corners = (positions[triangles[:, k]] for k in range(3))
        far[suspects] = _point_triangle_distance(points[suspects], *corners) > tolerance
    return far


def _face_points(positions, triangles):
    a, b, c = (positions[triangles[:, k]] for k in range(3))
    return np.vstack([(a + b + c) / 3, (a + b) / 2, (b + c) / 2, (a + c) / 2])


def _strayed(positions, before, after, tolerance, rng):
    """Vertices of faces that strayed: lost from the original or new in the result."""
    marked = np.zeros(len(positions), bool)
    for source, other in ((before, after), (after, before)):
        far = far_from_surface(
            _face_points(positions, source), positions, other, tolerance, rng
        )
        marked[source[far.reshape(4, -1).any(0)].ravel()] = True
    removed = np.setdiff1d(np.unique(before), np.unique(after))
    far = far_from_surface(positions[removed], positions, after, tolerance, rng)
    marked[removed[far]] = True
    return marked


def _grow(marked, position_id, triangle_ids, rings):
    """Spread a vertex mask over shared positions and `rings` edges outward."""
    hit = np.zeros(int(position_id.max()) + 1, bool)
    hit[position_id[marked]] = True
    for _ in range(rings):
        hit[triangle_ids[hit[triangle_ids].any(1)].ravel()] = True
    return hit[position_id]


def _bone_seams(triangles, skin):
    """On rigidly skinned meshes, vertices of triangles that span two bones."""
    lock = np.zeros(len(skin["w"]), bool)
    weight = skin["w"]
    if (weight.max(1) < 0.999).any():
        return lock
    bone = skin["ix"][np.arange(len(weight)), weight.argmax(1)][triangles]
    mixed = (bone[:, 0] != bone[:, 1]) | (bone[:, 1] != bone[:, 2])
    lock[triangles[mixed].ravel()] = True
    return lock


def _simplify(positions, index, attrs, skin, settings, backend, report):
    """Guarded simplification. Returns the new index buffer."""
    target, error, tolerance = settings
    columns, weights = [attrs["n"]], [NORMAL_WEIGHT] * 3
    if "u0" in attrs:
        columns.append(attrs["u0"])
        weights += [UV_WEIGHT] * 2
    attributes = np.ascontiguousarray(np.hstack(columns), np.float32)
    weights = np.array(weights, np.float32)
    exact = positions.astype(np.float64)
    before = index.reshape(-1, 3).astype(np.int64)
    _, position_id = np.unique(positions, axis=0, return_inverse=True)
    position_id = position_id.ravel()
    triangle_ids = position_id[before]
    lock = np.zeros(len(positions), bool)
    if "ix" in skin and "w" in skin:
        lock |= _grow(_bone_seams(before, skin), position_id, triangle_ids, 0)
    rng = np.random.default_rng(0)
    for attempt in range(model_standards.GUARD_ATTEMPTS):
        result = backend.simplify(
            index, positions, attributes, weights, lock, target, error
        )
        after = _drop_zero_area(exact, result.reshape(-1, 3).astype(np.int64))
        strayed = _strayed(exact, before, after, tolerance, rng)
        if not strayed.any():
            report["vertices_locked"] += int(lock.sum())
            return np.ascontiguousarray(after.ravel().astype(np.uint32))
        report["guard_retries"] += 1
        lock |= _grow(strayed, position_id, triangle_ids, 1 + attempt)
    report["guard_gave_up"] += 1
    return index


def optimize_part(part, settings, backend, report):
    """Weld, simplify and reorder one mesh in place."""
    props = part.mesh.props
    positions = np.ascontiguousarray(props["p"][1].reshape(-1, 3), np.float32)
    count = len(positions)
    index = np.ascontiguousarray(props["tri"][1], np.uint32)
    attrs = {
        name: props[name][1].reshape(count, width)
        for name, width in pdx_mesh.VERTEX_ATTRS.items()
        if name != "p" and name in props and props[name][1].size == count * width
    }
    skin = {}
    if part.skin is not None:
        skin = {
            name: part.skin.props[name][1].reshape(count, 4)
            for name in ("ix", "w")
            if name in part.skin.props and part.skin.props[name][1].size == count * 4
        }
    if "n" in attrs and part.triangles >= model_standards.MIN_TRIANGLES:
        positions, index, attrs, skin = _weld_vertices(positions, index, attrs, skin)
        index = _simplify(positions, index, attrs, skin, settings, backend, report)
    index, order = backend.reorder(index, len(positions))
    props["p"] = ("f", np.ascontiguousarray(positions[order]).ravel())
    for name, values in attrs.items():
        props[name] = (props[name][0], np.ascontiguousarray(values[order]).ravel())
    props["tri"] = ("i", index.astype(np.int32))
    for name, values in skin.items():
        kind = part.skin.props[name][0]
        part.skin.props[name] = (kind, np.ascontiguousarray(values[order]).ravel())


def optimize_file(data, rel_path, backend=None):
    """Repair a mesh file and, given a backend, simplify it.

    Returns (new bytes, report). The report counts triangles before and after,
    each repair, and the guard's retries.
    """
    root = pdx_mesh.parse(data)
    report = Counter()
    parts = pdx_mesh.mesh_parts(root)
    for part in parts:
        repair_part(part, report)
    rendered = [p for p in parts if p.rendered]
    report["triangles_before"] = sum(p.triangles for p in rendered)
    if backend is not None and rendered:
        corners = np.vstack([p.mesh.props["p"][1].reshape(-1, 3) for p in rendered])
        diagonal = float(np.linalg.norm(corners.max(0) - corners.min(0)))
        tolerance = model_standards.GUARD_TOLERANCE * diagonal
        budget = model_standards.triangle_target(rel_path)
        floor = model_standards.MIN_TRIANGLES // 2
        total = report["triangles_before"]
        for part in rendered:
            share = int(budget * part.triangles / total) if budget else 0
            settings = (
                max(floor, share),
                model_standards.error_ceiling(rel_path),
                tolerance,
            )
            optimize_part(part, settings, backend, report)
    report["triangles_after"] = sum(p.triangles for p in rendered)
    return pdx_mesh.write(root), report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("meshes", nargs="+", help="mesh files to process")
    parser.add_argument("--write", action="store_true", help="overwrite the files")
    parser.add_argument(
        "--repair-only", action="store_true", help="repair without simplifying"
    )
    args = parser.parse_args(argv)
    paths = [Path(p) for p in args.meshes]
    wrong = [str(p) for p in paths if not p.is_file() or p.suffix.lower() != ".mesh"]
    if wrong:
        print(f"Name .mesh files, not folders: {', '.join(wrong)}", file=sys.stderr)
        return 2
    backend = None if args.repair_only else MeshoptBackend()
    for path in paths:
        try:
            rel_path = path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel_path = path.as_posix()
        with open(path, "rb") as handle:
            data = handle.read()
        try:
            result, report = optimize_file(data, rel_path, backend)
        except pdx_mesh.MeshParseError as exc:
            print(f"{path}: unreadable: {exc}", file=sys.stderr)
            return 1
        changed = result != data
        if changed and args.write:
            with open(path, "wb") as handle:
                handle.write(result)
        state = (
            "written"
            if changed and args.write
            else "would change" if changed else "unchanged"
        )
        details = ", ".join(f"{name} {n}" for name, n in sorted(report.items()) if n)
        print(f"{path}: {state}: {details}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
