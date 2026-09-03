"""Tests for sprite_index — the shared name/texture index over interface/*.gfx.

Every sprite-reference check (event pictures, focus icons, idea pictures) asks
this module what exists, so a block it silently drops turns a live sprite into a
"missing" finding. The vanilla scan is switched off throughout: it depends on a
local HOI4 install, which CI does not have.
"""

import os

import pytest
import sprite_index


@pytest.fixture(autouse=True)
def _no_vanilla_install(monkeypatch):
    monkeypatch.setattr(sprite_index, "_vanilla_gfx_files", lambda: [])


def _write_gfx(tmp_path, name, body):
    interface = tmp_path / "interface"
    interface.mkdir(exist_ok=True)
    path = interface / name
    path.write_text(body, encoding="utf-8")
    return str(path)


def test_names_are_read_from_balanced_blocks(tmp_path):
    path = _write_gfx(
        tmp_path,
        "a.gfx",
        'spriteTypes = {\n\tspriteType = {\n\t\tname = "GFX_a"\n\t}\n'
        "\tspriteType = {\n\t\tname = GFX_bare\n\t}\n}\n",
    )
    assert sprite_index._names_in_file(path) == ["GFX_a", "GFX_bare"]


def test_unbalanced_block_falls_back_to_the_opening_line(tmp_path):
    # A .gfx missing its closing brace still declares the sprite the engine
    # loads up to that point; dropping it would report a live name as missing.
    path = _write_gfx(tmp_path, "b.gfx", 'spriteType = { name = "GFX_unbalanced"\n')
    assert sprite_index._names_in_file(path) == ["GFX_unbalanced"]


def test_block_without_a_name_is_skipped(tmp_path):
    path = _write_gfx(
        tmp_path, "c.gfx", 'spriteType = {\n\ttexturefile = "gfx/x.dds"\n}\n'
    )
    assert sprite_index._names_in_file(path) == []


def test_unreadable_file_yields_no_names(tmp_path):
    assert sprite_index._names_in_file(str(tmp_path / "absent.gfx")) == []


def test_pool_worker_wrapper_unpacks_its_argument_pair(tmp_path):
    path = _write_gfx(tmp_path, "d.gfx", 'spriteType = { name = "GFX_d" }\n')
    assert sprite_index._names_in_file_pair((path, str(tmp_path))) == ["GFX_d"]


def test_index_is_built_through_a_supplied_pool_map(tmp_path):
    _write_gfx(tmp_path, "e.gfx", 'spriteType = { name = "GFX_e" }\n')
    calls = []

    def fake_map(fn, items):
        calls.append(len(list(items)))
        return [fn(item) for item in items]

    index = sprite_index.build_sprite_index(
        str(tmp_path), pool_map=fake_map, include_vanilla=False
    )
    assert index == frozenset({"GFX_e"})
    assert calls == [1]


def test_vanilla_names_join_the_index_when_included(tmp_path, monkeypatch):
    vanilla = _write_gfx(tmp_path, "vanilla.gfx", 'spriteType = { name = "GFX_van" }\n')
    _write_gfx(tmp_path, "mod.gfx", 'spriteType = { name = "GFX_mod" }\n')
    monkeypatch.setattr(sprite_index, "_vanilla_gfx_files", lambda: [vanilla])

    assert sprite_index.build_sprite_index(str(tmp_path), include_vanilla=True) >= {
        "GFX_van",
        "GFX_mod",
    }


def test_mod_texture_overrides_a_vanilla_sprite_of_the_same_name(tmp_path, monkeypatch):
    vanilla_root = tmp_path / "vanilla"
    vanilla_gfx = vanilla_root / "interface" / "shared.gfx"
    vanilla_gfx.parent.mkdir(parents=True)
    vanilla_gfx.write_text(
        'spriteType = {\n\tname = "GFX_shared"\n\ttexturefile = "gfx/van.dds"\n}\n',
        encoding="utf-8",
    )
    _write_gfx(
        tmp_path,
        "shared.gfx",
        'spriteType = {\n\tname = "GFX_shared"\n\ttexturefile = "gfx/mod.dds"\n}\n',
    )
    monkeypatch.setattr(sprite_index, "_vanilla_gfx_files", lambda: [str(vanilla_gfx)])

    index = sprite_index.build_sprite_texture_index(str(tmp_path), include_vanilla=True)
    assert index["GFX_shared"] == os.path.join(str(tmp_path), "gfx", "mod.dds")


def test_gfx_only_drops_unprefixed_focus_icon_names(tmp_path):
    _write_gfx(
        tmp_path,
        "f.gfx",
        'spriteType = { name = "GFX_kept" }\nspriteType = { name = "focus_icon" }\n',
    )
    everything = sprite_index.build_sprite_index(str(tmp_path), include_vanilla=False)
    prefixed = sprite_index.build_sprite_index(
        str(tmp_path), gfx_only=True, include_vanilla=False
    )
    assert everything == frozenset({"GFX_kept", "focus_icon"})
    assert prefixed == frozenset({"GFX_kept"})


def test_texture_index_maps_sprites_to_absolute_paths(tmp_path):
    _write_gfx(
        tmp_path,
        "g.gfx",
        'spriteType = {\n\tname = "GFX_g"\n\ttexturefile = "gfx/art/g.dds"\n}\n'
        'spriteType = {\n\tname = "GFX_no_texture"\n}\n',
    )
    index = sprite_index.build_sprite_texture_index(
        str(tmp_path), include_vanilla=False
    )
    assert index == {"GFX_g": os.path.join(str(tmp_path), "gfx", "art", "g.dds")}


def test_texture_worker_tolerates_a_vanished_file(tmp_path):
    assert (
        sprite_index._textures_in_file((str(tmp_path / "gone.gfx"), str(tmp_path)))
        == []
    )


def test_gfx_root_is_the_directory_holding_interface(tmp_path):
    assert sprite_index._gfx_root("/opt/hoi4/dlc/dlc01/interface/x.gfx") == (
        "/opt/hoi4/dlc/dlc01"
    )
    assert sprite_index._gfx_root("/tmp/loose/x.gfx") == "/tmp/loose"
