"""Regressions for the unregistered dynamic token check in validate_variables.

A token missing from common/synchronized_dynamic_tokens/MD_tokens.txt makes the
engine log "Token X is a dynamic token, this can cause OOS" at load. Script names
tokens as `token:X` literals and as the `@X` target of token game variables.
"""

import runpy
import sys

import pytest
import validate_variables as V

_REGISTRY = "common/synchronized_dynamic_tokens/MD_tokens.txt"


def _tokens(text, registered=()):
    return [
        (message.split(" ", 1)[0], line)
        for message, _rel, line in V._scan_dynamic_tokens_text(
            text, "common/scripted_effects/x.txt", frozenset(registered)
        )
    ]


def test_unregistered_literal_flagged():
    text = "x = {\n\tadd_to_temp_array = { techs = token:gen_7_light }\n}\n"
    assert _tokens(text) == [("token:gen_7_light", 2)]


def test_registered_literal_ok():
    text = "add_to_temp_array = { techs = token:gen_7_light }\n"
    assert _tokens(text, {"gen_7_light"}) == []


def test_registration_is_case_sensitive():
    text = "set_variable = { x = token:Gen_7_Light }\n"
    assert _tokens(text, {"gen_7_light"}) == [("token:Gen_7_Light", 1)]


def test_repeated_literal_reports_once_per_file():
    text = "set_variable = { x = token:a_b }\nset_variable = { y = token:a_b }\n"
    assert _tokens(text) == [("token:a_b", 1)]


@pytest.mark.parametrize(
    "text",
    [
        "set_variable = { x = token:topbar_[THIS.GetTag] }\n",
        "set_variable = { x = token:gen_$LEVEL$_light }\n",
        "set_variable = { x = modifier@TST_$MOD$_factor }\n",
    ],
)
def test_runtime_built_token_not_flagged(text):
    assert _tokens(text) == []


@pytest.mark.parametrize(
    "text",
    [
        "set_variable = { x = token:TST_a. }\n",
        'desc = "Uses num_equipment@TST_a."\n',
        'desc = "num_equipment@TST_a- and more"\n',
    ],
)
def test_trailing_punctuation_is_not_part_of_the_token(text):
    assert _tokens(text, {"TST_a"}) == []
    assert [token.split(":")[-1].split("@")[-1] for token, _ in _tokens(text)] == [
        "TST_a"
    ]


@pytest.mark.parametrize(
    "ref",
    [
        "modifier@TST_custom_factor",
        "FROM.modifier@TST_custom_factor",
        "resource_produced@TST_custom_factor",
        "THIS.building_level@TST_custom_factor",
        "num_battalions_with_type@TST_custom_factor",
        "party_popularity_100@TST_custom_factor",
    ],
)
def test_unregistered_game_variable_target_flagged(ref):
    text = f"check_variable = {{ {ref} > 0 }}\n"
    assert _tokens(text) == [(ref.split(".")[-1], 1)]
    assert _tokens(text, {"TST_custom_factor"}) == []


@pytest.mark.parametrize(
    "text",
    [
        # Engine-known tokens need no registration.
        "check_variable = { resource@steel > 0 }\n",
        "check_variable = { party_popularity@democratic > 0.5 }\n",
        "check_variable = { modifier@political_power_gain > 0 }\n",
        # `@` after an ordinary variable is a scope, not a token target.
        "set_variable = { coup_party@ROOT = 1 }\n",
        "set_variable = { my_resource@TST_custom_factor = 1 }\n",
        # The target is read from a variable.
        "set_temp_variable = { size = party_popularity@var:ideology }\n",
    ],
)
def test_other_at_forms_not_flagged(text):
    assert _tokens(text) == []


def test_validator_reports_unregistered_tokens_as_errors(tmp_path, write_path):
    write_path(tmp_path, _REGISTRY, "gen_3_light\n")
    write_path(
        tmp_path,
        "common/scripted_effects/tokens.txt",
        "TST_demo = {\n"
        "\tadd_to_temp_array = { techs = token:gen_3_light }\n"
        "\tadd_to_temp_array = { techs = token:gen_7_light }\n"
        "\t# add_to_temp_array = { techs = token:commented_out }\n"
        '\tlog = "[GetDateText]: [?modifier@TST_logged_factor]"\n'
        "}\n",
    )
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1)

    validator.validate_unregistered_dynamic_tokens()

    assert [
        (issue.category, issue.severity, issue.file, issue.line)
        for issue in validator._issues
    ] == [
        (
            "unregistered-dynamic-token",
            V.Severity.ERROR,
            "common/scripted_effects/tokens.txt",
            line,
        )
        for line in (3, 5)
    ]
    assert validator._issues[0].message.startswith("token:gen_7_light ")
    assert validator._issues[1].message.startswith("modifier@TST_logged_factor ")


@pytest.mark.parametrize(
    ("path", "content", "line"),
    [
        (
            "history/countries/TST - Test.txt",
            "set_variable = { x = modifier@TST_custom_factor }\n",
            1,
        ),
        (
            "events/tst.txt",
            "TST_demo = {\n\tset_variable = { x = token:TST_custom_factor }\n}\n",
            2,
        ),
        (
            "interface/tst.gui",
            "guiTypes = {\n"
            "\t# instantTextBoxType\n"
            '\ttext = "[?modifier@TST_custom_factor|%0=+]"\n'
            "}\n",
            3,
        ),
    ],
)
def test_every_scanned_root_reports(tmp_path, write_path, path, content, line):
    write_path(tmp_path, _REGISTRY, "gen_3_light\n")
    write_path(tmp_path, path, content)
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1)

    validator.validate_unregistered_dynamic_tokens()

    assert [(issue.file, issue.line) for issue in validator._issues] == [(path, line)]


def test_english_localisation_is_scanned(tmp_path, write_path):
    write_path(tmp_path, _REGISTRY, "TST_mission\n")
    write_path(
        tmp_path,
        "localisation/english/tst_l_english.yml",
        "l_english:\n"
        ' # TST_c: "[?modifier@TST_commented_out]"\n'
        ' TST_a: "[?days_mission_timeout@TST_mission] days"\n'
        ' TST_b: "[?modifier@TST_custom_factor|%1]"\n',
    )
    write_path(
        tmp_path,
        "localisation/french/tst_l_french.yml",
        'l_french:\n TST_a: "[?modifier@TST_other_factor]"\n',
    )
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1)

    validator.validate_unregistered_dynamic_tokens()

    assert [
        (issue.message.split(" ", 1)[0], issue.file, issue.line)
        for issue in validator._issues
    ] == [
        (
            "modifier@TST_custom_factor",
            "localisation/english/tst_l_english.yml",
            4,
        )
    ]


@pytest.mark.parametrize(
    ("registry", "exit_code"),
    [("gen_3_light\n", 1), ("gen_3_light\nTST_custom_factor\n", 0)],
)
def test_unregistered_token_fails_a_strict_run(
    tmp_path, monkeypatch, write_path, registry, exit_code
):
    """CI runs the validator with --strict, so one finding must fail the job."""
    write_path(tmp_path, _REGISTRY, registry)
    write_path(
        tmp_path,
        "common/scripted_effects/tokens.txt",
        "TST_demo = {\n\tset_variable = { x = modifier@TST_custom_factor }\n}\n",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            V.__file__,
            "--path",
            str(tmp_path),
            "--workers",
            "1",
            "--no-color",
            "--strict",
        ],
    )

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(V.__file__, run_name="__main__")

    assert exit_info.value.code == exit_code


def test_missing_registry_reports_every_literal(tmp_path, write_path):
    write_path(
        tmp_path,
        "events/tokens.txt",
        "TST_demo = {\n\tset_variable = { x = token:gen_3_light }\n}\n",
    )
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1)

    validator.validate_unregistered_dynamic_tokens()

    assert [(issue.file, issue.line) for issue in validator._issues] == [
        ("events/tokens.txt", 2)
    ]
