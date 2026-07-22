"""Tests for the ai_will_do staffing/bankruptcy guard checks in
validate_focus_tree (issue #2233 + the AGENTS.md bankruptcy convention).

A focus whose completion_reward builds a staffable building needs a
factor = 0 ai_will_do modifier checking the matching can_staff_an_* trigger.
A focus whose reward spends money (summed negative treasury_change, or a
money-spending scripted effect) needs the bankruptcy_incoming_collapse guard;
a guard on a focus with no money cost is flagged as unneeded.
"""

from validate_focus_tree import Validator, _extract_ai_guard_data


def _write_focus_file(tmp_path, content):
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True, exist_ok=True)
    fpath = nf_dir / "test.txt"
    fpath.write_text(content, encoding="utf-8")
    return fpath


def _write_effects_file(tmp_path, extra=""):
    fx_dir = tmp_path / "common" / "scripted_effects"
    fx_dir.mkdir(parents=True, exist_ok=True)
    (fx_dir / "00_scripted_effects.txt").write_text(
        """one_random_industrial_complex = {
	random_owned_controlled_state = {
		add_building_construction = {
			type = industrial_complex
			level = 1
			instant_build = yes
		}
	}
}
grant_pp_effect = {
	add_political_power = 25
}
"""
        + extra,
        encoding="utf-8",
    )


FOCUS_TEMPLATE = """focus_tree = {{
	id = test_tree
	focus = {{
		id = TAG_focus_a
		x = 0
		y = 0
		cost = {cost}
		{extra}
		completion_reward = {{
			{reward}
		}}
		ai_will_do = {{
			base = 1
			{modifiers}
		}}
	}}
}}
"""

GUARD_OR_FORM = """modifier = {
				factor = 0
				OR = {
					has_active_mission = bankruptcy_incoming_collapse
					can_staff_an_industrial_complex = no
				}
			}"""

GUARD_FLAT_FORM = """modifier = {
				factor = 0
				can_staff_an_industrial_complex = no
			}"""

BANKRUPTCY_GUARD = """modifier = {
				factor = 0
				has_active_mission = bankruptcy_incoming_collapse
			}"""

STAFFABLE_MAP = {"one_random_industrial_complex": frozenset({"industrial_complex"})}


def _guard_data(fpath, tmp_path, staffable=STAFFABLE_MAP, money=frozenset()):
    return _extract_ai_guard_data((str(fpath), str(tmp_path), staffable, money))


def _spend(amount):
    """A reward that sets treasury_change and applies it via the budget effect."""
    return (
        f"set_temp_variable = {{ treasury_change = {amount} }}\n"
        "			modify_treasury_effect = yes"
    )


def _run_check(tmp_path):
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_ai_will_do_guards()
    return v


# --------------------------------------------------------------------------
# can_staff worker facts
# --------------------------------------------------------------------------


def test_worker_rejects_or_guard_form(tmp_path):
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="",
            reward="one_random_industrial_complex = yes",
            modifiers=GUARD_OR_FORM,
        ),
    )
    out = _guard_data(fpath, tmp_path)
    assert len(out) == 1
    d = out[0]
    assert d["buildings"] == {"industrial_complex"}
    assert d["guards"] == set()


def test_worker_credits_and_guard_form(tmp_path):
    modifiers = """modifier = {
				factor = 0
				AND = {
					has_active_mission = bankruptcy_incoming_collapse
					can_staff_an_industrial_complex = no
				}
			}"""
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="",
            reward="one_random_industrial_complex = yes",
            modifiers=modifiers,
        ),
    )
    out = _guard_data(fpath, tmp_path)
    assert out[0]["guards"] == {
        "bankruptcy_incoming_collapse",
        "can_staff_an_industrial_complex",
    }


def test_worker_detects_direct_add_building_construction(tmp_path):
    reward = (
        "add_building_construction = {\n"
        "				type = arms_factory\n"
        "				level = 1\n"
        "				instant_build = yes\n"
        "			}"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    out = _guard_data(fpath, tmp_path)
    assert out[0]["buildings"] == {"arms_factory"}
    assert out[0]["guards"] == set()


def test_worker_ignores_building_inside_effect_tooltip(tmp_path):
    """An effect_tooltip previews an outcome that happens elsewhere (here, in
    the target's event), so the focus does not build the arms_factory."""
    reward = (
        "GER = { country_event = x.1 }\n"
        "			custom_effect_tooltip = TT_IF_THEY_ACCEPT\n"
        "			effect_tooltip = {\n"
        "				GER = {\n"
        "					add_building_construction = {\n"
        "						type = arms_factory\n"
        "						level = 1\n"
        "						instant_build = yes\n"
        "					}\n"
        "				}\n"
        "			}"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    out = _guard_data(fpath, tmp_path)
    assert out[0]["buildings"] == set()


def test_worker_ignores_builder_effect_inside_effect_tooltip(tmp_path):
    """Same rule for a scripted builder effect named inside the preview."""
    reward = "effect_tooltip = {\n				one_random_industrial_complex = yes\n			}"
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    out = _guard_data(fpath, tmp_path)
    assert out[0]["buildings"] == set()


def test_worker_still_sees_building_outside_effect_tooltip(tmp_path):
    """A real construction alongside a preview is still a construction."""
    reward = (
        "add_building_construction = {\n"
        "				type = arms_factory\n"
        "				level = 1\n"
        "				instant_build = yes\n"
        "			}\n"
        "			effect_tooltip = {\n"
        "				one_random_industrial_complex = yes\n"
        "			}"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    out = _guard_data(fpath, tmp_path)
    assert out[0]["buildings"] == {"arms_factory"}


def test_worker_ignores_nonzero_factor_modifiers(tmp_path):
    modifiers = """modifier = {
				factor = 0.5
				can_staff_an_industrial_complex = no
			}"""
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="",
            reward="one_random_industrial_complex = yes",
            modifiers=modifiers,
        ),
    )
    out = _guard_data(fpath, tmp_path)
    assert out[0]["guards"] == set()


def test_worker_credits_not_yes_guard_form(tmp_path):
    modifiers = """modifier = {
				factor = 0
				NOT = { can_staff_an_industrial_complex = yes }
			}"""
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="",
            reward="one_random_industrial_complex = yes",
            modifiers=modifiers,
        ),
    )
    out = _guard_data(fpath, tmp_path)
    assert "can_staff_an_industrial_complex" in out[0]["guards"]


# --------------------------------------------------------------------------
# money-cost worker facts
# --------------------------------------------------------------------------


def test_worker_sums_negative_treasury_spend(tmp_path):
    reward = _spend(-7) + "\n			" + _spend(-3)
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    d = _guard_data(fpath, tmp_path)[0]
    assert d["spend"] == 10.0
    assert d["has_cost"] is True
    assert d["unknown"] is False


def test_worker_ignores_positive_treasury_income(tmp_path):
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=_spend(50), modifiers=""),
    )
    d = _guard_data(fpath, tmp_path)[0]
    assert d["spend"] == 0.0
    assert d["has_cost"] is False


def test_worker_computed_treasury_change_is_unknown(tmp_path):
    reward = (
        "set_temp_variable = { treasury_change = { value = 5 multiply = -1 } }\n"
        "			modify_treasury_effect = yes"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    d = _guard_data(fpath, tmp_path)[0]
    assert d["spend"] == 0.0
    assert d["has_cost"] is True
    assert d["unknown"] is True


def test_worker_gdp_multiply_idiom_is_unknown(tmp_path):
    """The `set gdp_total, multiply by -N%` idiom (issue: the multiply's own
    literal used to be misread as a fresh treasury_change set)."""
    reward = (
        "set_temp_variable = { treasury_change = gdp_total }\n"
        "			multiply_temp_variable = { treasury_change = -0.05 }\n"
        "			modify_treasury_effect = yes"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    d = _guard_data(fpath, tmp_path)[0]
    assert d["has_cost"] is True
    assert d["unknown"] is True


def test_worker_bare_identifier_set_is_unknown(tmp_path):
    reward = (
        "set_temp_variable = { treasury_change = needed_money }\n"
        "			modify_treasury_effect = yes"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    d = _guard_data(fpath, tmp_path)[0]
    assert d["has_cost"] is True
    assert d["unknown"] is True


def test_worker_ignores_spend_inside_effect_tooltip(tmp_path):
    reward = "effect_tooltip = {\n			" + _spend(-20) + "\n			}"
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    d = _guard_data(fpath, tmp_path)[0]
    assert d["spend"] == 0.0
    assert d["has_cost"] is False


def test_worker_detects_money_scripted_effect(tmp_path):
    d_effects = frozenset({"spend_money_effect"})
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2, extra="", reward="spend_money_effect = yes", modifiers=""
        ),
    )
    d = _guard_data(fpath, tmp_path, money=d_effects)[0]
    assert d["has_cost"] is True
    assert d["unknown"] is True


def test_worker_detects_treasury_effect_corruption_variant(tmp_path):
    reward = (
        "set_temp_variable = { treasury_change = -7 }\n"
        "			modify_treasury_effect_corruption = yes"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    d = _guard_data(fpath, tmp_path)[0]
    assert d["has_cost"] is True
    assert d["unknown"] is True


def test_worker_takes_max_spend_across_if_else(tmp_path):
    reward = (
        "if = {\n"
        "				limit = { original_tag = SAU }\n"
        "				set_temp_variable = { treasury_change = -14 }\n"
        "			}\n"
        "			else = { set_temp_variable = { treasury_change = -3.5 } }\n"
        "			modify_treasury_effect = yes"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    d = _guard_data(fpath, tmp_path)[0]
    assert d["spend"] == 14.0
    assert d["has_cost"] is True


def test_worker_apply_twice_reuses_treasury_change(tmp_path):
    reward = (
        "set_temp_variable = { treasury_change = -3 }\n"
        "			modify_treasury_effect = yes\n"
        "			modify_treasury_effect = yes"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    d = _guard_data(fpath, tmp_path)[0]
    assert d["spend"] == 6.0


# --------------------------------------------------------------------------
# can_staff reporting
# --------------------------------------------------------------------------


def test_validator_warns_on_unguarded_building_focus(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="",
            reward="one_random_industrial_complex = yes",
            modifiers="",
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_clean_on_guarded_building_focus(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="",
            reward="one_random_industrial_complex = yes",
            modifiers=GUARD_FLAT_FORM,
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 0
    assert v.errors_found == 0


def test_validator_ignores_non_building_non_money_effects(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2, extra="", reward="grant_pp_effect = yes", modifiers=""
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 0


def test_chained_builder_effect_detected(tmp_path):
    _write_effects_file(
        tmp_path,
        extra="""factory_with_energy_check = {
	if = {
		limit = { check_variable = { energy_deficit < 1 } }
		one_random_industrial_complex = yes
	}
}
deep_factory_with_energy_check = {
	factory_with_energy_check = yes
}
""",
    )
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="",
            reward="deep_factory_with_energy_check = yes",
            modifiers="",
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


# --------------------------------------------------------------------------
# bankruptcy reporting (money-based)
# --------------------------------------------------------------------------


def test_validator_warns_on_high_spend_without_bankruptcy_guard(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=_spend(-7), modifiers=""),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_clean_on_high_spend_with_bankruptcy_guard(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2, extra="", reward=_spend(-7), modifiers=BANKRUPTCY_GUARD
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 0


def test_validator_spend_below_threshold_not_flagged(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=_spend(-3), modifiers=""),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 0


def test_validator_spend_at_threshold_flagged(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=_spend(-5), modifiers=""),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_income_not_flagged(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=_spend(50), modifiers=""),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 0


def test_validator_gdp_multiply_focus_flagged_as_scripted(tmp_path):
    """A GDP-multiply spend with no guard has no summable spend, so it must
    surface in the scripted/unknown (verify) category, not go unflagged."""
    _write_effects_file(tmp_path)
    reward = (
        "set_temp_variable = { treasury_change = gdp_total }\n"
        "			multiply_temp_variable = { treasury_change = -0.05 }\n"
        "			modify_treasury_effect = yes"
    )
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found >= 1
    issues = [i for i in v._issues if i.category == "missing-bankruptcy-guard-scripted"]
    assert len(issues) == 1


def test_validator_unneeded_bankruptcy_guard_flagged(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="",
            reward="add_political_power = 50",
            modifiers=BANKRUPTCY_GUARD,
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_scripted_spend_without_guard_flagged(tmp_path):
    _write_effects_file(
        tmp_path,
        extra="""spend_money_effect = {
	set_temp_variable = { treasury_change = -10 }
	modify_treasury_effect = yes
}
""",
    )
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2, extra="", reward="spend_money_effect = yes", modifiers=""
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_bankruptcy_warnings_aggregate_per_file(tmp_path):
    _write_effects_file(tmp_path)
    content = (
        """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 0
		cost = 2
		completion_reward = { """
        + _spend(-7)
        + """ }
		ai_will_do = { base = 1 }
	}
	focus = {
		id = TAG_focus_b
		x = 2
		y = 0
		cost = 2
		completion_reward = { """
        + _spend(-7)
        + """ }
		ai_will_do = { base = 1 }
	}
}
"""
    )
    _write_focus_file(tmp_path, content)
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


# --------------------------------------------------------------------------
# search-filter mismatch reporting
# --------------------------------------------------------------------------


def test_validator_flags_money_focus_without_economic_filter(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="search_filters = { FOCUS_FILTER_POLITICAL }",
            reward=_spend(-7),
            modifiers=BANKRUPTCY_GUARD,
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_clean_when_money_focus_tagged_economic(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2,
            extra="search_filters = { FOCUS_FILTER_ECONOMY }",
            reward=_spend(-7),
            modifiers=BANKRUPTCY_GUARD,
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 0
