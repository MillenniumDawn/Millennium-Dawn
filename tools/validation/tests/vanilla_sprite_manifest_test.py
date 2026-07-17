"""Tests for the vanilla sprite manifest path in validate_gfx_references.

CI has no HOI4 install, so the committed vanilla_sprites.txt is the only
vanilla cross-reference there; these cover the loader and the shared .gfx
name parser the generator reuses.
"""

import validate_gfx_references as vg


def test_manifest_loads_names(tmp_path, monkeypatch):
    manifest = tmp_path / "vanilla_sprites.txt"
    manifest.write_text("# header\n\nGFX_alpha\nGFX_beta\n", encoding="utf-8")
    monkeypatch.setattr(vg, "_VANILLA_SPRITES_MANIFEST", str(manifest))
    assert vg._load_vanilla_sprite_manifest() == frozenset({"GFX_alpha", "GFX_beta"})


def test_missing_manifest_reads_as_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(
        vg, "_VANILLA_SPRITES_MANIFEST", str(tmp_path / "does_not_exist.txt")
    )
    assert vg._load_vanilla_sprite_manifest() == frozenset()


def test_corrupt_manifest_reads_as_absent(tmp_path, monkeypatch):
    manifest = tmp_path / "vanilla_sprites.txt"
    manifest.write_bytes(b"\xff\xfe\x00 not utf-8 \x80")
    monkeypatch.setattr(vg, "_VANILLA_SPRITES_MANIFEST", str(manifest))
    assert vg._load_vanilla_sprite_manifest() == frozenset()


def test_sprite_names_from_gfx_text():
    text = (
        "spriteTypes = {\n"
        "\tspriteType = {\n"
        '\t\tname = "GFX_manifest_probe"\n'
        '\t\ttexturefile = "gfx/interface/probe.dds"\n'
        "\t}\n"
        '\t# spriteType = { name = "GFX_commented_out" }\n'
        "}\n"
    )
    assert vg.sprite_names_from_gfx_text(text) == {"GFX_manifest_probe"}
