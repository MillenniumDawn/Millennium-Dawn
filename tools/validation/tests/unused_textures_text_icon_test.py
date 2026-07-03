"""Tests for loc £text_icon resolution in validate_unused_textures.py.

£stem and £GFX_stem both resolve to a spriteType named GFX_stem. A texture
whose sprite is referenced only through one of those loc forms must not be
reported as unused.
"""

from validate_unused_textures import Validator


def _write(mod_path, rel_path, content=""):
    p = mod_path / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _build_mod(tmp_path):
    _write(tmp_path, "gfx/texticons/only_via_stem.dds")
    _write(tmp_path, "gfx/texticons/only_via_gfx_stem.dds")
    _write(tmp_path, "gfx/texticons/truly_orphan.dds")

    _write(
        tmp_path,
        "interface/text_icons.gfx",
        "spriteTypes = {\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_only_via_stem"\n'
        '\t\ttexturefile = "gfx/texticons/only_via_stem.dds"\n'
        "\t}\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_only_via_gfx_stem"\n'
        '\t\ttexturefile = "gfx/texticons/only_via_gfx_stem.dds"\n'
        "\t}\n"
        "}\n",
    )

    _write(
        tmp_path,
        "localisation/english/test_l_english.yml",
        "l_english:\n"
        ' test_bare_stem: "£only_via_stem Some icon text"\n'
        ' test_gfx_stem: "£GFX_only_via_gfx_stem Some other icon text"\n',
    )

    return str(tmp_path)


def test_bare_stem_resolves_texture_and_is_not_reported_unused(tmp_path):
    mod_path = _build_mod(tmp_path)
    validator = Validator(mod_path=mod_path, use_colors=False, workers=1)
    validator.validate_unused_textures()

    assert "gfx/texticons/only_via_stem.dds" in validator.text_icon_referenced_textures
    unused = {issue.message for issue in validator._issues}
    assert "gfx/texticons/only_via_stem.dds" not in unused


def test_gfx_prefixed_stem_resolves_texture_and_is_not_reported_unused(tmp_path):
    mod_path = _build_mod(tmp_path)
    validator = Validator(mod_path=mod_path, use_colors=False, workers=1)
    validator.validate_unused_textures()

    assert (
        "gfx/texticons/only_via_gfx_stem.dds" in validator.text_icon_referenced_textures
    )
    unused = {issue.message for issue in validator._issues}
    assert "gfx/texticons/only_via_gfx_stem.dds" not in unused


def test_actually_unreferenced_texture_still_flagged(tmp_path):
    mod_path = _build_mod(tmp_path)
    validator = Validator(mod_path=mod_path, use_colors=False, workers=1)
    validator.validate_unused_textures()

    unused = {issue.message for issue in validator._issues}
    assert "gfx/texticons/truly_orphan.dds" in unused
    assert (
        "gfx/texticons/truly_orphan.dds" not in validator.text_icon_referenced_textures
    )
