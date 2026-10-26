import pytest
from targeted_operations_helpers import RaceScript, _parse_race_script


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


def test_parser_preserves_bare_engine_lists_without_swallowing_following_definitions():
    parsed = _parse_race_script(
        'TOP_create = { create_country_leader = { name = "Office holder" traits = { first second } } } '
        "TOP_next = { set_variable = { count = 3 } }"
    )
    leader = parsed["TOP_create"][0][2]
    assert leader == [
        ("name", "=", '"Office holder"'),
        ("traits", "=", ["first", "second"]),
    ]
    assert parsed["TOP_next"] == [("set_variable", "=", [("count", "=", "3")])]
