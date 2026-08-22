import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = ROOT / "events" / "SOV_computing_sovereignty_events.txt"
EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "SOV_computing_sovereignty_effects.txt"
)
TRIGGERS_PATH = (
    ROOT / "common" / "scripted_triggers" / "SOV_computing_sovereignty_triggers.txt"
)
IDEAS_PATH = ROOT / "common" / "ideas" / "SOV_computing_sovereignty_ideas.txt"
DECISIONS_PATH = ROOT / "common" / "decisions" / "SOV_computing_sovereignty.txt"
DECISION_CATEGORY_PATH = (
    ROOT
    / "common"
    / "decisions"
    / "categories"
    / "SOV_computing_sovereignty_decision_categories.txt"
)
TECHNOLOGIES_PATH = ROOT / "common" / "technologies" / "SOV_computing_sovereignty.txt"
SCRIPTED_LOCALISATION_PATH = (
    ROOT
    / "common"
    / "scripted_localisation"
    / "SOV_computing_sovereignty_dashboard.txt"
)
LOCALISATION_PATH = ROOT / "localisation" / "english" / "MD_focus_SOV_l_english.yml"
TECH_TREE_GUI_PATH = ROOT / "interface" / "countrytechtreeview.gui"
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
AI_STRATEGY_PATH = ROOT / "common" / "ai_strategy" / "SOV.txt"
AI_FOCUS_PATH = ROOT / "common" / "ai_focuses" / "MD_SOV.txt"
DISPATCH_EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_dispatch_effects.txt"
)

AXES = {
    "SOV_computing_sovereignty_architecture": 3.0,
    "SOV_computing_sovereignty_fabrication": 1.8,
    "SOV_computing_sovereignty_software": 4.5,
    "SOV_computing_sovereignty_systems_integration": 5.5,
    "SOV_computing_sovereignty_supply_tooling": 1.5,
    "SOV_computing_sovereignty_foreign_access": 9.0,
    "SOV_computing_sovereignty_human_capital": 5.5,
    "SOV_computing_sovereignty_procurement": 2.5,
    "SOV_computing_sovereignty_shortage": 0.5,
}
BOUNDED_AUXILIARY_STATE = {
    "SOV_computing_sovereignty_angstrem_t_debt",
    "SOV_computing_sovereignty_china_dependency",
    "SOV_computing_sovereignty_parallel_import_risk",
}
ALLOWED_READS = {
    "SOV_western_sanctions",
    "SOV_yandex_idea",
    "SOV_kaspersky_idea",
    "SOV_economic_destiny_yandex",
    "SOV_economic_kasperskyi",
    "SOV_creation_of_sovereign_economy",
    "TAI_tsmc_export_control_compliance",
}

TECHNOLOGIES = {
    "SOV_computing_sovereignty_elbrus_toolchain_1": 1.6,
    "SOV_computing_sovereignty_x86_translation_1": 1.8,
    "SOV_computing_sovereignty_elbrus_4c": 2.2,
    "SOV_computing_sovereignty_elbrus_8c": 3.0,
    "SOV_computing_sovereignty_elbrus_8sv": 2.4,
    "SOV_computing_sovereignty_elbrus_16c": 3.6,
    "SOV_computing_sovereignty_fab_180nm": 1.8,
    "SOV_computing_sovereignty_fab_90nm": 2.4,
    "SOV_computing_sovereignty_fab_65nm_research": 3.2,
    "SOV_computing_sovereignty_fab_65nm_hvm_engineering": 2.4,
    "SOV_computing_sovereignty_fab_28nm_research": 5.0,
    "SOV_computing_sovereignty_fab_28nm_hvm_engineering": 4.2,
    "SOV_computing_sovereignty_fab_16nm_hvm_engineering": 6.5,
    "SOV_computing_sovereignty_domestic_enterprise_software": 1.8,
    "SOV_computing_sovereignty_secure_software_stack": 2.2,
    "SOV_computing_sovereignty_cloud_software_stack": 2.6,
    "SOV_computing_sovereignty_client_system_scale": 1.8,
    "SOV_computing_sovereignty_trusted_server_scale": 2.4,
    "SOV_computing_sovereignty_datacenter_scale": 2.2,
}

TECH_AXIS_EFFECTS = {
    "SOV_computing_sovereignty_elbrus_toolchain_1": (
        "SOV_computing_sovereignty_software",
        0.3,
        "SOV_computing_sovereignty_research_software_03_tt",
    ),
    "SOV_computing_sovereignty_x86_translation_1": (
        "SOV_computing_sovereignty_systems_integration",
        0.3,
        "SOV_computing_sovereignty_research_systems_integration_03_tt",
    ),
    "SOV_computing_sovereignty_elbrus_4c": (
        "SOV_computing_sovereignty_architecture",
        0.3,
        "SOV_computing_sovereignty_research_architecture_03_tt",
    ),
    "SOV_computing_sovereignty_elbrus_8sv": (
        "SOV_computing_sovereignty_architecture",
        0.4,
        "SOV_computing_sovereignty_research_architecture_04_tt",
    ),
    "SOV_computing_sovereignty_fab_28nm_research": (
        "SOV_computing_sovereignty_fabrication",
        0.3,
        "SOV_computing_sovereignty_research_fabrication_03_tt",
    ),
    "SOV_computing_sovereignty_domestic_enterprise_software": (
        "SOV_computing_sovereignty_software",
        0.3,
        "SOV_computing_sovereignty_research_software_03_tt",
    ),
    "SOV_computing_sovereignty_secure_software_stack": (
        "SOV_computing_sovereignty_software",
        0.4,
        "SOV_computing_sovereignty_research_software_04_tt",
    ),
    "SOV_computing_sovereignty_cloud_software_stack": (
        "SOV_computing_sovereignty_software",
        0.3,
        "SOV_computing_sovereignty_research_software_03_tt",
    ),
    "SOV_computing_sovereignty_client_system_scale": (
        "SOV_computing_sovereignty_systems_integration",
        0.3,
        "SOV_computing_sovereignty_research_systems_integration_03_tt",
    ),
    "SOV_computing_sovereignty_trusted_server_scale": (
        "SOV_computing_sovereignty_systems_integration",
        0.3,
        "SOV_computing_sovereignty_research_systems_integration_03_tt",
    ),
    "SOV_computing_sovereignty_datacenter_scale": (
        "SOV_computing_sovereignty_systems_integration",
        0.4,
        "SOV_computing_sovereignty_research_systems_integration_04_tt",
    ),
}

TECH_PROJECT_CONSUMERS = {
    "SOV_computing_sovereignty_elbrus_8c": (
        "SOV_computing_sovereignty_project_foreign_8c_tapeout"
    ),
    "SOV_computing_sovereignty_elbrus_16c": (
        "SOV_computing_sovereignty_project_foreign_16c_tapeout"
    ),
    "SOV_computing_sovereignty_fab_180nm": ("SOV_computing_sovereignty_project_180nm"),
    "SOV_computing_sovereignty_fab_90nm": ("SOV_computing_sovereignty_project_90nm"),
    "SOV_computing_sovereignty_fab_65nm_research": (
        "SOV_computing_sovereignty_project_65nm_pilot"
    ),
    "SOV_computing_sovereignty_fab_65nm_hvm_engineering": (
        "SOV_computing_sovereignty_project_65nm_hvm"
    ),
    "SOV_computing_sovereignty_fab_28nm_hvm_engineering": (
        "SOV_computing_sovereignty_project_28nm_hvm"
    ),
    "SOV_computing_sovereignty_fab_16nm_hvm_engineering": (
        "SOV_computing_sovereignty_project_16nm_hvm"
    ),
}

TECH_CONTEXT_GATES = {
    "SOV_computing_sovereignty_domestic_enterprise_software": (
        {
            "has_tech = computing4",
            "has_country_flag = SOV_computing_sovereignty_1c_ecosystem_active",
        },
        set(),
    ),
    "SOV_computing_sovereignty_secure_software_stack": (
        {"has_tech = SOV_computing_sovereignty_elbrus_toolchain_1"},
        {
            "has_idea = SOV_kaspersky_idea",
            "has_completed_focus = SOV_economic_kasperskyi",
        },
    ),
    "SOV_computing_sovereignty_cloud_software_stack": (
        {"has_tech = computing5"},
        {
            "has_idea = SOV_yandex_idea",
            "has_completed_focus = SOV_economic_destiny_yandex",
        },
    ),
    "SOV_computing_sovereignty_client_system_scale": (
        {
            "has_tech = SOV_computing_sovereignty_domestic_enterprise_software",
            "has_country_flag = SOV_computing_sovereignty_aquarius_active",
        },
        set(),
    ),
    "SOV_computing_sovereignty_trusted_server_scale": (
        {
            "has_tech = SOV_computing_sovereignty_elbrus_4c",
            "has_country_flag = SOV_computing_sovereignty_kraftway_active",
        },
        set(),
    ),
    "SOV_computing_sovereignty_datacenter_scale": (
        {"has_tech = SOV_computing_sovereignty_cloud_software_stack"},
        {
            "has_country_flag = SOV_computing_sovereignty_depo_active",
            "has_country_flag = SOV_computing_sovereignty_kraftway_active",
            "has_country_flag = SOV_computing_sovereignty_aquarius_active",
        },
    ),
}

PROJECTS = {
    "SOV_computing_sovereignty_project_180nm",
    "SOV_computing_sovereignty_project_90nm",
    "SOV_computing_sovereignty_project_65nm_pilot",
    "SOV_computing_sovereignty_project_65nm_hvm",
    "SOV_computing_sovereignty_project_28nm_hvm",
    "SOV_computing_sovereignty_project_16nm_hvm",
    "SOV_computing_sovereignty_project_angstrem_t",
    "SOV_computing_sovereignty_project_foreign_8c_tapeout",
    "SOV_computing_sovereignty_project_foreign_16c_tapeout",
}

OUTCOMES = {
    "SOV_computing_sovereignty_global_integration",
    "SOV_computing_sovereignty_dual_track_sovereignty",
    "SOV_computing_sovereignty_chinese_substitution",
    "SOV_computing_sovereignty_parallel_import_economy",
    "SOV_computing_sovereignty_mature_node_specialization",
    "SOV_computing_sovereignty_sovereign_computing_stack",
    "SOV_computing_sovereignty_industrial_retrenchment",
}


def _extract_block(text: str, start: int) -> str:
    opening = text.index("{", start)
    depth = 0
    in_comment = False
    in_string = False
    escaped = False
    for index in range(opening, len(text)):
        character = text[index]
        if in_comment:
            if character == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == "#":
            in_comment = True
        elif character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError("Unclosed scripted block")


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^[ \t]*{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"Missing block {name}"
    return _extract_block(text, match.start())


def _reachable_effect_blocks(text: str, root: str) -> str:
    names = set(
        re.findall(
            r"(?m)^(SOV_computing_sovereignty_[A-Za-z0-9_]+)\s*=\s*\{",
            text,
        )
    )
    pending = [root]
    visited = set()
    blocks = []
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        block = _named_block(text, name)
        blocks.append(block)
        pending.extend(
            called
            for called in names
            if re.search(rf"\b{re.escape(called)}\s*=\s*yes\b", block)
        )
    return "\n".join(blocks)


def _event_block(text: str, event_number: int) -> str:
    event_id = f"SOV_computing_sovereignty_events.{event_number}"
    for match in re.finditer(r"(?m)^country_event\s*=\s*\{", text):
        block = _extract_block(text, match.start())
        if re.search(rf"\bid\s*=\s*{re.escape(event_id)}\b", block):
            return block
    raise AssertionError(f"Missing event {event_id}")


def _event_option_block(event: str, option_key: str) -> str:
    for match in re.finditer(r"(?m)^\toption\s*=\s*\{", event):
        block = _extract_block(event, match.start())
        if re.search(rf"\bname\s*=\s*{re.escape(option_key)}\b", block):
            return block
    raise AssertionError(f"Missing event option {option_key}")


def _defined_text_block(text: str, name: str) -> str:
    for match in re.finditer(r"(?m)^defined_text\s*=\s*\{", text):
        block = _extract_block(text, match.start())
        if re.search(rf"\bname\s*=\s*{re.escape(name)}\b", block):
            return block
    raise AssertionError(f"Missing defined_text {name}")


def _assigned_value(block: str, variable: str) -> float:
    patterns = (
        rf"set_variable\s*=\s*\{{\s*{re.escape(variable)}\s*=\s*(-?\d+(?:\.\d+)?)\s*\}}",
        rf"set_variable\s*=\s*\{{\s*var\s*=\s*{re.escape(variable)}\s+value\s*=\s*(-?\d+(?:\.\d+)?)\s*\}}",
    )
    for pattern in patterns:
        match = re.search(pattern, block)
        if match:
            return float(match.group(1))
    raise AssertionError(f"Missing initial assignment for {variable}")


def _added_value(block: str, variable: str) -> float:
    values = re.findall(
        rf"add_to_variable\s*=\s*\{{\s*{re.escape(variable)}\s*=\s*"
        r"(-?\d+(?:\.\d+)?)\s*\}",
        block,
    )
    assert values, f"Missing delta for {variable}"
    return sum(float(value) for value in values)


def _top_level_conditional_block(block: str, marker: str) -> str:
    for match in re.finditer(r"(?m)^\t(?:if|else_if)\s*=\s*\{", block):
        conditional = _extract_block(block, match.start())
        if marker in conditional:
            return conditional
    raise AssertionError(f"Missing conditional branch for {marker}")


def _smallest_conditional_block(block: str, marker: str) -> str:
    candidates = []
    for match in re.finditer(r"(?m)^[ \t]+(?:if|else_if)\s*=\s*\{", block):
        conditional = _extract_block(block, match.start())
        if marker in conditional:
            candidates.append(conditional)
    assert candidates, f"Missing conditional branch for {marker}"
    return min(candidates, key=len)


def test_initial_state_formula_and_clamps_match_the_contract():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "SOV_computing_sovereignty_initialize_state")
    clamp = _named_block(effects, "SOV_computing_sovereignty_clamp_state")
    recalculate = _named_block(effects, "SOV_computing_sovereignty_recalculate_state")

    assert {
        variable: _assigned_value(initialize, variable) for variable in AXES
    } == AXES
    for variable in AXES:
        assert variable in clamp
    for variable in BOUNDED_AUXILIARY_STATE:
        assert variable in clamp
    assert clamp.count("corporate_history_clamp_value = yes") >= len(AXES) + len(
        BOUNDED_AUXILIARY_STATE
    )
    expected_contributions = {
        "SOV_computing_sovereignty_temp_architecture": (
            "SOV_computing_sovereignty_architecture",
            0.25,
        ),
        "SOV_computing_sovereignty_temp_fabrication": (
            "SOV_computing_sovereignty_fabrication",
            0.30,
        ),
        "SOV_computing_sovereignty_temp_software": (
            "SOV_computing_sovereignty_software",
            0.15,
        ),
        "SOV_computing_sovereignty_temp_systems": (
            "SOV_computing_sovereignty_systems_integration",
            0.15,
        ),
        "SOV_computing_sovereignty_temp_supply": (
            "SOV_computing_sovereignty_supply_tooling",
            0.15,
        ),
    }
    source_assignments = dict(
        re.findall(
            r"set_temp_variable\s*=\s*\{\s*"
            r"(SOV_computing_sovereignty_temp_[a-z]+)\s*=\s*"
            r"(SOV_computing_sovereignty_[a-z_]+)\s*\}",
            recalculate,
        )
    )
    multipliers = {
        temporary: float(value)
        for temporary, value in re.findall(
            r"multiply_temp_variable\s*=\s*\{\s*"
            r"(SOV_computing_sovereignty_temp_[a-z]+)\s*=\s*"
            r"(-?\d+(?:\.\d+)?)\s*\}",
            recalculate,
        )
    }
    for temporary, (source, weight) in expected_contributions.items():
        assert source_assignments[temporary] == source
        assert multipliers[temporary] == weight

    sovereignty = "SOV_computing_sovereignty_sovereignty"
    first_temporary = "SOV_computing_sovereignty_temp_architecture"
    assert re.search(
        rf"set_variable\s*=\s*\{{\s*{sovereignty}\s*=\s*{first_temporary}\s*\}}",
        recalculate,
    )
    summands = re.findall(
        rf"add_to_variable\s*=\s*\{{\s*{sovereignty}\s*=\s*"
        r"(SOV_computing_sovereignty_temp_[a-z]+)\s*\}",
        recalculate,
    )
    assert set(summands) == set(expected_contributions) - {first_temporary}
    expected_sovereignty = sum(
        AXES[source_assignments[temporary]] * multipliers[temporary]
        for temporary in expected_contributions
    )
    assert round(expected_sovereignty, 6) == 3.015
    assert f"clamp_variable = {{ var = {sovereignty} min = 0 max = 10 }}" in recalculate

    exposure_steps = (
        "set_temp_variable = { SOV_computing_sovereignty_temp_dependence = 10 }",
        "subtract_from_temp_variable = { SOV_computing_sovereignty_temp_dependence = SOV_computing_sovereignty_sovereignty }",
        "set_temp_variable = { SOV_computing_sovereignty_temp_access_gap = 10 }",
        "subtract_from_temp_variable = { SOV_computing_sovereignty_temp_access_gap = SOV_computing_sovereignty_foreign_access }",
        "multiply_temp_variable = { SOV_computing_sovereignty_temp_dependence = SOV_computing_sovereignty_temp_access_gap }",
        "multiply_temp_variable = { SOV_computing_sovereignty_temp_dependence = 0.1 }",
        "set_variable = { SOV_computing_sovereignty_sanction_exposure = SOV_computing_sovereignty_temp_dependence }",
        "clamp_variable = { var = SOV_computing_sovereignty_sanction_exposure min = 0 max = 10 }",
    )
    positions = [recalculate.index(step) for step in exposure_steps]
    assert positions == sorted(positions)
    expected_exposure = (
        (10 - expected_sovereignty)
        * (10 - AXES["SOV_computing_sovereignty_foreign_access"])
        * 0.1
    )
    assert round(expected_exposure, 6) == 0.6985
    for company in (
        "SOV_computing_sovereignty_1c_ecosystem_active",
        "SOV_computing_sovereignty_depo_active",
    ):
        assert company in initialize


def test_sovereignty_band_selection_cannot_fall_through_when_already_current():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    update = _named_block(effects, "SOV_computing_sovereignty_update_band")
    threshold_bands = (
        "SOV_computing_sovereignty_import_dependent_core",
        "SOV_computing_sovereignty_hybrid_industrial_base",
        "SOV_computing_sovereignty_localized_stack",
        "SOV_computing_sovereignty_sovereign_computing_base",
    )

    for idea in threshold_bands:
        branch = _top_level_conditional_block(update, idea)
        outer_limit = _named_block(branch, "limit")
        assert "check_variable" in outer_limit
        assert "has_idea" not in outer_limit
        assert f"NOT = {{ has_idea = {idea} }}" in branch

    final_else_match = re.search(r"(?m)^\telse\s*=\s*\{", update)
    assert final_else_match
    final_else = _extract_block(update, final_else_match.start())
    assert (
        "NOT = { has_idea = SOV_computing_sovereignty_near_autarkic_stack }"
        in final_else
    )


def test_event_inventory_is_eighteen_visible_events():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    ids = [
        int(value)
        for value in re.findall(
            r"\bid\s*=\s*SOV_computing_sovereignty_events\.(\d+)", events
        )
    ]
    expected_ids = set(range(1, 19))
    assert set(ids) == expected_ids
    assert len(ids) == len(expected_ids)

    for event_number in range(1, 19):
        event = _event_block(events, event_number)
        assert "is_triggered_only = yes" in event
        assert "fire_only_once = yes" in event
        assert "original_tag = SOV" in event
        assert "collapsed_nation" in event
        options = [
            _extract_block(event, match.start())
            for match in re.finditer(r"(?m)^\toption\s*=\s*\{", event)
        ]
        assert options
        assert all("name =" in option and "log =" in option for option in options)


def test_reconstruction_is_silent_and_never_grants_advanced_hvm():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    direct_reconstruct = _named_block(
        effects, "SOV_computing_sovereignty_reconstruct_history"
    )
    reconstruct = _reachable_effect_blocks(
        effects, "SOV_computing_sovereignty_reconstruct_history"
    )
    for forbidden in (
        "country_event =",
        "modify_treasury_effect",
        "add_political_power",
        "add_building_construction",
        "add_offsite_building",
    ):
        assert forbidden not in reconstruct
    technology_grants = "\n".join(
        _extract_block(reconstruct, match.start())
        for match in re.finditer(r"(?m)^\s*set_technology\s*=\s*\{", reconstruct)
    )
    for forbidden_technology in (
        "microchip_production_",
        "SOV_computing_sovereignty_fab_65nm_hvm_engineering",
        "SOV_computing_sovereignty_fab_28nm_hvm_engineering",
        "SOV_computing_sovereignty_fab_16nm_hvm_engineering",
    ):
        assert forbidden_technology not in technology_grants
    for forbidden_idea in (
        "SOV_computing_sovereignty_28nm_hvm_capacity",
        "SOV_computing_sovereignty_16nm_hvm_capacity",
    ):
        assert not re.search(
            rf"\badd_ideas\s*=\s*{re.escape(forbidden_idea)}\b", reconstruct
        )
    historical_technology_grants = set(
        re.findall(
            r"(?m)^\s*(SOV_computing_sovereignty_[A-Za-z0-9_]+)\s*=\s*1\s*$",
            technology_grants,
        )
    )
    for technology in historical_technology_grants:
        assert re.search(
            rf"NOT\s*=\s*\{{\s*has_tech\s*=\s*{re.escape(technology)}\s*\}}",
            direct_reconstruct,
        )
    assert "SOV_computing_sovereignty_reconstruct_complete" in reconstruct


def test_same_year_startup_skips_are_silently_consumed_after_their_dates():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    advance = _named_block(effects, "SOV_computing_sovereignty_advance_startup_skipped")
    monthly = _named_block(effects, "SOV_computing_sovereignty_monthly")
    milestones = {
        1: ("2001.6.1", "SOV_computing_sovereignty_apply_elbrus_fabless"),
        2: ("2006.4.25", "SOV_computing_sovereignty_apply_stmicro_license"),
        3: ("2008.6.1", "SOV_computing_sovereignty_apply_angstrem_guarantee"),
        4: ("2012.6.1", "SOV_computing_sovereignty_apply_90nm_zelenograd"),
        5: (
            "2012.12.4",
            "SOV_computing_sovereignty_apply_yotaphone_global_failure",
        ),
        6: ("2014.4.1", "SOV_computing_sovereignty_apply_elbrus_8c"),
        7: (
            "2014.8.1",
            "SOV_computing_sovereignty_apply_import_substitution_strategic",
        ),
        8: ("2015.1.15", "SOV_computing_sovereignty_apply_software_register"),
        11: ("2020.11.1", "SOV_computing_sovereignty_apply_elbrus_16c"),
    }

    assert "SOV_computing_sovereignty_no_event_pending = yes" in advance
    assert "SOV_computing_sovereignty_advance_startup_skipped = yes" in monthly
    for event_number, (milestone, canonical_effect) in milestones.items():
        marker = f"SOV_computing_sovereignty_event_{event_number:02d}_startup_skipped"
        branch = _top_level_conditional_block(advance, marker)
        assert f"date > {milestone}" in branch
        assert f"has_country_flag = {marker}" in branch
        assert f"clr_country_flag = {marker}" in branch
        assert (
            "NOT = { has_country_flag = "
            f"SOV_computing_sovereignty_event_{event_number:02d}_resolved }}" in branch
        )
        assert f"{canonical_effect} = yes" in branch

    parallel_imports_branch = _top_level_conditional_block(
        advance, "SOV_computing_sovereignty_event_14_startup_skipped"
    )
    assert "date > 2022.5.5" in parallel_imports_branch
    assert "SOV_computing_sovereignty_parallel_imports_ready = yes" in (
        parallel_imports_branch
    )
    assert (
        "clr_country_flag = "
        "SOV_computing_sovereignty_event_14_startup_skipped" in parallel_imports_branch
    )
    assert "SOV_computing_sovereignty_recovery_target = 14" in parallel_imports_branch
    assert (
        "SOV_computing_sovereignty_schedule_current_year_events = yes"
        in parallel_imports_branch
    )

    angstrem_branch = _top_level_conditional_block(
        advance, "SOV_computing_sovereignty_event_03_startup_skipped"
    )
    assert "SOV_computing_sovereignty_project_slot_available = yes" in angstrem_branch
    assert (
        "SOV_computing_sovereignty_launch_project_angstrem_t = yes" in angstrem_branch
    )
    assert (
        "set_country_flag = SOV_computing_sovereignty_angstrem_t_financing_authorized"
        in angstrem_branch
    )
    assert "SOV_computing_sovereignty_event_18_startup_skipped" in advance
    assert "SOV_computing_sovereignty_resolve_terminal_outcome = yes" in advance
    assert "SOV_computing_sovereignty_finish_event_18 = yes" in advance


def test_exact_milestone_start_dates_are_delivered_instead_of_stranded():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    schedule = _named_block(
        effects, "SOV_computing_sovereignty_schedule_current_year_events"
    )
    date_windows = {
        1: ("2001.5.31", "2001.6.2"),
        2: ("2006.4.24", "2006.4.26"),
        3: ("2008.5.31", "2008.6.2"),
        4: ("2012.5.31", "2012.6.2"),
        5: ("2012.12.3", "2012.12.5"),
        6: ("2014.3.31", "2014.4.2"),
        7: ("2014.7.31", "2014.8.2"),
        8: ("2015.1.14", "2015.1.16"),
        11: ("2020.10.31", "2020.11.2"),
        14: ("2022.5.5", "2022.5.7"),
    }

    for event_number, (previous_day, next_day) in date_windows.items():
        marker = f"SOV_computing_sovereignty_event_{event_number:02d}_startup_skipped"
        branch = _top_level_conditional_block(schedule, marker)
        assert f"date < {next_day}" in branch
        assert f"date > {previous_day}" in branch
        assert (
            "country_event = { id = "
            f"SOV_computing_sovereignty_events.{event_number} days = 0 }}" in branch
        )


def test_outcomes_only_reconstruction_uses_the_owner_local_monthly_driver():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    monthly = _named_block(effects, "SOV_corporate_history_monthly_outcomes")

    assert "SOV_computing_sovereignty_events.90" not in events
    assert "corporate_history_outcomes_only_enabled = yes" in monthly
    assert "SOV_computing_sovereignty_reconstruct_history = yes" in monthly
    assert "corporate_history_full_enabled = yes" in monthly
    assert "SOV_computing_sovereignty_monthly = yes" in monthly


def test_project_narrative_callbacks_wait_for_the_shared_event_slot():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    recovery = _named_block(effects, "SOV_computing_sovereignty_recover_pending_events")

    for event_number in (4, 6, 11):
        queue = _named_block(
            effects, f"SOV_computing_sovereignty_queue_event_{event_number:02d}"
        )
        assert (
            "set_country_flag = "
            f"SOV_computing_sovereignty_event_{event_number:02d}_delivery_expected"
            in queue
        )
        assert "SOV_computing_sovereignty_no_event_pending = yes" in queue
        open_slot_branch = _top_level_conditional_block(
            queue, "SOV_computing_sovereignty_no_event_pending = yes"
        )
        assert (
            "SOV_computing_sovereignty_schedule_current_year_events = yes"
            in open_slot_branch
        )

        recovery_branch = _smallest_conditional_block(
            recovery,
            f"SOV_computing_sovereignty_event_{event_number:02d}_delivery_expected",
        )
        assert "SOV_computing_sovereignty_no_event_pending = yes" in recovery_branch


def test_state_event_recovery_rechecks_each_live_readiness_predicate():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    recovery = _named_block(effects, "SOV_computing_sovereignty_recover_pending_events")
    readiness = {
        9: "SOV_computing_sovereignty_guaranteed_purchases_ready",
        10: "SOV_computing_sovereignty_angstrem_crisis_ready",
        12: "SOV_computing_sovereignty_embargo_ready",
        13: "SOV_computing_sovereignty_tsmc_closure_ready",
        15: "SOV_computing_sovereignty_chinese_supply_ready",
        16: "SOV_computing_sovereignty_emergency_program_ready",
        17: "SOV_computing_sovereignty_mature_nodes_ready",
    }

    for event_number, predicate in readiness.items():
        branch = _smallest_conditional_block(
            recovery,
            f"SOV_computing_sovereignty_event_{event_number:02d}_delivery_expected",
        )
        assert f"{predicate} = yes" in branch


def test_project_lifecycle_is_serial_retryable_and_bankruptcy_safe():
    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    project_slot = _named_block(
        triggers, "SOV_computing_sovereignty_project_slot_available"
    )
    assert "SOV_computing_sovereignty_industrial_project_active" in project_slot
    assert "NOT =" in project_slot

    specialized_gates = {
        "SOV_computing_sovereignty_project_foreign_8c_tapeout": (
            "SOV_computing_sovereignty_8c_tapeout_available"
        ),
        "SOV_computing_sovereignty_project_foreign_16c_tapeout": (
            "SOV_computing_sovereignty_16c_tapeout_available"
        ),
    }
    for gate in specialized_gates.values():
        assert "SOV_computing_sovereignty_project_slot_available = yes" in _named_block(
            triggers, gate
        )

    for project in PROJECTS:
        block = _named_block(decisions, project)
        gate = specialized_gates.get(
            project, "SOV_computing_sovereignty_project_slot_available"
        )
        assert f"{gate} = yes" in block
        assert "days_re_enable = 30" in block
        assert "fire_only_once = no" in block
        assert "fixed_random_seed = no" in block
        assert "has_active_mission = bankruptcy_incoming_collapse" in block
        assert "ai_will_do = {" in block
        assert "log =" in block
        mission = _named_block(decisions, f"{project}_mission")
        assert "fixed_random_seed = no" in mission
        assert "timeout_effect = {" in mission
        assert "cancel_effect = {" in mission
        assert mission.count("log =") == 2
    assert "active_economic_project" not in decisions


def test_tapeout_projects_revalidate_live_foundry_routes_at_completion():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    external_route = _named_block(
        triggers, "SOV_computing_sovereignty_has_external_foundry_route"
    )
    resolver = _named_block(
        effects, "SOV_computing_sovereignty_resolve_industrial_project"
    )
    closure = _named_block(
        effects, "SOV_computing_sovereignty_apply_tsmc_closure_common"
    )

    assert "country_exists = CHI" in external_route
    assert re.search(
        r"AND\s*=\s*\{\s*country_exists\s*=\s*CHI\s*OR\s*=\s*\{[^}]*"
        r"SOV_computing_sovereignty_chinese_foundry_agreement[^}]*"
        r"SOV_computing_sovereignty_chinese_foundry_route",
        external_route,
        re.DOTALL,
    )

    route_failure = _top_level_conditional_block(
        resolver, "SOV_computing_sovereignty_project_foreign_8c_tapeout_active"
    )
    assert (
        "SOV_computing_sovereignty_project_foreign_16c_tapeout_active" in route_failure
    )
    assert (
        "SOV_computing_sovereignty_has_28nm_or_better_domestic_capacity"
        in route_failure
    )
    assert "has_idea = SOV_computing_sovereignty_16nm_hvm_capacity" in route_failure
    assert "SOV_computing_sovereignty_has_external_foundry_route" in route_failure
    assert (
        "SOV_computing_sovereignty_apply_industrial_project_failure = yes"
        in route_failure
    )

    assert (
        "SOV_computing_sovereignty_retire_project_foreign_8c_tapeout = yes" in closure
    )
    assert (
        "SOV_computing_sovereignty_retire_project_foreign_16c_tapeout = yes" in closure
    )


def test_angstrem_financing_trades_success_for_debt():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    debt_variable = "SOV_computing_sovereignty_angstrem_t_debt"
    guarantee = _named_block(
        effects, "SOV_computing_sovereignty_apply_angstrem_guarantee"
    )
    equity = _named_block(effects, "SOV_computing_sovereignty_apply_angstrem_equity")
    launch = _named_block(
        effects, "SOV_computing_sovereignty_launch_project_angstrem_t"
    )
    prepare = _named_block(
        effects, "SOV_computing_sovereignty_prepare_industrial_project"
    )

    assert _added_value(guarantee, debt_variable) == 4.0
    assert _added_value(equity, debt_variable) == 1.0
    equity_branch = _smallest_conditional_block(
        launch, "SOV_computing_sovereignty_angstrem_equity_financing"
    )
    assert "SOV_computing_sovereignty_project_base_chance = 35" in equity_branch
    assert "SOV_computing_sovereignty_project_base_chance = 55" not in equity_branch
    default_branches = [
        _extract_block(launch, match.start())
        for match in re.finditer(r"(?m)^\telse\s*=\s*\{", launch)
    ]
    assert any(
        "SOV_computing_sovereignty_project_base_chance = 55" in branch
        for branch in default_branches
    )
    assert "SOV_computing_sovereignty_project_success_chance = -10" in prepare
    assert 55 - 10 > 35


def test_technology_tree_matches_the_pdf_and_separates_design_from_fabs():
    technologies = TECHNOLOGIES_PATH.read_text(encoding="utf-8")
    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    assert "CAT_SOV_computing_sovereignty" not in technologies
    found = set(
        re.findall(
            r"(?m)^[ \t]*(SOV_computing_sovereignty_[A-Za-z0-9_]+)\s*=\s*\{",
            technologies,
        )
    )
    assert set(TECHNOLOGIES) == found

    for technology, cost in TECHNOLOGIES.items():
        block = _named_block(technologies, technology)
        research_cost = re.search(r"research_cost\s*=\s*(-?\d+(?:\.\d+)?)", block)
        assert research_cost
        assert float(research_cost.group(1)) == cost
        assert "original_tag = SOV" in block
        assert "SOV_computing_sovereignty_recalculate_state = yes" in block

    assert set(TECH_AXIS_EFFECTS) | set(TECH_PROJECT_CONSUMERS) == set(TECHNOLOGIES)
    assert not (set(TECH_AXIS_EFFECTS) & set(TECH_PROJECT_CONSUMERS))
    for technology, (axis, delta, tooltip) in TECH_AXIS_EFFECTS.items():
        block = _named_block(technologies, technology)
        assert tooltip in block
        assert re.search(
            rf"add_to_variable\s*=\s*\{{\s*{re.escape(axis)}\s*=\s*{delta}\s*\}}",
            block,
        )
    for technology, project in TECH_PROJECT_CONSUMERS.items():
        assert f"has_tech = {technology}" in _named_block(decisions, project)
    for technology, (required_gates, alternative_gates) in TECH_CONTEXT_GATES.items():
        block = _named_block(technologies, technology)
        allow = _named_block(block, "allow")
        assert "original_tag = SOV" in allow
        assert "corporate_history_full_enabled = yes" in allow
        if alternative_gates:
            alternatives = _named_block(allow, "OR")
            assert all(gate in alternatives for gate in alternative_gates)
            assert not any(gate in alternatives for gate in required_gates)
            conjunctive_allow = allow.replace(alternatives, "")
        else:
            assert not re.search(r"(?m)^\s*OR\s*=", allow)
            conjunctive_allow = allow
        assert all(gate in conjunctive_allow for gate in required_gates)

    for technology in (
        "SOV_computing_sovereignty_elbrus_8c",
        "SOV_computing_sovereignty_elbrus_16c",
    ):
        block = _named_block(technologies, technology)
        assert "foreign_foundry" not in block
        assert "hvm_capacity" not in block

    assert "SOV_computing_sovereignty_65nm_pilot_capability" in _named_block(
        technologies,
        "SOV_computing_sovereignty_fab_65nm_hvm_engineering",
    )
    assert "SOV_computing_sovereignty_28nm_hvm_capacity" in _named_block(
        technologies,
        "SOV_computing_sovereignty_fab_16nm_hvm_engineering",
    )


def test_supply_progression_reaches_frontier_thresholds():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    project_success = _named_block(
        effects, "SOV_computing_sovereignty_apply_industrial_project_success"
    )
    supply_variable = "SOV_computing_sovereignty_supply_tooling"
    progression = (
        (
            "SOV_computing_sovereignty_project_180nm_active",
            0.8,
        ),
        ("SOV_computing_sovereignty_project_65nm_pilot_active", 1.0),
        ("SOV_computing_sovereignty_project_65nm_hvm_active", 1.2),
    )

    supply = AXES[supply_variable]
    first_branch = _top_level_conditional_block(project_success, progression[0][0])
    assert _added_value(first_branch, supply_variable) == progression[0][1]
    supply += _added_value(first_branch, supply_variable)
    ninety_nm = _named_block(effects, "SOV_computing_sovereignty_apply_90nm_zelenograd")
    assert _added_value(ninety_nm, supply_variable) == 1.0
    supply += _added_value(ninety_nm, supply_variable)
    for marker, expected_delta in progression[1:]:
        branch = _top_level_conditional_block(project_success, marker)
        assert _added_value(branch, supply_variable) == expected_delta
        supply += _added_value(branch, supply_variable)
    assert supply == 5.5
    twenty_eight_nm = _top_level_conditional_block(
        project_success, "SOV_computing_sovereignty_project_28nm_hvm_active"
    )
    assert _added_value(twenty_eight_nm, supply_variable) == 1.5
    supply += _added_value(twenty_eight_nm, supply_variable)
    assert supply == 7.0

    technologies = TECHNOLOGIES_PATH.read_text(encoding="utf-8")
    assert "SOV_computing_sovereignty_supply_tooling > 5.499" in _named_block(
        technologies,
        "SOV_computing_sovereignty_fab_28nm_hvm_engineering",
    )
    assert "SOV_computing_sovereignty_supply_tooling > 6.999" in _named_block(
        technologies,
        "SOV_computing_sovereignty_fab_16nm_hvm_engineering",
    )


def test_capacity_ideas_form_a_highest_stage_upgrade_ladder():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    technologies = TECHNOLOGIES_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    project_success = _named_block(
        effects, "SOV_computing_sovereignty_apply_industrial_project_success"
    )
    stages = (
        (
            "SOV_computing_sovereignty_project_65nm_hvm_active",
            "SOV_computing_sovereignty_65nm_hvm_capacity",
            {
                "SOV_computing_sovereignty_domestic_180nm_capacity",
                "SOV_computing_sovereignty_domestic_90nm_capacity",
                "SOV_computing_sovereignty_65nm_pilot_capability",
            },
        ),
        (
            "SOV_computing_sovereignty_project_28nm_hvm_active",
            "SOV_computing_sovereignty_28nm_hvm_capacity",
            {
                "SOV_computing_sovereignty_domestic_180nm_capacity",
                "SOV_computing_sovereignty_domestic_90nm_capacity",
                "SOV_computing_sovereignty_65nm_pilot_capability",
                "SOV_computing_sovereignty_65nm_hvm_capacity",
            },
        ),
        (
            "SOV_computing_sovereignty_project_16nm_hvm_active",
            "SOV_computing_sovereignty_16nm_hvm_capacity",
            {
                "SOV_computing_sovereignty_domestic_180nm_capacity",
                "SOV_computing_sovereignty_domestic_90nm_capacity",
                "SOV_computing_sovereignty_65nm_pilot_capability",
                "SOV_computing_sovereignty_65nm_hvm_capacity",
                "SOV_computing_sovereignty_28nm_hvm_capacity",
            },
        ),
    )
    ninety_nm = _named_block(effects, "SOV_computing_sovereignty_apply_90nm_zelenograd")
    assert (
        "remove_ideas = SOV_computing_sovereignty_domestic_180nm_capacity" in ninety_nm
    )
    for marker, result, removed in stages:
        branch = _top_level_conditional_block(project_success, marker)
        assert f"add_ideas = {result}" in branch
        assert all(f"remove_ideas = {idea}" in branch for idea in removed)

    capacity_ideas = (
        "SOV_computing_sovereignty_domestic_180nm_capacity",
        "SOV_computing_sovereignty_domestic_90nm_capacity",
        "SOV_computing_sovereignty_65nm_pilot_capability",
        "SOV_computing_sovereignty_65nm_hvm_capacity",
        "SOV_computing_sovereignty_28nm_hvm_capacity",
        "SOV_computing_sovereignty_16nm_hvm_capacity",
    )
    capacity_projects = (
        "SOV_computing_sovereignty_project_180nm",
        "SOV_computing_sovereignty_project_90nm",
        "SOV_computing_sovereignty_project_65nm_pilot",
        "SOV_computing_sovereignty_project_65nm_hvm",
        "SOV_computing_sovereignty_project_28nm_hvm",
        "SOV_computing_sovereignty_project_16nm_hvm",
    )
    for stage, project in enumerate(capacity_projects):
        visible = _named_block(_named_block(decisions, project), "visible")
        assert all(f"has_idea = {idea}" in visible for idea in capacity_ideas[stage:])
        if stage >= 2:
            assert (
                "NOT = { has_country_flag = "
                "SOV_computing_sovereignty_mature_node_route }" in visible
            )

    mature_nodes = _named_block(effects, "SOV_computing_sovereignty_apply_mature_nodes")
    mature_reconciliation = _named_block(
        effects, "SOV_computing_sovereignty_reconcile_mature_node_capacity"
    )
    assert (
        "SOV_computing_sovereignty_reconcile_mature_node_capacity = yes" in mature_nodes
    )
    assert (
        "add_ideas = SOV_computing_sovereignty_domestic_90nm_capacity"
        in mature_reconciliation
    )
    for idea in capacity_ideas[:1] + capacity_ideas[2:]:
        assert f"remove_ideas = {idea}" in mature_reconciliation
    mature_qualified = _named_block(
        triggers, "SOV_computing_sovereignty_mature_node_qualified"
    )
    assert "SOV_computing_sovereignty_mature_node_route" in mature_qualified
    assert "SOV_computing_sovereignty_domestic_90nm_capacity" in mature_qualified
    for technology in (
        "SOV_computing_sovereignty_fab_65nm_research",
        "SOV_computing_sovereignty_fab_65nm_hvm_engineering",
        "SOV_computing_sovereignty_fab_28nm_research",
        "SOV_computing_sovereignty_fab_28nm_hvm_engineering",
        "SOV_computing_sovereignty_fab_16nm_hvm_engineering",
    ):
        allow = _named_block(_named_block(technologies, technology), "allow")
        assert (
            "NOT = { has_country_flag = "
            "SOV_computing_sovereignty_mature_node_route }" in allow
        )


def test_mature_node_retreat_is_authoritative_but_preserves_a_retry_choice():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = EVENTS_PATH.read_text(encoding="utf-8")
    reconcile = _named_block(
        effects, "SOV_computing_sovereignty_reconcile_mature_node_capacity"
    )
    event_17 = _event_block(events, 17)
    keep_frontier = _event_option_block(
        event_17, "SOV_computing_sovereignty_events.17.b"
    )
    keep_frontier_effect = _named_block(
        effects, "SOV_computing_sovereignty_keep_frontier_program"
    )

    assert "SOV_computing_sovereignty_retire_active_capacity_project = yes" in reconcile
    assert "add_ideas = SOV_computing_sovereignty_domestic_90nm_capacity" in reconcile
    for obsolete in (
        "SOV_computing_sovereignty_domestic_180nm_capacity",
        "SOV_computing_sovereignty_65nm_pilot_capability",
        "SOV_computing_sovereignty_65nm_hvm_capacity",
        "SOV_computing_sovereignty_28nm_hvm_capacity",
        "SOV_computing_sovereignty_16nm_hvm_capacity",
    ):
        assert f"remove_ideas = {obsolete}" in reconcile
    assert "SOV_computing_sovereignty_project_28nm_hvm_failed" in keep_frontier
    assert "SOV_computing_sovereignty_project_16nm_hvm_failed" in keep_frontier
    assert "SOV_computing_sovereignty_keep_frontier_program = yes" in keep_frontier
    assert "SOV_computing_sovereignty_apply_mature_nodes" not in keep_frontier_effect
    assert "SOV_computing_sovereignty_finish_event_17 = yes" in keep_frontier_effect


def test_crisis_and_chinese_routes_preserve_their_authoritative_state():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = EVENTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    scripted_localisation = SCRIPTED_LOCALISATION_PATH.read_text(encoding="utf-8")

    emergency = _named_block(
        triggers, "SOV_computing_sovereignty_emergency_program_ready"
    )
    assert re.search(
        r"var\s*=\s*SOV_computing_sovereignty_foreign_access\s+"
        r"value\s*=\s*2\.5\s+compare\s*=\s*less_than_or_equals",
        emergency,
    )
    assert re.search(
        r"var\s*=\s*SOV_computing_sovereignty_sovereignty\s+"
        r"value\s*=\s*5\.5\s+compare\s*=\s*less_than",
        emergency,
    )
    emergency_routes = _named_block(emergency, "OR")
    assert re.search(
        r"var\s*=\s*SOV_computing_sovereignty_shortage\s+"
        r"value\s*=\s*4\s+compare\s*=\s*greater_than_or_equals",
        emergency_routes,
    )
    assert "SOV_computing_sovereignty_emergency_fabrication_program" in emergency_routes

    mature = _named_block(triggers, "SOV_computing_sovereignty_mature_nodes_ready")
    assert "SOV_computing_sovereignty_event_16_resolved" not in mature
    mature_routes = _named_block(mature, "OR")
    for route in (
        "SOV_computing_sovereignty_mature_node_route",
        "SOV_computing_sovereignty_project_28nm_hvm_failed",
        "SOV_computing_sovereignty_project_16nm_hvm_failed",
        "SOV_computing_sovereignty_sovereignty_program_defaulted",
    ):
        assert route in mature_routes

    closure = _named_block(
        effects, "SOV_computing_sovereignty_apply_tsmc_closure_common"
    )
    assert (
        "add_to_variable = { SOV_computing_sovereignty_foreign_access = -1.5 }"
        in closure
    )

    external_route = _named_block(
        triggers, "SOV_computing_sovereignty_has_external_foundry_route"
    )
    assert "country_exists = CHI" in external_route
    assert "SOV_computing_sovereignty_chinese_foundry_agreement" in external_route
    assert "SOV_computing_sovereignty_chinese_foundry_route" in external_route
    chinese_outcome = _named_block(
        triggers, "SOV_computing_sovereignty_chinese_substitution_qualified"
    )
    assert "country_exists = CHI" in chinese_outcome

    chinese_search = _event_option_block(
        _event_block(events, 13), "SOV_computing_sovereignty_events.13.a"
    )
    assert "trigger = { country_exists = CHI }" in chinese_search
    unavailable_search = _named_block(
        effects, "SOV_computing_sovereignty_resolve_unavailable_chinese_search"
    )
    assert (
        "SOV_computing_sovereignty_reconcile_mature_node_capacity = yes"
        in unavailable_search
    )
    foundry = _defined_text_block(
        scripted_localisation, "SOV_computing_sovereignty_foundry_route"
    )
    assert foundry.count("country_exists = CHI") == 2


def test_parallel_imports_share_one_state_gate_and_do_not_leak_when_disabled():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = EVENTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")

    readiness = _named_block(
        triggers, "SOV_computing_sovereignty_parallel_imports_ready"
    )
    assert re.search(
        r"var\s*=\s*SOV_computing_sovereignty_foreign_access\s+"
        r"value\s*=\s*4\s+compare\s*=\s*less_than",
        readiness,
    )
    readiness_route = _named_block(readiness, "OR")
    assert "date > 2022.5.5" in readiness_route
    assert "SOV_computing_sovereignty_parallel_imports_authorized" in readiness_route

    event_trigger = _named_block(_event_block(events, 14), "trigger")
    assert "SOV_computing_sovereignty_parallel_imports_ready = yes" in event_trigger
    assert "SOV_computing_sovereignty_no_event_pending = yes" in event_trigger

    bridge = _named_block(
        effects, "SOV_computing_sovereignty_trigger_parallel_import_event"
    )
    enabled_branch = _top_level_conditional_block(
        bridge, "corporate_history_enabled = yes"
    )
    assert bridge.count("SOV_computing_sovereignty_parallel_imports_authorized") == 1
    assert "SOV_computing_sovereignty_parallel_imports_authorized" in enabled_branch
    assert "SOV_computing_sovereignty_parallel_imports_ready = yes" in enabled_branch

    monthly = _named_block(effects, "SOV_computing_sovereignty_monthly")
    monthly_delivery = _smallest_conditional_block(
        monthly, "SOV_computing_sovereignty_recovery_target = 14"
    )
    assert "SOV_computing_sovereignty_parallel_imports_ready = yes" in monthly_delivery


def test_checkpoint_reclassifies_only_on_outcome_mismatch():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    recalculate = _named_block(effects, "SOV_computing_sovereignty_recalculate_state")
    selector = _named_block(
        effects, "SOV_computing_sovereignty_select_terminal_outcome"
    )
    resolve = _named_block(
        effects, "SOV_computing_sovereignty_resolve_terminal_outcome"
    )
    reconstruct = _named_block(effects, "SOV_computing_sovereignty_reconstruct_history")
    reconstructed_checkpoint = _top_level_conditional_block(
        reconstruct, "SOV_computing_sovereignty_event_18_resolved"
    )
    post_checkpoint_recalculation = _smallest_conditional_block(
        recalculate, "SOV_computing_sovereignty_event_18_resolved"
    )

    assert "has_country_flag = SOV_computing_sovereignty_event_18_resolved" in (
        post_checkpoint_recalculation
    )
    assert "SOV_computing_sovereignty_select_terminal_outcome = yes" in (
        post_checkpoint_recalculation
    )
    assert (
        recalculate.count("SOV_computing_sovereignty_select_terminal_outcome = yes")
        == 1
    )
    for outcome in OUTCOMES:
        assert f"NOT = {{ has_idea = {outcome} }}" in selector
    qualified_outcomes = {
        "SOV_computing_sovereignty_sovereign_stack_qualified": (
            "SOV_computing_sovereignty_sovereign_computing_stack"
        ),
        "SOV_computing_sovereignty_mature_node_qualified": (
            "SOV_computing_sovereignty_mature_node_specialization"
        ),
        "SOV_computing_sovereignty_chinese_substitution_qualified": (
            "SOV_computing_sovereignty_chinese_substitution"
        ),
        "SOV_computing_sovereignty_parallel_import_qualified": (
            "SOV_computing_sovereignty_parallel_import_economy"
        ),
        "SOV_computing_sovereignty_dual_track_qualified": (
            "SOV_computing_sovereignty_dual_track_sovereignty"
        ),
        "SOV_computing_sovereignty_global_integration_qualified": (
            "SOV_computing_sovereignty_global_integration"
        ),
    }
    for predicate, outcome in qualified_outcomes.items():
        branch = _top_level_conditional_block(selector, predicate)
        assert f"NOT = {{ has_idea = {outcome} }}" in branch
    sovereign_selection = _top_level_conditional_block(
        selector, "SOV_computing_sovereignty_sovereign_stack_qualified"
    )
    assert "remove_ideas = SOV_computing_sovereignty_technology_embargo" in (
        sovereign_selection
    )
    assert "SOV_computing_sovereignty_recalculate_state = yes" in resolve
    assert "SOV_computing_sovereignty_select_terminal_outcome = yes" in resolve
    assert resolve.index("SOV_computing_sovereignty_recalculate_state = yes") < (
        resolve.index("SOV_computing_sovereignty_select_terminal_outcome = yes")
    )
    assert (
        "SOV_computing_sovereignty_resolve_terminal_outcome = yes"
        in reconstructed_checkpoint
    )
    assert "SOV_computing_sovereignty_apply_parallel_import_outcome" not in (
        reconstructed_checkpoint
    )

    sovereign = _named_block(
        triggers, "SOV_computing_sovereignty_sovereign_stack_qualified"
    )
    assert "SOV_computing_sovereignty_mature_node_route" in sovereign
    clear_outcome = _named_block(
        effects, "SOV_computing_sovereignty_clear_terminal_outcome"
    )
    assert "has_idea = SOV_computing_sovereignty_sovereign_computing_stack" in (
        clear_outcome
    )
    assert "add_ideas = SOV_computing_sovereignty_technology_embargo" in clear_outcome

    for effect_name in (
        "SOV_computing_sovereignty_finish_event_18",
        "SOV_computing_sovereignty_apply_industrial_retrenchment_outcome",
    ):
        block = _named_block(effects, effect_name)
        assert (
            "remove_mission = SOV_computing_sovereignty_sovereignty_program"
            not in block
        )
        assert "SOV_computing_sovereignty_cancel_industrial_project" not in block


def test_outcomes_are_authoritative_ideas_and_dashboard_is_read_only():
    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    scripted_localisation = SCRIPTED_LOCALISATION_PATH.read_text(encoding="utf-8")

    for outcome in OUTCOMES:
        assert re.search(rf"(?m)^\t\t{re.escape(outcome)}\s*=\s*\{{", ideas)
        assert f"has_idea = {outcome}" in scripted_localisation
    foundry = _defined_text_block(
        scripted_localisation, "SOV_computing_sovereignty_foundry_route"
    )
    assert "SOV_computing_sovereignty_chinese_foundry_agreement" in foundry
    assert "SOV_computing_sovereignty_chinese_foundry_search_pending" in foundry
    assert "SOV_computing_sovereignty_frontier_output_suspended" in foundry
    assert "SOV_computing_sovereignty_route_chinese_negotiations" in foundry
    for processor in ("8c", "16c"):
        status = _defined_text_block(
            scripted_localisation,
            f"SOV_computing_sovereignty_elbrus_{processor}_status",
        )
        assert f"SOV_computing_sovereignty_elbrus_{processor}_deployable" in status
        assert "foundry_route" not in status
    for forbidden in ("set_variable", "set_country_flag", "add_ideas", "remove_ideas"):
        assert forbidden not in scripted_localisation


def test_ai_bootstrap_and_capacity_strategies_are_bounded():
    strategy = AI_STRATEGY_PATH.read_text(encoding="utf-8")
    focuses = AI_FOCUS_PATH.read_text(encoding="utf-8")
    bootstrap = _named_block(
        strategy, "SOV_computing_sovereignty_research_microchip_bootstrap"
    )
    hybrid = _named_block(
        strategy, "SOV_computing_sovereignty_hybrid_microchip_capacity"
    )
    sovereign = _named_block(
        strategy, "SOV_computing_sovereignty_sovereign_microchip_capacity"
    )

    assert "is_special_project_completed = sp:sp_microchip_production" in bootstrap
    assert "id = microchip_production_1 value = 100" in bootstrap
    assert "microchip_plant_total < 4" in hybrid
    assert "id = microchip_plant value = 50" in hybrid
    assert "microchip_plant_total < 8" in sovereign
    assert "id = microchip_plant value = 75" in sovereign
    assert "CAT_microchips = 18.0" in focuses
    assert "CAT_computing_tech = 8.0" in focuses
    assert "CAT_microchips = 8.0" in focuses


def test_manifest_registers_the_national_ecosystem_contract():
    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(
        item
        for item in manifest["chains"]
        if item["root"] == "SOV_computing_sovereignty"
    )

    assert chain["name"] == "Russian Computing Sovereignty"
    assert chain["tag"] == "SOV"
    assert chain["namespace"] == "SOV_computing_sovereignty_events"
    assert chain["tier"] == 1
    assert set(chain["variables"]) == set(AXES) | BOUNDED_AUXILIARY_STATE
    assert all(
        bounds == {"min": 0, "max": 10} for bounds in chain["variables"].values()
    )
    assert set(chain["outcome_ideas"]) == OUTCOMES
    assert set(chain["allowed_reads"]) == ALLOWED_READS
    assert chain["monthly_driver"] == "SOV_corporate_history_monthly_outcomes"
    assert chain["terminal_marker"] == "SOV_computing_sovereignty_reconstruct_complete"
    assert chain["expected_callers"] == {}


def test_processor_event_tooltips_condition_deployability_on_foundry_routes():
    localisation = LOCALISATION_PATH.read_text(encoding="utf-8-sig")
    tooltip_values = dict(
        re.findall(
            r'(?m)^ (SOV_computing_sovereignty_events\.(?:6|11)\.a_tt): "([^"]+)"$',
            localisation,
        )
    )

    expected_capacity = {
        "SOV_computing_sovereignty_events.6.a_tt": "Domestic 28 nm Capacity",
        "SOV_computing_sovereignty_events.11.a_tt": "Domestic 16 nm Capacity",
    }
    assert tooltip_values.keys() == expected_capacity.keys()
    for key, capacity in expected_capacity.items():
        tooltip = tooltip_values[key]
        assert "becomes deployable only when" in tooltip
        assert capacity in tooltip
        assert "valid external foundry route" in tooltip
        assert "Without either" in tooltip
        assert "Makes the Elbrus" not in tooltip


def test_english_localisation_inventory_and_encoding():
    raw = LOCALISATION_PATH.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    localisation = raw.decode("utf-8-sig")
    keys = re.findall(r"(?m)^ ([^:#\r\n]+):", localisation)
    key_counts = {key: keys.count(key) for key in set(keys)}

    events = EVENTS_PATH.read_text(encoding="utf-8")
    technologies = TECHNOLOGIES_PATH.read_text(encoding="utf-8")
    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    scripted_localisation = SCRIPTED_LOCALISATION_PATH.read_text(encoding="utf-8")
    gui = TECH_TREE_GUI_PATH.read_text(encoding="utf-8")

    expected = set(
        re.findall(
            r"(?:title|desc|name|custom_effect_tooltip)\s*=\s*"
            r"(SOV_computing_sovereignty(?:_events)?\.[A-Za-z0-9_.]+|"
            r"SOV_computing_sovereignty_[A-Za-z0-9_]+)",
            events,
        )
    )
    expected.update(
        re.findall(
            r"\bcustom_effect_tooltip\s*=\s*"
            r"(SOV_computing_sovereignty_[A-Za-z0-9_]+)",
            technologies + "\n" + decisions,
        )
    )
    expected.update(
        re.findall(
            r"\blocalization_key\s*=\s*" r"(SOV_computing_sovereignty_[A-Za-z0-9_]+)",
            scripted_localisation,
        )
    )
    expected.update(re.findall(r'text\s*=\s*"(SOV_COMPUTING_[A-Za-z0-9_]+)"', gui))
    expected.update(
        {
            "SOV_computing_sovereignty_category",
            "SOV_computing_sovereignty_category_desc",
            "SOV_computing_sovereignty_folder",
            "SOV_computing_sovereignty_folder_desc",
        }
    )
    for technology in TECHNOLOGIES:
        expected.update({technology, f"{technology}_desc"})
    idea_ids = set(
        re.findall(
            r"(?m)^\t\t(SOV_computing_sovereignty_[A-Za-z0-9_]+)\s*=\s*\{",
            ideas,
        )
    )
    decision_ids = set(
        re.findall(
            r"(?m)^\t(SOV_computing_sovereignty_[A-Za-z0-9_]+)\s*=\s*\{",
            decisions,
        )
    )
    for object_id in idea_ids | decision_ids:
        expected.update({object_id, f"{object_id}_desc"})

    for key in expected:
        assert key_counts.get(key) == 1
    actual_system_keys = {
        key
        for key in key_counts
        if key.startswith("SOV_computing_sovereignty")
        or key.startswith("SOV_COMPUTING_")
    }
    assert actual_system_keys == expected
    assert "allowed = { original_tag = SOV }" in DECISION_CATEGORY_PATH.read_text(
        encoding="utf-8"
    )

    new_lines = [
        line
        for line in localisation.splitlines()
        if "SOV_computing_sovereignty" in line or "SOV_COMPUTING_" in line
    ]
    assert new_lines
    assert "—" not in "\n".join(new_lines)
