"""Variants a start OOB or country history consumes must exist at the start."""

import pytest
from shared.suite import write_tree
from validate_oob_units import Validator

_HISTORY = "history/countries/TST - Test.txt"
_OOB = "history/units/TST_2000.txt"
_LOADS = 'set_oob = "TST_2000"\n'
_VARIANT = 'create_equipment_variant = { name = "D" type = hull_1 }\n'
_GRANT = "set_technology = { hull_tech = 1 }\n"
_USE = (
    "instant_effect = { add_equipment_to_stockpile = "
    '{ type = hull_1 variant_name = "D" amount = 1 producer = TST } }\n'
)
_UNSET_PRODUCER = _USE.replace("producer = TST ", "")
_OTHER_HISTORY = "history/countries/BBB - Other.txt"
_TST_EVENT = "country_event = { immediate = { TST = { " + _VARIANT + "} } }\n"
_MISSING_TECH = "OOB VARIANT: hull technology missing at the start"
_LATER_ONLY = "OOB VARIANT: created only after the start"

_BASE = {
    "common/bookmarks/start.txt": "bookmarks = { b = { date = 2000.1.1.12 } }\n",
    "common/technologies/armor.txt": (
        "technologies = { hull_tech = { enable_equipments = { hull_1 } } }\n"
    ),
    "common/units/equipment/hulls.txt": (
        "equipments = { hull = { is_archetype = yes module_slots = { } } "
        "hull_1 = { archetype = hull module_slots = inherit } }\n"
        "duplicate_archetypes = { clone = { archetype = hull } }\n"
    ),
}

# start state: {case: (extra files, expected category or None)}
_CASES = {
    "tech missing": ({_HISTORY: _LOADS + _VARIANT, _OOB: _USE}, _MISSING_TECH),
    "tech granted": ({_HISTORY: _LOADS + _GRANT + _VARIANT, _OOB: _USE}, None),
    "tech granted after the variant": (
        {_HISTORY: _LOADS + _VARIANT + _GRANT, _OOB: _USE},
        None,
    ),
    "tech granted in a later bookmark": (
        {_HISTORY: _LOADS + _VARIANT + "2017.1.1 = { " + _GRANT + "}\n", _OOB: _USE},
        _MISSING_TECH,
    ),
    "tech possibly granted": (
        {
            _HISTORY: _LOADS
            + _VARIANT
            + "if = { limit = { has_country_flag = x } "
            + _GRANT
            + "}\n",
            _OOB: _USE,
        },
        None,
    ),
    "allowed without the tech": (
        {
            _HISTORY: _LOADS + 'create_equipment_variant = { name = "D" type = hull_1 '
            "allow_without_tech = yes }\n",
            _OOB: _USE,
        },
        None,
    ),
    "no producer, the only creator lacks the tech": (
        {_HISTORY: _LOADS + _VARIANT, _OOB: _UNSET_PRODUCER},
        _MISSING_TECH,
    ),
    "no producer, another creator has it at the start": (
        {
            _HISTORY: _LOADS,
            _OTHER_HISTORY: _VARIANT + _GRANT,
            _OOB: _UNSET_PRODUCER,
            "events/Test.txt": _TST_EVENT,
        },
        None,
    ),
    "no producer, another creator lacks the tech": (
        {
            _HISTORY: _LOADS,
            _OTHER_HISTORY: _VARIANT,
            _OOB: _UNSET_PRODUCER,
            "events/Test.txt": _TST_EVENT,
        },
        _MISSING_TECH,
    ),
    "no producer, one of two creators has the tech": (
        {
            _HISTORY: _LOADS + _VARIANT,
            _OTHER_HISTORY: _VARIANT + _GRANT,
            _OOB: _UNSET_PRODUCER,
        },
        None,
    ),
    "no producer, every creator is an event": (
        {_HISTORY: _LOADS, _OOB: _UNSET_PRODUCER, "events/Test.txt": _TST_EVENT},
        _LATER_ONLY,
    ),
    "consumed in the history itself": (
        {_HISTORY: _VARIANT + _USE},
        _MISSING_TECH,
    ),
    "consumed in a later history block": (
        {_HISTORY: _VARIANT + "2017.1.1 = { " + _USE + "}\n"},
        None,
    ),
    "OOB nothing loads at the start": ({_HISTORY: _VARIANT, _OOB: _USE}, None),
    "OOB loaded only later": (
        {_HISTORY: _VARIANT + "2017.1.1 = { " + _LOADS + "}\n", _OOB: _USE},
        None,
    ),
    "ship reference": (
        {
            _HISTORY: _LOADS + _VARIANT,
            _OOB: (
                "units = { fleet = { task_force = { ship = { equipment = { hull_1 = "
                '{ amount = 1 owner = TST creator = TST version_name = "D" } } } } } }\n'
            ),
        },
        _MISSING_TECH,
    ),
    "clone uses its source's tech": (
        {
            _HISTORY: _LOADS + _VARIANT.replace("hull_1", "clone_1"),
            _OOB: _USE.replace("hull_1", "clone_1"),
        },
        _MISSING_TECH,
    ),
    "created only by an event": (
        {
            _HISTORY: _LOADS,
            _OOB: _USE,
            "events/Test.txt": "country_event = { immediate = { TST = { "
            + _VARIANT
            + "} } }\n",
        },
        _LATER_ONLY,
    ),
    "scripted effect may run from history": (
        {
            _HISTORY: _LOADS,
            _OOB: _USE,
            "common/scripted_effects/test.txt": "test_effect = { " + _VARIANT + "}\n",
        },
        None,
    ),
    "created nowhere is another check's finding": (
        {_HISTORY: _LOADS, _OOB: _USE},
        None,
    ),
    "DLC branch the consumer cannot see": (
        {
            _HISTORY: _LOADS
            + 'if = { limit = { has_dlc = "No Step Back" } '
            + _VARIANT
            + "}\n",
            "history/units/TST_2000_nonnsb.txt": _USE,
        },
        None,
    ),
}


@pytest.mark.parametrize(("files", "category"), _CASES.values(), ids=_CASES)
def test_start_variant_consumers(tmp_path, files, category):
    write_tree(tmp_path, {**_BASE, **files})
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.validate_start_variants()

    assert [issue.category for issue in validator._issues] == (
        [category] if category else []
    )
    if category:
        assert validator._issues[0].severity == (
            "warning" if category == _MISSING_TECH else "error"
        )


def test_start_check_stays_out_of_staged_runs(tmp_path):
    write_tree(tmp_path, {**_BASE, _HISTORY: _LOADS + _VARIANT, _OOB: _USE})
    validator = Validator(str(tmp_path), use_colors=False, workers=1, staged_only=True)
    validator.validate_start_variants()
    assert validator._issues == []


def test_no_bookmark_skips_the_check(tmp_path):
    files = {key: value for key, value in _BASE.items() if "bookmarks" not in key}
    write_tree(tmp_path, {**files, _HISTORY: _LOADS + _VARIANT, _OOB: _USE})
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator.validate_start_variants()
    assert validator._issues == []
