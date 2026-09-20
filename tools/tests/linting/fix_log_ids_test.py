"""Behavioral tests for tools/linting/fix_log_ids.py.

Rewrites mismatched log = "...Focus X" / "...Decision X" tokens inside the
enclosing focus/decision block. Tests use real fixtures so the
finder/writer pipeline is exercised, not mocked.
"""

import subprocess
import sys
from pathlib import Path

_CLI = Path(__file__).resolve().parents[2] / "linting" / "fix_log_ids.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _shared_tree(tmp_path: Path) -> Path:
    """Build a tiny mod tree the CLI can walk."""
    root = tmp_path / "mod"
    (root / "common/national_focus").mkdir(parents=True)
    (root / "common/decisions").mkdir(parents=True)
    return root


def _run(root: Path, *args):
    return subprocess.run(
        [sys.executable, str(_CLI), *args],
        capture_output=True,
        text=True,
        cwd=str(root),
    )


def test_focus_finder_dispatches_to_focus_and_decision():
    from check_common_mistakes import _find_decision_log_mismatches as dec_fn
    from check_common_mistakes import _find_focus_log_mismatches as focus_fn
    from fix_log_ids import _finder_for

    assert _finder_for("common/national_focus/y.txt") is focus_fn
    assert _finder_for("common/decisions/x.txt") is dec_fn
    assert _finder_for("common/ideas/x.txt") is None


def test_rewrite_line_replaces_innermost_span_first():
    from fix_log_ids import _rewrite_line

    # `log = "...Focus TOK_A"` -> indices of TOK_A inside the line.
    line = 'log = "[GetDateText]: [Root.GetName]: Focus TST_aaa"'
    # Position 49..56 is `TST_aaa`.
    out = _rewrite_line(line, [(49, 56, "TST_bbb")])
    assert "TST_bbb" in out
    assert "TST_aaa" not in out


def test_rewrite_line_handles_two_spans_on_one_line():
    from fix_log_ids import _rewrite_line

    line = 'log = "[GetDateText]: Focus OLD_X and OLD_Y"'
    # Rightmost-first ensures earlier offsets remain valid after replacement.
    out = _rewrite_line(line, [(34, 39, "NEW_Y"), (24, 29, "NEW_X")])
    assert "NEW_X" in out
    assert "NEW_Y" in out
    assert "OLD_X" not in out
    assert "OLD_Y" not in out


def test_apply_rewrites_focus_log_token(tmp_path):
    from fix_log_ids import fix_file

    root = _shared_tree(tmp_path)
    focus = root / "common/national_focus/correct.txt"
    _write(
        focus,
        (
            "focus_tree = {\n"
            "    id = TST_correct_focus\n"
            "    focus = {\n"
            "        id = TST_correct_focus\n"
            '        log = "[GetDateText]: [Root.GetName]: Focus TST_wrong_focus"\n'
            "    }\n"
            "}\n"
        ),
    )

    path, count = fix_file(str(focus))
    assert path == str(focus)
    assert count == 1
    body = focus.read_text(encoding="utf-8")
    assert 'Focus TST_correct_focus"' in body
    assert "TST_wrong_focus" not in body


def test_apply_dry_run_does_not_write(tmp_path):
    from fix_log_ids import fix_file_dry_run

    root = _shared_tree(tmp_path)
    focus = root / "common/national_focus/dry.txt"
    original = (
        "focus_tree = {\n"
        "    id = TST_dry_focus\n"
        "    focus = {\n"
        "        id = TST_dry_focus\n"
        '        log = "[GetDateText]: [Root.GetName]: Focus TST_other"\n'
        "    }\n"
        "}\n"
    )
    _write(focus, original)

    path, count = fix_file_dry_run(str(focus))
    assert path == str(focus)
    assert count == 1
    assert focus.read_text(encoding="utf-8") == original


def test_apply_returns_zero_when_no_mismatch(tmp_path):
    from fix_log_ids import fix_file

    root = _shared_tree(tmp_path)
    focus = root / "common/national_focus/clean.txt"
    _write(
        focus,
        (
            "focus_tree = {\n"
            "    id = TST_clean\n"
            "    focus = {\n"
            "        id = TST_clean\n"
            '        log = "[GetDateText]: [Root.GetName]: Focus TST_clean"\n'
            "    }\n"
            "}\n"
        ),
    )
    _, count = fix_file(str(focus))
    assert count == 0


def test_apply_ignores_non_focus_decision_paths(tmp_path):
    from fix_log_ids import fix_file

    root = _shared_tree(tmp_path)
    other = root / "common/ideas/zzz.txt"
    _write(other, "focus_tree = { id = TST_zzz }\n")
    path, count = fix_file(str(other))
    assert path == str(other)
    assert count == 0


def test_apply_rewrites_decision_log_token(tmp_path):
    from fix_log_ids import fix_file

    root = _shared_tree(tmp_path)
    dec = root / "common/decisions/correct.txt"
    _write(
        dec,
        (
            "TAG_decisions = {\n"
            "    TAG_test_decision = {\n"
            '        log = "[GetDateText]: [Root.GetName]: Decision TAG_other_decision"\n'
            "        allowed = { always = yes }\n"
            "    }\n"
            "}\n"
        ),
    )
    _, count = fix_file(str(dec))
    assert count == 1
    body = dec.read_text(encoding="utf-8")
    assert 'Decision TAG_test_decision"' in body


def test_apply_read_failure_returns_zero(tmp_path, monkeypatch):
    from fix_log_ids import fix_file

    root = _shared_tree(tmp_path)
    focus = root / "common/national_focus/read_err.txt"
    _write(focus, "focus_tree = { id = TST_x }\n")
    monkeypatch.setattr(
        "fix_log_ids.read_text_strict",
        lambda *a, **k: (_ for _ in ()).throw(OSError("read fail")),
    )
    _, count = fix_file(str(focus))
    assert count == 0


def test_cli_dry_run_reports_completion(tmp_path):
    root = _shared_tree(tmp_path)
    focus = root / "common/national_focus/cli.txt"
    _write(focus, "focus_tree = { id = TST_cli }\n")

    result = _run(root, "--dry-run", "--workers", "1")
    assert result.returncode == 0
    assert "Fix Log IDs" in result.stdout


def test_apply_returns_zero_for_unknown_path(tmp_path):
    """The wrapper short-circuits on paths with no matching finder."""
    from fix_log_ids import fix_file

    other = tmp_path / "common/ideas/zzz.txt"
    other.parent.mkdir(parents=True, exist_ok=True)
    other.write_text("ideas = { country = { TST_x = { } } }", encoding="utf-8")
    path, count = fix_file(str(other))
    assert path == str(other)
    assert count == 0


def test_cli_writes_fix_when_target_is_repo_root(tmp_path):
    # The CLI walks the entire mod tree (default --root), so just place a
    # focus file with a mismatched log under the standard layout and let it
    # be rewritten by the live parser.
    target = (
        _repo_root()
        / "common"
        / "national_focus"
        / "_fixture_fix_log_ids_test_focus.txt"
    )
    original_content = (
        "focus_tree = {\n"
        "    id = TST_log_id_fix\n"
        "    focus = {\n"
        "        id = TST_log_id_fix\n"
        '        log = "[GetDateText]: [Root.GetName]: Focus TST_other_id"\n'
        "    }\n"
        "}\n"
    )
    _write(target, original_content)
    try:
        result = _run(_repo_root(), "--workers", "1")
        assert result.returncode == 0
        body = target.read_text(encoding="utf-8")
        assert "TST_other_id" not in body
        assert 'Focus TST_log_id_fix"' in body
    finally:
        target.unlink(missing_ok=True)
