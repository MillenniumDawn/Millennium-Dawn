"""Regression: global flags read only in map/adjacency_rules.txt count as used.

Canal/strait closure logic sets flags in common/scripted_effects and the
adjacency rules consume them in is_disabled blocks. should_skip_file used to
skip the whole map/ tree, so the reads were invisible and the setters were
reported unused (PANAMA_CANAL_BLOCKED / GLOBAL_KIEL_CANAL_BLOCKED on CI).
"""

from validate_variables import Validator

EFFECTS = """\
canal_block_effect = {
	if = {
		limit = { has_war_with = TUR }
		set_global_flag = TEST_CANAL_BLOCKED
	}
	else = { clr_global_flag = TEST_CANAL_BLOCKED }
}
"""

ADJACENCY = """\
adjacency_rule = {
	name = "TEST_STRAIT"

	is_disabled = {
		has_global_flag = TEST_CANAL_BLOCKED
		tooltip = test_blocked_tt
	}
}
"""


def _flag_findings(tmp_path, with_map=True):
    effects = tmp_path / "common" / "scripted_effects"
    effects.mkdir(parents=True)
    (effects / "00_test.txt").write_text(EFFECTS, encoding="utf-8")
    if with_map:
        map_dir = tmp_path / "map"
        map_dir.mkdir()
        (map_dir / "adjacency_rules.txt").write_text(ADJACENCY, encoding="utf-8")
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return [
        (issue.message, issue.file, issue.line)
        for issue in validator._issues
        if issue.category == "variables"
    ]


def test_flag_read_only_in_adjacency_rules_is_not_unused(tmp_path):
    assert _flag_findings(tmp_path) == []


def test_without_adjacency_rules_the_setter_is_still_unused(tmp_path):
    assert _flag_findings(tmp_path, with_map=False) == [
        ("TEST_CANAL_BLOCKED", "common/scripted_effects/00_test.txt", 4)
    ]
