"""Tests for fix_styling: the fix_line rules, the file-level fixers, and main().

fix_line only rewrites lines the shared line_spacing_warnings detection flags,
so checker and fixer cannot drift. The legacy whole-file passes (leading-space
indent conversion, comment-alignment collapse) and the changed-lines scope are
explicit opt-ins. The file-level cases cover what fix_file writes back, what it
can only report, and dry-run/apply agreement on BOM'd and CRLF files.
"""

import runpy
import shutil
import subprocess
import sys

import fix_styling
import pytest
from fix_styling import fix_file, fix_file_dry_run, fix_line


def _write(path, content):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def _run_main(monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", [fix_styling.__file__, *argv])
    return fix_styling.main()


def test_pads_inline_block():
    fixed, fixes = fix_line("\t\tNOT = {country_exists = ENG}\n")
    assert fixed == "\t\tNOT = { country_exists = ENG }\n"
    assert fixes == 1


def test_leading_spaces_become_tabs_only_behind_the_flag():
    assert fix_line("    x = { y = 1 }") == ("    x = { y = 1 }", 0)
    assert fix_line("    x = { y = 1 }", fix_indent=True) == ("\tx = { y = 1 }", 1)


def test_tab_before_equals_is_fixed():
    fixed, fixes = fix_line("newline\t= yes\n")
    assert fixed == "newline = yes\n"
    assert fixes == 1


def test_equals_separator_in_an_inline_comment_is_untouched_by_default():
    fixed, _ = fix_line("\tfoo=bar  # note ==== here\n")
    assert fixed == "\tfoo = bar  # note ==== here\n"


def test_comment_separators_are_a_legacy_flag():
    assert fix_line("\t# ==== section ====\n") == ("\t# ==== section ====\n", 0)
    assert fix_line(
        "\tfoo=bar  # note ==== here\n", collapse_comment_alignment=True
    ) == (
        "\tfoo = bar # note ---- here\n",
        2,
    )
    assert fix_line("# ==== section ====\n", collapse_comment_alignment=True) == (
        "# ---- section ----\n",
        1,
    )


def test_collapse_keeps_an_indented_comment_separator_indented():
    fixed, _ = fix_line("\t# ==== section ====\n", collapse_comment_alignment=True)
    assert fixed == "\t# ---- section ----\n"


def test_quoted_string_not_rewritten():
    line = '\tlog = "a=b {c}"\n'
    assert fix_line(line) == (line, 0)


def test_clean_line_reports_no_fixes():
    line = "\tavailable = { has_country_flag = some_flag }\n"
    assert fix_line(line) == (line, 0)


def test_inline_comment_alignment_is_byte_exact_by_default():
    fixed, _ = fix_line("\tfoo=bar\t\t#aligned note\n")
    assert fixed == "\tfoo = bar\t\t#aligned note\n"


def test_comment_alignment_collapse_is_opt_in():
    fixed, _ = fix_line("\tfoo=bar\t\t#aligned note\n", collapse_comment_alignment=True)
    assert fixed == "\tfoo = bar #aligned note\n"


def test_comment_alignment_collapse_runs_without_spacing_warning():
    fixed, fixes = fix_line(
        "\tattacker = 0.25\t\t#aligned note\n",
        collapse_comment_alignment=True,
    )
    assert fixed == "\tattacker = 0.25 #aligned note\n"
    assert fixes == 1


def test_single_leading_space_is_left_alone():
    """One space is not a full tab, so the rewrite is a no-op and costs no fix."""
    fixed, fixes = fix_line(" x = { y = 1 }\n", fix_indent=True)
    assert fixed == " x = { y = 1 }\n"
    assert fixes == 0


def test_fix_file_rewrites_and_counts(tmp_path):
    path = tmp_path / "focus.txt"
    _write(path, "cost=10   \nfoo = { bar = 1 }\n\n\n")

    _fp, fixes, unfixable = fix_file(str(path))

    with open(path, encoding="utf-8", newline="") as handle:
        assert handle.read() == "cost = 10   \nfoo = { bar = 1 }\n"
    assert fixes == 1
    assert unfixable == []


def test_fix_file_leaves_a_clean_file_byte_identical(tmp_path):
    path = tmp_path / "clean.txt"
    original = "focus = {\n\tid = TAG_focus\n}\n"
    _write(path, original)

    _fp, fixes, unfixable = fix_file(str(path))

    assert path.read_bytes() == original.encode()
    assert (fixes, unfixable) == (0, [])


def test_fix_file_preserves_bom_and_crlf(tmp_path):
    path = tmp_path / "bom.txt"
    _write(path, "﻿foo=bar\r\nbaz = 1\r\n")

    _fp, _fixes, _unfixable = fix_file(str(path))

    data = path.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")
    assert b"foo = bar\r\n" in data
    assert b"baz = 1\r\n" in data


@pytest.mark.parametrize(
    ("content", "expected_apply"),
    [
        ("﻿foo=bar\r\nbaz = 1\r\n", "﻿foo = bar\r\nbaz = 1\r\n"),
        ("﻿foo=bar\r\nbaz = 1", "﻿foo = bar\r\nbaz = 1\r\n"),
    ],
)
def test_dry_run_agrees_with_apply_on_bom_crlf_files(tmp_path, content, expected_apply):
    apply_path = tmp_path / "apply.txt"
    dry_path = tmp_path / "dry.txt"
    _write(apply_path, content)
    _write(dry_path, content)

    _fp, dry_fixes, _ = fix_file_dry_run(str(dry_path))
    _fp, apply_fixes, _ = fix_file(str(apply_path))

    assert dry_fixes == apply_fixes
    assert dry_path.read_bytes() == content.encode()
    assert apply_path.read_bytes() == expected_apply.encode()


def test_fix_file_reports_an_odd_quote_it_cannot_fix(tmp_path):
    path = tmp_path / "quotes.txt"
    _write(path, 'focus = {\n\tlog = "unterminated\n}\n')

    _fp, _fixes, unfixable = fix_file(str(path))

    assert len(unfixable) == 1
    assert unfixable[0].endswith(":2: Possible missing quotation mark")


def test_fix_file_reports_an_unreadable_path(tmp_path):
    filepath = str(tmp_path / "gone.txt")

    result_path, fixes, unfixable = fix_file(filepath)

    assert (result_path, fixes) == (filepath, 0)
    assert len(unfixable) == 1
    assert "Error processing" in unfixable[0]


def test_dry_run_counts_without_writing(tmp_path):
    path = tmp_path / "focus.txt"
    original = "cost=10\n"
    _write(path, original)

    _fp, fixes, unfixable = fix_file_dry_run(str(path))

    assert path.read_bytes() == original.encode()
    assert fixes == 1
    assert unfixable == []


def test_dry_run_reports_an_unreadable_path(tmp_path):
    _fp, fixes, unfixable = fix_file_dry_run(str(tmp_path / "gone.txt"))

    assert fixes == 0
    assert "Error processing" in unfixable[0]


def test_main_fixes_the_files_it_is_given(tmp_path, monkeypatch, capsys):
    path = tmp_path / "focus.txt"
    _write(path, "cost=10\n")

    assert _run_main(monkeypatch, str(path)) == 0

    assert path.read_bytes() == b"cost = 10\n"
    assert "Fixed 1 issues in 1 files" in capsys.readouterr().out


def test_main_dry_run_leaves_the_file_alone(tmp_path, monkeypatch, capsys):
    path = tmp_path / "focus.txt"
    original = "cost=10\n"
    _write(path, original)

    assert _run_main(monkeypatch, "--dry-run", str(path)) == 0

    assert path.read_bytes() == original.encode()
    assert "Would fix 1 issues in 1 files" in capsys.readouterr().out


def test_main_reports_nothing_to_do(tmp_path, monkeypatch, capsys):
    assert _run_main(monkeypatch, str(tmp_path / "gone.txt")) == 0

    assert "No files to process" in capsys.readouterr().out


@pytest.mark.parametrize("count,truncated", [(3, False), (51, True)])
def test_main_truncates_only_a_long_unfixable_list(
    tmp_path, monkeypatch, capsys, count, truncated
):
    path = tmp_path / "quotes.txt"
    _write(path, '\tlog = "unterminated\n' * count)

    assert _run_main(monkeypatch, str(path)) == 0

    out = capsys.readouterr().out
    assert f"{count} issues need manual attention" in out
    assert ("... and 1 more" in out) is truncated


def test_script_entry_point_exits_zero(tmp_path, monkeypatch):
    path = tmp_path / "focus.txt"
    _write(path, "cost=10\n")
    monkeypatch.setattr(sys, "argv", [fix_styling.__file__, str(path)])

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(fix_styling.__file__, run_name="__main__")

    assert excinfo.value.code == 0


# --- changed-lines scope -----------------------------------------------------


def _git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )


@pytest.fixture
def git_repo(tmp_path):
    """A minimal repo with one committed legacy focus file."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    legacy = (
        "attacker = 0.25\t\t\t# aligned legacy comment\n"
        "\t\tlegacy_aligned_line = 1\t\t# stays untouched\n"
    )
    (tmp_path / "focus.txt").write_text(legacy, encoding="utf-8", newline="")
    _git(tmp_path, "add", "focus.txt")
    _git(tmp_path, "commit", "-q", "-m", "legacy")
    return tmp_path


def test_staged_changed_lines_parses_hunk_headers(git_repo):
    path = git_repo / "focus.txt"
    with open(path, "a", encoding="utf-8", newline="") as handle:
        handle.write("newline\t= yes\n")
    _git(git_repo, "add", "focus.txt")

    lines = fix_styling.staged_changed_lines(str(path))

    assert lines == {3}


def test_staged_changed_lines_ignores_an_inherited_git_dir(git_repo, monkeypatch):
    """Git hands hooks an absolute GIT_DIR; discovery must not bind to it.

    Inside a worktree that binding makes `rev-parse --show-toplevel` answer with
    the file's own directory, so every staged path collapses to its basename.
    """
    nested = git_repo / "history" / "states"
    nested.mkdir(parents=True)
    path = nested / "focus.txt"
    _write(path, "cost\t= 10\n")
    _git(git_repo, "add", "history/states/focus.txt")
    monkeypatch.setenv("GIT_DIR", str(git_repo / ".git"))

    root, relative = fix_styling._repo_path(str(path))

    assert relative == "history/states/focus.txt"
    assert fix_styling.staged_changed_lines(str(path)) == {1}
    assert root.endswith(git_repo.name)


def test_staged_changed_lines_supports_an_unborn_head(tmp_path):
    _git(tmp_path, "init", "-q")
    path = tmp_path / "new.txt"
    path.write_text("cost\t= 10\n", encoding="utf-8", newline="")
    _git(tmp_path, "add", "new.txt")

    assert fix_styling.staged_changed_lines(str(path)) == {1}


def test_staged_changed_lines_supports_a_staged_deletion(git_repo):
    path = git_repo / "focus.txt"
    path.unlink()
    _git(git_repo, "add", "focus.txt")

    assert fix_styling.staged_changed_lines(str(path)) == set()


def test_staged_changed_lines_supports_a_renamed_path(git_repo):
    old = git_repo / "focus.txt"
    new = git_repo / "renamed.txt"
    old.rename(new)
    with new.open("a", encoding="utf-8", newline="") as handle:
        handle.write("cost\t= 10\n")
    _git(git_repo, "add", "-A")

    assert {3} <= fix_styling.staged_changed_lines(str(new))


def test_staged_changed_lines_fails_closed_on_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(kwargs.get("args", args[0]), 15)

    monkeypatch.setattr(fix_styling.subprocess, "run", timeout)

    with pytest.raises(fix_styling.StagedDiffError):
        fix_styling.staged_changed_lines("focus.txt")


def test_staged_changed_lines_fails_closed_when_git_fails(monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("no git")

    monkeypatch.setattr(fix_styling.subprocess, "run", boom)

    with pytest.raises(fix_styling.StagedDiffError, match="cannot find Git repository"):
        fix_styling.staged_changed_lines("focus.txt")


def test_changed_lines_pass_fixes_only_the_diff(tmp_path):
    legacy = "attacker = 0.25\t\t\t# aligned legacy comment\n"
    (tmp_path / "focus.txt").write_text(legacy + "newline\t= yes\n", encoding="utf-8")

    _fp, fixes, _unfixable = fix_file(str(tmp_path / "focus.txt"), only_lines={2})

    assert fixes == 1
    content = (tmp_path / "focus.txt").read_text(encoding="utf-8")
    assert content == legacy + "newline = yes\n"


def test_changed_lines_pass_leaves_a_clean_changed_file_alone(tmp_path):
    original = "a = 1\nb = 2\n"
    (tmp_path / "clean.txt").write_text(original, encoding="utf-8")

    _fp, fixes, _unfixable = fix_file(str(tmp_path / "clean.txt"), only_lines={2})

    assert fixes == 0
    assert (tmp_path / "clean.txt").read_text(encoding="utf-8") == original


def test_direct_changed_lines_fails_on_unstaged_worktree_edits(git_repo, monkeypatch):
    path = git_repo / "focus.txt"
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write("newline\t= yes\n")
    _git(git_repo, "add", "focus.txt")
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write("unstaged\t= yes\n")

    monkeypatch.chdir(git_repo)
    monkeypatch.setattr(
        fix_styling,
        "collect_files_by_mode",
        lambda *_args, **_kwargs: [str(path)],
    )
    monkeypatch.setattr(
        sys, "argv", [fix_styling.__file__, "--mode", "staged", "--changed-lines"]
    )

    assert fix_styling.main() == 1
    assert path.read_text(encoding="utf-8").endswith("unstaged\t= yes\n")


def test_precommit_stashes_unstaged_lines_without_restaging(git_repo):
    pre_commit = shutil.which("pre-commit")
    if pre_commit is None:
        pytest.skip("pre-commit is not installed")
    config = git_repo / ".pre-commit-config.yaml"
    config.write_text(
        "repos:\n"
        "- repo: local\n"
        "  hooks:\n"
        "  - id: fix\n"
        "    name: fix\n"
        f"    entry: {sys.executable} {fix_styling.__file__} --mode staged --changed-lines\n"
        "    language: system\n"
        "    files: \\.txt$\n"
        "    pass_filenames: false\n",
        encoding="utf-8",
        newline="",
    )
    path = git_repo / "common" / "focus.txt"
    path.parent.mkdir()
    original = "attacker = 0.25\nlegacy = 1\n"
    path.write_text(original, encoding="utf-8", newline="")
    _git(git_repo, "add", "common/focus.txt", ".pre-commit-config.yaml")
    _git(git_repo, "commit", "-q", "-m", "hooks")
    path.write_text(original + "newline\t= yes\n", encoding="utf-8", newline="")
    subprocess.run(
        [pre_commit, "install"],
        cwd=git_repo,
        check=True,
        capture_output=True,
        text=True,
    )
    _git(git_repo, "add", "common/focus.txt")
    path.write_text(
        "attacker\t= 0.25\nlegacy = 1\nnewline\t= yes\n", encoding="utf-8", newline=""
    )

    result = subprocess.run(
        ["git", "commit", "-m", "partial"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert path.read_text(encoding="utf-8").splitlines()[0] == "attacker\t= 0.25"
    assert path.read_text(encoding="utf-8").splitlines()[-1] == "newline\t= yes"
    assert "Stashed changes conflicted" in result.stdout + result.stderr
    staged = _git(git_repo, "diff", "--cached", "--", "common/focus.txt").stdout
    assert "+newline\t= yes" in staged


def test_staged_integration_fixes_only_the_added_line(git_repo):
    path = git_repo / "focus.txt"
    original = path.read_text(encoding="utf-8")
    with open(path, "a", encoding="utf-8", newline="") as handle:
        handle.write("newline\t= yes\n")
    _git(git_repo, "add", "focus.txt")

    only = fix_styling.staged_changed_lines(str(path))
    assert only is not None
    _fp, fixes, _unfixable = fix_file(str(path), only_lines=only)

    assert fixes == 1
    assert path.read_text(encoding="utf-8") == original + "newline = yes\n"
    staged = _git(git_repo, "diff", "--cached", "HEAD", "--", "focus.txt").stdout
    assert "+newline\t= yes" in staged


def test_main_changed_lines_mode(tmp_path, monkeypatch, capsys):
    path = tmp_path / "focus.txt"
    path.write_text("a = 1\ncost=10\n", encoding="utf-8", newline="")

    monkeypatch.setattr(fix_styling, "staged_changed_lines", lambda _f: {2})
    monkeypatch.setattr(fix_styling, "_worktree_matches_index", lambda _f: None)

    assert _run_main(monkeypatch, "--mode", "staged", "--changed-lines", str(path)) == 0

    assert path.read_text(encoding="utf-8") == "a = 1\ncost = 10\n"
    assert "Fixed 1 issues in 1 files" in capsys.readouterr().out
