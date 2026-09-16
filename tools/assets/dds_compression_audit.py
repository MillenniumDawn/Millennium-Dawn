#!/usr/bin/env python3
"""Find uncompressed DDS textures and say what each should be re-encoded to.

    dds_compression_audit.py [paths...] [--min-kb N] [--limit N]
    dds_compression_audit.py --by-dir
    dds_compression_audit.py --emit-commands > convert.sh
    dds_compression_audit.py --format json

Reads DDS headers only, so it is pure stdlib and does not need ImageMagick or
texconv. It reports what to convert; converting is a separate step on a machine
that has texconv or ImageMagick, which the --emit-commands output drives.

A texture is recommended for DXT1 when nothing in it is translucent, and DXT5
when the alpha channel is actually used. Textures whose width or height is not
a multiple of 4 are reported as skipped, because block compression cannot
represent them without padding.
"""

import argparse
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

HEADER = 128
DDPF_ALPHAPIXELS = 0x1
DDPF_FOURCC = 0x4

# Bytes per 4x4 block.
BLOCK_BYTES = {"DXT1": 8, "DXT5": 16}


class Texture:
    """One parsed DDS file."""

    def __init__(self, path, size, width, height, fourcc, mipmaps, alpha_used):
        self.path = path
        self.size = size
        self.width = width
        self.height = height
        self.fourcc = fourcc
        self.mipmaps = mipmaps
        self.alpha_used = alpha_used

    @property
    def compressed(self):
        return self.fourcc is not None

    @property
    def block_aligned(self):
        return self.width % 4 == 0 and self.height % 4 == 0

    @property
    def target(self):
        return "DXT5" if self.alpha_used else "DXT1"

    def projected_size(self):
        """Size after re-encoding, including the mip chain and header."""
        per_block = BLOCK_BYTES[self.target]
        total = 0
        w, h = self.width, self.height
        for _ in range(max(self.mipmaps, 1)):
            total += max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * per_block
            w, h = max(1, w // 2), max(1, h // 2)
        return total + HEADER

    def saving(self):
        return max(0, self.size - self.projected_size())


def parse(path, alpha_floor=0):
    """Return a Texture, or None if the file is not a DDS we understand.

    The alpha scan reads the whole top mip, so it only runs for uncompressed
    files at or above alpha_floor bytes. Everything below that is reported in
    the inventory but never recommended, so its target never matters.
    """
    try:
        size = path.stat().st_size
        with open(path, "rb") as handle:
            head = handle.read(HEADER)
            if len(head) < HEADER or head[:4] != b"DDS ":
                return None
            height, width = struct.unpack("<II", head[12:20])
            mipmaps = struct.unpack("<I", head[28:32])[0]
            pf_flags = struct.unpack("<I", head[80:84])[0]
            fourcc = head[84:88]
            if pf_flags & DDPF_FOURCC and fourcc.strip(b"\x00"):
                name = fourcc.decode("ascii", "replace").strip("\x00")
                return Texture(path, size, width, height, name, mipmaps, False)

            bit_count = struct.unpack("<I", head[88:92])[0]
            alpha_mask = struct.unpack("<I", head[104:108])[0]
            alpha_used = False
            if size >= alpha_floor and pf_flags & DDPF_ALPHAPIXELS and bit_count == 32 and alpha_mask:
                alpha_used = _alpha_is_used(handle, width, height, alpha_mask)
            return Texture(path, size, width, height, None, mipmaps, alpha_used)
    except (OSError, struct.error):
        return None


def _alpha_is_used(handle, width, height, alpha_mask):
    """True if any pixel in the top mip is translucent.

    An all-opaque alpha channel costs nothing to discard, which is the
    difference between a 4x and an 8x saving, so it is worth the read.
    """
    shift = (alpha_mask & -alpha_mask).bit_length() - 1
    remaining = width * height * 4
    handle.seek(HEADER)
    while remaining > 0:
        chunk = handle.read(min(1 << 20, remaining))
        if not chunk:
            break
        remaining -= len(chunk)
        for offset in range(0, len(chunk) - 3, 4):
            pixel = struct.unpack_from("<I", chunk, offset)[0]
            if ((pixel & alpha_mask) >> shift) != 0xFF:
                return True
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", default=["gfx"], help="files or directories (default: gfx)")
    parser.add_argument("--min-kb", type=float, default=64.0, help="ignore files smaller than this (default: 64)")
    parser.add_argument("--limit", type=int, default=40, help="rows to print (default: 40, 0 for all)")
    parser.add_argument("--by-dir", action="store_true", help="group the saving by directory instead")
    parser.add_argument("--emit-commands", action="store_true", help="print texconv commands instead of a report")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    floor = args.min_kb * 1024
    convert, skipped = [], []
    counts, sizes = defaultdict(int), defaultdict(int)

    for path in collect(args.paths):
        texture = parse(path, floor)
        if texture is None:
            continue
        label = texture.fourcc or "UNCOMPRESSED"
        counts[label] += 1
        sizes[label] += texture.size
        if texture.compressed or texture.size < floor:
            continue
        (convert if texture.block_aligned else skipped).append(texture)

    convert.sort(key=lambda t: -t.saving())
    total_saving = sum(t.saving() for t in convert)

    if args.format == "json":
        json.dump(
            {
                "inventory": {k: {"files": counts[k], "bytes": sizes[k]} for k in counts},
                "convert": [
                    {
                        "path": str(t.path).replace("\\", "/"),
                        "width": t.width,
                        "height": t.height,
                        "bytes": t.size,
                        "target": t.target,
                        "projected_bytes": t.projected_size(),
                        "saving_bytes": t.saving(),
                    }
                    for t in convert
                ],
                "skipped_not_block_aligned": [str(t.path).replace("\\", "/") for t in skipped],
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
            path = str(texture.path).replace("\\", "/")
            print(
                f'texconv -f BC{"3" if texture.target == "DXT5" else "1"}_UNORM -m 0 -y -o "{Path(path).parent}" "{path}"'
            )
        return 0

    print("DDS INVENTORY")
    for label in sorted(counts, key=lambda k: -sizes[k]):
        print(f"  {label:14} {counts[label]:7} files  {sizes[label] / 1048576:9.1f} MB")

    print(f"\nRECOMMENDED RE-ENCODES  (uncompressed, at least {args.min_kb:.0f} KB, block aligned)")
    print(f"  {len(convert)} files, about {total_saving / 1048576:.0f} MB saved\n")

    if args.by_dir:
        per_dir = defaultdict(int)
        for texture in convert:
            per_dir[str(texture.path.parent).replace("\\", "/")] += texture.saving()
        rows = sorted(per_dir.items(), key=lambda kv: -kv[1])
        for directory, saving in rows[: args.limit or len(rows)]:
            print(f"  {saving / 1048576:8.1f} MB  {directory}")
    else:
        rows = convert[: args.limit or len(convert)]
        for texture in rows:
            print(
                f"  {texture.size / 1048576:6.2f} -> {texture.projected_size() / 1048576:5.2f} MB"
                f"  {texture.target}  {texture.width}x{texture.height}"
                f"  {str(texture.path).replace(chr(92), '/')}"
            )

    if skipped:
        print(f"\nSKIPPED, not a multiple of 4 so block compression would need padding: {len(skipped)}")
        for texture in skipped[:10]:
            print(f"  {texture.width}x{texture.height}  {str(texture.path).replace(chr(92), '/')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
