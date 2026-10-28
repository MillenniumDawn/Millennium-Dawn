"""Tests for cosmetic country targeting in decisions."""

import pytest
import validate_decisions as V
from shared.suite import build_validator, issue_rows, write_tree

_SINGLE = "single country target GER; consider a normal decision with a custom icon"
_MULTIPLE = (
    "2 country targets but no explicit FROM use; use FROM for target-dependent"
    " behavior, or review whether targeting is only cosmetic"
)
_REVIEW = "; verify localisation and called scripts before changing targeting"
_ONE = "\t\ttargets = { GER }\n"
_MANY = "\t\ttargets = { GER FRA }\n"

# case: (decision body, warning advice or None)
_CASES = {
    "single country": (_ONE, _SINGLE),
    "single country with FROM": (
        _ONE + "\t\tcomplete_effect = { FROM = { add_stability = 0.1 } }\n",
        _SINGLE,
    ),
    "multiple countries without FROM": (_MANY, _MULTIPLE),
    "no target list": ("\t\ticon = generic_operation\n", None),
    "empty list": ("\t\ttargets = { }\n", None),
    "state targets": ("\t\ttargets = { 1 2 }\n", None),
    "nonliteral target": ("\t\ttargets = { GER var:other_country }\n", None),
    "nested targets field": (
        "\t\tcomplete_effect = { custom_effect = { targets = { GER } } }\n",
        None,
    ),
    "state target mode": (_ONE + "\t\tstate_target = yes\n", None),
    "other state target mode": (_ONE + "\t\tstate_target = any\n", None),
    "country target mode": (_ONE + "\t\tstate_target = no\n", _SINGLE),
    "map click": (_ONE + "\t\ton_map_mode = map_only\n", None),
    "map and decision list": (
        _ONE + "\t\ton_map_mode = map_and_decisions_view\n",
        None,
    ),
    "script activation": (_ONE + "\t\tallowed = { always = no }\n", None),
    "conditional activation gate": (
        _ONE + "\t\tallowed = { OR = { always = no original_tag = GER } }\n",
        _SINGLE,
    ),
    "array targets": (_ONE + "\t\ttarget_array = neighbors\n", None),
    "dynamic country variants": (_ONE + "\t\ttargets_dynamic = yes\n", None),
    "static country variants": (_ONE + "\t\ttargets_dynamic = no\n", _SINGLE),
    "FROM block": (_MANY + "\t\tavailable = { FROM = { has_war = yes } }\n", None),
    "FROM scalar": (_MANY + "\t\tvisible = { country_exists = FROM }\n", None),
    "FROM dynamic flag": (
        _MANY + "\t\tvisible = { has_country_flag = agreement_@FROM }\n",
        None,
    ),
    "FROM variable": (
        _MANY + "\t\tavailable = { check_variable = { FROM.influence > 5 } }\n",
        None,
    ),
    "mixed case FROM": (
        _MANY + "\t\tcomplete_effect = { From = { add_stability = 0.1 } }\n",
        None,
    ),
    "implicit target on complete": (
        _MANY + "\t\twar_with_target_on_complete = yes\n",
        None,
    ),
    "implicit target on remove": (
        _MANY + "\t\twar_with_target_on_remove = yes\n",
        None,
    ),
    "implicit target on timeout": (
        _MANY + "\t\twar_with_target_on_timeout = yes\n",
        None,
    ),
    "disabled implicit target": (
        _MANY + "\t\twar_with_target_on_complete = no\n",
        _MULTIPLE,
    ),
    "FROM in comment": (_MANY + "\t\t# FROM is not used here\n", _MULTIPLE),
    "FROM in log": (
        _MANY + '\t\tcomplete_effect = { log = "[FROM.GetName]" }\n',
        _MULTIPLE,
    ),
    "FROM in identifier": (
        _MANY + "\t\tcomplete_effect = { my_FROM_effect = yes }\n",
        _MULTIPLE,
    ),
    "called script needs review": (
        _MANY + "\t\tcomplete_effect = { diplomatic_effect = yes }\n",
        _MULTIPLE,
    ),
    "noncanonical field spacing": ("\t\ttargets={GER FRA}\n", _MULTIPLE),
    "multiline list with comments": (
        "\t\ttargets = {\n\t\t\tGER # FROM\n\t\t\tFRA\n\t\t}\n",
        _MULTIPLE,
    ),
}


@pytest.mark.parametrize(("body", "advice"), _CASES.values(), ids=_CASES)
def test_cosmetic_country_targeting(tmp_path, body, advice):
    path = "common/decisions/targeting.txt"
    write_tree(tmp_path, {path: "category = {\n\tdecision = {\n" + body + "\t}\n}\n"})
    validator = build_validator(V.Validator, tmp_path)

    validator.validate_cosmetic_targeting()

    expected = (
        [("decision-cosmetic-targeting", f"decision - {advice}{_REVIEW}", path, 2)]
        if advice
        else []
    )
    assert issue_rows(validator) == expected
    assert validator.errors_found == 0
    assert validator.warnings_found == len(expected)
    assert all(issue.severity == V.Severity.WARNING for issue in validator._issues)
