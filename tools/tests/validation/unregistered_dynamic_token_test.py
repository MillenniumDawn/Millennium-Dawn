"""Regressions for the unregistered `token:` literal check in validate_variables.

A `token:X` literal missing from common/synchronized_dynamic_tokens/MD_tokens.txt
makes the engine log "Token X is a dynamic token, this can cause OOS" at load.
"""

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


def test_runtime_built_token_not_flagged():
    text = "set_variable = { x = token:topbar_[THIS.GetTag] }\n"
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
        '\tlog = "token:in_a_string"\n'
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
            3,
        )
    ]
    assert validator._issues[0].message.startswith("token:gen_7_light ")


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
