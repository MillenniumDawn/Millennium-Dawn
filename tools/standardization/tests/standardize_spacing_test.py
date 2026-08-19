"""End-to-end guard: standardized output carries MD brace / `=` spacing.

Both writer paths (BaseStandardizer.standardize_file and standardize_focus_tree)
run every emitted line through normalize_spacing, so a hand-written
`NOT = {country_exists = ENG}` cannot survive a standardization pass.
"""

import subprocess
import sys
from pathlib import Path

_CLI = Path(__file__).resolve().parents[1] / "standardize.py"

_IDEA_FILE = """ideas = {
\tcountry = {
\t\tTST_test_idea = {
\t\t\tpicture = test_picture
\t\t\tallowed = {
\t\t\t\toriginal_tag = TST
\t\t\t}
\t\t\tcancel = {
\t\t\t\tOR = {
\t\t\t\t\tNOT = {country_exists = ENG}
\t\t\t\t\tNOT = {TST={has_idea = EU_member}}
\t\t\t\t\tNOT = {western_liberals_are_in_power=yes}
\t\t\t\t}
\t\t\t}
\t\t\tmodifier = {
\t\t\t\tpolitical_power_factor = 0.1
\t\t\t}
\t\t}
\t}
}
"""

_FOCUS_FILE = """focus_tree = {
\tid = TST_tree
\tcountry = {
\t\tfactor = 0
\t}

\tfocus = {
\t\tid = TST_focus
\t\ticon = GFX_goal_generic_political_pressure
\t\tx = 0
\t\ty = 0
\t\tcost = 10
\t\tavailable = {
\t\t\tNOT = {country_exists = ENG}
\t\t}
\t\tcompletion_reward = {
\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus TST_focus"
\t\t}
\t}
}
"""


def _standardize(tmp_path, subcommand, text, name="input.txt"):
    source = tmp_path / name
    output = tmp_path / "output.txt"
    source.write_text(text, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CLI), subcommand, str(source), "-o", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return output.read_text(encoding="utf-8")


def test_idea_writer_pads_inline_braces(tmp_path):
    out = _standardize(tmp_path, "idea", _IDEA_FILE)
    assert "NOT = { country_exists = ENG }" in out
    assert "NOT = { TST = { has_idea = EU_member } }" in out
    assert "NOT = { western_liberals_are_in_power = yes }" in out
    assert "{country_exists" not in out


def test_focus_writer_pads_inline_braces(tmp_path):
    out = _standardize(tmp_path, "focus", _FOCUS_FILE)
    assert "NOT = { country_exists = ENG }" in out


def test_log_string_survives_standardization(tmp_path):
    out = _standardize(tmp_path, "focus", _FOCUS_FILE)
    assert '"[GetDateText]: [Root.GetName]: Focus TST_focus"' in out


def test_second_pass_is_a_no_op(tmp_path):
    first = _standardize(tmp_path, "idea", _IDEA_FILE)
    second = _standardize(tmp_path, "idea", first, name="second.txt")
    assert second == first
