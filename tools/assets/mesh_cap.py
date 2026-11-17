"""Cut a mesh to a hard triangle cap, part by part. Used by optimize_mesh.py.

The normal simplifier stops at hard edges and texture seams, so boxy models
stay far above a cap. This one trades exactness for the cap:

- Every connected part gets the same share of its triangles, and a result that
  makes a part shorter is retried with more triangles, so no part vanishes.
- A part is first simplified with its texture seams intact. Only if that
  leaves it over its share is it simplified across seams. Corners of such
  triangles take their UVs from the UV island of the nearest original
  triangle, extended to the corner when the island does not reach it.
- Each corner takes the stored normal and tangent that best match its new
  face.
- Parts smaller than the prune size are dropped when they sit on a larger
  part.

Vertices stay at original positions and keep their bone weights.
"""

import model_standards
import numpy as np

UV_SETS = ("u0", "u1", "u2", "u3")


def _unique_rows(columns):
    key = np.ascontiguousarray(np.hstack(columns))
    rows = key.view(np.dtype((np.void, key.dtype.itemsize * key.shape[1]))).ravel()
    _, first, inverse = np.unique(rows, return_index=True, return_inverse=True)
    return first, inverse.ravel()


def _groups(group, count):
    """Members of each group as (order, starts): group g is order[starts[g]:starts[g + 1]]."""
    order = np.argsort(group, kind="stable")
    return order, np.searchsorted(group[order], np.arange(count + 1))


def _real(triangles):
    """Mask of triangles with three different corners."""
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    return (a != b) & (b != c) & (a != c)


def _components(triangles, count):
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    edges = np.vstack([triangles[:, [0, 1]], triangles[:, [1, 2]]])
    graph = coo_matrix(
        (np.ones(len(edges)), (edges[:, 0], edges[:, 1])), (count, count)
    )
    return connected_components(graph, directed=False)


def _has_area(positions, triangles):
    cross = np.cross(
        positions[triangles[:, 1]] - positions[triangles[:, 0]],
        positions[triangles[:, 2]] - positions[triangles[:, 0]],
    )
    return (
        np.linalg.norm(cross, axis=1)
        > 1e-12 * max(float(np.abs(positions).max()), 1.0) ** 2
    )


def _simplify(backend, triangles, positions, attributes, weights, lock, target):
    """Simplify a triangle subset on compacted arrays; ids stay the caller's."""
    used, local = np.unique(triangles, return_inverse=True)
    points = np.ascontiguousarray(positions[used])
    result = backend.simplify(
        np.ascontiguousarray(local.ravel().astype(np.uint32)),
        points,
        np.ascontiguousarray(attributes[used]),
        weights,
        lock[used],
        target,
        model_standards.CAP_PART_ERROR,
    )
    result = result.reshape(-1, 3).astype(np.int64)
    return used[result[_has_area(points.astype(np.float64), result)]]


class _Mesh:
    """One mesh split three ways: stored vertices, wedges (position + UV + skin), positions."""

    def __init__(self, part):
        props = part.mesh.props
        self.props = props
        self.skin_node = part.skin
        self.xyz, self.attrs, self.skin = part.arrays()
        count = len(self.xyz)
        bits = [self.xyz.view("<u4")]
        self.pos_first, self.pos_of_vertex = _unique_rows(bits)
        bits += [self.attrs[k].view("<u4") for k in UV_SETS if k in self.attrs]
        bits += [values.view("<u4") for values in self.skin.values()]
        self.wedge_first, self.wedge_of_vertex = _unique_rows(bits)
        self.pos_of_wedge = self.pos_of_vertex[self.wedge_first]
        self.points32 = np.ascontiguousarray(self.xyz[self.pos_first])
        self.points = self.points32.astype(np.float64)
        self.wedge_points32 = np.ascontiguousarray(self.xyz[self.wedge_first])
        triangles = self.wedge_of_vertex[
            props["tri"][1].reshape(-1, 3).astype(np.int64)
        ]
        self.wedge_triangles = triangles[_real(self.pos_of_wedge[triangles])]
        self.triangles = self.pos_of_wedge[self.wedge_triangles]
        _, self.island = _components(self.wedge_triangles, len(self.wedge_first))
        self.parts, self.part_of_pos = _components(self.triangles, len(self.pos_first))
        rigid = "w" in self.skin and not (self.skin["w"].max(1) < 0.999).any()
        bone = np.zeros(count, np.int64)
        if rigid:
            bone = self.skin["ix"][np.arange(count), self.skin["w"].argmax(1)]
        self.wedge_lock = self._seams(
            self.wedge_triangles, bone[self.wedge_first], rigid
        )
        self.pos_lock = self._seams(self.triangles, bone[self.pos_first], rigid)

    @staticmethod
    def _seams(triangles, bone, rigid):
        """Vertices of triangles that span two bones on a rigidly skinned mesh."""
        lock = np.zeros(len(bone), bool)
        if rigid:
            spans = bone[triangles]
            mixed = (spans[:, 0] != spans[:, 1]) | (spans[:, 1] != spans[:, 2])
            lock[triangles[mixed].ravel()] = True
        return lock


def _droppable(mesh, prune):
    """Parts smaller than the prune size that sit on a larger part."""
    from scipy.spatial import cKDTree

    low = np.full((mesh.parts, 3), np.inf)
    high = np.full((mesh.parts, 3), -np.inf)
    np.minimum.at(low, mesh.part_of_pos, mesh.points)
    np.maximum.at(high, mesh.part_of_pos, mesh.points)
    tiny = np.linalg.norm(high - low, axis=1) < prune
    large = mesh.triangles[~tiny[mesh.part_of_pos[mesh.triangles[:, 0]]]]
    if not tiny.any() or not len(large):
        return np.zeros(mesh.parts, bool), high - low
    anchor = mesh.points[large].reshape(-1, 3)
    anchor = np.vstack([anchor, mesh.points[large].mean(1)])
    far = cKDTree(anchor).query(mesh.points)[0] > 1.5 * prune
    sticks_out = np.zeros(mesh.parts, bool)
    np.logical_or.at(sticks_out, mesh.part_of_pos, far)
    return tiny & ~sticks_out, high - low


def _cut_part(mesh, rows, target, box, backend):
    """Simplify one connected part. Returns (position triangles, wedge corners or -1)."""
    wedges = mesh.wedge_triangles[rows]
    uv = mesh.attrs.get("u0")
    uv = (
        np.zeros((len(mesh.wedge_first), 2), np.float32)
        if uv is None
        else uv[mesh.wedge_first]
    )
    uv = np.ascontiguousarray(uv, np.float32)
    plain = np.zeros((len(mesh.pos_first), 2), np.float32)
    on, off = np.ones(2, np.float32), np.zeros(2, np.float32)
    floor = model_standards.CAP_MIN_PART_TRIANGLES
    size = max(float(np.linalg.norm(box)), 1e-12)
    while target < len(rows):
        kept = _simplify(
            backend, wedges, mesh.wedge_points32, uv, on, mesh.wedge_lock, target
        )
        positions, corners = mesh.pos_of_wedge[kept], kept
        if len(kept) > max(target * 1.15, floor * 2):
            across = positions[_real(positions)]
            if len(across):
                across = _simplify(
                    backend, across, mesh.points32, plain, off, mesh.pos_lock, target
                )
            if 0 < len(across) < len(kept):
                positions, corners = across, np.full_like(across, -1)
        if len(positions):
            reach = mesh.points[np.unique(positions)]
            shrink = float(np.max(box - (reach.max(0) - reach.min(0)))) / size
            if shrink <= model_standards.CAP_MAX_SHRINK:
                return positions, corners
        # The part got shorter or vanished: give it more triangles and try again.
        target *= 2
    return mesh.pos_of_wedge[wedges], wedges


def _resolve_corners(mesh, positions, corners):
    """Give seam-crossing triangles a wedge per corner. Returns (UV overrides, crossing mask)."""
    from scipy.spatial import cKDTree

    overrides = {}
    crossing = np.zeros(len(positions), bool)
    pending = np.flatnonzero((corners < 0).any(1))
    if not len(pending):
        return overrides, crossing
    centres = mesh.points[mesh.triangles].mean(1)
    tree = cKDTree(centres)
    island_of_triangle = mesh.island[mesh.wedge_triangles[:, 0]]
    nearest = tree.query(mesh.points[positions[pending]].mean(1))[1]
    order, starts = _groups(mesh.pos_of_wedge, len(mesh.pos_first))
    for triangle, island in zip(pending, island_of_triangle[nearest]):
        for corner in range(3):
            position = positions[triangle, corner]
            here = order[starts[position] : starts[position + 1]]
            match = here[mesh.island[here] == island]
            if len(match):
                corners[triangle, corner] = match[0]
                continue
            # The island does not reach this corner: extend its UV mapping to it.
            crossing[triangle] = True
            close = np.atleast_1d(
                tree.query(mesh.points[position], k=min(32, len(centres)))[1]
            )
            close = close[island_of_triangle[close] == island]
            if not len(close):
                corners[triangle, corner] = here[0]
                continue
            a, b, c = mesh.wedge_triangles[close[0]]
            corners[triangle, corner] = a
            origin = mesh.points[mesh.pos_of_wedge[a]]
            edge1 = mesh.points[mesh.pos_of_wedge[b]] - origin
            edge2 = mesh.points[mesh.pos_of_wedge[c]] - origin
            offset = mesh.points[position] - origin
            d11, d12, d22 = edge1 @ edge1, edge1 @ edge2, edge2 @ edge2
            det = d11 * d22 - d12 * d12
            if abs(det) > 1e-18:
                v = float(
                    np.clip(
                        (d22 * (offset @ edge1) - d12 * (offset @ edge2)) / det, -2, 3
                    )
                )
                w = float(
                    np.clip(
                        (d11 * (offset @ edge2) - d12 * (offset @ edge1)) / det, -2, 3
                    )
                )
                overrides[(int(triangle), corner)] = (
                    1 - v - w,
                    v,
                    w,
                    int(a),
                    int(b),
                    int(c),
                )
    return overrides, crossing


def _write(mesh, positions, corners, overrides, backend):
    """Build the vertex buffer for the kept triangles and store it on the mesh node."""
    xyz = mesh.points[positions]
    normal = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    normal /= np.linalg.norm(normal, axis=1, keepdims=True) + 1e-30
    members, starts = _groups(mesh.wedge_of_vertex, len(mesh.wedge_first))
    at_position, at_starts = _groups(mesh.pos_of_vertex, len(mesh.pos_first))
    stored = mesh.attrs["n"].astype(np.float64)
    index_of, blended = {}, {}
    out_position, out_donor, out_skin = [], [], []
    triangles = np.empty((len(positions), 3), np.int64)
    for triangle in range(len(positions)):
        for corner in range(3):
            wedge = corners[triangle, corner]
            choices = members[starts[wedge] : starts[wedge + 1]]
            donor = choices[np.argmax(stored[choices] @ normal[triangle])]
            position = positions[triangle, corner]
            skin = donor
            if mesh.pos_of_vertex[donor] != position:
                skin = at_position[at_starts[position]]
            blend = overrides.get((triangle, corner))
            key = (
                int(position),
                int(donor),
                int(skin),
                blend and blend[3:] + blend[1:3],
            )
            if key not in index_of:
                index_of[key] = len(out_position)
                out_position.append(position)
                out_donor.append(donor)
                out_skin.append(skin)
                if blend:
                    blended[index_of[key]] = blend
            triangles[triangle, corner] = index_of[key]
    out_position, out_donor, out_skin = map(
        np.array, (out_position, out_donor, out_skin)
    )
    index, order = backend.reorder(
        np.ascontiguousarray(triangles.ravel().astype(np.uint32)), len(out_position)
    )
    props = mesh.props
    props["p"] = ("f", np.ascontiguousarray(mesh.points32[out_position][order]).ravel())
    for name, values in mesh.attrs.items():
        chosen = values[out_donor].copy()
        if name in UV_SETS:
            for vertex, (wa, wb, wc, a, b, c) in blended.items():
                first = mesh.wedge_first
                chosen[vertex] = (
                    wa * values[first[a]]
                    + wb * values[first[b]]
                    + wc * values[first[c]]
                )
        props[name] = (props[name][0], np.ascontiguousarray(chosen[order]).ravel())
    props["tri"] = ("i", index.astype(np.int32))
    for name, values in mesh.skin.items():
        kind = mesh.skin_node.props[name][0]
        mesh.skin_node.props[name] = (
            kind,
            np.ascontiguousarray(values[out_skin][order]).ravel(),
        )


def cap_part(part, ratio, prune, backend, report):
    """Cut one mesh to about `ratio` of its triangles, in place."""
    if "n" not in part.mesh.props:
        return
    mesh = _Mesh(part)
    if not len(mesh.triangles):
        return
    droppable, boxes = _droppable(mesh, prune)
    part_of_triangle = mesh.part_of_pos[mesh.triangles[:, 0]]
    order, starts = _groups(part_of_triangle, mesh.parts)
    kept_positions, kept_corners = [], []
    for number in range(mesh.parts):
        rows = order[starts[number] : starts[number + 1]]
        if droppable[number]:
            report["parts_pruned"] += 1
            continue
        floor = model_standards.CAP_MIN_PART_TRIANGLES
        target = max(floor, int(round(len(rows) * ratio)))
        positions, corners = _cut_part(mesh, rows, target, boxes[number], backend)
        kept_positions.append(positions)
        kept_corners.append(corners)
    if not kept_positions:
        return
    positions, corners = np.vstack(kept_positions), np.vstack(kept_corners)
    solid = _has_area(mesh.points, positions)
    if solid.any():
        positions, corners = positions[solid], corners[solid]
    overrides, crossing = _resolve_corners(mesh, positions, corners)
    report["triangles_crossing_seams"] += int(crossing.sum())
    _write(mesh, positions, corners, overrides, backend)


def cap_parts(build, max_triangles, backend, report):
    """Cut the rendered meshes of a file to the cap.

    `build` returns a fresh list of repaired parts. Each try starts from it,
    with a smaller share or, when shares alone cannot meet the cap, the next
    prune size. Returns the parts of the last try.
    """
    for prune_share in model_standards.CAP_PRUNE_SIZES:
        budget = max_triangles
        for _ in range(4):
            parts = [p for p in build() if p.rendered]
            total = sum(p.triangles for p in parts)
            corners = np.vstack([p.mesh.props["p"][1].reshape(-1, 3) for p in parts])
            prune = prune_share * float(np.linalg.norm(corners.max(0) - corners.min(0)))
            trial = report.copy()
            for part in parts:
                cap_part(part, budget / total, prune, backend, trial)
            after = sum(p.triangles for p in parts)
            if after <= max_triangles:
                report.clear()
                report.update(trial)
                return parts
            budget = int(budget * max_triangles / after * 0.95)
    report.clear()
    report.update(trial)
    return parts
