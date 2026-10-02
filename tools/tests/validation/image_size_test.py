"""Header-parsing edge cases for image_size.read_image_size.

Every referenced texture is measured through this helper, so an unreadable,
truncated or malformed file has to read as None — a bogus size would put a
decision icon in the wrong slot band instead of skipping it.
"""

import struct

from image_size import read_image_size


def _write(path, payload):
    with open(path, "wb") as fh:
        fh.write(payload)
    return str(path)


def _tga(width, height, *, colour_map=0, image_type=2):
    header = bytearray(32)
    header[1] = colour_map
    header[2] = image_type
    struct.pack_into("<HH", header, 12, width, height)
    return bytes(header)


def test_uncompressed_tga_size_is_read(tmp_path):
    assert read_image_size(_write(tmp_path / "icon.tga", _tga(96, 64))) == (96, 64)


def test_rle_tga_with_colour_map_is_read(tmp_path):
    payload = _tga(24, 18, colour_map=1, image_type=9)
    assert read_image_size(_write(tmp_path / "rle.tga", payload)) == (24, 18)


def test_tga_with_unknown_image_type_is_rejected(tmp_path):
    payload = _tga(96, 64, image_type=7)
    assert read_image_size(_write(tmp_path / "odd.tga", payload)) is None


def test_tga_with_unknown_colour_map_byte_is_rejected(tmp_path):
    payload = _tga(96, 64, colour_map=5)
    assert read_image_size(_write(tmp_path / "odd2.tga", payload)) is None


def test_missing_file_is_none(tmp_path):
    assert read_image_size(str(tmp_path / "never_written.dds")) is None


def test_truncated_header_is_none(tmp_path):
    assert (
        read_image_size(_write(tmp_path / "short.dds", b"DDS " + b"\x00" * 8)) is None
    )


def test_png_without_ihdr_chunk_is_none(tmp_path):
    payload = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"iCCP" + b"\x00" * 16
    assert read_image_size(_write(tmp_path / "odd.png", payload)) is None


def test_zero_sized_dds_is_none(tmp_path):
    header = bytearray(128)
    header[0:4] = b"DDS "
    struct.pack_into("<II", header, 12, 0, 40)
    assert read_image_size(_write(tmp_path / "empty.dds", bytes(header))) is None
