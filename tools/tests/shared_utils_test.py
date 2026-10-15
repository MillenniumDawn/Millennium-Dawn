"""Tests for shared_utils.py."""

import argparse
import multiprocessing
import os
import random
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import shared_utils as U
from shared.suite import initialize_git_repository, run_git
from shared.suite import write_text as _write

# ---- path exclusions -----------------------------------------------------------


@pytest.mark.parametrize(
    "path, skipped",
    [
        (".claude/worktrees/test/events/x.txt", True),
        (r".git\objects\x", True),
        ("resources/reference.txt", True),
        ("common/resources/game-data.txt", False),
        ("map/adjacency_rules.txt", False),
        ("map\\adjacency_rules.txt", False),
        ("map/colors.txt", True),
        (".claude/worktrees/wt/map/adjacency_rules.txt", True),
        ("resources/vanilla/map/adjacency_rules.txt", True),
    ],
)
def test_should_skip_file(path, skipped):
    assert U.should_skip_file(path) is skipped


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


def test_excluded_path_ignores_different_drives(monkeypatch):
    def raise_cross_drive(*_args):
        raise ValueError("path is on another mount")

    monkeypatch.setattr(U.os.path, "relpath", raise_cross_drive)
    assert not U.is_excluded_path("C:/tmp/file.txt", {"resources"}, "D:/repo")
    assert U.is_excluded_path("C:/resources/file.txt", {"resources"}, "D:/repo")


def test_excluded_path_matches_a_directory_component(tmp_path):
    excluded = tmp_path / "common" / "nested" / "tools" / "ignored.txt"
    assert U.is_excluded_path(str(excluded), {"tools"}, str(tmp_path))
    assert not U.is_excluded_path(
        str(tmp_path / "common" / "nested" / "a.TXT"), {"tools"}, str(tmp_path)
    )


# ---- reads and writes ----------------------------------------------------------


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


def test_atomic_writes_of_text_with_a_bom_and_of_bytes(tmp_path):
    target = tmp_path / "nested" / "file.txt"
    U.atomic_write_text(str(target), "café\n", encoding="utf-8-sig", bom=True)
    binary = tmp_path / "nested" / "binary.dat"
    U.atomic_write_bytes(str(binary), b"\x00\xff")
    assert binary.read_bytes() == b"\x00\xff"
    assert target.read_bytes() == b"\xef\xbb\xbfcaf\xc3\xa9\n"
    assert U.read_text_strict(str(target)) == "café\n"
    assert U.read_text_strict(str(target), reject_symlink=False).startswith("café")


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


def test_write_text_under_rejects_escape(tmp_path):
    with pytest.raises(ValueError, match="not under"):
        U.write_text_under(str(tmp_path / ".." / "out.txt"), str(tmp_path), "nope")
    assert not (tmp_path / "out.txt").exists()


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


@pytest.mark.parametrize("needle, line", [("KEY", 1), ("missing", 0)])
def test_find_line_number(tmp_path, needle, line):
    path = _write(tmp_path / "data.txt", 'KEY = "Value # kept" # remove\n')
    assert U.find_line_number(str(path), needle) == line


# ---- staged files --------------------------------------------------------------


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


@pytest.mark.parametrize(
    "include_missing, staged",
    [(False, None), (True, ["common/country_leader/deleted.txt"])],
    ids=["dropped", "kept on request"],
)
def test_staged_files_whose_every_path_is_gone(
    tmp_path, monkeypatch, include_missing, staged
):
    monkeypatch.setenv("MD_STAGED_FILES", "common/country_leader/deleted.txt")

    assert U.get_staged_files(str(tmp_path), include_missing=include_missing) == (
        None if staged is None else [str(tmp_path / rel) for rel in staged]
    )


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


def test_txt_targets_of_a_directory_a_file_and_a_missing_path(tmp_path):
    content = tmp_path / "common" / "nested"
    _write(content / "a.TXT", "a")
    _write(content / "b.yml", "b")
    _write(content / "tools" / "ignored.txt", "ignored")
    a_txt = str(content / "a.TXT")
    assert list(U.iter_txt_targets(str(content), {"tools"})) == [("a.TXT", a_txt)]
    assert list(U.iter_txt_targets(a_txt, set())) == [(a_txt, a_txt)]
    assert list(U.iter_txt_targets(str(content / "missing.txt"), set())) == []


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


def test_idea_category_slots_character_slots_and_types(tmp_path):
    _write(
        tmp_path / "common" / "idea_tags" / "00_idea.txt",
        "idea_categories = {\n"
        " national_status = { slot = religion slot = corruption }\n"
        " military_staff = { character_slot = chief_of_staff }\n"
        " army_spirit = { type = army_spirit slot = army_chief }\n"
        "}\n",
    )
    categories = {c["name"]: c for c in U.get_all_idea_categories(str(tmp_path))}
    assert (
        categories["national_status"]["has_slot"],
        categories["national_status"]["type"],
    ) == (True, None)
    assert categories["military_staff"]["has_char_slot"] is True
    assert categories["army_spirit"]["type"] == "army_spirit"


def test_without_idea_tags_the_vanilla_defaults_apply(tmp_path):
    empty = tmp_path / "empty"
    assert U.get_all_idea_categories(str(empty)) == []
    assert U.get_non_selectable_idea_categories(str(empty)) == frozenset(
        {"country", "hidden_ideas"}
    )
    assert U.get_slotless_idea_categories(str(empty)) == frozenset()


# ---- AI-only gates -------------------------------------------------------------

# An unconditional `is_ai = yes` in visible/available/allowed hides a decision
# from every human; nested under OR/AND/if/limit or a TAG scope it is conditional.


@pytest.mark.parametrize(
    ("block", "expected"),
    [
        ("{\n\t\t\tis_ai = yes\n\t\t}", True),
        ("{ is_ai = yes }", True),
        ("{\n\t\t\tOR = {\n\t\t\t\tis_ai = yes\n\t\t\t}\n\t\t}", False),
        ("{\n\t\t\tGRE = {\n\t\t\t\tis_ai = yes\n\t\t\t}\n\t\t}", False),
        ("{\n\t\t\tif = {\n\t\t\t\tlimit = { is_ai = yes }\n\t\t\t}\n\t\t}", False),
        ("{\n\t\t\tis_ai = no\n\t\t}", False),
        ("{\n\t\t\t# is_ai = yes\n\t\t}", False),
        ("{\n\t\t\tfoo_is_ai = yes\n\t\t}", False),
        ("", False),
    ],
    ids=[
        "flat",
        "single_line",
        "nested_in_or",
        "scoped_to_tag",
        "in_if_limit",
        "is_ai_no",
        "commented",
        "mid_token",
        "empty",
    ],
)
def test_has_flat_is_ai(block, expected):
    assert bool(U.has_flat_is_ai(block)) is expected


@pytest.mark.parametrize(
    "body, block",
    [
        (
            "\tcost = 25\n\tvisible = {\n\t\tis_ai = yes\n\t}\n",
            "{\n\t\tis_ai = yes\n\t}",
        ),
        # A `visible` inside an effect's `limit` is not the object's own gate.
        (
            "\tcomplete_effect = {\n\t\tif = { limit = { visible = { is_ai = yes } } }\n\t}\n",
            "",
        ),
        ("\tcost = 25\n", ""),
    ],
    ids=["own gate", "nested gate of the same name", "no gate"],
)
def test_direct_child_block(body, block):
    assert U.direct_child_block(body, "visible") == block


@pytest.mark.parametrize(
    "body, ai_only",
    [
        ("{\n\tvisible = { is_ai = yes }\n}", True),
        ("\tallowed = { is_ai = yes }\n", True),
        ("\tcost = 25\n\tvisible = {\n\t\tis_ai = yes\n\t}\n", True),
        ("\tavailable = {\n\t\tis_ai = yes\n\t}\n", True),
        ("\tvisible = {\n\t\tOR = { is_ai = yes is_debug = yes }\n\t}\n", False),
        ("\tvisible = { has_country_flag = my_flag }\n", False),
    ],
    ids=[
        "braced body",
        "bare allowed gate",
        "bare visible gate after a field",
        "available gate",
        "nested gate",
        "plain decision",
    ],
)
def test_is_ai_only_block(body, ai_only):
    assert bool(U.is_ai_only_block(body)) is ai_only


def test_flat_block_text_keeps_an_unmatched_trailing_brace():
    # A bare body ending in the `}` of its last child is not a wrapped block;
    # stripping both ends would delete an unrelated brace and desync the depth
    # count of every walk downstream.
    body = "{ a }\n\tvisible = { is_ai = yes }"
    assert U.flat_block_text(body) == body
    assert U.flat_block_text("{ visible = { is_ai = yes } }") == (
        " visible = { is_ai = yes } "
    )


@pytest.mark.parametrize(
    "text, categories",
    [
        (
            "md_ai_category = {\n"
            "\tallowed = { original_tag = JAP }\n"
            "\tvisible = {\n"
            "\t\tis_ai = yes\n"
            "\t\thas_global_flag = MD_some_flag\n"
            "\t}\n"
            "}\n"
            "md_human_category = {\n"
            "\tallowed = { original_tag = JAP }\n"
            "}\n",
            {"md_ai_category": "cat.txt"},
        ),
        (
            "md_templates_category = {\n"
            "\tallowed = {\n"
            "\t\tOR = {\n"
            "\t\t\tis_ai = yes\n"
            "\t\t\tis_debug = yes\n"
            "\t\t}\n"
            "\t}\n"
            "}\n",
            {},
        ),
        ("md_ai_category = {\n\tvisible = {\n\t\t# is_ai = yes\n\t}\n}\n", {}),
        (None, {}),
    ],
    ids=["AI-only category", "debug-gated category", "commented is_ai", "no directory"],
)
def test_ai_only_decision_categories(tmp_path, text, categories):
    if text is not None:
        _write(tmp_path / "common" / "decisions" / "categories" / "cat.txt", text)
    assert U.ai_only_decision_categories(str(tmp_path)) == categories


# ---- brace and quote scanners --------------------------------------------------


def _split(text):
    return text.splitlines(keepends=True)


# case: (text, lines of the block, index after it)
_EXTRACT_BLOCK_CASES = {
    "same-line brace": ("focus = { id = a }\nnext = yes\n", (0, 1), 1),
    # The `{` opens on a later line than the name.
    "next-line brace": ("focus =\n{\n\tid = a\n}\nnext = yes\n", (0, 4), 4),
    "nested block": ("a = {\n\tb = {\n\t\tc = 1\n\t}\n}\ntrailing\n", (0, 5), 5),
    "unclosed block runs to the end": ("a = {\n\tb = 1\n\tc = 2\n", (0, 3), 3),
    "brace inside a comment": ("a = { # stray } brace\n\tb = 1\n}\nafter\n", (0, 3), 3),
    # A driver appends only truthy blocks, so a lost block deletes those lines.
    "over-closing line": ("focus = {\n\tid = a\n} }\nnext = yes\n", (0, 3), 3),
    "nested over-closing line": ("a = {\n\tb = {\n\t} } }\nafter\n", (0, 3), 3),
}


@pytest.mark.parametrize(
    "text, block, end", _EXTRACT_BLOCK_CASES.values(), ids=_EXTRACT_BLOCK_CASES
)
def test_extract_block(text, block, end):
    lines = _split(text)
    assert U.extract_block(lines, 0) == (lines[block[0] : block[1]], end)


def test_leading_stray_brace_advances_index():
    # A stray `}` before any `{` must return an advancing index so a caller
    # looping on it can't spin forever.
    block, end = U.extract_block(_split("}\nfocus = { id = a }\n"), 0)
    assert block == []
    assert end > 0


def _driver(lines):
    """The standardizer driver loop: `i = next_i` unconditionally."""
    out = []
    i = 0
    guard = 0
    while i < len(lines):
        guard += 1
        assert guard <= len(lines) + 5, "extract_block driver loop did not terminate"
        if "{" in lines[i] or "}" in lines[i]:
            block, next_i = U.extract_block(lines, i)
            assert next_i > i
            out.extend(block)
            i = next_i
        else:
            out.append(lines[i])
            i += 1
    return out


def test_driver_loop_over_stray_brace_terminates():
    lines = _split("}\na = {\n\tb = 1\n}\ntrailing\n")
    assert _driver(lines) == lines[1:]


def test_over_closing_driver_loses_no_lines():
    lines = _split("focus = {\n\tid = a\n} }\nnext = yes\n")
    assert _driver(lines) == lines


def test_quoted_string_brace_does_not_break_boundary():
    # A brace inside a quoted string (blanked via blank_quoted_strings, as the
    # standardizers pass their input) must not shift the block boundary.
    raw = 'a = {\n\tlog = "brace } and { inside"\n\tb = 1\n}\nafter\n'
    lines = _split(U.blank_quoted_strings(raw))
    block, end = U.extract_block(lines, 0)
    assert len(block) == 4
    assert end == 4


def test_blank_quoted_strings_escaped_quote_does_not_end_the_string():
    raw = 'log = "a \\"b\\" c { d } e"\nafter = { yes }\n'
    out = U.blank_quoted_strings(raw)
    assert out.count("{") == 1
    assert out.count("}") == 1
    assert 'log = "' in out
    assert out.endswith("after = { yes }\n")


@pytest.mark.parametrize(
    "raw, keep, kept, blanked",
    [
        (
            'has_dlc = "By Blood Alone" log = "hide me"\n',
            '"By Blood Alone"',
            'has_dlc = "By Blood Alone"',
            "hide me",
        ),
        ('x = "a { b }"\nyes', '"a { b }"', 'x = "a { b }"\nyes', None),
    ],
    ids=["one of two strings", "only string"],
)
def test_blank_quoted_strings_keeps_the_listed_quotes(raw, keep, kept, blanked):
    out = U.blank_quoted_strings(raw, {raw.index(keep)})
    assert kept in out
    if blanked:
        assert blanked not in out


def _reference_blank_quoted_strings(text, keep_start=None):
    if '"' not in text:
        return text
    out = list(text)
    in_str = False
    start = -1
    keep = keep_start or ()
    for i, c in enumerate(text):
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            if not in_str:
                start = i
            in_str = not in_str
        elif in_str and c != "\n" and start not in keep:
            out[i] = " "
    return "".join(out)


def _reference_find_matching_brace(text, open_idx):
    # Every character from open_idx, negative offsets included.
    level, quoted, pos = 0, False, open_idx
    while pos < len(text):
        char = text[pos]
        toggles = char == '"' and text[pos - 1] != "\\"
        quoted ^= toggles
        if not quoted and not toggles and char in "{}":
            level += 1 if char == "{" else -1
            if char == "}" and level == 0:
                return pos
        pos += 1
    return -1


_SCANNER_CASES = {
    "brace in a string": 'a = { log = "x } y {" b = 1 }\n',
    "hash in a string": 'a = { log = "#1 } done" }\n',
    "comment with braces": "a = { b = 1 } # c = { d }\n}\n",
    "unbalanced": "a = { b = { c = 1 }\n",
    "three deep": "a = {\n\tb = {\n\t\tc = { d = 1 }\n\t}\n}\n",
    "first and last line": '{ "x" }\nmid\n{ "y" }',
    "empty": "",
    "no trailing newline": 'a = { log = "q" }',
    "crlf": 'a = {\r\n\tlog = "x\r\ny"\r\n}\r\n',
    "escaped quote": 'log = "a \\"b\\" { c"\nd = { }\n',
    "backslash run before a quote": 'log = "a\\\\" b = { "c\\\\\\"" }\n',
    "unterminated string": 'a = { log = "never closed }\n',
    "adjacent strings": 'a = { "one""two" "" }\n',
    "quote first": '"{" = { x }',
}


@pytest.mark.parametrize("text", _SCANNER_CASES.values(), ids=_SCANNER_CASES.keys())
def test_blank_quoted_strings_matches_the_reference_loop(text):
    quotes = [i for i, c in enumerate(text) if c == '"']
    for keep in [None, set(quotes)] + [{q} for q in quotes]:
        assert U.blank_quoted_strings(text, keep) == _reference_blank_quoted_strings(
            text, keep
        )


def _brace_outcome(find, text, open_idx):
    # A quote at text[-len] makes both versions index before the text.
    try:
        return find(text, open_idx)
    except IndexError:
        return "IndexError"


def _same_brace_outcome(text, open_idx):
    return _brace_outcome(U.find_matching_brace, text, open_idx) == _brace_outcome(
        _reference_find_matching_brace, text, open_idx
    )


@pytest.mark.parametrize("text", _SCANNER_CASES.values(), ids=_SCANNER_CASES.keys())
def test_find_matching_brace_matches_the_reference_loop(text):
    # Negative offsets walk the tail first, as indexing from the end does.
    for open_idx in range(-len(text) - 1, len(text) + 2):
        assert _same_brace_outcome(text, open_idx), open_idx


def test_text_scanners_match_their_reference_loops_on_random_input():
    rng = random.Random(20261002)
    alphabet = ['"', "\\", "{", "}", "#", "a", " ", "\n", "\r"]
    for _ in range(3000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 20)))
        keep = {i for i, c in enumerate(text) if c == '"' and rng.random() < 0.5}
        assert U.blank_quoted_strings(text, keep) == _reference_blank_quoted_strings(
            text, keep
        ), repr(text)
        open_idx = rng.randint(-len(text) - 1, len(text) + 1)
        assert _same_brace_outcome(text, open_idx), (text, open_idx)


@pytest.mark.parametrize(
    "text, expected",
    [('x = { log = "}" value = { yes } }', 32), ("x = {", -1)],
    ids=["quoted brace and nested block", "unclosed"],
)
def test_find_matching_brace_from_the_opener(text, expected):
    assert U.find_matching_brace(text, 4) == expected


@pytest.mark.parametrize(
    "text, expected",
    [("name = { value = 1 } tail", (" value = 1 ", 20)), ("name = no block", ("", -1))],
    ids=["block", "no block"],
)
def test_extract_block_from_text(text, expected):
    assert U.extract_block_from_text(text, 0) == expected


@pytest.mark.parametrize(
    "text, expected",
    [("inner } tail", (7, True)), ("inner", (5, False))],
    ids=["closed", "unclosed"],
)
def test_find_unquoted_block_end(text, expected):
    assert U.find_unquoted_block_end(text, 0) == expected


@pytest.mark.parametrize(
    "line, expected",
    [("foo # comment", "foo "), ('foo = "# not a comment"', 'foo = "# not a comment"')],
    ids=["comment", "hash in quotes"],
)
def test_strip_inline_comment(line, expected):
    assert U.strip_inline_comment(line) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ('a # x\n# whole\nlog = "# keep"', 'a \n\nlog = "# keep"'),
        ('log = "a \\" # keep" # x', 'log = "a \\" # keep" '),
    ],
    ids=["comment lines", "escaped quote"],
)
def test_strip_comments_keeps_quoted_hashes(text, expected):
    assert U.strip_comments(text) == expected


# ---- script walkers and line helpers -------------------------------------------


def test_line_offsets_map_back_to_lines():
    offsets = U.compute_line_offsets("a\nb\n")
    assert offsets == [1, 3]
    assert U.line_for_offset(offsets, 1) == 1


def test_line_of_counts_from_one():
    text = "a\nb\nc"
    assert U.line_of(text, 0) == 1
    assert U.line_of(text, text.index("c")) == 3


@pytest.mark.parametrize(
    "names, fragments, expected",
    [({"abc": 1, "x": 2}, ("b",), ["x"]), (["abc", "x"], (), ["abc", "x"])],
    ids=["drops a match", "no fragments"],
)
def test_drop_partial_matches(names, fragments, expected):
    assert U.drop_partial_matches(names, fragments) == expected


# case: (body, (key, scalar, block) per statement)
_STATEMENT_CASES = {
    "scalar, block and quoted values": (
        'name = "DEN_AI" option = { name = HISTORICAL } flag = X',
        [
            ("name", "DEN_AI", None),
            ("option", None, " name = HISTORICAL "),
            ("flag", "X", None),
        ],
    ),
    "nested blocks are not yielded twice": (
        "a = { b = { c = 1 } } d = 2",
        [("a", None, " b = { c = 1 } "), ("d", "2", None)],
    ),
    "escaped quote keeps the text inside the string": (
        'desc = "text \\" x = 99" x = 2',
        [("desc", 'text \\" x = 99', None), ("x", "2", None)],
    ),
    "unclosed quoted scalar stops the walk": ('desc = "text \\" x = 99', []),
    # `>=` used to split into `>` plus a stray `=` scalar, losing the value.
    "two-character operator keeps its value": ("x >= 5", [("x", "5", None)]),
    "at sign belongs to the key": (
        "trade_agreement@GER = yes",
        [("trade_agreement@GER", "yes", None)],
    ),
    "unbalanced block stops the walk": ("a = { b = 1 c = 2", []),
}


@pytest.mark.parametrize(
    "body, statements", _STATEMENT_CASES.values(), ids=_STATEMENT_CASES
)
def test_iter_statements(body, statements):
    assert list(U.iter_statements(body)) == statements


def test_operators_are_reported_separately():
    body = "has_stability > 0.66 threat < 0.4 date >= 2005.1.1"
    assert list(U.iter_statement_ops(body)) == [
        ("has_stability", ">", "0.66", None),
        ("threat", "<", "0.4", None),
        ("date", ">=", "2005.1.1", None),
    ]


def _focus(body):
    return "\tfocus = {\n" + body + "\n\t}\n"


def test_focus_blocks_read_id_kind_and_line():
    text = "\n" + _focus("\t\tid = a\n\t\tx = 1")
    assert list(U.iter_focus_blocks(text)) == [
        ("a", "focus", 2, "\n\t\tid = a\n\t\tx = 1\n\t")
    ]


@pytest.mark.parametrize(
    "text, blocks",
    [
        (
            "shared_focus = {\n\tid = s\n}\n"
            "joint_focus = {\n\tid = j\n}\n"
            "focus = {\n\tid = f\n}\n",
            [("s", "shared_focus"), ("j", "joint_focus"), ("f", "focus")],
        ),
        (_focus("\t\tx = 1") + _focus("\t\tid = b"), [("b", "focus")]),
        (_focus("\t\tid = a\n\t\tprerequisite = { focus = b }"), [("a", "focus")]),
        ("focus = {\n\tid = a\n", []),
    ],
    ids=[
        "shared and joint focuses",
        "block without an id",
        "nested focus keyword",
        "unclosed block",
    ],
)
def test_iter_focus_blocks(text, blocks):
    assert [(i, k) for i, k, _, _ in U.iter_focus_blocks(text)] == blocks


@pytest.mark.parametrize(
    "content, encoding, keep_quotes, statements",
    [
        (
            'a = 1 # note\nlog = "x = { }"\n',
            "utf-8",
            False,
            [("a", "1", None), ("log", " " * len("x = { }"), None)],
        ),
        ('name = "GER_idea"\n', "utf-8", True, [("name", "GER_idea", None)]),
        ("a = 1\n", "utf-8-sig", False, [("a", "1", None)]),
    ],
    ids=["comments and quotes blanked", "quotes kept", "BOM stripped"],
)
def test_read_script(tmp_path, content, encoding, keep_quotes, statements):
    path = tmp_path / "f.txt"
    with path.open("w", encoding=encoding, newline="") as handle:
        handle.write(content)
    text = U.read_script(str(path), keep_quotes=keep_quotes)
    assert list(U.iter_statements(text)) == statements


# ---- spacing and block compaction ----------------------------------------------

# `{`, `}` and `=` carry single spaces; strings, comments and indentation stay
# byte-exact (tools/standardization/README.md).
_SPACING_CASES = {
    "inline block": (
        "\t\t\t\tNOT = {country_exists = ENG}",
        "\t\t\t\tNOT = { country_exists = ENG }",
    ),
    "nested block and double close": (
        "\t\tNOT = {FRA={has_idea = EU_member}}",
        "\t\tNOT = { FRA = { has_idea = EU_member } }",
    ),
    "equals": (
        "\tNOT = {western_liberals_are_in_power=yes}",
        "\tNOT = { western_liberals_are_in_power = yes }",
    ),
    "quoted string": (
        '\tlog = "[GetDateText]: a=b {c}  d"',
        '\tlog = "[GetDateText]: a=b {c}  d"',
    ),
    "inline comment": (
        "\tfoo = {bar = yes}\t# why {this} matters",
        "\tfoo = { bar = yes } # why {this} matters",
    ),
    "whole-line comment": ("\t# a note = {x}", "\t# a note = {x}"),
    "blank line": ("", ""),
    "indent-only line": ("\t\t", ""),
    "indentation": ("\t\t\tid = focus", "\t\t\tid = focus"),
    "already correct": (
        "\tavailable = { has_country_flag = some_flag }",
        "\tavailable = { has_country_flag = some_flag }",
    ),
    "empty block": ("\ton_add = {}", "\ton_add = {}"),
    "empty spaced block": ("\tsearch_filters = { }", "\tsearch_filters = { }"),
    "not-equals": ("\tcheck_variable = {x != 3}", "\tcheck_variable = { x != 3 }"),
    "greater-or-equal": ("\tcheck_variable = {x>=3}", "\tcheck_variable = { x >= 3 }"),
    "spaced comparison": ("\thas_war_support > 0.5", "\thas_war_support > 0.5"),
    "bare greater-than": ("\thas_war_support>0.5", "\thas_war_support > 0.5"),
    "bare less-than": ("\tvalue<3", "\tvalue < 3"),
    "extra whitespace": ("\tcost   =    10", "\tcost = 10"),
    "trailing whitespace": ("\tcost = 10   ", "\tcost = 10"),
}


@pytest.mark.parametrize("line, expected", _SPACING_CASES.values(), ids=_SPACING_CASES)
def test_normalize_spacing(line, expected):
    assert U.normalize_spacing(line) == expected


def test_normalize_spacing_is_idempotent():
    once = U.normalize_spacing("\tNOT={FRA={has_idea=EU_member}}")
    assert U.normalize_spacing(once) == once


def test_compact_block_drops_blank_lines_and_trailing_space():
    assert U.compact_block(["a\n", "\n", " b  \n"]) == ["a", " b"]


def test_collapse_ws_outside_quotes():
    assert U.collapse_ws_outside_quotes('  a   "b  c"  d  ') == 'a "b  c" d'


@pytest.mark.parametrize(
    "lines, base_line",
    [
        (["ai_will_do = {\n", " factor = 2\n", "}\n"], " base = 2\n"),
        (["ai_will_do = {\n", " base = 2\n", "}\n"], " base = 2\n"),
    ],
    ids=["root factor", "already base"],
)
def test_convert_root_factor_to_base(lines, base_line):
    assert U.convert_root_factor_to_base(lines)[1] == base_line


@pytest.mark.parametrize(
    "lines, expected",
    [
        (["a = {\n", " b = 1\n", "}\n"], ["a = { b = 1 }"]),
        (["a = { # keep\n", " b = 1\n", "}\n"], ["a = { # keep", "\tb = 1", "}"]),
    ],
    ids=["one leaf", "commented opener"],
)
def test_collapse_or_compact(lines, expected):
    assert U.collapse_or_compact(lines) == expected


def test_collapse_or_compact_reindents_a_multi_line_block():
    # Issue #4650: nested lines written at the wrong depth kept their tabs.
    block = [
        "\t\t34 = {\n",
        "\t\t\tadd_building_construction = {\n",
        "\t\t\ttype = infrastructure\n",
        "\t\t\tlevel = 1\n",
        "\t\t\t}\n",
        "\t\t}\n",
    ]
    expected = [
        "\t\t34 = {",
        "\t\t\tadd_building_construction = {",
        "\t\t\t\ttype = infrastructure",
        "\t\t\t\tlevel = 1",
        "\t\t\t}",
        "\t\t}",
    ]
    assert U.collapse_or_compact(block) == expected
    assert U.collapse_or_compact([line.lstrip() for line in block], "\t\t") == expected


_REWARD = [
    "\t\tcompletion_reward = {",
    '\t\t\tlog = "x"',
    "\t\t\tset_temp_variable = {",
    "\t\t\t\tparty_popularity_increase = 0.1",
    "\t\t\t}",
    "\t\t\thas_country_leader = {",
    '\t\t\t\tname = "Serzh Sargsyan"',
    "\t\t\t\truling_only = yes",
    "\t\t\t}",
    "\t\t}",
]
_REWARD_COLLAPSED = [
    "\t\tcompletion_reward = {",
    '\t\t\tlog = "x"',
    "\t\t\tset_temp_variable = { party_popularity_increase = 0.1 }",
    "\t\t\thas_country_leader = {",
    '\t\t\t\tname = "Serzh Sargsyan"',
    "\t\t\t\truling_only = yes",
    "\t\t\t}",
    "\t\t}",
]


def test_collapse_nested_blocks_collapses_one_leaf_children_once():
    assert U.collapse_nested_blocks(_REWARD) == _REWARD_COLLAPSED
    assert U.collapse_nested_blocks(_REWARD_COLLAPSED) == _REWARD_COLLAPSED
    assert U.collapse_or_compact(_REWARD) == _REWARD_COLLAPSED


# case: (block lines, collapsed lines)
_NESTED_CASES = {
    # Innermost first, at any depth.
    "innermost first": (
        [
            "a = {",
            "\tb = {",
            "\t\tc = {",
            "\t\t\tx = 1",
            "\t\t}",
            "\t\ty = 2",
            "\t}",
            "}",
        ],
        ["a = {", "\tb = {", "\t\tc = { x = 1 }", "\t\ty = 2", "\t}", "}"],
    ),
    "a child with a comment stays multi-line": (
        ["a = {", "\tb = {", "\t\tx = 1 # note", "\t}", "\tc = 3", "}"],
        ["a = {", "\tb = {", "\t\tx = 1 # note", "\t}", "\tc = 3", "}"],
    ),
    "unbalanced input is left alone": (
        ["a = {", "\tb = {", "\t\tx = 1", "}"],
        ["a = {", "\tb = {", "\t\tx = 1", "}"],
    ),
    "one line": (["a = { b = 1 }"], ["a = { b = 1 }"]),
}


@pytest.mark.parametrize(
    ("lines", "expected"), _NESTED_CASES.values(), ids=_NESTED_CASES
)
def test_collapse_nested_blocks(lines, expected):
    assert U.collapse_nested_blocks(lines) == expected


# A multi-token list is not a single leaf; a one-token list still collapses.
@pytest.mark.parametrize(
    "lines, expected",
    [
        (
            [
                "\t\t\treduce_focus_completion_cost = {",
                "\t\t\t\tcost = 20",
                "\t\t\t\tfocus = {",
                "\t\t\t\t\tCHI_project_921",
                "\t\t\t\t\tCHI_shenzhou_program",
                "\t\t\t\t}",
                "\t\t\t}",
            ],
            None,
        ),
        (
            [
                "\tx = {",
                "\t\tfocus = {",
                "\t\t\tJAP_blue_water_navy",
                "\t\t}",
                "\t\tcost = 35",
                "\t}",
            ],
            ["\tx = { focus = { JAP_blue_water_navy } cost = 35 }"],
        ),
    ],
    ids=["two tokens", "one token"],
)
def test_token_lists_collapse_only_with_one_token(lines, expected):
    assert U.collapse_or_compact(lines) == (lines if expected is None else expected)


# ---- worker budget -------------------------------------------------------------

# case: (MD_MAX_WORKERS, CI, budget)
_BUDGET_CASES = {
    "explicit override": ("4", None, 4),
    "local run keeps two cores free": ("0", None, 6),
    "CI uses every core": ("0", "true", 8),
    "unparsable override is ignored": ("not-a-number", "true", 8),
}


@pytest.mark.parametrize(
    ("workers", "ci", "expected"), _BUDGET_CASES.values(), ids=_BUDGET_CASES
)
def test_cpu_budget(monkeypatch, workers, ci, expected):
    monkeypatch.setenv("MD_MAX_WORKERS", workers)
    monkeypatch.setattr(U.os, "cpu_count", lambda: 8)
    if ci is None:
        monkeypatch.delenv("CI", raising=False)
    else:
        monkeypatch.setenv("CI", ci)
    assert U.cpu_budget() == expected


@pytest.mark.parametrize("share, expected", [(3, (3, 2)), (0, (1, 6))])
def test_split_cpu_budget(monkeypatch, share, expected):
    monkeypatch.setenv("MD_MAX_WORKERS", "0")
    monkeypatch.setattr(U.os, "cpu_count", lambda: 8)
    monkeypatch.delenv("CI", raising=False)
    assert U.split_cpu_budget(share) == expected


# ---- logging and timing --------------------------------------------------------


def test_debug_messages_are_hidden(capsys):
    U.log_message("DEBUG", "hidden")
    assert capsys.readouterr().err == ""


def test_no_color_env_drops_colour_codes(monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "1")
    U.log_message("INFO", "visible")
    U.log_message("NOTICE", "unknown", use_colors=False)
    captured = capsys.readouterr().err
    assert "INFO: visible" in captured
    assert "NOTICE: unknown" in captured
    assert "\033[" not in captured


def test_timing_disabled_prints_nothing(monkeypatch, capsys):
    monkeypatch.setenv("MD_TIMING", "0")
    assert not U.timing_enabled()
    assert U.Timer("disabled").enabled is False
    assert U.Timer("manual", enabled=False).stop() == 0.0
    U.print_timing_summary([])
    U.print_timing_summary([("step", 1.0)])
    assert capsys.readouterr().err == ""


def test_timing_summary_prints_when_enabled(capsys):
    with U.Timer("context", enabled=True):
        pass
    U.print_timing_summary([("first", 0.0), ("second", 1.0)])
    assert "Timing summary" in capsys.readouterr().err


# ---- argument parsers ----------------------------------------------------------


def test_standard_file_arguments():
    parser = argparse.ArgumentParser()
    U.add_standard_file_arguments(parser, input_help="Custom input")
    assert "Custom input" in parser.format_help()
    parsed = parser.parse_args(["source.txt", "-o", "dest.txt", "-b", "-v"])
    assert (parsed.input_file, parsed.output, parsed.backup, parsed.verbose) == (
        "source.txt",
        "dest.txt",
        True,
        True,
    )
    with pytest.raises(SystemExit):
        parser.parse_args(["source.txt", "--no-color"])


def test_validation_parser():
    parsed = U.create_validation_parser("validation").parse_args(
        ["--path", "/mod", "--strict", "--staged", "--no-cache", "--workers", "2"]
    )
    assert (parsed.path, parsed.strict, parsed.staged, parsed.no_cache) == (
        "/mod",
        True,
        True,
        True,
    )
    assert parsed.workers == 2


def test_linting_parser_takes_extra_arguments_and_can_drop_diff_mode():
    def add_extra(parser):
        parser.add_argument("--extra", action="store_true")

    lint = U.create_linting_parser("lint", include_diff=False, extra_args_fn=add_extra)
    parsed = lint.parse_args(["--mode", "staged", "--files", "x.txt", "--extra"])
    assert (parsed.mode, parsed.files, parsed.extra) == ("staged", ["x.txt"], True)
    with pytest.raises(SystemExit):
        lint.parse_args(["--mode", "diff"])


# ---- file collection by mode ---------------------------------------------------


def test_named_files_that_are_missing_are_warned_about(tmp_path, capsys):
    existing = _write(tmp_path / "one.txt", "x")
    args = SimpleNamespace(
        filenames=[str(existing), str(tmp_path / "gone.txt")], files=None, mode="all"
    )
    assert U.collect_files_by_mode(args, str(tmp_path)) == [str(existing)]
    assert "not found" in capsys.readouterr().out


# case: (mode, --files given, include_interface, git diff call expected)
_MODE_CASES = {
    "explicit files skip git": ("all", True, False, None),
    "diff mode": (
        "diff",
        False,
        False,
        {"base_branch": "release", "include_interface": False},
    ),
    "staged mode": (
        "staged",
        False,
        True,
        {"staged_only": True, "include_interface": True},
    ),
}


@pytest.mark.parametrize(
    ("mode", "files", "include_interface", "call"),
    _MODE_CASES.values(),
    ids=_MODE_CASES,
)
def test_collect_files_by_mode(
    tmp_path, monkeypatch, mode, files, include_interface, call
):
    existing = str(_write(tmp_path / "one.txt", "x"))
    calls = []
    monkeypatch.setattr(
        U, "get_git_diff_files", lambda **kwargs: calls.append(kwargs) or [existing]
    )
    args = SimpleNamespace(
        filenames=[],
        files=[existing] if files else None,
        mode=mode,
        base_branch="release",
    )
    assert U.collect_files_by_mode(
        args, str(tmp_path), include_interface=include_interface
    ) == [existing]
    assert calls == ([] if call is None else [call])


def test_all_mode_walks_the_tree(tmp_path, monkeypatch):
    existing = str(_write(tmp_path / "one.txt", "x"))
    monkeypatch.setattr(U, "get_all_txt_files", lambda root, **kwargs: [existing])
    args = SimpleNamespace(filenames=[], files=None, mode="all")
    assert U.collect_files_by_mode(args, str(tmp_path)) == [existing]


# ---- process pool --------------------------------------------------------------


@pytest.mark.parametrize(
    "items, workers", [(["a", "b"], 1), ([], 4)], ids=["one worker", "no items"]
)
def test_run_with_pool_runs_in_process(items, workers):
    assert U.run_with_pool(str.upper, items, workers=workers) == [
        item.upper() for item in items
    ]


class _FakePool:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def map(self, func, items, **kwargs):
        self.map_kwargs = kwargs
        return [func(item) for item in items]


@pytest.mark.parametrize("chunksize", [3, None], ids=["given", "computed"])
def test_run_with_pool_maps_over_a_pool(monkeypatch, chunksize):
    monkeypatch.setattr(multiprocessing, "Pool", _FakePool)
    kwargs = {} if chunksize is None else {"chunksize": chunksize}
    assert U.run_with_pool(str.upper, list("abcdefghij"), workers=2, **kwargs) == list(
        "ABCDEFGHIJ"
    )


# ---- run_validator_main --------------------------------------------------------


class _FailingValidator:
    created = {}

    def __init__(self, mod_path, **kwargs):
        _FailingValidator.created = {"path": mod_path, "kwargs": kwargs}

    def run_all_validations(self):
        return 1


class _CleanValidator:
    def __init__(self, *_args, **_kwargs):
        pass

    def run_all_validations(self):
        return 0


def test_strict_run_with_findings_exits_one_and_passes_the_arguments(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)

    def extra(parser):
        parser.add_argument("--flavor", default="plain")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validator",
            "--path",
            str(tmp_path),
            "--strict",
            "--no-cache",
            "--flavor",
            "fast",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        U.run_validator_main(_FailingValidator, extra_args_fn=extra)
    assert exc.value.code == 1
    created = _FailingValidator.created
    assert created["path"] == str(tmp_path.resolve())
    assert (created["kwargs"]["flavor"], created["kwargs"]["no_cache"]) == (
        "fast",
        True,
    )
    assert os.environ["MD_NO_CACHE"] == "1"


# case: (path under tmp_path, validator, exit code)
_MAIN_PATH_CASES = {
    "a file, not a directory": ("not-a-dir", _CleanValidator, 1),
    "a missing path": ("gone", _CleanValidator, 1),
    "a clean run": (".", _CleanValidator, 0),
}


@pytest.mark.parametrize(
    ("path", "validator", "code"), _MAIN_PATH_CASES.values(), ids=_MAIN_PATH_CASES
)
def test_run_validator_main_exit_codes(tmp_path, monkeypatch, path, validator, code):
    _write(tmp_path / "not-a-dir", "x")
    monkeypatch.setattr(sys, "argv", ["validator", "--path", str(tmp_path / path)])
    with pytest.raises(SystemExit) as exc:
        U.run_validator_main(validator)
    assert exc.value.code == code
