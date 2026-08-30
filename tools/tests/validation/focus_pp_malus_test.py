"""Tests for the PP malus check in validate_focus_tree.

A literal add_political_power = -N inside a focus's completion_reward is
flagged; occurrences inside an effect_tooltip subtree (previewing a PP
change applied elsewhere) and outside completion_reward (select_effect,
bypass) are not.
"""

import re

from shared.paths import REPO_ROOT as _MOD_ROOT
from validate_focus_tree import (
    _PP_MALUS_EXEMPT_FOCUS_IDS,
    Validator,
    _extract_pp_malus,
)


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


def test_exempt_focus_id_is_not_reported(tmp_path):
    exempt = sorted(_PP_MALUS_EXEMPT_FOCUS_IDS)[0]
    content = FOCUS_TEMPLATE.format(
        reward="add_political_power = -100", extra=""
    ).replace("TAG_focus_a", exempt)
    _write_focus_file(tmp_path, content)
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_pp_malus_in_rewards()
    assert v.warnings_found == 0
    assert v.errors_found == 0


def _focus_ids_with_pp_malus():
    """Focus ids in the real tree that still carry a literal negative
    add_political_power, found by walking back to the nearest preceding id."""
    id_or_malus = re.compile(
        r"^\s*(?:id\s*=\s*(\S+)|(add_political_power\s*=\s*-\d))", re.MULTILINE
    )
    found = set()
    for path in sorted((_MOD_ROOT / "common" / "national_focus").glob("*.txt")):
        current = None
        for m in id_or_malus.finditer(
            path.read_text(encoding="utf-8-sig", errors="replace")
        ):
            if m.group(1):
                current = m.group(1)
            elif current:
                found.add(current)
    return found


def test_pp_malus_exemptions_are_still_live():
    stale = sorted(_PP_MALUS_EXEMPT_FOCUS_IDS - _focus_ids_with_pp_malus())
    assert not stale, (
        "_PP_MALUS_EXEMPT_FOCUS_IDS names focuses that no longer apply a PP "
        f"malus: {stale}. Remove them from the exemption set."
    )
