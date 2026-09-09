"""Explicit `name = X` loc reuse is intentional, not a collision.

Regression context: CHI_sasac_idea (common/ideas/05_china.txt) sets
`name = CHI_sasac_founding` to reuse the focus CHI_sasac_founding
(common/national_focus/05_china.txt:1226) strings. The removed
loc-key-collision check warned on every such intentional share (142
warnings repo-wide) and contradicted the loc-consolidation guidance that
recommends `name = X` reuse. These tests pin the intended behavior: sharing
via `name =` is clean, and missing-localisation resolves through the
override as the definitive key.
"""

from shared.suite import write_under as _write
from validate_ideas import Validator

IDEA_TAGS = """idea_categories = {
	country = { type = national_spirit }
}
"""

IDEAS = """ideas = {
	country = {
		COL_idea = {
			name = shared_key
			picture = shared
		}
	}
}
"""

FOCUS = """focus = {
	id = shared_key
	icon = generic_air_bonus
}
"""


def _validator(root, **kwargs):
    return Validator(str(root), use_colors=False, workers=1, **kwargs)


def _setup_shared_key(root):
    _write(root, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(root, "common/ideas/test.txt", IDEAS)
    _write(root, "common/national_focus/tree.txt", FOCUS)
    _write(
        root,
        "localisation/english/collide_l_english.yml",
        'l_english:\n shared_key:0 "Shared"\n shared_key_desc:0 "Shared desc"\n',
    )


def test_name_override_collision_check_is_removed():
    assert not hasattr(Validator, "validate_name_override_collisions")
    assert not hasattr(Validator, "_object_loc_keys")


def test_name_override_sharing_focus_keys_is_clean(tmp_path):
    _setup_shared_key(tmp_path)
    validator = _validator(tmp_path)
    defined, _issues, _by_file = validator._parse_all_ideas()
    assert defined["COL_idea"] == ("country", "shared_key", "shared")
    validator.validate_missing_localisation(defined)
    assert [
        issue for issue in validator._issues if issue.category == "loc-key-collision"
    ] == []
    assert validator._issues == []


def test_missing_localisation_resolves_through_name_override(tmp_path):
    _setup_shared_key(tmp_path)
    validator = _validator(tmp_path)
    defined, _issues, _by_file = validator._parse_all_ideas()
    validator.validate_missing_localisation(defined)
    assert [
        issue
        for issue in validator._issues
        if issue.category == "missing-idea-localisation"
    ] == []


def test_missing_localisation_flags_missing_override_keys(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(tmp_path, "common/ideas/test.txt", IDEAS)
    validator = _validator(tmp_path)
    defined, _issues, _by_file = validator._parse_all_ideas()
    validator.validate_missing_localisation(defined)
    findings = [
        issue
        for issue in validator._issues
        if issue.category == "missing-idea-localisation"
    ]
    assert len(findings) == 1
    assert "shared_key" in findings[0].message
    assert "COL_idea" in findings[0].message
