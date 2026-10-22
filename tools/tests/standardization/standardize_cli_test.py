"""One real-process smoke test for the standardizer script entrypoint."""

from shared.suite import run_tool_script


def test_focus_help_runs_from_the_script_entrypoint():
    result = run_tool_script("standardization/standardize.py", "focus", "--help")

    assert result.returncode == 0
    assert "--check-naming" in result.stdout
