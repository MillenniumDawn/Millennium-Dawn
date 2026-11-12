#!/usr/bin/env python3
"""Report, fix or debug the mipmaps of DDS textures.

Usage:
    python3 tools/assets/dds_mipmaps.py                    # report for gfx/ and map/
    python3 tools/assets/dds_mipmaps.py gfx/models/units/tanks
    python3 tools/assets/dds_mipmaps.py --fix gfx/models/units/tanks
    python3 tools/assets/dds_mipmaps.py --fix --write gfx/models/units/tanks
    python3 tools/assets/dds_mipmaps.py --tint in.dds out.dds

The rule for each folder is in model_standards.py: textures drawn on the 3D map
need mipmaps, GUI art should have none, and a few folders are left as they are.

--fix adds a full chain where one is needed and missing, and drops the chain
where none is wanted. Without --write it only prints what it would do. The
full-size image is never re-encoded: its bytes stay exactly as they are.

--tint writes a debug copy whose smaller levels are coloured (red, green, blue,
yellow, magenta). Swap it in for the real file, look at it in game, and the
colour shows which level the engine draws. Do not commit the copy.

Needs numpy (`pip install --group analysis`) and Pillow (`--group runtime`).
"""

import argparse
import io
import struct
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import model_standards
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCOPE = ("gfx", "map")
HEADER_SIZE = 128
BLOCK_BYTES = {b"DXT1": 8, b"DXT3": 16, b"DXT5": 16}
FLAG_MIPMAPCOUNT = 0x20000
CAPS_MIPMAP = 0x400008
TINTS = ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255))
ENCODE_CHUNK = 16384


@dataclass
class Texture:
    width: int
    height: int
    mipmaps: int
    fourcc: bytes
    pixel_bytes: int

    def level_size(self, level=0):
        width = max(1, self.width >> level)
        height = max(1, self.height >> level)
        if self.fourcc:
            return ((width + 3) // 4) * ((height + 3) // 4) * BLOCK_BYTES[self.fourcc]
        return width * height * self.pixel_bytes

    @property
    def full_chain(self):
        return max(self.width, self.height).bit_length()


def read_header(data):
    """Parse a DDS header. Returns (Texture, None) or (None, why it is unsupported)."""
    if len(data) < HEADER_SIZE or data[:4] != b"DDS ":
        return None, "not DDS data"
    flags = struct.unpack_from("<I", data, 8)[0]
    height, width = struct.unpack_from("<II", data, 12)
    mipmaps = struct.unpack_from("<I", data, 28)[0] if flags & FLAG_MIPMAPCOUNT else 1
    fourcc = data[84:88] if struct.unpack_from("<I", data, 80)[0] & 4 else b""
    bits = struct.unpack_from("<I", data, 88)[0]
    if fourcc and fourcc not in BLOCK_BYTES:
        return None, f"unsupported format {fourcc.decode('latin-1')}"
    if not fourcc and bits not in (24, 32):
        return None, f"unsupported {bits}-bit format"
    if width == 0 or height == 0:
        return None, "zero size"
    texture = Texture(width, height, max(mipmaps, 1), fourcc, bits // 8)
    if len(data) < HEADER_SIZE + texture.level_size():
        return None, "truncated"
    return texture, None


def _with_mipmaps(data, count):
    """The header of `data` rewritten to declare `count` levels."""
    head = bytearray(data[:HEADER_SIZE])
    flags = struct.unpack_from("<I", head, 8)[0]
    caps = struct.unpack_from("<I", head, 108)[0]
    if count > 1:
        flags, caps = flags | FLAG_MIPMAPCOUNT, caps | CAPS_MIPMAP
    else:
        flags, caps = flags & ~FLAG_MIPMAPCOUNT, caps & ~CAPS_MIPMAP
    struct.pack_into("<I", head, 8, flags)
    struct.pack_into("<I", head, 28, count if count > 1 else 0)
    struct.pack_into("<I", head, 108, caps)
    return bytes(head)


def strip(data, texture):
    """The file with only its full-size level."""
    top = data[HEADER_SIZE : HEADER_SIZE + texture.level_size()]
    return _with_mipmaps(data, 1) + top


def _halve(image, coverage):
    """Half-size image by a 2x2 box filter. A 1-wide axis is kept.

    With `coverage`, alpha is treated as see-through cover: colours average
    over the covered texels only, so hidden texels do not bleed in.
    """
    height, width = image.shape[:2]
    rows, cols = (height // 2) * 2 or 1, (width // 2) * 2 or 1
    image = image[:rows, :cols]
    if rows > 1:
        pair = image.reshape(rows // 2, 2, cols, -1)
    else:
        pair = image.reshape(1, 1, cols, -1)
    if cols > 1:
        quad = pair.reshape(pair.shape[0], pair.shape[1], cols // 2, 2, -1)
    else:
        quad = pair.reshape(pair.shape[0], pair.shape[1], 1, 1, -1)
    if not coverage:
        return quad.mean(axis=(1, 3))
    weight = quad[..., 3:4] / 255.0
    cover = weight.sum(axis=(1, 3))
    colour = (quad[..., :3] * weight).sum(axis=(1, 3)) / np.maximum(cover, 1e-9)
    return np.concatenate([colour, quad[..., 3:4].mean(axis=(1, 3))], axis=-1)


def _blocks(image):
    """(h, w, 4) padded to multiples of four -> (blocks, 16, 4)."""
    height, width = image.shape[:2]
    pad = ((0, -height % 4), (0, -width % 4), (0, 0))
    image = np.pad(image, pad, mode="edge")
    height, width = image.shape[:2]
    tiles = image.reshape((height // 4, 4, width // 4, 4, 4))
    return tiles.transpose((0, 2, 1, 3, 4)).reshape((-1, 16, 4))


def _fit_line(colours, weight):
    """Ends of the best-fit colour line through the weighted texels of each block."""
    total = np.maximum(weight.sum(1, keepdims=True), 1.0)
    mean = (colours * weight[..., None]).sum(1) / total
    centred = colours - mean[:, None]
    spread = np.einsum("nki,nkj->nij", centred * weight[..., None], centred)
    axis = np.full((len(colours), 3), 3**-0.5)
    for _ in range(8):
        axis = np.einsum("nij,nj->ni", spread, axis)
        axis /= np.linalg.norm(axis, axis=1, keepdims=True) + 1e-12
    along = np.einsum("nki,ni->nk", centred, axis)
    high = np.where(weight > 0, along, -np.inf).max(1)
    low = np.where(weight > 0, along, np.inf).min(1)
    high, low = (np.where(np.isfinite(v), v, 0.0)[:, None] for v in (high, low))
    return np.clip(mean + axis * high, 0, 255), np.clip(mean + axis * low, 0, 255)


_LEVELS_565 = np.array([31, 63, 31], np.float64)


# Share of the first endpoint in each four-colour palette entry.
_FIRST_SHARE = np.array([1.0, 0.0, 2 / 3, 1 / 3])


def _packed(q):
    return (q[:, 0] << 11) | (q[:, 1] << 5) | q[:, 2]


def _quantize(ends):
    return np.rint(np.clip(ends, 0, 255) / 255.0 * _LEVELS_565).astype(np.uint32)


def _assign(first, second, colours, opaque):
    """Order two 5:6:5 endpoints for the block's mode and index every texel.

    Four-colour mode needs first > second. A block with a see-through texel,
    or with equal endpoints, uses three-colour mode, whose last entry is
    see-through. Returns (first, second, index, squared error).
    """
    solid = opaque.all(1)
    swap = np.where(
        solid, _packed(first) < _packed(second), _packed(first) > _packed(second)
    )
    first, second = (
        np.where(swap[:, None], second, first),
        np.where(swap[:, None], first, second),
    )
    three = _packed(first) <= _packed(second)
    a, b = (q * 255.0 / _LEVELS_565 for q in (first, second))
    palette = np.stack([a, b, (2 * a + b) / 3, (a + 2 * b) / 3], axis=1)
    palette[three, 2] = (a[three] + b[three]) / 2
    distance = ((colours[:, :, None, :] - palette[:, None, :, :]) ** 2).sum(-1)
    distance[three, :, 3] = np.inf
    index = distance.argmin(-1)
    error = np.take_along_axis(distance, index[..., None], -1)[..., 0]
    index[~opaque] = 3
    return first, second, index, np.where(opaque, error, 0.0).sum(1)


def _refit(index, colours):
    """Least-squares endpoints for the texel indices of four-colour blocks."""
    share = _FIRST_SHARE[index]
    a, b = (share * share).sum(1), (share * (1 - share)).sum(1)
    c = ((1 - share) ** 2).sum(1)
    det = a * c - b * b
    usable = np.abs(det) > 1e-9
    det = np.where(usable, det, 1.0)[:, None]
    first = (share[..., None] * colours).sum(1)
    second = ((1 - share)[..., None] * colours).sum(1)
    return (
        _quantize((c[:, None] * first - b[:, None] * second) / det),
        _quantize((a[:, None] * second - b[:, None] * first) / det),
        usable,
    )


def _encode_colour(colours, opaque):
    """BC1 colour blocks: a line fit, then two least-squares refinements."""
    ends = _fit_line(colours, opaque.astype(np.float64))
    first, second, index, error = _assign(*map(_quantize, ends), colours, opaque)
    solid = opaque.all(1)
    for _ in range(2):
        new_first, new_second, usable = _refit(index, colours)
        trial = _assign(new_first, new_second, colours, opaque)
        better = solid & usable & (trial[3] < error)
        first[better], second[better] = trial[0][better], trial[1][better]
        index[better], error[better] = trial[2][better], trial[3][better]
    index = index.astype(np.uint32)
    bits = (index << (2 * np.arange(16, dtype=np.uint32))).sum(1, dtype=np.uint32)
    out = np.zeros((len(colours), 8), np.uint8)
    out[:, 0:2] = _packed(first).astype("<u2").view(np.uint8).reshape(-1, 2)
    out[:, 2:4] = _packed(second).astype("<u2").view(np.uint8).reshape(-1, 2)
    out[:, 4:8] = bits.astype("<u4").view(np.uint8).reshape(-1, 4)
    return out


def _encode_alpha(alpha, fourcc):
    """The alpha half of a DXT3 (4-bit) or DXT5 (interpolated) block."""
    if fourcc == b"DXT3":
        nibble = np.clip(np.rint(alpha / 17.0), 0, 15).astype(np.uint8)
        return nibble[:, 0::2] | (nibble[:, 1::2] << 4)
    high = np.rint(alpha.max(1)).astype(np.int64)
    low = np.rint(alpha.min(1)).astype(np.int64)
    step = np.array([0, 7, 1, 2, 3, 4, 5, 6]) / 7.0
    values = high[:, None] * (1 - step) + low[:, None] * step
    index = ((alpha[:, :, None] - values[:, None, :]) ** 2).argmin(-1).astype(np.uint64)
    index[high == low] = 0
    bits = (index << (3 * np.arange(16, dtype=np.uint64))).sum(1, dtype=np.uint64)
    out = np.zeros((len(alpha), 8), np.uint8)
    out[:, 0], out[:, 1] = high, low
    out[:, 2:8] = bits.astype("<u8").view(np.uint8).reshape(-1, 8)[:, :6]
    return out


def _encode_level(image, fourcc):
    """Encode an (h, w, 4) RGBA float image as DXT1, DXT3 or DXT5 blocks."""
    blocks = _blocks(image)
    parts = []
    for start in range(0, len(blocks), ENCODE_CHUNK):
        chunk = blocks[start : start + ENCODE_CHUNK]
        if fourcc == b"DXT1":
            parts.append(_encode_colour(chunk[:, :, :3], chunk[:, :, 3] >= 128))
        else:
            solid = np.ones(chunk.shape[:2], bool)
            colour = _encode_colour(chunk[:, :, :3], solid)
            parts.append(np.hstack([_encode_alpha(chunk[:, :, 3], fourcc), colour]))
    return np.vstack(parts).tobytes()


def _decode_compressed(data):
    from PIL import Image

    with Image.open(io.BytesIO(data)) as image:
        return np.asarray(image.convert("RGBA"), np.float64)


def add(data, texture, tint=False):
    """The file with a full mipmap chain built from its full-size level."""
    top = data[HEADER_SIZE : HEADER_SIZE + texture.level_size()]
    if texture.fourcc:
        image = _decode_compressed(strip(data, texture))
    else:
        raw = np.frombuffer(top, np.uint8)
        image = raw.reshape(texture.height, texture.width, -1).astype(np.float64)
    levels = [top]
    for level in range(1, texture.full_chain):
        image = _halve(image, coverage=texture.fourcc == b"DXT1")
        shown = image
        if tint:
            colour = TINTS[min(level, len(TINTS)) - 1]
            shown = image.copy()
            # Raw texels are stored blue, green, red.
            shown[..., :3] = colour if texture.fourcc else colour[::-1]
        if texture.fourcc:
            levels.append(_encode_level(shown, texture.fourcc))
        else:
            levels.append(np.clip(np.rint(shown), 0, 255).astype(np.uint8).tobytes())
    return _with_mipmaps(data, len(levels)) + b"".join(levels)


def plan(data, rel_path):
    """What a file needs: (action, detail). Action is add, strip, ok or skip."""
    texture, problem = read_header(data)
    if texture is None:
        return "skip", problem
    rule = model_standards.mipmap_rule(rel_path)
    if rule == model_standards.MIPMAP_NEEDED and texture.mipmaps <= 1:
        if max(texture.width, texture.height) <= 4:
            return "ok", ""
        return "add", f"{texture.full_chain - 1} levels"
    if rule == model_standards.MIPMAP_NONE and texture.mipmaps > 1:
        saved = len(data) - HEADER_SIZE - texture.level_size()
        return "strip", f"{texture.mipmaps - 1} levels, {saved / 1024:.0f} KB"
    return "ok", ""


def apply(data, action):
    """The fixed bytes for a planned add or strip."""
    texture, _ = read_header(data)
    return add(data, texture) if action == "add" else strip(data, texture)


def collect(paths):
    """DDS files under the given files or folders, sorted."""
    files = set()
    for start in paths:
        start = Path(start)
        candidates = [start] if start.is_file() else start.rglob("*")
        files.update(
            c for c in candidates if c.suffix.lower() == ".dds" and c.is_file()
        )
    return sorted(files)


def _relative(path, root):
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run(paths, root, fix=False, write=False):
    """Check the paths. Prints one line per file to change; returns totals."""
    totals = Counter()
    for path in collect(paths):
        rel_path = _relative(path, root)
        with open(path, "rb") as handle:
            data = handle.read()
        action, detail = plan(data, rel_path)
        totals[action] += 1
        if action == "skip":
            totals[f"skip: {detail}"] += 1
        if action not in ("add", "strip"):
            continue
        if fix:
            result = apply(data, action)
            totals["bytes_changed"] += len(result) - len(data)
            if write:
                with open(path, "wb") as handle:
                    handle.write(result)
        verb = {"add": "needs mipmaps", "strip": "has unneeded mipmaps"}[action]
        if fix:
            verb = ("" if write else "would ") + action
        print(f"{rel_path}: {verb} ({detail})")
    return totals


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="DDS files or folders")
    parser.add_argument("--fix", action="store_true", help="add or drop mipmaps")
    parser.add_argument("--write", action="store_true", help="with --fix: save")
    parser.add_argument("--tint", action="store_true", help="paths are IN OUT")
    args = parser.parse_args(argv)
    if args.tint:
        if len(args.paths) != 2:
            parser.error("--tint takes an input file and an output file")
        with open(args.paths[0], "rb") as handle:
            data = handle.read()
        texture, problem = read_header(data)
        if texture is None:
            print(f"{args.paths[0]}: {problem}", file=sys.stderr)
            return 1
        with open(args.paths[1], "wb") as handle:
            handle.write(add(data, texture, tint=True))
        print(f"{args.paths[1]}: {texture.full_chain} levels, smaller ones tinted")
        return 0
    paths = args.paths or [REPO_ROOT / name for name in DEFAULT_SCOPE]
    missing = [str(p) for p in paths if not Path(p).exists()]
    if missing:
        print(f"Not found: {', '.join(missing)}", file=sys.stderr)
        return 2
    totals = run(paths, REPO_ROOT, fix=args.fix, write=args.fix and args.write)
    checked = sum(totals[k] for k in ("add", "strip", "ok", "skip"))
    print(f"\n{checked} textures checked")
    print(f"  need mipmaps: {totals['add']}")
    print(f"  have unneeded mipmaps: {totals['strip']}")
    for name, count in sorted(totals.items()):
        if name.startswith("skip: "):
            print(f"  skipped, {name[6:]}: {count}")
    if args.fix:
        state = "changed" if args.write else "would change"
        print(f"  size {state} by {totals['bytes_changed'] / 1e6:+.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
