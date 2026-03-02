#!/usr/bin/env python3
"""
Convert DDS files to DXT1 (BC1) or DXT5 (BC3) format without mipmaps.
Handles: DXT1, DXT3, DXT5 (legacy FourCC) and DX10 BC1–BC3, B8G8R8A8, R8G8B8A8.

Usage:
  batchdds-2.py <file_or_dir> [output.dds] [--format dxt5|dxt1|auto]

  --format dxt5   Always output DXT5 — preserves alpha (default)
  --format dxt1   Always output DXT1 — no alpha, smaller file
  --format auto   Pick DXT5 when transparency is detected, DXT1 otherwise
"""

import argparse
import os
import struct
import sys
from pathlib import Path

# DDS constants
DDS_MAGIC = 0x20534444
DDSD_CAPS = 0x1
DDSD_HEIGHT = 0x2
DDSD_WIDTH = 0x4
DDSD_PIXELFORMAT = 0x1000
DDSD_LINEARSIZE = 0x80000
DDSCAPS_TEXTURE = 0x1000
DDPF_FOURCC = 0x4
DDPF_RGB = 0x40

DXT1_FOURCC = 0x31545844  # "DXT1"
DXT3_FOURCC = 0x33545844  # "DXT3"
DXT5_FOURCC = 0x35545844  # "DXT5"
DX10_FOURCC = 0x30315844  # "DX10"

# DXGI formats
DXGI_FORMAT_R8G8B8A8_UNORM = 28
DXGI_FORMAT_R8G8B8A8_UNORM_SRGB = 29
DXGI_FORMAT_BC1_UNORM = 71
DXGI_FORMAT_BC1_UNORM_SRGB = 72
DXGI_FORMAT_BC2_UNORM = 74
DXGI_FORMAT_BC2_UNORM_SRGB = 75
DXGI_FORMAT_BC3_UNORM = 77
DXGI_FORMAT_BC3_UNORM_SRGB = 78
DXGI_FORMAT_B8G8R8A8_UNORM = 87
DXGI_FORMAT_B8G8R8X8_UNORM = 88
DXGI_FORMAT_B8G8R8A8_UNORM_SRGB = 91


# ── Helpers ───────────────────────────────────────────────────────────────────


def rgb_to_565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def rgb565_to_rgb(c):
    r = ((c >> 11) & 0x1F) * 255 // 31
    g = ((c >> 5) & 0x3F) * 255 // 63
    b = (c & 0x1F) * 255 // 31
    return r, g, b


def color_dist_sq(r1, g1, b1, r2, g2, b2):
    return (
        (int(r1) - int(r2)) ** 2 + (int(g1) - int(g2)) ** 2 + (int(b1) - int(b2)) ** 2
    )


def _color_block_palette(raw, off):
    """Return the 4-entry RGB palette from an 8-byte DXT color block."""
    c0_565, c1_565 = struct.unpack_from("<HH", raw, off)
    c0 = rgb565_to_rgb(c0_565)
    c1 = rgb565_to_rgb(c1_565)
    if c0_565 > c1_565:
        return [
            c0,
            c1,
            (
                (2 * c0[0] + c1[0]) // 3,
                (2 * c0[1] + c1[1]) // 3,
                (2 * c0[2] + c1[2]) // 3,
            ),
            (
                (c0[0] + 2 * c1[0]) // 3,
                (c0[1] + 2 * c1[1]) // 3,
                (c0[2] + 2 * c1[2]) // 3,
            ),
        ]
    else:
        return [
            c0,
            c1,
            ((c0[0] + c1[0]) // 2, (c0[1] + c1[1]) // 2, (c0[2] + c1[2]) // 2),
            (0, 0, 0),
        ]


# ── Decompressors → flat list of (b, g, r, a) ────────────────────────────────


def decompress_dxt1(raw, width, height):
    """Decompress DXT1 to flat (b,g,r,a) list. Transparent blocks get a=0."""
    pw = (width + 3) & ~3
    ph = (height + 3) & ~3
    bx_count = pw // 4
    pixels = [(0, 0, 0, 255)] * (width * height)
    for by in range(ph // 4):
        for bx in range(bx_count):
            off = (by * bx_count + bx) * 8
            c0_565, c1_565 = struct.unpack_from("<HH", raw, off)
            pal = _color_block_palette(raw, off)
            idx_dw = struct.unpack_from("<I", raw, off + 4)[0]
            has_transparency = c0_565 <= c1_565
            for py in range(4):
                for px in range(4):
                    dy, dx = by * 4 + py, bx * 4 + px
                    if dy < height and dx < width:
                        i = (idx_dw >> ((py * 4 + px) * 2)) & 0x3
                        if has_transparency and i == 3:
                            pixels[dy * width + dx] = (0, 0, 0, 0)
                        else:
                            r, g, b = pal[i]
                            pixels[dy * width + dx] = (b, g, r, 255)
    return pixels


def decompress_dxt3(raw, width, height):
    """Decompress DXT3 to flat (b,g,r,a) list."""
    pw = (width + 3) & ~3
    ph = (height + 3) & ~3
    bx_count = pw // 4
    pixels = [(0, 0, 0, 255)] * (width * height)
    for by in range(ph // 4):
        for bx in range(bx_count):
            off = (by * bx_count + bx) * 16
            color_off = off + 8
            pal = _color_block_palette(raw, color_off)
            idx_dw = struct.unpack_from("<I", raw, color_off + 4)[0]
            for py in range(4):
                for px in range(4):
                    dy, dx = by * 4 + py, bx * 4 + px
                    if dy < height and dx < width:
                        pi = py * 4 + px
                        # 4-bit alpha packed two-per-byte
                        ab = raw[off + pi // 2]
                        nibble = (ab >> ((pi % 2) * 4)) & 0xF
                        a = nibble * 255 // 15
                        r, g, b = pal[(idx_dw >> (pi * 2)) & 0x3]
                        pixels[dy * width + dx] = (b, g, r, a)
    return pixels


def decompress_dxt5(raw, width, height):
    """Decompress DXT5 to flat (b,g,r,a) list."""
    pw = (width + 3) & ~3
    ph = (height + 3) & ~3
    bx_count = pw // 4
    pixels = [(0, 0, 0, 255)] * (width * height)
    for by in range(ph // 4):
        for bx in range(bx_count):
            off = (by * bx_count + bx) * 16
            color_off = off + 8

            # Alpha block
            a0, a1 = raw[off], raw[off + 1]
            idx_bits = 0
            for k in range(6):
                idx_bits |= raw[off + 2 + k] << (k * 8)
            if a0 > a1:
                apal = [
                    a0,
                    a1,
                    (6 * a0 + 1 * a1) // 7,
                    (5 * a0 + 2 * a1) // 7,
                    (4 * a0 + 3 * a1) // 7,
                    (3 * a0 + 4 * a1) // 7,
                    (2 * a0 + 5 * a1) // 7,
                    (1 * a0 + 6 * a1) // 7,
                ]
            else:
                apal = [
                    a0,
                    a1,
                    (4 * a0 + 1 * a1) // 5,
                    (3 * a0 + 2 * a1) // 5,
                    (2 * a0 + 3 * a1) // 5,
                    (1 * a0 + 4 * a1) // 5,
                    0,
                    255,
                ]

            pal = _color_block_palette(raw, color_off)
            idx_dw = struct.unpack_from("<I", raw, color_off + 4)[0]

            for py in range(4):
                for px in range(4):
                    dy, dx = by * 4 + py, bx * 4 + px
                    if dy < height and dx < width:
                        pi = py * 4 + px
                        a = apal[(idx_bits >> (pi * 3)) & 0x7]
                        r, g, b = pal[(idx_dw >> (pi * 2)) & 0x3]
                        pixels[dy * width + dx] = (b, g, r, a)
    return pixels


def decode_bgra(raw, width, height):
    return [
        (raw[i * 4], raw[i * 4 + 1], raw[i * 4 + 2], raw[i * 4 + 3])
        for i in range(width * height)
    ]


def decode_rgba(raw, width, height):
    return [
        (raw[i * 4 + 2], raw[i * 4 + 1], raw[i * 4], raw[i * 4 + 3])
        for i in range(width * height)
    ]


def decode_bgrx(raw, width, height):
    """B8G8R8X8 — no alpha channel, treat as fully opaque."""
    return [
        (raw[i * 4], raw[i * 4 + 1], raw[i * 4 + 2], 255) for i in range(width * height)
    ]


# ── Compressors ───────────────────────────────────────────────────────────────


def _compress_color_block(bgra_block):
    """Compress 16 (b,g,r,a) tuples to an 8-byte DXT color block."""
    rgb = [(p[2], p[1], p[0]) for p in bgra_block]  # r, g, b

    min_r = min(p[0] for p in rgb)
    max_r = max(p[0] for p in rgb)
    min_g = min(p[1] for p in rgb)
    max_g = max(p[1] for p in rgb)
    min_b = min(p[2] for p in rgb)
    max_b = max(p[2] for p in rgb)

    c0_565 = rgb_to_565(max_r, max_g, max_b)
    c1_565 = rgb_to_565(min_r, min_g, min_b)

    if c0_565 <= c1_565:
        c0_565, c1_565 = c1_565, c0_565
    if c0_565 == c1_565 and c0_565 > 0:
        c1_565 -= 1

    c0r, c0g, c0b = rgb565_to_rgb(c0_565)
    c1r, c1g, c1b = rgb565_to_rgb(c1_565)

    palette = [
        (c0r, c0g, c0b),
        (c1r, c1g, c1b),
        ((2 * c0r + c1r) // 3, (2 * c0g + c1g) // 3, (2 * c0b + c1b) // 3),
        ((c0r + 2 * c1r) // 3, (c0g + 2 * c1g) // 3, (c0b + 2 * c1b) // 3),
    ]

    indices = 0
    for i, (pr, pg, pb) in enumerate(rgb):
        best_idx = min(range(4), key=lambda j: color_dist_sq(pr, pg, pb, *palette[j]))
        indices |= best_idx << (i * 2)

    return struct.pack("<HHI", c0_565, c1_565, indices)


def _compress_dxt5_alpha_block(alphas):
    """Compress 16 alpha values to an 8-byte DXT5 alpha block."""
    a0 = max(alphas)
    a1 = min(alphas)
    if a0 <= a1:
        a0, a1 = a1, a0
    if a0 == a1 and a0 > 0:
        a1 -= 1

    if a0 > a1:
        apal = [
            a0,
            a1,
            (6 * a0 + 1 * a1) // 7,
            (5 * a0 + 2 * a1) // 7,
            (4 * a0 + 3 * a1) // 7,
            (3 * a0 + 4 * a1) // 7,
            (2 * a0 + 5 * a1) // 7,
            (1 * a0 + 6 * a1) // 7,
        ]
    else:
        apal = [
            a0,
            a1,
            (4 * a0 + 1 * a1) // 5,
            (3 * a0 + 2 * a1) // 5,
            (2 * a0 + 3 * a1) // 5,
            (1 * a0 + 4 * a1) // 5,
            0,
            255,
        ]

    idx_bits = 0
    for i, a in enumerate(alphas):
        best_idx = min(range(8), key=lambda j: abs(int(a) - apal[j]))
        idx_bits |= best_idx << (i * 3)

    idx_bytes = bytes((idx_bits >> (k * 8)) & 0xFF for k in range(6))
    return bytes([a0, a1]) + idx_bytes


def compress_to_dxt1(pixels, width, height):
    """Compress flat (b,g,r,a) list to DXT1 data (alpha discarded)."""
    pw = (width + 3) & ~3
    ph = (height + 3) & ~3
    out = bytearray()
    for by in range(ph // 4):
        for bx in range(pw // 4):
            block = [
                pixels[
                    min(by * 4 + py, height - 1) * width + min(bx * 4 + px, width - 1)
                ]
                for py in range(4)
                for px in range(4)
            ]
            out += _compress_color_block(block)
    return out


def compress_to_dxt5(pixels, width, height):
    """Compress flat (b,g,r,a) list to DXT5 data (alpha preserved)."""
    pw = (width + 3) & ~3
    ph = (height + 3) & ~3
    out = bytearray()
    for by in range(ph // 4):
        for bx in range(pw // 4):
            block = [
                pixels[
                    min(by * 4 + py, height - 1) * width + min(bx * 4 + px, width - 1)
                ]
                for py in range(4)
                for px in range(4)
            ]
            out += _compress_dxt5_alpha_block([p[3] for p in block])
            out += _compress_color_block(block)
    return out


# ── DDS header builders ───────────────────────────────────────────────────────


def _make_header(width, height, fourcc, bytes_per_block):
    linear_size = max(
        bytes_per_block, ((width + 3) // 4) * ((height + 3) // 4) * bytes_per_block
    )
    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_LINEARSIZE

    hdr = struct.pack("<I", DDS_MAGIC)
    hdr += struct.pack("<I", 124)
    hdr += struct.pack("<I", flags)
    hdr += struct.pack("<I", height)
    hdr += struct.pack("<I", width)
    hdr += struct.pack("<I", linear_size)
    hdr += struct.pack("<I", 0)  # depth
    hdr += struct.pack("<I", 0)  # mipMapCount
    hdr += b"\x00" * 44  # reserved1[11]
    hdr += struct.pack("<I", 32)
    hdr += struct.pack("<I", DDPF_FOURCC)
    hdr += struct.pack("<I", fourcc)
    hdr += b"\x00" * 20  # rgbBitCount + masks
    hdr += struct.pack("<I", DDSCAPS_TEXTURE)
    hdr += b"\x00" * 16  # caps2–4, reserved2
    return hdr


def make_dxt1_header(width, height):
    return _make_header(width, height, DXT1_FOURCC, 8)


def make_dxt5_header(width, height):
    return _make_header(width, height, DXT5_FOURCC, 16)


# ── Main conversion ───────────────────────────────────────────────────────────


def convert_dds(input_path, output_path=None, fmt="dxt5"):
    """
    Convert any supported DDS to DXT1 or DXT5 (no mipmaps).

    fmt: "dxt5"  – always output DXT5 (default)
         "dxt1"  – always output DXT1
         "auto"  – DXT5 if transparency detected, DXT1 otherwise
    """
    if output_path is None:
        output_path = input_path

    with open(input_path, "rb") as f:
        data = bytearray(f.read())

    if struct.unpack_from("<I", data, 0)[0] != DDS_MAGIC:
        raise ValueError("not a valid DDS file")

    header_size = struct.unpack_from("<I", data, 4)[0]
    if header_size != 124:
        raise ValueError(f"unexpected header size {header_size}")

    height = struct.unpack_from("<I", data, 12)[0]
    width = struct.unpack_from("<I", data, 16)[0]
    pf_flags = struct.unpack_from("<I", data, 80)[0]
    pf_fourcc = struct.unpack_from("<I", data, 84)[0]

    pixels = None
    fmt_name = "unknown"

    # ── Legacy FourCC ─────────────────────────────────────────────────────────
    if pf_fourcc == DXT1_FOURCC:
        fmt_name = "DXT1"
        pixels = decompress_dxt1(data[128:], width, height)

    elif pf_fourcc == DXT3_FOURCC:
        fmt_name = "DXT3"
        pixels = decompress_dxt3(data[128:], width, height)

    elif pf_fourcc == DXT5_FOURCC:
        fmt_name = "DXT5"
        pixels = decompress_dxt5(data[128:], width, height)

    elif pf_fourcc == DX10_FOURCC:
        # ── DX10 extension ────────────────────────────────────────────────────
        dxgi = struct.unpack_from("<I", data, 128)[0]
        pixel_start = 148

        if dxgi in (DXGI_FORMAT_BC1_UNORM, DXGI_FORMAT_BC1_UNORM_SRGB):
            fmt_name = "BC1/DXT1"
            pixels = decompress_dxt1(data[pixel_start:], width, height)

        elif dxgi in (DXGI_FORMAT_BC2_UNORM, DXGI_FORMAT_BC2_UNORM_SRGB):
            fmt_name = "BC2/DXT3"
            pixels = decompress_dxt3(data[pixel_start:], width, height)

        elif dxgi in (DXGI_FORMAT_BC3_UNORM, DXGI_FORMAT_BC3_UNORM_SRGB):
            fmt_name = "BC3/DXT5"
            pixels = decompress_dxt5(data[pixel_start:], width, height)

        elif dxgi in (DXGI_FORMAT_B8G8R8A8_UNORM, DXGI_FORMAT_B8G8R8A8_UNORM_SRGB):
            fmt_name = "B8G8R8A8"
            pixels = decode_bgra(data[pixel_start:], width, height)

        elif dxgi == DXGI_FORMAT_B8G8R8X8_UNORM:
            fmt_name = "B8G8R8X8"
            pixels = decode_bgrx(data[pixel_start:], width, height)

        elif dxgi in (DXGI_FORMAT_R8G8B8A8_UNORM, DXGI_FORMAT_R8G8B8A8_UNORM_SRGB):
            fmt_name = "R8G8B8A8"
            pixels = decode_rgba(data[pixel_start:], width, height)

        else:
            raise ValueError(f"unsupported DXGI format {dxgi}")

    elif pf_flags & DDPF_RGB:
        # ── Legacy uncompressed ───────────────────────────────────────────────
        rgb_bits = struct.unpack_from("<I", data, 88)[0]
        r_mask = struct.unpack_from("<I", data, 92)[0]
        if rgb_bits == 32:
            if r_mask == 0x00FF0000:
                fmt_name = "B8G8R8A8 (legacy)"
                pixels = decode_bgra(data[128:], width, height)
            else:
                fmt_name = "R8G8B8A8 (legacy)"
                pixels = decode_rgba(data[128:], width, height)
        else:
            raise ValueError(f"unsupported legacy uncompressed format ({rgb_bits}-bit)")

    else:
        raise ValueError(f"unrecognized pixel format (fourcc=0x{pf_fourcc:08X})")

    # Resolve output format
    if fmt == "dxt5":
        use_dxt5 = True
    elif fmt == "dxt1":
        use_dxt5 = False
    else:  # auto
        use_dxt5 = any(p[3] < 255 for p in pixels)

    if use_dxt5:
        out_fmt = "DXT5"
        header = make_dxt5_header(width, height)
        compress = compress_to_dxt5
    else:
        out_fmt = "DXT1"
        header = make_dxt1_header(width, height)
        compress = compress_to_dxt1

    print(f"Converting: {input_path}  ({width}x{height}, {fmt_name} → {out_fmt})")
    compressed = compress(pixels, width, height)

    with open(output_path, "wb") as f:
        f.write(header)
        f.write(compressed)

    print(f"  ✓ Saved: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Convert DDS files to DXT1 (BC1) or DXT5 (BC3) without mipmaps.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  batchdds-2.py gfx/                        # DXT5 (default)\n"
            "  batchdds-2.py gfx/ --format dxt1          # force DXT1\n"
            "  batchdds-2.py gfx/ --format auto          # auto-detect per file\n"
            "  batchdds-2.py input.dds output.dds        # single file, DXT5\n"
            "  batchdds-2.py input.dds output.dds -f dxt1"
        ),
    )
    parser.add_argument("input", help="input .dds file or directory")
    parser.add_argument(
        "output", nargs="?", help="output .dds file (single-file mode only)"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["dxt5", "dxt1", "auto"],
        default="dxt5",
        help="output format: dxt5 (default), dxt1, or auto (detect from alpha)",
    )
    args = parser.parse_args()

    if os.path.isdir(args.input):
        if args.output:
            parser.error("output path cannot be used with a directory input")
        print(f"Processing directory: {args.input}  (format: {args.format.upper()})")
        count = 0
        failed = []
        for dds_file in Path(args.input).rglob("*.dds"):
            path = str(dds_file)
            try:
                if convert_dds(path, fmt=args.format):
                    count += 1
            except Exception as e:
                failed.append((path, str(e)))
                print(f"  ✗ Failed: {path}: {e}")

        print(f"\nConverted {count} file(s)")
        if failed:
            print(f"\n── {len(failed)} file(s) failed ──────────────────────────")
            for path, reason in failed:
                print(f"  ✗ {path}")
                print(f"    {reason}")
    else:
        try:
            convert_dds(args.input, args.output, fmt=args.format)
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
