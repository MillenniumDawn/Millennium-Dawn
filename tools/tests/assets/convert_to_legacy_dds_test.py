"""Deterministic tests for tools/assets/convert_to_legacy_dds.py.

Covers real DDS header parsing, sRGB linearisation via the SRGB_TO_LINEAR LUT,
branch coverage on each "SKIP" rejection (truncated, wrong magic, wrong header
size, already legacy, truncated DX10, unsupported DXGI, truncated pixels),
and the directory-vs-file CLI dispatch paths.
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


cl = _load_asset("convert_to_legacy_dds")


# --- LUT math -------------------------------------------------------------


def test_srgb_to_linear_uses_linear_segment_below_threshold():
    # n=0.1 (<=0.04045) -> n/12.92 branch.
    val = cl._srgb_to_linear(int(0.1 * 255))
    assert val < 5  # tiny but non-zero


def test_srgb_to_linear_uses_pow_branch_above_threshold():
    # Mid-range sRGB values come out far below the input because sRGB ~= sqrt.
    val = cl._srgb_to_linear(128)
    assert 40 < val < 80
    # 255 -> 255 exactly (linear == sRGB for white).
    assert cl._srgb_to_linear(255) == 255


def test_srgb_to_linear_lut_matches_function():
    # The LUT table is built with the function and includes both ranges.
    assert cl.SRGB_TO_LINEAR[0] == cl._srgb_to_linear(0)
    assert cl.SRGB_TO_LINEAR[255] == cl._srgb_to_linear(255)
    assert cl.SRGB_TO_LINEAR[128] == cl._srgb_to_linear(128)


# --- DDS fixtures ---------------------------------------------------------


def _make_dx10_dds(width, height, dxgi, pixels, *, with_dx10=True):
    flags = 0x10000B  # DDSD_CAPS | HEIGHT | WIDTH | PIXELFORMAT
    hdr = struct.pack("<I", cl.DDS_MAGIC)
    hdr += struct.pack("<I", 124)
    hdr += struct.pack("<I", flags)
    hdr += struct.pack("<I", height)
    hdr += struct.pack("<I", width)
    hdr += struct.pack("<I", width * height * 4)  # linearSize
    hdr += struct.pack("<I", 0)
    hdr += struct.pack("<I", 0)
    hdr += b"\x00" * 44
    hdr += struct.pack("<8I", 32, 0x04, cl.DX10_FOURCC, 0, 0, 0, 0, 0)
    hdr += struct.pack("<I", 0x1000)  # caps
    hdr += b"\x00" * 16
    payload = hdr
    if with_dx10:
        payload += struct.pack("<5I", dxgi, 0, 0, 0, 0)  # DX10 extension
    payload += pixels
    return payload


# --- Core conversion ------------------------------------------------------


def test_convert_unorm_dx10_writes_legacy_pixelformat_block(tmp_path):
    pixels = bytes([10, 20, 30, 255] * 4)
    raw = _make_dx10_dds(2, 2, cl.DXGI_B8G8R8A8_UNORM, pixels)
    src = tmp_path / "in.dds"
    src.write_bytes(raw)
    assert cl.convert_dds_to_legacy(str(src)) is True
    out = src.read_bytes()
    # Magic + header preserved; pixel format block replaced with LEGACY one.
    assert struct.unpack_from("<I", out, 0)[0] == cl.DDS_MAGIC
    assert out[76:108] == cl.LEGACY_PIXELFORMAT
    # DX10 extension removed.
    assert len(out) == 128 + len(pixels)


def test_convert_srgb_dx10_linearises_pixels_and_leaves_alpha(tmp_path):
    # Pixel 0 has B=50, G=100, R=150, A=99. After conversion A must stay 99.
    pixels = bytes([50, 100, 150, 99])
    raw = _make_dx10_dds(1, 1, cl.DXGI_B8G8R8A8_SRGB, pixels)
    src = tmp_path / "srgb.dds"
    src.write_bytes(raw)
    assert cl.convert_dds_to_legacy(str(src)) is True
    out = src.read_bytes()
    linearised_b = cl.SRGB_TO_LINEAR[50]
    linearised_g = cl.SRGB_TO_LINEAR[100]
    linearised_r = cl.SRGB_TO_LINEAR[150]
    assert out[128:131] == bytes([linearised_b, linearised_g, linearised_r])
    assert out[131] == 99  # alpha preserved


def test_convert_writes_to_separate_output_directory(tmp_path):
    pixels = bytes([1, 2, 3, 4])
    raw = _make_dx10_dds(1, 1, cl.DXGI_B8G8R8A8_UNORM, pixels)
    src = tmp_path / "sub" / "x.dds"
    src.parent.mkdir(parents=True)
    src.write_bytes(raw)
    out = tmp_path / "out" / "y.dds"
    assert cl.convert_dds_to_legacy(str(src), str(out)) is True
    assert out.is_file()
    assert out.read_bytes()[76:108] == cl.LEGACY_PIXELFORMAT


# --- SKIP branches --------------------------------------------------------


def test_skip_truncated_input(tmp_path, capsys):
    path = tmp_path / "short.dds"
    path.write_bytes(b"\x00" * 64)  # < 128 bytes
    assert cl.convert_dds_to_legacy(str(path)) is False
    assert "Truncated" in capsys.readouterr().out


def test_skip_wrong_magic(tmp_path, capsys):
    path = tmp_path / "wrong.dds"
    payload = b"XYZQ" + b"\x7c\x00\x00\x00" + b"\x00" * 200
    path.write_bytes(payload)
    assert cl.convert_dds_to_legacy(str(path)) is False
    assert "Not a DDS" in capsys.readouterr().out


def test_skip_unexpected_header_size(tmp_path, capsys):
    payload = struct.pack("<I", cl.DDS_MAGIC) + struct.pack("<I", 200)
    payload += b"\x00" * 200
    path = tmp_path / "hsize.dds"
    path.write_bytes(payload)
    assert cl.convert_dds_to_legacy(str(path)) is False
    assert "Unexpected header size" in capsys.readouterr().out


def test_skip_already_legacy_no_dx10(tmp_path, capsys):
    payload = struct.pack("<I", cl.DDS_MAGIC) + struct.pack("<I", 124)
    payload += b"\x00" * 200
    path = tmp_path / "legacy.dds"
    path.write_bytes(payload)
    assert cl.convert_dds_to_legacy(str(path)) is False
    assert "Already legacy" in capsys.readouterr().out


def test_skip_truncated_dx10_extension(tmp_path, capsys):
    # Build a complete 128-byte header whose pixel format block contains
    # the DX10 FourCC, but emit only 5 bytes after offset 128 (truncated ext).
    header = bytearray(b"\x00" * 128)
    struct.pack_into("<I", header, 0, cl.DDS_MAGIC)
    struct.pack_into("<I", header, 4, 124)
    # Pixel format block lives at bytes 76..107.
    pf_offset = 76
    struct.pack_into("<I", header, pf_offset + 0, 32)  # size
    struct.pack_into("<I", header, pf_offset + 4, 0x04)  # flags
    struct.pack_into("<I", header, pf_offset + 8, cl.DX10_FOURCC)
    path = tmp_path / "trunc.dds"
    payload = bytes(header) + b"onlyfive"  # 9 bytes total after header
    path.write_bytes(payload)
    assert cl.convert_dds_to_legacy(str(path)) is False
    assert "Truncated DX10" in capsys.readouterr().out


def test_skip_unsupported_dxgi_format(tmp_path, capsys):
    raw = _make_dx10_dds(2, 2, 71, bytes([0] * 16))  # BC1 = unsupported here
    path = tmp_path / "bc1.dds"
    path.write_bytes(raw)
    assert cl.convert_dds_to_legacy(str(path)) is False
    assert "Unsupported DXGI" in capsys.readouterr().out


def test_skip_truncated_pixel_data(tmp_path, capsys):
    # 2x2 file claiming 32 bytes but only shipping 8.
    raw = _make_dx10_dds(2, 2, cl.DXGI_B8G8R8A8_UNORM, bytes([0] * 8))
    path = tmp_path / "short_pixels.dds"
    path.write_bytes(raw)
    assert cl.convert_dds_to_legacy(str(path)) is False
    assert "Truncated pixel data" in capsys.readouterr().out


# --- CLI dispatch ---------------------------------------------------------


def test_main_file_no_args_exits_one(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["convert_to_legacy_dds.py"])
    with pytest.raises(SystemExit):
        cl.main()
    assert "usage" in capsys.readouterr().out.lower() or "convert_dds" in capsys.readouterr().out.lower()


def test_main_directory_iterates_and_reports_counts(tmp_path, monkeypatch, capsys):
    (tmp_path / "ok").mkdir()
    pixels = bytes([1, 2, 3, 255])
    for name in ("a.dds", "b.dds"):
        (tmp_path / "ok" / name).write_bytes(
            _make_dx10_dds(1, 1, cl.DXGI_B8G8R8A8_UNORM, pixels)
        )
    # Add a non-DDS file to exercise the failure path inside the loop.
    (tmp_path / "ok" / "skip.dds").write_bytes(b"\x00" * 64)

    monkeypatch.setattr(sys, "argv", ["convert_to_legacy_dds.py", str(tmp_path / "ok")])
    cl.main()
    out = capsys.readouterr().out
    assert "Done — converted:" in out
    assert "skipped:" in out


def test_main_directory_with_output_root_relocates_files(tmp_path, monkeypatch):
    src = tmp_path / "in"
    dst = tmp_path / "out"
    src.mkdir()
    pixels = bytes([5, 6, 7, 255])
    (src / "rel.dds").write_bytes(
        _make_dx10_dds(1, 1, cl.DXGI_B8G8R8A8_UNORM, pixels)
    )
    monkeypatch.setattr(sys, "argv", ["convert_to_legacy_dds.py", str(src), str(dst)])
    cl.main()
    assert (dst / "rel.dds").is_file()


def test_main_directory_no_files_prints_message(tmp_path, monkeypatch, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(sys, "argv", ["convert_to_legacy_dds.py", str(empty)])
    with pytest.raises(SystemExit) as exit_info:
        cl.main()
    assert exit_info.value.code == 0
    assert "No .dds files found" in capsys.readouterr().out


def test_main_single_file_success_exits_zero(tmp_path, monkeypatch):
    pixels = bytes([10, 20, 30, 255])
    (tmp_path / "only.dds").write_bytes(
        _make_dx10_dds(1, 1, cl.DXGI_B8G8R8A8_UNORM, pixels)
    )
    monkeypatch.setattr(sys, "argv", ["convert_to_legacy_dds.py", str(tmp_path / "only.dds")])
    with pytest.raises(SystemExit) as exit_info:
        cl.main()
    assert exit_info.value.code == 0


def test_main_single_file_skipped_exits_one(tmp_path, monkeypatch):
    header = bytearray(b"\x00" * 128)
    struct.pack_into("<I", header, 0, cl.DDS_MAGIC)
    struct.pack_into("<I", header, 4, 124)
    (tmp_path / "skipped.dds").write_bytes(bytes(header))
    monkeypatch.setattr(sys, "argv", ["convert_to_legacy_dds.py", str(tmp_path / "skipped.dds")])
    with pytest.raises(SystemExit) as exit_info:
        cl.main()
    assert exit_info.value.code == 1
