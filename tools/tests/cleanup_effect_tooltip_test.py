"""cleanup_effect_tooltip.py collapses only pure custom_effect_tooltip wrappers.

Covers the core transform (single- and multi-line), the must-NOT-touch cases
(real effects, empty blocks, comments), and the reference-dir guards: resources/
(AGENTS.md) and .claude/ (holds sibling worktree checkouts) must never be
rewritten, via both a file path and a directory entry point.
"""

import runpy
import sys

import cleanup_effect_tooltip as cet
import pytest

_WRAP_SINGLE = "foo = {\n\teffect_tooltip = { custom_effect_tooltip = bar_tt }\n}\n"
_WRAP_MULTI = (
    "foo = {\n\teffect_tooltip = {\n\t\tcustom_effect_tooltip = bar_tt\n\t}\n}\n"
)
_COLLAPSED = "foo = {\n\tcustom_effect_tooltip = bar_tt\n}\n"


def test_single_line_wrapper_collapses(tmp_path):
    f = tmp_path / "ctrl.txt"
    f.write_text(_WRAP_SINGLE, encoding="utf-8")
    cet.main([str(f)])
    assert f.read_text(encoding="utf-8") == _COLLAPSED


def test_multi_line_wrapper_collapses(tmp_path):
    f = tmp_path / "ctrl.txt"
    f.write_text(_WRAP_MULTI, encoding="utf-8")
    cet.main([str(f)])
    assert f.read_text(encoding="utf-8") == _COLLAPSED


def test_process_file_propagates_write_error(tmp_path, monkeypatch):
    f = tmp_path / "ctrl.txt"
    f.write_text(_WRAP_SINGLE, encoding="utf-8")
    real_open = open

    def fail_write(path, mode="r", *args, **kwargs):
        if "w" in mode:
            raise OSError("read-only")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(cet, "open", fail_write, raising=False)
    try:
        cet.process_file(str(f))
    except OSError as error:
        assert "read-only" in str(error)
    else:
        assert False, "process_file should propagate write failures"


def test_real_effect_block_untouched():
    src = "\teffect_tooltip = {\n\t\tadd_stability = 0.1\n\t}\n".splitlines(
        keepends=True
    )
    out, n = cet.simplify_effect_tooltip_block(src)
    assert n == 0
    assert out == src


def test_mixed_and_empty_and_comment_untouched():
    for src in (
        "\teffect_tooltip = {\n\t\tcustom_effect_tooltip = X\n\t\tadd_stability = 0.1\n\t}\n",
        "\teffect_tooltip = { }\n",
        "\teffect_tooltip = {\n\t\t# note\n\t\tcustom_effect_tooltip = X\n\t}\n",
    ):
        lines = src.splitlines(keepends=True)
        out, n = cet.simplify_effect_tooltip_block(lines)
        assert n == 0
        assert out == lines


def test_resources_file_path_not_modified(tmp_path):
    res = tmp_path / "resources"
    res.mkdir()
    f = res / "keep.txt"
    f.write_text(_WRAP_SINGLE, encoding="utf-8")
    cet.main([str(f)])
    assert f.read_text(encoding="utf-8") == _WRAP_SINGLE


def test_claude_directory_not_walked(tmp_path):
    # .claude/worktrees holds full sibling checkouts of other branches.
    wt = tmp_path / ".claude" / "worktrees" / "x" / "common"
    wt.mkdir(parents=True)
    f = wt / "keep.txt"
    f.write_text(_WRAP_SINGLE, encoding="utf-8")
    cet.main([str(tmp_path / ".claude")])
    assert f.read_text(encoding="utf-8") == _WRAP_SINGLE


def test_repo_own_resources_and_claude_excluded(tmp_path):
    repo_root = tmp_path / "MillenniumDawn"
    for sub in ("resources", ".claude"):
        target = repo_root / sub / "ref.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_WRAP_SINGLE, encoding="utf-8")
        assert cet._is_excluded_path(str(target), repo_root=str(repo_root))


def test_ancestor_excluded_name_outside_repo_not_excluded(tmp_path):
    # A checkout nested under an ancestor literally named "resources" must not
    # exclude the whole repo: relative to its own root nothing is excluded.
    repo_root = tmp_path / "resources" / "MillenniumDawn"
    target = repo_root / "common" / "foo.txt"
    target.parent.mkdir(parents=True)
    target.write_text(_WRAP_SINGLE, encoding="utf-8")
    assert not cet._is_excluded_path(str(target), repo_root=str(repo_root))


def test_detector_reports_inline_wrapper_only_when_it_is_pure():
    lines = [
        "\tcomplete_effect = { effect_tooltip = { add_stability = 0.1 } }\n",
        "\tcomplete_effect = { effect_tooltip = { custom_effect_tooltip = bar_tt } }\n",
    ]

    assert [
        line for line, _message in cet.find_redundant_effect_tooltip_wrappers(lines)
    ] == [2]


def test_main_reports_nothing_when_no_file_changes(tmp_path, capsys):
    (tmp_path / "clean.txt").write_text(
        "foo = {\n\tadd_stability = 0.1\n}\n", encoding="utf-8"
    )

    assert cet.main([str(tmp_path)]) == 0
    assert "No redundant effect_tooltip wrappers found." in capsys.readouterr().out


def _run_cli(argv):
    saved = sys.argv
    sys.argv = argv
    try:
        runpy.run_path(cet.__file__, run_name="__main__")
    finally:
        sys.argv = saved


def test_cli_check_mode_reports_without_writing(tmp_path, capsys):
    target = tmp_path / "focus.txt"
    target.write_text(_WRAP_SINGLE, encoding="utf-8")

    _run_cli(["cleanup_effect_tooltip.py", "--check", str(target)])

    assert target.read_text(encoding="utf-8") == _WRAP_SINGLE
    assert "Would collapse 1 redundant" in capsys.readouterr().out


def test_cli_rewrites_the_files_it_is_given(tmp_path, capsys):
    target = tmp_path / "focus.txt"
    target.write_text(_WRAP_SINGLE, encoding="utf-8")

    _run_cli(["cleanup_effect_tooltip.py", str(target)])

    assert target.read_text(encoding="utf-8") == _COLLAPSED
    assert "Collapsed 1 redundant" in capsys.readouterr().out


def test_cli_without_arguments_prints_usage_and_fails(capsys):
    with pytest.raises(SystemExit) as exc:
        _run_cli(["cleanup_effect_tooltip.py"])

    assert exc.value.code == 1
    assert "usage: cleanup_effect_tooltip.py" in capsys.readouterr().err
