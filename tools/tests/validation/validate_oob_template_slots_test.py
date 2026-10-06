"""Division template slot layout check in validate_oob_units.py.

A skipped row or column hides the unit past it in the designer and locks the
template for editing (#5421). A slot used twice shows only one of its units.
"""

import pytest
from validate_oob_units import Validator, check_template_slots

_PREFIX = "template 'Test Brigade' (line 1): "


def _block(name, slots):
    rows = "".join(f"\t\tUnit = {{ x = {x} y = {y} }}\n" for x, y in slots)
    return f"\t{name} = {{\n{rows}\t}}\n"


def _template(**blocks):
    """One template; the first block's units start on line 4."""
    body = "".join(_block(name, slots) for name, slots in blocks.items())
    return f'division_template = {{\n\tname = "Test Brigade"\n{body}}}\n'


def _findings(**blocks):
    return check_template_slots(_template(**blocks))


def test_contiguous_layout_is_clean():
    assert not _findings(
        regiments=[(0, 0), (0, 1), (0, 2), (1, 0)],
        regimental_support=[(0, 0), (0, 1)],
        support=[(0, 0), (0, 1)],
    )


def test_skipped_row_is_flagged_on_the_unit_past_the_gap():
    assert _findings(regiments=[(0, 0), (0, 1), (0, 3)]) == [
        (6, _PREFIX + "regiments column x = 0 skips row y = 2")
    ]


@pytest.mark.parametrize("block", ["regiments", "support"])
def test_column_that_starts_below_the_first_row_is_flagged(block):
    assert _findings(**{block: [(0, 1)]}) == [
        (4, _PREFIX + f"{block} column x = 0 skips row y = 0")
    ]


def test_skipped_column_is_flagged_on_the_column_past_the_gap():
    assert _findings(regiments=[(0, 0), (2, 0), (2, 1)]) == [
        (5, _PREFIX + "regiments skips column x = 1")
    ]


@pytest.mark.parametrize("block", ["regiments", "support"])
def test_slot_used_twice_is_flagged_on_the_second_unit(block):
    assert _findings(**{block: [(0, 0), (0, 0)]}) == [
        (5, _PREFIX + f"{block} slot x = 0 y = 0 is already used on line 4")
    ]


def test_regimental_support_may_skip_a_regiments_column():
    assert not _findings(
        regiments=[(0, 0), (1, 0), (2, 0)], regimental_support=[(2, 0)]
    )


def test_regimental_support_needs_its_regiments_column():
    assert _findings(regiments=[(0, 0)], regimental_support=[(1, 0)]) == [
        (7, _PREFIX + "regimental_support column x = 1 has no regiments column x = 1")
    ]


def test_regimental_support_row_gap_and_reuse_are_flagged():
    findings = _findings(regiments=[(0, 0)], regimental_support=[(0, 1), (0, 1)])
    assert findings == [
        (7, _PREFIX + "regimental_support column x = 0 skips row y = 0"),
        (8, _PREFIX + "regimental_support slot x = 0 y = 1 is already used on line 7"),
    ]


@pytest.mark.parametrize(
    "blocks, line, message",
    [
        (
            {"regiments": [(0, y) for y in range(6)]},
            9,
            "regiments slot x = 0 y = 5 is outside the 5x5 grid",
        ),
        (
            {"support": [(0, 0), (1, 0)]},
            5,
            "support slot x = 1 y = 0 is outside the 1x5 grid",
        ),
        (
            {"regiments": [(0, 0)], "regimental_support": [(0, y) for y in range(4)]},
            10,
            "regimental_support slot x = 0 y = 3 is outside the 5x3 grid",
        ),
    ],
)
def test_slot_past_the_designer_grid_is_flagged(blocks, line, message):
    assert _findings(**blocks) == [(line, _PREFIX + message)]


def test_commented_out_unit_does_not_fill_a_gap():
    raw = _template(regiments=[(0, 0), (0, 1), (0, 2)]).replace(
        "\t\tUnit = { x = 0 y = 1 }", "\t\t#Unit = { x = 0 y = 1 }"
    )
    assert check_template_slots(raw) == [
        (6, _PREFIX + "regiments column x = 0 skips row y = 1")
    ]


def test_each_template_in_a_file_has_its_own_grid():
    raw = _template(regiments=[(0, 0)]) + _template(regiments=[(0, 0)])
    assert not check_template_slots(raw)


@pytest.mark.parametrize(
    "rel",
    [
        "history/units/SWE_2000.txt",
        "common/national_focus/sweden.txt",
        "common/scripted_effects/00_AI_scripted_effects.txt",
        "events/Sweden.txt",
    ],
)
def test_validator_reports_an_error_for_every_template_source(tmp_path, rel):
    path = tmp_path / rel
    path.parent.mkdir(parents=True)
    path.write_text(_template(regiments=[(0, 0), (0, 2)]), encoding="utf-8")

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_template_slots()

    assert validator.errors_found == 1
    issue = validator._issues[0]
    assert (issue.severity, issue.category) == ("error", "template-slot")
    assert (issue.file, issue.line) == (rel, 5)
