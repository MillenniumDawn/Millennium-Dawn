import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import gfx_entry_generator as generator
import pytest

Image = importlib.import_module("PIL.Image")

ROOT = Path(__file__).resolve().parents[2]


def _load_asset(name):
    path = ROOT / "tools" / "assets" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"coverage_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


md_art_convert = _load_asset("md_art_convert")
state_gfx = _load_asset("state_gfx")


requires_imagemagick = pytest.mark.skipif(
    not md_art_convert.has_imagemagick(), reason="ImageMagick is not installed"
)


def _write_text(path, text, newline=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline=newline) as stream:
        stream.write(text)


def _read_text(path):
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def _inputs(*values):
    answers = iter(values)
    return lambda _prompt: next(answers)


def _image(path, size, pixels, mode="RGBA"):
    image = Image.new(mode, size)
    for position, color in pixels.items():
        image.putpixel(position, color)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return image


def _render(name, texture):
    return (
        f'\tspriteType = {{\n\t\tname = "{name}"\n\t\ttexturefile = "{texture}"\n\t}}\n'
    )


def _top_left_tga(image, datatype=2, tail=b""):
    header = md_art_convert.TGA_HEADER.pack(
        0,
        0,
        datatype,
        0,
        0,
        0,
        0,
        0,
        image.width,
        image.height,
        len(image.getbands()) * 8,
        md_art_convert.TGA_TOP_LEFT,
    )
    return header + image.tobytes() + tail


def test_md_imagemagick_resolution_and_missing_executable(monkeypatch):
    paths = {"magick": "/tools/magick", "convert": "/tools/convert"}
    monkeypatch.setattr(md_art_convert.shutil, "which", paths.get)
    assert md_art_convert.imagemagick() == ["/tools/magick"]

    paths.pop("magick")
    assert md_art_convert.imagemagick() == ["/tools/convert"]

    paths.clear()
    with pytest.raises(SystemExit, match="ImageMagick not found"):
        md_art_convert.imagemagick()


def test_md_windows_ntfs_convert_is_not_mistaken_for_imagemagick(monkeypatch):
    ntfs = "/fake-windows/system32/convert.exe"
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("SystemRoot", "/fake-windows")
    monkeypatch.setattr(md_art_convert.shutil, "which", {"convert": ntfs}.get)

    assert not md_art_convert.has_imagemagick()
    with pytest.raises(SystemExit, match="ImageMagick not found"):
        md_art_convert.imagemagick()

    elsewhere = "/opt/imagemagick/convert.exe"
    monkeypatch.setattr(md_art_convert.shutil, "which", {"convert": elsewhere}.get)
    assert md_art_convert.imagemagick() == [elsewhere]

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(md_art_convert.shutil, "which", {"convert": ntfs}.get)
    assert md_art_convert.imagemagick() == [ntfs]


def test_md_image_size_names_imagemagick_when_it_is_missing(monkeypatch):
    monkeypatch.setattr(md_art_convert.shutil, "which", lambda _name: None)
    with pytest.raises(SystemExit, match="ImageMagick not found"):
        md_art_convert.image_size(Path("x.png"))


def test_md_pixels_match_names_imagemagick_when_compare_is_missing(monkeypatch):
    monkeypatch.setattr(
        md_art_convert.shutil,
        "which",
        lambda name: "/usr/bin/convert" if name == "convert" else None,
    )
    with pytest.raises(SystemExit, match="ImageMagick not found"):
        md_art_convert.pixels_match(Path("a.png"), Path("b.png"))


def test_image_size_uses_magick_identify_subcommand(monkeypatch):
    monkeypatch.setattr(
        md_art_convert.shutil,
        "which",
        lambda name: "/usr/bin/magick" if name == "magick" else None,
    )
    recorded = {}

    def fake_run(argv, **_kwargs):
        recorded["argv"] = argv
        return SimpleNamespace(stdout="10 20")

    monkeypatch.setattr(md_art_convert.subprocess, "run", fake_run)
    assert md_art_convert.image_size(Path("x.png")) == (10, 20)
    assert recorded["argv"][:3] == ["/usr/bin/magick", "identify", "-format"]


def test_pixels_match_uses_magick_compare(monkeypatch):
    executables = {"magick": "/usr/bin/magick"}
    monkeypatch.setattr(md_art_convert.shutil, "which", executables.get)
    calls = []

    def fake_run(argv, **_kwargs):
        calls.append(argv)
        return SimpleNamespace(stderr="0")

    monkeypatch.setattr(md_art_convert.subprocess, "run", fake_run)
    assert md_art_convert.pixels_match(Path("a.png"), Path("b.png"))
    assert calls[0][:2] == ["/usr/bin/magick", "compare"]


def test_pixels_match_uses_compare_binary(monkeypatch):
    def which(name):
        return {"convert": "/usr/bin/convert", "compare": "/usr/bin/compare"}.get(name)

    monkeypatch.setattr(md_art_convert.shutil, "which", which)
    recorded = {}

    def fake_run(argv, **_kwargs):
        recorded["argv"] = argv
        return SimpleNamespace(stderr="0.0")

    monkeypatch.setattr(md_art_convert.subprocess, "run", fake_run)
    assert md_art_convert.pixels_match(Path("a.png"), Path("b.png"))
    assert recorded["argv"][0] == "/usr/bin/compare"


def test_fixed_size_counts_a_verify_mismatch(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(md_art_convert, "image_size", lambda _path: (2, 2))
    monkeypatch.setattr(md_art_convert, "write_dds", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(md_art_convert, "pixels_match", lambda *_args, **_kwargs: False)
    src = tmp_path / "x.png"
    src.write_bytes(b"x")
    failures = md_art_convert.convert_fixed_size(
        [src], tmp_path / "out", [(2, 2)], resize=False, verify=True
    )
    assert failures == 1
    assert "does not match its source" in capsys.readouterr().out


def test_fixed_size_skips_disallowed_dimensions(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(md_art_convert, "image_size", lambda _path: (3, 3))
    src = tmp_path / "odd.png"
    src.write_bytes(b"x")
    failures = md_art_convert.convert_fixed_size(
        [src], tmp_path / "out", [(2, 2)], resize=False, verify=False
    )
    assert failures == 1
    assert "SKIP" in capsys.readouterr().out


def test_flag_conversion_notes_a_resize_and_counts_verify_failures(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(md_art_convert, "write_tga", lambda *_args, **_kwargs: None)
    src = tmp_path / "flag.png"
    src.write_bytes(b"x")

    monkeypatch.setattr(md_art_convert, "image_size", lambda _path: (10, 10))
    assert (
        md_art_convert.convert_flag(src, "TST", tmp_path / "flags", verify=False) == 0
    )
    assert "resizing to 82x52" in capsys.readouterr().out

    monkeypatch.setattr(md_art_convert, "image_size", lambda _path: (82, 52))
    monkeypatch.setattr(md_art_convert, "pixels_match", lambda *_args, **_kwargs: False)
    failures = md_art_convert.convert_flag(src, "TST", tmp_path / "flags", verify=True)
    assert failures == 1
    assert "does not match its source" in capsys.readouterr().out


@requires_imagemagick
def test_md_converts_real_pillow_image_to_dds_and_tga(tmp_path):
    source = tmp_path / "source.png"
    _image(
        source,
        (2, 2),
        {
            (0, 0): (255, 0, 0, 255),
            (1, 0): (0, 255, 0, 255),
            (0, 1): (0, 0, 255, 255),
            (1, 1): (255, 255, 0, 255),
        },
    )
    assert md_art_convert.image_size(source) == (2, 2)

    dds = tmp_path / "converted.dds"
    md_art_convert.write_dds(source, dds, (2, 2), resize=False)
    assert dds.is_file()
    assert md_art_convert.image_size(dds) == (2, 2)

    same_size_tga = tmp_path / "same-size.tga"
    md_art_convert.write_tga(source, same_size_tga, (2, 2), resize=False)
    with Image.open(same_size_tga) as converted:
        assert converted.size == (2, 2)

    resize_source = tmp_path / "resize-source.png"
    _image(
        resize_source,
        (2, 2),
        {
            (0, 0): (255, 0, 0, 255),
            (1, 0): (255, 0, 0, 255),
            (0, 1): (255, 0, 0, 255),
            (1, 1): (255, 0, 0, 255),
        },
    )
    tga = tmp_path / "converted.tga"
    md_art_convert.write_tga(resize_source, tga, (1, 1), resize=True)
    assert md_art_convert.image_size(tga) == (1, 1)
    data = tga.read_bytes()
    header = md_art_convert.TGA_HEADER.unpack_from(data)
    id_length, color_map_length, color_map_depth = header[0], header[4], header[5]
    pixel_start = (
        md_art_convert.TGA_HEADER.size
        + id_length
        + color_map_length * (color_map_depth // 8)
    )
    assert header[10] == 32
    assert header[11] & md_art_convert.TGA_TOP_LEFT == 0
    assert data[pixel_start : pixel_start + 4] == b"\x00\x00\xff\xff"

    different = tmp_path / "different.png"
    _image(different, (2, 2), {(0, 0): (0, 0, 0, 255)})
    assert md_art_convert.pixels_match(source, source)
    assert not md_art_convert.pixels_match(source, different)


@requires_imagemagick
def test_md_fixed_size_and_flag_conversions_report_validation(tmp_path):
    good = tmp_path / "good.png"
    bad = tmp_path / "bad.png"
    _image(good, (2, 2), {})
    _image(bad, (3, 3), {})
    output = tmp_path / "dds"

    failures = md_art_convert.convert_fixed_size(
        [good, bad], output, [(2, 2)], resize=False, verify=True
    )
    assert failures == 1
    assert (output / "good.dds").is_file()
    assert not (output / "bad.dds").exists()

    assert (
        md_art_convert.convert_fixed_size(
            [bad], output, [(2, 2)], resize=True, verify=False
        )
        == 0
    )
    assert md_art_convert.image_size(output / "bad.dds") == (2, 2)

    source = tmp_path / "flag.png"
    _image(source, (2, 2), {(0, 0): (10, 20, 30, 255)})
    flags = tmp_path / "flags"
    assert md_art_convert.convert_flag(source, "TST", flags, verify=False) == 0
    for subdir, size in md_art_convert.FLAG_SIZES.items():
        with Image.open(flags / subdir / "TST.tga") as flag:
            assert flag.size == size


@requires_imagemagick
def test_md_main_parses_conversion_commands_and_returns_status(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    _image(source, (2, 2), {})
    output = tmp_path / "out"

    monkeypatch.setattr(
        sys,
        "argv",
        ["md_art_convert.py", "event", str(source), "--out-dir", str(output)],
    )
    assert md_art_convert.main() == 1

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "md_art_convert.py",
            "event",
            str(source),
            "--out-dir",
            str(output),
            "--resize",
            "--no-verify",
        ],
    )
    assert md_art_convert.main() == 0

    portrait_output = tmp_path / "portraits"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "md_art_convert.py",
            "portrait",
            str(source),
            "--out-dir",
            str(portrait_output),
            "--resize",
            "--no-verify",
        ],
    )
    assert md_art_convert.main() == 0

    flags = tmp_path / "flag-output"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "md_art_convert.py",
            "flag",
            str(source),
            "--name",
            "ABC",
            "--flags-dir",
            str(flags),
            "--no-verify",
        ],
    )
    assert md_art_convert.main() == 0
    assert (flags / "small" / "ABC.tga").is_file()


def test_md_tga_normalisation_handles_valid_and_invalid_data(tmp_path):
    image = Image.new("RGB", (2, 2))
    image.putdata([(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)])
    original = _top_left_tga(image, tail=b"trailer")
    normalised = md_art_convert.tga_normalised(original)

    assert normalised is not None
    assert (
        normalised[: md_art_convert.TGA_HEADER.size]
        != original[: md_art_convert.TGA_HEADER.size]
    )
    assert normalised[17] & md_art_convert.TGA_TOP_LEFT == 0
    start = md_art_convert.TGA_HEADER.size
    stride = 2 * 3
    assert (
        normalised[start : start + stride]
        == original[start + stride : start + 2 * stride]
    )
    assert normalised[-7:] == b"trailer"
    assert md_art_convert.tga_normalised(normalised) is None
    assert md_art_convert.tga_normalised(b"short") is None

    compressed = _top_left_tga(image, datatype=10)
    malformed = _top_left_tga(image)[:-3]
    assert md_art_convert.tga_normalised(compressed) is None
    assert md_art_convert.tga_normalised(malformed) is None
    zero_stride = md_art_convert.TGA_HEADER.pack(
        0, 0, 2, 0, 0, 0, 0, 0, 0, 1, 24, md_art_convert.TGA_TOP_LEFT
    )
    assert md_art_convert.tga_normalised(zero_stride) is None

    root = tmp_path / "nested"
    valid_path = root / "valid.tga"
    compressed_path = root / "compressed.tga"
    malformed_path = root / "malformed.tga"
    unchanged_path = root / "unchanged.tga"
    for path, data in (
        (valid_path, original),
        (compressed_path, compressed),
        (malformed_path, malformed),
        (unchanged_path, normalised),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    assert md_art_convert.normalise_dir(root, check_only=True) == (1, 2)
    assert valid_path.read_bytes() == original
    assert md_art_convert.normalise_dir(root, check_only=False) == (1, 2)
    assert valid_path.read_bytes() == normalised


def test_md_normalise_cli_success_and_failure_paths(tmp_path, monkeypatch):
    image = Image.new("RGB", (1, 1), (1, 2, 3))
    path = tmp_path / "one.tga"
    path.write_bytes(_top_left_tga(image))
    argv = ["md_art_convert.py", "normalise", str(tmp_path), "--check"]
    monkeypatch.setattr(sys, "argv", argv)
    assert md_art_convert.main() == 1
    assert path.read_bytes()[17] & md_art_convert.TGA_TOP_LEFT

    monkeypatch.setattr(sys, "argv", argv[:-1])
    assert md_art_convert.main() == 0
    assert not path.read_bytes()[17] & md_art_convert.TGA_TOP_LEFT

    monkeypatch.setattr(sys, "argv", argv)
    assert md_art_convert.main() == 0

    monkeypatch.setattr(sys, "argv", ["md_art_convert.py"])
    with pytest.raises(SystemExit):
        md_art_convert.main()


def test_state_merge_provinces_uses_pillow_pixels(tmp_path):
    source = tmp_path / "provinces.bmp"
    _image(
        source,
        (3, 2),
        {(0, 0): (10, 20, 30), (2, 1): (40, 50, 60)},
        mode="RGB",
    )
    merged = state_gfx.merge_provinces(source, {"#0a141e", "#28323c"}, "#ffffff")
    assert merged.mode == "RGB"
    assert merged.getpixel((0, 0)) == (255, 255, 255)
    assert merged.getpixel((2, 1)) == (255, 255, 255)
    assert merged.getpixel((1, 0)) == (0, 0, 0)
    assert state_gfx.rgb_to_hex((1, 2, 255)) == "#0102ff"


def _configure_state_module(root, monkeypatch, desktop=None):
    """Create the map/history tree state_gfx reads and point the module at it."""
    states = root / "history" / "states"
    states.mkdir(parents=True, exist_ok=True)
    definition = root / "map" / "definition.csv"
    bitmap = root / "map" / "provinces.bmp"
    definition.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(state_gfx, "REPO_ROOT", str(root))
    monkeypatch.setattr(state_gfx, "states_dir", str(states))
    monkeypatch.setattr(state_gfx, "definition_file", str(definition))
    monkeypatch.setattr(state_gfx, "provinces_bmp", str(bitmap))
    if desktop is not None:
        monkeypatch.setattr(state_gfx, "desktop_path", str(desktop))
    return states, definition, bitmap


def _run_state_selection(monkeypatch, root, state_file):
    """Run state_gfx.main() over a one-province state whose color never matches."""
    states, definition, bitmap = _configure_state_module(
        root, monkeypatch, root / "Desktop"
    )
    _write_text(states / state_file, "provinces = { 1 }\n")
    _write_text(definition, "id;r;g;b\n1;1;2;3\n")
    _image(bitmap, (1, 1), {(0, 0): (99, 99, 99)}, mode="RGB")
    monkeypatch.setattr("builtins.input", _inputs("12", "1"))
    state_gfx.main()


def test_state_main_writes_scaled_selection_from_real_bitmap(tmp_path, monkeypatch):
    desktop = tmp_path / "Desktop"
    desktop.mkdir()
    states, definition, bitmap = _configure_state_module(tmp_path, monkeypatch, desktop)
    _write_text(
        states / "12-Test State.txt",
        "state = {\n\tprovinces = { 1 2 }\n}\n",
    )
    _write_text(
        definition,
        "id;r;g;b;name\n"
        "1;10;20;30;One\n"
        "2;40;50;60;Two\n"
        "bad\n"
        "not-an-id;1;2;3;Bad\n"
        "3;70;80;90;Other\n",
    )
    _image(
        bitmap,
        (4, 4),
        {(1, 1): (10, 20, 30), (2, 2): (40, 50, 60)},
        mode="RGB",
    )
    answers = iter(["12", "2"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    state_gfx.main()

    output = desktop / "test_state.png"
    assert output.is_file()
    with Image.open(output) as image:
        assert image.size == (4, 4)
        assert image.mode == "RGBA"
        assert image.getpixel((0, 0))[3] == 255
        assert image.getpixel((3, 3))[3] == 255


def test_state_main_reports_required_input_and_filesystem_errors(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    monkeypatch.setattr(state_gfx, "states_dir", str(missing))
    monkeypatch.setattr(state_gfx, "definition_file", str(missing / "definition.csv"))
    monkeypatch.setattr(state_gfx, "provinces_bmp", str(missing / "provinces.bmp"))
    with pytest.raises(SystemExit, match="required path not found"):
        state_gfx.main()

    states, definition, bitmap = _configure_state_module(tmp_path, monkeypatch)
    _write_text(states / "12-State.txt", "provinces = { 1 }\n")
    _write_text(definition, "id;r;g;b\n1;1;2;3\n")
    _image(bitmap, (1, 1), {(0, 0): (1, 2, 3)}, mode="RGB")
    monkeypatch.setattr("builtins.input", _inputs("12", "bad"))
    with pytest.raises(SystemExit, match="Scale must be an integer"):
        state_gfx.main()

    monkeypatch.setattr("builtins.input", _inputs("12", "1"))
    monkeypatch.setattr(
        state_gfx.os,
        "listdir",
        lambda _path: (_ for _ in ()).throw(OSError("no access")),
    )
    with pytest.raises(SystemExit, match="cannot list states"):
        state_gfx.main()

    monkeypatch.setattr(state_gfx.os, "listdir", lambda path: ["12-State.txt"])
    monkeypatch.setattr("builtins.input", _inputs("12", "1"))
    monkeypatch.setattr(
        state_gfx,
        "read_text_under",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("unreadable")),
    )
    with pytest.raises(SystemExit, match="cannot read state file"):
        state_gfx.main()

    def read_state_then_fail(path, *_args, **_kwargs):
        if path == str(states / "12-State.txt"):
            return _read_text(states / "12-State.txt")
        raise OSError("bad definition")

    monkeypatch.setattr(state_gfx, "read_text_under", read_state_then_fail)
    monkeypatch.setattr("builtins.input", _inputs("12", "1"))
    with pytest.raises(SystemExit, match="cannot read definition file"):
        state_gfx.main()


def test_state_main_handles_unparseable_name_and_empty_selection(
    tmp_path, monkeypatch, capsys
):
    _run_state_selection(monkeypatch, tmp_path, "12.txt")

    assert "Could not extract state name" in capsys.readouterr().out
    assert not (tmp_path / "Desktop").exists()


def test_state_main_skips_output_when_no_province_color_matches(tmp_path, monkeypatch):
    _run_state_selection(monkeypatch, tmp_path, "12-State.txt")

    assert not (tmp_path / "Desktop").exists()


def test_gfx_paths_scanning_and_block_parser_cover_recursive_inputs(tmp_path):
    scan = tmp_path / "scan"
    nested = scan / "nested"
    nested.mkdir(parents=True)
    for name in ("B.DDS", "a.png", "c.TgA", "ignored.jpg"):
        (nested / name).write_bytes(b"fixture")
    (scan / "not-an-image.txt").write_bytes(b"fixture")
    files = generator.scan_images(scan)
    assert [path.name for path in files] == ["a.png", "B.DDS", "c.TgA"]
    assert generator.rel_texture_path(files[0], tmp_path) == "scan/nested/a.png"
    assert generator.interface_path(tmp_path, "icons.gfx") == (
        tmp_path / "interface" / "icons.gfx"
    )

    seen = set()
    assert not generator.check_duplicate("GFX_a", seen, "a.png")
    assert generator.check_duplicate("GFX_a", seen, "other.png")

    parsed = list(
        generator._parse_named_blocks(
            _render("GFX_good", "gfx/good.dds")
            + '\tspriteType = {\n\t\tname = "GFX_no_texture"\n\t}\n'
            + '\tspriteType = {\n\t\ttexturefile = "gfx/no_name.dds"\n\t}\n'
            + "\tspriteType = {\n"
        )
    )
    assert [(name, texture) for name, texture, _start, _end in parsed] == [
        ("GFX_good", "gfx/good.dds"),
        ("GFX_no_texture", None),
        (None, "gfx/no_name.dds"),
    ]
    assert generator._match_brace("{ nested { value } }", 0) == 19
    with pytest.raises(ValueError, match="Unmatched"):
        generator._match_brace("{", 0)

    assert generator._format_names(["b", "a"], cap=3) == "a, b"
    assert generator._format_names([str(i) for i in range(4)], cap=2).endswith(
        "+2 more"
    )


def test_gfx_merge_reports_changes_orphans_protection_and_newlines(tmp_path, capsys):
    path = tmp_path / "entries.gfx"
    _write_text(
        path,
        (
            "spriteTypes = {\r\n"
            + _render("GFX_change", "old.dds").replace("\n", "\r\n")
            + _render("GFX_orphan", "orphan.dds").replace("\n", "\r\n")
            + _render("GFX_protected", "external.dds").replace("\n", "\r\n")
            + "}\r\n"
        ),
    )
    entries = {
        "GFX_change": "new.dds",
        "GFX_new": "new-entry.dds",
        "GFX_protected": "local.dds",
    }
    result = generator.merge_gfx_entries(
        path, entries, _render, protected=frozenset({"GFX_protected"})
    )
    assert result[:4] == (["GFX_new"], ["GFX_change"], ["GFX_orphan"], [])
    assert result[4] is True
    text = _read_text(path)
    assert "new.dds" in text and "old.dds" not in text
    assert "external.dds" in text and "local.dds" not in text
    assert "GFX_orphan" in text
    raw = path.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")

    second = generator.merge_gfx_entries(
        path, entries, _render, protected=frozenset({"GFX_protected"})
    )
    assert second[4] is False

    generator._print_merge_report(
        "entries.gfx",
        ["new"],
        ["changed"],
        ["orphan"],
        ["duplicate"],
        True,
        [("duplicate", "kept", "dropped")],
    )
    report = capsys.readouterr().out
    assert "TEXTURE MISMATCH" in report and "already up to date" not in report
    generator._print_merge_report("entries.gfx", [], [], [], [], False)
    assert "already up to date" in capsys.readouterr().out


def test_gfx_low_level_error_and_region_helpers(tmp_path, capsys):
    assert generator._read_lf(tmp_path / "missing.gfx") == ""
    assert generator._newline_of("line\r\n") == "\r\n"
    assert generator._newline_of("line\n") == "\n"
    assert generator._remove_block_by_name('name = "GFX_a"', "GFX_a")[1] is False
    assert (
        generator._remove_block_by_name('spriteType = { name = "GFX_a"', "GFX_a")[1]
        is False
    )
    assert generator._strip_region("before\nafter", "BEGIN", "END") == "before\nafter"
    assert generator._strip_region("before\nBEGIN\nbody", "BEGIN", "END") == "before\n"
    assert generator._extract_manual_body("no markers") == ""
    assert generator._extract_manual_body(f"{generator.SG_MANUAL_BEGIN}\nbody") == ""
    assert (
        generator._remove_tag_headers("### keep ###\n### remove ###", ["remove"])
        == "### keep ###"
    )
    assert generator._collapse_blanks("a\n\n\n\nb") == "a\n\nb"

    bad_target = tmp_path / "directory"
    bad_target.mkdir()
    generator._write_with_newline(bad_target, "text", "\n")
    assert "Failed to write" in capsys.readouterr().out


def test_gfx_goals_scans_recursively_and_deduplicates(tmp_path):
    (tmp_path / "interface").mkdir()
    goals = tmp_path / "gfx" / "interface" / "goals"
    (goals / "nested").mkdir(parents=True)
    (goals / "alpha.dds").write_bytes(b"fixture")
    (goals / "nested" / "alpha.png").write_bytes(b"fixture")
    (goals / "nested" / "gamma.png").write_bytes(b"fixture")
    (goals / "beta.tga").write_bytes(b"fixture")

    generator.generate_goals(tmp_path, gfxbool=1)

    output = _read_text(tmp_path / "interface" / "goals.gfx")
    shine = _read_text(tmp_path / "interface" / "goals_shine.gfx")
    assert 'name = "GFX_alpha"' in output
    assert output.count('name = "GFX_alpha"') == 1
    assert "gfx/interface/goals/nested/gamma.png" in output
    assert 'name = "GFX_gamma_shine"' in shine
    assert 'name = "GFX_beta_shine"' in shine
    assert 'effectfile = "gfx/FX/buttonstate.lua"' in shine


def test_gfx_goals_interactive_validation_and_event_names(
    tmp_path, monkeypatch, capsys
):
    (tmp_path / "interface").mkdir()
    goals = tmp_path / "gfx" / "interface" / "goals"
    goals.mkdir(parents=True)
    (goals / "goal.dds").write_bytes(b"fixture")
    answers = iter(["", "not a number", "4", "0"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    generator.generate_goals(tmp_path)
    assert 'name = "goal"' in _read_text(tmp_path / "interface" / "goals.gfx")
    assert "Input cannot be empty" in capsys.readouterr().out

    event = tmp_path / "gfx" / "event_pictures"
    (event / "nested").mkdir(parents=True)
    (event / "plain.dds").write_bytes(b"fixture")
    (event / "nested" / "GFX_existing.png").write_bytes(b"fixture")
    (event / "nested" / "GFX_existing.tga").write_bytes(b"fixture")
    generator.generate_event_pictures(tmp_path)
    output = _read_text(tmp_path / "interface" / "MD_eventpictures.gfx")
    assert 'name = "GFX_plain"' in output
    assert output.count('name = "GFX_existing"') == 1


def test_gfx_ideas_parties_intelligence_and_decisions_naming(tmp_path):
    (tmp_path / "interface").mkdir()
    ideas = tmp_path / "gfx" / "interface" / "ideas"
    ideas.mkdir(parents=True)
    for name in ("idea_reform.dds", "reform.png", "traits_strip.dds"):
        (ideas / name).write_bytes(b"fixture")
    generator.generate_ideas(tmp_path)
    ideas_text = _read_text(tmp_path / "interface" / "MD_ideas.gfx")
    assert 'name = "GFX_idea_reform"' in ideas_text
    assert ideas_text.count('name = "GFX_idea_traits_strip"') == 1

    parties = tmp_path / "gfx" / "texticons" / "parties_icons"
    parties.mkdir(parents=True)
    (parties / "social_democrat.dds").write_bytes(b"fixture")
    generator.generate_party_icons(tmp_path)
    assert 'name = "GFX_social_democrat"' in _read_text(
        tmp_path / "interface" / "MD_parties_icons.gfx"
    )

    agencies = tmp_path / "gfx" / "interface" / "operatives" / "agencies"
    agencies.mkdir(parents=True)
    (agencies / "agency_logo_PER.dds").write_bytes(b"fixture")
    (agencies / "GER.png").write_bytes(b"fixture")
    generator.generate_intelligence_icons(tmp_path)
    agency_text = _read_text(tmp_path / "interface" / "MD_intelligence_icons.gfx")
    assert 'name = "GFX_intelligence_agency_logo_PER"' in agency_text
    assert 'name = "GFX_intelligence_agency_logo_GER"' in agency_text

    decisions = tmp_path / "gfx" / "interface" / "decisions"
    (decisions / "country" / "decision_text").mkdir(parents=True)
    (decisions / "regular").mkdir(parents=True)
    (decisions / "country" / "decision_text" / "war.dds").write_bytes(b"fixture")
    (decisions / "regular" / "decision_category_reform.png").write_bytes(b"fixture")
    (decisions / "regular" / "trade.tga").write_bytes(b"fixture")
    generator.generate_decisions(tmp_path)
    decisions_text = _read_text(tmp_path / "interface" / "MD_decisions.gfx")
    assert 'name = "GFX_decision_trade"' in decisions_text
    assert 'name = "GFX_decision_category_reform"' in decisions_text
    assert "GFX_decision_war" not in decisions_text

    generator.generate_decisions_desc(tmp_path)
    desc_text = _read_text(tmp_path / "interface" / "MD_decisions_desc.gfx")
    assert 'name = "GFX_war"' in desc_text
    assert "legacy_lazy_load = no" in desc_text


def test_gfx_modifier_icons_preserve_external_and_existing_names(tmp_path):
    icons = tmp_path / "gfx" / "texticons" / "modifier_icons"
    icons.mkdir(parents=True)
    (icons / "air_cost.dds").write_bytes(b"fixture")
    (icons / "anti_air_texticon.png").write_bytes(b"fixture")
    out = tmp_path / "interface" / "modifiericons_texticons.gfx"
    _write_text(
        out,
        "spriteTypes = {\n"
        + _render("GFX_AirCost_texticon", "gfx/texticons/modifier_icons/air_cost.dds")
        + _render("GFX_anti_air_texticon", "gfx/vanilla/role.dds")
        + "}\n",
    )

    generator.generate_modifier_icons(tmp_path)

    text = _read_text(out)
    assert 'name = "GFX_AirCost_texticon"' in text
    assert 'name = "GFX_air_cost"' not in text
    assert 'texturefile = "gfx/vanilla/role.dds"' in text
    assert text.count('name = "GFX_anti_air_texticon"') == 1


def test_gfx_scripted_gui_preserves_manual_region_and_crlf(tmp_path, capsys):
    (tmp_path / "interface").mkdir()
    countries = tmp_path / "gfx" / "interface" / "scripted_gui" / "countries"
    (countries / "PER" / "_manual").mkdir(parents=True)
    (countries / "ALG").mkdir(parents=True)
    (countries / "EMPTY").mkdir(parents=True)
    (countries / "PER" / "z.dds").write_bytes(b"fixture")
    (countries / "PER" / "_manual" / "skip.png").write_bytes(b"fixture")
    (countries / "ALG" / "z.png").write_bytes(b"fixture")
    (countries / "ALG" / "a.tga").write_bytes(b"fixture")

    generator.generate_scripted_gui(tmp_path)
    out = tmp_path / "interface" / "MD_scripted_gui.gfx"
    initial = _read_text(out)
    assert 'name = "GFX_z"' in initial
    assert initial.count('name = "GFX_z"') == 1
    assert 'name = "GFX_a"' in initial
    assert "skip" not in initial

    manual = initial.replace(
        "\t# === END MANUAL ===",
        '\tprogressbartype = {\n\t\tname = "GFX_manual"\n\t}\n\t# === END MANUAL ===',
    )
    _write_text(out, manual.replace("\n", "\r\n"))
    generator.generate_scripted_gui(tmp_path)
    assert "GFX_manual" in _read_text(out)
    raw = out.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")
    assert "already up to date" in capsys.readouterr().out


def _focus_fixture(root):
    titlebar = root / "gfx" / "interface" / "focusview" / "titlebar"
    titlebar.mkdir(parents=True)
    for state, suffix in (
        ("unavailable", "alpha"),
        ("can_start", "alpha"),
        ("completed", "alpha"),
        ("can_start", "beta"),
        ("unavailable", "gamma"),
    ):
        (titlebar / f"focus_{state}_joint_{suffix}_bg.dds").write_bytes(b"fixture")
    (root / "interface").mkdir(parents=True)
    (root / "common" / "national_focus").mkdir(parents=True)
    gfx = (
        "spriteTypes = {\n"
        "\t# comment before generated content\n"
        + _render(
            "GFX_focus_unavailable_joint_alpha",
            "gfx/interface/focusview/titlebar/focus_unavailable_joint_alpha_bg.dds",
        )
        + _render(
            "GFX_focus_can_start_joint_epsilon",
            "gfx/interface/focusview/titlebar/focus_can_start_joint_epsilon_bg.dds",
        )
        + _render(
            "GFX_focus_current_joint_epsilon",
            "gfx/interface/focusview/titlebar/focus_can_start_joint_epsilon_bg.dds",
        )
        + _render("GFX_focus_can_start_joint_delta", "gfx/hand/custom.dds")
        + "\t### alpha ###\n"
        + f"{generator.GFX_BEGIN}\nold generated\n{generator.GFX_END}\n"
        + "}\n"
    )
    styles = (
        "style = {\n"
        "\tname = JOINT_alpha_focus_style\n"
        "\tavailable = GFX_focus_can_start_joint_alpha\n"
        "}\n"
        f"{generator.STYLE_BEGIN}\nold styles\n{generator.STYLE_END}\n"
    )
    _write_text(root / "interface" / "nationalfocusview.gfx", gfx.replace("\n", "\r\n"))
    _write_text(
        root / "common" / "national_focus" / "00_titlebar_styles.txt",
        styles.replace("\n", "\r\n"),
    )


def test_gfx_focus_titlebars_generate_incomplete_sets_and_styles(tmp_path, capsys):
    _focus_fixture(tmp_path)
    generator.generate_focus_titlebars(tmp_path)

    gfx = tmp_path / "interface" / "nationalfocusview.gfx"
    styles = tmp_path / "common" / "national_focus" / "00_titlebar_styles.txt"
    output = _read_text(gfx)
    style_output = _read_text(styles)
    assert 'name = "GFX_focus_unavailable_joint_alpha"' in output
    assert 'name = "GFX_focus_current_joint_alpha"' in output
    assert "GFX_focus_unavailable_joint_beta" not in output
    assert 'name = "GFX_focus_current_joint_beta"' in output
    assert "GFX_focus_can_start_joint_delta" in output
    assert "GFX_focus_unavailable_joint_gamma" not in output
    assert "JOINT_beta_focus_style" in style_output
    assert "JOINT_epsilon_focus_style" in style_output
    assert output.count(generator.GFX_BEGIN) == 1
    assert "Incomplete sets" in capsys.readouterr().out

    generator.generate_focus_titlebars(tmp_path)
    assert "0 new style(s) added" in capsys.readouterr().out

    for path in (gfx, styles):
        raw = path.read_bytes()
        assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")


def test_gfx_generators_report_missing_source_directories(tmp_path, capsys):
    checks = (
        (generator.generate_goals, "Directory does not exist"),
        (generator.generate_event_pictures, "Directory does not exist"),
        (generator.generate_ideas, "Directory does not exist"),
        (generator.generate_party_icons, "Directory does not exist"),
        (generator.generate_intelligence_icons, "Directory does not exist"),
        (generator.generate_decisions, "Directory does not exist"),
        (generator.generate_decisions_desc, "Directory does not exist"),
        (generator.generate_modifier_icons, "Directory does not exist"),
        (generator.generate_scripted_gui, "Directory does not exist"),
        (generator.generate_focus_titlebars, "Titlebar directory not found"),
    )
    for function, message in checks:
        function(tmp_path)
        assert message in capsys.readouterr().out

    titlebar = tmp_path / "gfx" / "interface" / "focusview" / "titlebar"
    titlebar.mkdir(parents=True)
    generator.generate_focus_titlebars(tmp_path)
    assert "Missing file" in capsys.readouterr().out

    (tmp_path / "interface").mkdir(parents=True)
    (tmp_path / "interface" / "nationalfocusview.gfx").write_bytes(b"{}")
    generator.generate_focus_titlebars(tmp_path)
    assert "Missing file" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("selection", "function_name"),
    [
        (str(number), name)
        for number, name in enumerate(
            (
                "generate_goals",
                "generate_event_pictures",
                "generate_ideas",
                "generate_party_icons",
                "generate_intelligence_icons",
                "generate_decisions",
                "generate_focus_titlebars",
                "generate_scripted_gui",
                "generate_decisions_desc",
                "generate_modifier_icons",
            ),
            start=1,
        )
    ],
)
def test_gfx_main_dispatches_each_command(selection, function_name, monkeypatch):
    calls = []
    monkeypatch.setattr(generator, function_name, lambda root: calls.append(root))
    monkeypatch.setattr("builtins.input", lambda _prompt: selection)
    generator.main()
    assert calls == [ROOT]


def test_gfx_main_rejects_invalid_input_before_dispatch(monkeypatch, capsys):
    answers = iter(["", "not numeric", "0", "11", "2"])
    calls = []
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(
        generator, "generate_event_pictures", lambda root: calls.append(root)
    )

    generator.main()

    output = capsys.readouterr().out
    assert "Input cannot be empty" in output
    assert "Invalid input" in output
    assert "Invalid selection" in output
    assert calls == [ROOT]
