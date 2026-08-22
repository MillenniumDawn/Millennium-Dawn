import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
TRIGGERS_PATH = ROOT / "common" / "scripted_triggers" / "MD_linux_system_triggers.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "MD_linux_system_effects.txt"
EVENTS_PATH = ROOT / "events" / "MD_linux_system_events.txt"
FRAMEWORK_DOC_PATH = (
    ROOT / "docs" / "src" / "content" / "resources" / "corporate-history-framework.md"
)

HISTORICAL_ROUTES = {
    "BRA": "upstream",
    "CHI": "national",
    "ENG": "upstream",
    "FRA": "national",
    "GER": "upstream",
    "RAJ": "national",
    "SOV": "national",
    "USA": "enterprise",
}

UPSTREAM_STATES = {
    1: (3, 5, 3, 1),
    2: (4, 6, 4, 1),
    3: (4, 7, 5, 1),
    4: (6, 9, 6, 1),
    5: (6, 10, 7, 1),
}

NATIONAL_STATES = {
    1: (4, 3, 4, 2),
    2: (5, 3, 6, 3),
    3: (5, 3, 8, 3),
    4: (6, 3, 10, 3),
    5: (6, 3, 10, 3),
}

NATIONAL_READS = {
    "CHI_huawei_open_ai_ecosystem",
    "CHI_huawei_open_cloud_partnership",
    "CHI_huawei_open_enterprise_networking",
    "CHI_huawei_open_interoperability_5g",
    "CHI_huawei_software_ecosystem",
    "CHI_huawei_state_initialized",
    "CHI_huawei_supply_resilience",
    "ENG_arm_holdings_british_founded_global_platform",
    "ENG_arm_holdings_british_golden_share_settlement",
    "ENG_arm_holdings_nvidia_arm_compute_platform",
    "ENG_arm_holdings_sovereign_architecture_champion",
    "ENG_arm_holdings_terminal_resolved",
    "ENG_cloud_isles",
    "FRA_corporate_digital_infrastructure",
    "FRA_corporate_systems_resilient_multivendor_network",
    "FRA_corporate_systems_state_initialized",
    "GER_home_Grown_Software",
    "POL_industrial_sovereignty_event_05_resolved",
    "POL_industrial_sovereignty_event_05_scheduled",
    "POL_industrial_sovereignty_software_domestic_market",
    "POL_industrial_sovereignty_software_export_ecosystem",
    "POL_industrial_sovereignty_software_public_security",
    "RAJ_software_tech_park",
    "SOV_computing_sovereignty_foreign_access",
    "SOV_computing_sovereignty_procurement",
    "SOV_computing_sovereignty_shortage",
    "SOV_computing_sovereignty_software",
    "SOV_computing_sovereignty_state_initialized",
    "SOV_computing_sovereignty_systems_integration",
    "VEN_mission_ciencia",
}

NATIONAL_LOCALISATION = {
    "BRA": "linux_system_events.2.d_BRA",
    "CHI": "linux_system_events.4.d_CHI",
    "ENG": "linux_system_events.2.d_ENG",
    "FRA": "linux_system_events.2.d_FRA",
    "GER": "linux_system_events.2.d_GER",
    "RAJ": "linux_system_events.2.d_RAJ",
    "SOV": "linux_system_events.2.d_SOV",
}


def _extract_block(text: str, brace_index: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    for index in range(brace_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace_index : index + 1]
    raise AssertionError("Unbalanced scripted block")


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"Missing block {name}"
    return _extract_block(text, text.index("{", match.start()))


def _blocks(text: str, name: str) -> list[str]:
    return [
        _extract_block(text, text.index("{", match.start()))
        for match in re.finditer(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", text)
    ]


def _event_map(text: str) -> dict[int, str]:
    events = {}
    for match in re.finditer(r"(?m)^country_event\s*=\s*\{", text):
        block = _extract_block(text, text.index("{", match.start()))
        event_id = re.search(r"(?m)^\s*id\s*=\s*linux_system_events\.(\d+)", block)
        if event_id:
            events[int(event_id.group(1))] = block
    return events


def _option_by_name(event: str, name: str) -> str:
    for match in re.finditer(r"(?m)^\s*option\s*=\s*\{", event):
        block = _extract_block(event, event.index("{", match.start()))
        if re.search(rf"(?m)^\s*name\s*=\s*{re.escape(name)}\s*$", block):
            return block
    raise AssertionError(f"Missing option {name}")


def _shared_system() -> dict:
    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    systems = [
        system
        for system in manifest["shared_systems"]
        if system["namespace"] == "linux_system_events"
    ]
    assert len(systems) == 1
    return systems[0]


def _assert_state(block: str, marker: str, state: tuple[int, int, int, int]) -> None:
    marker_index = block.index(marker)
    starts = [
        match
        for match in re.finditer(r"(?m)^\s*(?:if|else_if)\s*=\s*\{", block)
        if match.start() < marker_index
    ]
    assert starts
    branch = _extract_block(block, block.index("{", starts[-1].start()))
    deployment, stewardship, assurance, support = state
    assert f"linux_system_base_deployment = {deployment}" in branch
    assert f"linux_system_base_stewardship = {stewardship}" in branch
    assert f"linux_system_base_assurance = {assurance}" in branch
    assert f"linux_system_base_support_model = {support}" in branch


def test_manifest_declares_exact_historical_routes_and_national_reads():
    system = _shared_system()

    assert system["historical_routes"] == HISTORICAL_ROUTES
    declared_reads = set(system["allowed_native_reads"])
    assert {read for read in declared_reads if not read.startswith("USA_")} == (
        NATIONAL_READS
    )
    assert system["excluded_generic_idea_tags"] == ["USA"]


def test_historical_reconstruction_replays_source_aligned_route_state():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")

    upstream = _named_block(triggers, "linux_system_historical_upstream_route")
    national = _named_block(triggers, "linux_system_historical_national_route")
    assert set(re.findall(r"original_tag\s*=\s*([A-Z]{3})", upstream)) == {
        "ENG",
        "GER",
        "BRA",
    }
    assert set(re.findall(r"original_tag\s*=\s*([A-Z]{3})", national)) == {
        "FRA",
        "RAJ",
        "SOV",
        "CHI",
    }

    for stage in range(1, 6):
        block = _named_block(effects, f"linux_system_reconstruct_event_{stage}")
        _assert_state(
            block,
            "linux_system_historical_upstream_route = yes",
            UPSTREAM_STATES[stage],
        )
        _assert_state(
            block,
            "linux_system_historical_national_route = yes",
            NATIONAL_STATES[stage],
        )
        if stage in (2, 3, 4):
            assert f"linux_system_event_{stage}_route_upstream" in block
            assert f"linux_system_event_{stage}_route_national" in block


def test_historical_ai_uses_only_the_declared_national_routes():
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))
    upstream_tags = {"ENG", "GER", "BRA"}
    national_tags = {"FRA", "RAJ", "SOV", "CHI"}

    for event_number in range(1, 6):
        upstream = _option_by_name(
            events[event_number], f"linux_system_events.{event_number}.a"
        )
        enterprise = _option_by_name(
            events[event_number], f"linux_system_events.{event_number}.b"
        )
        assert upstream_tags <= set(
            re.findall(r"original_tag\s*=\s*([A-Z]{3})", upstream)
        )
        assert "USA" in re.findall(r"original_tag\s*=\s*([A-Z]{3})", enterprise)
        if event_number == 1:
            assert national_tags <= set(
                re.findall(r"original_tag\s*=\s*([A-Z]{3})", enterprise)
            )
        else:
            national = _option_by_name(
                events[event_number], f"linux_system_events.{event_number}.c"
            )
            assert national_tags <= set(
                re.findall(r"original_tag\s*=\s*([A-Z]{3})", national)
            )

    assert not re.search(
        r"is_historical_focus_on\s*=\s*yes\s+NOT\s*=\s*\{\s*original_tag\s*=\s*USA",
        EVENTS_PATH.read_text(encoding="utf-8"),
    )


def test_national_adapters_are_bounded_read_only_and_change_driven():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    refresh = _named_block(effects, "linux_system_refresh_adapter")
    monthly = _named_block(effects, "linux_system_monthly_driver")
    change_check = _named_block(effects, "linux_system_refresh_adapter_if_changed")
    countries = ("eng", "ger", "fra", "raj", "sov", "chi", "pol", "ven")

    for country in countries:
        assert f"linux_system_refresh_{country}_adapter = yes" in refresh
    assert refresh.count("corporate_history_enabled = yes") == 5
    for tag in ("USA", "FRA", "SOV", "CHI", "POL"):
        gated = min(
            (
                block
                for block in _blocks(refresh, "if") + _blocks(refresh, "else_if")
                if f"original_tag = {tag}" in block
            ),
            key=len,
        )
        assert "corporate_history_enabled = yes" in gated
    eng_adapter = _named_block(effects, "linux_system_refresh_eng_adapter")
    assert "corporate_history_enabled = yes" in eng_adapter
    assert "ENG_arm_holdings_terminal_resolved" in eng_adapter
    assert "original_tag = BRA" not in refresh
    for variable in ("deployment", "stewardship", "assurance"):
        assert (
            f"clamp_variable = {{ var = linux_system_adapter_{variable} min = -2 max = 2 }}"
            in refresh
        )

    adapter_text = "\n".join(
        _named_block(effects, f"linux_system_refresh_{country}_adapter")
        for country in countries
    )
    assert "linux_system_adapter_support_model" not in adapter_text
    native_token = r"(?:ENG|GER|FRA|RAJ|SOV|CHI|POL|VEN)_[A-Za-z0-9_]+"
    native_target = rf"(?:[A-Za-z0-9_]+[.:])*{native_token}"
    flag_write = (
        r"(?:set|clr|modify)_"
        r"(?:character|country|country_pmc|global|mio|project|state|unit_leader)_flag"
    )
    variable_block_write = (
        r"(?:set_variable|add_to_variable|subtract_from_variable|multiply_variable|"
        r"divide_variable|modulo_variable|clamp_variable|randomize_variable|"
        r"set_variable_to_random)"
    )
    array_block_write = r"(?:add_to_array|remove_from_array|resize_array)"
    assert not re.search(
        rf"{flag_write}\s*=\s*(?:\{{\s*flag\s*=\s*)?{native_target}",
        adapter_text,
    )
    assert not re.search(
        rf"{flag_write}\s*=\s*\{{[^{{}}]*?\bflag\s*=\s*{native_target}",
        adapter_text,
        re.DOTALL,
    )
    assert not re.search(
        rf"{variable_block_write}\s*=\s*\{{\s*(?:var\s*=\s*)?{native_target}",
        adapter_text,
    )
    assert not re.search(
        rf"{variable_block_write}\s*=\s*\{{[^{{}}]*?\bvar\s*=\s*{native_target}",
        adapter_text,
        re.DOTALL,
    )
    assert not re.search(
        rf"(?:clear|round)_variable\s*=\s*"
        rf"(?:\{{[^{{}}]*?\b(?:var|which)\s*=\s*)?{native_target}",
        adapter_text,
        re.DOTALL,
    )
    assert not re.search(
        rf"{array_block_write}\s*=\s*\{{\s*(?:array\s*=\s*)?{native_target}",
        adapter_text,
    )
    assert not re.search(
        rf"{array_block_write}\s*=\s*\{{[^{{}}]*?\barray\s*=\s*{native_target}",
        adapter_text,
        re.DOTALL,
    )
    assert not re.search(
        rf"clear_array\s*=\s*" rf"(?:\{{[^{{}}]*?\barray\s*=\s*)?{native_target}",
        adapter_text,
        re.DOTALL,
    )
    for output in ("value", "index"):
        assert not re.search(
            rf"(?:find_highest_in_array|find_lowest_in_array)\s*=\s*"
            rf"\{{[^{{}}]*?\b{output}\s*=\s*{native_target}",
            adapter_text,
            re.DOTALL,
        )
    assert not re.search(
        rf"(?:add_ideas|remove_ideas|add_idea|remove_idea)\s*=\s*{native_target}",
        adapter_text,
    )
    assert not re.search(
        rf"add_timed_idea\s*=\s*\{{[^{{}}]*?\bidea\s*=\s*{native_target}",
        adapter_text,
        re.DOTALL,
    )
    assert not re.search(
        rf"(?:complete_national_focus|uncomplete_national_focus|unlock_national_focus)"
        rf"\s*=\s*(?:\{{\s*focus\s*=\s*)?{native_target}",
        adapter_text,
    )
    assert not re.search(
        rf"(?:country_event|news_event)\s*=\s*"
        rf"(?:\{{[^{{}}]*?\bid\s*=\s*)?{native_target}",
        adapter_text,
        re.DOTALL,
    )
    for idea_block in re.findall(
        r"(?:add_ideas|remove_ideas)\s*=\s*\{([^{}]*)\}",
        adapter_text,
        re.DOTALL,
    ):
        assert not re.search(native_token, idea_block)

    assert "linux_system_refresh_adapter = yes" in change_check
    assert change_check.count("compare = not_equals") == 4
    assert "linux_system_mark_dirty = yes" in change_check
    assert "linux_system_refresh_ideas" not in change_check
    assert monthly.index(
        "linux_system_refresh_adapter_if_changed = yes"
    ) < monthly.index("limit = { has_country_flag = linux_system_dirty }")


def test_country_adapter_mappings_match_the_approved_bounds():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")

    eng = _named_block(effects, "linux_system_refresh_eng_adapter")
    assert "has_completed_focus = ENG_cloud_isles" in eng
    assert eng.count("linux_system_adapter_deployment = 1") == 2

    ger = _named_block(effects, "linux_system_refresh_ger_adapter")
    assert "has_completed_focus = GER_home_Grown_Software" in ger
    assert "linux_system_adapter_deployment = 1" in ger
    assert "linux_system_adapter_stewardship = 1" in ger

    fra = _named_block(effects, "linux_system_refresh_fra_adapter")
    assert (
        "var = FRA_corporate_digital_infrastructure value = 7 "
        "compare = greater_than_or_equals"
    ) in fra
    assert "FRA_corporate_systems_resilient_multivendor_network" in fra
    assert "linux_system_adapter_deployment = 1" in fra
    assert "linux_system_adapter_assurance = 1" in fra

    raj = _named_block(effects, "linux_system_refresh_raj_adapter")
    assert "has_completed_focus = RAJ_software_tech_park" in raj
    assert raj.count("linux_system_adapter_deployment = 1") == 1

    sov = _named_block(effects, "linux_system_refresh_sov_adapter")
    for variable in (
        "SOV_computing_sovereignty_software",
        "SOV_computing_sovereignty_procurement",
        "SOV_computing_sovereignty_systems_integration",
        "SOV_computing_sovereignty_foreign_access",
        "SOV_computing_sovereignty_shortage",
    ):
        assert variable in sov
    for threshold in (
        "var = SOV_computing_sovereignty_software value = 6 compare = greater_than_or_equals",
        "var = SOV_computing_sovereignty_procurement value = 4 compare = greater_than_or_equals",
        "var = SOV_computing_sovereignty_systems_integration value = 6 compare = greater_than_or_equals",
        "var = SOV_computing_sovereignty_foreign_access value = 7 compare = greater_than_or_equals",
        "var = SOV_computing_sovereignty_shortage value = 4 compare = less_than",
        "var = SOV_computing_sovereignty_foreign_access value = 3 compare = less_than",
        "var = SOV_computing_sovereignty_shortage value = 4 compare = greater_than_or_equals",
    ):
        assert threshold in sov
    assert sov.count("linux_system_adapter_deployment = 1") == 2
    assert "linux_system_adapter_assurance = 1" in sov

    chi = _named_block(effects, "linux_system_refresh_chi_adapter")
    assert (
        "var = CHI_huawei_software_ecosystem value = 7 "
        "compare = greater_than_or_equals"
    ) in chi
    assert (
        "var = CHI_huawei_supply_resilience value = 6 "
        "compare = greater_than_or_equals"
    ) in chi
    assert "linux_system_adapter_stewardship = 1" in chi
    assert "OpenHarmony" not in chi
    assert "openharmony" not in chi
    assert "android" not in chi.lower()

    pol = _named_block(effects, "linux_system_refresh_pol_adapter")
    assert "POL_industrial_sovereignty_software_public_security" in pol
    assert "POL_industrial_sovereignty_software_export_ecosystem" in pol
    assert "POL_industrial_sovereignty_software_domestic_market" in pol
    assert "linux_system_adapter_stewardship" not in pol

    ven = _named_block(effects, "linux_system_refresh_ven_adapter")
    assert "has_completed_focus = VEN_mission_ciencia" in ven
    assert ven.count("linux_system_adapter_deployment = 1") == 1
    assert "linux_system_adapter_stewardship" not in ven


def test_polish_native_overlap_suppresses_only_the_2008_delivery():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    events = _event_map(EVENTS_PATH.read_text(encoding="utf-8"))
    suppression_trigger = _named_block(triggers, "linux_system_pol_suppresses_event_2")
    resolution_trigger = _named_block(triggers, "linux_system_pol_resolves_event_2")
    suppression = _named_block(effects, "linux_system_suppress_event_2_pol")

    assert "original_tag = POL" in suppression_trigger
    assert "corporate_history_enabled = yes" in suppression_trigger
    assert "POL_industrial_sovereignty_event_05_scheduled" in suppression_trigger
    assert "POL_industrial_sovereignty_event_05_resolved" in suppression_trigger
    assert "POL_industrial_sovereignty_event_05_scheduled" not in resolution_trigger
    assert "POL_industrial_sovereignty_event_05_resolved" in resolution_trigger
    assert "date > 2008.5.31" in resolution_trigger
    assert "linux_system_event_2_expected" in suppression
    assert "linux_system_event_2_pending" in suppression
    assert "set_country_flag = linux_system_event_2_resolved" in suppression
    assert "add_to_variable = { linux_system_base_deployment = 1 }" in suppression
    assert "linux_system_base_stewardship" not in suppression
    assert "linux_system_base_assurance" not in suppression
    assert "linux_system_base_support_model" not in suppression
    assert "linux_system_pol_suppresses_event_2 = yes" in events[2]
    schedule = _named_block(effects, "linux_system_schedule_event_2")
    assert "linux_system_pol_suppresses_event_2 = yes" in schedule
    assert "set_country_flag = linux_system_event_2_expected" in schedule
    assert "linux_system_suppress_event_2_pol = yes" not in schedule
    activate = _named_block(effects, "linux_system_activate_event_2")
    recovery = _named_block(effects, "linux_system_recover_due_events")
    assert "linux_system_suppress_event_2_pol = yes" in activate
    assert "linux_system_activate_event_2 = yes" in recovery
    for event_number in (1, 3, 4, 5):
        assert "linux_system_pol_suppresses_event_2" not in events[event_number]


def test_national_localisation_is_complete_bom_safe_and_country_owned():
    system = _shared_system()
    event_text = EVENTS_PATH.read_text(encoding="utf-8")
    declared_paths = {
        Path(path).name: ROOT / path for path in system["files"]["localisation"]
    }

    for tag, key in NATIONAL_LOCALISATION.items():
        path = declared_paths[f"MD_focus_{tag}_l_english.yml"]
        assert path.read_bytes().startswith(b"\xef\xbb\xbf")
        text = path.read_text(encoding="utf-8-sig")
        assert len(re.findall(rf"(?m)^ {re.escape(key)}:", text)) == 1
        assert key in event_text
        value_line = next(
            line for line in text.splitlines() if line.startswith(f" {key}:")
        )
        assert "—" not in value_line
        assert not re.search(r"(?m)^ {2,}[^ #\r\n][^:]*:", text)

    assert set(NATIONAL_LOCALISATION.values()) <= set(system["localisation_keys"])


def test_public_contract_documents_every_national_adapter():
    framework = FRAMEWORK_DOC_PATH.read_text(encoding="utf-8")
    system = _shared_system()

    assert system["historical_routes"] == HISTORICAL_ROUTES
    for tag in ("ENG", "GER", "FRA", "BRA", "RAJ", "SOV", "CHI", "POL", "VEN"):
        assert f"{tag}_" in system["native_write_prefixes"]

    assert "national adapters" in framework
    assert "Adapters contribute bounded values" in framework
    assert "cannot write back into their source chains" in framework


def test_context_only_countries_have_no_adapter_or_authored_description():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = EVENTS_PATH.read_text(encoding="utf-8")

    for tag in ("FIN", "CAN", "TAI", "JAP", "SWE"):
        assert f"original_tag = {tag}" not in _named_block(
            effects, "linux_system_refresh_adapter"
        )
        assert f"linux_system_events.2.d_{tag}" not in events
        assert f"linux_system_events.4.d_{tag}" not in events
