"""Regression: global flags read only in map/adjacency_rules.txt count as used.

Canal/strait closure logic sets flags in common/scripted_effects and the
adjacency rules consume them in is_disabled blocks. should_skip_file used to
skip the whole map/ tree, so the reads were invisible and the setters were
reported unused (PANAMA_CANAL_BLOCKED / GLOBAL_KIEL_CANAL_BLOCKED on CI).
"""

from validate_variables import Validator, Variables

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


def _validator(tmp_path, with_map=True):
    effects = tmp_path / "common" / "scripted_effects"
    effects.mkdir(parents=True)
    (effects / "00_test.txt").write_text(EFFECTS, encoding="utf-8")
    if with_map:
        map_dir = tmp_path / "map"
        map_dir.mkdir()
        (map_dir / "adjacency_rules.txt").write_text(ADJACENCY, encoding="utf-8")
    return Validator(str(tmp_path), use_colors=False, workers=1)


def _unused_global_flags(tmp_path, with_map=True):
    validator = _validator(tmp_path, with_map=with_map)
    set_paths, used_paths, _ = Variables.get_all_flags(
        mod_path=str(tmp_path),
        lowercase=False,
        flag_type="global",
        workers=1,
    )
    validator.validate_unused_flags("global", [], set_paths, used_paths)
    return validator._issues


def test_flag_read_only_in_adjacency_rules_is_not_unused(tmp_path):
    assert _unused_global_flags(tmp_path) == []


def test_without_adjacency_rules_the_setter_is_still_unused(tmp_path):
    issues = _unused_global_flags(tmp_path, with_map=False)
    assert any("TEST_CANAL_BLOCKED" in str(issue) for issue in issues)
