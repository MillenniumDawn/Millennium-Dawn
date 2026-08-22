"""Regression tests for Corporate History Clausewitz parsing and data-model checks."""

from .corporate_history_contract_support_test import (
    _NATIVE_ARRAY_BLOCK_EFFECTS,
    _NATIVE_CONTRACT_ROLES,
    _NATIVE_VARIABLE_BLOCK_EFFECTS,
    _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS,
    _UNGUARDED_MESSAGE,
    Decimal,
    Validator,
    _build_fixture,
    _collect_native_write_tokens,
    _guarded_branch,
    _messages,
    _reconstruct,
    _write_loc,
    json,
    pytest,
)


def test_direct_negative_flag_guard_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch("\t\t\tNOT = { has_country_flag = USA_test_branch_a }\n")
        ),
    )
    assert _messages(tmp_path) == []


def test_direct_negative_idea_guard_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch("\t\t\tNOT = { has_idea = USA_test_outcome_a }\n")
        ),
    )
    assert _messages(tmp_path) == []


def test_negated_or_flag_set_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\tOR = {\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_b\n"
                "\t\t\t\t}\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == []


def test_negated_or_mixed_flag_and_idea_set_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\tOR = {\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\t\thas_idea = USA_test_outcome_a\n"
                "\t\t\t\t}\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == []


def test_positive_or_marker_set_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tOR = {\n"
                "\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\thas_country_flag = USA_test_branch_b\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_double_negated_marker_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\tNOT = { has_country_flag = USA_test_branch_a }\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_marker_guarding_another_country_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tCAN = { NOT = { has_country_flag = USA_test_branch_a } }\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_marker_only_in_the_effect_body_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            "\tif = {\n"
            "\t\tlimit = { date > 2001.2.1 }\n"
            "\t\tcustom_effect_tooltip = USA_test_branch_a_tt\n"
            "\t\tNOT = { has_country_flag = USA_test_branch_a }\n"
            "\t\tset_country_flag = USA_test_branch_a\n"
            "\t}\n"
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_date_only_state_changing_branch_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(_guarded_branch("")),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_branch_without_a_limit_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            "\tif = {\n"
            "\t\tset_country_flag = USA_test_branch_a\n"
            "\t\tadd_to_variable = { USA_test_state = 1 }\n"
            "\t\tUSA_test_clamp_state = yes\n"
            "\t}\n"
        ),
    )
    assert _messages(tmp_path) == [
        "USA_test_reconstruct_history has a state-changing block without a date guard",
        _UNGUARDED_MESSAGE,
    ]


def test_variable_only_mutation_still_needs_a_marker_guard(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            "\tif = {\n"
            "\t\tlimit = { date > 2001.2.1 }\n"
            "\t\tadd_to_variable = { USA_test_state = 1 }\n"
            "\t\tUSA_test_clamp_state = yes\n"
            "\t}\n"
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_bare_multi_child_not_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\thas_country_flag = USA_test_branch_b\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_separate_negated_markers_are_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = { has_country_flag = USA_test_branch_a }\n"
                "\t\t\tNOT = { has_country_flag = USA_test_branch_b }\n"
            )
        ),
    )
    assert _messages(tmp_path) == []


def test_negated_and_marker_set_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\tAND = {\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_b\n"
                "\t\t\t\t}\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_tooltip_exemption_requires_a_reason(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["effect_preview_policy"] = "explicit"
    manifest["chains"][0]["tooltip_exemptions"] = {"USA_test_events.1.a": ""}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    messages = _messages(tmp_path)
    assert "Tooltip exemption USA_test_events.1.a requires a reason" in messages
    assert not any(
        "requires exact custom_effect_tooltip" in message for message in messages
    )


def test_scoped_english_localisation_rejects_malformed_quotes(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        'USA_test_events.1.d: "Test description."',
        'USA_test_events.1.d: "A "broken" description"',
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode())
    assert any(
        "Malformed English corporate-history localisation value USA_test_events.1.d"
        in message
        for message in _messages(tmp_path)
    )


def test_scoped_english_localisation_rejects_physical_newline(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        'USA_test_events.1.d: "Test description."',
        'USA_test_events.1.d: "First line\n second line"',
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode())
    assert any(
        "Malformed English corporate-history localisation value USA_test_events.1.d"
        in message
        for message in _messages(tmp_path)
    )


def test_scoped_english_localisation_accepts_escapes_and_literal_newline(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        'USA_test_events.1.d: "Test description."',
        r'USA_test_events.1.d: "A \"quoted\" description\nSecond line #4"',
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode())
    assert not any(
        "Malformed English corporate-history localisation value USA_test_events.1.d"
        in message
        for message in _messages(tmp_path)
    )


def test_duplicate_scoped_english_key_is_rejected_but_non_english_is_ignored(tmp_path):
    _build_fixture(tmp_path)
    _write_loc(
        tmp_path,
        "localisation/english/duplicate_l_english.yml",
        'l_english:\n USA_test_events.1.t: "Duplicate"\n',
    )
    _write_loc(
        tmp_path,
        "localisation/french/duplicate_l_french.yml",
        'l_french:\n USA_test_events.1.t: "French duplicate"\n',
    )
    assert any(
        "English OEM localisation key USA_test_events.1.t is defined 2 times" in message
        for message in _messages(tmp_path)
    )


def test_decimal_manifest_bounds_are_preserved(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={"variables": {"USA_test_state": {"min": 0.05, "max": 1.0}}},
    )
    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, no_cache=True
    )

    chains = validator._load_manifest()

    assert chains[0].variables["USA_test_state"].minimum == Decimal("0.05")
    assert chains[0].variables["USA_test_state"].maximum == Decimal("1.0")


def test_decimal_clamp_mismatch_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={"variables": {"USA_test_state": {"min": 0.05, "max": 1.0}}},
    )

    assert any(
        "must clamp USA_test_state to manifest bounds 0.05..1.0" in message
        for message in _messages(tmp_path)
    )


def test_decimal_clamp_matching_manifest_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={"variables": {"USA_test_state": {"min": 0.05, "max": 1.0}}},
    )
    effects_path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8").replace(
            "var = USA_test_state min = 0 max = 10",
            "var = USA_test_state min = 0.05 max = 1.00",
        ),
        encoding="utf-8",
    )

    assert not any(
        "must clamp USA_test_state to manifest bounds" in message
        for message in _messages(tmp_path)
    )


def test_shared_system_native_write_scanner_covers_structured_mutations():
    text = """
set_country_flag = { flag = POL_native_flag days = 30 }
set_global_flag = { flag = USA_native_global_flag }
modify_country_flag = { value = 2 flag = FRA_native_numeric_flag }
set_mio_flag = ENG_native_mio_flag
set_variable = { var = THIS.SOV_native_meter value = 1 }
modulo_variable = { var = FRA_native_modulo value = 2 }
set_variable_to_random = { max = 5 var = ENG_native_random min = -5 integer = yes }
clear_variable = ROOT.CHI_native_meter
round_variable = THIS.SOV_native_rounded
randomize_variable = { distribution = uniform var = ROOT.CHI_native_random min = 0 max = 1 }
add_to_array = { array = ROOT.POL_native_array value = 1 }
clear_array = THIS.RAJ_native_array
find_highest_in_array = { array = values value = CHI_native_max index = SOV_native_index }
add_ideas = FRA_native_idea
add_timed_idea = { days = 365 idea = RAJ_native_timed_idea }
remove_ideas = { ENG_native_idea CHI_native_idea }
complete_national_focus = { focus = GER_native_focus }
country_event = { days = 1 id = VEN_native_events.1 }
news_event = GER_native_news.1
"""

    assert _collect_native_write_tokens(
        text,
        ("CHI_", "ENG_", "FRA_", "GER_", "POL_", "RAJ_", "SOV_", "USA_", "VEN_"),
    ) == {
        "CHI_native_meter",
        "CHI_native_max",
        "CHI_native_random",
        "CHI_native_idea",
        "ENG_native_idea",
        "ENG_native_mio_flag",
        "ENG_native_random",
        "FRA_native_idea",
        "FRA_native_modulo",
        "FRA_native_numeric_flag",
        "GER_native_news",
        "GER_native_focus",
        "POL_native_array",
        "POL_native_flag",
        "RAJ_native_array",
        "RAJ_native_timed_idea",
        "SOV_native_index",
        "SOV_native_meter",
        "SOV_native_rounded",
        "USA_native_global_flag",
        "VEN_native_events",
    }


@pytest.mark.parametrize(
    ("event_dispatch", "expected_token"),
    (
        ("state_event = USA_native_state_events.1", "USA_native_state_events"),
        (
            "unit_leader_event = { id = USA_native_unit_events.1 days = 1 }",
            "USA_native_unit_events",
        ),
        (
            "operative_leader_event = { days = 1 id = USA_native_operative_events.1 }",
            "USA_native_operative_events",
        ),
    ),
)
def test_shared_system_native_write_scanner_covers_all_event_dispatch_effects(
    event_dispatch, expected_token
):
    assert _collect_native_write_tokens(event_dispatch, ("USA_",)) == {expected_token}


def test_shared_system_native_write_scanner_covers_canonical_persistent_operators():
    assert _NATIVE_VARIABLE_BLOCK_EFFECTS == (
        "set_variable",
        "add_to_variable",
        "subtract_from_variable",
        "multiply_variable",
        "divide_variable",
        "modulo_variable",
        "clamp_variable",
        "randomize_variable",
        "set_variable_to_random",
    )
    assert _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS == (
        "clear_variable",
        "round_variable",
    )
    assert _NATIVE_ARRAY_BLOCK_EFFECTS == (
        "add_to_array",
        "remove_from_array",
        "resize_array",
    )


def test_shared_system_native_write_scanner_covers_every_executable_owned_role():
    assert _NATIVE_CONTRACT_ROLES == (
        "effect",
        "trigger",
        "on_action",
        "event",
        "idea",
        "decision",
        "category",
    )
