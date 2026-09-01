"""Behavior tests for the idea validator's checks and its command line.

Each test builds a miniature mod under tmp_path and drives one check, so the
assertions are on the findings a reviewer would see rather than on internals.
"""

import argparse
import runpy
import sys

import pytest
import validate_ideas
from shared.suite import write_under as _write
from validate_ideas import IdeaIssue, Validator, _add_extra_args

IDEA_TAGS = """idea_categories = {
\thidden_ideas = { hidden = yes }
\tcountry = { type = national_spirit }
\tpolitical_advisor = { slot = political_advisor }
}
"""

QUALITY_IDEAS = """ideas = {
\tcountry = {
\t\tCANCEL_idea = {
\t\t\tcancel = { always = no }
\t\t\tpicture = shared
\t\t}
\t\tLOG_idea = {
\t\t\ton_add = {
\t\t\t\tlog = "traced"
\t\t\t}
\t\t\tpicture = shared
\t\t}
\t\tCIVIL_idea = {
\t\t\tallowed_civil_war = { always = no }
\t\t\tpicture = shared
\t\t}
\t}
\tpolitical_advisor = {
\t\tTAG_advisor = {
\t\t\tallowed = { tag = ISR }
\t\t\tpicture = shared
\t\t}
\t\tTAG_advisor_two = {
\t\t\tallowed = { original_tag = ISR tag = ISR }
\t\t\tpicture = shared
\t\t}
\t}
}
"""

RUN_IDEAS = """ideas = {
\tcountry = {
\t\tTIER_one = {
\t\t\tpicture = shared
\t\t}
\t\tTIER_two = {
\t\t\tpicture = shared
\t\t}
\t\tDEAD_spirit = {
\t\t\tpicture = shared
\t\t}
\t}
}
"""

RUN_GRANTS = """grant = {
\tadd_ideas = TIER_one
\tadd_ideas = TIER_two
}
"""

RUN_LOC = (
    " l_english:\n"
    ' TIER_one:0 "Shared Name"\n'
    ' TIER_one_desc:0 "Desc"\n'
    ' TIER_two:0 "Shared Name"\n'
    ' TIER_two_desc:0 "Desc"\n'
)

RUN_GFX = (
    'spriteType = { name = "GFX_idea_shared" }\n'
    'spriteType = { name = "GFX_idea_categories" noOfFrames = 2 }\n'
)


def _validator(root, **kwargs):
    kwargs.setdefault("unused_ideas", False)
    return Validator(str(root), use_colors=False, workers=1, **kwargs)


def _findings(validator):
    return sorted(
        (issue.category, issue.message, issue.file, issue.line)
        for issue in validator._issues
    )


def _write_run_mod(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(tmp_path, "common/ideas/test.txt", RUN_IDEAS)
    _write(tmp_path, "common/synchronized_dynamic_tokens/MD_tokens.txt", "")
    _write(tmp_path, "events/MD_grants.txt", RUN_GRANTS)
    _write(tmp_path, "localisation/english/MD_test_l_english.yml", RUN_LOC)
    _write(tmp_path, "interface/ideas.gfx", RUN_GFX)


def test_quality_issues_carry_their_idea_file_and_line(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(tmp_path, "common/ideas/quality.txt", QUALITY_IDEAS)
    _write(tmp_path, "common/ideas/placeholder.txt", "")
    validator = _validator(tmp_path)
    _defined, issues_by_file, _ideas_by_file = validator._parse_all_ideas()

    validator.validate_idea_quality(issues_by_file)

    assert sorted(
        (issue.line, issue.message, issue.file) for issue in validator._issues
    ) == [
        (
            3,
            "'CANCEL_idea' has cancel = { always = no } (checked hourly, always false)",
            "common/ideas/quality.txt",
        ),
        (
            7,
            "'LOG_idea' has on_add = { log = ... } with no real effects"
            " (drop the on_add block — tracing-only logs are dead weight)",
            "common/ideas/quality.txt",
        ),
        (
            14,
            "redundant allowed_civil_war = { always = no }",
            "common/ideas/quality.txt",
        ),
        (
            19,
            "'TAG_advisor' uses tag = ISR in allowed"
            " (use original_tag for civil war safety)",
            "common/ideas/quality.txt",
        ),
        (
            23,
            "'TAG_advisor_two' has both tag and original_tag = ISR in allowed"
            " (drop the tag = ...; original_tag already restricts it)",
            "common/ideas/quality.txt",
        ),
    ]
    assert validator.warnings_found == 5


def test_quality_report_ignores_an_issue_type_it_has_no_message_for(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    validator = _validator(tmp_path)

    validator.validate_idea_quality(
        {
            str(tmp_path / "common" / "ideas" / "quality.txt"): [
                IdeaIssue("KNOWN_idea", "country", 4, "cancel-always-no"),
                IdeaIssue("ODD_idea", "country", 9, "not-a-rendered-type"),
            ]
        }
    )

    assert [issue.line for issue in validator._issues] == [4]


def test_character_idea_tokens_join_the_defined_set(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(
        tmp_path,
        "common/ideas/clean.txt",
        "ideas = {\n\tcountry = {\n\t\tCLEAN_idea = { picture = x }\n\t}\n}\n",
    )
    _write(
        tmp_path,
        "common/characters/TAG.txt",
        "characters = {\n"
        "\tTAG_leader = {\n"
        "\t\tadvisor = { idea_token = TAG_leader_token }\n"
        "\t\tadvisor = { idea_token = TAG_leader_token }\n"
        "\t}\n"
        "}\n",
    )
    _write(
        tmp_path,
        "common/characters/OTH.txt",
        "characters = {\n\tOTH_leader = {\n\t\tcountry_leader = { ideology = a }\n\t}\n}\n",
    )
    validator = _validator(tmp_path)

    defined, issues_by_file, ideas_by_file = validator._parse_all_ideas()

    assert defined["TAG_leader_token"] == ("character", None, None)
    assert defined["CLEAN_idea"][0] == "country"
    assert issues_by_file == {}
    assert list(ideas_by_file.values()) == [["CLEAN_idea"]]


def test_repeated_undefined_reference_is_reported_once(tmp_path):
    _write(
        tmp_path,
        "events/MD_test.txt",
        "option = {\n\thas_idea = nope_idea\n\thas_idea = nope_idea\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_undefined_idea_refs({})

    assert [issue.message for issue in validator._issues] == [
        "MD_test.txt: undefined idea reference 'nope_idea'"
    ]


def test_missing_localisation_is_grouped_by_category(tmp_path):
    _write(
        tmp_path,
        "localisation/english/MD_test_l_english.yml",
        ' l_english:\n TAG_present:0 "Present"\n TAG_present_desc:0 "Desc"\n',
    )
    validator = _validator(tmp_path)

    validator.validate_missing_localisation(
        {
            "TAG_present": ("country", None, None),
            "TAG_renamed": ("country", "TAG_present", None),
            "TAG_absent": ("hidden_ideas", None, None),
        }
    )

    assert _findings(validator) == [
        (
            "missing-idea-localisation",
            "hidden_ideas: TAG_absent: TAG_absent, TAG_absent_desc",
            "",
            0,
        )
    ]


def test_loc_consolidation_only_suggests_true_duplicates(tmp_path):
    _write(
        tmp_path,
        "localisation/english/MD_test_l_english.yml",
        " l_english:\n"
        ' TIER_one:0 "Shared Name"\n'
        ' TIER_two:0 "Shared Name"\n'
        " TIER_one_desc:0 $TIER_desc$\n"
        ' SOLO_idea:0 "Solo Name"\n'
        ' SPLIT_one:0 "Split Name"\n'
        ' SPLIT_two:0 "Split Name"\n'
        ' SPLIT_one_desc:0 "First"\n'
        ' SPLIT_two_desc:0 "Second"\n'
        ' RENAMED_idea:0 "Shared Name"\n',
    )
    ideas_file = str(_write(tmp_path, "common/ideas/test.txt", "ideas = { }\n"))
    defined: dict[str, tuple[str, str | None, str | None]] = {
        name: ("country", None, None)
        for name in ("TIER_one", "TIER_two", "SOLO_idea", "SPLIT_one", "SPLIT_two")
    }
    defined["RENAMED_idea"] = ("country", "TIER_one", None)
    defined["NO_LOC_idea"] = ("country", None, None)
    validator = _validator(tmp_path)

    validator.validate_loc_consolidation(
        defined, {ideas_file: sorted(defined) + ["UNKNOWN_idea"]}
    )

    assert [issue.message for issue in validator._issues] == [
        "test.txt: 2 ideas share display name '\"Shared Name\"': TIER_one, TIER_two"
        " — set `name = TIER_one` on TIER_two and drop their duplicate loc keys"
    ]


def test_missing_icons_skip_hidden_and_character_categories(tmp_path, no_vanilla_gfx):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(
        tmp_path, "interface/ideas.gfx", 'spriteType = { name = "GFX_idea_known" }\n'
    )
    validator = _validator(tmp_path)

    validator.validate_missing_icons(
        {
            "WITH_pic": ("country", None, "known"),
            "NO_icon": ("country", None, None),
            "HIDDEN_idea": ("hidden_ideas", None, None),
            "CHAR_token": ("character", None, None),
        }
    )

    assert _findings(validator) == [
        (
            "missing-idea-icon",
            "country: NO_icon: auto-icon GFX_idea_NO_icon (undefined)",
            "",
            0,
        )
    ]


def test_sprite_index_includes_vanilla_gfx_files(tmp_path, monkeypatch):
    vanilla = _write(
        tmp_path,
        "vanilla/interface/core.gfx",
        'spriteType = { name = "GFX_idea_vanilla_pic" }\n',
    )
    _write(tmp_path, "interface/ideas.gfx", 'spriteType = { name = "GFX_idea_mod" }\n')
    monkeypatch.setattr(
        "validate_gfx_references._vanilla_gfx_files", lambda: [str(vanilla)]
    )
    validator = _validator(tmp_path)

    sprites = validator._build_idea_sprite_set()

    assert {"GFX_idea_mod", "GFX_idea_vanilla_pic"} <= sprites.defined


def test_category_frame_check_is_skipped_without_the_sprite(tmp_path, monkeypatch):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    monkeypatch.setattr(
        "validate_gfx_references._find_vanilla_interface_dir", lambda: None
    )
    validator = _validator(tmp_path)

    validator.validate_category_icon_frames()

    assert validator._issues == []


def test_category_frame_shortage_names_the_overflow(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "common/idea_tags/00_idea.txt",
        "idea_categories = {\n"
        "\tnational_status = { slot = religion }\n"
        "\tpolitical_advisor = { slot = political_advisor }\n"
        "\teconomy = { slot = economy }\n"
        "}\n",
    )
    _write(
        tmp_path,
        "interface/ideas.gfx",
        'spriteType = { name = "GFX_idea_categories" noOfFrames = 1 }\n',
    )
    monkeypatch.setattr(
        "validate_gfx_references._find_vanilla_interface_dir", lambda: None
    )
    validator = _validator(tmp_path)

    validator.validate_category_icon_frames()

    assert [issue.message for issue in validator._issues] == [
        "3 politics-view idea categories defined but GFX_idea_categories has only "
        "1 frame(s) — these render a missing icon: political_advisor, economy. "
        "Add frames to the sprite (noOfFrames) and the idea_categories.dds strip."
    ]


def _write_unused_mod(tmp_path):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(
        tmp_path,
        "common/ideas/spirits.txt",
        "ideas = {\n"
        "\tcountry = {\n"
        "\t\tUSED_spirit = { picture = x }\n"
        "\t\tDEAD_spirit = { picture = x }\n"
        "\t\tTOKEN_spirit = { picture = x }\n"
        "\t\tMETA_spirit_TAG = { picture = x }\n"
        "\t}\n"
        "\tpolitical_advisor = {\n"
        "\t\tADVISOR_idea = { picture = x }\n"
        "\t}\n"
        "}\n",
    )
    _write(
        tmp_path,
        "common/synchronized_dynamic_tokens/MD_tokens.txt",
        "TOKEN_spirit\n",
    )
    _write(
        tmp_path,
        "events/MD_grants.txt",
        "grant = {\n"
        "\tadd_ideas = USED_spirit\n"
        "\tadd_timed_idea = { idea = META_spirit_[ROOTTAG] days = 30 }\n"
        "}\n",
    )


def test_only_the_never_referenced_spirit_is_flagged_as_unused(tmp_path):
    _write_unused_mod(tmp_path)
    validator = _validator(tmp_path, unused_ideas=True)
    defined, _issues, ideas_by_file = validator._parse_all_ideas()

    validator.validate_unused_ideas(defined, ideas_by_file)

    assert _findings(validator) == [
        (
            "unused-idea",
            "'DEAD_spirit' (country) is defined but never referenced",
            "common/ideas/spirits.txt",
            0,
        )
    ]
    assert validator.warnings_found == 1


def test_staged_mode_limits_unused_ideas_to_staged_files(tmp_path):
    _write_unused_mod(tmp_path)
    _write(
        tmp_path,
        "common/ideas/extra.txt",
        "ideas = {\n\tcountry = {\n\t\tOTHER_dead_spirit = { picture = x }\n\t}\n}\n",
    )
    validator = _validator(tmp_path, unused_ideas=True)
    defined, _issues, ideas_by_file = validator._parse_all_ideas()
    validator.staged_only = True
    validator.staged_files = [str(tmp_path / "common" / "ideas" / "extra.txt")]

    validator.validate_unused_ideas(defined, ideas_by_file)

    assert [issue.message for issue in validator._issues] == [
        "'OTHER_dead_spirit' (country) is defined but never referenced"
    ]


def test_staged_mode_with_no_candidate_ideas_reports_nothing(tmp_path):
    _write_unused_mod(tmp_path)
    validator = _validator(tmp_path, unused_ideas=True)
    defined, _issues, ideas_by_file = validator._parse_all_ideas()
    validator.staged_only = True
    validator.staged_files = ["events/MD_grants.txt"]

    validator.validate_unused_ideas(defined, ideas_by_file)

    assert validator._issues == []


def test_default_run_reports_only_the_always_on_checks(tmp_path, no_vanilla_gfx):
    _write_run_mod(tmp_path)
    validator = Validator(str(tmp_path), use_colors=False, workers=1, unused_ideas=True)

    validator.run_validations()

    assert _findings(validator) == [
        (
            "unused-idea",
            "'DEAD_spirit' (country) is defined but never referenced",
            "common/ideas/test.txt",
            0,
        )
    ]


def test_optional_flags_enable_the_advisory_checks(tmp_path, no_vanilla_gfx):
    _write_run_mod(tmp_path)
    validator = Validator(
        str(tmp_path),
        use_colors=False,
        workers=1,
        unused_ideas=False,
        missing_loc=True,
        suggest_consolidation=True,
    )

    validator.run_validations()

    assert {issue.category for issue in validator._issues} == {
        "loc-consolidation",
        "missing-idea-localisation",
    }
    assert any(
        "DEAD_spirit: DEAD_spirit, DEAD_spirit_desc" in issue.message
        for issue in validator._issues
    )


def test_staged_run_without_staged_idea_files_skips_the_quality_pass(
    tmp_path, no_vanilla_gfx
):
    _write_run_mod(tmp_path)
    _write(tmp_path, "common/ideas/quality.txt", QUALITY_IDEAS)
    validator = _validator(tmp_path, suggest_consolidation=True)
    validator.staged_only = True
    validator.staged_files = ["events/MD_grants.txt"]

    validator.run_validations()

    assert validator._issues == []


def test_staged_run_reports_quality_for_the_staged_idea_file(tmp_path, no_vanilla_gfx):
    _write_run_mod(tmp_path)
    _write(tmp_path, "common/ideas/quality.txt", QUALITY_IDEAS)
    validator = _validator(tmp_path)
    validator.staged_only = True
    validator.staged_files = [str(tmp_path / "common" / "ideas" / "quality.txt")]

    validator.run_validations()

    assert {issue.category for issue in validator._issues} == {"idea-quality"}
    assert validator.warnings_found == 5


def test_extra_cli_arguments_default_to_the_documented_values():
    parser = argparse.ArgumentParser()
    _add_extra_args(parser)

    defaults = parser.parse_args([])
    assert (
        defaults.missing_loc,
        defaults.unused_ideas,
        defaults.suggest_consolidation,
    ) == (
        False,
        True,
        False,
    )
    assert parser.parse_args(["--no-unused-ideas"]).unused_ideas is False
    assert parser.parse_args(["--missing-loc"]).missing_loc is True
    assert parser.parse_args(["--suggest-consolidation"]).suggest_consolidation is True


def test_script_entry_point_exits_nonzero_under_strict(tmp_path, monkeypatch):
    _write(tmp_path, "common/idea_tags/00_idea.txt", IDEA_TAGS)
    _write(tmp_path, "common/synchronized_dynamic_tokens/MD_tokens.txt", "")
    _write(
        tmp_path,
        "events/MD_test.txt",
        "option = {\n\thas_idea = nope_idea\n}\n",
    )
    monkeypatch.setattr("validate_gfx_references._vanilla_gfx_files", lambda: [])
    monkeypatch.setattr(
        sys,
        "argv",
        [
            validate_ideas.__file__,
            "--path",
            str(tmp_path),
            "--strict",
            "--workers",
            "1",
            "--no-color",
            "--no-unused-ideas",
        ],
    )

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(validate_ideas.__file__, run_name="__main__")

    assert exit_info.value.code == 1
