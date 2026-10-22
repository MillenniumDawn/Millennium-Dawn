"""The pre-commit wrapper that routes staged files to their standardizer."""

import sys

import pytest
import standardize_staged
from shared.suite import read_text, run_tool_script, write_text

# case: staged path -> the standardizer the hook runs, or None when it skips
_ROUTES = {
    "common/national_focus/USA.txt": "focus",
    "events/USA_events.txt": "event",
    "common/decisions/USA_decisions.txt": "decision",
    "common/ideas/USA_ideas.txt": "idea",
    "history/countries/USA.txt": None,
    "common/national_focus": None,
}


@pytest.mark.parametrize(("path", "kind"), _ROUTES.items(), ids=_ROUTES)
def test_staged_path_is_routed_to_its_standardizer(path, kind):
    assert standardize_staged.get_standardizer(path) == kind


def test_false_standardizer_return_raises(tmp_path, monkeypatch):
    # A False return is a failure that did not raise, such as a write error.
    # Counting it as "not modified" would let the commit through.
    path = write_text(tmp_path / "x.txt", "idea = { }\n")
    monkeypatch.setattr(
        standardize_staged.IdeaStandardizer,
        "standardize_file",
        lambda self, inp, out: False,
    )

    with pytest.raises(RuntimeError):
        standardize_staged.standardize_file(str(path), "idea")


def _main(monkeypatch, *paths):
    monkeypatch.setattr(sys, "argv", ["standardize_staged.py", *paths])
    return standardize_staged.main()


def test_main_standardizes_routed_files_and_reports_a_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    focus = write_text(
        tmp_path / "common/national_focus/TST.txt",
        "focus_tree = {\n\tfocus = {\n\t\tid = TST_focus\n\t}\n}\n",
    )
    write_text(tmp_path / "README.txt", "plain\n")

    code = _main(
        monkeypatch, "common/national_focus/TST.txt", "README.txt", "missing.txt"
    )

    assert code == 1
    assert "focus = {" in read_text(focus)


def test_main_fails_when_a_standardizer_raises(monkeypatch):
    def boom(*_args):
        raise RuntimeError("boom")

    monkeypatch.setattr(standardize_staged, "standardize_file", boom)
    monkeypatch.setattr(standardize_staged.os.path, "exists", lambda _path: True)

    assert _main(monkeypatch, "events/TST.txt") == 1


def test_main_passes_with_no_files(monkeypatch):
    assert _main(monkeypatch) == 0


def test_the_script_passes_when_every_file_is_missing():
    result = run_tool_script(
        "standardize_staged.py", "does/not/exist.txt", "also_missing.txt"
    )

    assert result.returncode == 0, result.stderr
