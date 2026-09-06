"""Tests for the bonus source name check in validate_bonus_names.

Six effects print a `name =` loc key as the *source* of the bonus they grant.
The convention is that the name identifies the granting object — the focus id,
the decision token, the event id (or its `.t` title key), the MIO trait token —
so the check resolves the enclosing block before judging the name. A technology
category token satisfies the loc-key test trivially (every CAT_ name is
localised) while naming the tech field rather than the source, so it has its own
finding.
"""

from validate_bonus_names import Validator, _scan_file


def _write(tmp_path, relpath, content):
    fpath = tmp_path / relpath
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")
    return fpath


def _write_focus_file(tmp_path, content):
    return _write(tmp_path, "common/national_focus/test.txt", content)


def _write_tech_tags(tmp_path, cats):
    body = "\n".join(f"\t\t{c}" for c in cats)
    _write(
        tmp_path,
        "common/technology_tags/00_technology.txt",
        f"technology_categories = {{\n{body}\n}}\n",
    )


def _write_loc(tmp_path, keys):
    loc_dir = tmp_path / "localisation" / "english"
    loc_dir.mkdir(parents=True, exist_ok=True)
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


def _run_check(tmp_path, **kwargs):
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1, **kwargs)
    v.validate_bonus_names()
    return v


def _categories(validator):
    return sorted(i.category for i in validator._issues)


# ---------------------------------------------------------------------------
# Worker: owner resolution per block type
# ---------------------------------------------------------------------------


def test_worker_resolves_focus_owner(tmp_path):
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
    out = _scan_file((str(fpath), str(tmp_path)))
    assert out == [
        (
            "add_tech_bonus",
            "TAG_focus_a",
            "focus",
            "TAG_focus_a",
            ("TAG_focus_a",),
            "common/national_focus/test.txt",
            8,
        )
    ]


def test_worker_reads_single_line_block(tmp_path):
    # The benelux joint-focus form: whole block on one line.
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = TAG_focus_a bonus = 0.30 uses = 2 category = CAT_air_eqp }"
        ),
    )
    out = _scan_file((str(fpath), str(tmp_path)))
    assert [r[1] for r in out] == ["TAG_focus_a"]


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
    out = _scan_file((str(fpath), str(tmp_path)))
    assert [(r[1], r[3]) for r in out] == [
        ("TAG_joint", "TAG_joint"),
        (None, "TAG_joint"),
    ]


def test_worker_resolves_decision_owner(tmp_path):
    content = """TAG_category = {
	TAG_the_decision = {
		complete_effect = {
			add_tech_bonus = { name = TAG_the_decision bonus = 0.5 uses = 1 category = CAT_industry }
		}
	}
}
"""
    fpath = _write(tmp_path, "common/decisions/test.txt", content)
    out = _scan_file((str(fpath), str(tmp_path)))
    assert [(r[2], r[3]) for r in out] == [("decision", "TAG_the_decision")]


def test_worker_resolves_event_owner_and_accepts_title_key(tmp_path):
    content = """add_namespace = test

country_event = {
	id = test.1
	is_triggered_only = yes
	option = {
		name = test.1.a
		add_tech_bonus = { name = test.1.t bonus = 0.5 uses = 1 category = CAT_industry }
	}
}
"""
    fpath = _write(tmp_path, "events/test.txt", content)
    out = _scan_file((str(fpath), str(tmp_path)))
    assert [(r[1], r[2], r[3], r[4]) for r in out] == [
        ("test.1.t", "event", "test.1", ("test.1", "test.1.t"))
    ]


def test_worker_resolves_mio_trait_owner(tmp_path):
    content = """TAG_company_manufacturer = {
	allowed = { original_tag = TAG }

	trait = {
		token = TAG_the_trait
		name = TAG_the_trait

		on_complete = {
			FROM = {
				add_tech_bonus = { name = TAG_the_trait bonus = 0.1 uses = 1 category = CAT_industry }
			}
		}
	}
}
"""
    fpath = _write(
        tmp_path,
        "common/military_industrial_organization/organizations/test.txt",
        content,
    )
    out = _scan_file((str(fpath), str(tmp_path)))
    assert [(r[2], r[3]) for r in out] == [("MIO trait", "TAG_the_trait")]


def test_worker_leaves_owner_unset_without_id_convention(tmp_path):
    content = """some_scripted_effect = {
	add_tech_bonus = { name = shared_lab_bonus bonus = 0.5 uses = 1 category = CAT_industry }
}
"""
    fpath = _write(tmp_path, "common/scripted_effects/test.txt", content)
    out = _scan_file((str(fpath), str(tmp_path)))
    assert [(r[2], r[3], r[4]) for r in out] == [(None, None, ())]


def test_worker_reads_bonus_outside_completion_reward(tmp_path):
    # Unlike the old focus-only check, a select_effect bonus is still a bonus.
    content = """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 0
		select_effect = {
			add_tech_bonus = { bonus = 0.5 uses = 1 category = CAT_industry }
		}
	}
}
"""
    fpath = _write_focus_file(tmp_path, content)
    out = _scan_file((str(fpath), str(tmp_path)))
    assert [(r[1], r[3]) for r in out] == [(None, "TAG_focus_a")]


def test_worker_covers_all_six_effects(tmp_path):
    content = """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 0
		completion_reward = {
			add_tech_bonus = { name = TAG_focus_a bonus = 0.1 uses = 1 category = CAT_industry }
			add_equipment_bonus = { name = TAG_focus_a bonus = { armor = { armor_value = 3 } } }
			add_design_template_bonus = { name = TAG_focus_a uses = 1 cost_factor = 0.4 }
			add_doctrine_cost_reduction = { name = TAG_focus_a cost_reduction = 0.5 uses = 1 category = CAT_land_doctrine }
			add_daily_mastery = { name = TAG_focus_a amount = 0.15 days = 360 folder = naval }
			add_mastery_bonus = { name = TAG_focus_a bonus = 0.1 days = 90 folder = land }
		}
	}
}
"""
    fpath = _write_focus_file(tmp_path, content)
    out = _scan_file((str(fpath), str(tmp_path)))
    assert [r[0] for r in out] == [
        "add_tech_bonus",
        "add_equipment_bonus",
        "add_design_template_bonus",
        "add_doctrine_cost_reduction",
        "add_daily_mastery",
        "add_mastery_bonus",
    ]
    assert {r[1] for r in out} == {"TAG_focus_a"}


# ---------------------------------------------------------------------------
# Validator: the four findings
# ---------------------------------------------------------------------------


def test_validator_warns_on_missing_name(tmp_path):
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a"])
    v = _run_check(tmp_path)
    assert _categories(v) == ["bonus-name-missing"]


def test_validator_requires_name_on_optional_name_effects(tmp_path):
    # Vanilla lets these omit `name`; MD wants an explicit source in every case.
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward=(
                "			add_design_template_bonus = { uses = 1 cost_factor = 0.4 equipment = light_tank_chassis }\n"
                "			add_equipment_bonus = { project = FROM bonus = { armor = { armor_value = 3 } } }"
            )
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a"])
    v = _run_check(tmp_path)
    assert _categories(v) == ["bonus-name-missing", "bonus-name-missing"]


def test_validator_warns_on_unlocalised_name(tmp_path):
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = TAG_typoed_name bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a"])
    v = _run_check(tmp_path)
    assert _categories(v) == ["bonus-name-missing-loc"]


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
    assert _categories(v) == ["bonus-name-is-category"]


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


def test_name_not_owner_id_is_opt_in(tmp_path):
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            reward="			add_tech_bonus = { name = TAG_shared_bonus bonus = 0.5 uses = 1 category = CAT_industry }"
        ),
    )
    _write_loc(tmp_path, ["TAG_focus_a", "TAG_shared_bonus"])
    _write_tech_tags(tmp_path, ["CAT_industry"])
    assert _run_check(tmp_path).warnings_found == 0
    assert _categories(_run_check(tmp_path, name_not_owner_id=True)) == [
        "bonus-name-not-owner-id"
    ]


def test_owner_token_check_matches_decision_token(tmp_path):
    content = """TAG_category = {
	TAG_the_decision = {
		complete_effect = {
			add_tech_bonus = { name = TAG_the_decision bonus = 0.5 uses = 1 category = CAT_industry }
			add_doctrine_cost_reduction = { name = TAG_other_thing cost_reduction = 0.5 uses = 1 category = CAT_land_doctrine }
		}
	}
}
"""
    _write(tmp_path, "common/decisions/test.txt", content)
    _write_loc(tmp_path, ["TAG_the_decision", "TAG_other_thing"])
    _write_tech_tags(tmp_path, ["CAT_industry"])
    assert _run_check(tmp_path).warnings_found == 0
    assert _categories(_run_check(tmp_path, name_not_owner_id=True)) == [
        "bonus-name-not-owner-id"
    ]


def test_owner_token_check_accepts_event_id_or_title_key(tmp_path):
    content = """add_namespace = test

country_event = {
	id = test.1
	is_triggered_only = yes
	option = {
		name = test.1.a
		add_tech_bonus = { name = test.1.t bonus = 0.5 uses = 1 category = CAT_industry }
		add_doctrine_cost_reduction = { name = test.1 cost_reduction = 0.5 uses = 1 category = CAT_land_doctrine }
		add_daily_mastery = { name = test.2.t amount = 0.15 days = 360 folder = naval }
	}
}
"""
    _write(tmp_path, "events/test.txt", content)
    _write_loc(tmp_path, ["test.1", "test.1.t", "test.2.t"])
    _write_tech_tags(tmp_path, ["CAT_industry"])
    assert _run_check(tmp_path).warnings_found == 0
    assert _categories(_run_check(tmp_path, name_not_owner_id=True)) == [
        "bonus-name-not-owner-id"
    ]


def test_owner_token_check_skips_blocks_without_an_owner(tmp_path):
    # A scripted effect has no id convention, so the opt-in check stays quiet.
    _write(
        tmp_path,
        "common/scripted_effects/test.txt",
        "some_scripted_effect = {\n"
        "	add_tech_bonus = { name = shared_lab_bonus bonus = 0.5 uses = 1 category = CAT_industry }\n"
        "}\n",
    )
    _write_loc(tmp_path, ["shared_lab_bonus"])
    _write_tech_tags(tmp_path, ["CAT_industry"])
    assert _run_check(tmp_path, name_not_owner_id=True).warnings_found == 0
