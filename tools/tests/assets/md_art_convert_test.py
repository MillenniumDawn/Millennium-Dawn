"""Art conversion tool: ImageMagick discovery and command lines, the fixed-size
and flag conversions, the byte-level TGA rewrite, and the CLI.

The command lines and the conversion rules run against a stubbed ImageMagick,
so they are tested on every machine. Two tests drive the real binary and skip
where it is not installed.
"""

import importlib
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import md_art_convert as M
import pytest
from shared.suite import imagemagick_available

Image = importlib.import_module("PIL.Image")

requires_imagemagick = pytest.mark.skipif(
    not imagemagick_available(), reason="ImageMagick is not installed"
)


def _on_path(monkeypatch, binaries, trusted=True):
    """Put `binaries` (name to path) on PATH. `trusted` skips the version probe."""
    monkeypatch.setattr(M.shutil, "which", binaries.get)
    if trusted:
        monkeypatch.setattr(M, "_is_imagemagick", lambda _path: True)


def _record_runs(monkeypatch, **result):
    """Stub subprocess.run to return `result` and record each command line."""
    calls = []
    monkeypatch.setattr(
        M.subprocess,
        "run",
        lambda argv, **_kwargs: calls.append(argv) or SimpleNamespace(**result),
    )
    return calls


def _png(path, size, pixels=None):
    image = Image.new("RGBA", size)
    for position, color in (pixels or {}).items():
        image.putpixel(position, color)
    image.save(path)
    return path


# ---- ImageMagick discovery and command lines ---------------------------------

# Windows ships its own convert.exe, which converts FAT volumes to NTFS.
# case: (binaries on PATH, version probe output or None when it cannot run,
#        binary chosen or None when the tool must exit)
_DISCOVERY_CASES = {
    "magick before convert": (
        {"magick": "/tools/magick", "convert": "/tools/convert"},
        "Version: ImageMagick 7",
        "/tools/magick",
    ),
    "convert alone": (
        {"convert": "/tools/convert"},
        "Version: ImageMagick 6",
        "/tools/convert",
    ),
    "nothing on PATH": ({}, "", None),
    "a convert that is not ImageMagick": (
        {"convert": "C:/Windows/system32/convert.exe"},
        "Converts FAT volumes to NTFS.",
        None,
    ),
    "probe cannot run": ({"magick": "/tools/magick"}, None, None),
}


@pytest.mark.parametrize(
    ("binaries", "probe", "chosen"), _DISCOVERY_CASES.values(), ids=_DISCOVERY_CASES
)
def test_imagemagick_is_the_first_binary_that_answers_as_imagemagick(
    monkeypatch, binaries, probe, chosen
):
    def run(*_args, **_kwargs):
        if probe is None:
            raise OSError("cannot run")
        return SimpleNamespace(stdout=probe, stderr="")

    _on_path(monkeypatch, binaries, trusted=False)
    monkeypatch.setattr(M.subprocess, "run", run)

    if chosen is None:
        with pytest.raises(SystemExit, match="ImageMagick not found"):
            M.imagemagick()
    else:
        assert M.imagemagick() == [chosen]


# case: (binaries on PATH, start of the command line)
_IDENTIFY_CASES = {
    "identify binary": (
        {"identify": "/usr/bin/identify"},
        ["/usr/bin/identify", "-format"],
    ),
    "magick subcommand": (
        {"magick": "/usr/bin/magick"},
        ["/usr/bin/magick", "identify", "-format"],
    ),
}


@pytest.mark.parametrize(
    ("binaries", "head"), _IDENTIFY_CASES.values(), ids=_IDENTIFY_CASES
)
def test_image_size_runs_identify(monkeypatch, binaries, head):
    _on_path(monkeypatch, binaries)
    calls = _record_runs(monkeypatch, stdout="10 20")

    assert M.image_size(Path("x.png")) == (10, 20)
    assert calls[0][: len(head)] == head


# case: (binaries on PATH, compare output, start of the command line, match)
_COMPARE_CASES = {
    "magick subcommand": (
        {"magick": "/usr/bin/magick"},
        "0",
        ["/usr/bin/magick", "compare"],
        True,
    ),
    "compare binary": (
        {"convert": "/usr/bin/convert", "compare": "/usr/bin/compare"},
        "0.0",
        ["/usr/bin/compare", "-metric"],
        True,
    ),
    "pixels differ": (
        {"magick": "/usr/bin/magick"},
        "3 (4.5e-05)",
        ["/usr/bin/magick", "compare"],
        False,
    ),
}


@pytest.mark.parametrize(
    ("binaries", "output", "head", "match"),
    _COMPARE_CASES.values(),
    ids=_COMPARE_CASES,
)
def test_pixels_match_reads_the_differing_pixel_count(
    monkeypatch, binaries, output, head, match
):
    _on_path(monkeypatch, binaries)
    calls = _record_runs(monkeypatch, stderr=output)

    assert M.pixels_match(Path("a.png"), Path("b.png")) is match
    assert calls[0][: len(head)] == head


# ---- conversions on a stubbed ImageMagick ------------------------------------


def _stub_conversion(monkeypatch, size, match):
    """Fix the source size and the compare result; record each file written."""
    written = []

    def write(_src, dest, _target, resize):
        written.append((dest, resize))

    monkeypatch.setattr(M, "image_size", lambda _path: size)
    monkeypatch.setattr(M, "pixels_match", lambda *_args: match)
    monkeypatch.setattr(M, "write_dds", write)
    monkeypatch.setattr(M, "write_tga", write)
    return written


_NO_MATCH = "does not match its source"

# A copy is resized only when its size differs, and a resized copy is not
# compared with its source.
# case: (source size, --resize, verify, pixels match, problems, line printed,
#        the copy written as (file, resized) or None)
_FIXED_SIZE_CASES = {
    "allowed size": ((2, 2), False, True, True, 0, "OK", ("x.dds", False)),
    "wrong size": ((3, 3), False, True, True, 1, "SKIP", None),
    "wrong size, resized": ((3, 3), True, True, False, 0, "OK", ("x.dds", True)),
    "copy does not match": ((2, 2), False, True, False, 1, _NO_MATCH, ("x.dds", False)),
    "unverified copy": ((2, 2), False, False, False, 0, "OK", ("x.dds", False)),
}


@pytest.mark.parametrize(
    ("size", "resize", "verify", "match", "problems", "line", "copy"),
    _FIXED_SIZE_CASES.values(),
    ids=_FIXED_SIZE_CASES,
)
def test_fixed_size_conversion_checks_the_size_and_the_copy(
    monkeypatch, tmp_path, capsys, size, resize, verify, match, problems, line, copy
):
    written = _stub_conversion(monkeypatch, size, match)

    found = M.convert_fixed_size(
        [tmp_path / "x.png"], tmp_path / "out", [(2, 2)], resize=resize, verify=verify
    )

    assert found == problems
    assert line in capsys.readouterr().out
    assert [(dest.name, resized) for dest, resized in written] == (
        [copy] if copy else []
    )


# case: (source size, verify, pixels match, problems, line printed)
_FLAG_CASES = {
    "base size": ((82, 52), True, True, 0, "OK"),
    "other size": ((10, 10), True, False, 0, "resizing to 82x52"),
    "base copy does not match": ((82, 52), True, False, 1, _NO_MATCH),
    "unverified base copy": ((82, 52), False, False, 0, "OK"),
}


@pytest.mark.parametrize(
    ("size", "verify", "match", "problems", "line"),
    _FLAG_CASES.values(),
    ids=_FLAG_CASES,
)
def test_flag_conversion_writes_three_sizes_and_checks_the_unscaled_one(
    monkeypatch, tmp_path, capsys, size, verify, match, problems, line
):
    written = _stub_conversion(monkeypatch, size, match)
    flags = tmp_path / "flags"

    found = M.convert_flag(tmp_path / "flag.png", "TST", flags, verify=verify)

    assert found == problems
    assert line in capsys.readouterr().out
    # Only a source already at the base size is copied unscaled.
    assert written == [
        (flags / "TST.tga", size != (82, 52)),
        (flags / "medium" / "TST.tga", True),
        (flags / "small" / "TST.tga", True),
    ]


_RESIZE = ["-filter", "Lanczos", "-resize", "4x2!"]
_DDS = ["-alpha", "set", "-define", "dds:compression=none", "-define", "dds:mipmaps=0"]
_TGA = ["-flip", "-alpha", "set", "-orient", "bottom-left", "-compress", "None"]

# The DDS is uncompressed with alpha. The TGA is flipped to a bottom-left origin.
# case: (writer, resize, options between the source and the destination)
_WRITER_CASES = {
    "dds": ("write_dds", False, _DDS),
    "dds, resized": ("write_dds", True, _RESIZE + _DDS),
    "tga": ("write_tga", False, _TGA),
    "tga, resized": ("write_tga", True, _RESIZE + _TGA),
}


@pytest.mark.parametrize(
    ("writer", "resize", "options"), _WRITER_CASES.values(), ids=_WRITER_CASES
)
def test_writer_builds_its_imagemagick_command(
    monkeypatch, tmp_path, writer, resize, options
):
    _on_path(monkeypatch, {"magick": "/usr/bin/magick"})
    calls = _record_runs(monkeypatch)
    dest = tmp_path / "out" / "copy"

    getattr(M, writer)(Path("src.png"), dest, (4, 2), resize)

    assert calls == [["/usr/bin/magick", "src.png", *options, str(dest)]]
    assert dest.parent.is_dir()


# ---- conversions on the real ImageMagick -------------------------------------


@requires_imagemagick
def test_real_imagemagick_writes_a_dds_and_a_bottom_left_tga(tmp_path):
    red = (255, 0, 0, 255)
    source = _png(
        tmp_path / "source.png",
        (2, 2),
        {(0, 0): red, (1, 0): (0, 255, 0, 255), (0, 1): (0, 0, 255, 255)},
    )
    assert M.image_size(source) == (2, 2)

    dds = tmp_path / "converted.dds"
    M.write_dds(source, dds, (2, 2), resize=False)
    assert M.image_size(dds) == (2, 2)

    same_size = tmp_path / "same-size.tga"
    M.write_tga(source, same_size, (2, 2), resize=False)
    with Image.open(same_size) as converted:
        assert converted.size == (2, 2)

    all_red = _png(
        tmp_path / "red.png", (2, 2), {(x, y): red for x in (0, 1) for y in (0, 1)}
    )
    tga = tmp_path / "converted.tga"
    M.write_tga(all_red, tga, (1, 1), resize=True)
    assert M.image_size(tga) == (1, 1)
    data = tga.read_bytes()
    header = M.TGA_HEADER.unpack_from(data)
    pixel_start = M.TGA_HEADER.size + header[0] + header[4] * (header[5] // 8)
    # 32 bits per pixel, bottom-left origin, pixels stored as BGRA.
    assert header[10] == 32
    assert header[11] & M.TGA_TOP_LEFT == 0
    assert data[pixel_start : pixel_start + 4] == b"\x00\x00\xff\xff"

    assert M.pixels_match(source, source)
    assert not M.pixels_match(source, all_red)


@requires_imagemagick
def test_real_imagemagick_converts_event_pictures_and_flags(tmp_path):
    good = _png(tmp_path / "good.png", (2, 2))
    bad = _png(tmp_path / "bad.png", (3, 3))
    output = tmp_path / "dds"

    assert M.convert_fixed_size([good, bad], output, [(2, 2)], False, True) == 1
    assert (output / "good.dds").is_file()
    assert not (output / "bad.dds").exists()
    assert M.convert_fixed_size([bad], output, [(2, 2)], True, False) == 0
    assert M.image_size(output / "bad.dds") == (2, 2)

    flags = tmp_path / "flags"
    assert M.convert_flag(good, "TST", flags, verify=False) == 0
    for subdir, size in M.FLAG_SIZES.items():
        with Image.open(flags / subdir / "TST.tga") as flag:
            assert flag.size == size


# ---- the TGA rewrite ---------------------------------------------------------


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
    header = M.TGA_HEADER.pack(
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
        M.TGA_HEADER.unpack_from(data, 0)
    )
    start = M.TGA_HEADER.size + idlength + cmap_length * (cmap_depth // 8)
    stride = width * (bpp // 8)
    return [data[start + i * stride : start + (i + 1) * stride] for i in range(height)]


_TWO_ROWS = [b"\x01\x01\x01\x01", b"\x02\x02\x02\x02"]
_TOP_LEFT = _tga(_TWO_ROWS, width=1, bpp=32, descriptor=0x28)
_BOTTOM_LEFT = _tga(_TWO_ROWS, width=1, bpp=32, descriptor=0x08)


def test_top_left_rows_are_reversed_and_the_origin_bit_cleared():
    rows = [b"\x01\x01\x01\x01", b"\x02\x02\x02\x02", b"\x03\x03\x03\x03"]
    out = M.tga_normalised(_tga(rows, width=1, bpp=32, descriptor=0x28))

    assert out is not None
    assert out[17] == 0x08
    assert _rows(out) == list(reversed(rows))
    assert len(out) == len(_tga(rows, width=1, bpp=32, descriptor=0x28))


def test_twenty_four_bit_keeps_its_depth_and_clears_only_the_origin_bit():
    rows = [b"\x01\x02\x03", b"\x04\x05\x06"]
    out = M.tga_normalised(_tga(rows, width=1, bpp=24, descriptor=0x20))

    assert out is not None
    assert out[16] == 24
    assert out[17] == 0x00
    assert _rows(out) == list(reversed(rows))


def test_colour_mapped_rows_flip_without_disturbing_the_palette():
    palette = bytes(range(12))
    rows = [b"\x00", b"\x01", b"\x02"]
    out = M.tga_normalised(
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
    assert out[M.TGA_HEADER.size : M.TGA_HEADER.size + len(palette)] == palette
    assert _rows(out) == list(reversed(rows))


def test_id_field_and_footer_survive():
    footer = b"TRUEVISION-XFILE.\x00"
    out = M.tga_normalised(
        _tga(
            _TWO_ROWS,
            width=1,
            bpp=32,
            descriptor=0x28,
            id_field=b"note",
            trailer=footer,
        )
    )

    assert out is not None
    assert out[M.TGA_HEADER.size : M.TGA_HEADER.size + 4] == b"note"
    assert out.endswith(footer)


# A file the rewrite cannot move byte for byte is refused, never scrambled.
_REFUSED_CASES = {
    "bottom-left already": _BOTTOM_LEFT,
    "run-length encoded": struct.pack(
        "<BBBHHBHHHHBB", 0, 0, 10, 0, 0, 0, 0, 0, 2, 2, 32, 0x28
    )
    + b"\x82\x01\x02\x03\x04",
    "truncated pixel data": M.TGA_HEADER.pack(0, 0, 2, 0, 0, 0, 0, 0, 4, 4, 32, 0x28)
    + b"\x00" * 8,
    "header too short": b"\x00\x00\x02",
    "zero width": M.TGA_HEADER.pack(0, 0, 2, 0, 0, 0, 0, 0, 0, 1, 24, 0x20),
}


@pytest.mark.parametrize("data", _REFUSED_CASES.values(), ids=_REFUSED_CASES)
def test_tga_that_cannot_be_rewritten_is_left_alone(data):
    assert M.tga_normalised(data) is None


def test_normalise_dir_fixes_top_left_files_and_counts_those_it_cannot(tmp_path):
    root = tmp_path / "nested"
    root.mkdir()
    fixed = M.tga_normalised(_TOP_LEFT)
    (root / "valid.tga").write_bytes(_TOP_LEFT)
    (root / "unchanged.tga").write_bytes(_BOTTOM_LEFT)
    # Top-left files the rewrite refuses need a manual pass.
    (root / "compressed.tga").write_bytes(_REFUSED_CASES["run-length encoded"])
    (root / "malformed.tga").write_bytes(_REFUSED_CASES["truncated pixel data"])

    assert M.normalise_dir(root, check_only=True) == (1, 2)
    assert (root / "valid.tga").read_bytes() == _TOP_LEFT
    assert M.normalise_dir(root, check_only=False) == (1, 2)
    assert (root / "valid.tga").read_bytes() == fixed


# ---- the CLI -----------------------------------------------------------------


def _main(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["md_art_convert.py", *map(str, argv)])
    return M.main()


def test_normalise_command_fails_a_check_until_the_files_are_fixed(
    tmp_path, monkeypatch
):
    path = tmp_path / "one.tga"
    path.write_bytes(_TOP_LEFT)

    assert _main(monkeypatch, "normalise", tmp_path, "--check") == 1
    assert path.read_bytes() == _TOP_LEFT
    assert _main(monkeypatch, "normalise", tmp_path) == 0
    assert path.read_bytes() == M.tga_normalised(_TOP_LEFT)
    assert _main(monkeypatch, "normalise", tmp_path, "--check") == 0


def test_main_requires_a_command(monkeypatch):
    with pytest.raises(SystemExit):
        _main(monkeypatch)


_EVENT_SIZES = [M.COUNTRY_EVENT_SIZE, M.NEWS_EVENT_SIZE]
_EVENT = ("fixed", [Path("a.png")], Path("out"), _EVENT_SIZES, False, True)

# case: (arguments, conversion called with, problems it returns, exit code)
_COMMAND_CASES = {
    "event": (["event", "a.png", "--out-dir", "out"], _EVENT, 0, 0),
    "event with problems": (["event", "a.png", "--out-dir", "out"], _EVENT, 2, 1),
    "portrait, resized, unverified": (
        ["portrait", "a.png", "--out-dir", "out", "--resize", "--no-verify"],
        ("fixed", [Path("a.png")], Path("out"), [M.PORTRAIT_SIZE], True, False),
        0,
        0,
    ),
    "flag": (
        ["flag", "a.png", "--name", "ABC", "--flags-dir", "flags", "--no-verify"],
        ("flag", Path("a.png"), "ABC", Path("flags"), False),
        0,
        0,
    ),
}


@pytest.mark.parametrize(
    ("argv", "call", "problems", "code"),
    _COMMAND_CASES.values(),
    ids=_COMMAND_CASES,
)
def test_main_routes_each_command_to_its_conversion(
    monkeypatch, argv, call, problems, code
):
    calls = []
    for name, attribute in (("fixed", "convert_fixed_size"), ("flag", "convert_flag")):
        monkeypatch.setattr(
            M,
            attribute,
            lambda *args, name=name: calls.append((name, *args)) or problems,
        )

    assert _main(monkeypatch, *argv) == code
    assert calls == [call]
