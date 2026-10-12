"""Division template layout checks in validate_oob_units.py.

A skipped row or column hides the unit past it in the designer and locks the
template for editing (#5421). A slot used twice shows only one of its units.
Rows past the base column height stay locked until a doctrine opens them.
"""

import pytest
import validate_oob_units as V
from validate_oob_units import TemplateLimits, Validator, read_template_limits
from validator_common import strip_comments

_PREFIX = "template 'Test Brigade' (line 1): "
_OOB = "history/units/TST_2000.txt"
# Millennium Dawn's defines: three open rows, two more from doctrines.
_LIMITS = TemplateLimits(
    grids={"regiments": (5, 5), "regimental_support": (5, 3), "support": (1, 5)},
    open_rows=3,
    required_battalions=(1, 3, 5),
    column_bonus={"UKR": 1},
)
_DEFINES = (
    "NDefines.NMilitary.MIN_DIVISION_BRIGADE_HEIGHT = 3 -- 4\n"
    "\tNDefines.NMilitary.MAX_REGIMENTAL_SUPPORT_HEIGHT = 3\t\t-- Max height\n"
    "-- NDefines.NMilitary.MAX_DIVISION_BRIGADE_WIDTH = 9\n"
    "NDefines.NMilitary.REGIMENTAL_SUPPORT_REQUIRED_BATTALIONS = { 1, 3, 5 } -- rows\n"
)
_DOCTRINES = (
    "centralized_command = {\n"
    "\ttrack = structure_doctrine\n"
    "\tadditional_brigade_column_size = 1\n"
    "\trewards = {\n"
    "\t\tdivision_structure = {\n"
    "\t\t\tadditional_brigade_column_size = 1\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
    "mobile_infantry = {\n"
    "\tplanning_speed = 0.1\n"
    "}\n"
)


def _block(name, slots):
    rows = "".join(f"\t\tUnit = {{ x = {x} y = {y} }}\n" for x, y in slots)
    return f"\t{name} = {{\n{rows}\t}}\n"


def _template(**blocks):
    """One template; the first block's units start on line 4."""
    body = "".join(_block(name, slots) for name, slots in blocks.items())
    return f'division_template = {{\n\tname = "Test Brigade"\n{body}}}\n'


def _check(raw, rel=_OOB):
    text = strip_comments(raw)
    return V.check_template_slots(text, V._build_block_nodes(text), rel, _LIMITS)


def _errors(**blocks):
    findings = _check(_template(**blocks))
    assert {category for _, category, _ in findings} <= {"template-slot"}
    return [(line, message) for line, _, message in findings]


def _write(tmp_path, rel, content):
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_contiguous_layout_is_clean():
    assert not _errors(
        regiments=[(0, 0), (0, 1), (0, 2), (1, 0)],
        regimental_support=[(0, 0), (0, 1), (1, 0)],
        support=[(0, 0), (0, 1)],
    )


def test_skipped_row_is_flagged_on_the_unit_past_the_gap():
    assert _errors(regiments=[(0, 0), (0, 2)]) == [
        (5, _PREFIX + "regiments column x = 0 skips row y = 1")
    ]


def test_row_that_jumps_to_y_3_is_a_gap_and_a_locked_row():
    # The #5420 shape: y = 0, 1, 3 where 0, 1, 2 was meant.
    assert _check(_template(regiments=[(0, 0), (0, 1), (0, 3)])) == [
        (
            6,
            "template-locked-row",
            _PREFIX + "1 regiments unit(s) on row y = 3 or higher, locked without "
            "a doctrine that adds additional_brigade_column_size",
        ),
        (6, "template-slot", _PREFIX + "regiments column x = 0 skips row y = 2"),
    ]


@pytest.mark.parametrize("block", ["regiments", "support"])
def test_column_that_starts_below_the_first_row_is_flagged(block):
    assert _errors(**{block: [(0, 1)]}) == [
        (4, _PREFIX + f"{block} column x = 0 skips row y = 0")
    ]


def test_skipped_column_is_flagged_on_the_column_past_the_gap():
    assert _errors(regiments=[(0, 0), (2, 0), (2, 1)]) == [
        (5, _PREFIX + "regiments skips column x = 1")
    ]


@pytest.mark.parametrize("block", ["regiments", "support"])
def test_slot_used_twice_is_flagged_on_the_second_unit(block):
    assert _errors(**{block: [(0, 0), (0, 0)]}) == [
        (5, _PREFIX + f"{block} slot x = 0 y = 0 is already used on line 4")
    ]


def test_unit_without_both_coordinates_is_flagged():
    raw = _template(regiments=[(0, 0), (0, 1)]).replace("x = 0 y = 1", "x = 0")
    assert _check(raw) == [
        (5, "template-slot", _PREFIX + "regiments unit 'Unit' has no readable x and y")
    ]


def test_regimental_support_may_skip_a_regiments_column():
    assert not _errors(regiments=[(0, 0), (1, 0), (2, 0)], regimental_support=[(2, 0)])


def test_regimental_support_needs_its_regiments_column():
    assert _errors(regiments=[(0, 0)], regimental_support=[(1, 0)]) == [
        (7, _PREFIX + "regimental_support column x = 1 has no regiments column x = 1")
    ]


def test_regimental_support_row_needs_enough_battalions():
    errors = _errors(
        regiments=[(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)],
        regimental_support=[(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)],
    )
    slot = "regimental_support slot x = {} y = {} needs {} battalions in regiments "
    assert errors == [
        (12, _PREFIX + slot.format(0, 1, 3) + "column x = 0, which has 2"),
        (15, _PREFIX + slot.format(1, 2, 5) + "column x = 1, which has 3"),
    ]


def test_regimental_support_row_gap_and_reuse_are_flagged():
    assert _errors(regiments=[(0, 0)], regimental_support=[(0, 1), (0, 1)]) == [
        (7, _PREFIX + "regimental_support column x = 0 skips row y = 0"),
        (
            7,
            _PREFIX + "regimental_support slot x = 0 y = 1 needs 3 battalions in "
            "regiments column x = 0, which has 1",
        ),
        (8, _PREFIX + "regimental_support slot x = 0 y = 1 is already used on line 7"),
    ]


@pytest.mark.parametrize(
    "blocks, line, message",
    [
        (
            {"regiments": [(x, 0) for x in range(6)]},
            9,
            "regiments slot x = 5 y = 0 is outside the 5x5 grid",
        ),
        (
            {"support": [(0, 0), (1, 0)]},
            5,
            "support slot x = 1 y = 0 is outside the 1x5 grid",
        ),
        (
            {"support": [(0, y) for y in range(6)]},
            9,
            "support slot x = 0 y = 5 is outside the 1x5 grid",
        ),
    ],
)
def test_slot_past_the_designer_grid_is_flagged(blocks, line, message):
    assert _errors(**blocks) == [(line, _PREFIX + message)]


def test_commented_out_unit_does_not_fill_a_gap():
    raw = _template(regiments=[(0, 0), (0, 1), (0, 2)]).replace(
        "\t\tUnit = { x = 0 y = 1 }", "\t\t#Unit = { x = 0 y = 1 }"
    )
    assert _check(raw) == [
        (6, "template-slot", _PREFIX + "regiments column x = 0 skips row y = 1")
    ]


def test_each_template_in_a_file_has_its_own_grid():
    assert not _check(_template(regiments=[(0, 0)]) + _template(regiments=[(0, 0)]))


def test_rows_past_the_base_height_are_a_locked_row_warning():
    raw = _template(regiments=[(0, y) for y in range(5)] + [(1, 0)])
    assert _check(raw) == [
        (
            7,
            "template-locked-row",
            _PREFIX + "2 regiments unit(s) on row y = 3 or higher, locked without "
            "a doctrine that adds additional_brigade_column_size",
        )
    ]


def test_starting_doctrine_opens_a_row_for_that_tag_only():
    raw = _template(regiments=[(0, y) for y in range(5)])
    findings = _check(raw, rel="history/units/UKR_2000.txt")
    assert [(line, category) for line, category, _ in findings] == [
        (8, "template-locked-row")
    ]
    assert "1 regiments unit(s) on row y = 4 or higher" in findings[0][2]


def test_limits_come_from_the_defines_and_starting_doctrines(tmp_path):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        "add_mastery = {\n\tamount = 25\n\tsub_doctrine = centralized_command\n}\n",
    )
    _write(
        tmp_path,
        "history/countries/GER - Germany.txt",
        "set_sub_doctrine = {\n\tsub_doctrine = mobile_infantry\n}\n"
        "2017.1.1 = {\n\tset_sub_doctrine = centralized_command\n}\n",
    )

    assert read_template_limits(str(tmp_path)) == _LIMITS


def test_starting_mastery_below_reward_threshold_does_not_open_reward_row(tmp_path):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(
        tmp_path,
        "common/defines/doctrine.lua",
        "NDefines.NDoctrines.DEFAULT_REWARD_MASTERY = 100.0\n",
    )
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "common/doctrines/grand_doctrines/land.txt",
        "combined_arms = { folder = land }\n",
    )
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_grand_doctrine = combined_arms\n"
        "set_sub_doctrine = centralized_command\n"
        "add_mastery = { amount = 25 sub_doctrine = centralized_command }\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 1}


@pytest.mark.parametrize("amount", [100, 125])
def test_starting_mastery_at_or_above_reward_threshold_opens_reward_row(
    tmp_path, amount
):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(
        tmp_path,
        "common/defines/doctrine.lua",
        "NDefines.NDoctrines.DEFAULT_REWARD_MASTERY = 100.0\n",
    )
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        f"add_mastery = {{ amount = {amount} sub_doctrine = centralized_command }}\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 2}


def test_mastery_reward_threshold_override_is_respected(tmp_path):
    doctrine = _DOCTRINES.replace(
        "division_structure = {\n\t\t\tadditional_brigade_column_size = 1",
        "division_structure = {\n\t\t\tmastery = 50\n\t\t\tadditional_brigade_column_size = 1",
    )
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", doctrine)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        "add_mastery = { amount = 50 sub_doctrine = centralized_command }\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 2}


def test_inactive_subdoctrine_mastery_does_not_open_replaced_track_reward(tmp_path):
    doctrines = _DOCTRINES + "other_command = {\n\ttrack = structure_doctrine\n}\n"
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", doctrines)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        "set_sub_doctrine = other_command\n"
        "add_mastery = { amount = 100 sub_doctrine = centralized_command }\n"
        "set_sub_doctrine = centralized_command\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 1}


def test_add_mastery_filter_does_not_credit_inactive_subdoctrine(tmp_path):
    doctrines = (
        _DOCTRINES + "other_command = {\n\ttrack = another_structure_doctrine\n}\n"
    )
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", doctrines)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        "set_sub_doctrine = other_command\n"
        "add_mastery = { amount = 100 sub_doctrine = other_command }\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 1}


def test_add_mastery_filters_match_active_doctrine_state(tmp_path):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "common/doctrines/grand_doctrines/land.txt",
        "combined_arms = { folder = land }\n",
    )
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_grand_doctrine = combined_arms\n"
        "set_sub_doctrine = centralized_command\n"
        "add_mastery = { amount = 100 folder = land grand_doctrine = combined_arms "
        "sub_doctrine = centralized_command track = structure_doctrine }\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 2}


def test_changing_grand_doctrine_after_subdoctrine_invalidates_its_row_bonus(
    tmp_path,
):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "common/doctrines/grand_doctrines/land.txt",
        "combined_arms = { folder = land }\nother_arms = { folder = land }\n",
    )
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_grand_doctrine = combined_arms\n"
        "set_sub_doctrine = centralized_command\n"
        "set_grand_doctrine = other_arms\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {}


def test_nested_conditional_doctrine_command_makes_starting_state_uncertain(
    tmp_path,
):
    doctrines = _DOCTRINES + "other_command = {\n\ttrack = structure_doctrine\n}\n"
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", doctrines)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        "if = { limit = { always = yes } set_sub_doctrine = other_command }\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {}


@pytest.mark.parametrize(
    "history, grand_doctrines",
    [
        (
            "set_sub_doctrine = centralized_command.variable\n",
            "",
        ),
        (
            "set_grand_doctrine = combined_arms\n"
            "set_sub_doctrine = centralized_command\n"
            "set_grand_doctrine = combined_arms.variable\n",
            "combined_arms = { folder = land }\n",
        ),
    ],
)
def test_assignment_suffix_expression_is_not_parsed_as_static_identifier(
    history, grand_doctrines, tmp_path
):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    if grand_doctrines:
        _write(
            tmp_path,
            "common/doctrines/grand_doctrines/land.txt",
            grand_doctrines,
        )
    _write(tmp_path, "history/countries/UKR - Ukraine.txt", history)

    assert read_template_limits(str(tmp_path)).column_bonus == {}


def test_dynamic_mastery_amount_prevents_later_numeric_mastery_from_unlocking(tmp_path):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        "add_mastery = { amount = ROOT.starting_mastery sub_doctrine = centralized_command }\n"
        "add_mastery = { amount = 100 sub_doctrine = centralized_command }\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 1}


def test_dynamic_mastery_filter_is_conservative_for_known_active_candidates(tmp_path):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        "add_mastery = { amount = 100 sub_doctrine = ROOT.starting_doctrine }\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 1}


def test_unresolved_track_index_prevents_mastery_reward_inference(tmp_path):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        "add_mastery = { amount = 100 sub_doctrine = centralized_command index = 0 }\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 1}


def test_unresolved_subdoctrine_track_selector_is_conservative_in_its_folder(tmp_path):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = { sub_doctrine = centralized_command folder = land track = 0 }\n"
        "add_mastery = { amount = 100 sub_doctrine = centralized_command }\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {}


def test_doctrine_without_row_modifier_does_not_hide_another_active_doctrines_bonus(
    tmp_path,
):
    doctrines = (
        _DOCTRINES + "other_command = {\n\ttrack = another_structure_doctrine\n}\n"
    )
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", doctrines)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\nset_sub_doctrine = other_command\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 1}


@pytest.mark.parametrize("amount, expected_rows", [(100, 1), (200, 2)])
def test_second_mastery_reward_uses_cumulative_cost(amount, expected_rows, tmp_path):
    doctrine = _DOCTRINES.replace(
        "\t\t\tadditional_brigade_column_size = 1\n",
        "\t\t\tplanning_speed = 0.05\n",
        1,
    ).replace(
        "\t\t}\n\t}\n}\nmobile_infantry",
        "\t\t}\n"
        "\t\tdivision_structure_two = {\n"
        "\t\t\tadditional_brigade_column_size = 1\n"
        "\t\t}\n"
        "\t}\n}\nmobile_infantry",
    )
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", doctrine)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "set_sub_doctrine = centralized_command\n"
        f"add_mastery = {{ amount = {amount} sub_doctrine = centralized_command }}\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": expected_rows}


def test_root_doctrine_assignment_precedes_later_in_file_dated_assignment(tmp_path):
    doctrines = _DOCTRINES + "other_command = {\n\ttrack = structure_doctrine\n}\n"
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", doctrines)
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "2000.1.1 = {\n\tset_sub_doctrine = other_command\n}\n"
        "set_sub_doctrine = centralized_command\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {}


def test_dated_doctrine_assignments_replay_in_date_order_not_source_order(tmp_path):
    doctrines = _DOCTRINES + "other_command = {\n\ttrack = structure_doctrine\n}\n"
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", doctrines)
    _write(
        tmp_path,
        "common/bookmarks/default.txt",
        "bookmark = {\n\tdefault = yes\n\tdate = 2002.1.1.12\n}\n",
    )
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "2001.1.1 = {\n\tset_sub_doctrine = other_command\n}\n"
        "2000.1.1 = {\n\tset_sub_doctrine = centralized_command\n}\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {}


def test_dated_doctrine_and_mastery_after_default_bookmark_do_not_count(tmp_path):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(tmp_path, "common/doctrines/subdoctrines/land/combat.txt", _DOCTRINES)
    _write(
        tmp_path,
        "common/bookmarks/default.txt",
        "bookmark = {\n\tdefault = yes\n\tdate = 2000.1.1.12\n}\n",
    )
    _write(
        tmp_path,
        "history/countries/UKR - Ukraine.txt",
        "2000.1.1 = {\n\tset_sub_doctrine = centralized_command\n}\n"
        "2001.1.1 = {\n"
        "\tadd_mastery = { amount = 100 sub_doctrine = centralized_command }\n}\n",
    )

    assert read_template_limits(str(tmp_path)).column_bonus == {"UKR": 1}


def test_limits_fall_back_to_vanilla_without_defines(tmp_path):
    assert read_template_limits(str(tmp_path)) == TemplateLimits(
        grids={"regiments": (5, 5), "regimental_support": (5, 1), "support": (1, 5)},
        open_rows=4,
        required_battalions=(3,),
        column_bonus={},
    )


@pytest.mark.parametrize(
    "rel",
    [
        _OOB,
        "common/national_focus/tst.txt",
        "common/scripted_effects/00_AI_scripted_effects.txt",
        "events/Tst.txt",
    ],
)
def test_full_run_reports_both_categories_for_every_template_source(tmp_path, rel):
    _write(tmp_path, "common/defines/MD_defines.lua", _DEFINES)
    _write(
        tmp_path,
        rel,
        _template(regiments=[(0, 0), (0, 2)])
        + _template(regiments=[(0, y) for y in range(4)]),
    )

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_all_validations()

    assert [
        (issue.severity, issue.category, issue.file, issue.line)
        for issue in validator._issues
        if issue.category.startswith("template-")
    ] == [
        ("error", "template-slot", rel, 5),
        ("warning", "template-locked-row", rel, 14),
    ]
