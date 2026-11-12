#!/usr/bin/env python3
"""Report problems in 3D model meshes and their textures. Changes nothing.

Usage:
    python3 tools/assets/audit_models.py                     # all of gfx/models
    python3 tools/assets/audit_models.py gfx/models/units/tanks/SOV

For each `.mesh` it reports broken vertex data (invalid or zero-length normals
and tangents, zero-area triangles), broken skinning (unweighted vertices,
weights that do not sum to 1, bone indices outside the skeleton) and triangle
counts above the target in model_standards.py. For each `.dds` it reports
what the 3D Model Performance Guidelines rule out: uncompressed data, missing
mipmaps, sizes that are not powers of two or exceed the maximum.

Needs numpy (`pip install --group analysis`).
"""

import argparse
import os
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import model_standards
import pdx_mesh

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCOPE = "gfx/models"
COMPRESSED = (b"DXT1", b"DXT3", b"DXT5")


def _vertex_findings(mesh, count):
    """Problems in the per-vertex arrays of one mesh."""
    found = Counter()
    props = mesh.props
    for name, width in pdx_mesh.VERTEX_ATTRS.items():
        if name not in props:
            continue
        values = props[name][1]
        if values.size != count * width:
            found[f"{name}_length_mismatch"] += 1
        elif not np.isfinite(values).all():
            bad = ~np.isfinite(values.reshape(count, width))
            found[f"{name}_invalid_values"] += int(bad.any(1).sum())
    if "n" in props and props["n"][1].size == count * 3:
        length = np.linalg.norm(props["n"][1].reshape(-1, 3), axis=1)
        zero = ~(length >= 1e-6)
        found["normal_zero_length"] += int(zero.sum())
        found["normal_not_unit"] += int((~zero & (np.abs(length - 1) > 0.01)).sum())
    if "ta" in props and props["ta"][1].size == count * 4:
        tangent = props["ta"][1].reshape(-1, 4)
        length = np.linalg.norm(tangent[:, :3], axis=1)
        found["tangent_zero_length"] += int((~(length >= 1e-6)).sum())
        handed = np.abs(np.abs(tangent[:, 3]) - 1) > 0.01
        found["tangent_bad_handedness"] += int(handed.sum())
    return found


def _skin_findings(part, count):
    """Problems in the bone indices and weights of one skinned mesh."""
    found = Counter()
    index = part.skin.props.get("ix", ("i", np.zeros(0, "<i4")))[1]
    weight = part.skin.props.get("w", ("f", np.zeros(0, "<f4")))[1]
    if index.size != count * 4 or weight.size != count * 4:
        found["skin_not_four_slots"] += 1
        return found
    index = index.reshape(count, 4)
    weight = weight.reshape(count, 4)
    finite = np.isfinite(weight).all(1)
    found["skin_invalid_weights"] += int((~finite).sum())
    total = np.where(finite, weight.sum(1), 1.0)
    found["skin_unweighted"] += int((total <= 1e-6).sum())
    found["skin_weights_not_normalized"] += int(
        ((total > 1e-6) & (np.abs(total - 1) > 0.01)).sum()
    )
    found["skin_negative_weights"] += int((weight < 0).any(1).sum())
    if part.joints == 0:
        found["skin_without_skeleton"] += 1
    else:
        outside = (weight > 0) & ((index < 0) | (index >= part.joints))
        found["skin_bone_index_out_of_range"] += int(outside.any(1).sum())
    return found


def mesh_findings(root):
    """Count each kind of problem across the meshes of a parsed file."""
    found = Counter()
    for part in pdx_mesh.mesh_parts(root):
        positions = part.mesh.props["p"][1].reshape(-1, 3)
        count = len(positions)
        index = part.mesh.props["tri"][1]
        if index.size % 3 or (index.size and (index.min() < 0 or index.max() >= count)):
            found["triangle_index_out_of_range"] += 1
            continue
        found.update(_vertex_findings(part.mesh, count))
        triangles = index.reshape(-1, 3)
        p = positions.astype(np.float64)
        a, b, c = p[triangles[:, 0]], p[triangles[:, 1]], p[triangles[:, 2]]
        area = np.linalg.norm(np.cross(b - a, c - a), axis=1)
        diagonal = float(np.linalg.norm(p.max(0) - p.min(0))) if count else 0.0
        found["zero_area_triangles"] += int((area <= (diagonal * 1e-6) ** 2).sum())
        if part.skin is not None:
            found.update(_skin_findings(part, count))
    return Counter({name: n for name, n in found.items() if n})


def rendered_triangles(root):
    return sum(p.triangles for p in pdx_mesh.mesh_parts(root) if p.rendered)


def audit_mesh(path, rel_path):
    """Findings for one mesh file as `name` or `name xN` strings."""
    try:
        with open(path, "rb") as handle:
            root = pdx_mesh.parse(handle.read())
    except (OSError, pdx_mesh.MeshParseError) as exc:
        return [f"unreadable: {exc}"]
    findings = [f"{name} x{n}" for name, n in sorted(mesh_findings(root).items())]
    target = model_standards.triangle_target(rel_path)
    triangles = rendered_triangles(root)
    if target is not None and triangles > target:
        findings.append(f"triangles {triangles} over target {target}")
    return findings


def _is_power_of_two(value):
    return value > 0 and value & (value - 1) == 0


def audit_texture(path):
    """Findings for one model texture, from its DDS header."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(128)
    except OSError as exc:
        return [f"unreadable: {exc}"]
    if len(head) < 128 or head[:4] != b"DDS ":
        return ["not_dds_data"]
    flags = struct.unpack_from("<I", head, 8)[0]
    height, width = struct.unpack_from("<II", head, 12)
    mipmaps = struct.unpack_from("<I", head, 28)[0] if flags & 0x20000 else 1
    fourcc = head[84:88] if struct.unpack_from("<I", head, 80)[0] & 4 else b""
    findings = []
    if fourcc == b"DX10":
        findings.append("dx10_header")
    elif fourcc not in COMPRESSED:
        findings.append("uncompressed")
    if mipmaps <= 1 and max(width, height) > 4:
        findings.append("no_mipmaps")
    if not (_is_power_of_two(width) and _is_power_of_two(height)):
        findings.append("not_power_of_two")
    if max(width, height) > model_standards.MAX_TEXTURE_SIZE:
        findings.append(f"larger_than_{model_standards.MAX_TEXTURE_SIZE}")
    return findings


def collect(paths):
    """Mesh and texture files under the given files or directories, sorted."""
    files = set()
    for start in paths:
        start = Path(start)
        candidates = [start] if start.is_file() else start.rglob("*")
        for candidate in candidates:
            if candidate.suffix.lower() in (".mesh", ".dds") and candidate.is_file():
                files.add(candidate)
    return sorted(files)


def run(paths, root=REPO_ROOT):
    """Audit the paths. Returns (files checked, {relative path: findings})."""
    report = {}
    files = collect(paths)
    for path in files:
        try:
            rel_path = path.resolve().relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            rel_path = path.as_posix()
        if path.suffix.lower() == ".mesh":
            findings = audit_mesh(path, rel_path)
        else:
            findings = audit_texture(path)
        if findings:
            report[rel_path] = findings
    return len(files), report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "paths",
        nargs="*",
        help=f"mesh or texture files or folders (default: {DEFAULT_SCOPE})",
    )
    args = parser.parse_args(argv)
    paths = args.paths or [REPO_ROOT / DEFAULT_SCOPE]
    missing = [str(p) for p in paths if not Path(p).exists()]
    if missing:
        print(f"Not found: {', '.join(missing)}", file=sys.stderr)
        return 2
    checked, report = run(paths, REPO_ROOT)
    totals = Counter()
    for rel_path, findings in report.items():
        print(f"{rel_path}: {'; '.join(findings)}")
        totals.update(f.split(" ")[0] for f in findings)
    print(f"\n{checked} files checked, {len(report)} with findings")
    for name, count in totals.most_common():
        print(f"  {name}: {count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
