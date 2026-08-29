import os
import stat

import pytest
import shared_utils as U
from shared.suite import initialize_git_repository, run_git


def test_normalized_traversal_exclusions_handle_both_separators():
    assert U.should_skip_file(".claude/worktrees/test/events/x.txt")
    assert U.should_skip_file(r".git\objects\x")
    assert U.should_skip_file("resources/reference.txt")
    assert not U.should_skip_file("common/resources/game-data.txt")


def test_strict_read_rejects_malformed_bytes(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"ok\xff")
    with pytest.raises(UnicodeDecodeError):
        U.read_text_strict(str(path))


def test_file_opener_fails_closed_on_malformed_bytes(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"ok\xff")
    U.FileOpener.clear_cache()

    with pytest.raises(UnicodeDecodeError):
        U.FileOpener.open_text_file(str(path))


def test_atomic_write_invalidates_file_opener_cache(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("old", encoding="utf-8")
    U.FileOpener.clear_cache()
    assert U.FileOpener.open_text_file(str(path)) == "old"

    U.atomic_write_text(str(path), "new")

    assert U.FileOpener.open_text_file(str(path)) == "new"


def test_atomic_write_preserves_mode_and_existing_bom(tmp_path):
    path = tmp_path / "loc.yml"
    path.write_bytes(b"\xef\xbb\xbfl_english:\n")
    path.chmod(0o744)

    U.atomic_write_text(str(path), 'l_english:\n key: "value"\n')

    expected_mode = 0o666 if os.name == "nt" else 0o744
    assert stat.S_IMODE(path.stat().st_mode) == expected_mode
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert path.read_bytes().count(b"\xef\xbb\xbf") == 1


def test_atomic_write_uses_non_executable_mode_for_new_files(tmp_path):
    path = tmp_path / "generated.txt"

    U.atomic_write_text(str(path), "generated\n")

    expected_mode = 0o666 if os.name == "nt" else 0o644
    assert stat.S_IMODE(path.stat().st_mode) == expected_mode


def test_atomic_write_preserves_bom_and_crlf(tmp_path):
    path = tmp_path / "loc.yml"
    path.write_bytes(b"\xef\xbb\xbfkey: old\r\n")

    U.atomic_write_text(str(path), "key: new\n")

    assert path.read_bytes() == b"\xef\xbb\xbfkey: new\r\n"


def test_atomic_write_failure_leaves_original(tmp_path, monkeypatch):
    path = tmp_path / "file.txt"
    path.write_bytes(b"original\n")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr(U.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        U.atomic_write_text(str(path), "replacement\n")

    assert path.read_bytes() == b"original\n"
    assert not list(tmp_path.glob(".file.txt.*"))


def test_resolve_under_rejects_escape(tmp_path):
    inside = tmp_path / "ok.txt"
    inside.write_text("ok", encoding="utf-8")
    assert U.resolve_under(str(inside), str(tmp_path)) == inside.resolve()
    with pytest.raises(ValueError, match="not under"):
        U.resolve_under(str(tmp_path / ".." / "outside.txt"), str(tmp_path))


def test_read_text_under_reads_inside_and_rejects_escape(tmp_path):
    inside = tmp_path / "ok.txt"
    inside.write_text("hello", encoding="utf-8")
    assert U.read_text_under(str(inside), str(tmp_path)) == "hello"
    with pytest.raises(ValueError, match="not under"):
        U.read_text_under("/etc/passwd", str(tmp_path))


def test_excluded_path_ignores_different_drives(monkeypatch):
    def raise_cross_drive(*_args):
        raise ValueError("path is on another mount")

    monkeypatch.setattr(U.os.path, "relpath", raise_cross_drive)
    assert not U.is_excluded_path("C:/tmp/file.txt", {"resources"}, "D:/repo")
    assert not U.is_excluded_path("C:/resources/file.txt", {"resources"}, "D:/repo")


def test_write_text_under_rejects_escape(tmp_path):
    with pytest.raises(ValueError, match="not under"):
        U.write_text_under(str(tmp_path / ".." / "out.txt"), str(tmp_path), "nope")
    assert not (tmp_path / "out.txt").exists()


def test_atomic_write_rejects_symlink(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("target", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        os.symlink(target, link)
    except OSError:
        pytest.skip("symlinks unavailable")

    with pytest.raises(OSError, match="symlink"):
        U.atomic_write_text(str(link), "changed")
    assert target.read_text(encoding="utf-8") == "target"


def test_atomic_write_rejects_symlinked_parent(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        os.symlink(target, link, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")

    with pytest.raises(OSError, match="symlinked parent"):
        U.atomic_write_text(str(link / "file.txt"), "changed")
    assert not (target / "file.txt").exists()


def test_staged_files_drops_paths_that_are_no_longer_on_disk(tmp_path, monkeypatch):
    """CI's MD_STAGED_FILES carries deletions and the old side of a rename.

    Validators open every entry unguarded, so an unfiltered list crashes the
    whole run with FileNotFoundError instead of validating the files that exist.
    """
    kept = tmp_path / "common" / "country_leader" / "01_high_command_traits.txt"
    kept.parent.mkdir(parents=True)
    kept.write_text("leader_traits = {\n}\n", encoding="utf-8")
    monkeypatch.setenv(
        "MD_STAGED_FILES",
        "common/country_leader/01_high_command_traits.txt\n"
        "common/country_leader/01_military_advisor_traits.txt",
    )

    staged = U.get_staged_files(str(tmp_path))

    assert staged is not None
    assert [os.path.normpath(f) for f in staged] == [os.path.normpath(str(kept))]


def test_staged_files_returns_none_when_every_path_is_gone(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_STAGED_FILES", "common/country_leader/deleted.txt")

    assert U.get_staged_files(str(tmp_path)) is None


def test_staged_files_retains_missing_paths_when_requested(tmp_path, monkeypatch):
    deleted = tmp_path / "common" / "country_leader" / "deleted.txt"
    monkeypatch.setenv("MD_STAGED_FILES", "common/country_leader/deleted.txt")

    assert U.get_staged_files(str(tmp_path), include_missing=True) == [str(deleted)]


def test_staged_files_includes_deleted_git_paths_when_requested(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    units = tmp_path / "history" / "units"
    units.mkdir(parents=True)
    deleted = units / "deleted.txt"
    renamed_from = units / "renamed-from.txt"
    moved_from = units / "moved-out.txt"
    for path, content in (
        (deleted, "units = { deleted = yes }\n"),
        (renamed_from, "units = { renamed = yes }\n"),
        (moved_from, "units = { moved = yes }\n"),
    ):
        with path.open("w", encoding="utf-8", newline="") as output_file:
            output_file.write(content)

    initialize_git_repository(tmp_path, "history/units")
    deleted.unlink()
    renamed_to = units / "renamed-to.txt"
    renamed_from.rename(renamed_to)
    moved_from.rename(tmp_path / "moved-out.txt")
    run_git(tmp_path, "add", "-A")

    staged = U.get_staged_files(str(tmp_path), include_missing=True)

    assert staged is not None
    assert str(deleted) in staged
    assert str(renamed_to) in staged
    assert str(moved_from) in staged
