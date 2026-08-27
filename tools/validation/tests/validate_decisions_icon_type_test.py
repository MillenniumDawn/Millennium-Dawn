"""Tests for the decision icon slot check and its image-size backing."""

import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from image_size import read_image_size
from validate_decisions import _icon_type_message, _slot_for_size


def _write_dds(path, width, height):
    header = bytearray(128)
    header[0:4] = b"DDS "
    struct.pack_into("<II", header, 12, height, width)
    with open(path, "wb") as fh:
        fh.write(header)


def test_read_dds_size(tmp_path):
    dds = tmp_path / "icon.dds"
    _write_dds(dds, 52, 40)

    assert read_image_size(str(dds)) == (52, 40)


def test_read_png_size(tmp_path):
    png = tmp_path / "icon.png"
    header = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
    with open(png, "wb") as fh:
        fh.write(header + struct.pack(">II", 114, 101) + b"\x08\x06\x00\x00\x00")

    assert read_image_size(str(png)) == (114, 101)


def test_read_unknown_format_returns_none(tmp_path):
    blob = tmp_path / "icon.dds"
    with open(blob, "wb") as fh:
        fh.write(b"not an image at all, but long enough to read")

    assert read_image_size(str(blob)) is None


def test_slot_bands():
    assert _slot_for_size(33, 32) == "decision"
    assert _slot_for_size(52, 40) == "category_icon"
    assert _slot_for_size(114, 101) == "category_picture"


def test_in_between_size_identifies_no_slot():
    assert _slot_for_size(38, 40) is None


def _textures(tmp_path, sprites):
    index = {}
    for name, (width, height) in sprites.items():
        path = tmp_path / f"{name}.dds"
        _write_dds(path, width, height)
        index[name] = str(path)
    return index


def test_category_art_on_a_decision_is_reported(tmp_path):
    textures = _textures(tmp_path, {"GFX_decision_politics": (52, 40)})

    msg = _icon_type_message("decision", "some_decision", "politics", textures)

    assert msg is not None
    assert "category icon art" in msg


def test_decision_art_on_a_category_is_reported(tmp_path):
    textures = _textures(tmp_path, {"GFX_decision_category_x": (33, 32)})

    msg = _icon_type_message("category_icon", "some_category", "x", textures)

    assert msg is not None
    assert "decision icon art" in msg


def test_correctly_sized_icon_is_not_reported(tmp_path):
    textures = _textures(tmp_path, {"GFX_decision_politics": (33, 32)})

    assert _icon_type_message("decision", "some_decision", "politics", textures) is None


def test_unresolved_sprite_is_left_to_the_missing_icon_check(tmp_path):
    assert _icon_type_message("decision", "some_decision", "nothing", {}) is None


def test_runtime_value_is_skipped(tmp_path):
    textures = _textures(tmp_path, {"GFX_decision_politics": (52, 40)})

    assert _icon_type_message("decision", "d", "[?var]", textures) is None
