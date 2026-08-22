from pathlib import Path

from validate_corporate_history_contract import ChainConfig, Validator

ON_ACTION_PATH = "common/on_actions/01_oem_corporate_history_on_actions.txt"
EFFECT_PATH = "common/scripted_effects/00_corporate_history_effects.txt"
GPU_EFFECT_PATH = "common/scripted_effects/00_gpu_development_effects.txt"
IBM_EFFECT_PATH = "common/scripted_effects/USA_ibm_effects.txt"
E3_EFFECT_PATH = "common/scripted_effects/USA_e3_effects.txt"
EVENT_PATH = "events/USA_oem_startup_test_events.txt"
YEARLY_PATH = "common/scripted_effects/00_yearly_effects.txt"


def _write(root: Path, relative: str, text: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build_fixture(root: Path):
    _write(
        root,
        ON_ACTION_PATH,
        """on_actions = {
	on_startup = {
		effect = {
			ABK = { OEM_corporate_history_startup_bootstrap = yes }
		}
	}
}
""",
    )
    _write(
        root,
        EFFECT_PATH,
        """OEM_corporate_history_startup_bootstrap = {
	if = {
		limit = {
			NOT = { has_global_flag = GLOBAL_oem_corporate_history_startup_dispatched }
		}
		set_global_flag = GLOBAL_oem_corporate_history_startup_dispatched
		corporate_history_on_startup = yes
		if = {
			limit = { country_exists = USA }
			USA = {
				gpu_development_reconstruct_history = yes
				gpu_development_schedule_current_year_events = yes
				if = {
					limit = {
						date < 2001.1.1
						corporate_history_full_enabled = yes
					}
					country_event = { id = USA_oem_events.13 days = 90 }
				}
			}
		}
	}
}

corporate_history_on_startup = {
	if = {
		limit = { corporate_history_full_enabled = yes }
		if = {
			limit = { country_exists = USA }
			USA = {
				country_event = { id = USA_e3_events.90 days = 1 }
				country_event = { id = USA_ibm_events.90 days = 1 }
			}
		}
		if = {
			limit = {
				country_exists = USA
				NOT = { has_start_date < 2000.1.1 }
				has_start_date < 2000.1.2
			}
			USA = { country_event = { id = USA_hp_events.1 days = 153 } }
		}
	}
	else_if = {
		limit = { corporate_history_outcomes_only_enabled = yes }
		if = {
			limit = { country_exists = USA }
			USA = { USA_oem_reconstruct_history = yes }
		}
	}
}
""",
    )
    _write(
        root,
        GPU_EFFECT_PATH,
        """gpu_development_schedule_current_year_events = {
	if = {
		limit = { NOT = { has_country_flag = gpu_development_start_year_events_scheduled } }
		if = {
			limit = {
				NOT = { has_country_flag = collapsed_nation }
				OR = {
					original_tag = USA
					original_tag = CAN
					original_tag = TAI
				}
				NOT = { has_start_date < 2000.1.1 }
				has_start_date < 2000.1.2
				NOT = { has_country_flag = gpu_development_1_resolved }
			}
			country_event = { id = gpu_development.1 days = 110 }
		}
	}
	set_country_flag = gpu_development_start_year_events_scheduled
}
""",
    )
    _write(
        root,
        IBM_EFFECT_PATH,
        """USA_ibm_schedule_prehistory = {
	if = {
		limit = {
			NOT = { has_country_flag = USA_ibm_event_12_scheduled }
			NOT = { has_country_flag = USA_ibm_event_12_resolved }
		}
		set_country_flag = USA_ibm_event_12_scheduled
		country_event = { id = USA_ibm_events.12 days = 30 }
	}
	if = {
		limit = {
			NOT = { has_country_flag = USA_ibm_event_13_scheduled }
			NOT = { has_country_flag = USA_ibm_event_13_resolved }
		}
		set_country_flag = USA_ibm_event_13_scheduled
		country_event = { id = USA_ibm_events.13 days = 120 }
	}
}
""",
    )
    _write(
        root,
        E3_EFFECT_PATH,
        """USA_e3_schedule_current_year_events = {
	if = {
		limit = { NOT = { has_country_flag = USA_e3_start_year_events_scheduled } }
		if = {
			limit = {
				NOT = { has_start_date < 2000.1.1 }
				has_start_date < 2000.1.2
				NOT = { has_country_flag = USA_e3_opening_context_seen }
			}
			country_event = { id = USA_e3_events.1 days = 131 }
		}
	}
	set_country_flag = USA_e3_start_year_events_scheduled
}
""",
    )
    _write(
        root,
        EVENT_PATH,
        """country_event = {
	id = USA_oem_events.13
	is_triggered_only = yes
	trigger = {
		original_tag = USA
		NOT = { has_country_flag = collapsed_nation }
	}
}

country_event = {
	id = gpu_development.1
	is_triggered_only = yes
	trigger = {
		OR = {
			original_tag = USA
			original_tag = CAN
			original_tag = TAI
		}
		NOT = { has_country_flag = collapsed_nation }
		NOT = { has_country_flag = gpu_development_1_resolved }
	}
}

country_event = {
	id = USA_ibm_events.12
	is_triggered_only = yes
	trigger = {
		original_tag = USA
		NOT = { has_country_flag = collapsed_nation }
		has_country_flag = USA_ibm_event_12_scheduled
		NOT = { has_country_flag = USA_ibm_event_12_resolved }
	}
	immediate = { set_country_flag = USA_ibm_event_12_resolved }
}

country_event = {
	id = USA_ibm_events.13
	is_triggered_only = yes
	trigger = {
		original_tag = USA
		NOT = { has_country_flag = collapsed_nation }
		has_country_flag = USA_ibm_event_13_scheduled
		NOT = { has_country_flag = USA_ibm_event_13_resolved }
	}
	immediate = { set_country_flag = USA_ibm_event_13_resolved }
}

country_event = {
	id = USA_ibm_events.90
	is_triggered_only = yes
	hidden = yes
	trigger = {
		original_tag = USA
		NOT = { has_country_flag = collapsed_nation }
	}
	immediate = {
		if = {
			limit = { date < 2000.2.1 }
			USA_ibm_initialize_state = yes
			USA_ibm_schedule_prehistory = yes
		}
		else = { USA_ibm_reconstruct_history = yes }
	}
}

country_event = {
	id = USA_e3_events.1
	is_triggered_only = yes
	trigger = {
		original_tag = USA
		NOT = { has_country_flag = collapsed_nation }
		NOT = { has_country_flag = USA_e3_opening_context_seen }
	}
}

country_event = {
	id = USA_e3_events.90
	is_triggered_only = yes
	hidden = yes
	trigger = {
		original_tag = USA
		NOT = { has_country_flag = collapsed_nation }
	}
	immediate = {
		USA_e3_reconstruct_history = yes
		USA_e3_schedule_current_year_events = yes
	}
}

country_event = {
	id = USA_hp_events.1
	is_triggered_only = yes
	trigger = {
		original_tag = USA
		NOT = { has_country_flag = collapsed_nation }
	}
}
""",
    )
    _write(root, YEARLY_PATH, "trigger_year_2000_events = { }\n")


def _replace(root: Path, relative: str, old: str, new: str):
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _findings(root: Path):
    validator = Validator(str(root), no_color=True)
    effects = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    events = validator._load_events()
    call_sites = validator._load_event_call_sites(events, effects, set())
    return validator._validate_oem_startup_architecture(effects, events, call_sites)


def _messages(root: Path):
    return [message for message, _file, _line in _findings(root)]


def test_valid_oem_startup_models_the_usa_2000_schedule(tmp_path):
    _build_fixture(tmp_path)
    assert _findings(tmp_path) == []


def test_deleted_bootstrap_call_fails_with_schedulers_intact(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
        "\t\t\tABK = { }\n",
    )
    messages = _messages(tmp_path)
    assert any("requires exactly one caller" in message for message in messages)
    assert any("ABK scoped bootstrap call" in message for message in messages)


def test_root_none_tag_guard_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
        "\t\t\tif = {\n"
        "\t\t\t\tlimit = { tag = ABK }\n"
        "\t\t\t\tOEM_corporate_history_startup_bootstrap = yes\n"
        "\t\t\t}\n",
    )
    messages = _messages(tmp_path)
    assert any("ROOT=None" in message for message in messages)
    assert any("ABK scoped bootstrap call" in message for message in messages)


def test_bootstrap_requires_global_idempotence_guard(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\tNOT = { has_global_flag = GLOBAL_oem_corporate_history_startup_dispatched }\n",
        "\t\t\talways = yes\n",
    )
    assert any(
        "direct NOT has_global_flag guard" in message for message in _messages(tmp_path)
    )


def test_bootstrap_sets_marker_before_dispatch(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n"
        "\t\tcorporate_history_on_startup = yes\n",
        "\t\tcorporate_history_on_startup = yes\n"
        "\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n",
    )
    assert any(
        "before dispatching startup work" in message for message in _messages(tmp_path)
    )


def test_bootstrap_marker_is_first_direct_effect_statement(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n",
        "\t\tOEM_unexpected_startup_work = yes\n"
        "\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n",
    )
    assert any(
        "first direct effect statement" in message for message in _messages(tmp_path)
    )


def test_bootstrap_marker_precedes_nested_dispatch(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n",
        "\t\tif = {\n"
        "\t\t\tlimit = { always = yes }\n"
        "\t\t\tOEM_unexpected_startup_work = yes\n"
        "\t\t}\n"
        "\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n",
    )
    effect_path = tmp_path / EFFECT_PATH
    effect_path.write_text(
        effect_path.read_text(encoding="utf-8")
        + '\nOEM_unexpected_startup_work = { log = "premarker" }\n',
        encoding="utf-8",
    )
    assert any(
        "before dispatching startup work" in message for message in _messages(tmp_path)
    )


def test_bootstrap_cannot_dispatch_outside_idempotence_guard(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t}\n}\n\ncorporate_history_on_startup = {\n",
        "\t}\n"
        "\tCAN = { gpu_development_schedule_current_year_events = yes }\n"
        "}\n\n"
        "corporate_history_on_startup = {\n",
    )
    assert any(
        "sole direct NOT has_global_flag guard" in message
        for message in _messages(tmp_path)
    )


def test_changed_offset_breaks_machine_checked_schedule(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        GPU_EFFECT_PATH,
        "gpu_development.1 days = 110",
        "gpu_development.1 days = 111",
    )
    messages = _messages(tmp_path)
    assert any("gpu_development.1 at days = 110" in message for message in messages)
    assert any("expected 2000-04-20" in message for message in messages)


def test_duplicate_independent_event_caller_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _write(
        tmp_path,
        YEARLY_PATH,
        "trigger_year_2000_events = {\n"
        "\tcountry_event = { id = USA_oem_events.13 days = 90 }\n"
        "}\n",
    )
    messages = _messages(tmp_path)
    assert any(
        "USA_oem_events.13 requires sole caller" in message for message in messages
    )
    assert any(
        "outside upstream-owned 00_yearly_effects.txt" in message
        for message in messages
    )


def test_gpu_startup_cannot_inherit_full_mode_gate(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\t\tgpu_development_schedule_current_year_events = yes\n",
        "\t\t\t\tif = {\n"
        "\t\t\t\t\tlimit = { corporate_history_full_enabled = yes }\n"
        "\t\t\t\t\tgpu_development_schedule_current_year_events = yes\n"
        "\t\t\t\t}\n",
    )
    assert any("incorrectly gated" in message for message in _messages(tmp_path))


def test_outcomes_only_cannot_schedule_full_popup(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\tUSA = { USA_oem_reconstruct_history = yes }\n",
        "\t\t\tUSA = {\n"
        "\t\t\t\tUSA_oem_reconstruct_history = yes\n"
        "\t\t\t\tcountry_event = { id = USA_hp_events.1 days = 153 }\n"
        "\t\t\t}\n",
    )
    assert any("Outcomes Only schedules" in message for message in _messages(tmp_path))


def test_outcomes_only_cannot_reach_full_scheduler_through_wrapper(tmp_path):
    _build_fixture(tmp_path)
    effect_path = tmp_path / EFFECT_PATH
    effect_path.write_text(
        effect_path.read_text(encoding="utf-8")
        + "\nUSA_e3_outcomes_popup_wrapper = { USA_e3_schedule_current_year_events = yes }\n",
        encoding="utf-8",
    )
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\tUSA = { USA_oem_reconstruct_history = yes }\n",
        "\t\t\tUSA = {\n"
        "\t\t\t\tUSA_oem_reconstruct_history = yes\n"
        "\t\t\t\tUSA_e3_outcomes_popup_wrapper = yes\n"
        "\t\t\t}\n",
    )
    assert any("Outcomes Only schedules" in message for message in _messages(tmp_path))


def test_outcomes_only_cannot_reach_full_scheduler_through_hidden_event(tmp_path):
    _build_fixture(tmp_path)
    effect_path = tmp_path / EFFECT_PATH
    effect_path.write_text(
        effect_path.read_text(encoding="utf-8")
        + "\nUSA_e3_outcomes_bridge_wrapper = { country_event = USA_e3_outcomes_bridge.1 }\n",
        encoding="utf-8",
    )
    event_path = tmp_path / EVENT_PATH
    event_path.write_text(
        event_path.read_text(encoding="utf-8") + "\ncountry_event = {\n"
        "\tid = USA_e3_outcomes_bridge.1\n"
        "\tis_triggered_only = yes\n"
        "\thidden = yes\n"
        "\timmediate = { USA_e3_schedule_current_year_events = yes }\n"
        "}\n",
        encoding="utf-8",
    )
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\tUSA = { USA_oem_reconstruct_history = yes }\n",
        "\t\t\tUSA = {\n"
        "\t\t\t\tUSA_oem_reconstruct_history = yes\n"
        "\t\t\t\tUSA_e3_outcomes_bridge_wrapper = yes\n"
        "\t\t\t}\n",
    )
    assert any("Outcomes Only schedules" in message for message in _messages(tmp_path))


def test_off_mode_cannot_gain_startup_else_branch(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / EFFECT_PATH
    text = path.read_text(encoding="utf-8")
    marker = (
        "\telse_if = {\n\t\tlimit = { corporate_history_outcomes_only_enabled = yes }"
    )
    start = text.index(marker)
    closing = text.index("\n\t}\n}\n", start)
    text = (
        text[: closing + 4]
        + "\telse = { USA_oem_reconstruct_history = yes }\n"
        + text[closing + 4 :]
    )
    path.write_text(text, encoding="utf-8")
    assert any(
        "Off must leave startup inert" in message for message in _messages(tmp_path)
    )


def test_upstream_yearly_file_cannot_own_startup(tmp_path):
    _build_fixture(tmp_path)
    _write(
        tmp_path,
        YEARLY_PATH,
        "trigger_year_2000_events = { corporate_history_on_startup = yes }\n",
    )
    assert any(
        "corporate_history_on_startup must remain outside upstream-owned" in message
        for message in _messages(tmp_path)
    )


def test_direct_on_action_corporate_dispatch_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n"
        "\t\t\tcorporate_history_on_startup = yes\n",
    )
    assert any(
        "must not be called directly from on_actions" in message
        for message in _messages(tmp_path)
    )


def test_bootstrap_call_must_be_direct_in_abk_scope(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
        "\t\t\tABK = {\n"
        "\t\t\t\tif = {\n"
        "\t\t\t\t\tlimit = { always = no }\n"
        "\t\t\t\t\tOEM_corporate_history_startup_bootstrap = yes\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n",
    )
    assert any(
        "ABK scoped bootstrap call" in message for message in _messages(tmp_path)
    )


def test_bootstrap_guard_cannot_be_replayable_or(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\tNOT = { has_global_flag = GLOBAL_oem_corporate_history_startup_dispatched }\n",
        "\t\t\tOR = {\n"
        "\t\t\t\tNOT = { has_global_flag = GLOBAL_oem_corporate_history_startup_dispatched }\n"
        "\t\t\t\talways = yes\n"
        "\t\t\t}\n",
    )
    assert any(
        "direct NOT has_global_flag guard" in message for message in _messages(tmp_path)
    )


def test_bootstrap_marker_set_must_be_direct(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n",
        "\t\tif = {\n"
        "\t\t\tlimit = { always = no }\n"
        "\t\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n"
        "\t\t}\n",
    )
    assert any("must set" in message for message in _messages(tmp_path))


def test_corporate_dispatch_must_be_direct_in_bootstrap(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\tcorporate_history_on_startup = yes\n",
        "\t\tif = {\n"
        "\t\t\tlimit = { always = no }\n"
        "\t\t\tcorporate_history_on_startup = yes\n"
        "\t\t}\n",
    )
    assert any(
        "must be called directly from the guarded" in message
        for message in _messages(tmp_path)
    )


def test_startup_marker_has_one_owner_and_no_clear_path(tmp_path):
    _build_fixture(tmp_path)
    _write(
        tmp_path,
        YEARLY_PATH,
        "trigger_year_2000_events = {\n"
        "\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n"
        "\tclr_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n"
        "}\n",
    )
    messages = _messages(tmp_path)
    assert any("must be set only by" in message for message in messages)
    assert any("must never be cleared" in message for message in messages)


def test_bootstrap_usa_scope_cannot_inherit_parent_full_gate(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\tlimit = { country_exists = USA }\n\t\t\tUSA = {\n"
        "\t\t\t\tgpu_development_reconstruct_history = yes\n",
        "\t\t\tlimit = {\n"
        "\t\t\t\tcountry_exists = USA\n"
        "\t\t\t\tcorporate_history_full_enabled = yes\n"
        "\t\t\t}\n"
        "\t\t\tUSA = {\n"
        "\t\t\t\tgpu_development_reconstruct_history = yes\n",
    )
    assert any(
        "unconditionally country_exists = USA" in message
        for message in _messages(tmp_path)
    )


def test_off_mode_cannot_gain_direct_startup_effect(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "corporate_history_on_startup = {\n\tif = {\n",
        "corporate_history_on_startup = {\n"
        "\tUSA_oem_reconstruct_history = yes\n"
        "\tif = {\n",
    )
    assert any(
        "only its direct Full and Outcomes Only branches" in message
        for message in _messages(tmp_path)
    )


def test_full_mode_anchors_must_be_inside_usa_scope(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\tUSA = {\n"
        "\t\t\t\tcountry_event = { id = USA_e3_events.90 days = 1 }\n",
        "\t\t\tCHI = {\n"
        "\t\t\t\tcountry_event = { id = USA_e3_events.90 days = 1 }\n",
    )
    messages = _messages(tmp_path)
    assert any("USA_e3_events.90 at days = 1" in message for message in messages)
    assert any("USA_ibm_events.90 at days = 1" in message for message in messages)


def test_gpu_scheduler_must_permit_usa(tmp_path):
    _build_fixture(tmp_path)
    _replace(tmp_path, GPU_EFFECT_PATH, "original_tag = USA", "original_tag = FRA")
    assert any(
        "permits USA and excludes collapsed nations" in message
        for message in _messages(tmp_path)
    )


def test_ibm_scheduler_must_set_flag_before_queue(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        IBM_EFFECT_PATH,
        "\t\tset_country_flag = USA_ibm_event_12_scheduled\n",
        "",
    )
    assert any(
        "USA_ibm_event_12_scheduled directly before queueing" in message
        for message in _messages(tmp_path)
    )


def test_ibm_event_must_consume_scheduled_flag(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EVENT_PATH,
        "\t\thas_country_flag = USA_ibm_event_13_scheduled\n",
        "",
    )
    assert any(
        "must consume USA_ibm_event_13_scheduled" in message
        for message in _messages(tmp_path)
    )


def test_full_mode_arm_cannot_be_made_unconditional(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\tlimit = { corporate_history_full_enabled = yes }\n",
        "\t\tlimit = {\n"
        "\t\t\tOR = {\n"
        "\t\t\t\tcorporate_history_full_enabled = yes\n"
        "\t\t\t\talways = yes\n"
        "\t\t\t}\n"
        "\t\t}\n",
    )
    assert any(
        "missing its Full-mode branch" in message for message in _messages(tmp_path)
    )


def test_outcomes_arm_cannot_be_made_unconditional(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\tlimit = { corporate_history_outcomes_only_enabled = yes }\n",
        "\t\tlimit = {\n"
        "\t\t\tOR = {\n"
        "\t\t\t\tcorporate_history_outcomes_only_enabled = yes\n"
        "\t\t\t\talways = yes\n"
        "\t\t\t}\n"
        "\t\t}\n",
    )
    assert any(
        "missing its Outcomes Only branch" in message for message in _messages(tmp_path)
    )


def test_anchor_country_branch_cannot_be_disabled(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\tlimit = { country_exists = USA }\n"
        "\t\t\tUSA = {\n"
        "\t\t\t\tcountry_event = { id = USA_e3_events.90 days = 1 }\n",
        "\t\t\tlimit = {\n"
        "\t\t\t\tcountry_exists = USA\n"
        "\t\t\t\talways = no\n"
        "\t\t\t}\n"
        "\t\t\tUSA = {\n"
        "\t\t\t\tcountry_event = { id = USA_e3_events.90 days = 1 }\n",
    )
    assert any("with no additional gate" in message for message in _messages(tmp_path))


def test_hp_startup_branch_cannot_be_disabled(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\t\thas_start_date < 2000.1.2\n"
        "\t\t\t}\n"
        "\t\t\tUSA = { country_event = { id = USA_hp_events.1 days = 153 } }\n",
        "\t\t\t\thas_start_date < 2000.1.2\n"
        "\t\t\t\talways = no\n"
        "\t\t\t}\n"
        "\t\t\tUSA = { country_event = { id = USA_hp_events.1 days = 153 } }\n",
    )
    assert any("exact 2000.1.1 bookmark" in message for message in _messages(tmp_path))


def test_dell_full_gate_cannot_be_made_unconditional(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\t\t\tcorporate_history_full_enabled = yes\n",
        "\t\t\t\t\tOR = {\n"
        "\t\t\t\t\t\tcorporate_history_full_enabled = yes\n"
        "\t\t\t\t\t\talways = yes\n"
        "\t\t\t\t\t}\n",
    )
    assert any(
        "USA_oem_events.13 is not reachable" in message
        for message in _messages(tmp_path)
    )


def test_negated_usa_event_owner_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EVENT_PATH,
        "\t\toriginal_tag = USA\n",
        "\t\tNOT = { original_tag = USA }\n",
    )
    assert any(
        "USA_oem_events.13 must retain its exact viable" in message
        for message in _messages(tmp_path)
    )


def test_permanently_false_event_trigger_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EVENT_PATH,
        "\t\toriginal_tag = USA\n\t\tNOT = { has_country_flag = collapsed_nation }\n",
        "\t\toriginal_tag = USA\n"
        "\t\tNOT = { has_country_flag = collapsed_nation }\n"
        "\t\talways = no\n",
    )
    assert any(
        "USA_oem_events.13 must retain its exact viable" in message
        for message in _messages(tmp_path)
    )


def test_ibm_set_before_queue_cannot_be_spoofed_by_nested_set(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        IBM_EFFECT_PATH,
        "\t\tset_country_flag = USA_ibm_event_12_scheduled\n"
        "\t\tcountry_event = { id = USA_ibm_events.12 days = 30 }\n",
        "\t\tif = {\n"
        "\t\t\tlimit = { always = no }\n"
        "\t\t\tset_country_flag = USA_ibm_event_12_scheduled\n"
        "\t\t}\n"
        "\t\tcountry_event = { id = USA_ibm_events.12 days = 30 }\n"
        "\t\tset_country_flag = USA_ibm_event_12_scheduled\n",
    )
    assert any(
        "USA_ibm_event_12_scheduled directly before queueing" in message
        for message in _messages(tmp_path)
    )


def test_gpu_scheduler_requires_outer_replay_guard(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        GPU_EFFECT_PATH,
        "\t\tlimit = { NOT = { has_country_flag = gpu_development_start_year_events_scheduled } }\n",
        "\t\tlimit = { always = yes }\n",
    )
    assert any(
        "must guard all start-year queues" in message for message in _messages(tmp_path)
    )


def test_e3_anchor_scheduler_call_is_exactly_once(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EVENT_PATH,
        "\t\tUSA_e3_schedule_current_year_events = yes\n",
        "\t\tUSA_e3_schedule_current_year_events = yes\n"
        "\t\tUSA_e3_schedule_current_year_events = yes\n",
    )
    assert any(
        "does not reconstruct E3 and call its current-year scheduler" in message
        for message in _messages(tmp_path)
    )


def test_scripted_gui_duplicate_event_caller_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _write(
        tmp_path,
        "common/scripted_guis/oem_duplicate.txt",
        "oem_duplicate = { effect = { country_event = { id = USA_oem_events.13 days = 90 } } }\n",
    )
    assert any(
        "USA_oem_events.13 requires sole caller" in message
        for message in _messages(tmp_path)
    )


def test_indirect_daily_bootstrap_caller_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    effect_path = tmp_path / EFFECT_PATH
    effect_path.write_text(
        effect_path.read_text(encoding="utf-8")
        + "\nOEM_replay_wrapper = { OEM_corporate_history_startup_bootstrap = yes }\n",
        encoding="utf-8",
    )
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t}\n}\n",
        "\t}\n"
        "\ton_daily = { effect = { ABK = { OEM_replay_wrapper = yes } } }\n"
        "}\n",
    )
    assert any(
        "requires exactly one caller" in message for message in _messages(tmp_path)
    )


def test_hidden_event_cannot_call_bootstrap_directly(tmp_path):
    _build_fixture(tmp_path)
    event_path = tmp_path / EVENT_PATH
    event_path.write_text(
        event_path.read_text(encoding="utf-8") + "\ncountry_event = {\n"
        "\tid = OEM_duplicate_startup.1\n"
        "\tis_triggered_only = yes\n"
        "\thidden = yes\n"
        "\timmediate = { OEM_corporate_history_startup_bootstrap = yes }\n"
        "}\n",
        encoding="utf-8",
    )
    assert any(
        "requires exactly one direct repository caller" in message
        for message in _messages(tmp_path)
    )


def test_hidden_event_cannot_call_corporate_startup_directly(tmp_path):
    _build_fixture(tmp_path)
    event_path = tmp_path / EVENT_PATH
    event_path.write_text(
        event_path.read_text(encoding="utf-8") + "\ncountry_event = {\n"
        "\tid = OEM_duplicate_startup.1\n"
        "\tis_triggered_only = yes\n"
        "\thidden = yes\n"
        "\timmediate = { corporate_history_on_startup = yes }\n"
        "}\n",
        encoding="utf-8",
    )
    assert any(
        "sole direct repository caller" in message for message in _messages(tmp_path)
    )


def test_broad_architecture_deletion_still_activates_validator(tmp_path):
    _build_fixture(tmp_path)
    (tmp_path / ON_ACTION_PATH).unlink()
    effect_path = tmp_path / EFFECT_PATH
    text = effect_path.read_text(encoding="utf-8")
    effect_path.write_text(
        text[text.index("corporate_history_on_startup = {") :], encoding="utf-8"
    )
    (tmp_path / EVENT_PATH).unlink()
    messages = _messages(tmp_path)
    assert any(
        "authoritative OEM startup on-action file is missing" in m for m in messages
    )
    assert any("requires exactly one definition" in m for m in messages)


def test_normal_validator_run_invokes_oem_startup_phase(tmp_path, monkeypatch):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
        "\t\t\tABK = { }\n",
    )
    validator = Validator(str(tmp_path), no_color=True)
    dummy = ChainConfig(
        name="fixture",
        tag="USA",
        namespace="USA_ibm_events",
        root="USA_ibm",
        tier=1,
        owned_prefixes=("USA_ibm",),
        variables={},
        outcome_idea_prefixes=(),
        requires_current_year_scheduler=False,
        allow_yearly_scheduler_duplicates=False,
        callerless_anchors=set(),
        allowed_multiple_callers=set(),
        allowed_reads=(),
        allowed_writes=(),
    )
    monkeypatch.setattr(validator, "_load_manifest", lambda: [dummy])
    for name in dir(validator):
        if (
            name.startswith("_validate_")
            and name != "_validate_oem_startup_architecture"
        ):
            monkeypatch.setattr(validator, name, lambda *args, **kwargs: [])
    reports = []
    monkeypatch.setattr(
        validator,
        "_report",
        lambda findings, _success, _failure, category: reports.append(
            (category, findings)
        ),
    )
    validator.run_validations()
    startup_reports = [
        findings
        for category, findings in reports
        if category == "OEM startup architecture"
    ]
    assert startup_reports
    assert any(
        "requires exactly one caller" in message
        for message, _file, _line in startup_reports[0]
    )


def test_same_line_transitive_bootstrap_caller_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    effect_path = tmp_path / EFFECT_PATH
    effect_path.write_text(
        effect_path.read_text(encoding="utf-8")
        + "\nOEM_replay_wrapper = { OEM_corporate_history_startup_bootstrap = yes }\n",
        encoding="utf-8",
    )
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes OEM_replay_wrapper = yes }\n",
    )
    assert any(
        "requires exactly one caller" in message for message in _messages(tmp_path)
    )


def test_bootstrap_caller_count_preserves_diamond_paths(tmp_path):
    _build_fixture(tmp_path)
    effect_path = tmp_path / EFFECT_PATH
    effect_path.write_text(
        effect_path.read_text(encoding="utf-8")
        + "\nOEM_path_a = { OEM_corporate_history_startup_bootstrap = yes }\n"
        + "OEM_path_b = { OEM_corporate_history_startup_bootstrap = yes }\n"
        + "OEM_path_diamond = { OEM_path_a = yes OEM_path_b = yes }\n",
        encoding="utf-8",
    )
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
        "\t\t\tABK = { OEM_path_diamond = yes }\n",
    )
    validator = Validator(str(tmp_path), no_color=True)
    assert (
        len(
            validator._script_effect_call_sites(
                "OEM_corporate_history_startup_bootstrap"
            )
        )
        == 2
    )


def test_bootstrap_caller_count_preserves_duplicate_wrapper_edges(tmp_path):
    _build_fixture(tmp_path)
    effect_path = tmp_path / EFFECT_PATH
    effect_path.write_text(
        effect_path.read_text(encoding="utf-8")
        + "\nOEM_duplicate_wrapper = { "
        + "OEM_corporate_history_startup_bootstrap = yes "
        + "OEM_corporate_history_startup_bootstrap = yes }\n",
        encoding="utf-8",
    )
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
        "\t\t\tABK = { OEM_duplicate_wrapper = yes }\n",
    )
    validator = Validator(str(tmp_path), no_color=True)
    assert (
        len(
            validator._script_effect_call_sites(
                "OEM_corporate_history_startup_bootstrap"
            )
        )
        == 2
    )


def test_scheduler_replay_marker_cannot_be_cleared(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        GPU_EFFECT_PATH,
        "\tset_country_flag = gpu_development_start_year_events_scheduled\n",
        "\tset_country_flag = gpu_development_start_year_events_scheduled\n"
        "\tclr_country_flag = gpu_development_start_year_events_scheduled\n",
    )
    assert any(
        "must guard all start-year queues" in message for message in _messages(tmp_path)
    )


def test_duplicate_event_trigger_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EVENT_PATH,
        "\t\tNOT = { has_country_flag = collapsed_nation }\n\t}\n}\n\ncountry_event = {\n\tid = gpu_development.1\n",
        "\t\tNOT = { has_country_flag = collapsed_nation }\n"
        "\t}\n"
        "\ttrigger = { always = no }\n"
        "}\n\n"
        "country_event = {\n"
        "\tid = gpu_development.1\n",
    )
    assert any(
        "USA_oem_events.13 must retain its exact viable" in message
        for message in _messages(tmp_path)
    )


def test_duplicate_bootstrap_limit_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        EFFECT_PATH,
        "\t\t\tNOT = { has_global_flag = GLOBAL_oem_corporate_history_startup_dispatched }\n"
        "\t\t}\n"
        "\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n",
        "\t\t\tNOT = { has_global_flag = GLOBAL_oem_corporate_history_startup_dispatched }\n"
        "\t\t}\n"
        "\t\tlimit = { always = no }\n"
        "\t\tset_global_flag = GLOBAL_oem_corporate_history_startup_dispatched\n",
    )
    assert any(
        "direct NOT has_global_flag guard" in message for message in _messages(tmp_path)
    )


def test_external_gpu_scheduler_marker_preset_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _replace(
        tmp_path,
        ON_ACTION_PATH,
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
        "\t\t\tUSA = { set_country_flag = gpu_development_start_year_events_scheduled }\n"
        "\t\t\tABK = { OEM_corporate_history_startup_bootstrap = yes }\n",
    )
    assert any(
        "gpu_development_start_year_events_scheduled must be set only" in message
        for message in _messages(tmp_path)
    )
