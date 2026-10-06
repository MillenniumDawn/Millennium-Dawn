"""Staged runs build a repo-wide index only when a staged file reaches its check.

Each early exit is pinned twice: once with the expensive work made to raise,
proving a staged set that cannot use it never pays for it, and once with a
staged file that does need it, proving the check still fires with the same
file, line and message.
"""

import os

import pytest
import validate_events as E
import validate_scripted_localisation as SL
import validate_variables as V
from shared.suite import issue_rows as _rows


def _staged(validator, *paths):
    validator.staged_only = True
    validator.staged_files = [str(path) for path in paths]
    return validator


def _forbid(monkeypatch, target, *names):
    def boom(*_args, **_kwargs):
        raise AssertionError("staged run built an index it cannot use")

    for name in names:
        monkeypatch.setattr(target, name, boom)


@pytest.fixture(autouse=True)
def _no_shared_staged_list(monkeypatch):
    # The pre-commit dispatcher exports this; a test must not inherit it.
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)


# --- scripted localisation -------------------------------------------------

_SLOC_DEFS = (
    "defined_text = {\n\tname = UsedLoc\n}\ndefined_text = {\n\tname = OrphanLoc\n}\n"
)


def _forbid_repo_usage_scan(monkeypatch):
    usage_scan = SL.ScriptedLocalisation.get_all_used_localisations

    def staged_usage_only(*args, staged_files=None, **kwargs):
        if staged_files is None:
            raise AssertionError("repo-wide usage scan ran")
        return usage_scan(*args, staged_files=staged_files, **kwargs)

    monkeypatch.setattr(
        SL.ScriptedLocalisation, "get_all_used_localisations", staged_usage_only
    )


def test_scripted_loc_without_a_staged_definition_skips_the_usage_scan(
    tmp_path, write_path, monkeypatch
):
    write_path(tmp_path, "common/scripted_localisation/defs.txt", _SLOC_DEFS)
    yml = write_path(
        tmp_path,
        "localisation/english/use_l_english.yml",
        'l_english:\n key: "[UsedLoc] [GhostLoc]"\n',
    )
    _forbid_repo_usage_scan(monkeypatch)
    validator = _staged(SL.Validator(str(tmp_path), use_colors=False, workers=4), yml)
    _forbid(monkeypatch, validator, "_get_pool")

    validator.run_validations()

    assert _rows(validator) == [
        (
            "missing-scripted-loc",
            "ghostloc",
            "localisation/english/use_l_english.yml",
            2,
        )
    ]


def test_staged_scripted_loc_definition_still_reads_unstaged_consumers(
    tmp_path, write_path
):
    defs = write_path(tmp_path, "common/scripted_localisation/defs.txt", _SLOC_DEFS)
    write_path(tmp_path, "interface/use.gui", 'text = "[UsedLoc]"\n')
    validator = _staged(SL.Validator(str(tmp_path), use_colors=False, workers=1), defs)

    validator.run_validations()

    assert _rows(validator) == [
        (
            "unused-scripted-loc",
            "orphanloc",
            "common/scripted_localisation/defs.txt",
            5,
        )
    ]


_GETTER_YML = "localisation/english/use_l_english.yml"


def _getter_repo(tmp_path, write_path, documented, call):
    """Docs listing *documented* getters and one loc line making *call*."""
    write_path(tmp_path, SL._LOC_OBJECTS_DOC, documented)
    return write_path(tmp_path, _GETTER_YML, f'l_english:\n key: "{call}"\n')


def _getter_row(member, spelling):
    message = f"'{member}' is not the documented getter spelling '{spelling}'"
    return ("loc-getter-spelling", message, _GETTER_YML, 2)


def test_staged_definition_feeds_the_getter_and_unused_checks(tmp_path, write_path):
    """The getter check accepts a Get-named loc from an unstaged definition file."""
    yml = _getter_repo(
        tmp_path, write_path, "**GetName**\n", "[ROOT.GetOwnLoc] [ROOT.Getname]"
    )
    write_path(
        tmp_path,
        "common/scripted_localisation/other.txt",
        "defined_text = {\n\tname = GetOwnLoc\n}\n",
    )
    defs = write_path(
        tmp_path,
        "common/scripted_localisation/defs.txt",
        "defined_text = {\n\tname = OrphanLoc\n}\n",
    )
    validator = _staged(
        SL.Validator(str(tmp_path), use_colors=False, workers=1), defs, yml
    )

    validator.run_validations()

    assert _rows(validator) == [
        _getter_row("Getname", "GetName"),
        (
            "unused-scripted-loc",
            "orphanloc",
            "common/scripted_localisation/defs.txt",
            2,
        ),
    ]


def test_staged_documentation_drives_the_getter_check_without_the_usage_scan(
    tmp_path, write_path, monkeypatch
):
    _getter_repo(
        tmp_path,
        write_path,
        "**GetName**\n**GetNewGetter**\n",
        "[ROOT.GetNewGetter] [ROOT.Getnewgetter]",
    )
    write_path(tmp_path, "localisation/english/other_l_english.yml", "[ROOT.Getname]\n")
    _forbid_repo_usage_scan(monkeypatch)

    def staged_run(*paths):
        # Through the real staged filter, which drops the .md from the list.
        monkeypatch.setenv("MD_STAGED_FILES", "\n".join(paths))
        validator = SL.Validator(
            str(tmp_path), use_colors=False, staged_only=True, workers=4
        )
        _forbid(monkeypatch, validator, "_get_pool")
        validator.run_validations()
        return _rows(validator)

    assert staged_run(SL._LOC_OBJECTS_DOC, _GETTER_YML) == [
        _getter_row("Getnewgetter", "GetNewGetter")
    ]
    assert staged_run(SL._LOC_OBJECTS_DOC) == []


def test_unrelated_staged_file_reads_no_loc_for_the_getter_check(
    tmp_path, write_path, monkeypatch
):
    _getter_repo(tmp_path, write_path, "**GetName**\n", "[ROOT.Getname] [GhostLoc]")
    write_path(tmp_path, "common/scripted_localisation/defs.txt", _SLOC_DEFS)
    txt = write_path(tmp_path, "common/ideas/unrelated.txt", "ideas = {\n}\n")
    _forbid_repo_usage_scan(monkeypatch)
    _forbid(monkeypatch, SL, "process_file_for_getter_refs")
    validator = _staged(SL.Validator(str(tmp_path), use_colors=False, workers=4), txt)
    _forbid(monkeypatch, validator, "_get_pool")

    validator.run_validations()

    assert _rows(validator) == []


# --- variables -------------------------------------------------------------


def _variables_repo(tmp_path, write_path):
    """Unstaged definitions every staged-mode variables harvest reads."""
    write_path(
        tmp_path,
        "common/synchronized_dynamic_tokens/MD_tokens.txt",
        "TST_registered\n",
    )
    write_path(
        tmp_path,
        "common/scripted_effects/meter.txt",
        "TST_meter_effect = {\n"
        "\tclamp_variable = { var = TST_meter min = 0 max = 100 }\n"
        "}\n"
        "TST_pay = {\n\tmodify_treasury_effect = yes\n}\n",
    )
    write_path(
        tmp_path,
        "common/scripted_triggers/gate.txt",
        "TST_gate = {\n\thas_global_flag = TST_gate_open\n}\n",
    )
    write_path(
        tmp_path,
        "common/dynamic_modifiers/dyn.txt",
        "TST_modifier = {\n\tpolitical_power_factor = TST_pp\n}\n",
    )
    write_path(
        tmp_path,
        "localisation/english/flags_l_english.yml",
        "l_english:\n"
        ' TST_known_flag:0 "Known"\n'
        ' TST_shown_NOT:0 "Not shown"\n'
        ' TST_shown_tt:0 "Shown"\n'
        ' political_power_factor_tt:0 "Modifier"\n',
    )


def test_variables_staged_localisation_builds_no_script_index(
    tmp_path, write_path, monkeypatch
):
    _variables_repo(tmp_path, write_path)
    yml = write_path(
        tmp_path,
        "localisation/english/tokens_l_english.yml",
        'l_english:\n a:0 "[token:TST_registered]"\n b:0 "[token:TST_stray]"\n',
    )
    validator = _staged(V.Validator(str(tmp_path), use_colors=False, workers=1), yml)
    _forbid(monkeypatch, V, "collect_clamp_ranges")
    _forbid(
        monkeypatch,
        validator,
        "_get_ai_only_categories",
        "_collect_scripted_trigger_flag_names",
        "_collect_scripted_trigger_requirements",
        "_collect_dynamic_modifier_vars",
        "_load_localisation_keys",
    )

    validator.run_validations()

    assert _rows(validator) == [
        (
            "unregistered-dynamic-token",
            "token:TST_stray uses a token that is not registered in"
            " common/synchronized_dynamic_tokens/MD_tokens.txt (the engine logs"
            " a dynamic-token OOS warning at load)",
            "localisation/english/tokens_l_english.yml",
            3,
        )
    ]


def test_variables_staged_decision_still_reads_every_repo_index(tmp_path, write_path):
    _variables_repo(tmp_path, write_path)
    decision = write_path(
        tmp_path,
        "common/decisions/dec.txt",
        "TST_category = {\n"
        "\tTST_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { TST_meter > 150 }\n"
        "\t\t\thas_country_flag = TST_known_flag\n"
        "\t\t\thas_country_flag = TST_unknown_flag\n"
        "\t\t\tTST_gate = yes\n"
        "\t\t\tNOT = { custom_trigger_tooltip = { tooltip = TST_shown always = yes } }\n"
        "\t\t\tNOT = { custom_trigger_tooltip = { tooltip = TST_hidden always = yes } }\n"
        "\t\t}\n"
        "\t\tcomplete_effect = {\n"
        "\t\t\tset_temp_variable = { treasury_change = 5 }\n"
        "\t\t\tTST_pay = yes\n"
        "\t\t\tadd_to_variable = { TST_pp = 1 }\n"
        "\t\t\tadd_to_variable = { var = TST_score value = 1 tooltip = TST_shown_tt }\n"
        "\t\t\tadd_to_variable = { var = TST_score value = 2 tooltip = TST_absent_tt }\n"
        "\t\t}\n"
        "\t\tremove_effect = {\n"
        "\t\t\tset_temp_variable = { treasury_change = 1 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = _staged(
        V.Validator(str(tmp_path), use_colors=False, workers=1), decision
    )

    validator.run_validations()

    rel = "common/decisions/dec.txt"
    assert _rows(validator) == [
        (
            "clamp-range-conflict",
            "TST_meter is clamped to 0.0..100.0 but compared against 150"
            " — the check can never change outcome",
            rel,
            4,
        ),
        (
            "dynamic-modifier-tooltip-missing",
            "add_to_variable = { TST_pp ... } moves dynamic modifier"
            " `political_power_factor` with no tooltip - the change is invisible"
            " to the player; add tooltip = political_power_factor_tt",
            rel,
            14,
        ),
        (
            "unlocalised-available-flag",
            "has_country_flag = TST_unknown_flag in `available` has no"
            " localisation key - the player sees the raw flag name; add a loc"
            " key named after the flag",
            rel,
            6,
        ),
        (
            "unlocalised-available-flag",
            "has_global_flag = TST_gate_open in `available` via scripted trigger"
            " TST_gate has no localisation key - the player sees the raw flag"
            " name; add a loc key named after the flag",
            rel,
            7,
        ),
        (
            "unlocalised-negated-trigger-tooltip",
            "Custom trigger tooltip renders negated in `available`, so the player"
            " sees the raw token TST_hidden_NOT; add that localisation key",
            rel,
            9,
        ),
        (
            "untooltipped-available-check",
            "check_variable in `available` renders no tooltip line - the player"
            " sees a blank requirement; wrap it in custom_trigger_tooltip ="
            " { tooltip = KEY ... }",
            rel,
            4,
        ),
        (
            "untooltipped-available-scripted-trigger",
            "TST_gate = yes in `available` resolves to a scripted trigger that"
            " checks a flag directly - the player sees no requirement line at"
            " all; wrap it in custom_trigger_tooltip = { tooltip = KEY ... }",
            rel,
            7,
        ),
        (
            "variable-tooltip-missing-loc",
            "tooltip = TST_absent_tt has no English localisation entry - the"
            " tooltip renders the raw key; add it to MD_dm_modifiers_l_english.yml",
            rel,
            16,
        ),
    ]


# --- events ----------------------------------------------------------------

_EVENTS = (
    "add_namespace = tst\n"
    "country_event = {\n\tid = tst.1\n\tis_triggered_only = yes\n"
    "\tfire_only_once = yes\n\toption = { name = tst.1.a }\n}\n"
    "news_event = {\n\tid = tst.2\n\tis_triggered_only = yes\n"
    "\tmajor = yes\n\toption = { name = tst.2.a }\n}\n"
)

_CALLER = (
    "TST_category = {\n"
    "\tTST_decision = {\n"
    "\t\tcomplete_effect = {\n"
    "\t\t\tevery_country = {\n"
    "\t\t\t\tcountry_event = tst.1\n"
    "\t\t\t\tnews_event = tst.2\n"
    "\t\t\t}\n"
    "\t\t\tcountry_event = { id = tst.1 }\n"
    "\t\t\tcountry_event = tst.2\n"
    "\t\t\tcountry_event = ghost.9\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)


def _events_validator(tmp_path, write_path, staged_rel):
    paths = {
        "events/tst.txt": write_path(tmp_path, "events/tst.txt", _EVENTS),
        "common/decisions/dec.txt": write_path(
            tmp_path, "common/decisions/dec.txt", _CALLER
        ),
    }
    validator = E.Validator(str(tmp_path), use_colors=False, workers=1)
    return _staged(validator, *(paths[rel] for rel in staged_rel))


def test_events_run_with_no_script_staged_builds_no_call_site_index(
    tmp_path, write_path, monkeypatch
):
    validator = _events_validator(tmp_path, write_path, ())
    _forbid(
        monkeypatch,
        validator,
        "_get_fire_scan_args",
        "_get_fire_only_once_ids",
        "_get_major_event_ids",
    )

    validator.run_validations()

    assert _rows(validator) == []


_CALLER_FINDINGS = [
    (
        "Long-form event calls with only id (use shorthand instead)",
        "country_event = { id = tst.1 } → use shorthand `country_event = tst.1`",
        "common/decisions/dec.txt",
        8,
    ),
    (
        "fire-only-once-in-loop",
        "fire_only_once event tst.1 fired inside an every_*/for_each_* iterator"
        " (only the first recipient gets it; drop fire_only_once or fire it"
        " outside the loop)",
        "common/decisions/dec.txt",
        5,
    ),
    (
        "major-event-in-loop",
        "major event tst.2 fired inside an every_*/for_each_* iterator (each"
        " iteration broadcasts to every country; fire it once outside the loop)",
        "common/decisions/dec.txt",
        6,
    ),
]

_TYPE_AND_UNDEFINED = [
    (
        "event-fire-type-mismatch",
        "tst.2 - fired with country_event, defined as news_event",
        "common/decisions/dec.txt",
        9,
    ),
    (
        "undefined-event-fire",
        f"ghost.9 - fired from {os.path.normpath('common/decisions/dec.txt')}:10, "
        "no event defines it",
        "",
        0,
    ),
]


def test_events_staged_caller_still_reads_unstaged_event_flags(tmp_path, write_path):
    validator = _events_validator(tmp_path, write_path, ["common/decisions/dec.txt"])

    validator.run_validations()

    assert _rows(validator) == sorted(_CALLER_FINDINGS + _TYPE_AND_UNDEFINED)


def test_events_staged_event_file_still_scans_unstaged_callers(tmp_path, write_path):
    validator = _events_validator(tmp_path, write_path, ["events/tst.txt"])

    validator.run_validations()

    assert _rows(validator) == sorted(
        _TYPE_AND_UNDEFINED
        + [
            (
                "missing-event-localisation",
                f"{eid} - tst.txt: missing loc key '{eid}.a'",
                "",
                0,
            )
            for eid in ("tst.1", "tst.2")
        ]
        + [
            (
                "news-event-picture-omitted",
                "tst.2: event has no picture, add `picture = GFX_<sprite>` below"
                " `desc =`",
                "tst.txt",
                8,
            )
        ]
    )
