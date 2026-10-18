"""Localisation keys and the checks that cross-reference them: duplicates,
localization_key and custom tooltip references, add_resistance_target
tooltips, orphaned tooltip keys, opinion modifiers and raids. Also the run:
which checks it calls, staged mode, and a full run over a synthetic mod.

The pool workers (`process_*`) are called directly: the validator runs them in
a real multiprocessing Pool, so driving them through `run_validations` proves
nothing about their branches.
"""

import re

import pytest
import validate_localisation as VL
from shared.suite import (
    build_validator,
    checks_called_by_run,
    issue_rows,
    write_tree,
    write_under_str,
)
from validator_common import Severity


def _english(tmp_path, name, body):
    return write_under_str(tmp_path, f"localisation/english/{name}", body)


def _messages(validator):
    return [issue.message for issue in validator._issues]


@pytest.fixture
def worker_keys(monkeypatch):
    """Plant the valid and scripted key sets the reference workers read."""

    def plant(valid=(), scripted=()):
        monkeypatch.setattr(VL, "_W_VALID_KEYS", frozenset(valid))
        monkeypatch.setattr(VL, "_W_SCRIPTED_KEYS", frozenset(scripted))

    plant()
    return plant


# ---- loading keys and colours -----------------------------------------------


def test_loc_keys_and_duplicates_are_read_from_english_only(tmp_path):
    _english(
        tmp_path,
        "a_l_english.yml",
        'l_english:\n KEY_ONE:0 "one"\n KEY_ONE:0 "again"\n',
    )
    _english(tmp_path, "b_l_english.yml", 'l_english:\n KEY_TWO:0 "two"\n')
    write_under_str(
        tmp_path,
        "localisation/french/a_l_french.yml",
        'l_french:\n KEY_FR:0 "trois"\n',
    )

    loc_keys, duplicated = VL.get_all_loc_keys(str(tmp_path))

    assert loc_keys == {"KEY_ONE": '"one"', "KEY_TWO": '"two"'}
    assert duplicated == ["KEY_ONE"]


def test_files_without_the_english_header_are_not_read_for_keys(tmp_path):
    _english(tmp_path, "orphan_l_english.yml", ' KEY_ORPHAN:0 "value"\n')
    assert VL.get_all_loc_keys(str(tmp_path)) == ({}, [])


# case: (00_operations file body, keys collected)
_SKIPPED_KEY_CASES = {
    "keys of a skipped file": (
        'l_english:\n OPERATION_KEY:0 "value"\n no_colon_line\n',
        {"OPERATION_KEY"},
    ),
    "skipped file without the header": (' OPERATION_KEY:0 "value"\n', set()),
}


@pytest.mark.parametrize(
    ("body", "expected"), _SKIPPED_KEY_CASES.values(), ids=_SKIPPED_KEY_CASES
)
def test_keys_defined_in_skipped_loc_files(tmp_path, body, expected):
    _english(tmp_path, "00_operations_l_english.yml", body)
    _english(tmp_path, "normal_l_english.yml", 'l_english:\n NORMAL_KEY:0 "value"\n')
    assert VL._get_skipped_loc_keys(str(tmp_path)) == expected


def test_scripted_loc_names_are_harvested(tmp_path):
    write_under_str(
        tmp_path,
        "common/scripted_localisation/defs.txt",
        'defined_text = {\n\tname = PlainLoc\n}\ndefined_text = {\n\tname = "QuotedLoc"\n}\n',
    )
    assert VL._get_scripted_loc_keys(str(tmp_path)) == {"PlainLoc", "QuotedLoc"}


_FALLBACK_COLOURS = list("WGRBYCMwgrbycm!")

# case: (core.gfx body or None for no file, colours)
_COLOUR_CASES = {
    "no core.gfx": (None, _FALLBACK_COLOURS),
    "textcolors block": (
        "guiTypes = {\n\ttextcolors = {\n\t\tY = { 255 200 0 }\n"
        "\t\tR = { 200 0 0 }\n\t}\n}\n",
        ["Y", "R"],
    ),
    "no textcolors block": ("guiTypes = {\n}\n", _FALLBACK_COLOURS),
}


@pytest.mark.parametrize(
    ("body", "expected"), _COLOUR_CASES.values(), ids=_COLOUR_CASES
)
def test_colours_come_from_core_gfx(tmp_path, body, expected):
    if body is not None:
        write_under_str(tmp_path, "interface/core.gfx", body)
    assert VL.get_all_colors(str(tmp_path)) == expected


def test_duplicate_keys_from_skipped_files_are_not_reported(tmp_path):
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_duplicated_keys(["DUP_KEY", "SKIPPED_KEY"], {"SKIPPED_KEY"})
    assert _messages(validator) == ["DUP_KEY"]


# ---- localization_key and custom tooltip references --------------------------


# case: (localization_key value, reported)
_LOC_KEY_REF_CASES = {
    "defined key": ("KNOWN_KEY", []),
    "scripted loc": ("MyScriptedLoc", []),
    "missing key": ("MISSING_KEY", ["MISSING_KEY"]),
    "dynamic": ("[GetSomething]", []),
    "piped": ('PIPED|KEY"', []),
    "EU agenda": ("EUXXX_EP_agenda_vote", []),
    "EU number": ("EU12", []),
    "GFX": ("GFX_some_icon", []),
    "EFFECT": ("EFFECT_SOMETHING", []),
    "TRIGGER": ("TRIGGER_SOMETHING", []),
}


@pytest.mark.parametrize(
    ("key", "expected"), _LOC_KEY_REF_CASES.values(), ids=_LOC_KEY_REF_CASES
)
def test_localization_key_references(tmp_path, worker_keys, key, expected):
    worker_keys(valid={"KNOWN_KEY"}, scripted={"MyScriptedLoc"})
    path = write_under_str(tmp_path, "common/refs.txt", f"localization_key = {key}\n")
    assert VL.process_txt_for_loc_key_refs(path) == expected


# case: (tooltip statement, reported)
_TOOLTIP_REF_CASES = {
    "defined key": ("custom_effect_tooltip = KNOWN_TT", []),
    "scripted loc": ("custom_effect_tooltip = MyScriptedLoc", []),
    "missing key": ("custom_effect_tooltip = MISSING_TT", ["MISSING_TT - tt.txt"]),
    "dynamic": ("custom_effect_tooltip = [GetSomething]", []),
    "piped": ("custom_effect_tooltip = PIPED|KEY", []),
    "quoted": ('custom_effect_tooltip = "QUOTED"', []),
    "GFX": ("custom_effect_tooltip = GFX_some_icon", []),
    "cannot go higher": ("custom_effect_tooltip = cannot_go_higher_than_x", []),
    "cannot go lower": ("custom_effect_tooltip = cannot_go_lower_than_x", []),
    # A nested block in the trigger body must not hide the tooltip key.
    "trigger tooltip behind a nested block": (
        "custom_trigger_tooltip = {\n"
        "\tcheck_variable = { party_pop_array^19 > 0.30 }\n"
        "\ttooltip = MISSING_NESTED_TT\n"
        "}\n"
        "custom_trigger_tooltip = {\n\ttooltip = KNOWN_TT\n}",
        ["MISSING_NESTED_TT - tt.txt"],
    ),
}


@pytest.mark.parametrize(
    ("statement", "expected"), _TOOLTIP_REF_CASES.values(), ids=_TOOLTIP_REF_CASES
)
def test_custom_tooltip_references(tmp_path, worker_keys, statement, expected):
    worker_keys(valid={"KNOWN_TT"}, scripted={"MyScriptedLoc"})
    path = write_under_str(tmp_path, "common/tt.txt", statement + "\n")
    assert VL.process_txt_for_custom_tt_refs(path) == expected


# Every .txt scan skips the ignored directories, such as docs/.
# case: (scan of one file, what it returns for docs/x.txt)
_IGNORED_DIRECTORY_CASES = {
    "localization_key": (VL.process_txt_for_loc_key_refs, []),
    "custom tooltip": (VL.process_txt_for_custom_tt_refs, []),
    "orphan tooltip refs": (
        lambda path: VL.process_file_for_orphan_tt_refs(
            (path, [r"tooltip\s*=\s*(\S+)"])
        ),
        (set(), [], set()),
    ),
    "add_resistance_target": (
        lambda path: VL._scan_resistance_tooltips(path, None),
        [],
    ),
}


@pytest.mark.parametrize(
    ("scan", "expected"),
    _IGNORED_DIRECTORY_CASES.values(),
    ids=_IGNORED_DIRECTORY_CASES,
)
def test_scans_skip_ignored_directories(tmp_path, worker_keys, scan, expected):
    path = write_under_str(
        tmp_path,
        "docs/x.txt",
        "localization_key = MISSING_KEY\n"
        "custom_effect_tooltip = MISSING_TT\n"
        "tooltip = SOME_TT\n"
        "x = {\n\tadd_resistance_target = {\n\t\ttooltip = MISSING_RES_TT\n\t}\n}\n",
    )
    assert scan(path) == expected


def test_key_references_share_one_read_but_follow_new_key_sets(tmp_path, monkeypatch):
    write_under_str(
        tmp_path,
        "common/keys.txt",
        "x = {\n"
        "\tlocalization_key = MISSING_KEY\n"
        "\tcustom_effect_tooltip = MISSING_TT\n"
        "}\n",
    )
    calls = []
    scan = VL._scan_txt_key_refs

    def counting_scan(filename):
        calls.append(filename)
        return scan(filename)

    monkeypatch.setattr(VL, "_scan_txt_key_refs", counting_scan)
    validator = build_validator(VL.Validator, tmp_path)
    loc_keys, scripted = {}, set()

    validator.validate_localization_key_references(loc_keys, scripted)
    validator.validate_custom_tooltip_references(loc_keys, scripted)
    assert len(calls) == 1
    validator.validate_custom_tooltip_references({"MISSING_TT": "x"}, scripted)

    assert len(calls) == 2
    assert _messages(validator) == ["MISSING_KEY", "MISSING_TT - keys.txt"]


# ---- add_resistance_target tooltips ------------------------------------------


def _resistance_block(tooltip_line):
    return (
        "test_effect = {\n"
        "\tadd_resistance_target = {\n"
        f"{tooltip_line}"
        "\t\tvalue = 0.1\n"
        "\t}\n"
        "}\n"
    )


# case: (tooltip line, loc keys, messages)
_RESISTANCE_CASES = {
    "tooltip with the value token": (
        "\t\ttooltip = RES_TT\n",
        {"RES_TT": '"$VALUE|=-%0$ resistance"'},
        [],
    ),
    "tooltip missing the value token": (
        "\t\ttooltip = RES_TT\n",
        {"RES_TT": '"flat resistance"'},
        ["RES_TT - missing $VALUE|=-%0$ in loc value"],
    ),
    "tooltip without a loc key": (
        "\t\ttooltip = MISSING_RES_TT\n",
        {},
        ["MISSING_RES_TT - localization key not found"],
    ),
    "vanilla OTT_ tooltip": ("\t\ttooltip = OTT_vanilla\n", {}, []),
    "no tooltip": ("", {}, ["{ value = 0.1: missing tooltip"]),
    # `tooltip =` with no value parses to no key: neither reported as
    # untooltipped nor cross-referenced.
    "empty tooltip assignment": ("\t\ttooltip =\n", {}, []),
}


@pytest.mark.parametrize(
    ("tooltip_line", "loc_keys", "expected"),
    _RESISTANCE_CASES.values(),
    ids=_RESISTANCE_CASES,
)
def test_add_resistance_tooltip(tmp_path, tooltip_line, loc_keys, expected):
    write_under_str(tmp_path, "common/res.txt", _resistance_block(tooltip_line))
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_add_resistance_tooltip(loc_keys)
    assert _messages(validator) == expected


# The resistance check skips 00_operations files; the variable checks do not.
def test_each_check_keeps_its_own_file_set(tmp_path):
    write_under_str(
        tmp_path,
        "common/00_operations.txt",
        "x = {\n"
        "\tadd_resistance_target = {\n"
        "\t\tvalue = 1\n"
        "\t}\n"
        "\tset_variable = { ops_var = 1 }\n"
        "}\n",
    )
    write_under_str(
        tmp_path,
        "common/res.txt",
        "x = {\n"
        "\tadd_resistance_target = {\n"
        "\t\tvalue = 1\n"
        "\t}\n"
        "\tcheck_variable = { ops_var > 0 }\n"
        "}\n",
    )
    validator = build_validator(VL.Validator, tmp_path)

    validator.validate_add_resistance_tooltip({})
    validator.validate_unwritten_script_variables()

    assert _messages(validator) == ["{ value = 1: missing tooltip"]


# ---- NOT blocks and orphaned tooltip keys ------------------------------------


# case: (text, NOT block bodies)
_NOT_BLOCK_CASES = {
    "brace balanced": (
        "NOT = { has_idea = a OR = { has_idea = b } }\nNOT = { has_idea = c }\n",
        [" has_idea = a OR = { has_idea = b } ", " has_idea = c "],
    ),
    "unbalanced block stops the scan": ("NOT = { has_idea = a\n", []),
}


@pytest.mark.parametrize(
    ("text", "expected"), _NOT_BLOCK_CASES.values(), ids=_NOT_BLOCK_CASES
)
def test_not_blocks(text, expected):
    assert VL._extract_not_blocks(text) == expected


# The look-behind stands in for a leading \b, so each case must agree with it.
@pytest.mark.parametrize(
    ("text", "spans"),
    [
        ("NOT = { a }", [(0, 7)]),
        ("xNOT = {", []),
        ("_NOT={", []),
        ("ÖNOT = {", []),
        ("a.NOT = {", [(2, 9)]),
        ("\nNOT\n=\n{", [(1, 8)]),
    ],
)
def test_not_opener_matches_only_where_a_word_boundary_does(text, spans):
    assert [m.span() for m in VL._NOT_OPEN_RE.finditer(text)] == spans
    assert spans == [m.span() for m in re.finditer(r"\bNOT\s*=\s*\{", text)]


def _orphaned(tmp_path, loc_keys, skipped=(), scripted=()):
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_orphaned_tooltip_keys(loc_keys, set(skipped), set(scripted))
    return _messages(validator)


# A tooltip-named key ends in _tt or _TT or starts with tooltip_.
# case: (loc key, keys of skipped files, scripted loc names, orphans reported)
_ORPHAN_KEY_CASES = {
    "_tt suffix": ("a_tt", (), (), ["a_tt"]),
    "_TT suffix": ("a_TT", (), (), ["a_TT"]),
    "tooltip_ prefix": ("tooltip_a", (), (), ["tooltip_a"]),
    "not tooltip-named": ("PLAIN_KEY", (), (), []),
    "defined in a skipped file": ("a_tt", ("a_tt",), (), []),
    "named by scripted loc": ("a_tt", (), ("a_tt",), []),
    "cannot go higher": ("cannot_go_higher_than_x_tt", (), (), []),
    "cannot go lower": ("cannot_go_lower_than_x_tt", (), (), []),
    "operative mission": ("OPERATIVE_MISSION_x_tt", (), (), []),
}


@pytest.mark.parametrize(
    ("key", "skipped", "scripted", "expected"),
    _ORPHAN_KEY_CASES.values(),
    ids=_ORPHAN_KEY_CASES,
)
def test_orphaned_tooltip_keys(tmp_path, key, skipped, scripted, expected):
    assert _orphaned(tmp_path, {key: "x"}, skipped, scripted) == expected


def test_tooltip_key_referenced_only_through_a_loc_substitution_is_not_orphaned(
    tmp_path,
):
    loc_keys = {
        # The second substitution names a key nothing defines, so it grants
        # nothing; only $used_tt$ counts as a reference.
        "wrapper_key": "prefix $used_tt$ $undefined_tt$ suffix",
        "used_tt": "used",
        "orphan_tt": "orphan",
    }
    assert _orphaned(tmp_path, loc_keys) == ["orphan_tt"]


def test_not_variant_is_only_forgiven_when_its_base_is_negated(tmp_path):
    write_under_str(
        tmp_path,
        "common/gates.txt",
        "trigger = {\n"
        "\tNOT = { custom_trigger_tooltip = { tooltip = tooltip_negated } }\n"
        "\tcustom_trigger_tooltip = { tooltip = tooltip_positive }\n"
        "}\n",
    )
    loc_keys = {
        "tooltip_negated": "a",
        "tooltip_negated_NOT": "b",
        "tooltip_positive": "c",
        "tooltip_positive_NOT": "d",
    }
    assert _orphaned(tmp_path, loc_keys) == ["tooltip_positive_NOT"]


def test_repeated_dynamic_token_is_compiled_once(tmp_path):
    for name in ("a.txt", "b.txt"):
        write_under_str(
            tmp_path,
            f"common/{name}",
            "custom_effect_tooltip = tooltip_EU_[EUXXX]_approve\n",
        )
    loc_keys = {"tooltip_EU_FRA_approve": "x", "tooltip_unmatched": "y"}
    assert _orphaned(tmp_path, loc_keys) == ["tooltip_unmatched"]


# ---- opinion modifiers and raids ---------------------------------------------


def _opinion_file(tmp_path):
    return write_under_str(
        tmp_path,
        "common/opinion_modifiers/00_test.txt",
        "opinion_modifiers = {\n"
        "\tlocalised_modifier = {\n\t\tvalue = 10\n\t}\n"
        "\tunlocalised_modifier = {\n\t\tvalue = -10\n\t}\n"
        "\tunlocalised_modifier = {\n\t\tvalue = -20\n\t}\n"
        "}\n",
    )


def test_opinion_modifier_without_localisation_is_a_warning(tmp_path):
    _opinion_file(tmp_path)
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_opinion_modifiers({"localised_modifier": "Localised"}, set())

    assert [(i.severity, i.category) for i in validator._issues] == [
        (Severity.WARNING, "missing-opinion-modifier-localisation")
    ]
    assert validator._issues[0].message.startswith("unlocalised_modifier - 00_test.txt")


def test_opinion_modifier_localised_by_scripted_loc_is_clean(tmp_path):
    _opinion_file(tmp_path)
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_opinion_modifiers(
        {"localised_modifier": "Localised"}, {"unlocalised_modifier"}
    )
    assert validator._issues == []


def test_opinion_modifier_scan_tolerates_a_vanished_file(tmp_path, monkeypatch):
    _opinion_file(tmp_path)
    validator = build_validator(VL.Validator, tmp_path)
    real_collect = validator._collect_files
    monkeypatch.setattr(
        validator,
        "_collect_files",
        lambda patterns, **kw: [str(tmp_path / "gone.txt")]
        + real_collect(patterns, **kw),
    )
    validator.validate_opinion_modifiers({}, set())

    assert {i.message.split(" - ")[0] for i in validator._issues} == {
        "localised_modifier",
        "unlocalised_modifier",
    }


def _raid_files(tmp_path):
    write_tree(
        tmp_path,
        {
            "common/raids/00_test.txt": "types = {\n"
            "\tlocalised_raid = {\n\t\tcategory = test_raids\n\t}\n"
            "\tunlocalised_raid = {\n\t\tcategory = test_raids\n\t}\n"
            "}\n",
            "common/raids/categories/00_test.txt": "categories = {\n"
            "\ttest_raids = {\n\t\tintel_source = army\n\t}\n}\n",
        },
    )


def test_raid_without_a_desc_is_a_warning(tmp_path):
    _raid_files(tmp_path)
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_raid_localisation(
        {
            "raid_type_localised_raid": "Raid",
            "raid_type_localised_raid_desc": "Desc",
            "raid_type_unlocalised_raid": "Raid",
            "raid_category_test_raids": "Test Raids",
        },
        set(),
    )

    assert [(i.severity, i.category, i.message) for i in validator._issues] == [
        (
            Severity.WARNING,
            "missing-raid-localisation",
            "raid_type_unlocalised_raid_desc - 00_test.txt: raid without localisation",
        )
    ]


def test_raid_types_and_categories_each_need_localisation(tmp_path):
    _raid_files(tmp_path)
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_raid_localisation({}, set())

    assert {i.message.split(" - ")[0] for i in validator._issues} == {
        "raid_category_test_raids",
        "raid_type_localised_raid",
        "raid_type_localised_raid_desc",
        "raid_type_unlocalised_raid",
        "raid_type_unlocalised_raid_desc",
    }


def test_raid_localised_by_scripted_or_vanilla_loc_is_clean(tmp_path):
    write_under_str(
        tmp_path,
        "common/raids/00_test.txt",
        "types = {\n\trescue_captured_general = {\n\t}\n\tscripted_raid = {\n\t}\n}\n",
    )
    validator = build_validator(VL.Validator, tmp_path)
    validator.validate_raid_localisation(
        {}, {"raid_type_scripted_raid", "raid_type_scripted_raid_desc"}
    )
    assert validator._issues == []


# ---- the run -----------------------------------------------------------------


_CROSS_REFERENCE_CHECKS = {
    "validate_localization_key_references",
    "validate_custom_tooltip_references",
    "validate_add_resistance_tooltip",
    "validate_orphaned_tooltip_keys",
    "validate_opinion_modifiers",
    "validate_raid_localisation",
    "validate_variable_references",
    "validate_unwritten_script_variables",
    "validate_targeted_dynamic_variables",
}


# A staged run skips the checks that scan every .txt and .gui file.
@pytest.mark.parametrize("staged_only", [False, True], ids=["full", "staged"])
def test_run_calls_every_check(tmp_path, monkeypatch, staged_only):
    path = _english(tmp_path, "a_l_english.yml", 'l_english:\n A:0 "value"\n')
    monkeypatch.setenv("MD_STAGED_FILES", path)
    validator = build_validator(VL.Validator, tmp_path, staged_only=staged_only)
    called, checks = checks_called_by_run(validator, monkeypatch)
    expected = set(checks) - _CROSS_REFERENCE_CHECKS if staged_only else set(checks)
    assert set(called) == expected


def test_staged_run_without_staged_files_does_nothing(tmp_path):
    _english(tmp_path, "a_l_english.yml", 'l_english:\n A:0 "x"\n A:0 "y"\n')
    validator = build_validator(VL.Validator, tmp_path, staged_only=True)
    validator.staged_files = []
    validator.run_validations()
    assert validator._issues == []


def _synthetic_mod(tmp_path):
    write_tree(
        tmp_path,
        {
            "localisation/english/main_l_english.yml": "l_english:\n"
            ' dup: "one"\n'
            ' dup: "two"\n'
            ' skipped_dup: "main copy"\n'
            ' orphan_tt: "never used"\n'
            ' used_tt: "used"\n'
            ' resistance_bad: "bad value"\n',
            "localisation/english/00_operations_l_english.yml": "l_english:\n"
            ' skipped_dup: "skipped copy"\n'
            ' skipped_tt: "intentionally skipped"\n',
            "common/scripted_localisation/keys.txt": "defined_text = {\n"
            "\tname = scripted_key\n}\n",
            "events/loc_refs.txt": "localization_key = missing_key\n"
            "localization_key = scripted_key\n"
            "tooltip = used_tt\n"
            "x = {\n\tadd_resistance_target = {\n\t\ttooltip = resistance_bad\n\t}\n}\n",
        },
    )


def test_full_run_passes_each_check_its_keys(tmp_path):
    _synthetic_mod(tmp_path)
    validator = build_validator(VL.Validator, tmp_path)
    validator.run_all_validations()
    assert [row[1] for row in issue_rows(validator)] == [
        "dup",
        "missing_key",
        "orphan_tt",
        "resistance_bad - missing $VALUE|=-%0$ in loc value",
    ]


def test_clean_tree_passes_every_check(tmp_path):
    _english(tmp_path, "a_l_english.yml", 'l_english:\n valid: "plain"\n')
    validator = build_validator(VL.Validator, tmp_path)
    assert validator.run_all_validations() == 0
    assert validator._issues == []


def _pooled_tree(tmp_path):
    _english(
        tmp_path, "t_l_english.yml", 'l_english:\n orphan_tt: "x"\n used_tt: "y"\n'
    )
    for index in range(12):
        write_under_str(
            tmp_path,
            f"common/scripted_effects/f{index:02}.txt",
            f"fx_{index} = {{\n"
            "\tcustom_effect_tooltip = used_tt\n"
            f"\tset_variable = {{ written_{index} = 1 }}\n"
            f"\tcheck_variable = {{ unwritten_{index} > 0 }}\n"
            "\tadd_resistance_target = {\n"
            "\t\ttooltip = MISSING_RES_TT\n"
            "\t}\n"
            "}\n",
        )


def test_pooled_run_matches_the_in_process_run(tmp_path, monkeypatch, pool_sizes):
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    _pooled_tree(tmp_path)

    def run(workers):
        validator = VL.Validator(
            mod_path=str(tmp_path), use_colors=False, workers=workers
        )
        validator.run_all_validations()
        return [
            (issue.category, issue.message, issue.file, issue.line)
            for issue in validator._issues
        ]

    pooled = run(2)
    assert pool_sizes and set(pool_sizes) == {2}
    assert pooled == run(1)
    # Files come back in directory order, so compare each check's rows as a set.
    assert sorted(pooled) == sorted(
        [("add_resistance_target tooltip issues", _MISSING_RES, "", 0)] * 12
        + [(_ORPHANED, "orphan_tt", "", 0)]
        + [
            (
                "script-unwritten-variable",
                f"unwritten_{index} - f{index:02}.txt",
                f"f{index:02}.txt",
                4,
            )
            for index in range(12)
        ]
    )


_MISSING_RES = "MISSING_RES_TT - localization key not found"
_ORPHANED = "Orphaned tooltip keys (defined in loc but never referenced)"
