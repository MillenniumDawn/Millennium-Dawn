"""Regression test for validate_missing_textures in validate_unused_textures.py.

The missing-texture check iterates ``raw_referenced_textures`` — every texture
path as written in a .gfx file. Before that it scanned ``referenced_textures``,
which only held already-resolved on-disk paths, so a reference that resolved to
nothing was never in the set and the check was dead.
"""

from validate_unused_textures import Validator


def _write(mod_path, rel_path, content=""):
    p = mod_path / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_referenced_but_missing_texture_is_reported(tmp_path):
    _write(tmp_path, "gfx/present/real.dds")
    _write(
        tmp_path,
        "interface/test.gfx",
        "spriteTypes = {\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_real"\n'
        '\t\ttexturefile = "gfx/present/real.dds"\n'
        "\t}\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_missing"\n'
        '\t\ttexturefile = "gfx/md_missing_test/does_not_exist.dds"\n'
        "\t}\n"
        "}\n",
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_unused_textures()
    validator.validate_missing_textures()

    messages = "\n".join(issue.message for issue in validator._issues)
    assert validator.missing_count == 1
    assert "gfx/md_missing_test/does_not_exist.dds" in messages
    # The texture that exists on disk is not falsely reported as missing.
    assert "gfx/present/real.dds" not in messages
