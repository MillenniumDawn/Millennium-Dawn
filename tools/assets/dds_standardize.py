#!/usr/bin/env python3
"""Bring DDS textures in line with the art standards.

Usage:
    python3 tools/assets/dds_standardize.py                       # report for gfx/
    python3 tools/assets/dds_standardize.py --fix gfx/interface/technologies
    python3 tools/assets/dds_standardize.py --fix --write gfx/interface/technologies
    python3 tools/assets/dds_standardize.py --fix --write --max-size 512 gfx/models

The format for each folder is in model_standards.py. Three things are fixed:

- Files the game's loader was not written for: a DX10 header, 16- and 24-bit
  texels, odd channel orders, and PNG, JPEG or TGA data under a `.dds` name.
  They are rewritten in the folder's standard format. Going to uncompressed
  A8R8G8B8 keeps every texel exactly; a DX10 header is replaced without
  touching the texels.
- Uncompressed art in a folder whose standard is compressed (portraits, event
  pictures, loading screens, model textures) is compressed to DXT1 or DXT5.
- Uncompressed GUI art is compressed only when the result passes the quality
  gate in model_standards.py, so smooth backgrounds shrink and icons stay sharp.
  Tech, focus and idea icons are never compressed.

Mipmaps then follow dds_mipmaps.py's rule. --max-size also halves model
textures until their longer side fits. Without --write nothing is saved.

Needs numpy (`pip install --group analysis`) and Pillow (`--group runtime`).
"""

import io
import struct
import sys
from collections import Counter
from pathlib import Path

import dds_mipmaps
import model_standards
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCOPE = ("gfx",)
HEADER_SIZE = dds_mipmaps.HEADER_SIZE
DX10_SIZE = 20
# DXGI format -> the legacy four-character code with the same block layout.
DX10_BLOCKS = {
    71: b"DXT1",
    72: b"DXT1",
    74: b"DXT3",
    75: b"DXT3",
    77: b"DXT5",
    78: b"DXT5",
}
# DXGI formats holding four 8-bit channels -> their order in the file.
DX10_RAW = {87: "bgra", 91: "bgra", 88: "bgrx", 93: "bgrx", 28: "rgba", 29: "rgba"}
BGRA_MASKS = (0xFF0000, 0xFF00, 0xFF, 0xFF000000)


def _raw_header(width, height):
    """Legacy header of an uncompressed A8R8G8B8 texture."""
    head = bytearray(HEADER_SIZE)
    head[0:4] = b"DDS "
    struct.pack_into("<IIIII", head, 4, 124, 0x100F, height, width, width * 4)
    struct.pack_into("<III", head, 76, 32, 0x41, 0)
    struct.pack_into("<I4I", head, 88, 32, *BGRA_MASKS)
    struct.pack_into("<I", head, 108, 0x1000)
    return bytes(head)


def _block_header(width, height, fourcc, size):
    """Legacy header of a DXT1, DXT3 or DXT5 texture without mipmaps."""
    head = bytearray(HEADER_SIZE)
    head[0:4] = b"DDS "
    struct.pack_into("<IIIII", head, 4, 124, 0x81007, height, width, size)
    struct.pack_into("<II", head, 76, 32, 4)
    head[84:88] = fourcc
    struct.pack_into("<I", head, 108, 0x1000)
    return bytes(head)


def as_raw(rgba):
    """An (h, w, 4) RGBA array as an uncompressed A8R8G8B8 file."""
    height, width = rgba.shape[:2]
    texels = np.ascontiguousarray(rgba[..., [2, 1, 0, 3]], np.uint8)
    return _raw_header(width, height) + texels.tobytes()


def as_blocks(rgba, fourcc):
    """An (h, w, 4) RGBA array as a DXT1 or DXT5 file without mipmaps."""
    height, width = rgba.shape[:2]
    body = dds_mipmaps._encode_level(rgba.astype(np.float64), fourcc)
    return _block_header(width, height, fourcc, len(body)) + body


def _from_masks(data, width, height, bits, masks, has_alpha):
    """Decode legacy uncompressed texels through their channel masks."""
    step = bits // 8
    raw = np.frombuffer(data, np.uint8, width * height * step, HEADER_SIZE)
    raw = raw.reshape(height, width, step).astype(np.uint32)
    value = sum(raw[..., i] << (8 * i) for i in range(step))
    out = np.full((height, width, 4), 255, np.uint8)
    for channel, mask in enumerate(masks):
        if mask and (channel < 3 or has_alpha):
            shift = (mask & -mask).bit_length() - 1
            top = mask >> shift
            out[..., channel] = np.rint(((value & mask) >> shift) * 255.0 / top)
        elif channel < 3:
            out[..., channel] = 0
    return out


def _open_image(data):
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(data)) as image:
            return np.asarray(image.convert("RGBA")), None
    except (UnidentifiedImageError, OSError, NotImplementedError, ValueError) as exc:
        return None, f"cannot decode: {exc}"


def _read_dx10(data):
    """Decode a DX10-header file. Returns (kind, payload, problem)."""
    if len(data) < HEADER_SIZE + DX10_SIZE:
        return None, None, "truncated"
    height, width = struct.unpack_from("<II", data, 12)
    dxgi = struct.unpack_from("<I", data, HEADER_SIZE)[0]
    body = data[HEADER_SIZE + DX10_SIZE :]
    if dxgi in DX10_BLOCKS:
        fourcc = DX10_BLOCKS[dxgi]
        legacy = bytearray(data[:HEADER_SIZE])
        legacy[84:88] = fourcc
        return "blocks", bytes(legacy) + body, None
    if dxgi in DX10_RAW and len(body) >= width * height * 4 and width and height:
        texels = np.frombuffer(body, np.uint8, width * height * 4).reshape(
            height, width, 4
        )
        order = DX10_RAW[dxgi]
        rgba = texels[..., [2, 1, 0, 3]] if order.startswith("bgr") else texels
        rgba = rgba.copy()
        if order == "bgrx":
            rgba[..., 3] = 255
        return "image", rgba, None
    return None, None, f"unsupported DX10 format {dxgi}"


def read(data):
    """Classify a texture file.

    Returns (kind, payload, problem). Kind is "blocks" (a legacy DXT file,
    payload its bytes), "raw" (a standard A8R8G8B8 file, payload RGBA),
    "image" (anything else that decodes, payload RGBA) or None.
    """
    if data[:4] != b"DDS ":
        rgba, problem = _open_image(data)
        return ("image", rgba, None) if rgba is not None else (None, None, problem)
    if len(data) < HEADER_SIZE:
        return None, None, "truncated"
    height, width = struct.unpack_from("<II", data, 12)
    flags = struct.unpack_from("<I", data, 80)[0]
    fourcc = data[84:88] if flags & 4 else b""
    if fourcc == b"DX10":
        return _read_dx10(data)
    if fourcc:
        texture, problem = dds_mipmaps.read_header(data)
        return ("blocks", data, None) if texture else (None, None, problem)
    bits = struct.unpack_from("<I", data, 88)[0]
    masks = struct.unpack_from("<4I", data, 92)
    usable = bits in (16, 24, 32) or (bits == 8 and masks[0])
    if not usable or width == 0 or height == 0:
        return None, None, f"unsupported {bits}-bit format"
    if len(data) < HEADER_SIZE + width * height * bits // 8:
        return None, None, "truncated"
    has_alpha = bool(flags & 1)
    rgba = _from_masks(data, width, height, bits, masks, has_alpha)
    standard = (
        bits == 32 and masks[:3] == BGRA_MASKS[:3] and masks[3] in (0, BGRA_MASKS[3])
    )
    return ("raw" if standard else "image"), rgba, None


def quality(rgba, compressed):
    """(decibels of the visible colour, decibels of alpha, 99.9th percentile error)."""
    decoded, _ = _open_image(compressed)
    cover = rgba[..., 3].astype(np.float64) / 255.0
    diff = rgba[..., :3].astype(np.float64) - decoded[..., :3]
    alpha = rgba[..., 3].astype(np.float64) - decoded[..., 3]

    def decibels(mean):
        return 99.0 if mean < 1e-9 else float(10 * np.log10(255.0**2 / mean))

    visible = cover.sum() * 3
    colour = (diff**2 * cover[..., None]).sum() / visible if visible else 0.0
    worst = np.percentile(np.abs(diff).max(-1) * cover, 99.9)
    return decibels(colour), decibels((alpha**2).mean()), float(worst)


def passes_gate(rgba, compressed):
    colour, alpha, worst = quality(rgba, compressed)
    gate = model_standards.COMPRESS_GATE_DB
    return (
        colour >= gate
        and alpha >= gate
        and worst <= model_standards.COMPRESS_GATE_ERROR
    )


def _wants_blocks(rule, rgba):
    if rule == model_standards.FORMAT_PORTRAIT:
        return min(rgba.shape[:2]) >= model_standards.SMALL_PORTRAIT_SIZE
    return rule in (model_standards.FORMAT_COMPRESSED, model_standards.FORMAT_DXT5)


def _fourcc_for(rule, rgba):
    if rule == model_standards.FORMAT_DXT5 or (rgba[..., 3] < 255).any():
        return b"DXT5"
    return b"DXT1"


def _shrink(data, max_size):
    """A DXT file halved until its longer side fits. Stored levels are reused when possible."""
    texture, _ = dds_mipmaps.read_header(data)
    drop = 0
    while max(texture.width >> drop, texture.height >> drop) > max_size:
        drop += 1
    width, height = max(1, texture.width >> drop), max(1, texture.height >> drop)
    sizes = [texture.level_size(level) for level in range(texture.mipmaps)]
    if texture.mipmaps > drop and len(data) >= HEADER_SIZE + sum(sizes):
        start = HEADER_SIZE + sum(sizes[:drop])
        head = bytearray(data[:HEADER_SIZE])
        struct.pack_into("<II", head, 12, height, width)
        struct.pack_into("<I", head, 20, sizes[drop])
        left = texture.mipmaps - drop
        return (
            dds_mipmaps._with_mipmaps(bytes(head), left)
            + data[start : HEADER_SIZE + sum(sizes)]
        )
    from PIL import Image

    rgba, _ = _open_image(dds_mipmaps.strip(data, texture))
    small = np.asarray(
        Image.fromarray(rgba).resize((width, height), Image.Resampling.LANCZOS)
    )
    return as_blocks(small, texture.fourcc)


def standardize(data, rel_path, max_size=None):
    """The file as the standards want it. Returns (new bytes, what was done)."""
    rule = model_standards.texture_format(rel_path)
    if rule == model_standards.FORMAT_KEEP:
        return data, []
    kind, payload, problem = read(data)
    if kind is None:
        return data, [f"skipped: {problem}"]
    done = []
    out = data
    if kind == "blocks":
        if payload is not data:
            out = payload
            done.append("replaced the DX10 header")
    elif _wants_blocks(rule, payload):
        out = as_blocks(payload, _fourcc_for(rule, payload))
        done.append("compressed, as the standards say")
    elif kind == "image":
        out = as_raw(payload)
        done.append("rewritten as A8R8G8B8")
    gated = rule != model_standards.FORMAT_ICON and not _wants_blocks(rule, payload)
    if kind != "blocks" and gated:
        trial = as_blocks(payload, _fourcc_for(rule, payload))
        if passes_gate(payload, trial):
            out = trial
            done.append("compressed, passes the quality gate")
    is_model = (
        rule == model_standards.FORMAT_COMPRESSED and "/gfx/models/" in "/" + rel_path
    )
    texture, _ = dds_mipmaps.read_header(out)
    if (
        max_size
        and is_model
        and texture.fourcc
        and max(texture.width, texture.height) > max_size
    ):
        out = _shrink(out, max_size)
        done.append(f"shrunk to fit {max_size} px")
    action, _ = dds_mipmaps.plan(out, rel_path)
    if action in ("add", "strip"):
        out = dds_mipmaps.apply(out, action)
        done.append("mipmaps added" if action == "add" else "mipmaps dropped")
    return out, done


def run(paths, root, fix=False, write=False, max_size=None):
    """Check the paths. Prints one line per file to change; returns totals."""
    totals = Counter()
    for path in dds_mipmaps.collect(paths):
        rel_path = dds_mipmaps._relative(path, root)
        with open(path, "rb") as handle:
            data = handle.read()
        result, done = standardize(data, rel_path, max_size)
        totals["checked"] += 1
        totals.update(done)
        if not done:
            continue
        if result != data:
            totals["changed"] += 1
            totals["bytes"] += len(result) - len(data)
            if fix and write:
                with open(path, "wb") as handle:
                    handle.write(result)
        print(f"{rel_path}: {'; '.join(done)}")
    return totals


def main(argv=None):
    parser = dds_mipmaps.base_parser(__doc__.splitlines()[0])
    parser.add_argument(
        "--max-size", type=int, help="halve model textures until they fit this size"
    )
    args = parser.parse_args(argv)
    paths = dds_mipmaps.scope(args.paths, REPO_ROOT, DEFAULT_SCOPE)
    if paths is None:
        return 2
    totals = run(paths, REPO_ROOT, args.fix, args.fix and args.write, args.max_size)
    saved = args.fix and args.write
    print(f"\n{totals['checked']} textures checked, {totals['changed']} to change")
    for name, count in sorted(totals.items()):
        if name not in ("checked", "changed", "bytes"):
            print(f"  {name}: {count}")
    print(
        f"  size {'changed' if saved else 'would change'} by {totals['bytes'] / 1e6:+.1f} MB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
