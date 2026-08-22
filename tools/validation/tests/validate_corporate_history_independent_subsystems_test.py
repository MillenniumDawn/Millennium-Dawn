import json
from pathlib import Path

import pytest
from validate_corporate_history_contract import Validator


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _chain() -> dict:
    return {
        "name": "Fixture chain",
        "tag": "USA",
        "namespace": "fixture_events",
        "root": "USA_fixture",
        "tier": 2,
        "owned_prefixes": ["USA_fixture"],
        "variables": {},
        "outcome_idea_prefixes": [],
        "requires_current_year_scheduler": False,
        "allow_yearly_scheduler_duplicates": False,
        "callerless_anchors": [],
        "allowed_multiple_callers": [],
        "allowed_reads": [],
        "allowed_writes": [],
        "full_start_strategies": [],
        "outcomes_only_strategy": "suppressed",
        "monthly_driver": "USA_fixture_monthly_driver",
        "terminal_marker": "USA_fixture_complete",
        "terminal_date": "2000.1.1",
        "outcome_ideas": [],
        "expected_callers": {},
        "dependency_order": [],
        "localisation_prefixes": ["USA_fixture"],
        "effect_preview_policy": "engine_or_explicit",
        "bridge_refresh_policy": "none",
    }


def _subsystems() -> list[dict]:
    return [
        {
            "id": "cross_tag_gpu_development",
            "kind": "cross_tag_event_system",
            "namespaces": ["gpu_test"],
            "event_ids": ["gpu_test.1"],
            "owner_tags": ["USA", "CAN"],
            "reconstruction_effects": ["gpu_test_reconstruct"],
            "scheduler_entrypoints": ["gpu_test_schedule"],
            "effect_roots": ["gpu_test_monthly_driver"],
            "mode_policy": "full_events_outcomes_reconstruct_off_inert",
        },
        {
            "id": "israel_oem_historical_flavour",
            "kind": "country_event_system",
            "namespaces": ["ISR_test"],
            "event_ids": ["ISR_test.1"],
            "owner_tags": ["ISR"],
            "reconstruction_effects": ["ISR_test_reconstruct"],
            "scheduler_entrypoints": ["ISR_test_schedule"],
            "effect_roots": ["ISR_test_monthly_driver"],
            "mode_policy": "full_events_outcomes_reconstruct_off_inert",
        },
        {
            "id": "legacy_usa_oem_storage_history",
            "kind": "country_event_system",
            "namespaces": ["USA_test"],
            "event_ids": ["USA_test.1"],
            "owner_tags": ["USA"],
            "reconstruction_effects": ["USA_test_reconstruct"],
            "scheduler_entrypoints": ["USA_test_schedule"],
            "effect_roots": ["USA_test_monthly_driver"],
            "mode_policy": "full_events_outcomes_reconstruct_off_inert",
        },
        {
            "id": "physical_compute_stack",
            "kind": "derived_aggregate",
            "namespaces": [],
            "event_ids": [],
            "owner_tags": ["USA"],
            "reconstruction_effects": [],
            "scheduler_entrypoints": [],
            "effect_roots": ["USA_physical_compute_stack_resolve"],
            "mode_policy": "derived_only",
        },
    ]


def _build_fixture(root: Path) -> None:
    manifest = {
        "schema_version": 6,
        "independent_subsystems": _subsystems(),
        "chains": [_chain()],
    }
    _write(
        root,
        "tools/corporate_history_contract.json",
        json.dumps(manifest, indent=2),
    )
    _write(
        root,
        "common/on_actions/02_independent_test_on_actions.txt",
        """on_actions = {
	on_monthly_USA = { effect = { gpu_test_monthly_driver = yes USA_test_monthly_driver = yes } }
	on_monthly_CAN = { effect = { gpu_test_monthly_driver = yes } }
	on_monthly_ISR = { effect = { ISR_test_monthly_driver = yes } }
}
""",
    )
    _write(
        root,
        "common/scripted_effects/independent_test_effects.txt",
        """gpu_test_reconstruct = { set_country_flag = gpu_test_reconstructed }
gpu_test_schedule = { country_event = { id = gpu_test.1 days = 1 } }
gpu_test_monthly_driver = {
	if = {
		limit = { corporate_history_enabled = yes }
		gpu_test_reconstruct = yes
		if = {
			limit = { corporate_history_full_enabled = yes }
			gpu_test_schedule = yes
		}
	}
}

ISR_test_reconstruct = { set_country_flag = ISR_test_reconstructed }
ISR_test_schedule = { country_event = { id = ISR_test.1 days = 1 } }
ISR_test_monthly_driver = {
	if = {
		limit = { corporate_history_enabled = yes }
		ISR_test_reconstruct = yes
		if = {
			limit = { corporate_history_full_enabled = yes }
			ISR_test_schedule = yes
		}
	}
}

USA_test_reconstruct = { set_country_flag = USA_test_reconstructed }
USA_test_schedule = { country_event = { id = USA_test.1 days = 1 } }
USA_test_monthly_driver = {
	if = {
		limit = { corporate_history_enabled = yes }
		USA_test_reconstruct = yes
		if = {
			limit = { corporate_history_full_enabled = yes }
			USA_test_schedule = yes
		}
	}
}

USA_physical_compute_stack_resolve = {
	set_variable = { USA_physical_compute_stack_score = 1 }
}
""",
    )
    _write(
        root,
        "events/independent_test_events.txt",
        """add_namespace = gpu_test
add_namespace = ISR_test
add_namespace = USA_test
country_event = { id = gpu_test.1 is_triggered_only = yes }
country_event = { id = ISR_test.1 is_triggered_only = yes }
country_event = { id = USA_test.1 is_triggered_only = yes }
""",
    )


def _validator_findings(root: Path) -> tuple[Validator, list[str]]:
    validator = Validator(str(root), no_color=True)
    chains = validator._load_manifest()
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()
    findings = validator._validate_independent_subsystems(
        validator._independent_subsystems, chains, effect_defs, event_defs
    )
    messages = [issue.message for issue in validator._issues]
    messages.extend(message for message, _file, _line in findings)
    return validator, messages


def test_schema_v6_independent_subsystems_accept_one_local_monthly_owner(tmp_path):
    _build_fixture(tmp_path)

    _validator, messages = _validator_findings(tmp_path)

    assert messages == []


def test_schema_v6_accepts_explicit_hidden_ninety_save_anchor(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    isr = next(
        subsystem
        for subsystem in manifest["independent_subsystems"]
        if subsystem["id"] == "israel_oem_historical_flavour"
    )
    isr["event_ids"].append("ISR_test.90")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    events_path = tmp_path / "events/independent_test_events.txt"
    events_path.write_text(
        events_path.read_text(encoding="utf-8")
        + "country_event = { id = ISR_test.90 hidden = yes is_triggered_only = yes }\n",
        encoding="utf-8",
    )

    _validator, messages = _validator_findings(tmp_path)

    assert messages == []


@pytest.mark.parametrize(
    ("event_id", "hidden"),
    (("ISR_test.90", "no"), ("ISR_test.91", "yes")),
)
def test_schema_v6_rejects_non_compatibility_callerless_events(
    tmp_path, event_id, hidden
):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    isr = next(
        subsystem
        for subsystem in manifest["independent_subsystems"]
        if subsystem["id"] == "israel_oem_historical_flavour"
    )
    isr["event_ids"].append(event_id)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    events_path = tmp_path / "events/independent_test_events.txt"
    events_path.write_text(
        events_path.read_text(encoding="utf-8")
        + f"country_event = {{ id = {event_id} hidden = {hidden} is_triggered_only = yes }}\n",
        encoding="utf-8",
    )

    _validator, messages = _validator_findings(tmp_path)

    assert f"{event_id} has no declared scheduler path" in messages
    assert f"{event_id} is unreachable in Full mode" in messages


def test_schema_v6_reports_missing_and_restored_legacy_usa_contract(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    usa = next(
        subsystem
        for subsystem in manifest["independent_subsystems"]
        if subsystem["id"] == "legacy_usa_oem_storage_history"
    )
    manifest["independent_subsystems"].remove(usa)
    path.write_text(json.dumps(manifest), encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)
    assert any("missing independent subsystems" in message for message in messages)

    manifest["independent_subsystems"].append(usa)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    _validator, messages = _validator_findings(tmp_path)
    assert messages == []


def test_schema_v6_rejects_outcomes_and_off_mode_bypasses(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/independent_test_effects.txt"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "gpu_test_monthly_driver = {\n",
        "gpu_test_monthly_driver = {\n\tgpu_test_reconstruct = yes\n"
        "\tif = { limit = { corporate_history_outcomes_only_enabled = yes } "
        "gpu_test_schedule = yes }\n",
        1,
    )
    path.write_text(text, encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any("gpu_test_reconstruct is reachable in Off mode" in m for m in messages)
    assert any(
        "gpu_test_schedule is reachable in outcomes_only mode" in m for m in messages
    )
    assert any("gpu_test.1 is reachable in outcomes_only mode" in m for m in messages)


def test_schema_v6_explores_else_after_mixed_off_and_runtime_limit(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/independent_test_effects.txt"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "gpu_test_monthly_driver = {\n",
        "gpu_test_monthly_driver = {\n"
        "\tif = { limit = { corporate_history_enabled = no "
        "has_country_flag = gpu_runtime_gate } }\n"
        "\telse = { gpu_test_reconstruct = yes }\n",
        1,
    )
    path.write_text(text, encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any("gpu_test_reconstruct is reachable in Off mode" in m for m in messages)


def test_schema_v6_explores_else_after_mixed_else_if_limit(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/independent_test_effects.txt"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "gpu_test_monthly_driver = {\n",
        "gpu_test_monthly_driver = {\n"
        "\tif = { limit = { corporate_history_full_enabled = yes } }\n"
        "\telse_if = { limit = { corporate_history_outcomes_only_enabled = yes "
        "has_country_flag = gpu_runtime_gate } }\n"
        "\telse = { gpu_test_schedule = yes }\n",
        1,
    )
    path.write_text(text, encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any(
        "gpu_test_schedule is reachable in outcomes_only mode" in m for m in messages
    )


def test_schema_v6_explores_or_with_unresolved_runtime_disjunct(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/independent_test_effects.txt"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "gpu_test_monthly_driver = {\n",
        "gpu_test_monthly_driver = {\n"
        "\tif = {\n"
        "\t\tlimit = {\n"
        "\t\t\tOR = {\n"
        "\t\t\t\tcorporate_history_enabled = yes\n"
        "\t\t\t\thas_country_flag = gpu_runtime_gate\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t\tgpu_test_schedule = yes\n"
        "\t}\n",
        1,
    )
    path.write_text(text, encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any("gpu_test_schedule is reachable in off mode" in m for m in messages)
    assert any("gpu_test.1 is reachable in off mode" in m for m in messages)


def test_schema_v6_rejects_direct_gpu_and_usa_event_dispatch(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/on_actions/02_independent_test_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\ton_monthly_USA = { effect = { gpu_test_monthly_driver = yes USA_test_monthly_driver = yes } }",
            "\ton_monthly_USA = { effect = { gpu_test_monthly_driver = yes "
            "USA_test_monthly_driver = yes country_event = gpu_test.1 "
            "country_event = USA_test.1 } }",
        ),
        encoding="utf-8",
    )

    _validator, messages = _validator_findings(tmp_path)

    assert any("gpu_test.1 is dispatched outside" in message for message in messages)
    assert any("USA_test.1 is dispatched outside" in message for message in messages)


def test_schema_v6_rejects_duplicate_ati_gpu_ownership(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    duplicate = dict(manifest["independent_subsystems"][0])
    duplicate["id"] = "ati_duplicate_gpu_owner"
    duplicate["effect_roots"] = ["CAN_ati_gpu_monthly_driver"]
    duplicate["scheduler_entrypoints"] = ["CAN_ati_gpu_schedule"]
    duplicate["reconstruction_effects"] = ["CAN_ati_gpu_reconstruct"]
    manifest["independent_subsystems"].append(duplicate)
    path.write_text(json.dumps(manifest), encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any(
        "Namespace gpu_test requires exactly one contract owner" in message
        for message in messages
    )
    assert any(
        "Event gpu_test.1 requires exactly one independent subsystem owner" in message
        for message in messages
    )


def test_schema_v6_rejects_missing_scheduler_and_reconstruction_effects(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    gpu = manifest["independent_subsystems"][0]
    gpu["scheduler_entrypoints"] = ["gpu_test_missing_scheduler"]
    gpu["reconstruction_effects"] = ["gpu_test_missing_reconstruction"]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any("effect gpu_test_missing_scheduler; found 0" in m for m in messages)
    assert any("effect gpu_test_missing_reconstruction; found 0" in m for m in messages)


def test_schema_v6_derived_aggregate_cannot_declare_events_or_schedulers(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    physical = manifest["independent_subsystems"][3]
    physical["namespaces"] = ["USA_test"]
    physical["event_ids"] = ["USA_test.1"]
    physical["scheduler_entrypoints"] = ["USA_test_schedule"]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any("is derived-only and must leave" in message for message in messages)


def test_schema_v6_derived_aggregate_requires_exactly_one_root(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["independent_subsystems"][3]["effect_roots"].append(
        "USA_physical_compute_stack_duplicate_resolve"
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    effects_path = tmp_path / "common/scripted_effects/independent_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8")
        + "\nUSA_physical_compute_stack_duplicate_resolve = { }\n",
        encoding="utf-8",
    )

    _validator, messages = _validator_findings(tmp_path)

    assert any("exactly one derived effect root" in message for message in messages)


def test_schema_v6_scans_foreign_writes_through_reachable_helpers(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/independent_test_effects.txt"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "gpu_test_monthly_driver = {\n",
        "gpu_test_foreign_helper = { set_country_flag = ISR_foreign_owned }\n"
        "gpu_test_monthly_driver = {\n\tgpu_test_foreign_helper = yes\n",
        1,
    )
    path.write_text(text, encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any(
        "reaches foreign-owner write ISR_foreign_owned through gpu_test_foreign_helper"
        in message
        for message in messages
    )


def test_schema_v6_rejects_cross_subsystem_event_dispatch(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "events/independent_test_events.txt"
    text = path.read_text(encoding="utf-8").replace(
        "country_event = { id = gpu_test.1 is_triggered_only = yes }",
        "country_event = { id = gpu_test.1 is_triggered_only = yes "
        "immediate = { country_event = USA_test.1 } }",
    )
    path.write_text(text, encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any(
        "USA_test.1 is dispatched outside legacy_usa_oem_storage_history "
        "scheduler entrypoints by gpu_test.1" in message
        for message in messages
    )


def test_schema_v6_accepts_reachable_intra_subsystem_event_dispatch(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["independent_subsystems"][0]["event_ids"].append("gpu_test.2")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    events_path = tmp_path / "events/independent_test_events.txt"
    events_path.write_text(
        events_path.read_text(encoding="utf-8").replace(
            "country_event = { id = gpu_test.1 is_triggered_only = yes }",
            "country_event = { id = gpu_test.1 is_triggered_only = yes "
            "immediate = { country_event = gpu_test.2 } }\n"
            "country_event = { id = gpu_test.2 is_triggered_only = yes }",
        ),
        encoding="utf-8",
    )

    _validator, messages = _validator_findings(tmp_path)

    assert messages == []


def test_schema_v6_accepts_event_effect_event_dispatch_within_subsystem(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["independent_subsystems"][0]["event_ids"].append("gpu_test.2")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    events_path = tmp_path / "events/independent_test_events.txt"
    events_path.write_text(
        events_path.read_text(encoding="utf-8").replace(
            "country_event = { id = gpu_test.1 is_triggered_only = yes }",
            "country_event = { id = gpu_test.1 is_triggered_only = yes "
            "immediate = { gpu_test_event_followup = yes } }\n"
            "country_event = { id = gpu_test.2 is_triggered_only = yes }",
        ),
        encoding="utf-8",
    )
    effects_path = tmp_path / "common/scripted_effects/independent_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8")
        + "\ngpu_test_event_followup = { country_event = gpu_test.2 }\n",
        encoding="utf-8",
    )

    _validator, messages = _validator_findings(tmp_path)

    assert messages == []


def test_schema_v6_rejects_foreign_write_in_declared_event_body(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "events/independent_test_events.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "country_event = { id = gpu_test.1 is_triggered_only = yes }",
            "country_event = { id = gpu_test.1 is_triggered_only = yes "
            "immediate = { set_country_flag = ISR_foreign_owned } }",
        ),
        encoding="utf-8",
    )

    _validator, messages = _validator_findings(tmp_path)

    assert any(
        "cross_tag_gpu_development event gpu_test.1 writes foreign-owner state "
        "ISR_foreign_owned" in message
        for message in messages
    )


def test_schema_v6_rejects_foreign_write_through_event_helper(tmp_path):
    _build_fixture(tmp_path)
    events_path = tmp_path / "events/independent_test_events.txt"
    events_path.write_text(
        events_path.read_text(encoding="utf-8").replace(
            "country_event = { id = gpu_test.1 is_triggered_only = yes }",
            "country_event = { id = gpu_test.1 is_triggered_only = yes "
            "immediate = { gpu_test_event_foreign_helper = yes } }",
        ),
        encoding="utf-8",
    )
    effects_path = tmp_path / "common/scripted_effects/independent_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8")
        + "\ngpu_test_event_foreign_helper = { "
        "set_country_flag = ISR_event_helper_foreign_owned }\n",
        encoding="utf-8",
    )

    _validator, messages = _validator_findings(tmp_path)

    assert any(
        "reaches foreign-owner write ISR_event_helper_foreign_owned through "
        "gpu_test_event_foreign_helper" in message
        for message in messages
    )


def test_schema_v6_rejects_extra_independent_subsystem_fields(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["independent_subsystems"][0]["wildcard_events"] = "gpu_test.*"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    _validator, messages = _validator_findings(tmp_path)

    assert any("unsupported fields: wildcard_events" in message for message in messages)


def _build_monthly_architecture(root: Path) -> Validator:
    dispatchers = "\n".join(
        f"corporate_history_dispatch_year_{year} = {{ }}" for year in range(2000, 2027)
    )
    calls = "\n".join(
        f"\tcorporate_history_dispatch_year_{year} = yes" for year in range(2000, 2027)
    )
    _write(
        root,
        "common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt",
        "corporate_history_country_bootstrap = { }\n"
        "USA_fixture_monthly_driver = { corporate_history_monthly_dispatch = yes }\n"
        + dispatchers
        + "\ncorporate_history_monthly_dispatch = {\n"
        + calls
        + "\n}\n",
    )
    _write(
        root,
        "common/on_actions/99_USA_on_actions.txt",
        "on_actions = { on_monthly_USA = { effect = { "
        "USA_fixture_monthly_driver = yes } } }",
    )
    validator = Validator(str(root), no_color=True)
    validator._manifest_payload = {"schema_version": 6, "chains": [_chain()]}
    return validator


def test_schema_v6_monthly_chronology_needs_no_abk_startup(tmp_path):
    validator = _build_monthly_architecture(tmp_path)
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])

    assert validator._validate_country_local_monthly_architecture(effect_defs) == []


def test_schema_v6_rejects_restored_abk_startup_host(tmp_path):
    validator = _build_monthly_architecture(tmp_path)
    _write(
        tmp_path,
        "common/on_actions/01_oem_corporate_history_on_actions.txt",
        "on_actions = { on_startup = { effect = { ABK = { "
        "corporate_history_monthly_dispatch = yes } } } }",
    )
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    findings = validator._validate_country_local_monthly_architecture(effect_defs)
    messages = [message for message, _file, _line in findings]

    assert any("deprecated ABK OEM startup" in message for message in messages)
    assert any("forbidden host on_startup" in message for message in messages)
    assert any("must not use ABK" in message for message in messages)


def test_schema_v6_rejects_monthly_driver_on_foreign_host(tmp_path):
    validator = _build_monthly_architecture(tmp_path)
    path = tmp_path / "common/on_actions/99_USA_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("on_monthly_USA", "on_monthly_CAN"),
        encoding="utf-8",
    )
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    findings = validator._validate_country_local_monthly_architecture(effect_defs)
    messages = [message for message, _file, _line in findings]

    assert any(
        "requires country-local path on_monthly_USA -> USA_fixture_monthly_driver"
        in message
        for message in messages
    )
    assert any(
        "undeclared country-local path on_monthly_CAN -> USA_fixture_monthly_driver"
        in message
        for message in messages
    )


def _build_core_mode_fixture(root: Path) -> tuple[Validator, list]:
    chain = _chain()
    chain.update(
        {
            "tier": 1,
            "full_start_strategies": [
                "yearly_dispatcher",
                "current_year_scheduler",
                "reconstruction",
            ],
            "outcomes_only_strategy": "reconstruction",
            "requires_current_year_scheduler": True,
            "expected_callers": {
                "fixture_events.1": ["effect:USA_fixture_schedule_current_year_events"],
                "fixture_events.2": ["effect:USA_fixture_event_followup"],
                "fixture_events.90": [],
            },
        }
    )
    manifest = {
        "schema_version": 6,
        "independent_subsystems": _subsystems(),
        "chains": [chain],
    }
    _write(
        root,
        "tools/corporate_history_contract.json",
        json.dumps(manifest, indent=2),
    )
    _write(
        root,
        "common/on_actions/02_core_mode_on_actions.txt",
        """on_actions = {
	on_monthly_USA = {
		effect = {
			corporate_history_monthly_dispatch = yes
			USA_fixture_monthly_driver = yes
		}
	}
}
""",
    )
    _write(
        root,
        "common/scripted_effects/core_mode_effects.txt",
        """corporate_history_country_bootstrap = {
	if = {
		limit = { original_tag = USA }
		USA_fixture_reconstruct_history = yes
		if = {
			limit = { corporate_history_full_enabled = yes }
			USA_fixture_schedule_current_year_events = yes
		}
	}
}

corporate_history_monthly_dispatch = {
	if = {
		limit = { corporate_history_enabled = yes }
		corporate_history_country_bootstrap = yes
	}
}

USA_fixture_reconstruct_history = {
	set_country_flag = USA_fixture_reconstructed
	if = {
		limit = { date > 2000.1.1 }
		set_country_flag = USA_fixture_complete
	}
}
USA_fixture_schedule_current_year_events = {
	country_event = fixture_events.1
}
USA_fixture_event_followup = { country_event = fixture_events.2 }
USA_fixture_monthly_driver = {
	if = {
		limit = {
			corporate_history_enabled = yes
			NOT = { has_country_flag = USA_fixture_complete }
		}
		USA_fixture_reconstruct_history = yes
	}
}
""",
    )
    _write(
        root,
        "events/core_mode_events.txt",
        """add_namespace = fixture_events
country_event = {
	id = fixture_events.1
	is_triggered_only = yes
	immediate = { USA_fixture_event_followup = yes }
}
country_event = { id = fixture_events.2 is_triggered_only = yes }
country_event = { id = fixture_events.90 hidden = yes is_triggered_only = yes }
""",
    )
    validator = Validator(str(root), no_color=True)
    chains = validator._load_manifest()
    return validator, chains


def _core_mode_messages(root: Path) -> list[str]:
    validator, chains = _build_core_mode_fixture(root)
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()
    call_sites = validator._load_event_call_sites(
        event_defs, effect_defs, {"fixture_events"}
    )
    return [
        message
        for message, _file, _line in validator._validate_core_chain_mode_paths(
            chains, effect_defs, event_defs, call_sites
        )
    ]


def test_schema_v6_core_modes_expand_event_effect_event_paths(tmp_path):
    assert _core_mode_messages(tmp_path) == []


def test_schema_v6_core_modes_reject_outcomes_event_delivery(tmp_path):
    _build_core_mode_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/core_mode_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "limit = { corporate_history_full_enabled = yes }",
            "limit = { corporate_history_enabled = yes }",
        ),
        encoding="utf-8",
    )

    validator = Validator(str(tmp_path), no_color=True)
    chains = validator._load_manifest()
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()
    call_sites = validator._load_event_call_sites(
        event_defs, effect_defs, {"fixture_events"}
    )
    messages = [
        message
        for message, _file, _line in validator._validate_core_chain_mode_paths(
            chains, effect_defs, event_defs, call_sites
        )
    ]

    assert any("fixture_events.1 is reachable in outcomes_only" in m for m in messages)
    assert any("fixture_events.2 is reachable in outcomes_only" in m for m in messages)


def test_schema_v6_core_modes_reject_off_reconstruction(tmp_path):
    _build_core_mode_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/core_mode_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "limit = { corporate_history_enabled = yes }",
            "limit = { always = yes }",
            1,
        ),
        encoding="utf-8",
    )

    validator = Validator(str(tmp_path), no_color=True)
    chains = validator._load_manifest()
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()
    call_sites = validator._load_event_call_sites(
        event_defs, effect_defs, {"fixture_events"}
    )
    messages = [
        message
        for message, _file, _line in validator._validate_core_chain_mode_paths(
            chains, effect_defs, event_defs, call_sites
        )
    ]

    assert any(
        "Reconstruction effect USA_fixture_reconstruct_history" in m for m in messages
    )
    assert any("reachable in off mode" in m for m in messages)


def test_schema_v6_core_modes_reject_nonmonthly_host(tmp_path):
    _build_core_mode_fixture(tmp_path)
    path = tmp_path / "common/on_actions/02_core_mode_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("on_monthly_USA", "on_daily_USA"),
        encoding="utf-8",
    )

    validator = Validator(str(tmp_path), no_color=True)
    chains = validator._load_manifest()
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()
    call_sites = validator._load_event_call_sites(
        event_defs, effect_defs, {"fixture_events"}
    )
    messages = [
        message
        for message, _file, _line in validator._validate_core_chain_mode_paths(
            chains, effect_defs, event_defs, call_sites
        )
    ]

    assert any("reached from forbidden host on_daily_USA" in m for m in messages)


def test_schema_v5_core_mode_gate_is_intentionally_unchanged(tmp_path):
    validator, chains = _build_core_mode_fixture(tmp_path)
    validator._manifest_payload["schema_version"] = 5
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()

    assert (
        validator._validate_core_chain_mode_paths(chains, effect_defs, event_defs, {})
        == []
    )


def test_schema_v6_tier_one_uses_country_bootstrap_registration(tmp_path):
    validator, chains = _build_core_mode_fixture(tmp_path)
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()
    messages = [
        message
        for message, _file, _line in validator._validate_tier_one_contract(
            chains, effect_defs, event_defs, {}
        )
    ]

    assert not any("corporate_history_on_startup" in message for message in messages)
    assert not any("country-bootstrap registration" in message for message in messages)
    assert not any(
        "missing its USA registration in corporate_history_country_bootstrap" in message
        for message in messages
    )


def test_schema_v5_tier_one_still_requires_singleton_startup(tmp_path):
    validator, chains = _build_core_mode_fixture(tmp_path)
    validator._manifest_payload["schema_version"] = 5
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()
    messages = [
        message
        for message, _file, _line in validator._validate_tier_one_contract(
            chains, effect_defs, event_defs, {}
        )
    ]

    assert any(
        "corporate_history_on_startup requires exactly one on-action caller; found 0"
        in message
        for message in messages
    )
    assert any(
        "missing startup registration in corporate_history_on_startup" in message
        for message in messages
    )


def test_schema_v6_auxiliary_lifecycle_uses_target_local_bootstrap(tmp_path):
    _build_core_mode_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chain = manifest["chains"][0]
    chain["auxiliary_completion_markers"] = ["USA_fixture_aux_complete"]
    chain["auxiliary_lifecycles"] = [
        {
            "root": "USA_fixture_aux",
            "tag": "USA",
            "reconstruction_effect": "USA_fixture_aux_reconstruct_history",
            "scheduler_effect": "USA_fixture_aux_schedule_current_year_events",
            "monthly_driver": "USA_fixture_aux_monthly_driver",
            "terminal_marker": "USA_fixture_aux_complete",
            "terminal_date": "2001-01-01",
            "expected_yearly_callers": {
                "fixture_aux_events.1": "USA_corporate_trigger_year_2001"
            },
        }
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    effects_path = tmp_path / "common/scripted_effects/core_mode_effects.txt"
    effects = effects_path.read_text(encoding="utf-8")
    effects = effects.replace(
        "\t\tUSA_fixture_reconstruct_history = yes\n",
        "\t\tUSA_fixture_reconstruct_history = yes\n"
        "\t\tUSA_fixture_aux_reconstruct_history = yes\n",
        1,
    ).replace(
        "\t\t\tUSA_fixture_schedule_current_year_events = yes\n",
        "\t\t\tUSA_fixture_schedule_current_year_events = yes\n"
        "\t\t\tUSA_fixture_aux_schedule_current_year_events = yes\n",
        1,
    )
    effects += """
USA_fixture_aux_reconstruct_history = {
	if = {
		limit = { date > 2001.1.1 }
		set_country_flag = USA_fixture_aux_complete
	}
}
USA_fixture_aux_schedule_current_year_events = {
	if = {
		limit = {
			NOT = { has_start_date < 2001.1.1 }
			has_start_date < 2001.1.2
		}
		country_event = fixture_aux_events.1
	}
}
USA_fixture_aux_monthly_driver = {
	if = {
		limit = { NOT = { has_country_flag = USA_fixture_aux_complete } }
		USA_fixture_aux_reconstruct_history = yes
	}
}
USA_corporate_trigger_year_2001 = { country_event = fixture_aux_events.1 }
"""
    effects_path.write_text(effects, encoding="utf-8")
    _write(
        tmp_path,
        "events/fixture_aux_events.txt",
        """add_namespace = fixture_aux_events
country_event = { id = fixture_aux_events.1 is_triggered_only = yes }
""",
    )

    validator = Validator(str(tmp_path), no_color=True)
    chains = validator._load_manifest()
    effect_defs = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    event_defs = validator._load_events()
    call_sites = validator._load_event_call_sites(
        event_defs, effect_defs, {"fixture_events", "fixture_aux_events"}
    )
    messages = [
        message
        for message, _file, _line in validator._validate_lifecycle_metadata(
            chains, effect_defs, event_defs, call_sites
        )
    ]

    assert not any("USA_fixture_aux" in message for message in messages)
