"""Tests for the add_tech_bonus name check in validate_focus_tree.

Every add_tech_bonus inside a completion_reward (or joint-focus reward
variant) needs a name = parameter whose value resolves to a loc key —
otherwise the research-bonus row shows no source in-game. Convention is
name = <focus id>, reusing the focus title loc key. A technology category
token satisfies the loc-key test trivially (every CAT_ name is localised)
while naming the tech field rather than the focus, so it has its own finding.
"""

from validate_focus_tree import Validator, _extract_tech_bonuses


def _write_focus_file(tmp_path, content):
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True)
    fpath = nf_dir / "test.txt"
    fpath.write_text(content, encoding="utf-8")
    return fpath


def _write_tech_tags(tmp_path, cats):
    tags_dir = tmp_path / "common" / "technology_tags"
    tags_dir.mkdir(parents=True)
    body = "\n".join(f"\t\t{c}" for c in cats)
    (tags_dir / "00_technology.txt").write_text(
        f"technology_categories = {{\n{body}\n}}\n", encoding="utf-8"
    )


def _write_loc(tmp_path, keys):
    loc_dir = tmp_path / "localisation" / "english"
    loc_dir.mkdir(parents=True)
    lines = "\n".join(f' {k}:0 "x"' for k in keys)
    (loc_dir / "test_l_english.yml").write_text(
        f"l_english:\n{lines}\n", encoding="utf-8-sig"
    )


FOCUS_TEMPLATE = """focus_tree = {{
	id = test_tree
	focus = {{
		id = TAG_focus_a
		x = 0
		y = 0
		completion_reward = {{
{reward}
		}}
	}}
}}
"""


def test_worker_finds_multiline_name(tmp_path):
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward=(
                "			add_tech_bonus = {\n"
                "				name = TAG_focus_a\n"
                "				bonus = 0.5\n"
                "				uses = 1\n"
                "				category = CAT_industry\n"
                "			}"
            )
        ),
    )
    out = _extract_tech_bonuses((str(fpath), str(tmp_path)))
    assert out == [("TAG_focus_a", "TAG_focus_a", str(fpath), 8)]


def test_worker_finds_single_line_name(tmp_path):
    # The benelux joint-focus form: whole block on one line
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = TAG_focus_a bonus = 0.30 uses = 2 category = CAT_air_eqp }"
        ),
    )
    out = _extract_tech_bonuses((str(fpath), str(tmp_path)))
    assert len(out) == 1
    assert out[0][1] == "TAG_focus_a"


def test_worker_reports_missing_name(tmp_path):
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward=(
                "			add_tech_bonus = {\n"
                "				bonus = 0.5\n"
                "				uses = 1\n"
                "				category = CAT_industry\n"
                "			}"
            )
        ),
    )
    out = _extract_tech_bonuses((str(fpath), str(tmp_path)))
    assert len(out) == 1
    assert out[0][1] is None


def test_worker_scans_joint_reward_variants(tmp_path):
    content = """joint_focus = {
	id = TAG_joint
	x = 0
	y = 0
	completion_reward_joint_originator = {
		add_tech_bonus = { name = TAG_joint bonus = 0.30 uses = 2 category = CAT_air_eqp }
	}
	completion_reward_joint_member = {
		add_tech_bonus = { bonus = 0.15 uses = 1 category = CAT_air_eqp }
	}
}
"""
    fpath = _write_focus_file(tmp_path, content)
    out = _extract_tech_bonuses((str(fpath), str(tmp_path)))
    names = [name for _, name, _, _ in out]
    assert names == ["TAG_joint", None]


def test_worker_ignores_bonus_outside_completion_reward(tmp_path):
    content = """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 0
		select_effect = {
			add_tech_bonus = { bonus = 0.5 uses = 1 category = CAT_industry }
		}
		completion_reward = {
			add_political_power = 50
		}
	}
}
"""
    fpath = _write_focus_file(tmp_path, content)
    out = _extract_tech_bonuses((str(fpath), str(tmp_path)))
    assert out == []


def _run_check(tmp_path, **kwargs):
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1, **kwargs)
    v.validate_tech_bonus_names()
    return v


def test_validator_warns_on_missing_name(tmp_path):
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a"])
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_warns_on_unlocalised_name(tmp_path):
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = TAG_typoed_name bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a"])
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_clean_on_localised_name(tmp_path):
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = TAG_focus_a bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a"])
    v = _run_check(tmp_path)
    assert v.warnings_found == 0
    assert v.errors_found == 0


def test_validator_skips_dynamic_bracket_names(tmp_path):
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = [TAG.GetTechName] bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a"])
    v = _run_check(tmp_path)
    assert v.warnings_found == 0


def test_validator_warns_on_category_as_name(tmp_path):
    # CAT_industry is localised, so the loc-key branch would pass it silently.
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = CAT_industry bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a", "CAT_industry"])
    _write_tech_tags(tmp_path, ["CAT_industry", "CAT_renewable"])
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_clean_when_name_is_focus_id_with_tags_loaded(tmp_path):
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = TAG_focus_a bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a", "CAT_industry"])
    _write_tech_tags(tmp_path, ["CAT_industry"])
    v = _run_check(tmp_path)
    assert v.warnings_found == 0
    assert v.errors_found == 0


def test_category_name_check_noop_without_tech_tags(tmp_path):
    # No common/technology_tags/ — the category set is empty and the check
    # degrades to the plain loc-key test rather than misreporting.
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = CAT_industry bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a", "CAT_industry"])
    v = _run_check(tmp_path)
    assert v.warnings_found == 0


def test_name_not_focus_id_is_opt_in(tmp_path):
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = TAG_shared_bonus bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a", "TAG_shared_bonus"])
    _write_tech_tags(tmp_path, ["CAT_industry"])
    assert _run_check(tmp_path).warnings_found == 0
    assert _run_check(tmp_path, name_not_focus_id=True).warnings_found == 1
