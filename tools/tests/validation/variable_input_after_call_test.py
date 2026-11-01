"""Tests for real variable inputs declared in "# Parameters:" blocks.

China's history wrote its party setup after startup_politics had read it, so the
effect ran on failsafe values and nothing reported it (issue #6247).
"""

import pytest
import validate_scripted_params as vsp
from shared.suite import run_validator
from shared.suite import write_text as _write

INPUTS = {"startup": ["party_pop", "ruling", "coalition"]}
CALL = "startup = yes"
WRITE = "set_variable = { party_pop^1 = 0.5 }"

_CASES = {
    "write after the call": ([CALL, WRITE], [("party_pop", 2)]),
    "write before the call": ([WRITE, CALL], []),
    "later call picks it up": ([CALL, WRITE, CALL], []),
    "long variable form": (
        [CALL, "set_variable = { var = ruling value = 4 }"],
        [("ruling", 2)],
    ),
    "add to array": ([CALL, "add_to_array = { coalition = 7 }"], [("coalition", 2)]),
    "long array form": (
        [CALL, "add_to_array = { array = coalition value = 7 }"],
        [("coalition", 2)],
    ),
    "remove from array": (
        [CALL, "remove_from_array = { coalition = 7 }"],
        [("coalition", 2)],
    ),
    "clear array": ([CALL, "clear_array = coalition"], [("coalition", 2)]),
    "change an existing value": (
        [CALL, "add_to_variable = { party_pop^1 = 0.1 }"],
        [("party_pop", 2)],
    ),
    "write inside an if": (
        [CALL, "if = { limit = { always = yes }", WRITE, "}"],
        [("party_pop", 3)],
    ),
    "call inside hidden_effect": (
        ["hidden_effect = {", CALL, "}", WRITE],
        [("party_pop", 4)],
    ),
    "another country's variable": ([CALL, "SYR = {", WRITE, "}"], []),
    "next dated block": (["2000.1.1 = {", CALL, "}", "2017.1.1 = {", WRITE, "}"], []),
    "longer variable name": ([CALL, "set_variable = { party_pop_elect^1 = 0.5 }"], []),
    "temp variable of the same name": (
        [CALL, "set_temp_variable = { ruling = 4 }"],
        [],
    ),
    "only one finding per variable": ([CALL, WRITE, WRITE], [("party_pop", 2)]),
}


@pytest.mark.parametrize("lines, expected", _CASES.values(), ids=_CASES.keys())
def test_variables_written_after_the_call(lines, expected):
    found = vsp._find_variables_written_after_call("\n".join(lines), INPUTS)
    assert found == [(var, "startup", line) for var, line in expected]


def test_parser_reads_each_parameter_kind(tmp_path):
    path = tmp_path / "effects.txt"
    _write(
        path,
        "# Parameters:\n"
        "# - needed: a temp variable\n"
        "# - skippable (optional): a temp variable\n"
        "# - chained (set by other_effect): a temp variable\n"
        "# - stored (variable): a real variable\n"
        "my_effect = {\n}\n",
    )
    assert vsp._parse_effect_contracts_from_file(str(path)) == {
        "my_effect": {
            "required": ["needed"],
            "optional": ["skippable", "chained"],
            "variables": ["stored"],
        }
    }


def test_late_write_is_an_error_at_the_write(tmp_path):
    _write(
        tmp_path / "common" / "scripted_effects" / "effects.txt",
        "# Parameters:\n# - ruling_party (variable): the governing party\n"
        "startup_politics = {\n}\n",
    )
    _write(
        tmp_path / "history" / "countries" / "TST - Test.txt",
        "2000.1.1 = {\n"
        "\tstartup_politics = yes # set_variable = { ruling_party = 1 }\n"
        '\tlog = "set_variable = { ruling_party = 2 }"\n'
        "\tset_variable = { ruling_party = 4 }\n"
        "}\n",
    )
    validator = run_validator(vsp.Validator, tmp_path)
    (issue,) = [
        i for i in validator._issues if i.category == "variable-input-after-call"
    ]
    assert issue.severity == vsp.Severity.ERROR
    assert (issue.file, issue.line) == ("history/countries/TST - Test.txt", 4)
    assert "'ruling_party' is written after 'startup_politics'" in issue.message
