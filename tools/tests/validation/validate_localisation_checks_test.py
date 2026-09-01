"""Coverage for the localisation checks that are not exercised elsewhere.

The pool workers (`process_*`) are called directly: the validator runs them in a
real multiprocessing Pool, so driving them through `run_validations` proves
nothing about their branches. The cross-reference checks
(`validate_add_resistance_tooltip`, `validate_orphaned_tooltip_keys`,
`validate_opinion_modifiers`) are driven through their public methods.
"""

import os

import pytest
import validate_localisation as VL


def _write(path, body, encoding="utf-8-sig"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as handle:
        handle.write(body)
    return str(path)


def _english(tmp_path, name, body):
    return _write(tmp_path / "localisation" / "english" / name, body)


def _txt(tmp_path, relative, body):
    return _write(tmp_path / relative, body, encoding="utf-8")


# --- § colour-code balance --------------------------------------------------


def test_unclosed_colour_codes_report_the_expected_count(tmp_path):
    path = _english(tmp_path, "a_l_english.yml", 'l_english:\n A:0 "§Ya §Yb"\n')
    results = VL.process_yml_for_syntax((path, ["Y"], frozenset()))
    assert len(results) == 1
    assert isinstance(results[0], str)
    assert "expected 1 § but got 0" in results[0].replace("§!", "§")


def test_balanced_colour_codes_are_clean(tmp_path):
    path = _english(tmp_path, "b_l_english.yml", 'l_english:\n B:0 "§Ya§! §Yb§!"\n')
    assert VL.process_yml_for_syntax((path, ["Y"], frozenset())) == []


# --- mandatory l_english: line ----------------------------------------------


def test_empty_loc_file_is_not_reported_as_missing_the_header(tmp_path):
    path = _english(tmp_path, "empty_l_english.yml", "")
    assert VL.process_yml_for_mandatory((path,)) == []


def test_loc_file_without_the_header_is_reported(tmp_path):
    path = _english(tmp_path, "headless_l_english.yml", ' KEY:0 "value"\n')
    assert VL.process_yml_for_mandatory((path,)) == [
        "headless_l_english.yml - l_english: line is absent"
    ]


# --- typo watchlist ---------------------------------------------------------


def test_exempt_phrase_suppresses_a_watchlist_hit(tmp_path, monkeypatch):
    path = _english(tmp_path, "typo_l_english.yml", 'l_english:\n T:0 "seperate"\n')
    assert len(VL.process_yml_for_typos((path,))) == 1

    monkeypatch.setattr(VL, "_TYPO_EXEMPTIONS", {"seperate"})
    assert VL.process_yml_for_typos((path,)) == []


# --- localization_key = references ------------------------------------------


def _init_worker_keys(monkeypatch, valid=(), scripted=()):
    monkeypatch.setattr(VL, "_W_VALID_KEYS", frozenset(valid))
    monkeypatch.setattr(VL, "_W_SCRIPTED_KEYS", frozenset(scripted))


@pytest.mark.parametrize(
    "key",
    [
        "[GetSomething]",
        'PIPED|KEY"',
        "EUXXX_EP_agenda_vote",
        "EU12",
        "GFX_some_icon",
        "EFFECT_SOMETHING",
        "TRIGGER_SOMETHING",
    ],
)
def test_loc_key_reference_exemptions(tmp_path, monkeypatch, key):
    _init_worker_keys(monkeypatch)
    path = _txt(tmp_path, "common/refs.txt", f"localization_key = {key}\n")
    assert VL.process_txt_for_loc_key_refs(path) == []


def test_file_without_localization_key_is_not_scanned(tmp_path, monkeypatch):
    _init_worker_keys(monkeypatch)
    path = _txt(tmp_path, "common/plain.txt", "stability_factor = 0.1\n")
    assert VL.process_txt_for_loc_key_refs(path) == []


def test_scripted_loc_names_satisfy_a_localization_key_reference(tmp_path, monkeypatch):
    _init_worker_keys(monkeypatch, scripted={"MyScriptedLoc"})
    path = _txt(tmp_path, "common/refs.txt", "localization_key = MyScriptedLoc\n")
    assert VL.process_txt_for_loc_key_refs(path) == []


@pytest.mark.parametrize(
    "key",
    [
        "[GetSomething]",
        'PIPED|KEY"',
        "GFX_some_icon",
        "cannot_go_higher_than_x",
        "cannot_go_lower_than_x",
    ],
)
def test_custom_tooltip_exemptions(tmp_path, monkeypatch, key):
    _init_worker_keys(monkeypatch)
    path = _txt(tmp_path, "common/tt.txt", f"custom_effect_tooltip = {key}\n")
    assert VL.process_txt_for_custom_tt_refs(path) == []


def test_file_without_a_custom_tooltip_is_not_scanned(tmp_path, monkeypatch):
    _init_worker_keys(monkeypatch)
    path = _txt(tmp_path, "common/plain.txt", "stability_factor = 0.1\n")
    assert VL.process_txt_for_custom_tt_refs(path) == []


def test_unknown_loc_key_reference_is_reported(tmp_path, monkeypatch):
    _init_worker_keys(monkeypatch, valid={"KNOWN_KEY"})
    path = _txt(
        tmp_path,
        "common/refs.txt",
        "localization_key = KNOWN_KEY\nlocalization_key = MISSING_KEY\n",
    )
    assert VL.process_txt_for_loc_key_refs(path) == ["MISSING_KEY"]


def test_loc_key_scan_skips_ignored_directories(tmp_path, monkeypatch):
    _init_worker_keys(monkeypatch)
    path = _txt(tmp_path, "docs/refs.txt", "localization_key = MISSING_KEY\n")
    assert VL.process_txt_for_loc_key_refs(path) == []


def test_custom_tooltip_scan_skips_ignored_directories(tmp_path, monkeypatch):
    _init_worker_keys(monkeypatch)
    path = _txt(tmp_path, "docs/tt.txt", "custom_effect_tooltip = MISSING_TT\n")
    assert VL.process_txt_for_custom_tt_refs(path) == []


def test_custom_tooltip_reference_is_reported(tmp_path, monkeypatch):
    _init_worker_keys(monkeypatch, valid={"KNOWN_TT"})
    path = _txt(
        tmp_path,
        "common/tt.txt",
        "custom_effect_tooltip = KNOWN_TT\ncustom_effect_tooltip = MISSING_TT\n",
    )
    assert VL.process_txt_for_custom_tt_refs(path) == ["MISSING_TT - tt.txt"]


# --- NOT-block extraction ---------------------------------------------------


def test_not_blocks_are_brace_balanced():
    text = "NOT = { has_idea = a OR = { has_idea = b } }\nNOT = { has_idea = c }\n"
    bodies = VL._extract_not_blocks(text)
    assert len(bodies) == 2
    assert "OR = { has_idea = b }" in bodies[0]


def test_unbalanced_not_block_stops_the_scan():
    assert VL._extract_not_blocks("NOT = { has_idea = a\n") == []


def test_orphan_tooltip_scan_skips_ignored_directories(tmp_path):
    path = _txt(tmp_path, "docs/tt.txt", "tooltip = SOME_TT\n")
    assert VL.process_file_for_orphan_tt_refs((path, [r"tooltip\s*=\s*(\S+)"])) == (
        set(),
        [],
        set(),
    )


# --- skipped-file key harvesting --------------------------------------------


def test_keys_defined_in_skipped_loc_files_are_collected(tmp_path):
    _english(
        tmp_path,
        "00_operations_l_english.yml",
        'l_english:\n# comment\n OPERATION_KEY:0 "value"\n no_colon_line\n',
    )
    _english(tmp_path, "normal_l_english.yml", 'l_english:\n NORMAL_KEY:0 "value"\n')

    keys = VL._get_skipped_loc_keys(str(tmp_path))
    assert "OPERATION_KEY" in keys
    assert "NORMAL_KEY" not in keys


def test_skipped_file_without_the_english_header_is_ignored(tmp_path):
    _english(tmp_path, "00_operations_l_english.yml", ' OPERATION_KEY:0 "value"\n')
    assert VL._get_skipped_loc_keys(str(tmp_path)) == set()


def test_substitution_key_scan_tolerates_an_unreadable_file(tmp_path):
    good = _english(tmp_path, "subst_l_english.yml", 'l_english:\n A:0 "$gip$"\n')
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    keys = validator._collect_substitution_keys([str(tmp_path / "gone.yml"), good])
    assert keys == frozenset({"gip"})


# --- add_resistance_target tooltips -----------------------------------------


def _resistance_file(tmp_path, relative, tooltip_line):
    return _txt(
        tmp_path,
        relative,
        "test_effect = {\n"
        "\tadd_resistance_target = {\n"
        f"{tooltip_line}"
        "\t\tvalue = 0.1\n"
        "\t}\n"
        "}\n",
    )


def test_resistance_tooltip_without_a_loc_key_is_reported(tmp_path):
    _resistance_file(tmp_path, "common/res.txt", "\t\ttooltip = MISSING_RES_TT\n")
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_add_resistance_tooltip({})
    assert [i.message for i in validator._issues] == [
        "MISSING_RES_TT - localization key not found"
    ]


def test_resistance_tooltip_with_the_value_token_is_clean(tmp_path):
    _resistance_file(tmp_path, "common/res.txt", "\t\ttooltip = RES_TT\n")
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_add_resistance_tooltip({"RES_TT": '"$VALUE|=-%0$ resistance"'})
    assert validator._issues == []


def test_resistance_tooltip_missing_the_value_token_is_reported(tmp_path):
    _resistance_file(tmp_path, "common/res.txt", "\t\ttooltip = RES_TT\n")
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_add_resistance_tooltip({"RES_TT": '"flat resistance"'})
    assert "missing $VALUE|=-%0$" in validator._issues[0].message


def test_resistance_tooltip_scan_skips_ignored_directories(tmp_path):
    _resistance_file(tmp_path, "docs/res.txt", "\t\ttooltip = MISSING_RES_TT\n")
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_add_resistance_tooltip({})
    assert validator._issues == []


def test_resistance_tooltip_with_an_empty_assignment_yields_nothing(tmp_path):
    # `tooltip =` with no value parses to no key at all; the block is neither
    # reported as untooltipped nor cross-referenced.
    _resistance_file(tmp_path, "common/res.txt", "\t\ttooltip =\n")
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_add_resistance_tooltip({})
    assert validator._issues == []


# --- orphaned tooltip keys --------------------------------------------------


def _orphaned_messages(tmp_path, loc_keys):
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_orphaned_tooltip_keys(loc_keys, set(), set())
    return [issue.message for issue in validator._issues]


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
    assert _orphaned_messages(tmp_path, loc_keys) == ["orphan_tt"]


def test_not_variant_is_only_forgiven_when_its_base_is_negated(tmp_path):
    _txt(
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
    assert _orphaned_messages(tmp_path, loc_keys) == ["tooltip_positive_NOT"]


def test_repeated_dynamic_token_is_compiled_once(tmp_path):
    for name in ("a.txt", "b.txt"):
        _txt(
            tmp_path,
            f"common/{name}",
            "custom_effect_tooltip = tooltip_EU_[EUXXX]_approve\n",
        )
    loc_keys = {"tooltip_EU_FRA_approve": "x", "tooltip_unmatched": "y"}
    assert _orphaned_messages(tmp_path, loc_keys) == ["tooltip_unmatched"]


def test_no_tooltip_named_keys_reports_nothing(tmp_path):
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_orphaned_tooltip_keys({"PLAIN_KEY": "value"}, set(), set())
    assert validator._issues == []


# --- opinion modifiers ------------------------------------------------------


def _opinion_file(tmp_path):
    return _txt(
        tmp_path,
        "common/opinion_modifiers/00_test.txt",
        "opinion_modifiers = {\n"
        "\tlocalised_modifier = {\n\t\tvalue = 10\n\t}\n"
        "\tunlocalised_modifier = {\n\t\tvalue = -10\n\t}\n"
        # A redeclaration keeps the first file it was seen in.
        "\tunlocalised_modifier = {\n\t\tvalue = -20\n\t}\n" "}\n",
    )


def test_opinion_modifier_without_localisation_is_a_warning(tmp_path):
    _opinion_file(tmp_path)
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_opinion_modifiers({"localised_modifier": "Localised"}, set())

    assert validator.errors_found == 0
    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert issue.category == "missing-opinion-modifier-localisation"
    assert issue.message.startswith("unlocalised_modifier - 00_test.txt")


def test_opinion_modifier_localised_by_scripted_loc_is_clean(tmp_path):
    _opinion_file(tmp_path)
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_opinion_modifiers(
        {"localised_modifier": "Localised"}, {"unlocalised_modifier"}
    )
    assert validator._issues == []


def test_opinion_modifier_scan_tolerates_a_vanished_file(tmp_path, monkeypatch):
    _opinion_file(tmp_path)
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    real_collect = validator._collect_files
    monkeypatch.setattr(
        validator,
        "_collect_files",
        lambda patterns, **kw: (
            [str(tmp_path / "gone.txt")] + real_collect(patterns, **kw)
        ),
    )
    validator.validate_opinion_modifiers({}, set())

    assert {i.message.split(" - ")[0] for i in validator._issues} == {
        "localised_modifier",
        "unlocalised_modifier",
    }


# --- staged mode ------------------------------------------------------------


def test_staged_run_without_staged_files_does_nothing(tmp_path):
    _english(tmp_path, "a_l_english.yml", 'l_english:\n A:0 "value"\n')
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.staged_only = True
    validator.staged_files = []
    validator.run_validations()
    assert validator._issues == []


def test_colour_fallback_set_is_used_without_core_gfx(tmp_path):
    assert VL.get_all_colors(str(tmp_path)) == list("WGRBYCMwgrbycm!")


def test_colours_are_parsed_from_core_gfx(tmp_path):
    _write(
        tmp_path / "interface" / "core.gfx",
        "guiTypes = {\n\ttextcolors = {\n\t\tY = { 255 200 0 }\n"
        "\t\tR = { 200 0 0 }\n\t}\n}\n",
        encoding="utf-8",
    )
    assert VL.get_all_colors(str(tmp_path)) == ["Y", "R"]


def test_core_gfx_without_a_textcolors_block_falls_back(tmp_path):
    _write(
        tmp_path / "interface" / "core.gfx",
        "guiTypes = {\n}\n",
        encoding="utf-8",
    )
    assert VL.get_all_colors(str(tmp_path)) == list("WGRBYCMwgrbycm!")


def test_scripted_loc_names_are_harvested(tmp_path):
    _write(
        tmp_path / "common" / "scripted_localisation" / "defs.txt",
        'defined_text = {\n\tname = PlainLoc\n}\ndefined_text = {\n\tname = "QuotedLoc"\n}\n',
        encoding="utf-8",
    )
    assert VL._get_scripted_loc_keys(str(tmp_path)) == {"PlainLoc", "QuotedLoc"}


def test_duplicate_keys_from_skipped_files_are_not_reported(tmp_path):
    validator = VL.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_duplicated_keys(["DUP_KEY", "SKIPPED_KEY"], {"SKIPPED_KEY"})
    assert [i.message for i in validator._issues] == ["DUP_KEY"]


def test_loc_keys_and_duplicates_are_read_from_english_only(tmp_path):
    _english(
        tmp_path,
        "a_l_english.yml",
        'l_english:\n# comment\n KEY_ONE:0 "one"\n KEY_ONE:0 "again"\n',
    )
    _english(tmp_path, "b_l_english.yml", 'l_english:\n KEY_TWO:0 "two"\n')
    _write(
        tmp_path / "localisation" / "french" / "a_l_french.yml",
        'l_french:\n KEY_FR:0 "trois"\n',
    )

    loc_keys, duplicated = VL.get_all_loc_keys(str(tmp_path))

    assert loc_keys["KEY_ONE"] == '"one"'
    assert loc_keys["KEY_TWO"] == '"two"'
    assert "KEY_FR" not in loc_keys
    assert duplicated == ["KEY_ONE"]


def test_files_without_the_english_header_are_not_read_for_keys(tmp_path):
    _english(tmp_path, "orphan_l_english.yml", ' KEY_ORPHAN:0 "value"\n')
    loc_keys, duplicated = VL.get_all_loc_keys(str(tmp_path))
    assert loc_keys == {}
    assert duplicated == []


def test_issue_paths_use_the_file_basename(tmp_path):
    path = _english(tmp_path, "prose_l_english.yml", 'l_english:\n A:0 "a — b"\n')
    issues = VL.process_yml_for_prose((path,))
    assert [i.file for i in issues] == [os.path.basename(path)]
