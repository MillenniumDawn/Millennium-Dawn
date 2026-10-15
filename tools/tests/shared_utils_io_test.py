import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import shared_utils as U
from shared.suite import initialize_git_repository, run_git
from shared.suite import write_text as _write


def test_normalized_traversal_exclusions_handle_both_separators():
    assert U.should_skip_file(".claude/worktrees/test/events/x.txt")
    assert U.should_skip_file(r".git\objects\x")
    assert U.should_skip_file("resources/reference.txt")
    assert not U.should_skip_file("common/resources/game-data.txt")


def test_adjacency_rules_count_as_game_logic_but_map_stays_ignored():
    assert not U.should_skip_file("map/adjacency_rules.txt")
    assert U.should_skip_file("map/colors.txt")
    assert not U.should_skip_file("map\\adjacency_rules.txt")
    assert U.should_skip_file(".claude/worktrees/wt/map/adjacency_rules.txt")
    assert U.should_skip_file("resources/vanilla/map/adjacency_rules.txt")


@pytest.mark.parametrize(
    "checkout",
    [
        "repo",
        ".claude/worktrees/repo",
        ".git/worktrees/repo",
        "tools/repo",
        "resources/repo",
        "docs/repo",
        "gfx/repo",
        "map/repo",
    ],
)
def test_exclusions_ignore_checkout_ancestors(tmp_path, checkout):
    root = tmp_path / checkout
    assert not U.should_skip_file(str(root / "events/event.txt"), mod_path=str(root))
    assert not U.should_skip_file(
        str(root / "map/adjacency_rules.txt"), mod_path=str(root)
    )
    assert not U.should_skip_file("events/event.txt", mod_path=str(root))


@pytest.mark.parametrize(
    "relative",
    [
        ".claude/worktrees/stale/events/event.txt",
        ".git/worktrees/stale/events/event.txt",
        "events/.claude/stale.txt",
        "common/.git/stale.txt",
        "resources/vanilla/events/event.txt",
        "tools/fixture.txt",
        "docs/example.txt",
        "map/colors.txt",
        "resources/vanilla/map/adjacency_rules.txt",
    ],
)
def test_exclusions_still_apply_inside_a_worktree(tmp_path, relative):
    root = tmp_path / ".claude/worktrees/repo"
    assert U.should_skip_file(str(root / relative), mod_path=str(root))
    assert U.should_skip_file(relative, mod_path=str(root))


def test_extra_exclusions_ignore_checkout_ancestors(tmp_path):
    root = tmp_path / "excluded-fixture/repo"
    assert not U.should_skip_file(
        str(root / "events/event.txt"), ["excluded-fixture"], mod_path=str(root)
    )
    assert U.should_skip_file(
        str(root / "events/excluded-fixture/event.txt"),
        ["excluded-fixture"],
        mod_path=str(root),
    )


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
    assert U.is_excluded_path("C:/resources/file.txt", {"resources"}, "D:/repo")


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


@pytest.mark.parametrize(
    "extension, expected", [(".txt", ["a.txt"]), (".yml", None)], ids=["match", "none"]
)
def test_staged_files_filter_by_extension(tmp_path, monkeypatch, extension, expected):
    _write(tmp_path / "common" / "a.txt", "a")
    monkeypatch.setenv("MD_STAGED_FILES", "common/a.txt")
    staged = U.get_staged_files(str(tmp_path), extensions=[extension])
    assert staged == (
        None
        if expected is None
        else [str(tmp_path / "common" / name) for name in expected]
    )


def test_staged_rename_lists_both_sides(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    output = SimpleNamespace(
        stdout="R100\tcommon/old.txt\tcommon/new.txt\n", returncode=0
    )
    monkeypatch.setattr(U.subprocess, "run", lambda *args, **kwargs: output)
    assert U.get_staged_files(str(tmp_path), include_missing=True) == [
        str(tmp_path / "common" / "old.txt"),
        str(tmp_path / "common" / "new.txt"),
    ]


def _raise(error):
    def run(*_args, **_kwargs):
        raise error

    return run


@pytest.mark.parametrize(
    "run",
    [
        _raise(subprocess.TimeoutExpired("git", 1)),
        lambda *args, **kwargs: SimpleNamespace(stdout=""),
    ],
    ids=["git timed out", "nothing staged"],
)
def test_staged_files_without_git_output_is_none(tmp_path, monkeypatch, run):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    monkeypatch.setattr(U.subprocess, "run", run)
    assert U.get_staged_files(str(tmp_path)) is None


# ---- git diff and tree discovery -----------------------------------------------


@pytest.mark.parametrize(
    "include_interface, expected",
    [(False, ["common/a.txt"]), (True, ["common/a.txt", "interface/b.txt"])],
    ids=["content only", "with interface"],
)
def test_staged_diff_files_come_from_the_env(
    tmp_path, monkeypatch, include_interface, expected
):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "common" / "a.txt", "a")
    _write(tmp_path / "interface" / "b.txt", "b")
    monkeypatch.setattr(U, "_staged_files_cache", None)
    monkeypatch.setenv("MD_STAGED_FILES", "common/a.txt\ninterface/b.txt\nmissing.txt")
    assert (
        U.get_git_diff_files(staged_only=True, include_interface=include_interface)
        == expected
    )


def test_branch_diff_asks_git_for_the_merge_base_range(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write(tmp_path / "common" / "a.txt", "a")
    _write(tmp_path / "interface" / "b.txt", "b")
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    # A branch diff never reads the staged-file cache.
    monkeypatch.setattr(U, "_staged_files_cache", ["common/stale.txt"])
    calls = []
    result = SimpleNamespace(stdout="common/a.txt\ninterface/b.txt\n", returncode=0)
    monkeypatch.setattr(
        U.subprocess, "run", lambda command, **kwargs: calls.append(command) or result
    )
    assert U.get_git_diff_files(base_branch="release") == ["common/a.txt"]
    assert calls[0][-1] == "release...HEAD"


def test_branch_diff_without_git_is_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    monkeypatch.setattr(U.subprocess, "run", _raise(OSError()))
    assert U.get_git_diff_files() == []


@pytest.mark.parametrize(
    "include_interface, expected",
    [(False, ["common/a.txt"]), (True, ["common/a.txt", "interface/b.txt"])],
    ids=["content only", "with interface"],
)
def test_all_txt_files(tmp_path, include_interface, expected):
    _write(tmp_path / "common" / "a.txt", "a")
    _write(tmp_path / "interface" / "b.txt", "b")
    assert U.get_all_txt_files(str(tmp_path), include_interface=include_interface) == [
        str(tmp_path / relative) for relative in expected
    ]


def test_excluded_path_matches_a_directory_component(tmp_path):
    excluded = tmp_path / "common" / "nested" / "tools" / "ignored.txt"
    assert U.is_excluded_path(str(excluded), {"tools"}, str(tmp_path))
    assert not U.is_excluded_path(
        str(tmp_path / "common" / "nested" / "a.TXT"), {"tools"}, str(tmp_path)
    )


def test_txt_targets_of_a_directory_a_file_and_a_missing_path(tmp_path):
    content = tmp_path / "common" / "nested"
    _write(content / "a.TXT", "a")
    _write(content / "b.yml", "b")
    _write(content / "tools" / "ignored.txt", "ignored")
    a_txt = str(content / "a.TXT")
    assert list(U.iter_txt_targets(str(content), {"tools"})) == [("a.TXT", a_txt)]
    assert list(U.iter_txt_targets(a_txt, set())) == [(a_txt, a_txt)]
    assert list(U.iter_txt_targets(str(content / "missing.txt"), set())) == []


# ---- writes, reads and backups -------------------------------------------------


def test_atomic_writes_of_text_with_a_bom_and_of_bytes(tmp_path):
    target = tmp_path / "nested" / "file.txt"
    U.atomic_write_text(str(target), "café\n", encoding="utf-8-sig", bom=True)
    binary = tmp_path / "nested" / "binary.dat"
    U.atomic_write_bytes(str(binary), b"\x00\xff")
    assert binary.read_bytes() == b"\x00\xff"
    assert target.read_bytes() == b"\xef\xbb\xbfcaf\xc3\xa9\n"
    assert U.read_text_strict(str(target)) == "café\n"
    assert U.read_text_strict(str(target), reject_symlink=False).startswith("café")


def test_backup_copies_the_file_and_a_missing_file_has_none(tmp_path):
    target = _write(tmp_path / "file.txt", "content\n")
    backup = U.create_backup(str(target))
    assert Path(backup).read_bytes() == target.read_bytes()
    assert U.create_backup(str(tmp_path / "missing")) == ""


@pytest.mark.parametrize(
    "path, expected",
    [("prefix/common/file.txt", "common/file.txt"), ("unrelated.txt", "unrelated.txt")],
)
def test_clean_filepath(path, expected):
    assert U.clean_filepath(path) == expected


def test_file_opener_lowercases_strips_comments_and_caches(tmp_path):
    path = _write(tmp_path / "data.txt", 'KEY = "Value # kept" # remove\n')
    U.FileOpener.clear_cache()
    raw = U.FileOpener.open_text_file(
        str(path), lowercase=True, strip_comments_flag=True
    )
    assert raw == 'key = "value # kept" \n'
    assert (
        U.FileOpener.open_text_file(str(path), lowercase=True, strip_comments_flag=True)
        == raw
    )
    U.FileOpener.invalidate(str(path))


@pytest.mark.parametrize("needle, line", [("KEY", 1), ("missing", 0)])
def test_find_line_number(tmp_path, needle, line):
    path = _write(tmp_path / "data.txt", 'KEY = "Value # kept" # remove\n')
    assert U.find_line_number(str(path), needle) == line


# ---- HOI4 install and idea categories ------------------------------------------


def test_install_comes_from_the_env_then_the_known_paths(tmp_path, monkeypatch):
    install = tmp_path / "hoi4"
    install.mkdir()
    monkeypatch.setenv("HOI4_PATH", str(install))
    assert U.find_hoi4_install() == str(install)
    assert U.find_hoi4_install(str(install)) == str(install)

    monkeypatch.delenv("HOI4_PATH")
    monkeypatch.setattr(U, "HOI4_INSTALL_PATHS", [str(tmp_path / "missing-install")])
    monkeypatch.setattr(U, "HOI4_DISCOVERY_SOURCES", [])
    assert U.find_hoi4_install() is None

    monkeypatch.setattr(U, "HOI4_DISCOVERY_SOURCES", [lambda: [str(install)]])
    assert U.find_hoi4_install() == str(install)


def test_steam_library_installs_reads_every_library_folder(tmp_path, monkeypatch):
    steam = tmp_path / "Steam"
    other = tmp_path / "Games"
    game = other / "steamapps" / "common" / "Hearts of Iron IV"
    game.mkdir(parents=True)
    escaped_steam = str(steam).replace("\\", "\\\\")
    escaped_other = str(other).replace("\\", "\\\\")
    _write(
        steam / "steamapps" / "libraryfolders.vdf",
        '"libraryfolders"\n{\n'
        f'\t"0"\n\t{{\n\t\t"path"\t\t"{escaped_steam}"\n\t}}\n'
        f'\t"1"\n\t{{\n\t\t"path"\t\t"{escaped_other}"\n\t}}\n}}\n',
    )
    monkeypatch.setattr(U, "_steam_roots", lambda: [str(steam)])
    assert U._steam_library_installs() == [
        os.path.join(str(steam), U._HOI4_GAME_SUBDIR),
        os.path.join(str(other), U._HOI4_GAME_SUBDIR),
    ]
    monkeypatch.setattr(U, "HOI4_INSTALL_PATHS", [])
    monkeypatch.delenv("HOI4_PATH", raising=False)
    assert U.find_hoi4_install() == str(game)

    monkeypatch.setattr(U, "_steam_roots", lambda: [str(tmp_path / "nowhere")])
    assert U._steam_library_installs() == []


def test_editor_settings_installs_parses_jsonc(tmp_path, monkeypatch):
    settings = _write(
        tmp_path / "settings.json",
        "{\n"
        "    // user settings\n"
        '    "cwtools.cache.hoi4": "H:\\\\Games\\\\Hearts of Iron IV",\n'
        '    "mdHoi4Utilities.installPath": "h:\\\\Games\\\\Hearts of Iron IV\\\\",\n'
        '    "mdHoi4Utilities.modFile": "D:\\\\mod\\\\descriptor.mod",\n'
        "}\n",
    )
    monkeypatch.setattr(U, "_editor_settings_files", lambda: [str(settings)])
    assert U._editor_settings_installs() == [
        "H:\\Games\\Hearts of Iron IV",
        "h:\\Games\\Hearts of Iron IV",
    ]

    _write(settings, '{ "editor.tabSize": 4 }\n')
    assert U._editor_settings_installs() == []
    monkeypatch.setattr(U, "_editor_settings_files", lambda: [str(tmp_path / "gone")])
    assert U._editor_settings_installs() == []


def test_idea_categories_read_every_tags_file(tmp_path):
    tags = tmp_path / "common" / "idea_tags"
    _write(
        tags / "00_tags.txt",
        "idea_categories = {\n"
        " selectable = { slot = national_spirit type = national_spirit }\n"
        " hidden = { hidden = yes slot = dynamic_modifier_slots }\n"
        " plain = { type = army_spirit }\n"
        "}\n",
    )
    _write(tags / "not_tags.txt", "not categories = { x = { yes = no } }\n")
    _write(tags / "broken.txt", "idea_categories = { broken = { slot = x\n")
    categories = U.get_all_idea_categories(str(tmp_path))
    assert [category["name"] for category in categories] == [
        "selectable",
        "hidden",
        "plain",
        "broken",
    ]
    assert categories[0]["has_slot"] and categories[0]["type"] == "national_spirit"
    assert categories[1]["hidden"] and categories[1]["has_char_slot"] is False
    assert U.get_non_selectable_idea_categories(str(tmp_path)) == frozenset(
        {"plain", "hidden"}
    )
    assert U.get_slotless_idea_categories(str(tmp_path)) == frozenset({"plain"})


def test_without_idea_tags_the_vanilla_defaults_apply(tmp_path):
    empty = tmp_path / "empty"
    assert U.get_all_idea_categories(str(empty)) == []
    assert U.get_non_selectable_idea_categories(str(empty)) == frozenset(
        {"country", "hidden_ideas"}
    )
    assert U.get_slotless_idea_categories(str(empty)) == frozenset()
