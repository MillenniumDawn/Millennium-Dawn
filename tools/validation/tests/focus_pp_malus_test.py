"""Tests for the PP malus check in validate_focus_tree.

A literal add_political_power = -N inside a focus's completion_reward is
flagged; occurrences inside an effect_tooltip subtree (previewing a PP
change applied elsewhere) and outside completion_reward (select_effect,
bypass) are not.
"""

from validate_focus_tree import Validator, _extract_pp_malus


def _write_focus_file(tmp_path, content):
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True, exist_ok=True)
    fpath = nf_dir / "test.txt"
    fpath.write_text(content, encoding="utf-8")
    return fpath


FOCUS_TEMPLATE = """focus_tree = {{
	id = test_tree
	focus = {{
		id = TAG_focus_a
		x = 0
		y = 0
		cost = 1
		{extra}
		completion_reward = {{
			{reward}
		}}
	}}
}}
"""


def _ids(tmp_path, reward, extra=""):
    fpath = _write_focus_file(
        tmp_path, FOCUS_TEMPLATE.format(reward=reward, extra=extra)
    )
    return {d[0] for d in _extract_pp_malus((str(fpath), str(tmp_path)))}


def test_negative_pp_in_completion_reward_is_flagged(tmp_path):
    assert _ids(tmp_path, "add_political_power = -50") == {"TAG_focus_a"}


def test_positive_pp_is_clean(tmp_path):
    assert _ids(tmp_path, "add_political_power = 50") == set()


def test_negative_pp_inside_effect_tooltip_is_clean(tmp_path):
    reward = "effect_tooltip = {\n\t\t\t\tadd_political_power = -50\n\t\t\t}"
    assert _ids(tmp_path, reward) == set()


def test_negative_pp_in_select_effect_is_clean(tmp_path):
    extra = "select_effect = {\n\t\t\tadd_political_power = -50\n\t\t}"
    assert _ids(tmp_path, "newline = yes", extra=extra) == set()


def test_negative_pp_in_bypass_is_clean(tmp_path):
    extra = "bypass = {\n\t\t\tadd_political_power = -50\n\t\t}"
    assert _ids(tmp_path, "newline = yes", extra=extra) == set()


def test_variable_form_is_clean(tmp_path):
    assert _ids(tmp_path, "add_political_power = some_var") == set()


def test_validator_reports_pp_malus_as_warning_not_error(tmp_path):
    _write_focus_file(
        tmp_path, FOCUS_TEMPLATE.format(reward="add_political_power = -50", extra="")
    )
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_pp_malus_in_rewards()
    assert v.warnings_found == 1
    assert v.errors_found == 0
