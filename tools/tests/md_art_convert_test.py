"""Covers the byte-level TGA rewrite in tools/assets/md_art_convert.py.

The conversion subcommands shell out to ImageMagick and are not exercised
here; `tga_normalised` is pure and is the part that must never corrupt a
shipped flag, so it carries the tests.
"""

import struct

from md_art_convert import TGA_HEADER, tga_normalised


def _tga(
    rows: list[bytes],
    *,
    width: int,
    bpp: int,
    descriptor: int,
    datatype: int = 2,
    id_field: bytes = b"",
    palette: bytes = b"",
    cmap_length: int = 0,
    cmap_depth: int = 0,
    trailer: bytes = b"",
) -> bytes:
    header = TGA_HEADER.pack(
        len(id_field),
        1 if cmap_length else 0,
        datatype,
        0,
        cmap_length,
        cmap_depth,
        0,
        0,
        width,
        len(rows),
        bpp,
        descriptor,
    )
    return header + id_field + palette + b"".join(rows) + trailer


def _rows(data: bytes) -> list[bytes]:
    idlength, _, _, _, cmap_length, cmap_depth, _, _, width, height, bpp, _ = (
        TGA_HEADER.unpack_from(data, 0)
    )
    start = TGA_HEADER.size + idlength + cmap_length * (cmap_depth // 8)
    stride = width * (bpp // 8)
    return [data[start + i * stride : start + (i + 1) * stride] for i in range(height)]


def test_top_left_rows_are_reversed_and_the_origin_bit_cleared():
    rows = [b"\x01\x01\x01\x01", b"\x02\x02\x02\x02", b"\x03\x03\x03\x03"]
    out = tga_normalised(_tga(rows, width=1, bpp=32, descriptor=0x28))

    assert out is not None
    assert out[17] == 0x08
    assert _rows(out) == list(reversed(rows))
    assert len(out) == len(_tga(rows, width=1, bpp=32, descriptor=0x28))


def test_bottom_left_is_left_alone():
    rows = [b"\x01\x01\x01\x01", b"\x02\x02\x02\x02"]
    assert tga_normalised(_tga(rows, width=1, bpp=32, descriptor=0x08)) is None


def test_twenty_four_bit_keeps_its_depth_and_clears_only_the_origin_bit():
    rows = [b"\x01\x02\x03", b"\x04\x05\x06"]
    out = tga_normalised(_tga(rows, width=1, bpp=24, descriptor=0x20))

    assert out is not None
    assert out[16] == 24
    assert out[17] == 0x00
    assert _rows(out) == list(reversed(rows))


def test_colour_mapped_rows_flip_without_disturbing_the_palette():
    palette = bytes(range(12))
    rows = [b"\x00", b"\x01", b"\x02"]
    out = tga_normalised(
        _tga(
            rows,
            width=1,
            bpp=8,
            descriptor=0x20,
            datatype=1,
            palette=palette,
            cmap_length=4,
            cmap_depth=24,
        )
    )

    assert out is not None
    assert out[TGA_HEADER.size : TGA_HEADER.size + len(palette)] == palette
    assert _rows(out) == list(reversed(rows))


def test_id_field_and_footer_survive():
    rows = [b"\x01\x01\x01\x01", b"\x02\x02\x02\x02"]
    footer = b"TRUEVISION-XFILE.\x00"
    out = tga_normalised(
        _tga(rows, width=1, bpp=32, descriptor=0x28, id_field=b"note", trailer=footer)
    )

    assert out is not None
    assert out[TGA_HEADER.size : TGA_HEADER.size + 4] == b"note"
    assert out.endswith(footer)


def test_rle_is_refused_rather_than_scrambled():
    payload = b"\x82\x01\x02\x03\x04"
    data = struct.pack("<BBBHHBHHHHBB", 0, 0, 10, 0, 0, 0, 0, 0, 2, 2, 32, 0x28)
    assert tga_normalised(data + payload) is None


def test_truncated_pixel_data_is_refused():
    header = TGA_HEADER.pack(0, 0, 2, 0, 0, 0, 0, 0, 4, 4, 32, 0x28)
    assert tga_normalised(header + b"\x00" * 8) is None


def test_header_shorter_than_a_tga_is_refused():
    assert tga_normalised(b"\x00\x00\x02") is None
