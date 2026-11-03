"""Shared HOI4 script execution model for Targeted Operations source tests."""

import pytest
from content.ai_race_state_model_test import RaceScript as _AIRaceScript
from content.ai_race_state_model_test import (  # noqa: F401
    _extract_block,
    _named_block,
    _parse_race_script,
)


@pytest.mark.parametrize("reference", ("TOP_history_rows", "global.TOP_history_rows"))
def test_array_membership_treats_unset_history_as_empty(reference):
    script = RaceScript()
    script.countries = {1: {"vars": {}}}
    script.globals = {}
    script.temps = {}
    statements = _parse_race_script(
        f"check = {{ is_in_array = {{ {reference} = 3 }} }}"
    )["check"]

    assert not script.condition(statements, 1)
    scope, name = script._scope(reference, 1)
    assert name not in scope
    scope[name] = [3]
    assert script.condition(statements, 1)
    scope[name] = [4]
    assert not script.condition(statements, 1)


class RaceScript(_AIRaceScript):
    """The AI Race interpreter without its race content; suites load their own."""

    def __init__(self):
        pass
