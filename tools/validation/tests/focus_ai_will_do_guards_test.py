"""Tests for the ai_will_do staffing/bankruptcy guard checks in
validate_focus_tree (issue #2233 + the AGENTS.md bankruptcy convention).

A focus whose completion_reward builds a staffable building needs a
factor = 0 ai_will_do modifier checking the matching can_staff_an_* trigger;
high-cost focuses need the bankruptcy_incoming_collapse mission guard.
"""

from validate_focus_tree import Validator, _extract_ai_guard_data


def _write_focus_file(tmp_path, content):
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True, exist_ok=True)
    fpath = nf_dir / "test.txt"
    fpath.write_text(content, encoding="utf-8")
    return fpath


def _write_effects_file(tmp_path):
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
""",
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

STAFFABLE_MAP = {"one_random_industrial_complex": frozenset({"industrial_complex"})}


def _run_check(tmp_path):
    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.validate_ai_will_do_guards()
    return v


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
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
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
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
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
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
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
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
    assert out[0]["buildings"] == set()


def test_worker_ignores_builder_effect_inside_effect_tooltip(tmp_path):
    """Same rule for a scripted builder effect named inside the preview."""
    reward = (
        "effect_tooltip = {\n"
        "				one_random_industrial_complex = yes\n"
        "			}"
    )
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(cost=2, extra="", reward=reward, modifiers=""),
    )
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
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
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
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
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
    assert out[0]["guards"] == set()


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


def test_validator_ignores_non_building_effects(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=2, extra="", reward="grant_pp_effect = yes", modifiers=""
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 0


def test_validator_warns_on_high_cost_without_bankruptcy_guard(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=10, extra="", reward="add_political_power = 50", modifiers=""
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_clean_on_high_cost_with_bankruptcy_guard(tmp_path):
    _write_effects_file(tmp_path)
    modifiers = """modifier = {
				factor = 0
				has_active_mission = bankruptcy_incoming_collapse
			}"""
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=10, extra="", reward="add_political_power = 50", modifiers=modifiers
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 0


def test_validator_uses_lower_threshold_for_econ_filters(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=5,
            extra="search_filters = { FOCUS_FILTER_ECONOMY FOCUS_FILTER_TEST }",
            reward="add_political_power = 50",
            modifiers="",
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_validator_keeps_default_threshold_without_econ_filters(tmp_path):
    _write_effects_file(tmp_path)
    _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost=5,
            extra="search_filters = { FOCUS_FILTER_POLITICAL }",
            reward="add_political_power = 50",
            modifiers="",
        ),
    )
    v = _run_check(tmp_path)
    assert v.warnings_found == 0


def test_bankruptcy_warnings_aggregate_per_file(tmp_path):
    _write_effects_file(tmp_path)
    content = """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 0
		cost = 10
		completion_reward = { add_political_power = 50 }
		ai_will_do = { base = 1 }
	}
	focus = {
		id = TAG_focus_b
		x = 2
		y = 0
		cost = 10
		completion_reward = { add_political_power = 50 }
		ai_will_do = { base = 1 }
	}
}
"""
    _write_focus_file(tmp_path, content)
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_worker_resolves_at_constant_cost(tmp_path):
    content = "@tier_high = 20\n" + FOCUS_TEMPLATE.format(
        cost="@tier_high",
        extra="",
        reward="add_political_power = 50",
        modifiers="",
    )
    fpath = _write_focus_file(tmp_path, content)
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
    assert out[0]["cost"] == 20.0


def test_worker_unresolvable_constant_cost_is_none(tmp_path):
    fpath = _write_focus_file(
        tmp_path,
        FOCUS_TEMPLATE.format(
            cost="@undefined_tier",
            extra="",
            reward="add_political_power = 50",
            modifiers="",
        ),
    )
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
    assert out[0]["cost"] is None


def test_worker_ignores_nested_cost_keys(tmp_path):
    content = """focus_tree = {
	id = test_tree
	focus = {
		id = TAG_focus_a
		x = 0
		y = 0
		completion_reward = {
			add_advisor_slot = { cost = 100 }
		}
		ai_will_do = { base = 1 }
	}
}
"""
    fpath = _write_focus_file(tmp_path, content)
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
    assert out[0]["cost"] is None


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
    out = _extract_ai_guard_data((str(fpath), str(tmp_path), STAFFABLE_MAP))
    assert "can_staff_an_industrial_complex" in out[0]["guards"]


def test_at_constant_cost_triggers_bankruptcy_check(tmp_path):
    _write_effects_file(tmp_path)
    content = "@tier_high = 20\n" + FOCUS_TEMPLATE.format(
        cost="@tier_high",
        extra="",
        reward="add_political_power = 50",
        modifiers="",
    )
    _write_focus_file(tmp_path, content)
    v = _run_check(tmp_path)
    assert v.warnings_found == 1


def test_chained_builder_effect_detected(tmp_path):
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
factory_with_energy_check = {
	if = {
		limit = { check_variable = { energy_deficit < 1 } }
		one_random_industrial_complex = yes
	}
}
deep_factory_with_energy_check = {
	factory_with_energy_check = yes
}
""",
        encoding="utf-8",
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
