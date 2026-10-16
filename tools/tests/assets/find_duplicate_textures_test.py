"""Deterministic tests for tools/assets/find_duplicate_textures.py.

Covers the .gfx file walker, the texturefile regex extraction (with line
numbers and exception swallowing), goals_shine / Modding resources exclusion,
the duplicate grouping, the formatted output (empty + populated, with and
without an output stream), and the CLI which writes a timestamped report file.
"""

import io
import sys
from pathlib import Path

import pytest
from shared.suite import load_tool_module

fdt = load_tool_module("assets/find_duplicate_textures.py")


def _write_gfx(root, name, body):
    target = Path(root) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


# --- find_gfx_files -------------------------------------------------------


def test_find_gfx_files_walks_recursively(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "x.gfx").write_text("//")
    (tmp_path / "a" / "b" / "y.gfx").write_text("//")
    (tmp_path / "ignore.txt").write_text("//")
    files = fdt.find_gfx_files(str(tmp_path))
    assert sorted(Path(p).name for p in files) == ["x.gfx", "y.gfx"]


# --- extract_texture_definitions ------------------------------------------


def test_extract_texture_definitions_returns_path_line_and_match(tmp_path):
    body = (
        "spriteTypes = {\n"
        "    spriteType = {\n"
        '        name = "GFX_one"\n'
        '        textureFile = "gfx/one.dds"\n'
        "    }\n"
        "}\n"
    )
    path = _write_gfx(tmp_path, "test.gfx", body)
    defs = fdt.extract_texture_definitions(str(path))
    assert len(defs) == 1
    d = defs[0]
    assert d["texture_path"] == "gfx/one.dds"
    assert d["line_number"] == 4
    assert d["file"] == str(path)
    assert "textureFile" in d["full_match"]


def test_extract_texture_definitions_swallows_read_errors(tmp_path, capsys):
    # A missing file raises inside open(); extract catches it, logs to stdout,
    # and returns an empty list (does not propagate).
    defs = fdt.extract_texture_definitions("/this/path/is/missing.gfx")
    assert defs == []
    out = capsys.readouterr().out
    assert "Error reading" in out


def test_extract_texture_definitions_handles_multiple_texturefile_per_file(tmp_path):
    body = (
        'spriteType = { name = "GFX_a" textureFile = "gfx/shared.dds" }\n'
        'spriteType = { name = "GFX_b" textureFile = "gfx/shared.dds" }\n'
        'spriteType = { name = "GFX_c" textureFile = "gfx/other.dds" }\n'
    )
    path = _write_gfx(tmp_path, "multi.gfx", body)
    defs = fdt.extract_texture_definitions(str(path))
    paths = [d["texture_path"] for d in defs]
    assert paths.count("gfx/shared.dds") == 2
    assert paths.count("gfx/other.dds") == 1


# --- find_duplicate_textures ----------------------------------------------


def test_find_duplicate_textures_skips_goals_shine_and_modding_resources(
    tmp_path, capsys
):
    _write_gfx(
        tmp_path,
        "goals_shine.gfx",
        'spriteType = { name = "GFX_a" textureFile = "gfx/dup.dds" }\n',
    )
    _write_gfx(
        tmp_path,
        "Modding resources/test.gfx",
        'spriteType = { name = "GFX_b" textureFile = "gfx/dup.dds" }\n',
    )
    _write_gfx(
        tmp_path,
        "interface/test.gfx",
        'spriteType = { name = "GFX_c" textureFile = "gfx/dup.dds" }\n',
    )

    dupes = fdt.find_duplicate_textures(str(tmp_path))
    # goals_shine.gfx and "Modding resources" are skipped, so only one
    # definition of gfx/dup.dds survives — no duplicates reported.
    assert dupes == {}


def test_find_duplicate_textures_groups_by_texture_path(tmp_path):
    _write_gfx(
        tmp_path,
        "a.gfx",
        'spriteType = { name = "GFX_a1" textureFile = "gfx/x.dds" }\n',
    )
    _write_gfx(
        tmp_path,
        "b.gfx",
        'spriteType = { name = "GFX_b1" textureFile = "gfx/x.dds" }\n',
    )
    _write_gfx(
        tmp_path,
        "c.gfx",
        'spriteType = { name = "GFX_c1" textureFile = "gfx/unique.dds" }\n',
    )

    dupes = fdt.find_duplicate_textures(str(tmp_path))
    assert set(dupes) == {"gfx/x.dds"}
    assert len(dupes["gfx/x.dds"]) == 2


def test_find_duplicate_textures_no_results_returns_empty(tmp_path):
    _write_gfx(
        tmp_path, "a.gfx", 'spriteType = { name = "GFX_a" textureFile = "gfx/a.dds" }\n'
    )
    _write_gfx(
        tmp_path, "b.gfx", 'spriteType = { name = "GFX_b" textureFile = "gfx/b.dds" }\n'
    )
    dupes = fdt.find_duplicate_textures(str(tmp_path))
    assert dupes == {}


def test_find_duplicate_textures_walks_through_ioerror_in_one_file(
    tmp_path, monkeypatch, capsys
):
    _write_gfx(
        tmp_path, "good.gfx", 'spriteType = { name = "G" textureFile = "gfx/g.dds" }\n'
    )
    real_extract = fdt.extract_texture_definitions

    def maybe_fail(path):
        if path.endswith("bad.gfx"):
            return []
        return real_extract(path)

    monkeypatch.setattr(fdt, "extract_texture_definitions", maybe_fail)
    dupes = fdt.find_duplicate_textures(str(tmp_path))
    assert "gfx/g.dds" not in dupes


# --- print_results --------------------------------------------------------


def test_print_results_empty_writes_to_optional_output(capsys):
    buf = io.StringIO()
    fdt.print_results({}, output_file=buf)
    captured = capsys.readouterr().out
    buf_text = buf.getvalue()
    assert "No duplicate texture definitions found!" in captured
    assert "No duplicate texture definitions found!" in buf_text


def test_print_results_uses_optional_output_stream(capsys):
    buf = io.StringIO()
    dupes = {
        "gfx/dup.dds": [
            {
                "file": "/root/interface/a.gfx",
                "texture_path": "gfx/dup.dds",
                "line_number": 7,
                "full_match": 'textureFile = "gfx/dup.dds"',
            },
            {
                "file": "/root/interface/b.gfx",
                "texture_path": "gfx/dup.dds",
                "line_number": 14,
                "full_match": 'textureFile = "gfx/dup.dds"',
            },
        ]
    }
    fdt.print_results(dupes, output_file=buf)
    captured = capsys.readouterr().out
    joined = buf.getvalue()
    for haystack in (captured, joined):
        assert "Found 1 textures" in haystack
        assert "gfx/dup.dds" in haystack
        assert "Found 2 definitions" in haystack
        assert str(Path("interface") / "a.gfx") in haystack
        assert "Line: 7" in haystack
        assert "Line: 14" in haystack


# --- main() ---------------------------------------------------------------


def test_main_writes_timestamped_report_and_prints_results(
    tmp_path, monkeypatch, capsys
):
    _write_gfx(
        tmp_path,
        "a.gfx",
        'spriteType = { name = "GFX_a" textureFile = "gfx/x.dds" }\n',
    )
    _write_gfx(
        tmp_path,
        "b.gfx",
        'spriteType = { name = "GFX_b" textureFile = "gfx/x.dds" }\n',
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["find_duplicate_textures.py", str(tmp_path)])
    fdt.main()

    reports = list(tmp_path.glob("duplicate_textures_report_*.txt"))
    assert reports, "expected the report file to be created in cwd"
    text = reports[0].read_text(encoding="utf-8")
    assert "Found 1 textures with duplicate definitions" in text
    assert "2 total texture definitions" in text
    # Summary block also written.
    assert "1 unique textures have duplicates" in text
    # CLI also echoes to stdout.
    out = capsys.readouterr().out
    assert "Search completed!" in out


def test_main_with_no_duplicates_writes_clean_report(tmp_path, monkeypatch, capsys):
    _write_gfx(
        tmp_path,
        "a.gfx",
        'spriteType = { name = "GFX_a" textureFile = "gfx/a.dds" }\n',
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["find_duplicate_textures.py", str(tmp_path)])
    fdt.main()
    reports = list(tmp_path.glob("duplicate_textures_report_*.txt"))
    assert reports and "No duplicate" in reports[0].read_text(encoding="utf-8")
    assert "No duplicate texture definitions found!" in capsys.readouterr().out


def test_main_exits_nonzero_on_missing_directory(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["find_duplicate_textures.py", "/no/such/dir/here"]
    )
    with pytest.raises(SystemExit):
        fdt.main()
