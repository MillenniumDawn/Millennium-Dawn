"""Tests for the standardize.py subcommand wrapper.

The wrapper is the documented entrypoint, so a flag missing here breaks the
CLI even when the underlying standardizer supports it.
"""

import subprocess
import sys
from pathlib import Path

_STD_DIR = Path(__file__).resolve().parents[1]
_CLI = _STD_DIR / "standardize.py"

_LEGACY_MODIFIER_FOCUS = """focus_tree = {
\tid = TST_tree
\tcountry = {
\t\tfactor = 0
\t}

\tfocus = {
\t\tid = TST_legacy
\t\ticon = GFX_goal_generic_political_pressure
\t\tx = 0
\t\ty = 0
\t\tcost = 10
\t\tcustom_effect_tooltip = { MODIFIER = TST_Legacy_modifier }
\t}
}
"""


def _run(*args):
    return subprocess.run(
        [sys.executable, str(_CLI), *args], capture_output=True, text=True
    )


def test_focus_naming_check_rejects_legacy_name_by_default(tmp_path):
    source = tmp_path / "input.txt"
    output = tmp_path / "output.txt"
    source.write_text(_LEGACY_MODIFIER_FOCUS, encoding="utf-8")

    result = _run("focus", str(source), "-o", str(output))

    assert result.returncode != 0
    assert not output.exists()


def test_focus_no_check_naming_flag_is_forwarded(tmp_path):
    source = tmp_path / "input.txt"
    output = tmp_path / "output.txt"
    source.write_text(_LEGACY_MODIFIER_FOCUS, encoding="utf-8")

    result = _run("focus", str(source), "-o", str(output), "--no-check-naming")

    assert result.returncode == 0
    assert output.exists()
    assert "TST_Legacy_modifier" in output.read_text(encoding="utf-8")
