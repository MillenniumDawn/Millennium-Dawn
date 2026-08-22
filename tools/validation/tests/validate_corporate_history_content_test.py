"""Regression tests for Corporate History content and integration checks."""

from .corporate_history_contract_support_test import (
    _build_fixture,
    _enable_bridge_fixture,
    _enable_economic_layer_fixture,
    _messages,
    _write,
    json,
    pytest,
)


def test_explicitly_allowed_custom_anchor(tmp_path):
    _build_fixture(tmp_path, include_anchor=True, callerless=["USA_test_events.2"])
    messages = _messages(tmp_path)
    assert not any(
        "USA_test_events.2 has no direct callers" in message for message in messages
    )


def test_declared_cross_chain_read_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={
            "with_other_chain": True,
            "allowed_reads": ["USA_other_qnx_stack"],
        },
        cross_chain_reads=["USA_other_qnx_stack"],
    )
    assert _messages(tmp_path) == []


def test_cross_chain_exception_does_not_cover_prefix_neighbours(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={
            "with_other_chain": True,
            "allowed_reads": ["USA_other_qnx_stack"],
        },
        cross_chain_reads=["USA_other_qnx_stack", "USA_other_qnx_stack_v2"],
    )
    assert _messages(tmp_path) == [
        "TestCo has undeclared cross-chain read-only AI/flavour use of "
        "USA_other_qnx_stack_v2, owned by OtherCo"
    ]


def test_declared_cross_chain_scripted_trigger_read_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={
            "with_other_chain": True,
            "allowed_reads": ["USA_other_administration"],
        },
        cross_chain_trigger_reads=["USA_other_administration"],
    )
    assert _messages(tmp_path) == []


def test_undeclared_cross_chain_scripted_trigger_read_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        callerless=["USA_test_events.91"],
        manifest_overrides={"with_other_chain": True},
        cross_chain_trigger_reads=["USA_other_administration"],
    )
    assert _messages(tmp_path) == [
        "TestCo has undeclared cross-chain read-only AI/flavour use of "
        "USA_other_administration, owned by OtherCo"
    ]


def test_cross_chain_effect_call_remains_a_write(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={
            "with_other_chain": True,
            "allowed_reads": ["USA_other_administration"],
        },
        cross_chain_effect_calls=["USA_other_administration"],
    )
    assert _messages(tmp_path) == [
        "TestCo writes USA_other_administration, owned by OtherCo, "
        "outside declared exceptions"
    ]


def test_cross_chain_read_in_split_namespace_file_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        callerless=["USA_test_events.91"],
        manifest_overrides={
            "with_other_chain": True,
            "other_callerless": ["USA_other_events.91"],
        },
    )
    _write(
        tmp_path,
        "events/USA_test_events_extension.txt",
        """country_event = {
\tid = USA_test_events.91
\thidden = yes
\tis_triggered_only = yes
\ttrigger = { has_country_flag = USA_other_platform }
}
""",
    )
    assert _messages(tmp_path) == [
        "TestCo has undeclared cross-chain read-only AI/flavour use of "
        "USA_other_platform, owned by OtherCo"
    ]


def test_events_sharing_a_file_are_checked_under_their_own_namespaces(tmp_path):
    _build_fixture(
        tmp_path,
        callerless=["USA_test_events.91"],
        manifest_overrides={
            "with_other_chain": True,
            "other_callerless": ["USA_other_events.91"],
        },
    )
    _write(
        tmp_path,
        "events/shared_events.txt",
        """country_event = {
\tid = USA_test_events.91
\thidden = yes
\tis_triggered_only = yes
\timmediate = { set_country_flag = USA_test_platform }
}

country_event = {
\tid = USA_other_events.91
\thidden = yes
\tis_triggered_only = yes
\timmediate = { set_country_flag = USA_other_platform }
}
""",
    )
    assert _messages(tmp_path) == []


def test_duplicate_manifest_identity_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"].append(dict(manifest["chains"][0]))
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    messages = _messages(tmp_path)
    assert "Manifest name TestCo is declared 2 times" in messages
    assert "Manifest namespace USA_test_events is declared 2 times" in messages
    assert "Manifest root USA_test is declared 2 times" in messages


def test_full_trigger_must_exclude_disabled(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_triggers/MD_corporate_history_triggers.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\tNOT = { has_game_rule = { rule = rule_corporate_history option = disabled } }\n",
            "",
        ),
        encoding="utf-8",
    )
    assert any(
        "corporate_history_full_enabled does not exclude disabled" in message
        for message in _messages(tmp_path)
    )


def test_cross_chain_event_call_is_a_declared_write(tmp_path):
    _build_fixture(tmp_path, manifest_overrides={"with_other_chain": True})
    path = tmp_path / "events/USA_test_events.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\t\tname = USA_test_events.1.a\n",
            "\t\tname = USA_test_events.1.a\n"
            "\t\tcountry_event = { id = USA_other_events.1 days = 1 }\n",
        ),
        encoding="utf-8",
    )
    assert any(
        "TestCo writes USA_other_events, owned by OtherCo" in message
        for message in _messages(tmp_path)
    )


def test_explicit_preview_policy_requires_option_tooltip(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["effect_preview_policy"] = "explicit"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any(
        "USA_test_events.1.a requires exact custom_effect_tooltip = USA_test_events.1.a_tt"
        in message
        for message in _messages(tmp_path)
    )


def test_oem_localisation_requires_utf8_bom(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig")
    path.write_text(text, encoding="utf-8")
    assert any(
        "English OEM localisation file is missing a UTF-8 BOM" in message
        for message in _messages(tmp_path)
    )


def test_shared_english_localisation_key_resolves_outside_owned_prefix(tmp_path):
    _build_fixture(tmp_path)
    events_path = tmp_path / "events/USA_test_events.txt"
    events_path.write_text(
        events_path.read_text(encoding="utf-8").replace(
            "title = USA_test_events.1.t", "title = SHARED_CORPORATE_TITLE"
        ),
        encoding="utf-8",
    )
    loc_path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    loc_path.write_bytes(
        loc_path.read_bytes() + b' SHARED_CORPORATE_TITLE: "Shared title"\n'
    )
    assert not any(
        "Missing English corporate-history localisation key SHARED_CORPORATE_TITLE"
        in message
        for message in _messages(tmp_path)
    )


def test_bridge_contribution_requires_immediate_refresh(tmp_path):
    _build_fixture(tmp_path)
    _enable_bridge_fixture(tmp_path, refresh="missing")
    assert any(
        "changes a USA bridge contribution without an immediate refresh" in message
        for message in _messages(tmp_path)
    )


def test_bridge_accepts_transitive_immediate_refresh(tmp_path):
    _build_fixture(tmp_path)
    _enable_bridge_fixture(tmp_path, refresh="transitive")
    assert not any(
        "changes a USA bridge contribution without an immediate refresh" in message
        for message in _messages(tmp_path)
    )


def test_valid_real_options_contract_fixture(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)

    assert not any("real-options" in message.lower() for message in _messages(tmp_path))


def test_real_options_requires_one_authoritative_updater(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\nUSA_oem_update_real_options_economy = { always = yes }\n",
        encoding="utf-8",
    )

    assert any(
        "requires exactly one authoritative updater" in message
        for message in _messages(tmp_path)
    )


def test_real_options_rejects_unsupported_script_math_operator(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "set_temp_variable = { USA_oem_cdf_output = 0.5 }",
            "set_temp_variable = { USA_oem_cdf_output = 0.5 exp = 2 }",
        ),
        encoding="utf-8",
    )

    assert any(
        "uses unsupported scripted math operator exp" in message
        for message in _messages(tmp_path)
    )


def test_real_options_dashboard_reads_authoritative_outputs(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        "USA_oem_option_value_display", "USA_oem_stale_value_display"
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))

    assert any(
        "dashboard does not read authoritative output USA_oem_option_value_display"
        in message
        for message in _messages(tmp_path)
    )


def test_real_options_rejects_company_owned_writes(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "set_country_flag = USA_oem_real_options_initialized",
            "set_country_flag = USA_oem_real_options_initialized\n"
            "\t\tset_variable = { USA_test_state = 5 }",
            1,
        ),
        encoding="utf-8",
    )

    assert any(
        "writes company-owned variable USA_test_state" in message
        for message in _messages(tmp_path)
    )


def test_real_options_rejects_undeclared_persistent_writes(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "set_country_flag = USA_oem_real_options_initialized",
            "set_country_flag = USA_oem_real_options_initialized\n"
            "\t\tset_variable = { USA_oem_untracked_state = 5 }",
            1,
        ),
        encoding="utf-8",
    )

    assert any(
        "writes undeclared persistent variable USA_oem_untracked_state" in message
        for message in _messages(tmp_path)
    )


def test_real_options_requires_bounded_cdf_output(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\t\tclamp_temp_variable = { var = USA_oem_cdf_output min = 0 max = 1 }\n",
            "",
        ),
        encoding="utf-8",
    )

    assert any(
        "CDF output must clamp to 0..1" in message for message in _messages(tmp_path)
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    (("knots", "0.5"), ("values", None), ("values", True)),
)
def test_real_options_rejects_nonnumeric_cdf_elements(tmp_path, field, replacement):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["economic_layers"][0]["cdf"][field][1] = replacement
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "CDF knots and values must contain only finite numbers" in message
        for message in _messages(tmp_path)
    )


@pytest.mark.parametrize("replacement", ("40", None, True, float("nan")))
def test_real_options_rejects_invalid_modifier_thresholds(tmp_path, replacement):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    family = manifest["economic_layers"][0]["modifier_families"][0]
    family["thresholds"] = [20, replacement]
    family["members"].append("USA_oem_investment_climate_3")
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "modifier family investment_climate thresholds must contain only finite numbers"
        in message
        for message in _messages(tmp_path)
    )


def test_schema_v4_requires_shared_systems(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 4
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "Schema v4 requires a non-empty shared_systems list" in message
        for message in _messages(tmp_path)
    )


def test_schema_v6_requires_independent_subsystems(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 6
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "Schema v6 requires a non-empty independent_subsystems list" in message
        for message in _messages(tmp_path)
    )


def test_schema_v4_rejects_incomplete_shared_system_declarations(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 4
    manifest["shared_systems"] = [{}]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "shared_systems[0] is missing required fields" in message
        for message in _messages(tmp_path)
    )
