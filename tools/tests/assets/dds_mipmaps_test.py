"""Tests for tools/assets/dds_mipmaps.py."""

import io
import struct

import pytest

np = pytest.importorskip("numpy")
Image = pytest.importorskip("PIL.Image")

import dds_mipmaps
from shared.suite import dds_texture


def _gradient(width, height):
    """An opaque RGBA image whose colour slides along one line from left to right."""
    x, _ = np.meshgrid(np.arange(width), np.arange(height))
    step = 255 * x / max(width - 1, 1)
    return np.stack([step, step / 2, 255 - step, np.full(x.shape, 255.0)], axis=-1)


def _texture(image, fourcc, mipmaps=1, extra=b""):
    """A DDS file of `image` in a compressed format or, for b"", as raw texels."""
    height, width = image.shape[:2]
    if fourcc:
        body = dds_mipmaps._encode_level(image, fourcc)
        return dds_texture(width, height, fourcc, mipmaps, body + extra)
    channels = image.shape[-1]
    body = np.rint(image).astype(np.uint8).tobytes()
    return dds_texture(width, height, b"", mipmaps, body + extra, bits=8 * channels)


def _level(data, level):
    """Decode one level of a compressed DDS as an RGBA array."""
    texture, _ = dds_mipmaps.read_header(data)
    start = 128 + sum(texture.level_size(i) for i in range(level))
    body = data[start : start + texture.level_size(level)]
    width, height = max(1, texture.width >> level), max(1, texture.height >> level)
    single = dds_texture(width, height, texture.fourcc, 1, body)
    with Image.open(io.BytesIO(single)) as image:
        return np.asarray(image.convert("RGBA"), float)


def _header_fields(data):
    flags = struct.unpack_from("<I", data, 8)[0]
    return (
        bool(flags & 0x20000),
        struct.unpack_from("<I", data, 28)[0],
        bool(struct.unpack_from("<I", data, 108)[0] & 0x400008),
    )


# case: (file bytes, why it is unsupported or None)
_HEADER_CASES = {
    "dxt1": (dds_texture(8, 8, body=bytes(32)), None),
    "raw 24-bit": (dds_texture(2, 2, b"", body=bytes(12), bits=24), None),
    "not dds": (b"\x89PNG" + bytes(200), "not DDS data"),
    "short": (b"DDS ", "not DDS data"),
    "dx10": (dds_texture(8, 8, b"DX10", body=bytes(64)), "unsupported format DX10"),
    "16-bit": (
        dds_texture(8, 8, b"", body=bytes(128), bits=16),
        "unsupported 16-bit format",
    ),
    "zero size": (dds_texture(8, 0), "zero size"),
    "truncated": (dds_texture(8, 8, body=bytes(31)), "truncated"),
}


@pytest.mark.parametrize(
    "data, problem", _HEADER_CASES.values(), ids=_HEADER_CASES.keys()
)
def test_read_header(data, problem):
    texture, found = dds_mipmaps.read_header(data)
    assert found == problem
    assert (texture is None) == (problem is not None)


# case: (width, height, fourcc, bytes per raw texel, chain length, sizes of levels 0-2)
_SIZE_CASES = {
    "dxt1": (16, 8, b"DXT1", 0, 5, [64, 16, 8]),
    "dxt5 odd": (5, 3, b"DXT5", 0, 3, [32, 16, 16]),
    "raw": (6, 1, b"", 4, 3, [24, 12, 4]),
}


@pytest.mark.parametrize(
    "width, height, fourcc, pixel, chain, sizes",
    _SIZE_CASES.values(),
    ids=_SIZE_CASES.keys(),
)
def test_level_sizes(width, height, fourcc, pixel, chain, sizes):
    texture = dds_mipmaps.Texture(width, height, 1, fourcc, pixel)
    assert texture.full_chain == chain
    assert [texture.level_size(level) for level in range(3)] == sizes


# case: (fourcc, channels of the source image)
_FORMATS = {
    "dxt1": (b"DXT1", 4),
    "dxt3": (b"DXT3", 4),
    "dxt5": (b"DXT5", 4),
    "raw 32-bit": (b"", 4),
    "raw 24-bit": (b"", 3),
}


@pytest.mark.parametrize("fourcc, channels", _FORMATS.values(), ids=_FORMATS.keys())
def test_add_then_strip_keeps_the_full_size_level(fourcc, channels):
    source = _texture(_gradient(16, 8)[..., :channels], fourcc)
    texture, _ = dds_mipmaps.read_header(source)
    added = dds_mipmaps.add(source, texture)
    with_chain, _ = dds_mipmaps.read_header(added)
    assert _header_fields(added) == (True, 5, True)
    assert len(added) == 128 + sum(with_chain.level_size(i) for i in range(5))
    assert added[128 : 128 + texture.level_size()] == source[128:]
    stripped = dds_mipmaps.strip(added, with_chain)
    assert stripped[128:] == source[128:]
    assert _header_fields(stripped) == (False, 0, False)


def test_raw_levels_are_box_filtered():
    image = np.zeros((2, 4, 4))
    image[:, :2] = [10, 20, 30, 40]
    image[:, 2:] = [50, 60, 70, 80]
    source = _texture(image, b"")
    added = dds_mipmaps.add(source, dds_mipmaps.read_header(source)[0])
    assert list(added[128 + 32 :]) == [10, 20, 30, 40, 50, 60, 70, 80, 30, 40, 50, 60]


@pytest.mark.parametrize(
    "shape", [(1, 4), (4, 1)], ids=["one texel high", "one texel wide"]
)
def test_thin_texture_halves_along_its_long_side_only(shape):
    image = np.zeros((*shape, 4))
    image[..., 0] = np.array([10.0, 30.0, 50.0, 70.0]).reshape(shape)
    source = _texture(image, b"")
    added = dds_mipmaps.add(source, dds_mipmaps.read_header(source)[0])
    assert list(added[128 + 16 :: 4]) == [20, 60, 40]


@pytest.mark.parametrize("fourcc", [b"DXT1", b"DXT3", b"DXT5"])
def test_compressed_levels_stay_close_to_the_source(fourcc, monkeypatch):
    # A tiny chunk size runs the same blocks through several encoder passes.
    monkeypatch.setattr(dds_mipmaps, "ENCODE_CHUNK", 3)
    image = _gradient(32, 32)
    image[..., 3] = image[..., 0] if fourcc != b"DXT1" else 255
    source = _texture(image, fourcc)
    added = dds_mipmaps.add(source, dds_mipmaps.read_header(source)[0])
    expected = image.reshape(16, 2, 16, 2, 4).mean(axis=(1, 3))
    assert np.abs(_level(added, 1) - expected).mean() < 4
    assert np.abs(_level(added, 5) - image.mean(axis=(0, 1))).max() < 12


def test_flat_colour_survives_every_level():
    image = np.tile([200.0, 100.0, 50.0, 255.0], (8, 8, 1))
    source = _texture(image, b"DXT1")
    added = dds_mipmaps.add(source, dds_mipmaps.read_header(source)[0])
    for level in range(4):
        assert np.abs(_level(added, level) - image[0, 0]).max() < 6


def test_dxt1_see_through_texels_stay_see_through_and_do_not_bleed():
    image = np.tile([255.0, 255.0, 255.0, 255.0], (16, 16, 1))
    image[:, :8] = [0, 0, 0, 0]
    source = _texture(image, b"DXT1")
    added = dds_mipmaps.add(source, dds_mipmaps.read_header(source)[0])
    half = _level(added, 1)
    assert (half[:, :4, 3] == 0).all() and (half[:, 4:, 3] == 255).all()
    assert half[:, 4:, :3].min() > 245


# case: (fourcc, level-1 texel written by --tint)
_TINT_CASES = {
    "compressed is red, green, blue": (b"DXT5", [255, 0, 0, 255]),
    "raw texels are blue, green, red": (b"", [0, 0, 255, 255]),
}


@pytest.mark.parametrize("fourcc, texel", _TINT_CASES.values(), ids=_TINT_CASES.keys())
def test_tint_colours_the_smaller_levels(tmp_path, capsys, fourcc, texel):
    source, out = tmp_path / "in.dds", tmp_path / "out.dds"
    source.write_bytes(_texture(_gradient(8, 8), fourcc))
    assert dds_mipmaps.main(["--tint", str(source), str(out)]) == 0
    assert "4 levels" in capsys.readouterr().out
    data = out.read_bytes()
    assert data[128 : 128 + len(source.read_bytes()) - 128] == source.read_bytes()[128:]
    if fourcc:
        first = _level(data, 1)[0, 0]
    else:
        first = np.frombuffer(data, np.uint8, 4, 128 + 8 * 8 * 4)
    assert np.abs(np.asarray(first, float) - texel).max() < 8


def test_tint_rejects_bad_input(tmp_path, capsys):
    source = tmp_path / "in.dds"
    source.write_bytes(b"junk")
    assert dds_mipmaps.main(["--tint", str(source), str(tmp_path / "out.dds")]) == 1
    assert "not DDS data" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        dds_mipmaps.main(["--tint", str(source)])


_PLAIN = _texture(_gradient(16, 16), b"DXT1")
_CHAINED = dds_mipmaps.add(_PLAIN, dds_mipmaps.read_header(_PLAIN)[0])

# case: (path, file bytes, (action, detail))
_PLAN_CASES = {
    "model without mipmaps": ("gfx/models/a.dds", _PLAIN, ("add", "4 levels")),
    "model with mipmaps": ("gfx/models/a.dds", _CHAINED, ("ok", "")),
    "tiny model texture": (
        "gfx/models/a.dds",
        dds_texture(4, 4, body=bytes(8)),
        ("ok", ""),
    ),
    "icon with mipmaps": ("gfx/interface/a.dds", _CHAINED, ("strip", "4 levels, 0 KB")),
    "icon without mipmaps": ("gfx/interface/a.dds", _PLAIN, ("ok", "")),
    "terrain is left alone": ("map/terrain/a.dds", _PLAIN, ("ok", "")),
    "unsupported file": ("gfx/models/a.dds", b"junk", ("skip", "not DDS data")),
}


@pytest.mark.parametrize(
    "path, data, expected", _PLAN_CASES.values(), ids=_PLAN_CASES.keys()
)
def test_plan(path, data, expected):
    assert dds_mipmaps.plan(data, path) == expected


def _tree(root):
    files = {
        "gfx/models/unit.dds": _PLAIN,
        "gfx/interface/icon.dds": _CHAINED,
        "gfx/interface/fine.dds": _PLAIN,
        "gfx/interface/broken.dds": b"junk",
        "map/terrain/atlas.dds": _PLAIN,
        "gfx/interface/notes.txt": b"ignored",
    }
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return files


def test_report_lists_files_against_the_rule(tmp_path, monkeypatch, capsys):
    files = _tree(tmp_path)
    monkeypatch.setattr(dds_mipmaps, "REPO_ROOT", tmp_path)
    assert dds_mipmaps.main([]) == 0
    out = capsys.readouterr().out
    assert "gfx/models/unit.dds: needs mipmaps (4 levels)" in out
    assert "gfx/interface/icon.dds: has unneeded mipmaps (4 levels, 0 KB)" in out
    assert "5 textures checked" in out and "skipped, not DDS data: 1" in out
    assert all((tmp_path / name).read_bytes() == data for name, data in files.items())


# case: (extra arguments, verb printed, files rewritten)
_FIX_CASES = {
    "dry run": ([], "would add", False),
    "write": (["--write"], "add", True),
}


@pytest.mark.parametrize(
    "flags, verb, rewritten", _FIX_CASES.values(), ids=_FIX_CASES.keys()
)
def test_fix(tmp_path, monkeypatch, capsys, flags, verb, rewritten):
    _tree(tmp_path)
    monkeypatch.setattr(dds_mipmaps, "REPO_ROOT", tmp_path)
    assert dds_mipmaps.main(["--fix", *flags, str(tmp_path / "gfx")]) == 0
    out = capsys.readouterr().out
    assert f"gfx/models/unit.dds: {verb} (4 levels)" in out
    assert "size " in out and "MB" in out
    unit = (tmp_path / "gfx/models/unit.dds").read_bytes()
    icon = (tmp_path / "gfx/interface/icon.dds").read_bytes()
    assert (unit == _CHAINED, icon[128:] == _PLAIN[128:]) == (rewritten, rewritten)
    if rewritten:
        assert dds_mipmaps.main(["--fix", str(tmp_path / "gfx")]) == 0
        assert "need mipmaps: 0" in capsys.readouterr().out


def test_paths_outside_the_repo_fall_back_to_keep(tmp_path, capsys):
    path = tmp_path / "loose.dds"
    path.write_bytes(_CHAINED)
    assert dds_mipmaps.main([str(path)]) == 0
    assert "have unneeded mipmaps: 0" in capsys.readouterr().out


def test_main_rejects_missing_path(tmp_path, capsys):
    assert dds_mipmaps.main([str(tmp_path / "nowhere")]) == 2
    assert "Not found" in capsys.readouterr().err
