"""Tests for tools/assets/dds_standardize.py."""

import io
import struct

import pytest

np = pytest.importorskip("numpy")
Image = pytest.importorskip("PIL.Image")

import dds_mipmaps
import dds_standardize
from shared.suite import dds_texture


def _smooth(width, height, alpha=255):
    """RGBA whose colour slides along one line: DXT reproduces it closely."""
    x, _ = np.meshgrid(np.arange(width), np.arange(height))
    step = (255 * x / max(width - 1, 1)).astype(np.uint8)
    return np.stack([step, step // 2, 255 - step, np.full_like(step, alpha)], axis=-1)


def _noise(width, height):
    """RGBA noise: DXT cannot reproduce it."""
    rng = np.random.default_rng(0)
    rgba = rng.integers(0, 256, (height, width, 4), dtype=np.uint8)
    rgba[..., 3] = 255
    return rgba


def _bgra(rgba):
    return np.ascontiguousarray(rgba[..., [2, 1, 0, 3]]).tobytes()


def _dx10(rgba, dxgi, body=None):
    height, width = rgba.shape[:2]
    extension = struct.pack("<5I", dxgi, 3, 0, 1, 0)
    return dds_texture(width, height, b"DX10", 1, extension + (body or _bgra(rgba)))


def _legacy(width, height, bits, flags, masks, body):
    head = bytearray(dds_texture(width, height, b"", 1, bits=32))
    struct.pack_into("<I", head, 80, flags)
    struct.pack_into("<I4I", head, 88, bits, *masks)
    return bytes(head) + body


def _png(rgba):
    out = io.BytesIO()
    Image.fromarray(rgba).save(out, "PNG")
    return out.getvalue()


def _decode(data):
    with Image.open(io.BytesIO(data)) as image:
        return np.asarray(image.convert("RGBA"))


_ICON = _smooth(8, 8, alpha=128)
_RED = np.tile(np.array([255, 0, 0, 255], np.uint8), (2, 2, 1))

# case: (file bytes, kind, expected RGBA or None)
_READ_CASES = {
    "standard raw": (dds_standardize.as_raw(_ICON), "raw", _ICON),
    "raw without an alpha flag": (
        _legacy(2, 2, 32, 0x40, (0xFF0000, 0xFF00, 0xFF, 0), _bgra(_RED)),
        "raw",
        _RED,
    ),
    "red and blue swapped": (
        _legacy(2, 2, 32, 0x41, (0xFF, 0xFF00, 0xFF0000, 0xFF000000), _RED.tobytes()),
        "image",
        _RED,
    ),
    "24-bit": (
        _legacy(2, 2, 24, 0x40, (0xFF0000, 0xFF00, 0xFF, 0), bytes([0, 0, 255] * 4)),
        "image",
        _RED,
    ),
    "16-bit 5:6:5": (
        _legacy(
            2, 2, 16, 0x40, (0xF800, 0x7E0, 0x1F, 0), struct.pack("<4H", *[0xF800] * 4)
        ),
        "image",
        _RED,
    ),
    "16-bit grey with alpha": (
        _legacy(2, 2, 16, 0x41, (0xFF, 0xFF, 0xFF, 0xFF00), bytes([200, 100] * 4)),
        "image",
        np.tile(np.array([200, 200, 200, 100], np.uint8), (2, 2, 1)),
    ),
    "dx10 bgra": (_dx10(_ICON, 91), "image", _ICON),
    "dx10 rgba": (_dx10(_ICON, 29, _ICON.tobytes()), "image", _ICON),
    "dx10 without alpha": (_dx10(_RED, 88, _bgra(_RED)[:-1] + b"\x00"), "image", _RED),
    "png data": (_png(_ICON), "image", _ICON),
    "legacy dxt": (dds_standardize.as_blocks(_ICON, b"DXT5"), "blocks", None),
    "dx10 dxt": (_dx10(_ICON, 77, bytes(64)), "blocks", None),
}


@pytest.mark.parametrize(
    "data, kind, rgba", _READ_CASES.values(), ids=_READ_CASES.keys()
)
def test_read_decodes_each_container(data, kind, rgba):
    found, payload, problem = dds_standardize.read(data)
    assert (found, problem) == (kind, None)
    if rgba is not None:
        np.testing.assert_array_equal(payload, rgba)


# case: (file bytes, start of the problem)
_UNREADABLE = {
    "junk": (b"junk" * 40, "cannot decode"),
    "short header": (b"DDS " + bytes(20), "truncated"),
    "short dx10": (dds_texture(8, 8, b"DX10"), "truncated"),
    "dx10 format": (_dx10(_ICON, 98), "unsupported DX10 format 98"),
    "dx10 texels cut off": (_dx10(_ICON, 91, bytes(8)), "unsupported DX10 format 91"),
    "unknown fourcc": (
        dds_texture(8, 8, b"ATI2", body=bytes(64)),
        "unsupported format ATI2",
    ),
    "paletted": (
        _legacy(2, 2, 8, 0x20, (0, 0, 0, 0), bytes(4)),
        "unsupported 8-bit format",
    ),
    "zero size": (
        _legacy(0, 2, 32, 0x41, (0xFF0000, 0xFF00, 0xFF, 0xFF000000), b""),
        "unsupported",
    ),
    "texels cut off": (dds_standardize.as_raw(_ICON)[:-8], "truncated"),
}


@pytest.mark.parametrize("data, start", _UNREADABLE.values(), ids=_UNREADABLE.keys())
def test_read_reports_what_it_cannot_decode(data, start):
    kind, payload, problem = dds_standardize.read(data)
    assert kind is None and payload is None
    assert problem.startswith(start)


def test_raw_file_round_trips_exactly():
    data = dds_standardize.as_raw(_ICON)
    np.testing.assert_array_equal(_decode(data), _ICON)


# case: (image, passes the quality gate)
_GATE_CASES = {
    "smooth": (_smooth(32, 32), True),
    "noise": (_noise(32, 32), False),
    "see-through noise is ignored": (
        np.dstack([_noise(32, 32)[..., :3], np.zeros((32, 32), np.uint8)]),
        True,
    ),
}


@pytest.mark.parametrize("rgba, passes", _GATE_CASES.values(), ids=_GATE_CASES.keys())
def test_quality_gate(rgba, passes):
    fourcc = b"DXT5" if (rgba[..., 3] < 255).any() else b"DXT1"
    assert (
        dds_standardize.passes_gate(rgba, dds_standardize.as_blocks(rgba, fourcc))
        == passes
    )


def _format(data):
    """(fourcc or "raw", width, height, levels) of a legacy DDS."""
    texture, _ = dds_mipmaps.read_header(data)
    name = texture.fourcc.decode() if texture.fourcc else "raw"
    return name, texture.width, texture.height, texture.mipmaps


_PORTRAIT = _noise(120, 160)
_CHAINED_ICON = dds_mipmaps.add(
    dds_standardize.as_raw(_noise(16, 16)),
    dds_mipmaps.read_header(dds_standardize.as_raw(_noise(16, 16)))[0],
)
_MODEL = dds_standardize.as_blocks(_noise(64, 32), b"DXT1")
_MODEL_CHAINED = dds_mipmaps.add(_MODEL, dds_mipmaps.read_header(_MODEL)[0])

# case: (path, file bytes, max size, what was done, resulting format)
_STANDARDIZE_CASES = {
    "terrain is kept": ("map/terrain/a.dds", _dx10(_ICON, 91), None, [], None),
    "standard icon is left": (
        "gfx/interface/a.dds",
        dds_standardize.as_raw(_noise(16, 16)),
        None,
        [],
        None,
    ),
    "dx10 icon": (
        "gfx/interface/a.dds",
        _dx10(_noise(16, 16), 91),
        None,
        ["rewritten as A8R8G8B8"],
        ("raw", 16, 16, 1),
    ),
    "png icon": (
        "gfx/interface/a.dds",
        _png(_noise(16, 16)),
        None,
        ["rewritten as A8R8G8B8"],
        ("raw", 16, 16, 1),
    ),
    "smooth background passes the gate": (
        "gfx/interface/a.dds",
        dds_standardize.as_raw(_smooth(32, 32)),
        None,
        ["compressed, passes the quality gate"],
        ("DXT1", 32, 32, 1),
    ),
    "smooth tech icon is never compressed": (
        "gfx/interface/technologies/a.dds",
        dds_standardize.as_raw(_smooth(32, 32)),
        None,
        [],
        None,
    ),
    "smooth dx10 art is rewritten then compressed": (
        "gfx/interface/a.dds",
        _dx10(_smooth(32, 32), 91),
        None,
        ["rewritten as A8R8G8B8", "compressed, passes the quality gate"],
        ("DXT1", 32, 32, 1),
    ),
    "icon mipmaps are dropped": (
        "gfx/interface/a.dds",
        _CHAINED_ICON,
        None,
        ["mipmaps dropped"],
        ("raw", 16, 16, 1),
    ),
    "dx10 dxt keeps its blocks": (
        "gfx/interface/a.dds",
        _dx10(_ICON, 77, bytes(64)),
        None,
        ["replaced the DX10 header"],
        ("DXT5", 8, 8, 1),
    ),
    "large portrait": (
        "gfx/leaders/USA/a.dds",
        dds_standardize.as_raw(_PORTRAIT),
        None,
        ["compressed, as the standards say"],
        ("DXT1", 120, 160, 1),
    ),
    "small portrait stays raw": (
        "gfx/leaders/USA/a.dds",
        dds_standardize.as_raw(_noise(38, 51)),
        None,
        [],
        None,
    ),
    "event picture is always dxt5": (
        "gfx/event_pictures/a.dds",
        dds_standardize.as_raw(_noise(16, 16)),
        None,
        ["compressed, as the standards say"],
        ("DXT5", 16, 16, 1),
    ),
    "model texture gets compressed with mipmaps": (
        "gfx/models/a.dds",
        dds_standardize.as_raw(_smooth(16, 16, alpha=128)),
        None,
        ["compressed, as the standards say", "mipmaps added"],
        ("DXT5", 16, 16, 5),
    ),
    "model texture drops stored levels to fit": (
        "gfx/models/a.dds",
        _MODEL_CHAINED,
        16,
        ["shrunk to fit 16 px"],
        ("DXT1", 16, 8, 5),
    ),
    "model texture without levels is resized": (
        "gfx/models/a.dds",
        _MODEL,
        16,
        ["shrunk to fit 16 px", "mipmaps added"],
        ("DXT1", 16, 8, 5),
    ),
    "max size leaves icons alone": (
        "gfx/interface/a.dds",
        dds_standardize.as_blocks(_noise(64, 32), b"DXT1"),
        16,
        [],
        None,
    ),
    "unreadable file is skipped": (
        "gfx/interface/a.dds",
        b"junk" * 40,
        None,
        ["skipped: cannot decode"],
        None,
    ),
}


@pytest.mark.parametrize(
    "path, data, max_size, done, result",
    _STANDARDIZE_CASES.values(),
    ids=_STANDARDIZE_CASES.keys(),
)
def test_standardize(path, data, max_size, done, result):
    out, found = dds_standardize.standardize(data, path, max_size)
    assert [
        text.split(":")[0] + (":" + text.split(":")[1][:14] if ":" in text else "")
        for text in found
    ] == done
    if result is None:
        assert out == data
    else:
        assert _format(out) == result


def test_dx10_icon_keeps_every_texel():
    rgba = _noise(16, 16)
    out, _ = dds_standardize.standardize(_dx10(rgba, 91), "gfx/interface/a.dds")
    assert out[128:] == _bgra(rgba)


def test_dropped_levels_are_the_stored_ones():
    out, _ = dds_standardize.standardize(_MODEL_CHAINED, "gfx/models/a.dds", 16)
    assert out[128:] == _MODEL_CHAINED[128 + 64 * 32 // 2 + 32 * 16 // 2 :]


def _tree(root):
    files = {
        "gfx/interface/dx10.dds": _dx10(_noise(16, 16), 91),
        "gfx/interface/fine.dds": dds_standardize.as_raw(_noise(16, 16)),
        "gfx/interface/broken.dds": b"junk" * 40,
        "gfx/event_pictures/photo.dds": dds_standardize.as_raw(_noise(16, 16)),
    }
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return files


# case: (arguments, files rewritten, text in the summary)
_MAIN_CASES = {
    "report": ([], False, "size would change by"),
    "dry run": (["--fix"], False, "size would change by"),
    "write": (["--fix", "--write"], True, "size changed by"),
}


@pytest.mark.parametrize(
    "flags, rewritten, summary", _MAIN_CASES.values(), ids=_MAIN_CASES.keys()
)
def test_main(tmp_path, monkeypatch, capsys, flags, rewritten, summary):
    files = _tree(tmp_path)
    monkeypatch.setattr(dds_standardize, "REPO_ROOT", tmp_path)
    assert dds_standardize.main(flags) == 0
    out = capsys.readouterr().out
    assert "gfx/interface/dx10.dds: rewritten as A8R8G8B8" in out
    assert "gfx/event_pictures/photo.dds: compressed, as the standards say" in out
    assert "4 textures checked, 2 to change" in out and summary in out
    assert "skipped: cannot decode" in out
    changed = [
        name for name, data in files.items() if (tmp_path / name).read_bytes() != data
    ]
    assert changed == (
        ["gfx/interface/dx10.dds", "gfx/event_pictures/photo.dds"] if rewritten else []
    )


def test_main_rejects_missing_path(tmp_path, capsys):
    assert dds_standardize.main([str(tmp_path / "nowhere")]) == 2
    assert "Not found" in capsys.readouterr().err
