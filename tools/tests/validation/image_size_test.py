"""Header parsing in image_size.read_image_size.

Every referenced texture is measured through this helper. An unreadable,
truncated or malformed file has to read as None: a bogus size would put a
decision icon in the wrong slot band instead of skipping it.
"""

import struct

import pytest
from image_size import read_image_size
from shared.suite import dds_stub

_PNG = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13)
_PNG_SIZE = struct.pack(">II", 114, 101) + b"\x08\x06\x00\x00\x00"


def _tga(width, height, *, colour_map=0, image_type=2):
    header = bytearray(32)
    header[1] = colour_map
    header[2] = image_type
    struct.pack_into("<HH", header, 12, width, height)
    return bytes(header)


# case: (file name, payload, size read)
_CASES = {
    "dds": ("icon.dds", dds_stub(52, 40), (52, 40)),
    "png": ("icon.png", _PNG + b"IHDR" + _PNG_SIZE, (114, 101)),
    "uncompressed tga": ("icon.tga", _tga(96, 64), (96, 64)),
    "RLE tga with a colour map": (
        "rle.tga",
        _tga(24, 18, colour_map=1, image_type=9),
        (24, 18),
    ),
    "tga with an unknown image type": ("odd.tga", _tga(96, 64, image_type=7), None),
    "tga with an unknown colour map byte": (
        "odd2.tga",
        _tga(96, 64, colour_map=5),
        None,
    ),
    "unknown format": ("icon.dds", b"not an image, but long enough to read", None),
    "truncated header": ("short.dds", b"DDS " + b"\x00" * 8, None),
    "png without an IHDR chunk": ("odd.png", _PNG + b"iCCP" + b"\x00" * 16, None),
    "zero-sized dds": ("empty.dds", dds_stub(40, 0), None),
    "missing file": ("never_written.dds", None, None),
}


@pytest.mark.parametrize(("name", "payload", "size"), _CASES.values(), ids=_CASES)
def test_read_image_size(tmp_path, name, payload, size):
    path = tmp_path / name
    if payload is not None:
        path.write_bytes(payload)

    assert read_image_size(str(path)) == size
