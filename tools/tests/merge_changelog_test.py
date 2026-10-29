import subprocess
import sys
from pathlib import Path

import merge_changelog
import pytest
from check_changelog import check_lines, duplicate_warnings
from merge_changelog import consolidation_candidates, merge_text
from shared.suite import initialize_git_repository, run_git

SCRIPT = Path(__file__).resolve().parents[1] / "merge_changelog.py"
PARTY_LINE = " - Standardized party names for the countries: DEN, EGY{}\n"
TANK_LINE = " - [GER] Added the Leopard 2A8 tank variant{}\n"
OLD_VERSION = "\nv2.0.1\nContent:\n - [USA] Old\n - Global old\n - Global old\n"


def changelog(*content):
    return "v2.0.1\n\nContent:\n" + "".join(content) + "\nBugfix:\n - Fixed a bug\n"


def top(*content):
    return "v2.1.0\n\nContent:\n" + "".join(content)


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


@pytest.mark.parametrize(
    ("content", "messages"),
    [
        (" - A.\n - A.\n", ["line 5: warning: duplicate of line 4; --fix removes it"]),
        (
            " - A.\n\nAI:\n - A.\n",
            ["line 7: warning: duplicate of line 4; keep one of Content and AI"],
        ),
        (
            " - [ERI] Added an OOB.\n - [ETH] Added an OOB.\n",
            [
                "lines 4 and 5: same entry for other tags; "
                "combine as [ERI]/[ETH] Added an OOB."
            ],
        ),
        (
            " - Updated currency tooltips for strength.\n"
            " - Updated currency tooltips for strenght.\n",
            ["lines 4 and 5: near-duplicate entries"],
        ),
        (
            " - [AST] Added an AI tweak to buff stability.\n\nAI:\n"
            " - [AST] Added an AI tweak to buff stability. AI holds elections (Issue #7).\n",
            ["lines 4 and 7: near-duplicate entries; keep [AST], #7"],
        ),
        (
            " - [ALG] Halved spending on a high deficit and stopped it.\n"
            " - [CUB] Halved healthcare on a high deficit and skipped it.\n"
            " - Added a tank.\n"
            " - [DEN] Halved weights on a high deficit and paused (Issue #6000).\n",
            [
                'lines 4, 5, 7: 3 Content entries share "on a high deficit and"; '
                "consider one summary entry; keep [ALG], [CUB], [DEN], #6000"
            ],
        ),
        (" - [ALG] Added a tank.\n - [CUB] Added a plane.\n", []),
    ],
)
def test_preview_messages(content, messages):
    lines = (top(content) + OLD_VERSION).splitlines(True)
    assert duplicate_warnings(lines) + consolidation_candidates(lines) == messages


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


def test_fix_cli_cleans_sorts_and_warns_without_touching_history(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "Changelog.txt"
    path.write_bytes(
        (
            top(" - [USA] U\n", " - Global\n", "  - Global\n", "\nAI:\n - [USA] U.\n")
            + OLD_VERSION
        ).encode()
    )
    monkeypatch.chdir(tmp_path)
    assert _run_main(monkeypatch, "--fix") == 0
    assert (
        path.read_bytes()
        == (
            top(" - Global.\n", " - [USA] U.\n", "\nAI:\n - [USA] U.\n") + OLD_VERSION
        ).encode()
    )
    output = capsys.readouterr()
    assert "Fixed changelog: Changelog.txt" in output.out
    assert output.err.splitlines() == [
        "Changelog.txt: warning: removed duplicate entry: Global.",
        "Changelog.txt: line 8: warning: duplicate of line 5; keep one of Content and AI",
    ]
    first = path.read_bytes()
    assert _run_main(monkeypatch, "--fix", path) == 0
    assert path.read_bytes() == first
    assert check_lines(first.decode().splitlines()) == []


def test_preview_cli_reports_without_writing(tmp_path, monkeypatch, capsys):
    path = tmp_path / "Changelog.txt"
    original = top(" - [USA] U\n", "  - [USA] U\n").encode()
    path.write_bytes(original)
    assert _run_main(monkeypatch, "--preview", path) == 0
    assert path.read_bytes() == original
    assert "line 5: warning: duplicate of line 4" in capsys.readouterr().out


def test_beta_cli_replaces_version_sections_and_keeps_intro(tmp_path, monkeypatch):
    path = tmp_path / "Changelog.txt"
    path.write_bytes(
        top(" - [USA] U\n", " - Global\n", "\nAI:\n - Smarter AI\n").encode()
    )
    page = tmp_path / merge_changelog.BETA_PAGE
    page.parent.mkdir(parents=True)
    intro = (
        "---\ntitle: Beta Changelog\n---\n\n## Purpose of this Page\n\nBeta changes.\n"
    )
    page.write_text(intro + "\n## v2.0.9\n\n### Content\n\n- Old beta entry\n")
    assert _run_main(monkeypatch, "--beta", path) == 0
    assert page.read_text() == (
        intro + "\n## v2.1.0\n\n### Content\n\n- Global.\n- [USA] U.\n"
        "\n### AI\n\n- Smarter AI.\n"
    )
    first = page.read_bytes()
    assert _run_main(monkeypatch, "--beta", path) == 0
    assert page.read_bytes() == first


def test_release_cli_writes_the_next_page_and_keeps_its_order(tmp_path, monkeypatch):
    path = tmp_path / "Changelog.txt"
    path.write_bytes(top(" - Global\n").encode())
    sections = tmp_path / merge_changelog.RELEASE_DIR
    sections.mkdir(parents=True)
    (sections / "v2-0-changes.md").write_text("---\ntitle: v2.0.0\norder: 14\n---\n")
    (sections / "v2-0-hotfixes.md").write_text("---\norder: 15\nhidden: true\n---\n")
    assert _run_main(monkeypatch, "--release", "The Next Chapter", path) == 0
    page = sections / "v2-1-the-next-chapter.md"
    assert page.read_text() == (
        "---\ntitle: \"v2.1.0 'The Next Chapter'\"\n"
        "page_id: changelog-v2-1-the-next-chapter\norder: 16\n---\n\n"
        '## v2.1.0 - "The Next Chapter"\n\n### Content\n\n- Global.\n'
    )
    first = page.read_bytes()
    (sections / "v2-2-later.md").write_text("---\norder: 20\n---\n")
    assert _run_main(monkeypatch, "--release", "The Next Chapter", path) == 0
    assert page.read_bytes() == first


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


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--fix", "a", "b"],
        ["--beta", "a", "b"],
        ["--fix", "--beta"],
        ["--release", " "],
    ],
)
def test_cli_rejects_invalid_arguments(monkeypatch, args):
    with pytest.raises(SystemExit) as exc:
        _run_main(monkeypatch, *args)
    assert exc.value.code == 2
