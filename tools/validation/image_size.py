"""Read image dimensions from file headers, stdlib only.

Validators that care about how big a sprite renders need the texture's pixel
size, and the header is enough — decoding the pixel data is wasted work and
would drag Pillow into CI, which installs the dev group only. DDS, TGA and PNG
cover every ``texturefile`` in the mod.
"""

import struct
from typing import Optional, Tuple

_DDS_MAGIC = b"DDS "
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def read_image_size(path: str) -> Optional[Tuple[int, int]]:
    """Return ``(width, height)`` for *path*, or None when it cannot be read.

    Anything unreadable, truncated or of an unknown format returns None so the
    caller skips it rather than reporting a bogus size.
    """
    try:
        with open(path, "rb") as fh:
            head = fh.read(32)
    except OSError:
        return None
    if len(head) < 26:
        return None

    if head.startswith(_DDS_MAGIC):
        height, width = struct.unpack_from("<II", head, 12)
    elif head.startswith(_PNG_MAGIC):
        if head[12:16] != b"IHDR":
            return None
        width, height = struct.unpack_from(">II", head, 16)
    else:
        # TGA has no magic; its dimensions sit at a fixed offset in the 18-byte
        # header and the colour-map/image type bytes are what identify it.
        if head[1] not in (0, 1) or head[2] not in (1, 2, 3, 9, 10, 11):
            return None
        width, height = struct.unpack_from("<HH", head, 12)

    if width <= 0 or height <= 0:
        return None
    return width, height
