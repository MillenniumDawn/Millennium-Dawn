"""Tests for tools/assets/generate_background_thumbnails.py against a temp tree.

Covers entry parsing (comments, nesting, duplicates), the implicit
GFX_frontend_bg tile, DXT1 output shape, byte-stable reruns, --check staleness,
and the reported-not-fatal problem paths (missing, undecodable, orphaned art).
"""

import struct

import pytest
from PIL import Image
from shared.suite import load_tool_module, read_text, write_under

gbt = load_tool_module("assets/generate_background_thumbnails.py")

BACKGROUNDS = "common/frontend/backgrounds/base_backgrounds.txt"
FRONTEND_BG = "interface/frontendmainviewbg.gfx"
GFX = "interface/small_background.gfx"


def _source(root, relative, color):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (16, 12), color).save(path, format="DDS")
    return path


def _tree(root, names, colors=None):
    write_under(root, BACKGROUNDS, "".join(f"{name} = {{ }}\n" for name in names))
    for index, name in enumerate(names):
        color = (colors or {}).get(name, (10 * index + 5, 40, 90, 255))
        _source(root, f"gfx/loadingscreens/{name}.dds", color)


def _dds_shape(path):
    header = path.read_bytes()[:128]
    flags, height, width, linear = struct.unpack("<4I", header[8:24])
    return flags, width, height, linear, header[84:88]


def _sprite_names(root):
    body = read_text(root / GFX)
    return [line.split('"')[1] for line in body.splitlines() if "name =" in line]


def test_generates_dxt1_thumbnails_and_gfx(tmp_path, capsys):
    _tree(tmp_path, ["load_1", "load_2"])

    assert gbt.main([], root=tmp_path) == 0

    for name in ("load_1", "load_2"):
        thumbnail = tmp_path / f"gfx/loadingscreens/{name}_small.dds"
        assert _dds_shape(thumbnail) == (0x81007, 192, 144, 13824, b"DXT1")
        assert thumbnail.stat().st_size == 128 + 13824
    assert _sprite_names(tmp_path) == [
        "GFX_load_1_small",
        "GFX_load_2_small",
        gbt.BORDER_SPRITE,
    ]
    assert gbt.BORDER_TEXTURE in read_text(tmp_path / GFX)
    assert "3 file(s) written, 2 background(s)" in capsys.readouterr().out
    assert gbt.main(["--check"], root=tmp_path) == 0
    assert "2 background thumbnails up to date" in capsys.readouterr().out


def test_rerun_is_byte_stable(tmp_path, capsys):
    _tree(tmp_path, ["load_1"])
    gbt.main([], root=tmp_path)
    before = (tmp_path / "gfx/loadingscreens/load_1_small.dds").read_bytes()
    capsys.readouterr()

    assert gbt.main([], root=tmp_path) == 0

    assert "0 file(s) written" in capsys.readouterr().out
    assert (tmp_path / "gfx/loadingscreens/load_1_small.dds").read_bytes() == before


def test_check_reports_replaced_art_and_writes_nothing(tmp_path, capsys):
    _tree(tmp_path, ["load_1"])
    gbt.main([], root=tmp_path)
    thumbnail = tmp_path / "gfx/loadingscreens/load_1_small.dds"
    before = thumbnail.read_bytes()
    _source(tmp_path, "gfx/loadingscreens/load_1.dds", (250, 250, 250, 255))

    assert gbt.main(["--check"], root=tmp_path) == 1

    assert "stale gfx/loadingscreens/load_1_small.dds" in capsys.readouterr().err
    assert thumbnail.read_bytes() == before
    assert gbt.main([], root=tmp_path) == 0
    assert thumbnail.read_bytes() != before
    assert gbt.main(["--check"], root=tmp_path) == 0


def test_missing_source_is_reported_and_others_still_generated(tmp_path, capsys):
    _tree(tmp_path, ["load_1"])
    write_under(tmp_path, BACKGROUNDS, "load_1 = { }\nload_2 = { }\n")

    assert gbt.main([], root=tmp_path) == 1

    assert "load_2: no gfx/loadingscreens/load_2.dds" in capsys.readouterr().err
    assert (tmp_path / "gfx/loadingscreens/load_1_small.dds").is_file()
    assert "GFX_load_2_small" not in _sprite_names(tmp_path)


def test_undecodable_source_is_reported_not_fatal(tmp_path, capsys):
    _tree(tmp_path, ["load_1", "load_bad"])
    (tmp_path / "gfx/loadingscreens/load_bad.dds").write_bytes(b"not a dds")

    assert gbt.main([], root=tmp_path) == 1

    assert "load_bad: cannot decode load_bad.dds" in capsys.readouterr().err
    assert (tmp_path / "gfx/loadingscreens/load_1_small.dds").is_file()
    assert not (tmp_path / "gfx/loadingscreens/load_bad_small.dds").exists()
    assert "GFX_load_bad_small" not in _sprite_names(tmp_path)


def test_orphan_thumbnail_is_reported(tmp_path, capsys):
    _tree(tmp_path, ["load_1"])
    (tmp_path / "gfx/loadingscreens/load_9_small.dds").write_bytes(b"x")

    assert gbt.main(["--check"], root=tmp_path) == 1

    assert "orphan gfx/loadingscreens/load_9_small.dds" in capsys.readouterr().err


def test_menu_background_tile_survives_key_order(tmp_path):
    _tree(tmp_path, ["load_1"])
    _source(tmp_path, "gfx/main_menu/menu.dds", (1, 2, 3, 255))
    write_under(
        tmp_path,
        FRONTEND_BG,
        "spriteTypes = {\n"
        "\tcorneredTileSpriteType = {\n"
        '\t\tname = "GFX_frontend_bg"\n'
        '\t\tsize = { x=1920 y=1440 }  # texturefile = "gfx/wrong.dds"\n'
        '\t\ttexturefile = "gfx/main_menu/menu.dds"\n'
        "\t}\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_frontend_bg_basic"\n'
        '\t\ttexturefile = "gfx/loadingscreens/load_1.dds"\n'
        "\t}\n"
        "}\n",
    )

    assert gbt.main([], root=tmp_path) == 0

    assert (tmp_path / "gfx/main_menu/menu_small.dds").is_file()
    assert _sprite_names(tmp_path) == [
        "GFX_load_1_small",
        "GFX_menu_small",
        gbt.BORDER_SPRITE,
    ]
    assert 'texturefile = "gfx/main_menu/menu_small.dds"' in read_text(tmp_path / GFX)


def test_menu_background_already_declared_is_not_duplicated(tmp_path):
    _tree(tmp_path, ["load_1"])
    write_under(
        tmp_path,
        FRONTEND_BG,
        'spriteType = {\n\tname = "GFX_frontend_bg"\n'
        '\ttexturefile = "gfx/loadingscreens/load_1.dds"\n}\n',
    )

    assert gbt.main([], root=tmp_path) == 0

    assert _sprite_names(tmp_path) == ["GFX_load_1_small", gbt.BORDER_SPRITE]


@pytest.mark.parametrize(
    "body",
    [
        'spriteType = {\n\tname = "GFX_frontend_bg_basic"\n\ttexturefile = "a.dds"\n}\n',
        'spriteType = {\n\tname = "GFX_frontend_bg"\n\tsize = { x=1 y=1 }\n}\n',
    ],
)
def test_menu_background_parse_miss_is_a_problem(tmp_path, capsys, body):
    _tree(tmp_path, ["load_1"])
    write_under(tmp_path, FRONTEND_BG, body)

    assert gbt.main([], root=tmp_path) == 1

    assert f"{FRONTEND_BG}: no GFX_frontend_bg texture" in capsys.readouterr().err


def test_declared_backgrounds_takes_only_top_level_names_once(tmp_path):
    write_under(
        tmp_path,
        BACKGROUNDS,
        "# load_comment = { }\n"
        "load_1 = {\n"
        "\tgfx = {\n\t\tnested = 1\n\t}\n"
        "}\n"
        "load_2 = { } # trailing\n"
        "load_1 = { }\n"
        'load_dlc = { dlc_allowed = "No Step Back" }\n',
    )

    assert gbt.declared_backgrounds(tmp_path) == ["load_1", "load_2", "load_dlc"]


def test_no_backgrounds_declared(tmp_path, capsys):
    (tmp_path / "common/frontend/backgrounds").mkdir(parents=True)

    assert gbt.main([], root=tmp_path) == 1

    assert "No backgrounds declared" in capsys.readouterr().err
