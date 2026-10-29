"""Diff-scoped whitespace cleanup preserves unstaged and legacy content."""

import sys

import fix_styling as fixer
import pytest
import yaml
from shared.paths import REPO_ROOT
from shared.suite import initialize_git_repository, run_git, write_text


@pytest.fixture
def repository(tmp_path):
    write_text(tmp_path / ".gitattributes", "* -text\n")
    write_text(tmp_path / "legacy.txt", "legacy = yes \t\nkeep = yes\n")
    initialize_git_repository(tmp_path, ".gitattributes", "legacy.txt")
    return tmp_path


# case: (path, new content, staged, unstaged, expected, exit code)
_CASES = {
    "changed line keeps legacy whitespace": (
        "legacy.txt",
        b"legacy = yes \t\nkeep = no \t\n",
        True,
        None,
        b"legacy = yes \t\nkeep = no\n",
        1,
    ),
    "clean change": (
        "legacy.txt",
        b"legacy = yes \t\nkeep = no\n",
        True,
        None,
        b"legacy = yes \t\nkeep = no\n",
        0,
    ),
    "new utf8 bom and mixed endings": (
        "new.yml",
        b'\xef\xbb\xbfl_english: \t\r\n KEY: "value"  \n LAST: "end"\t',
        True,
        None,
        b'\xef\xbb\xbfl_english:\r\n KEY: "value"\n LAST: "end"',
        1,
    ),
    "empty new file": ("new.txt", b"", True, None, b"", 0),
    "partially staged": (
        "legacy.txt",
        b"legacy = yes \t\nkeep = no \t\n",
        True,
        b"legacy = changed \t\nkeep = no \t\n",
        b"legacy = changed \t\nkeep = no \t\n",
        1,
    ),
    "untracked file": ("new.txt", b"text \t\n", False, None, b"text \t\n", 1),
    "no staged changes": (
        "legacy.txt",
        b"legacy = yes \t\nkeep = yes\n",
        False,
        None,
        b"legacy = yes \t\nkeep = yes\n",
        0,
    ),
    "invalid utf8": ("new.txt", b"\xff \n", True, None, b"\xff \n", 1),
}


@pytest.mark.parametrize(
    "relative,content,staged,unstaged,expected,code",
    _CASES.values(),
    ids=_CASES,
)
def test_scoped_cleanup(
    repository, relative, content, staged, unstaged, expected, code
):
    path = repository / relative
    path.write_bytes(content)
    if staged:
        run_git(repository, "add", relative)
    if unstaged is not None:
        path.write_bytes(unstaged)
    index = run_git(repository, "ls-files", "--stage").stdout
    assert fixer.fix_trailing_whitespace(str(path)) == code
    assert path.read_bytes() == expected
    assert run_git(repository, "ls-files", "--stage").stdout == index


@pytest.mark.parametrize(
    "error", [OSError("unreadable"), fixer.StagedDiffError("git failed")]
)
def test_cleanup_reports_io_and_git_failures(monkeypatch, capsys, error):
    def fail(_filename):
        raise error

    monkeypatch.setattr(fixer, "_worktree_matches_index", fail)
    assert fixer.fix_trailing_whitespace("file.txt") == 1
    assert str(error) in capsys.readouterr().err


def test_main_processes_every_file_even_after_a_failure(monkeypatch):
    calls = []
    monkeypatch.setattr(
        sys,
        "argv",
        [fixer.__file__, "--trailing-whitespace-only", "first.txt", "second.txt"],
    )
    monkeypatch.setattr(
        fixer,
        "fix_trailing_whitespace",
        lambda name, **_kwargs: calls.append(name) or int(name == "first.txt"),
    )
    assert fixer.main() == 1
    assert calls == ["first.txt", "second.txt"]


def test_dry_run_reports_whitespace_without_writing(repository, monkeypatch):
    path = repository / "new.txt"
    path.write_bytes(b"new = yes \t\n")
    run_git(repository, "add", "new.txt")
    monkeypatch.setattr(
        sys,
        "argv",
        [fixer.__file__, "--trailing-whitespace-only", "--dry-run", str(path)],
    )
    assert fixer.main() == 1
    assert path.read_bytes() == b"new = yes \t\n"


def test_whitespace_mode_requires_explicit_paths(monkeypatch):
    monkeypatch.setattr(sys, "argv", [fixer.__file__, "--trailing-whitespace-only"])
    with pytest.raises(SystemExit) as error:
        fixer.main()
    assert error.value.code == 2


def test_hook_uses_the_scoped_fixer_without_a_whole_file_whitespace_hook():
    config = yaml.safe_load(
        (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    )
    hooks = [hook for repo in config["repos"] for hook in repo["hooks"]]
    assert not any(hook["id"] == "trailing-whitespace" for hook in hooks)
    hook = next(hook for hook in hooks if hook["id"] == "md-trailing-whitespace")
    assert (
        hook["entry"]
        == "python3 tools/linting/fix_styling.py --trailing-whitespace-only"
    )
    assert hook["types"] == ["text"]
    assert hook.get("pass_filenames", True)
    assert hook["exclude"] == r"\.mod$|^(gfx|map|interface|music|sound)/"
