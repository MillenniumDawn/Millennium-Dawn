"""Tests for the standardize.py subcommand wrapper.

The wrapper is the documented entrypoint, so a flag missing here breaks the
CLI even when the underlying standardizer supports it.
"""

import subprocess
import sys

from shared.paths import STANDARDIZATION_DIR

_STD_DIR = STANDARDIZATION_DIR
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


def test_focus_legacy_name_does_not_block_standardization_by_default(tmp_path):
    """A pre-existing violation elsewhere in the tree must not reject an unrelated edit."""
    source = tmp_path / "input.txt"
    output = tmp_path / "output.txt"
    source.write_text(_LEGACY_MODIFIER_FOCUS, encoding="utf-8")

    result = _run("focus", str(source), "-o", str(output))

    assert result.returncode == 0
    assert output.exists()
    assert "TST_Legacy_modifier" in output.read_text(encoding="utf-8")


def test_focus_check_naming_flag_is_forwarded(tmp_path):
    source = tmp_path / "input.txt"
    output = tmp_path / "output.txt"
    source.write_text(_LEGACY_MODIFIER_FOCUS, encoding="utf-8")

    result = _run("focus", str(source), "-o", str(output), "--check-naming")

    assert result.returncode != 0
    assert not output.exists()
