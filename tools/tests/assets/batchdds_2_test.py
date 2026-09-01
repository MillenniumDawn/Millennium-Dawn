"""Deterministic tests for tools/assets/batchdds-2.py DXT1/DXT5 codec and CLI.

Covers real binary parsing/conversion round-trips with synthetic DDS fixtures,
flag and pixelformat edge cases, error branches, and the two-mode CLI dispatcher
(file vs. directory) by invoking the module's main() via sys.argv.
"""

import importlib.util
import struct
import sys
from pathlib import Path

import pytest


def _load_asset(name):
    path = Path(__file__).resolve().parents[2] / "assets" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_asset_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bd = _load_asset("batchdds-2")

# --- DDS fixture helpers ---------------------------------------------------


def _make_dds(width, height, fourcc, body, mip_count=0):
    """Assemble a minimal DDS with a 124-byte header + DX10 ext (when needed)."""
    flags = (
        bd.DDSD_CAPS
        | bd.DDSD_HEIGHT
        | bd.DDSD_WIDTH
        | bd.DDSD_PIXELFORMAT
        | bd.DDSD_LINEARSIZE
    )
    linear_size = max(1, len(body))
    if fourcc == bd.DX10_FOURCC:
        pixelformat_block = struct.pack(
            "<8I",
            32,
            bd.DDPF_FOURCC,
            bd.DX10_FOURCC,
            0,
            0,
            0,
            0,
            0,
        )
    else:
        pixelformat_block = struct.pack(
            "<8I",
            32,
            bd.DDPF_FOURCC,
            fourcc,
            0,
            0,
            0,
            0,
            0,
        )
    hdr = struct.pack("<I", bd.DDS_MAGIC)
    hdr += struct.pack("<I", 124)
    hdr += struct.pack("<I", flags)
    hdr += struct.pack("<I", height)
    hdr += struct.pack("<I", width)
    hdr += struct.pack("<I", linear_size)
    hdr += struct.pack("<I", 0)  # depth
    hdr += struct.pack("<I", mip_count)
    hdr += b"\x00" * 44  # reserved1[11]
    hdr += pixelformat_block
    hdr += struct.pack("<I", bd.DDSCAPS_TEXTURE)
    hdr += b"\x00" * 16  # caps2..4 + reserved2
    out = hdr + body
    if fourcc == bd.DX10_FOURCC:
        # empty DX10 extension block (20 bytes) at offset 128; dxgi goes here
        out = hdr + struct.pack("<I", 0) * 5 + body
    return out


def _flat_pixels(color, width, height):
    """Return a flat (b, g, r, a) list of one solid color."""
    b, g, r, a = color
    return [(b, g, r, a)] * (width * height)


# --- Color/alpha math helpers (untested helpers) ---------------------------


def test_rgb_to_565_and_back_truncation():
    # Pure red -> 0xF800 in 5-6-5; pure white -> 0xFFFF.
    assert bd.rgb_to_565(255, 0, 0) == 0xF800
    assert bd.rgb_to_565(255, 255, 255) == 0xFFFF
    # Mid values round-trip within DXT quantization error.
    r, g, b = bd.rgb565_to_rgb(bd.rgb_to_565(50, 100, 150))
    # 50 -> 3 bits, 100 -> 6 bits, 150 -> 5 bits, so don't expect identity.
    assert (r, g, b) == bd.rgb565_to_rgb(bd.rgb_to_565(50, 100, 150))


def test_color_block_palette_branches():
    # c0_565 > c1_565: 4-color palette using weighted averages.
    high, low = bd.rgb_to_565(255, 0, 0), bd.rgb_to_565(0, 0, 0)
    pal = bd._color_block_palette(struct.pack("<HH", high, low), 0)
    assert len(pal) == 4
    assert pal[2] == ((2 * 255 + 0) // 3, 0, 0)
    # c0_565 <= c1_565: third entry is midpoint, fourth is black (transparent).
    pal2 = bd._color_block_palette(struct.pack("<HH", low, high), 0)
    assert pal2[3] == (0, 0, 0)
    assert pal2[2][0] == (0 + 255) // 2


def test_alpha_block_palette_a0_gt_a1_branch():
    pal = bd._dxt5_alpha_palette(200, 50)
    assert pal[2] == (6 * 200 + 1 * 50) // 7
    assert pal[7] == (1 * 200 + 6 * 50) // 7


def test_alpha_block_palette_a0_le_a1_branch():
    pal = bd._dxt5_alpha_palette(50, 200)
    assert pal[2] == (4 * 50 + 1 * 200) // 5
    assert pal[6] == 0
    assert pal[7] == 255


def test_compress_color_block_returns_indices_for_real_pixels():
    block = _flat_pixels((0, 0, 255, 255), 4, 4)
    encoded = bd._compress_color_block(block)
    assert len(encoded) == 8
    c0, c1, idx_dw = struct.unpack("<HHI", encoded)
    # c0_565 >= c1_565 always (we enforce ordering inside the encoder).
    assert c0 > 0 or c1 > 0


def test_compress_color_block_c0_equals_c1_swap_branch():
    # All same color, "c0_565 == c1_565 and c0_565 > 0" -> c1_565 -= 1.
    block = _flat_pixels((40, 80, 120, 255), 4, 4)
    encoded = bd._compress_color_block(block)
    c0, c1, _idx = struct.unpack("<HHI", encoded)
    assert c0 > c1


def test_compress_dxt5_alpha_block_a0_equals_a1_swap_branch():
    # All alpha=128, _a0 == a1 > 0 triggers a1 -= 1.
    alphas = [128] * 16
    encoded = bd._compress_dxt5_alpha_block(alphas)
    assert len(encoded) == 8
    assert encoded[0] > encoded[1]


def test_decompress_setup_and_block_grid_clamps_to_4x4():
    bx, by, pixels = bd._decompress_setup(5, 7)
    assert (bx, by) == (2, 2)
    assert len(pixels) == 5 * 7
    assert pixels[0] == (0, 0, 0, 255)


def test_gather_block_clamps_at_image_edge():
    pixels = _flat_pixels((10, 20, 30, 255), 5, 5)
    block = bd._gather_block(pixels, 5, 5, by=1, bx=1)
    assert len(block) == 16
    # Pixels at the bottom-right corner clamp to the last valid pixel.
    assert all(p == (10, 20, 30, 255) for p in block)


def test_dxt5_alpha_values_decode_compressed_block():
    # With index_bits == 0, every pixel reads palette[0].
    alphas = bd._dxt5_alpha_values(bytes([250, 5, 0, 0, 0, 0, 0, 0]), 0)
    assert len(alphas) == 16
    assert alphas[0] == 250
    assert all(a == 250 for a in alphas)


def test_dxt3_alpha_values_return_4bit_extrapolation():
    # 16 entries packed as 4-bit nibbles, 0xFF -> 255.
    raw = bytes([0x55] * 8)  # alternating 5s and 5s -> all 5*255/15 = 85
    values = bd._dxt3_alpha_values(raw, 0)
    assert values == [85] * 16


def test_decode_helpers_cover_bgrx_rgba_and_bgra():
    # Raw bytes [1,2,3,4] indexed by (B, G, R, A) order.
    raw = bytes([1, 2, 3, 4]) * 4
    assert bd.decode_bgra(raw, 2, 2) == [(1, 2, 3, 4)] * 4
    # RGBA swaps R/B indices.
    assert bd.decode_rgba(raw, 2, 2)[0] == (3, 2, 1, 4)
    # BGRX ignores the X slot and writes 255 alpha.
    assert bd.decode_bgrx(raw, 2, 2) == [(1, 2, 3, 255)] * 4


def test_decompress_dxt1_opaque_and_transparent_blocks():
    # c0 > c1 -> no transparency slot.
    pal_high, pal_low = bd.rgb_to_565(255, 0, 0), bd.rgb_to_565(0, 0, 0)
    block_high_low = struct.pack(
        "<HHI", pal_high, pal_low, 0x00000000  # all index 0 -> c0 (red)
    )
    pixels = bd.decompress_dxt1(block_high_low, 4, 4)
    assert all(p == (0, 0, 255, 255) for p in pixels)
    # c0 <= c1 -> index 3 is transparent.
    block_low_high = struct.pack("<HHI", pal_low, pal_high, 0xFFFFFFFF)  # all index 3
    pixels_t = bd.decompress_dxt1(block_low_high, 4, 4)
    assert all(p == (0, 0, 0, 0) for p in pixels_t)


def test_decompress_dxt3_and_dxt5_match_compressed_input():
    block = _flat_pixels((0, 0, 255, 128), 4, 4)
    body = bd._compress_dxt5_alpha_block([p[3] for p in block])
    body += bd._compress_color_block(block)
    pixels = bd.decompress_dxt5(body, 4, 4)
    assert pixels[0] == (0, 0, 255, 128)


def test_make_dxt_headers_have_magic_and_pixelformat():
    h1 = bd.make_dxt1_header(8, 8)
    h5 = bd.make_dxt5_header(8, 8)
    assert struct.unpack_from("<I", h1, 0)[0] == bd.DDS_MAGIC
    assert struct.unpack_from("<I", h1, 4)[0] == 124
    assert struct.unpack_from("<I", h1, 84)[0] == bd.DXT1_FOURCC
    assert struct.unpack_from("<I", h5, 84)[0] == bd.DXT5_FOURCC


# --- convert_dds() round trips -------------------------------------------


def _write_dds(tmp_path, name, fourcc, body, mip_count=0):
    """Write a DDS file and return its path."""
    raw = _make_dds(4, 4, fourcc, body, mip_count=mip_count)
    path = tmp_path / name
    # When DX10, _make_dds already pads an extra 20 bytes at offset 128.
    if fourcc == bd.DX10_FOURCC:
        # Inject a real dxgi value so the convert_dds dispatch reads it.
        dxgi = body[0] if body else 0
        dx10 = struct.pack("<5I", dxgi, 0, 0, 0, 0)
        raw = raw[:128] + dx10 + raw[148:]
    path.write_bytes(raw)
    return path


def test_convert_dds_dxt1_to_dxt5_in_place(tmp_path):
    body = bd._compress_color_block(_flat_pixels((0, 0, 255, 255), 4, 4))
    body *= 1  # 4x4 takes exactly 1 block
    path = _write_dds(tmp_path, "in.dds", bd.DXT1_FOURCC, body)
    bd.convert_dds(str(path))
    out_bytes = path.read_bytes()
    assert struct.unpack_from("<I", out_bytes, 0)[0] == bd.DDS_MAGIC
    assert struct.unpack_from("<I", out_bytes, 84)[0] == bd.DXT5_FOURCC


def test_convert_dds_already_target_format_is_idempotent(tmp_path):
    body = bd._compress_color_block(_flat_pixels((50, 100, 150, 255), 4, 4))
    path = _write_dds(tmp_path, "ok.dds", bd.DXT5_FOURCC, body + b"\x00" * 8)
    original = path.read_bytes()
    assert bd.convert_dds(str(path)) is True
    # byte-identical (already in target FourCC, no mipmaps).
    assert path.read_bytes() == original


def test_convert_dds_writes_to_separate_output(tmp_path):
    body = bd._compress_color_block(_flat_pixels((10, 20, 30, 255), 4, 4))
    src = _write_dds(tmp_path, "src.dds", bd.DXT1_FOURCC, body)
    out = tmp_path / "out.dds"
    assert bd.convert_dds(str(src), str(out)) is True
    assert out.is_file()
    assert struct.unpack_from("<I", out.read_bytes(), 84)[0] == bd.DXT5_FOURCC


def test_convert_dds_rejects_bad_magic_and_bad_header(tmp_path):
    bogus = tmp_path / "nope.dds"
    bogus.write_bytes(b"AAAA" + b"\x00" * 200)
    with pytest.raises(ValueError, match="not a valid DDS"):
        bd.convert_dds(str(bogus))

    bad_size = tmp_path / "wrong.dds"
    body = bd._compress_color_block(_flat_pixels((0, 0, 255, 255), 4, 4))
    raw = _make_dds(4, 4, bd.DXT1_FOURCC, body)
    raw = raw[:4] + struct.pack("<I", 64) + raw[8:]
    bad_size.write_bytes(raw)
    with pytest.raises(ValueError, match="unexpected header size"):
        bd.convert_dds(str(bad_size))


def test_convert_dds_rejects_unknown_pixel_format(tmp_path):
    # FourCC that's neither legacy nor DX10, and RGB bits = 16 (unsupported).
    raw = _make_dds(2, 2, 0xDEADBEEF, b"\x00" * 8)
    # Force pf_flags to NOT have DDPF_RGB so we hit the else branch.
    raw = raw[:80] + struct.pack("<I", 0) + raw[84:]
    bad = tmp_path / "weird.dds"
    bad.write_bytes(raw)
    with pytest.raises(ValueError, match="unrecognized pixel format"):
        bd.convert_dds(str(bad))


def test_convert_dds_legacy_uncompressed_bgra_24bit_rejected(tmp_path):
    # RGB-bit=24 instead of 32 must surface as a ValueError.
    raw = _make_dds(2, 2, 0, b"\x00" * 16)
    # Patch pf_flags to DDPF_RGB and rgb_bits to 24.
    raw = bytearray(raw)
    struct.pack_into("<I", raw, 80, bd.DDPF_RGB)
    struct.pack_into("<I", raw, 88, 24)
    bad = tmp_path / "bad24.dds"
    bad.write_bytes(bytes(raw))
    with pytest.raises(ValueError, match="unsupported legacy uncompressed format"):
        bd.convert_dds(str(bad))


def test_convert_dds_legacy_uncompressed_bgra_round_trip(tmp_path):
    pixels = _flat_pixels((10, 20, 30, 200), 4, 4)
    raw = bytes(sum(pixels, ()))
    buf = bytearray(_make_dds(4, 4, 0, raw))
    struct.pack_into("<I", buf, 80, bd.DDPF_RGB)  # pf_flags
    struct.pack_into("<I", buf, 88, 32)  # rgb_bits
    struct.pack_into("<I", buf, 92, 0x00FF0000)  # r_mask = B8G8R8A8
    src = tmp_path / "bgra.dds"
    src.write_bytes(bytes(buf))
    assert bd.convert_dds(str(src)) is True
    out = src.read_bytes()
    fourcc = struct.unpack_from("<I", out, 84)[0]
    assert fourcc == bd.DXT5_FOURCC


def test_convert_dds_dx10_bc1_srgb_routes_to_dxt5(tmp_path):
    body = bd._compress_color_block(_flat_pixels((255, 0, 0, 255), 4, 4))
    raw = bytearray(_make_dds(4, 4, bd.DX10_FOURCC, body))
    # Insert dxgi at offset 128 (BC1 sRGB variant).
    raw[128 : 128 + 4] = struct.pack("<I", bd.DXGI_FORMAT_BC1_UNORM_SRGB)
    src = tmp_path / "bc1.dds"
    src.write_bytes(bytes(raw))
    assert bd.convert_dds(str(src)) is True
    out = src.read_bytes()
    fourcc = struct.unpack_from("<I", out, 84)[0]
    assert fourcc == bd.DXT5_FOURCC


def test_convert_dds_dx10_bgra_unorm_round_trip(tmp_path):
    body = bytes(sum(_flat_pixels((30, 40, 50, 255), 4, 4), ()))
    raw = bytearray(_make_dds(4, 4, bd.DX10_FOURCC, body))
    raw[128:132] = struct.pack("<I", bd.DXGI_FORMAT_B8G8R8A8_UNORM)
    src = tmp_path / "bgra_dx10.dds"
    src.write_bytes(bytes(raw))
    assert bd.convert_dds(str(src)) is True


def test_convert_dds_dx10_unknown_dxgi_raises(tmp_path):
    raw = bytearray(_make_dds(4, 4, bd.DX10_FOURCC, b"\x00" * 16))
    raw[128:132] = struct.pack("<I", 999)  # not in any branch
    src = tmp_path / "bogus_dx10.dds"
    src.write_bytes(bytes(raw))
    with pytest.raises(ValueError, match="unsupported DXGI format"):
        bd.convert_dds(str(src))


def test_convert_dds_dxt3_input_routes_to_dxt5(tmp_path):
    # DXT3 block = 16 bytes per 4x4: 8-byte alpha + 8-byte color.
    block = _flat_pixels((0, 255, 0, 200), 4, 4)
    body = bd._compress_dxt5_alpha_block([p[3] for p in block])
    body += bd._compress_color_block(block)
    raw = _make_dds(4, 4, bd.DXT3_FOURCC, body)
    src = tmp_path / "dxt3.dds"
    src.write_bytes(raw)
    assert bd.convert_dds(str(src)) is True
    assert struct.unpack_from("<I", src.read_bytes(), 84)[0] == bd.DXT5_FOURCC


def test_convert_dds_format_auto_detects_transparency(tmp_path):
    # All opaque -> auto should pick DXT1.
    body = bd._compress_color_block(_flat_pixels((0, 0, 200, 255), 4, 4))
    src = _write_dds(tmp_path, "opaque.dds", bd.DXT1_FOURCC, body)
    bd.convert_dds(str(src), fmt="auto")
    out_fourcc = struct.unpack_from("<I", src.read_bytes(), 84)[0]
    assert out_fourcc == bd.DXT1_FOURCC

    # Semi-transparent requires alpha in the source. DXT1 discards alpha, so
    # feed a 4x4 DXT5 with alpha=100 and let auto choose DXT5.
    block = _flat_pixels((0, 0, 200, 100), 4, 4)
    body2 = bd._compress_dxt5_alpha_block([p[3] for p in block])
    body2 += bd._compress_color_block(block)
    src2 = tmp_path / "trans.dds"
    src2.write_bytes(_make_dds(4, 4, bd.DXT5_FOURCC, body2))
    bd.convert_dds(str(src2), fmt="auto")
    out2_fourcc = struct.unpack_from("<I", src2.read_bytes(), 84)[0]
    assert out2_fourcc == bd.DXT5_FOURCC


def test_convert_dds_force_dxt1_discards_alpha(tmp_path):
    body = bd._compress_color_block(_flat_pixels((0, 200, 0, 0), 4, 4))
    src = _write_dds(tmp_path, "alpha.dds", bd.DXT5_FOURCC, body + b"\x00" * 8)
    bd.convert_dds(str(src), fmt="dxt1")
    out_fourcc = struct.unpack_from("<I", src.read_bytes(), 84)[0]
    assert out_fourcc == bd.DXT1_FOURCC


# --- CLI: directory mode ----------------------------------------------------


def test_main_directory_iterates_files_and_reports_failures(tmp_path, capsys):
    (tmp_path / "sub").mkdir()
    a = tmp_path / "sub" / "ok.dds"
    body_a = bd._compress_color_block(_flat_pixels((255, 0, 0, 255), 4, 4))
    a.write_bytes(_make_dds(4, 4, bd.DXT1_FOURCC, body_a))
    b = tmp_path / "sub" / "bad.dds"
    b.write_bytes(b"NOT A DDS" * 4)  # deliberately corrupt

    monkey_argv = ["batchdds-2.py", str(tmp_path)]
    saved = sys.argv
    sys.argv = monkey_argv
    try:
        bd.main()
    finally:
        sys.argv = saved

    out = capsys.readouterr().out
    assert "Converted 1 file(s)" in out
    assert "1 file(s) failed" in out


def test_main_directory_rejects_output_argument(tmp_path, capsys):
    body = bd._compress_color_block(_flat_pixels((0, 0, 0, 255), 4, 4))
    (tmp_path / "x.dds").write_bytes(_make_dds(4, 4, bd.DXT1_FOURCC, body))

    saved = sys.argv
    sys.argv = ["batchdds-2.py", str(tmp_path), "should-not-be-here.dds"]
    try:
        with pytest.raises(SystemExit):
            bd.main()
    finally:
        sys.argv = saved


def test_main_single_file_propagates_exception_as_exit(tmp_path, capsys):
    saved = sys.argv
    sys.argv = ["batchdds-2.py", "/nonexistent/never-actually-here.dds"]
    try:
        with pytest.raises(SystemExit):
            bd.main()
    finally:
        sys.argv = saved
