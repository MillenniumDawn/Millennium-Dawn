"""Regression tests for Corporate History scheduler reachability and owner-local dispatch checks."""

from .corporate_history_contract_support_test import (
    Path,
    _build_fixture,
    _enable_economic_layer_fixture,
    _messages,
    _schema_v6_dispatcher_messages,
    _write,
    json,
)


def test_live_schema_v6_bootstrap_anchors_are_documented_and_unique():
    root = Path(__file__).resolve().parents[3]
    contract = json.loads(
        (root / "tools/corporate_history_contract.json").read_text(encoding="utf-8")
    )
    bootstrap = (
        root
        / "common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt"
    ).read_text(encoding="utf-8")

    expected = {
        "E3": ("USA_e3_events.90", "USA_e3_reconstruct_history = yes"),
        "IBM": ("USA_ibm_events.90", "USA_ibm_reconstruct_history = yes"),
    }
    declared_nineties = {}
    for chain in contract["chains"]:
        for event_id, callers in chain["expected_callers"].items():
            if event_id.endswith(".90"):
                declared_nineties[event_id] = callers

    assert declared_nineties == {
        event_id: ["effect:corporate_history_country_bootstrap"]
        for event_id, _reconstruct in expected.values()
    }
    for name, (event_id, reconstruct) in expected.items():
        assert bootstrap.count(f"country_event = {{ id = {event_id} days = 1 }}") == 1
        event_file = (root / f"events/USA_{name.lower()}_events.txt").read_text(
            encoding="utf-8"
        )
        event_start = event_file.index(f"id = {event_id}")
        next_event = event_file.find("\ncountry_event = {", event_start)
        event_block = event_file[event_start : next_event if next_event > 0 else None]
        assert reconstruct in event_block


def test_visible_event_with_no_caller(tmp_path):
    _build_fixture(tmp_path, include_anchor=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_events.2 has no direct callers" in message for message in messages
    )


def test_duplicate_dispatch_caller(tmp_path):
    _build_fixture(tmp_path, duplicate_dispatch=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_corporate_trigger_year_2001 schedules USA_test_events.1 2 times" in message
        for message in messages
    )


def test_recovery_helper_routed_through_the_scheduler_keeps_the_caller_pair(tmp_path):
    """Lost-delivery recovery must re-enter the scheduler, not fire the event itself.

    Nintendo and AIG recover a missed delivery from their monthly driver. Routing that
    through the current-year scheduler keeps the permitted dispatcher + scheduler pair;
    a helper that queued the event directly would silently become a third caller.
    """
    _build_fixture(
        tmp_path,
        extra_effects=(
            "USA_test_recover_missing_events = {\n"
            "\tif = {\n"
            "\t\tlimit = { NOT = { has_country_flag = USA_test_branch_a } }\n"
            "\t\tUSA_test_schedule_current_year_events = yes\n"
            "\t}\n"
            "}\n"
        ),
    )
    messages = _messages(tmp_path)
    assert not any("multiple direct callers" in message for message in messages)


def test_recovery_helper_firing_the_event_directly_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        extra_effects=(
            "USA_test_recover_missing_events = {\n"
            "\tif = {\n"
            "\t\tlimit = { NOT = { has_country_flag = USA_test_branch_a } }\n"
            "\t\tcountry_event = { id = USA_test_events.1 days = 5 }\n"
            "\t}\n"
            "}\n"
        ),
    )
    messages = _messages(tmp_path)
    assert any(
        "USA_test_events.1 has multiple direct callers" in message
        for message in messages
    )


def test_tier_one_missing_hidden_ninety(tmp_path):
    _build_fixture(tmp_path, include_hidden_ninety=False)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_events.90 is missing or not hidden and "
        "USA_test_reconstruct_history is not called directly from "
        "corporate_history_on_startup" in message
        for message in messages
    )


def test_tier_one_startup_reconstruct_replaces_hidden_ninety(tmp_path):
    _build_fixture(tmp_path, include_hidden_ninety=False, startup_reconstructs=True)
    assert _messages(tmp_path) == []


def test_tier_one_missing_monthly_outcomes_registration(tmp_path):
    _build_fixture(tmp_path, monthly_registration=False)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_reconstruct_history is not called from USA_corporate_history_monthly_outcomes"
        in message
        for message in messages
    )


def test_valid_minimal_tier_one_fixture(tmp_path):
    _build_fixture(tmp_path)
    assert _messages(tmp_path) == []


def test_startup_driver_requires_exactly_one_on_action_caller(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/on_actions/MD_event_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "on_new_term = { effect = { corporate_history_on_startup = yes } }\n",
        encoding="utf-8",
    )
    assert any(
        "corporate_history_on_startup requires exactly one on-action caller; found 2"
        in message
        for message in _messages(tmp_path)
    )


def test_monthly_driver_requires_matching_on_action_caller(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/on_actions/MD_event_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "on_monthly_USA = { effect = { USA_corporate_history_monthly_outcomes = yes } }\n",
            "",
        ),
        encoding="utf-8",
    )
    assert any(
        "USA_corporate_history_monthly_outcomes requires exactly one matching on-monthly caller; found 0"
        in message
        for message in _messages(tmp_path)
    )


def test_hidden_event_without_a_caller_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _write(
        tmp_path,
        "events/USA_test_events_extension.txt",
        """country_event = {
\tid = USA_test_events.91
\thidden = yes
\tis_triggered_only = yes
\timmediate = { set_country_flag = USA_test_hidden_resolved }
}
""",
    )
    assert any(
        "USA_test_events.91 has no direct callers" in message
        for message in _messages(tmp_path)
    )


def test_manifest_expected_callers_are_exact(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["expected_callers"] = {
        "USA_test_events.1": ["effect:wrong_owner"]
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any(
        "USA_test_events.1 callers differ from the manifest" in message
        for message in _messages(tmp_path)
    )


def test_dispatcher_requires_the_matching_trigger_year_caller(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/00_yearly_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "trigger_year_2001_events", "trigger_year_2002_events"
        ),
        encoding="utf-8",
    )
    assert any(
        "USA_corporate_trigger_year_2001 must be called by trigger_year_2001_events"
        in message
        for message in _messages(tmp_path)
    )


def test_schema_v6_dispatcher_requires_central_monthly_year_owner(tmp_path):
    _build_fixture(tmp_path)

    messages = _schema_v6_dispatcher_messages(tmp_path)

    assert any(
        "USA_corporate_trigger_year_2001 must be called by "
        "corporate_history_dispatch_year_2001" in message
        for message in messages
    )


def test_schema_v6_dispatcher_accepts_central_monthly_year_owner(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/00_yearly_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "trigger_year_2001_events = {\n"
            "\tUSA_corporate_trigger_year_2001 = yes\n"
            "}",
            "trigger_year_2001_events = {\n"
            "\tcorporate_history_dispatch_year_2001 = yes\n"
            "}\n\n"
            "corporate_history_dispatch_year_2001 = {\n"
            "\tUSA_corporate_trigger_year_2001 = yes\n"
            "}",
        ),
        encoding="utf-8",
    )

    messages = _schema_v6_dispatcher_messages(tmp_path)

    assert not any(
        "USA_corporate_trigger_year_2001 requires exactly one yearly-dispatch caller"
        in message
        or "USA_corporate_trigger_year_2001 must be called by" in message
        for message in messages
    )


def test_dispatcher_event_calls_must_be_inside_the_full_gate(tmp_path):
    _build_fixture(tmp_path)
    path = (
        tmp_path / "common/scripted_effects/00_corporate_history_dispatch_effects.txt"
    )
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\t\t\tcorporate_history_full_enabled = yes\n", ""
        ),
        encoding="utf-8",
    )
    assert any(
        "schedules events outside its corporate_history_full_enabled branch" in message
        for message in _messages(tmp_path)
    )


def test_startup_driver_accepts_one_hop_on_action_caller(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/on_actions/MD_event_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "corporate_history_on_startup = yes", "startup_events = yes"
        ),
        encoding="utf-8",
    )
    assert not any(
        "corporate_history_on_startup requires exactly one on-action caller" in message
        for message in _messages(tmp_path)
    )


def test_reconstruction_rejects_visible_event_replay(tmp_path):
    _build_fixture(tmp_path)
    effects_path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8").replace(
            "USA_test_reconstruct_history = {\n",
            "USA_test_reconstruct_history = {\n\tcountry_event = USA_test_events.1\n",
        ),
        encoding="utf-8",
    )
    assert any(
        "transitively fires an event" in message for message in _messages(tmp_path)
    )


def test_manifest_scheduler_requirement_matches_full_start_strategy(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["full_start_strategies"].remove("current_year_scheduler")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "requires_current_year_scheduler disagrees with full_start_strategies"
        in message
        for message in _messages(tmp_path)
    )


def test_real_options_rejects_direct_on_action_hook(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/on_actions/MD_event_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\non_daily_USA = { effect = { USA_oem_update_real_options_economy = yes } }\n",
        encoding="utf-8",
    )

    assert any(
        "must be reached through the economic bridge, not an on-action" in message
        for message in _messages(tmp_path)
    )


def test_real_options_requires_monthly_bridge_reachability(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\tUSA_oem_update_real_options_economy = yes\n", "", 1
        ),
        encoding="utf-8",
    )

    assert any(
        "must call USA_oem_update_real_options_economy exactly once" in message
        for message in _messages(tmp_path)
    )
