"""Scanning and reporting tests for validate_unused_textures.

The unused/missing verdict is the union of five independent scans (.gfx blocks,
game-script .txt, .mesh blobs, loc text icons, vanilla). Each is exercised on
its own here, because a scan that silently returns nothing turns live art into
an "unused" finding and a dead reference into silence.

`find_hoi4_install` is stubbed out by default: a developer machine with HOI4
installed would otherwise scan the real install and take a different branch than
CI does.
"""

import argparse
import os

import pytest
import validate_unused_textures as vut
from validate_unused_textures import Validator


@pytest.fixture(autouse=True)
def _no_hoi4_install(monkeypatch):
    monkeypatch.setattr(vut, "find_hoi4_install", lambda: None)


def _write(path, body="", binary=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if binary is None:
        path.write_text(body, encoding="utf-8")
    else:
        path.write_bytes(binary)
    return str(path)


# --- texture discovery ------------------------------------------------------


def test_texture_discovery_skips_flags_and_unshipped_dumps(tmp_path):
    _write(tmp_path / "gfx" / "interface" / "kept.dds")
    _write(tmp_path / "gfx" / "flags" / "USA.tga")
    _write(tmp_path / "gfx" / "resources" / "dump.dds")
    _write(tmp_path / "gfx" / "loadingscreens" / "splash.png")
    _write(tmp_path / "gfx" / "interface" / "notes.md")

    assert vut.find_texture_files(str(tmp_path)) == {"gfx/interface/kept.dds"}


def test_gfx_file_discovery_skips_the_same_dumps(tmp_path):
    _write(tmp_path / "interface" / "real.gfx", "spriteTypes = {\n}\n")
    _write(tmp_path / "gfx" / "loadingscreens" / "dump.gfx", "spriteTypes = {\n}\n")

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    found = validator._find_all_gfx_files()

    assert [os.path.basename(f) for f in found] == ["real.gfx"]


# --- .gfx reference resolution ----------------------------------------------


def test_gfx_reference_resolves_by_basename_for_entity_textures(tmp_path):
    path = _write(
        tmp_path / "gfx" / "models" / "unit.gfx",
        'objectTypes = {\n\tpdxmesh = {\n\t\ttexture_diffuse = "unit_diffuse.dds"\n\t}\n}\n',
    )
    vut._textures_init(
        str(tmp_path),
        {"gfx/models/deep/unit_diffuse.dds"},
        {"unit_diffuse.dds": ["gfx/models/deep/unit_diffuse.dds"]},
    )
    resolved, raw = vut.process_gfx_file(path)

    assert resolved == {"gfx/models/deep/unit_diffuse.dds"}
    assert raw == {"unit_diffuse.dds"}


def test_unreadable_gfx_file_resolves_nothing(tmp_path):
    vut._textures_init(str(tmp_path), set(), {})
    assert vut.process_gfx_file(str(tmp_path / "absent.gfx")) == (set(), set())


def test_sprite_texture_map_skips_incomplete_and_unbalanced_blocks(tmp_path):
    path = _write(
        tmp_path / "interface" / "icons.gfx",
        "spriteTypes = {\n"
        '\tspriteType = {\n\t\tname = "GFX_ok"\n\t\ttexturefile = "gfx//a//b.dds"\n\t}\n'
        '\tspriteType = {\n\t\ttexturefile = "gfx/nameless.dds"\n\t}\n'
        '\tspriteType = {\n\t\tname = "GFX_no_texture"\n\t}\n'
        "}\n"
        '\tspriteType = {\n\t\tname = "GFX_unbalanced"\n',
    )
    assert vut._sprite_name_to_texture([path]) == {"GFX_ok": "gfx/a/b.dds"}


# --- game-script references -------------------------------------------------


def test_texture_reference_patterns_cover_portrait_picture_and_paths():
    content = (
        'portrait = "gfx/leaders/USA/leader.dds"\n'
        'picture = "gfx\\\\events/event.tga"\n'
        'texture = "gfx//interface//icon.png"\n'
        'unrelated = "common/ideas/x.txt"\n'
    )
    assert vut._extract_texture_refs(content) == {
        "gfx/leaders/USA/leader.dds",
        "gfx/events/event.tga",
        "gfx/interface/icon.png",
    }


def test_game_file_references_match_by_path_and_by_basename(tmp_path):
    path = _write(
        tmp_path / "common" / "characters" / "USA.txt",
        'portrait = "gfx/leaders/USA/leader.dds"\nportrait = "moved.dds"\n',
    )
    vut._textures_init(
        str(tmp_path),
        {"gfx/leaders/USA/leader.dds", "gfx/leaders/deep/moved.dds"},
        {"moved.dds": ["gfx/leaders/deep/moved.dds"]},
    )
    assert vut.process_game_file(path) == {
        "gfx/leaders/USA/leader.dds",
        "gfx/leaders/deep/moved.dds",
    }


def test_unreadable_game_file_matches_nothing(tmp_path):
    vut._textures_init(str(tmp_path), set(), {})
    assert vut.process_game_file(str(tmp_path / "absent.txt")) == set()


def test_game_file_scan_does_not_descend_into_hidden_directories(tmp_path):
    _write(
        tmp_path / "common" / "characters" / "USA.txt",
        'portrait = "gfx/leaders/USA/leader.dds"\n',
    )
    _write(
        tmp_path / "common" / ".claude" / "scratch.txt",
        'portrait = "gfx/leaders/USA/scratch.dds"\n',
    )
    _write(tmp_path / "gfx" / "leaders" / "USA" / "leader.dds")
    _write(tmp_path / "gfx" / "leaders" / "USA" / "scratch.dds")

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_unused_textures()

    unused = {issue.message for issue in validator._issues}
    assert "gfx/leaders/USA/leader.dds" not in unused
    assert "gfx/leaders/USA/scratch.dds" in unused


# --- .mesh references -------------------------------------------------------


def test_mesh_blob_marks_its_textures_as_used(tmp_path):
    _write(tmp_path / "gfx" / "models" / "unit_diffuse.dds")
    _write(
        tmp_path / "gfx" / "models" / "unit.mesh",
        binary=b"\x00\x01pdxmesh\x00unit_diffuse.dds\x00\xff",
    )
    # A directory ending in .mesh is matched by the glob but cannot be read.
    (tmp_path / "gfx" / "models" / "broken.mesh").mkdir()

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_unused_textures()

    assert "gfx/models/unit_diffuse.dds" in validator.mesh_referenced_textures
    assert validator._issues == []


# --- loc text icons ---------------------------------------------------------


def test_text_icon_resolves_through_the_texture_basename(tmp_path):
    # The sprite's texturefile path is stale but the art moved, not vanished —
    # the basename lookup is what keeps it out of the unused report.
    _write(tmp_path / "gfx" / "moved" / "icon.dds")
    _write(
        tmp_path / "interface" / "icons.gfx",
        'spriteType = {\n\tname = "GFX_icon"\n\ttexturefile = "gfx/old/icon.dds"\n}\n',
    )
    _write(
        tmp_path / "localisation" / "english" / "a_l_english.yml",
        'l_english:\n A:0 "£icon"\n',
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_unused_textures()

    assert validator.text_icon_referenced_textures == {"gfx/moved/icon.dds"}


def test_text_icon_scan_tolerates_an_unreadable_loc_path(tmp_path):
    (tmp_path / "localisation" / "english" / "broken_l_english.yml").mkdir(parents=True)
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    assert validator._get_text_icon_referenced_textures() == set()


def test_duplicate_basenames_share_one_lookup_entry(tmp_path):
    _write(tmp_path / "gfx" / "a" / "icon.dds")
    _write(tmp_path / "gfx" / "b" / "icon.dds")

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_unused_textures()

    assert sorted(validator.texture_filename_lookup["icon.dds"]) == [
        "gfx/a/icon.dds",
        "gfx/b/icon.dds",
    ]


# --- HOI4 install detection -------------------------------------------------


def test_provided_install_path_is_used(tmp_path):
    install = tmp_path / "hoi4"
    install.mkdir()
    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, hoi4_path=str(install)
    )
    assert validator.hoi4_path == str(install)


def test_provided_install_path_that_does_not_exist_is_dropped(tmp_path):
    validator = Validator(
        mod_path=str(tmp_path),
        use_colors=False,
        workers=1,
        hoi4_path=str(tmp_path / "absent"),
    )
    assert validator.hoi4_path is None
    assert any("does not exist" in line for line in validator.output_lines)


def test_auto_detected_install_is_used(tmp_path, monkeypatch):
    install = tmp_path / "detected"
    install.mkdir()
    monkeypatch.setattr(vut, "find_hoi4_install", lambda: str(install))
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    assert validator.hoi4_path == str(install)


# --- missing-texture verdict ------------------------------------------------


def _missing_validator(tmp_path, raw_refs, **kwargs):
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1, **kwargs)
    validator.texture_files = vut.find_texture_files(str(tmp_path))
    validator.texture_filename_lookup = {}
    for tex in validator.texture_files:
        validator.texture_filename_lookup.setdefault(os.path.basename(tex), []).append(
            tex
        )
    validator.raw_referenced_textures = set(raw_refs)
    return validator


def test_reference_resolving_by_basename_is_not_missing(tmp_path):
    _write(tmp_path / "gfx" / "deep" / "icon.dds")
    validator = _missing_validator(tmp_path, {"gfx/old/icon.dds"})
    validator.validate_missing_textures()
    assert validator.missing_count == 0


def test_reference_to_a_non_texture_file_on_disk_is_not_missing(tmp_path):
    # Flags are excluded from the texture index by design, but the file is
    # really there, so a .gfx pointing at one is not a broken reference.
    _write(tmp_path / "gfx" / "flags" / "USA.tga")
    validator = _missing_validator(tmp_path, {"gfx/flags/USA.tga"})
    validator.validate_missing_textures()
    assert validator.missing_count == 0


def test_vanilla_referenced_texture_is_not_missing(tmp_path):
    validator = _missing_validator(tmp_path, {"gfx/interface/vanilla_icon.dds"})
    validator.vanilla_raw_referenced_textures = {"gfx/interface/vanilla_icon.dds"}
    validator.validate_missing_textures()
    assert validator.missing_count == 0


def test_texture_present_in_the_install_but_undeclared_is_not_missing(tmp_path):
    install = tmp_path / "hoi4"
    _write(install / "gfx" / "interface" / "atlas.dds")
    validator = _missing_validator(
        tmp_path, {"gfx/interface/atlas.dds"}, hoi4_path=str(install)
    )
    validator.validate_missing_textures()
    assert validator.missing_count == 0


def test_missing_texture_is_only_a_warning_without_an_install(tmp_path):
    validator = _missing_validator(tmp_path, {"gfx/absent/icon.dds"})
    validator.validate_missing_textures()

    assert validator.missing_count == 1
    assert validator.errors_found == 0
    assert validator.warnings_found == 1


def test_missing_texture_is_an_error_with_an_install(tmp_path):
    install = tmp_path / "hoi4"
    install.mkdir()
    validator = _missing_validator(
        tmp_path, {"gfx/absent/icon.dds"}, hoi4_path=str(install)
    )
    validator.validate_missing_textures()

    assert validator.errors_found == 1
    assert validator.warnings_found == 0


# --- full run ---------------------------------------------------------------


def test_full_run_reports_unused_and_missing_without_an_install(tmp_path):
    _write(tmp_path / "gfx" / "interface" / "orphan.dds")
    _write(
        tmp_path / "interface" / "icons.gfx",
        'spriteType = {\n\tname = "GFX_x"\n\ttexturefile = "gfx/absent/icon.dds"\n}\n',
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()

    assert validator.unused_count == 1
    assert validator.missing_count == 1
    messages = {issue.message for issue in validator._issues}
    assert "gfx/interface/orphan.dds" in messages
    assert "gfx/absent/icon.dds" in messages


def test_full_run_with_an_install_scans_vanilla_too(tmp_path):
    install = tmp_path / "hoi4"
    _write(install / "gfx" / "interface" / "vanilla.dds")
    _write(
        install / "interface" / "core.gfx",
        'spriteType = {\n\tname = "GFX_v"\n\ttexturefile = "gfx/interface/vanilla.dds"\n}\n',
    )
    _write(tmp_path / "gfx" / "interface" / "orphan.dds")
    _write(
        tmp_path / "interface" / "icons.gfx",
        'spriteType = {\n\tname = "GFX_x"\n\ttexturefile = "gfx/interface/vanilla.dds"\n}\n',
    )

    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, hoi4_path=str(install)
    )
    validator.run_validations()

    # The mod's reference points at vanilla art, so it is neither a mod texture
    # nor a missing one.
    assert "gfx/interface/vanilla.dds" in validator.vanilla_raw_referenced_textures
    assert validator.missing_count == 0
    assert validator.unused_count == 1


def test_full_run_with_an_install_errors_on_a_reference_nothing_can_resolve(tmp_path):
    install = tmp_path / "hoi4"
    install.mkdir()
    _write(
        tmp_path / "interface" / "icons.gfx",
        'spriteType = {\n\tname = "GFX_x"\n\ttexturefile = "gfx/absent/icon.dds"\n}\n',
    )

    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, hoi4_path=str(install)
    )
    validator.run_validations()

    assert validator.missing_count == 1
    assert validator.errors_found == 1


def test_clean_mod_reports_nothing(tmp_path):
    _write(tmp_path / "gfx" / "interface" / "used.dds")
    _write(
        tmp_path / "interface" / "icons.gfx",
        'spriteType = {\n\tname = "GFX_x"\n\ttexturefile = "gfx/interface/used.dds"\n}\n',
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()

    assert (validator.unused_count, validator.missing_count) == (0, 0)
    assert validator._issues == []


def test_hoi4_path_argument_is_registered():
    parser = argparse.ArgumentParser()
    vut.add_extra_args(parser)
    assert parser.parse_args(["--hoi4-path", "/opt/hoi4"]).hoi4_path == "/opt/hoi4"
