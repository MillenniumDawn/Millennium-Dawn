"""The localisation validator's shared .txt pass and its per-file scan shortcuts.

Every check that reads script files now takes its per-file results from one
pass, and several scans skip work no match could need. Each case pins exact
findings, so a shortcut that drops or invents one fails here.
"""

import re

import pytest
import validate_localisation as VL
from shared.suite import write_under_str


def _validator(tmp_path, workers=1):
    return VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=workers)


def _rows(validator):
    return [
        (issue.category, issue.message, issue.file, issue.line)
        for issue in validator._issues
    ]


# --- typo watchlist ---------------------------------------------------------


def test_every_watchlist_entry_is_one_word_token():
    assert all(re.fullmatch(r"\w+", typo) for typo in VL._TYPO_WATCHLIST)


def test_typo_scan_finds_whole_words_on_every_line_shape(tmp_path):
    path = write_under_str(
        tmp_path,
        "localisation/english/typo_l_english.yml",
        "l_english:\r\n"
        ' A:0 "Seperate, sepe[X]rate, seperate2 and #seperate {x}"\r\n'
        ' B:0 "plain words only"\r\n'
        ' C:0 "Café Isreal xseperate"',
    )

    assert VL.process_yml_for_typos((path,)) == [
        "typo_l_english.yml - line 2 - 'Seperate' -> 'separate'",
        "typo_l_english.yml - line 2 - 'seperate' -> 'separate'",
        "typo_l_english.yml - line 2 - 'seperate' -> 'separate'",
        "typo_l_english.yml - line 4 - 'Isreal' -> 'Israel'",
    ]


@pytest.mark.parametrize(
    "value",
    [
        "Seperate!",
        "SEPERATE_x",
        "sepe[x]rate",
        "Café seperate",
        "a seperated b",
        "Disproportinate, bocme",
    ],
)
def test_typo_tokens_match_a_full_regex_scan(value):
    prose = VL._TYPO_RUNTIME_REFERENCE_RE.sub("", value)
    expected = [m.group(0) for m in VL._TYPO_RE.finditer(prose)]

    found = VL._scan_typos_text(f'l_english:\n K:0 "{value}"\n', "t.yml")

    assert [line.split("'")[1] for line in found] == expected


# --- literal-first block openers --------------------------------------------


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


@pytest.mark.parametrize(
    ("text", "spans"),
    [
        ("check_variable = {", [(0, 18)]),
        ("xcheck_variable = {", []),
        ("Öcheck_variable={", []),
        ("\tcheck_variable={", [(1, 17)]),
    ],
)
def test_check_variable_opener_matches_only_where_a_word_boundary_does(text, spans):
    assert [m.span() for m in VL._CHECK_VARIABLE_OPEN_RE.finditer(text)] == spans
    assert spans == [m.span() for m in re.finditer(r"\bcheck_variable\s*=\s*\{", text)]


# --- check_variable / has_variable reads ------------------------------------


def test_script_reads_keep_their_lines_across_crlf_and_skipped_blocks(tmp_path):
    path = write_under_str(
        tmp_path,
        "common/reads.txt",
        "check_variable = { first_var > 0 }\r\n"
        "# check_variable = { commented_var > 0 }\r\n"
        'log = "# { quoted"\r\n'
        "check_variable = { [dyn] > 0 }\r\n"
        "has_variable = has_var\r\n"
        "check_variable = {\r\n"
        "\tmulti_var > 0\r\n"
        "}\r\n"
        "x = { check_variable = { last_var > 0 } }",
    )

    assert VL.process_txt_for_script_var_reads((path,)) == [
        ("has_var", "reads.txt", 5),
        ("first_var", "reads.txt", 1),
        ("multi_var", "reads.txt", 6),
        ("last_var", "reads.txt", 9),
    ]


def test_writes_behind_each_literal_gate_still_count(tmp_path):
    write_under_str(
        tmp_path,
        "common/arrays.txt",
        "x = { add_to_array = { gated_list = 1 } }\n",
    )
    write_under_str(
        tmp_path,
        "common/vars.txt",
        "x = {\n"
        "\t# set_variable = { commented_var = 1 }\n"
        "\tset_variable = { gated_var = 1 }\n"
        "}",
    )
    write_under_str(
        tmp_path,
        "events/reads.txt",
        "x = {\n"
        "\tcheck_variable = { gated_list > 0 }\n"
        "\tcheck_variable = { gated_var > 0 }\n"
        "\tcheck_variable = { commented_var > 0 }\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_unwritten_script_variables()

    assert _rows(validator) == [
        (
            "script-unwritten-variable",
            "commented_var - reads.txt",
            "reads.txt",
            4,
        )
    ]


# --- one .txt pass for several checks ---------------------------------------


def test_each_check_keeps_its_own_file_set(tmp_path):
    """add_resistance_target skips 00_operations files; variable checks do not."""
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
    validator = _validator(tmp_path)

    validator.validate_add_resistance_tooltip({})
    validator.validate_unwritten_script_variables()

    assert _rows(validator) == [
        (
            "add_resistance_target tooltip issues",
            "{ value = 1: missing tooltip",
            "res.txt",
            0,
        )
    ]


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
    validator = _validator(tmp_path)
    loc_keys, scripted = {}, set()

    validator.validate_localization_key_references(loc_keys, scripted)
    validator.validate_custom_tooltip_references(loc_keys, scripted)
    assert len(calls) == 1
    validator.validate_custom_tooltip_references({"MISSING_TT": "x"}, scripted)

    assert len(calls) == 2
    assert [row[1] for row in _rows(validator)] == [
        "MISSING_KEY",
        "MISSING_TT - keys.txt",
    ]


def _pooled_tree(tmp_path):
    write_under_str(
        tmp_path,
        "localisation/english/t_l_english.yml",
        'l_english:\n orphan_tt:0 "x"\n used_tt:0 "y"\n',
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
        validator = _validator(tmp_path, workers=workers)
        validator.run_all_validations()
        return _rows(validator)

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
