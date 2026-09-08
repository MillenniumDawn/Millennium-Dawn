"""Tests for the idea name-override vs focus/decision id loc collision check."""

from shared.suite import write_under as _write
from validate_ideas import Validator

IDEA_TAGS = """idea_categories = {
	country = { type = national_spirit }
}
"""

IDEAS = """ideas = {
	country = {
		COL_idea = {
			name = {key}
			picture = shared
		}
		PLAIN_{key} = {
			picture = shared
		}
	}
}
"""

FOCUS = """focus = {
	id = {key}
	icon = generic_air_bonus
}
"""

FOCUS_NESTED_ID = """focus = {
	id = real_focus
	icon = generic_air_bonus
	completion_reward = {
		country_event = { id = {key} }
	}
}
"""

DECISION_HEAD = "sweden_category = {\n\tsweden_dec = {\n\t\ticon = generic_operation\n"
DECISION_END = "\t}\n}\n"


def _validator(root, **kwargs):
    return Validator(str(root), use_colors=False, workers=1, **kwargs)


def _ideas_and_file(root, key):
    _write(root, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(root, "common/ideas/test.txt", IDEAS.replace("{key}", key))
    validator = _validator(root)
    defined, _issues, by_file = validator._parse_all_ideas()
    return validator, defined, by_file


def _collision_findings(validator):
    return [
        (issue.category, issue.message, issue.file)
        for issue in validator._issues
        if issue.category == "loc-key-collision"
    ]


def test_name_override_colliding_with_focus_id_is_warned(tmp_path):
    validator, defined, by_file = _ideas_and_file(tmp_path, "shared_key")
    _write(
        tmp_path,
        "common/national_focus/tree.txt",
        FOCUS.replace("{key}", "shared_key"),
    )
    _write(
        tmp_path,
        "localisation/english/collide_l_english.yml",
        ' l_english:\n shared_key:0 "Shared"\n shared_key_desc:0 "Shared desc"\n',
    )

    validator.validate_name_override_collisions(defined, by_file)

    findings = _collision_findings(validator)
    assert len(findings) == 2
    assert all(f[0] == "loc-key-collision" for f in findings)
    assert "`shared_key`" in findings[0][1]
    assert "focus `shared_key` (common/national_focus/tree.txt:1)" in findings[0][1]
    assert "shared-key collision" in findings[0][1]
    assert "silently overrides" not in findings[0][1]
    assert findings[0][2] == "common/ideas/test.txt"


def test_name_override_colliding_with_decision_id_is_warned(tmp_path):
    validator, defined, by_file = _ideas_and_file(tmp_path, "sweden_dec")
    _write(
        tmp_path,
        "common/decisions/test.txt",
        DECISION_HEAD + "\t\tallowed = { always = yes }\n" + DECISION_END,
    )
    _write(
        tmp_path,
        "localisation/english/collide_l_english.yml",
        ' l_english:\n sweden_dec:0 "Sweden"\n',
    )

    validator.validate_name_override_collisions(defined, by_file)

    findings = _collision_findings(validator)
    assert len(findings) == 1
    assert "decision `sweden_dec` (common/decisions/test.txt)" in findings[0][1]


def test_unlocalised_collision_key_is_not_a_finding(tmp_path):
    validator, defined, by_file = _ideas_and_file(tmp_path, "shared_key")
    _write(
        tmp_path,
        "common/national_focus/tree.txt",
        FOCUS.replace("{key}", "shared_key"),
    )

    validator.validate_name_override_collisions(defined, by_file)

    assert _collision_findings(validator) == []


def test_bare_idea_id_collision_is_out_of_scope(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(
        tmp_path,
        "common/ideas/test.txt",
        IDEAS.replace("{key}", "shared_key"),
    )
    _write(
        tmp_path,
        "common/national_focus/tree.txt",
        FOCUS.replace("{key}", "PLAIN_shared_key"),
    )
    _write(
        tmp_path,
        "localisation/english/collide_l_english.yml",
        ' l_english:\n PLAIN_shared_key:0 "Shared"\n',
    )
    validator = _validator(tmp_path)
    defined, _issues, by_file = validator._parse_all_ideas()

    validator.validate_name_override_collisions(defined, by_file)

    assert _collision_findings(validator) == []


def test_nested_non_object_keys_do_not_own_loc_keys(tmp_path):
    validator, defined, by_file = _ideas_and_file(tmp_path, "ovr_key")
    _write(
        tmp_path,
        "common/national_focus/tree.txt",
        FOCUS_NESTED_ID.replace("{key}", "ovr_key"),
    )
    _write(
        tmp_path,
        "common/decisions/test.txt",
        DECISION_HEAD
        + "\t\tcomplete_effect = { create_ship = { name = ovr_key } }\n"
        + DECISION_END,
    )
    _write(
        tmp_path,
        "localisation/english/collide_l_english.yml",
        ' l_english:\n ovr_key:0 "Override"\n',
    )

    validator.validate_name_override_collisions(defined, by_file)

    assert _collision_findings(validator) == []


def test_staged_mode_reports_only_when_a_side_is_staged(tmp_path):
    validator, defined, by_file = _ideas_and_file(tmp_path, "shared_key")
    _write(
        tmp_path,
        "common/national_focus/tree.txt",
        FOCUS.replace("{key}", "shared_key"),
    )
    _write(
        tmp_path,
        "localisation/english/collide_l_english.yml",
        ' l_english:\n shared_key:0 "Shared"\n',
    )

    validator.staged_only = True
    validator.staged_files = []
    validator.validate_name_override_collisions(defined, by_file)
    assert _collision_findings(validator) == []

    validator.staged_files = ["common/national_focus/tree.txt"]
    validator.validate_name_override_collisions(defined, by_file)
    assert len(_collision_findings(validator)) == 1


def test_dynamic_focus_id_is_not_an_owner(tmp_path):
    validator, defined, by_file = _ideas_and_file(tmp_path, "TAG_shared_key")
    _write(
        tmp_path,
        "common/national_focus/tree.txt",
        FOCUS.replace("{key}", "[ROOT.GetTag]_shared_key"),
    )
    _write(
        tmp_path,
        "localisation/english/collide_l_english.yml",
        ' l_english:\n TAG_shared_key:0 "Shared"\n',
    )

    validator.validate_name_override_collisions(defined, by_file)

    assert _collision_findings(validator) == []
