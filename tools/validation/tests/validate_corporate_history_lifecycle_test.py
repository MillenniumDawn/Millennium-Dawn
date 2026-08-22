"""Regression tests for Corporate History rule-mode and lifecycle checks."""

from .corporate_history_contract_support_test import (
    Validator,
    _build_fixture,
    _enable_economic_layer_fixture,
    _enable_reusable_lifecycle_fixture,
    _is_repeatable_decision,
    _messages,
    _removes_active_decision,
    json,
    pytest,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("fire_only_once = no", True),
        ("fire_only_once=no", True),
        ("fire_only_once = no # reusable decision", True),
        ("fire_only_once = yes", False),
        ("# fire_only_once = no", False),
        ('log = "fire_only_once = no"', False),
        ('log = "start\nfire_only_once = no\nend"', False),
        ('log = "fire_only_once = no"\nfire_only_once = no', True),
        ("", False),
    ),
)
def test_repeatable_decision_requires_an_active_no_declaration(text, expected):
    assert _is_repeatable_decision(text) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("remove_decision = linux_system_program", True),
        ("remove_decision=linux_system_program", True),
        ("remove_decision = linux_system_other_program", False),
        ("# remove_decision = linux_system_program", False),
        ('log = "remove_decision = linux_system_program"', False),
        ('log = "start\nremove_decision = linux_system_program\nend"', False),
        (
            'log = "remove_decision = linux_system_program"\n'
            "remove_decision = linux_system_program",
            True,
        ),
        ("", False),
    ),
)
def test_active_decision_cleanup_requires_an_executable_removal(text, expected):
    assert _removes_active_decision(text, "linux_system_program") is expected


def _participant_on_actions(tags):
    return {
        tag: (
            "on_actions = {\n"
            f"\ton_monthly_{tag} = {{\n"
            "\t\teffect = { linux_system_monthly_driver = yes }\n"
            "\t}\n"
            "}\n"
        )
        for tag in tags
    }


def _participant_trigger(tags):
    assignments = "".join(f"\t\toriginal_tag = {tag}\n" for tag in tags)
    return f"linux_system_is_participant = {{\n\tOR = {{\n{assignments}\t}}\n}}\n"


def test_schema_v6_requires_participant_tags(tmp_path):
    validator = Validator(str(tmp_path))
    validator._manifest_payload = {"schema_version": 6, "shared_systems": [{}]}
    messages = {
        message for message, _file, _line in validator._validate_shared_systems({}, {})
    }
    assert any("participant_tags" in message for message in messages)


@pytest.mark.parametrize(
    "raw_tags",
    (None, [], ["US"], ["USA", "USA"], ["usa"], [123], [{}]),
)
def test_participant_tags_reject_missing_malformed_or_duplicate_values(raw_tags):
    assert not Validator._participant_tags_are_valid(raw_tags)


def test_participant_dispatch_requires_one_exact_country_host(tmp_path):
    tags = ["BRA", "USA"]
    validator = Validator(str(tmp_path))
    valid = _participant_on_actions(tags)
    assert validator._participant_dispatch_is_exact(
        valid, "linux_system_monthly_driver", tags
    )

    missing = dict(valid)
    del missing["BRA"]
    assert not validator._participant_dispatch_is_exact(
        missing, "linux_system_monthly_driver", tags
    )

    extra = dict(valid)
    extra["CAN"] = _participant_on_actions(["CAN"])["CAN"]
    assert not validator._participant_dispatch_is_exact(
        extra, "linux_system_monthly_driver", tags
    )

    duplicate = dict(valid)
    duplicate["USA"] = duplicate["USA"].replace(
        "linux_system_monthly_driver = yes",
        "linux_system_monthly_driver = yes linux_system_monthly_driver = yes",
    )
    assert not validator._participant_dispatch_is_exact(
        duplicate, "linux_system_monthly_driver", tags
    )

    global_host = dict(valid)
    global_host["USA"] = global_host["USA"].replace("on_monthly_USA", "on_monthly")
    assert not validator._participant_dispatch_is_exact(
        global_host, "linux_system_monthly_driver", tags
    )


def test_participant_trigger_must_match_contract_exactly(tmp_path):
    tags = ["BRA", "USA"]
    validator = Validator(str(tmp_path))
    valid = _participant_trigger(tags)
    assert validator._participant_trigger_is_exact(
        valid, "linux_system_is_participant", tags
    )

    for invalid in (
        _participant_trigger(["USA"]),
        _participant_trigger(["BRA", "CAN", "USA"]),
        _participant_trigger(["BRA", "BRA", "USA"]),
        valid.replace("original_tag = BRA", "tag = BRA"),
        valid.replace("\t}\n}", "\thas_country_flag = extra_gate\n\t}\n}"),
    ):
        assert not validator._participant_trigger_is_exact(
            invalid, "linux_system_is_participant", tags
        )


def test_option_mutating_bounded_variable_without_clamp(tmp_path):
    _build_fixture(tmp_path, missing_clamp=True)
    messages = _messages(tmp_path)
    assert any(
        "mutates bounded variables without a later USA_test_clamp_state call" in message
        for message in messages
    )


def test_reconstruction_replaying_treasury(tmp_path):
    _build_fixture(tmp_path, treasury_in_reconstruct=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_reconstruct_history transitively replays treasury changes" in message
        for message in messages
    )


def test_duplicate_reconstruct_complete_producers(tmp_path):
    _build_fixture(tmp_path, duplicate_complete=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_reconstruct_complete has 2 producers" in message
        for message in messages
    )


def test_allowed_duplicate_reconstruct_complete_producers(tmp_path):
    _build_fixture(
        tmp_path,
        duplicate_complete=True,
        allow_multiple_completion_producers=True,
    )
    messages = _messages(tmp_path)
    assert not any(
        "USA_test_reconstruct_complete has 2 producers" in message
        for message in messages
    )


def test_outcome_idea_missing_allowed_civil_war(tmp_path):
    _build_fixture(tmp_path, missing_civil_war=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_outcome_a is missing allowed_civil_war = { always = yes }" in message
        for message in messages
    )


def test_flag_state_chain_needs_no_initialize_or_clamp_effect(tmp_path):
    _build_fixture(
        tmp_path, manifest_overrides={"variables": {}}, drop_state_effects=True
    )
    assert _messages(tmp_path) == []


def test_bounded_state_chain_still_needs_initialize_and_clamp_effects(tmp_path):
    _build_fixture(tmp_path, drop_state_effects=True)
    messages = _messages(tmp_path)
    assert "TestCo is missing its initialization effect" in messages
    assert "TestCo is missing its clamp effect" in messages


def test_reconstruction_that_never_lands_an_outcome_has_no_terminal_resolver(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=(
            "\tif = {\n"
            "\t\tlimit = {\n"
            "\t\t\tdate > 2001.2.1\n"
            "\t\t\tNOT = { has_country_flag = USA_test_branch_a }\n"
            "\t\t}\n"
            "\t\tset_country_flag = USA_test_branch_a\n"
            "\t}\n"
            "\tif = {\n"
            "\t\tlimit = { date > 2001.3.1 }\n"
            "\t\tset_country_flag = USA_test_reconstruct_complete\n"
            "\t}\n"
        ),
    )
    assert _messages(tmp_path) == ["TestCo is missing a terminal resolver effect"]


def test_capstone_cleanup_may_live_in_the_event_option(tmp_path):
    _build_fixture(tmp_path, cleanup_in_option=True)
    assert _messages(tmp_path) == []


def test_chain_without_any_capstone_cleanup_is_reported(tmp_path):
    _build_fixture(tmp_path, drop_cleanup_effect=True)
    assert _messages(tmp_path) == [
        "TestCo is missing a mutually exclusive cleanup effect"
    ]


def test_game_rule_requires_all_three_modes(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/game_rules/00_game_rules.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\toption = { name = disabled }\n", ""
        ),
        encoding="utf-8",
    )
    assert any(
        "must define Full, Outcomes Only, and Disabled" in message
        for message in _messages(tmp_path)
    )


def test_multiply_variable_without_clamp_is_rejected(tmp_path):
    _build_fixture(tmp_path, missing_clamp=True)
    path = tmp_path / "events/USA_test_events.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "add_to_variable = { USA_test_state = 1 }",
            "multiply_variable = { USA_test_state = 2 }",
        ),
        encoding="utf-8",
    )
    assert any(
        "mutates bounded variables without a later USA_test_clamp_state call" in message
        for message in _messages(tmp_path)
    )


def test_transitive_reconstruction_reward_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    text = path.read_text(encoding="utf-8").replace(
        "USA_test_reconstruct_history = {\n",
        "USA_test_reconstruct_history = {\n\tUSA_test_reward_helper = yes\n",
    )
    text += "\nUSA_test_reward_helper = {\n\tmodify_treasury_effect = yes\n}\n"
    path.write_text(text, encoding="utf-8")
    assert any(
        "transitively replays treasury changes through USA_test_reward_helper"
        in message
        for message in _messages(tmp_path)
    )


def test_cleanup_must_remove_every_declared_outcome(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("\t\tUSA_test_outcome_b\n", ""),
        encoding="utf-8",
    )
    assert any(
        "TestCo is missing a mutually exclusive cleanup effect" in message
        for message in _messages(tmp_path)
    )


def test_manifest_v2_requires_lifecycle_fields(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["chains"][0]["terminal_date"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any(
        "is missing required fields: terminal_date" in message
        for message in _messages(tmp_path)
    )


def test_standard_indirect_clamp_matches_manifest_bounds(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "clamp_variable = { var = USA_test_state min = 0 max = 10 }",
            "set_temp_variable = { corp_value = USA_test_state }\n"
            "\tcorporate_history_clamp_value = yes\n"
            "\tset_variable = { USA_test_state = corp_value }",
        ),
        encoding="utf-8",
    )
    assert not any(
        "must clamp USA_test_state to manifest bounds" in message
        for message in _messages(tmp_path)
    )


def test_nonstandard_indirect_temp_clamp_matches_manifest_bounds(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={"variables": {"USA_test_state": {"min": 0, "max": 7}}},
    )
    path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    text = path.read_text(encoding="utf-8").replace(
        "clamp_variable = { var = USA_test_state min = 0 max = 10 }",
        "USA_test_validate_registers = yes",
    )
    text += (
        "\nUSA_test_validate_registers = {\n"
        "\tset_temp_variable = { corp_value = USA_test_state }\n"
        "\tclamp_temp_variable = { var = corp_value min = 0 max = 7 }\n"
        "\tset_variable = { USA_test_state = corp_value }\n"
        "}\n"
    )
    path.write_text(text, encoding="utf-8")
    assert not any(
        "must clamp USA_test_state to manifest bounds" in message
        for message in _messages(tmp_path)
    )


def test_reconstruction_may_call_hidden_integration_event(tmp_path):
    _build_fixture(tmp_path)
    events_path = tmp_path / "events/USA_test_events.txt"
    events_path.write_text(
        events_path.read_text(encoding="utf-8") + "\ncountry_event = {\n"
        "\tid = USA_test_events.91\n"
        "\thidden = yes\n"
        "\tis_triggered_only = yes\n"
        "\timmediate = { set_country_flag = USA_test_hidden_integrated }\n"
        "}\n",
        encoding="utf-8",
    )
    effects_path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8").replace(
            "USA_test_reconstruct_history = {\n",
            "USA_test_reconstruct_history = {\n\tcountry_event = USA_test_events.91\n",
        ),
        encoding="utf-8",
    )
    assert not any(
        "transitively fires an event" in message for message in _messages(tmp_path)
    )


def test_auxiliary_completion_marker_has_declared_ownership(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["auxiliary_completion_markers"] = [
        "USA_test_aux_reconstruct_complete"
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    effects_path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8") + "\nUSA_test_aux_complete = {\n"
        "\tset_country_flag = USA_test_aux_reconstruct_complete\n"
        "}\n",
        encoding="utf-8",
    )
    core_path = tmp_path / "common/scripted_effects/00_corporate_history_effects.txt"
    core_path.write_text(
        core_path.read_text(encoding="utf-8").replace(
            "NOT = { has_country_flag = USA_test_reconstruct_complete }",
            "NOT = { has_country_flag = USA_test_reconstruct_complete }\n"
            "\t\t\tNOT = { has_country_flag = USA_test_aux_reconstruct_complete }",
        ),
        encoding="utf-8",
    )
    assert not any(
        "USA_test_aux_reconstruct_complete has 0 owning chains" in message
        for message in _messages(tmp_path)
    )


def test_manifest_terminal_date_matches_scripted_completion_guard(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["terminal_date"] = "2001-03-02"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "terminal marker USA_test_reconstruct_complete must use date > 2001.3.2"
        in message
        for message in _messages(tmp_path)
    )


def test_real_options_tier_family_requires_cleanup(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    text = path.read_text(encoding="utf-8").replace(
        "\t\t\tremove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }\n",
        "",
    )
    text = text.replace(
        "\t\tremove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }\n",
        "",
    )
    path.write_text(text, encoding="utf-8")

    assert any(
        "never clears dynamic modifier USA_oem_investment_climate_1" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_duration_must_match_contract(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("days = 180", "days = 730", 1),
        encoding="utf-8",
    )

    assert any(
        "must add USA_oem_program_1 once for 180 days" in message
        for message in _messages(tmp_path)
    )


def test_reusable_temporary_program_cannot_exceed_365_days(tmp_path):
    _build_fixture(tmp_path)
    _enable_reusable_lifecycle_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["reusable_decision_lifecycles"][0]["programs"][0]["active_days"] = 730
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "USA_oem_policy_1 temporary program must last 1 to 365 days" in message
        for message in _messages(tmp_path)
    )


def test_reusable_program_localisation_must_match_duration(tmp_path):
    _build_fixture(tmp_path)
    _enable_reusable_lifecycle_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    path.write_text(
        path.read_text(encoding="utf-8-sig").replace(
            "Runs for 180 days.", "Runs for 730 days.", 1
        ),
        encoding="utf-8-sig",
    )

    messages = _messages(tmp_path)
    assert any(
        "USA_oem_policy_1_desc must state 180 days" in message for message in messages
    )
    assert any(
        "USA_oem_policy_1_desc still claims a 730-day lifecycle" in message
        for message in messages
    )


def test_reusable_program_reenable_period_must_equal_active_duration(tmp_path):
    _build_fixture(tmp_path)
    _enable_reusable_lifecycle_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["reusable_decision_lifecycles"][0]["programs"][0]["cooldown_days"] = 365
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "USA_oem_policy_1 re-enable period must equal its active duration" in message
        for message in _messages(tmp_path)
    )


def test_long_construction_timer_requires_a_manifest_reason(tmp_path):
    _build_fixture(tmp_path)
    _enable_reusable_lifecycle_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    program = manifest["reusable_decision_lifecycles"][0]["programs"][0]
    program.update(
        {
            "kind": "construction_project",
            "active_days": 0,
            "cooldown_days": 180,
            "mission": "USA_oem_policy_2",
            "project_days": 730,
        }
    )
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "USA_oem_policy_1 construction timer over 365 days needs a reason" in message
        for message in _messages(tmp_path)
    )


def test_major_policy_program_duration_must_match_contract(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("days = 365", "days = 180", 1),
        encoding="utf-8",
    )

    assert any(
        "must add USA_oem_program_2 once for 365 days" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_cooldown_must_match_contract(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "days_re_enable = 180", "days_re_enable = 365", 1
        ),
        encoding="utf-8",
    )

    assert any(
        "USA_oem_policy_1 must declare a 180-day cooldown" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_must_remain_reusable(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("\n\tfire_only_once = no\n", "", 1),
        encoding="utf-8",
    )

    assert any(
        "USA_oem_policy_1 must remain reusable after its declared cooldown" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_must_block_while_active(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "NOT = { has_idea = USA_oem_program_1 }", "always = yes", 1
        ),
        encoding="utf-8",
    )

    assert any(
        "USA_oem_policy_1 must block while USA_oem_program_1 is active" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_is_unavailable_after_collapse(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\t\tNOT = { has_country_flag = collapsed_nation }\n", "", 1
        ),
        encoding="utf-8",
    )

    assert any(
        "USA_oem_policy_1 must be unavailable after national collapse" in message
        for message in _messages(tmp_path)
    )


def test_real_options_cleanup_removes_policy_programs(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("\t\t\tUSA_oem_program_1\n", "", 1),
        encoding="utf-8",
    )

    assert any(
        "Off/collapse cleanup must remove USA_oem_program_1" in message
        for message in _messages(tmp_path)
    )


def test_real_options_requires_program_localisation(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        ' USA_oem_program_1_desc: "Program 1 description."\n', ""
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))

    assert any(
        "Missing English real-options localisation key USA_oem_program_1_desc"
        in message
        for message in _messages(tmp_path)
    )


def test_real_options_helpers_are_mode_neutral(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "corporate_history_enabled = yes",
            "corporate_history_enabled = yes\n\t\t\tcorporate_history_full_enabled = yes",
            1,
        ),
        encoding="utf-8",
    )

    assert any("must be mode-neutral" in message for message in _messages(tmp_path))


def test_real_options_rejects_non_object_policy_programs(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["economic_layers"][0]["policy_programs"] = [None, "invalid", 1, True]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    messages = _messages(tmp_path)
    assert {message for message in messages if "policy_programs[" in message} == {
        f"Test Real Options policy_programs[{index}] must be an object"
        for index in range(4)
    }


def test_schema_v5_requires_reusable_decision_lifecycles(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 5
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "Schema v5 requires reusable_decision_lifecycles" in message
        for message in _messages(tmp_path)
    )
