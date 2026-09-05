"""Tests for the vanilla-side inputs of validate_file_paths.

The case-collision check is only as good as the path universe it compares
against: the checksum manifest decides which directories count, DLC roots each
carry their own copy of them, and the git index (not the working tree) is what
lists the mod's own shipped paths under a sparse checkout.
"""

import os

import pytest
import validate_file_paths as vfp
from shared.suite import initialize_git_repository, write_text

_MANIFEST = """
directory
name = common
sub_directories = yes
file_extension = .txt

directory
name = map
sub_directories = no
file_extension = .bmp
"""

_DESCRIPTOR = 'version="2.0.0"\nreplace_path = "common/ai_focuses"\n'


def _install(tmp_path):
    """Build a fake HOI4 install: base roots plus one DLC and one integrated DLC."""
    root = tmp_path / "hoi4"
    write_text(root / "checksum_manifest.txt", _MANIFEST)
    write_text(root / "common" / "ideas" / "00_ideas.txt", "")
    write_text(root / "common" / "notes.md", "")
    write_text(root / "map" / "terrain.bmp", "")
    write_text(root / "map" / "strategicregions" / "1.bmp", "")
    write_text(root / "dlc" / "dlc01_toa" / "common" / "ideas" / "toa.txt", "")
    write_text(root / "integrated_dlc" / "gotterdammerung" / "map" / "extra.bmp", "")
    write_text(root / "dlc" / "loose_file.txt", "")
    return str(root)


def test_content_roots_cover_the_base_install_and_every_dlc(tmp_path):
    install = _install(tmp_path)
    roots = list(vfp.vanilla_content_roots(install))
    assert roots[0] == install
    assert os.path.join(install, "dlc", "dlc01_toa") in roots
    assert os.path.join(install, "integrated_dlc", "gotterdammerung") in roots
    # A stray file beside the DLC directories is not a content root.
    assert os.path.join(install, "dlc", "loose_file.txt") not in roots


def test_content_roots_skip_absent_dlc_groups(tmp_path):
    root = tmp_path / "bare"
    root.mkdir()
    assert list(vfp.vanilla_content_roots(str(root))) == [str(root)]


def test_collect_vanilla_paths_honours_extension_and_recursion(tmp_path):
    paths = vfp.collect_vanilla_paths(_install(tmp_path))
    assert "common/ideas/00_ideas.txt" in paths
    assert "map/terrain.bmp" in paths
    # sub_directories = no for map/, so the nested .bmp is outside the checksum.
    assert "map/strategicregions/1.bmp" not in paths
    # Wrong extension inside a checksummed directory.
    assert "common/notes.md" not in paths


def test_collect_vanilla_paths_reads_dlc_roots(tmp_path):
    paths = vfp.collect_vanilla_paths(_install(tmp_path))
    assert "common/ideas/toa.txt" in paths
    assert "map/extra.bmp" in paths


def test_collect_vanilla_paths_without_a_checksum_manifest_is_empty(tmp_path):
    root = tmp_path / "no_manifest"
    write_text(root / "common" / "a.txt", "")
    assert vfp.collect_vanilla_paths(str(root)) == set()


def test_corrupt_paths_manifest_reads_as_absent(tmp_path, monkeypatch):
    manifest = tmp_path / "vanilla_paths.txt"
    manifest.write_bytes(b"common/a.txt\n\xff\xfe not utf-8 \x80\n")
    monkeypatch.setattr(vfp, "_MANIFEST", str(manifest))
    assert vfp.load_paths_manifest() == set()


def test_tracked_content_paths_reads_the_git_index(tmp_path):
    write_text(tmp_path / "common" / "ideas" / "00_ideas.txt", "x")
    write_text(tmp_path / "tools" / "helper.py", "x")
    write_text(tmp_path / "README.md", "x")
    initialize_git_repository(str(tmp_path), "-A")

    tracked = vfp.tracked_content_paths(str(tmp_path))
    assert tracked == ["common/ideas/00_ideas.txt"]


def test_tracked_content_paths_outside_a_repository_is_none(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    assert vfp.tracked_content_paths(str(tmp_path / "not_a_repo")) is None


def test_unreadable_git_index_fails_setup(tmp_path, monkeypatch):
    mod = tmp_path / "mod"
    write_text(mod / "descriptor.mod", _DESCRIPTOR)
    monkeypatch.setattr(vfp, "tracked_content_paths", lambda _p: None)

    validator = vfp.Validator(mod_path=str(mod), use_colors=False)
    validator.run_validations()

    assert validator.errors_found == 1
    assert validator._issues[0].category == "paths-setup"
    assert "git ls-files failed" in validator._issues[0].message


def test_live_install_paths_are_used_instead_of_the_manifest(tmp_path, monkeypatch):
    install = _install(tmp_path)
    mod = tmp_path / "mod"
    write_text(mod / "descriptor.mod", _DESCRIPTOR)
    monkeypatch.setattr(vfp, "find_hoi4_install", lambda: install)
    monkeypatch.setattr(
        vfp, "load_paths_manifest", lambda: pytest.fail("manifest fallback used")
    )
    monkeypatch.setattr(
        vfp, "tracked_content_paths", lambda _p: ["common/ideas/00_IDEAS.txt"]
    )

    validator = vfp.Validator(mod_path=str(mod), use_colors=False)
    validator.run_validations()

    assert validator.errors_found == 1
    assert validator._issues[0].category == "vanilla-path-case"
    assert "common/ideas/00_ideas.txt" in validator._issues[0].message


def test_windows_hostile_tracked_name_is_reported(tmp_path, monkeypatch):
    mod = tmp_path / "mod"
    write_text(mod / "descriptor.mod", _DESCRIPTOR)
    monkeypatch.setattr(vfp, "find_hoi4_install", lambda: None)
    monkeypatch.setattr(vfp, "load_paths_manifest", lambda: {"common/ideas/a.txt"})
    monkeypatch.setattr(
        vfp, "tracked_content_paths", lambda _p: ["common/ideas/what?.txt"]
    )

    validator = vfp.Validator(mod_path=str(mod), use_colors=False)
    validator.run_validations()

    hostile = [i for i in validator._issues if i.category == "windows-hostile-name"]
    assert len(hostile) == 1
    assert hostile[0].file == "common/ideas/what?.txt"
    assert "Windows forbids" in hostile[0].message
