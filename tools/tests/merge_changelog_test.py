import subprocess
import sys
from pathlib import Path

import merge_changelog
import pytest
from check_changelog import check_lines
from merge_changelog import merge_text
from shared.suite import initialize_git_repository, run_git

SCRIPT = Path(__file__).resolve().parents[1] / "merge_changelog.py"
PARTY_LINE = " - Standardized party names for the countries: DEN, EGY{}\n"
TANK_LINE = " - [GER] Added the Leopard 2A8 tank variant{}\n"


def changelog(*content):
    return "v2.0.1\n\nContent:\n" + "".join(content) + "\nBugfix:\n - Fixed a bug\n"


def test_both_sides_append_to_the_same_section():
    base = changelog(" - A\n")
    ours = changelog(" - A\n", " - Main entry\n")
    theirs = changelog(" - A\n", " - PR entry\n")

    assert merge_text(base, ours, theirs) == changelog(
        " - A\n", " - Main entry\n", " - PR entry\n"
    )


def test_both_sides_extend_the_same_tag_list():
    base = changelog(PARTY_LINE.format(""), " - B\n")
    ours = changelog(PARTY_LINE.format(", FIJ"), " - B\n", " - Main entry\n")
    theirs = changelog(PARTY_LINE.format(", GEO"), " - B\n", " - PR entry\n")

    assert merge_text(base, ours, theirs) == changelog(
        PARTY_LINE.format(", FIJ, GEO"), " - B\n", " - Main entry\n", " - PR entry\n"
    )


def test_entry_already_on_main_is_not_duplicated():
    base = changelog(" - A\n")
    ours = changelog(" - A\n", " - Shared entry\n", " - Main entry\n")
    theirs = changelog(" - A\n", "  - Shared entry\n", " - PR entry\n")

    assert merge_text(base, ours, theirs) == changelog(
        " - A\n", " - Shared entry\n", " - Main entry\n", " - PR entry\n"
    )


def test_pr_edit_lands_next_to_main_append():
    base = changelog(TANK_LINE.format(""))
    ours = changelog(TANK_LINE.format(""), " - Main entry\n")
    theirs = changelog(TANK_LINE.format(" (Issue #1)"), " - PR entry\n")

    assert merge_text(base, ours, theirs) == changelog(
        TANK_LINE.format(" (Issue #1)"), " - Main entry\n", " - PR entry\n"
    )


def test_conflicting_word_edits_stay_unresolved():
    base = changelog(" - Added a red tank\n")
    ours = changelog(" - Added a blue tank\n")
    theirs = changelog(" - Added a green tank\n")

    assert merge_text(base, ours, theirs) is None


def test_pr_deleting_an_entry_main_edited_stays_unresolved():
    base = changelog(TANK_LINE.format(""), " - B\n")
    ours = changelog(TANK_LINE.format(" (Issue #1)"), " - B\n")
    theirs = changelog(" - B\n")

    assert merge_text(base, ours, theirs) is None


def test_main_replacing_an_entry_the_pr_edited_stays_unresolved():
    base = changelog(TANK_LINE.format(""))
    ours = changelog(" - [GER] Added the Puma IFV variant\n")
    theirs = changelog(TANK_LINE.format(" (Issue #7)"))

    assert merge_text(base, ours, theirs) is None


def test_pr_replacing_an_entry_main_edited_stays_unresolved():
    base = changelog(TANK_LINE.format(""))
    ours = changelog(TANK_LINE.format(" (Issue #1)"))
    theirs = changelog(" - [GER] Added the Puma IFV variant\n")

    assert merge_text(base, ours, theirs) is None


def test_tag_both_sides_added_is_not_duplicated():
    base = changelog(PARTY_LINE.format(""))
    ours = changelog(PARTY_LINE.format(", FIJ"))
    theirs = changelog(PARTY_LINE.format(", FIJ, GEO"))

    assert merge_text(base, ours, theirs) == changelog(PARTY_LINE.format(", FIJ, GEO"))


def test_pr_deleting_an_entry_main_left_alone_merges():
    base = changelog(" - Old\n")
    ours = changelog(" - Old\n", " - Main\n")
    theirs = changelog()

    assert merge_text(base, ours, theirs) == changelog(" - Main\n")


def test_pr_entry_keeps_its_place_between_main_edits():
    base = changelog(TANK_LINE.format(""), PARTY_LINE.format(""))
    ours = changelog(TANK_LINE.format(" (Issue #1)"), PARTY_LINE.format(", FIJ"))
    theirs = changelog(TANK_LINE.format(""), " - New\n", PARTY_LINE.format(""))

    assert merge_text(base, ours, theirs) == changelog(
        TANK_LINE.format(" (Issue #1)"), " - New\n", PARTY_LINE.format(", FIJ")
    )


def test_pr_entry_stays_in_its_category_when_main_adds_the_next_one():
    graphics = "\nGraphics:\n - Main icon\n"
    base = changelog(" - A\n")
    ours = changelog(" - A\n", " - Main entry\n", graphics)
    theirs = changelog(" - A\n", " - PR entry\n")

    assert merge_text(base, ours, theirs) == changelog(
        " - A\n", " - Main entry\n", " - PR entry\n", graphics
    )


def test_pr_entry_joins_the_category_both_sides_added():
    database = "\nDatabase:\n - Main unit\n"
    base = changelog(" - A\n")
    ours = changelog(" - A\n", "\nGraphics:\n - Main icon\n", database)
    theirs = changelog(" - A\n", "\nGraphics:\n - PR icon\n")

    assert merge_text(base, ours, theirs) == changelog(
        " - A\n", "\nGraphics:\n - Main icon\n", " - PR icon\n", database
    )


def test_pr_category_main_lacks_keeps_its_entries():
    graphics = "\nGraphics:\n - Main icon\n"
    database = "\nDatabase:\n - PR unit\n"
    base = changelog(" - A\n")

    assert merge_text(
        base, changelog(" - A\n", graphics), changelog(" - A\n", database)
    ) == changelog(" - A\n", graphics, database)


def test_pr_entry_follows_its_category_into_the_version_main_started():
    ours = "v2.0.2\n\nContent:\n - New feature\n{}\nBugfix:\n - New fix\n"
    theirs = changelog(" - A\n", " - PR entry\n")

    assert merge_text(changelog(" - A\n"), ours.format(""), theirs) == ours.format(
        " - PR entry\n"
    )


def test_pr_entry_whose_category_main_dropped_stays_unresolved():
    ours = "v2.0.2\n\nBugfix:\n - New fix\n"
    theirs = changelog(" - A\n", " - PR entry\n")

    assert merge_text(changelog(" - A\n"), ours, theirs) is None


def commit_changelog(repository, branch, text):
    run_git(repository, "checkout", "--quiet", "-B", branch, "base")
    (repository / "Changelog.txt").write_bytes(text.encode("utf-8"))
    run_git(repository, "commit", "--quiet", "-am", branch)


def merge_tree(repository, ours, theirs):
    return subprocess.run(
        ["git", "merge-tree", "--write-tree", ours, theirs],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )


def test_merge_tree_uses_the_driver(tmp_path):
    (tmp_path / "Changelog.txt").write_bytes(changelog(PARTY_LINE.format("")).encode())
    initialize_git_repository(tmp_path, "Changelog.txt")
    run_git(tmp_path, "branch", "base")
    (tmp_path / ".git" / "info" / "attributes").write_text(
        "Changelog.txt merge=changelog\n"
    )
    python = Path(sys.executable).as_posix()
    run_git(
        tmp_path,
        "config",
        "merge.changelog.driver",
        f'"{python}" "{SCRIPT.as_posix()}" %O %A %B',
    )
    commit_changelog(tmp_path, "main-side", changelog(PARTY_LINE.format(", FIJ")))
    commit_changelog(tmp_path, "pr-side", changelog(PARTY_LINE.format(", GEO")))
    commit_changelog(tmp_path, "pr-clash", changelog(" - Something else\n"))

    result = merge_tree(tmp_path, "main-side", "pr-side")
    assert result.returncode == 0, result.stdout
    tree = result.stdout.split()[0]
    merged = run_git(tmp_path, "cat-file", "-p", f"{tree}:Changelog.txt").stdout
    assert merged == changelog(PARTY_LINE.format(", FIJ, GEO"))

    assert merge_tree(tmp_path, "main-side", "pr-clash").returncode == 1


def _run_main(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), *(str(arg) for arg in args)])
    return merge_changelog.main()


def test_fix_cli_sorts_without_losing_duplicates_or_touching_history(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "Changelog.txt"
    old = "\nv2.0.1\nContent:\n - [USA] Old\n - Global old\n"
    path.write_bytes(
        changelog(" - [USA] U\n", " - Global\n", " - Global\n").encode() + old.encode()
    )
    monkeypatch.chdir(tmp_path)
    assert _run_main(monkeypatch, "--fix") == 0
    assert (
        path.read_bytes()
        == (changelog(" - Global\n", " - Global\n", " - [USA] U\n") + old).encode()
    )
    assert "Fixed changelog ordering" in capsys.readouterr().out
    first = path.read_bytes()
    assert _run_main(monkeypatch, "--fix", path) == 0
    assert path.read_bytes() == first


def test_driver_cli_sorts_both_sides_insertions(tmp_path, monkeypatch):
    base, ours, theirs = (tmp_path / name for name in ("base", "ours", "theirs"))
    base.write_bytes(changelog().encode())
    ours.write_bytes(changelog(" - [USA] U\n").encode())
    theirs.write_bytes(changelog(" - [ENG] E\n", " - Global\n").encode())
    assert _run_main(monkeypatch, base, ours, theirs) == 0
    assert (
        ours.read_bytes()
        == changelog(" - Global\n", " - [ENG] E\n", " - [USA] U\n").encode()
    )
    assert check_lines(ours.read_text(encoding="utf-8").splitlines()) == []


def test_driver_cli_leaves_unresolved_edits_untouched(tmp_path, monkeypatch):
    paths = [tmp_path / name for name in ("base", "ours", "theirs")]
    for path, color in zip(paths, ("red", "blue", "green")):
        path.write_bytes(changelog(f" - Added a {color} tank\n").encode())
    original = paths[1].read_bytes()
    assert _run_main(monkeypatch, *paths) == 1
    assert paths[1].read_bytes() == original


@pytest.mark.parametrize(
    "marker", ["<<<<<<< ours", "||||||| base", "=======", ">>>>>>> theirs"]
)
def test_fix_cli_refuses_conflict_markers(tmp_path, monkeypatch, marker):
    path = tmp_path / "Changelog.txt"
    original = changelog(f"{marker}\n", " - [USA] U\n", " - Global\n").encode()
    path.write_bytes(original)
    assert _run_main(monkeypatch, "--fix", path) == 1
    assert path.read_bytes() == original


@pytest.mark.parametrize("content", [None, b"\xff"])
def test_fix_cli_reports_unreadable_input(tmp_path, monkeypatch, capsys, content):
    path = tmp_path / "Changelog.txt"
    if content is not None:
        path.write_bytes(content)
    assert _run_main(monkeypatch, "--fix", path) == 1
    assert "Cannot update changelog" in capsys.readouterr().err


@pytest.mark.parametrize("args", [[], ["--fix", "a", "b"]])
def test_cli_rejects_invalid_arguments(monkeypatch, args):
    with pytest.raises(SystemExit) as exc:
        _run_main(monkeypatch, *args)
    assert exc.value.code == 2
