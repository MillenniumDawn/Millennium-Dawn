"""Tests for tools/assets/resize_decision_icons.py against a temp mod tree.

Covers the three outcomes: a texture only ever used in the wrong slot is
resized in place, a texture that also serves its own slot gets a sibling
sprite plus repointed references, and category `picture` art is reported but
left alone.
"""

import pytest
from PIL import Image
from shared.suite import load_tool_module, read_text, write_under

rdi = load_tool_module("assets/resize_decision_icons.py")

GFX = "interface/MD_decisions.gfx"
DECISIONS = "common/decisions/test.txt"
CATEGORIES = "common/decisions/categories/test_categories.txt"


def _dds(root, relative, size):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, (200, 40, 40, 255)).save(path, format="DDS")
    return path


def _mod(root):
    _dds(root, "gfx/interface/decisions/shared.dds", (52, 40))
    _dds(root, "gfx/interface/decisions/lonely.dds", (52, 40))
    _dds(root, "gfx/interface/decisions/tiny.dds", (33, 32))
    write_under(
        root,
        GFX,
        "spriteTypes = {\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_decision_category_shared"\n'
        '\t\ttexturefile = "gfx/interface/decisions/shared.dds"\n'
        "\t}\n\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_decision_lonely"\n'
        '\t\ttexturefile = "gfx/interface/decisions/lonely.dds"\n'
        "\t}\n\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_decision_tiny"\n'
        '\t\ttexturefile = "gfx/interface/decisions/tiny.dds"\n'
        "\t}\n\n"
        "}\n",
    )
    write_under(
        root,
        DECISIONS,
        "test_category = {\n"
        "\tuses_shared = {\n"
        "\t\ticon = GFX_decision_category_shared\n"
        "\t}\n"
        "\tuses_lonely = {\n"
        "\t\ticon = lonely\n"
        "\t}\n"
        "\tdynamic = {\n"
        "\t\ticon = {\n"
        "\t\t\tkey = GFX_decision_category_shared\n"
        "\t\t\ttrigger = { always = yes }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    write_under(
        root,
        CATEGORIES,
        "test_category = {\n"
        "\ticon = GFX_decision_category_shared\n"
        "\tpicture = GFX_decision_tiny\n"
        "}\n",
    )


@pytest.fixture
def mod(tmp_path, monkeypatch):
    """Temp mod with the vanilla install kept out of the sprite indexes."""
    _mod(tmp_path)
    texture_index = rdi.build_sprite_texture_index
    name_index = rdi.build_sprite_index
    monkeypatch.setattr(
        rdi,
        "build_sprite_texture_index",
        lambda mod_path: texture_index(mod_path, include_vanilla=False),
    )
    monkeypatch.setattr(
        rdi,
        "build_sprite_index",
        lambda mod_path, gfx_only=False: name_index(
            mod_path, gfx_only=gfx_only, include_vanilla=False
        ),
    )
    return tmp_path


def _size(path):
    with Image.open(path) as image:
        return image.size


def test_dry_run_classifies_without_writing(mod, capsys):
    before = read_text(mod / DECISIONS)
    assert rdi.main(["--path", str(mod), "--dry-run"], root=mod) == 0
    out = capsys.readouterr().out
    assert "in-place GFX_decision_lonely" in out
    assert "sibling  GFX_decision_category_shared" in out
    assert "=> GFX_decision_shared" in out
    assert "manual   GFX_decision_tiny" in out
    assert read_text(mod / DECISIONS) == before
    assert _size(mod / "gfx/interface/decisions/lonely.dds") == (52, 40)
    assert not (mod / "gfx/interface/decisions/decision_shared.dds").exists()


def test_apply_resizes_creates_siblings_and_repoints(mod):
    assert rdi.main(["--path", str(mod)], root=mod) == 0

    assert _size(mod / "gfx/interface/decisions/lonely.dds") == (33, 32)
    assert _size(mod / "gfx/interface/decisions/shared.dds") == (52, 40)
    assert _size(mod / "gfx/interface/decisions/decision_shared.dds") == (33, 32)

    gfx = read_text(mod / GFX)
    assert gfx.endswith(
        "\tspriteType = {\n"
        '\t\tname = "GFX_decision_shared"\n'
        '\t\ttexturefile = "gfx/interface/decisions/decision_shared.dds"\n'
        "\t}\n\n}\n"
    )
    assert "\r" not in gfx

    decisions = read_text(mod / DECISIONS)
    assert "\t\ticon = GFX_decision_shared\n" in decisions
    assert "\t\t\tkey = GFX_decision_shared\n" in decisions
    assert "GFX_decision_category_shared" not in decisions
    assert "\t\ticon = lonely\n" in decisions

    categories = read_text(mod / CATEGORIES)
    assert "\ticon = GFX_decision_category_shared\n" in categories
    assert "\tpicture = GFX_decision_tiny\n" in categories


def test_render_fits_and_centres_on_canvas(tmp_path):
    source = _dds(tmp_path, "wide.dds", (144, 68))
    image = rdi.render(str(source), "decision")
    assert image.size == (33, 32)
    assert image.getpixel((16, 0))[3] == 0
    assert image.getpixel((16, 16))[3] == 255
