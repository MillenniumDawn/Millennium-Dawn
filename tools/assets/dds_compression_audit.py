#!/usr/bin/env python3
"""Find uncompressed DDS textures and say what each should be re-encoded to.

    dds_compression_audit.py [paths...] [--min-kb N] [--limit N]
    dds_compression_audit.py --by-dir
    dds_compression_audit.py --emit-commands > convert.sh
    dds_compression_audit.py --format json

Reads DDS headers only, so it is pure stdlib and does not need ImageMagick or
texconv. It reports what to convert; converting is a separate step on a machine
that has texconv, which the --emit-commands output drives.

Follows docs/src/content/resources/art-standards.md, which allows only DXT1
(BC1) and DXT5 (BC3), asks for no mip chain, and tells authors to keep flat
colour art uncompressed because block compression blocks up on hard edges. So a
texture is offered for DXT1 when no mip level is translucent and DXT5 when any
level uses alpha, but only if it is photographic. Flat art, anything whose
width or height is not a multiple of 4, and anything already compressed are
each reported in their own bucket instead.
"""

import argparse
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

HEADER = 128
DX10_HEADER = 20
DDPF_ALPHAPIXELS = 0x1
DDPF_FOURCC = 0x4

# Bytes per 4x4 block.
BLOCK_BYTES = {"DXT1": 8, "DXT5": 16}

# art-standards.md lists DXT1 (BC1) and DXT5 (BC3) and nothing else. DXT3, BC7
# and the rest load or fail at the engine's discretion, so they are reported
# rather than left alone.
SUPPORTED_COMPRESSED = frozenset({"DXT1", "DXT5", "BC1", "BC3"})

# Share of sampled pixels that are a distinct colour. Measured on the tree, a
# playing card or logo sits near 0.002 and a photograph near 0.15, so anything
# under this is the flat art the standard says to leave uncompressed.
FLAT_COLOUR_RATIO = 0.02

# Every fourth pixel of the top level is enough to separate two orders of
# magnitude without reading whole textures.
FLAT_SAMPLE_STEP = 7

# DXGI formats that are already block compressed. Anything else behind a DX10
# container is an uncompressed payload and is a candidate like any other.
DXGI_BLOCK_COMPRESSED = frozenset(range(70, 85)) | frozenset(range(94, 100))

DXGI_NAMES = {
    70: "BC1",
    73: "BC2",
    76: "BC3",
    79: "BC4",
    82: "BC5",
    94: "BC6H",
    97: "BC7",
}


def _mip_levels(width, height):
    """How many mip levels this size can physically have."""
    levels = 1
    w, h = width, height
    while w > 1 or h > 1:
        w, h = max(1, w // 2), max(1, h // 2)
        levels += 1
    return levels


def _dxgi_label(fmt):
    for base, name in sorted(DXGI_NAMES.items()):
        if base <= fmt < base + 3:
            return name
    return f"DXGI{fmt}"


class Texture:
    """One parsed DDS file."""

    def __init__(
        self, path, size, width, height, fourcc, mipmaps, alpha_used, flat=False
    ):
        self.path = path
        self.size = size
        self.width = width
        self.height = height
        self.fourcc = fourcc
        self.mipmaps = mipmaps
        self.alpha_used = alpha_used
        self.flat = flat

    @property
    def compressed(self):
        return self.fourcc is not None

    @property
    def conforms(self):
        """True if an already compressed texture uses a format the standard lists."""
        return self.fourcc in SUPPORTED_COMPRESSED

    @property
    def block_aligned(self):
        return self.width % 4 == 0 and self.height % 4 == 0

    @property
    def target(self):
        return "DXT5" if self.alpha_used else "DXT1"

    def projected_size(self):
        """Size after re-encoding. The standard ships no mip chain, so this is
        the top level plus the header whatever the source carried."""
        per_block = BLOCK_BYTES[self.target]
        blocks = max(1, (self.width + 3) // 4) * max(1, (self.height + 3) // 4)
        return blocks * per_block + HEADER

    def saving(self):
        return max(0, self.size - self.projected_size())


def parse(path, alpha_floor=0):
    """Return a Texture, or None if the file is not a DDS we understand.

    The alpha scan walks every mip level, so it only runs for uncompressed
    files at or above alpha_floor bytes. Everything below that is counted in
    the inventory but never recommended, so its target never matters.
    """
    try:
        size = path.stat().st_size
        with open(path, "rb") as handle:
            head = handle.read(HEADER)
            if len(head) < HEADER or head[:4] != b"DDS ":
                return None
            height, width = struct.unpack("<II", head[12:20])
            if not 0 < width <= 1 << 16 or not 0 < height <= 1 << 16:
                return None

            # dwMipMapCount is attacker-controlled; clamp it to what the
            # dimensions can actually hold so no loop runs away.
            declared = struct.unpack("<I", head[28:32])[0]
            mipmaps = max(1, min(declared or 1, _mip_levels(width, height)))

            pf_flags = struct.unpack("<I", head[80:84])[0]
            fourcc = head[84:88]
            if pf_flags & DDPF_FOURCC and fourcc.strip(b"\x00"):
                name = fourcc.decode("ascii", "replace").strip("\x00")
                if name == "DX10":
                    ext = handle.read(DX10_HEADER)
                    if len(ext) < DX10_HEADER:
                        return None
                    dxgi = struct.unpack("<I", ext[0:4])[0]
                    if dxgi in DXGI_BLOCK_COMPRESSED:
                        return Texture(
                            path, size, width, height, _dxgi_label(dxgi), mipmaps, False
                        )
                    # Uncompressed payload in a DX10 container: a real candidate.
                    alpha = flat = False
                    if size >= alpha_floor:
                        start = HEADER + DX10_HEADER
                        alpha = _alpha_is_used(
                            handle, width, height, 0xFF000000, mipmaps, start
                        )
                        flat = _is_flat_colour(handle, width, height, start)
                    return Texture(
                        path, size, width, height, None, mipmaps, alpha, flat
                    )
                return Texture(path, size, width, height, name, mipmaps, False)

            bit_count = struct.unpack("<I", head[88:92])[0]
            alpha_mask = struct.unpack("<I", head[104:108])[0]
            alpha_used = flat = False
            if size >= alpha_floor and bit_count == 32:
                if pf_flags & DDPF_ALPHAPIXELS and alpha_mask:
                    alpha_used = _alpha_is_used(
                        handle, width, height, alpha_mask, mipmaps, HEADER
                    )
                flat = _is_flat_colour(handle, width, height, HEADER)
            return Texture(path, size, width, height, None, mipmaps, alpha_used, flat)
    except (OSError, struct.error):
        return None


def _is_flat_colour(handle, width, height, data_start):
    """True if the top level is flat art rather than a photograph.

    art-standards.md asks for flat colour and hard edged art to stay
    uncompressed, because DXT blocks up on it: the doc measures a two colour
    logo at about 26 dB PSNR against 30 dB on a painting. Distinct colours per
    sampled pixel separates the two cleanly on this tree, a playing card
    landing near 0.002 and a background near 0.15.
    """
    pixels = width * height
    handle.seek(data_start)
    body = handle.read(pixels * 4)
    if len(body) < pixels * 4:
        return False
    colours = {body[i * 4 : i * 4 + 4] for i in range(0, pixels, FLAT_SAMPLE_STEP)}
    sampled = len(range(0, pixels, FLAT_SAMPLE_STEP))
    return len(colours) / sampled < FLAT_COLOUR_RATIO


def _alpha_is_used(handle, width, height, alpha_mask, mipmaps, data_start):
    """True if any pixel in any mip level is translucent.

    An all-opaque alpha channel costs nothing to discard, which is the
    difference between a 4x and an 8x saving. A texture can be opaque at the
    top level and translucent further down, so every level is checked before
    DXT1 is offered.
    """
    shift = (alpha_mask & -alpha_mask).bit_length() - 1
    handle.seek(data_start)
    w, h = width, height
    for _ in range(mipmaps):
        remaining = w * h * 4
        while remaining > 0:
            chunk = handle.read(min(1 << 20, remaining))
            if not chunk:
                return False
            remaining -= len(chunk)
            for offset in range(0, len(chunk) - 3, 4):
                pixel = struct.unpack_from("<I", chunk, offset)[0]
                if ((pixel & alpha_mask) >> shift) != 0xFF:
                    return True
        w, h = max(1, w // 2), max(1, h // 2)
    return False


def collect(roots):
    for root in roots:
        root = Path(root)
        if root.is_file():
            yield root
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() == ".dds":
                yield path


def build_report(paths, floor):
    """Return (convert, skipped, flat, nonconforming, counts, sizes)."""
    convert, skipped, flat, nonconforming = [], [], [], []
    counts, sizes = defaultdict(int), defaultdict(int)
    for path in collect(paths):
        texture = parse(path, floor)
        if texture is None:
            continue
        label = texture.fourcc or "UNCOMPRESSED"
        counts[label] += 1
        sizes[label] += texture.size
        if texture.compressed:
            if not texture.conforms:
                nonconforming.append(texture)
            continue
        if texture.size < floor:
            continue
        if texture.flat:
            flat.append(texture)
        elif texture.block_aligned:
            convert.append(texture)
        else:
            skipped.append(texture)
    convert.sort(key=lambda t: -t.saving())
    flat.sort(key=lambda t: -t.size)
    return convert, skipped, flat, nonconforming, counts, sizes


def texconv_command(texture):
    """texconv invocation for one texture.

    art-standards.md asks for no mip chain on every category, so -m is always
    1. texconv reads 0 as "the full chain", which would both disobey the
    standard and add levels a single-level source never had.
    """
    fmt = "BC3_UNORM" if texture.target == "DXT5" else "BC1_UNORM"
    path = str(texture.path).replace("\\", "/")
    return f'texconv -f {fmt} -m 1 -y -o "{Path(path).parent}" "{path}"'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "paths", nargs="*", default=["gfx"], help="files or directories (default: gfx)"
    )
    parser.add_argument(
        "--min-kb",
        type=float,
        default=64.0,
        help="ignore files smaller than this (default: 64)",
    )
    parser.add_argument(
        "--limit", type=int, default=40, help="rows to print (default: 40, 0 for all)"
    )
    parser.add_argument(
        "--by-dir", action="store_true", help="group the saving by directory instead"
    )
    parser.add_argument(
        "--emit-commands",
        action="store_true",
        help="print texconv commands instead of a report",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    floor = args.min_kb * 1024
    convert, skipped, flat, nonconforming, counts, sizes = build_report(
        args.paths, floor
    )
    total_saving = sum(t.saving() for t in convert)

    if args.format == "json":
        json.dump(
            {
                "inventory": {
                    k: {"files": counts[k], "bytes": sizes[k]} for k in counts
                },
                "convert": [
                    {
                        "path": str(t.path).replace("\\", "/"),
                        "width": t.width,
                        "height": t.height,
                        "mipmaps": t.mipmaps,
                        "bytes": t.size,
                        "target": t.target,
                        "projected_bytes": t.projected_size(),
                        "saving_bytes": t.saving(),
                    }
                    for t in convert
                ],
                "skipped_not_block_aligned": [
                    str(t.path).replace("\\", "/") for t in skipped
                ],
                "kept_uncompressed_flat_art": [
                    str(t.path).replace("\\", "/") for t in flat
                ],
                "unsupported_format": [
                    {"path": str(t.path).replace("\\", "/"), "format": t.fourcc}
                    for t in nonconforming
                ],
                "total_saving_bytes": total_saving,
            },
            sys.stdout,
            indent=2,
        )
        return 0

    if args.emit_commands:
        print("# Re-encode uncompressed DDS textures. Needs texconv on PATH.")
        print(f"# {len(convert)} files, about {total_saving / 1048576:.0f} MB saved.")
        for texture in convert:
            print(texconv_command(texture))
        return 0

    print("DDS INVENTORY")
    for label in sorted(counts, key=lambda k: -sizes[k]):
        print(f"  {label:14} {counts[label]:7} files  {sizes[label] / 1048576:9.1f} MB")

    print(
        f"\nRECOMMENDED RE-ENCODES  (photographic, uncompressed, at least "
        f"{args.min_kb:.0f} KB, block aligned)"
    )
    print(f"  {len(convert)} files, about {total_saving / 1048576:.0f} MB saved\n")

    if args.by_dir:
        per_dir = defaultdict(int)
        for texture in convert:
            per_dir[str(texture.path.parent).replace("\\", "/")] += texture.saving()
        rows = sorted(per_dir.items(), key=lambda kv: -kv[1])
        for directory, saving in rows[: args.limit or len(rows)]:
            print(f"  {saving / 1048576:8.1f} MB  {directory}")
    else:
        for texture in convert[: args.limit or len(convert)]:
            path = str(texture.path).replace("\\", "/")
            print(
                f"  {texture.size / 1048576:6.2f} -> {texture.projected_size() / 1048576:5.2f} MB"
                f"  {texture.target}  {texture.width}x{texture.height}  {path}"
            )

    if skipped:
        print(
            f"\nSKIPPED, not a multiple of 4 so block compression would need padding: {len(skipped)}"
        )
        for texture in skipped[:10]:
            print(
                f"  {texture.width}x{texture.height}  {str(texture.path).replace(chr(92), '/')}"
            )

    if flat:
        kept = sum(t.size for t in flat) / 1048576
        print(
            f"\nLEFT ALONE, flat colour art the standard keeps uncompressed: "
            f"{len(flat)} files, {kept:.0f} MB"
        )
        for texture in flat[:10]:
            print(
                f"  {texture.size / 1048576:6.2f} MB  {texture.width}x{texture.height}"
                f"  {str(texture.path).replace(chr(92), '/')}"
            )

    if nonconforming:
        print(
            f"\nNOT IN art-standards.md, which lists only DXT1 and DXT5: "
            f"{len(nonconforming)} files"
        )
        for texture in nonconforming[:10]:
            print(f"  {texture.fourcc:6}  {str(texture.path).replace(chr(92), '/')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
