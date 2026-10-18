"""Behavioural tests for check_common_mistakes' entry points and file-level checks.

check_common_mistakes_test.py drills the individual `_check_*` scanners with
hand-built line lists. This file covers what sits around them: check_file's
inline rules and per-directory dispatch, the reference scan, main()'s exit
codes, and the readers for definitions under common/.
"""

import runpy
import sys

import check_common_mistakes as checker
import pytest
from shared.suite import write_text as _write
from shared.suite import write_under_str


def _script(*lines):
    return "".join(line + "\n" for line in lines)


def _messages(tmp_path, rel, *lines):
    path = tmp_path / rel
    _write(path, _script(*lines))
    return [message for _fp, _line, message in checker.check_file(str(path))]


def _matching(messages, needle):
    return [message for message in messages if needle in message]


@pytest.fixture
def scoped_refs(monkeypatch):
    """Give one test its own view of the codebase-wide reference sets."""

    def _apply(focuses=(), decisions=(), nation_flags=()):
        monkeypatch.setattr(checker, "_SCRIPT_COMPLETED_FOCUSES", set(focuses))
        monkeypatch.setattr(checker, "_SCRIPT_COMPLETED_DECISIONS", set(decisions))
        monkeypatch.setattr(checker, "_REAL_NATION_FLAGS", set(nation_flags))

    _apply()
    return _apply


@pytest.fixture
def fake_mod_root(monkeypatch, tmp_path):
    """Point the cached common/ readers at an empty tree, then reset them."""
    cached = (
        checker._equipment_bonus_enum,
        checker._equipment_names,
        checker._decision_ids,
        checker._opinion_modifier_names,
        checker._static_modifier_names,
    )
    root = tmp_path / "modroot"
    root.mkdir()
    for function in cached:
        function.cache_clear()
    monkeypatch.setattr(checker, "_mod_root", lambda: str(root))
    yield root
    for function in cached:
        function.cache_clear()


# ---------------------------------------------------------------------------
# check_file — inline rules and per-directory dispatch
# ---------------------------------------------------------------------------

_TRIGGERS = "common/scripted_triggers/tst.txt"
_FOCUS = "common/national_focus/TAG.txt"
_IDEAS = "common/ideas/tst.txt"
_IDEA_DEFAULT = "allowed = { always = no } is the default for ideas in 'country' -- remove it (checked once at load; add_ideas bypasses it)"
_DIVISION = "use multiplication instead of division (/ 100 -> * 0.01)"


@pytest.mark.parametrize(
    "rel_path, text, expected",
    [
        pytest.param(
            _TRIGGERS,
            "t = { has_war_support > 50 has_stability < 20 }\n",
            [
                (
                    1,
                    "has_war_support > 50 looks like a percentage -- has_war_support is 0.0-1.0 (use 0.5?)",
                ),
                (
                    1,
                    "has_stability < 20 looks like a percentage -- has_stability is 0.0-1.0 (use 0.2?)",
                ),
            ],
            id="war support and stability",
        ),
        pytest.param(
            _FOCUS,
            _script(
                "focus = {",
                "\tid = TAG_focus",
                "\tavailable = {",
                "\t\tthreat > 40",
                "\t\thas_war_support > 50",
                "\t\thas_stability > 60",
                "\t}",
                "}",
            ),
            [
                (
                    4,
                    "threat > 40.0 looks like a percentage -- threat is 0.0-1.0 (use 0.4?)",
                ),
                (
                    5,
                    "has_war_support > 50 looks like a percentage -- has_war_support is 0.0-1.0 (use 0.5?)",
                ),
                (
                    6,
                    "has_stability > 60 looks like a percentage -- has_stability is 0.0-1.0 (use 0.6?)",
                ),
            ],
            id="percentage ranges in a focus",
        ),
        pytest.param(
            _FOCUS,
            _script(
                "focus = {",
                "\tid = TAG_focus",
                "\tavailable = {",
                "\t\tthreat > 0.4",
                "\t\thas_war_support > 0.5",
                "\t}",
                "}",
            ),
            [],
            id="values below one are not percentages",
        ),
        pytest.param(
            "common/national_focus/tst.txt",
            "focus = {\n\tid = TST_f\n\tai_will_do = { factor = 2 }\n}\n",
            [
                (
                    3,
                    "ai_will_do root-level 'factor =' should be 'base =' -- factor is only valid inside modifier = { } children",
                )
            ],
            id="ai_will_do factor",
        ),
        pytest.param(
            "common/scripted_effects/MD_test.txt",
            _script(
                "test_effect = {",
                "\tif = {",
                "\t\tlimit = { is_in_faction = SOV }",
                "\t\tset_variable = { share = money_total/100 }",
                "\t}",
                "\tif = {",
                "\t\tlimit = { has_trade_agreement_with = USA }",
                "\t\tadd_political_power = 10",
                "\t}",
                "}",
            ),
            [
                (
                    3,
                    "is_in_faction = SOV is invalid -- is_in_faction takes yes/no; use is_in_faction_with = SOV",
                ),
                (4, _DIVISION),
                (
                    7,
                    "has_trade_agreement_with is not a valid trigger -- use has_country_flag = trade_agreement@TAG",
                ),
            ],
            id="faction rules and an unspaced division",
        ),
        pytest.param(
            _TRIGGERS,
            "effect = {\n"
            "\tset_variable = { x = whatever / 100 }\n"
            '\tlog = "progress 50/100 complete"\n'
            "}\n",
            [(2, _DIVISION)],
            id="division beside a quoted slash",
        ),
        pytest.param(
            _TRIGGERS,
            "t = { has_war = yes } # threat > 50 / 100\n",
            [],
            id="literals only in a comment",
        ),
        pytest.param(
            _TRIGGERS,
            "trigger = { is_at_war = yes }\n",
            [(1, "is_at_war is not a HOI4 trigger -- use has_war = yes/no")],
            id="is_at_war",
        ),
        pytest.param(
            "common/scripted_triggers/MD_test.txt",
            _script(
                "test_trigger = {",
                "\tOR = {",
                "\t\thas_war = yes",
                "\t}",
                "\tAND = {",
                "\t\thas_civil_war = yes",
                "\t\thas_war = no",
                "\t}",
                "}",
            ),
            [
                (
                    2,
                    "redundant OR = { } wrapper around single condition -- run tools/cleanup_or.py to fix",
                ),
                (
                    5,
                    "redundant AND = { } wrapper (AND is the default scope) -- run tools/cleanup_or.py to fix",
                ),
            ],
            id="redundant OR and AND wrappers",
        ),
        pytest.param(
            _IDEAS,
            "ideas = {\n"
            "\tcountry = {\n"
            "\t\tFOO_idea = {\n"
            "\t\t\t# this comment has an extra { brace\n"
            "\t\t\tallowed = { tag = FOO }\n"
            "\t\t}\n"
            "\t}\n"
            "}\n",
            [
                (
                    5,
                    "allowed = { tag = TAG } breaks for civil war split-offs -- use original_tag = TAG instead",
                )
            ],
            id="idea allowed tag after a comment brace",
        ),
        pytest.param(
            _IDEAS,
            "ideas = {\n"
            "\tcountry = {\n"
            "\t\tTST_idea = {\n"
            "\t\t\tallowed = { always = no }\n"
            "\t\t\tallowed_civil_war = { always = no }\n"
            "\t\t\tcancel = { always = no }\n"
            "\t\t\tallowed = {\n"
            "\t\t\t\talways = no\n"
            "\t\t\t}\n"
            "\t\t}\n"
            "\t}\n"
            "}\n",
            [
                (4, _IDEA_DEFAULT),
                (5, "allowed_civil_war = { always = no } has no effect -- remove it"),
                (
                    6,
                    "cancel = { always = no } is checked hourly and never true -- remove it (redundant default)",
                ),
                (7, _IDEA_DEFAULT),
            ],
            id="idea category defaults",
        ),
        pytest.param(
            _IDEAS,
            _script(
                "ideas = {",
                "\tcountry = {",
                "\t\tone_idea = {",
                "\t\t\tallowed = {",
                "\t\t\t\toriginal_tag = USA",
                "\t\t\t\talways = no",
                "\t\t\t}",
                "\t\t}",
                "\t}",
                "}",
            ),
            [],
            id="multi-line allowed with a real condition",
        ),
        pytest.param(
            _IDEAS,
            _script(
                "ideas = {",
                "\tmobilization_laws = {",
                "\t\tone_idea = {",
                "\t\t\tallowed = { always = no }",
                "\t\t}",
                "\t}",
                "}",
            ),
            [],
            id="selectable idea category",
        ),
    ],
)
def test_check_file_line_checks(tmp_path, scoped_refs, rel_path, text, expected):
    findings = checker.check_file(write_under_str(tmp_path, rel_path, text))
    assert [(line, message) for _path, line, message in findings] == expected


def test_focus_file_dispatch_covers_the_focus_only_checks(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/national_focus/TAG.txt",
        "focus = {",
        "\tid = TAG_war",
        "\tavailable = { always = no }",
        "\tai_will_do = { factor = 5 }",
        "\tcompletion_reward = {",
        '\t\tlog = "[GetDateText]: Focus TAG_other"',
        "\t\tcreate_wargoal = { type = annex_everything target = USA }",
        "\t}",
        "}",
    )

    assert _matching(messages, "focus is permanently unreachable")
    assert _matching(messages, "no will_lead_to_war_with")
    assert _matching(messages, "log references Focus TAG_other")
    assert _matching(messages, "ai_will_do root-level 'factor ='")


def test_decision_file_dispatch_covers_the_decision_only_checks(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/decisions/MD_test.txt",
        "test_category = {",
        "\tmy_decision = {",
        "\t\tfire_only_once = yes",
        "\t\tavailable = { always = no }",
        "\t\tallowed = { num_of_factories > 5 }",
        "\t\tcomplete_effect = {",
        '\t\t\tlog = "[GetDateText]: Decision other_decision"',
        "\t\t\tadd_political_power = 10",
        "\t\t}",
        "\t}",
        "}",
    )

    assert _matching(messages, "add visible = { always = no } for script-triggered")
    assert _matching(messages, "dynamic trigger 'num_of_factories'")
    assert _matching(messages, "log references Decision other_decision")


def test_event_file_dispatch_covers_the_event_only_checks(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "events/MD_test_events.txt",
        "country_event = {",
        "\tid = test.1",
        "\toption = {",
        "\t\tname = test.1.a",
        '\t\tlog = "[GetDateText]: Event test.2"',
        "\t\tadd_political_power = 10",
        "\t}",
        "}",
    )

    assert _matching(messages, "log references Event test.2")


def test_political_leaders_file_dispatch(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/scripted_effects/MD_TAG_political_leaders.txt",
        "set_leader_TAG = {",
        "\tif = {",
        "\t\tlimit = { check_variable = { ruling_party = 1 } }",
        "\t\tif = {",
        "\t\t\tlimit = { check_variable = { conservatism_leader = 0 } }",
        "\t\t\tadd_to_variable = { conservatism_leader = 2 }",
        "\t\t}",
        "\t}",
        "}",
    )

    assert _matching(messages, "advances the counter by 2")


def test_provincial_building_checks_only_run_for_common_and_events(
    tmp_path, scoped_refs
):
    body = (
        "test_effect = {",
        "\tadd_building_construction = {",
        "\t\ttype = naval_base",
        "\t\tlevel = 1",
        "\t\tinstant_build = yes",
        "\t}",
        "}",
    )

    inside = _messages(tmp_path, "common/scripted_effects/MD_test.txt", *body)
    outside = _messages(tmp_path, "history/countries/TAG - Test.txt", *body)

    assert _matching(inside, "it is a provincial building")
    assert not _matching(outside, "it is a provincial building")


def test_windows_separators_classify_like_forward_slashes():
    assert checker.classify_file_path(
        "common\\ideas\\united_states.txt"
    ) == checker.classify_file_path("common/ideas/united_states.txt")


def test_check_file_ignores_a_path_it_cannot_read(tmp_path):
    directory = tmp_path / "common" / "unreadable.txt"
    directory.mkdir(parents=True)

    assert checker.check_file(str(directory)) == []


# ---------------------------------------------------------------------------
# _scan_global_refs / _files_need_global_refs
# ---------------------------------------------------------------------------


def test_scan_global_refs_collects_ids_from_the_scanned_directories(tmp_path):
    _write(
        tmp_path / "common" / "refs.txt",
        _script(
            "complete_national_focus = TAG_one",
            "unlock_national_focus = TAG_two",
            "activate_decision = TAG_decision",
            "set_country_flag = arab_nation_flag",
        ),
    )
    _write(
        tmp_path / "events" / "notes.md",
        _script("complete_national_focus = TAG_ignored"),
    )

    focuses, decisions, flags = checker._scan_global_refs(str(tmp_path))

    assert focuses == {"TAG_one", "TAG_two"}
    assert decisions == {"TAG_decision"}
    assert flags == {"arab_nation_flag"}


def test_scan_global_refs_survives_an_unreadable_file(tmp_path):
    common = tmp_path / "common"
    common.mkdir()
    _write(common / "good.txt", _script("complete_national_focus = TAG_one"))
    try:
        (common / "broken.txt").symlink_to(common / "no_such_target.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")

    focuses, _decisions, _flags = checker._scan_global_refs(str(tmp_path))

    assert focuses == {"TAG_one"}


@pytest.mark.parametrize(
    ("rel_path", "text", "expected"),
    [
        pytest.param(
            "common/nation.txt",
            "test_trigger = { is_arab_nation = yes }\n",
            True,
            id="is_X_nation",
        ),
        pytest.param(
            "common/national_focus/TAG.txt",
            "focus = {\n\tavailable={always=no}\n}\n",
            True,
            id="spaceless always-no",
        ),
        pytest.param(
            "common/national_focus/TAG.txt",
            "focus = {\n\tavailable = { has_war = yes }\n}\n",
            False,
            id="focus with a real available",
        ),
    ],
)
def test_files_need_global_refs(tmp_path, rel_path, text, expected):
    path = write_under_str(tmp_path, rel_path, text)
    assert checker._files_need_global_refs([path]) is expected


def test_unreadable_file_needs_global_refs(tmp_path):
    assert checker._files_need_global_refs([str(tmp_path / "gone.txt")])


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def _run_main(monkeypatch, tmp_path, *argv):
    monkeypatch.setattr(checker, "get_root_dir", lambda: str(tmp_path))
    monkeypatch.setattr(checker, "_SCRIPT_COMPLETED_FOCUSES", set())
    monkeypatch.setattr(checker, "_SCRIPT_COMPLETED_DECISIONS", set())
    monkeypatch.setattr(checker, "_REAL_NATION_FLAGS", set())
    monkeypatch.setattr(sys, "argv", [checker.__file__, *argv])
    return checker.main()


def test_main_reports_issues_and_exits_nonzero(tmp_path, monkeypatch, capsys):
    path = tmp_path / "common" / "dirty.txt"
    _write(path, _script("test_trigger = { is_at_war = yes }"))

    assert _run_main(monkeypatch, tmp_path, str(path)) == 1

    out = capsys.readouterr().out
    assert "is_at_war is not a HOI4 trigger" in out
    assert "Found 1 issue(s)" in out


def test_main_reports_an_empty_run(tmp_path, monkeypatch, capsys):
    assert _run_main(monkeypatch, tmp_path) == 0

    assert "No files to check" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_main_scans_the_tree_when_a_targeted_file_needs_the_reference_sets(
    tmp_path, monkeypatch, capsys
):
    focus = tmp_path / "common" / "national_focus" / "TAG.txt"
    _write(
        focus,
        _script(
            "focus = {",
            "\tid = TAG_locked",
            "\tavailable = { always = no }",
            "}",
        ),
    )
    _write(
        tmp_path / "common" / "unlockers.txt",
        _script("test_effect = { complete_national_focus = TAG_locked }"),
    )

    assert _run_main(monkeypatch, tmp_path, str(focus)) == 0

    assert "scan global refs" in capsys.readouterr().err


def test_main_skips_the_tree_scan_for_files_that_cannot_need_it(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "common" / "clean.txt"
    _write(path, _script("test_effect = { add_political_power = 10 }"))

    assert _run_main(monkeypatch, tmp_path, str(path)) == 0

    assert "scan global refs (skipped)" in capsys.readouterr().err


def test_script_entry_point_exits_with_the_finding_count(tmp_path, monkeypatch):
    path = tmp_path / "common" / "dirty.txt"
    _write(path, _script("test_trigger = { is_at_war = yes }"))
    monkeypatch.setattr(sys, "argv", [checker.__file__, str(path)])

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(checker.__file__, run_name="__main__")

    assert excinfo.value.code == 1


def test_targeted_mode_recognises_every_scoping_flag():
    class Args:
        filenames: list[str] | None = None
        files: list[str] | None = None
        mode = "all"

    assert not checker._targeted_mode(Args())
    Args.mode = "staged"
    assert checker._targeted_mode(Args())
    Args.mode = "all"
    Args.files = ["a.txt"]
    assert checker._targeted_mode(Args())


def test_worker_initialiser_publishes_the_reference_sets(scoped_refs):
    checker._init_worker({"TAG_focus"}, {"a_decision"}, {"arab_nation_flag"})

    assert checker._SCRIPT_COMPLETED_FOCUSES == {"TAG_focus"}
    assert checker._SCRIPT_COMPLETED_DECISIONS == {"a_decision"}
    assert checker._REAL_NATION_FLAGS == {"arab_nation_flag"}


# ---------------------------------------------------------------------------
# Definition lookups under common/
# ---------------------------------------------------------------------------


_NAVAL_BASE = [
    "\t\t\tadd_building_construction = {\n",
    "\t\t\t\ttype = naval_base\n",
    "\t\t\t\tlevel = 2\n",
    "\t\t\t}\n",
]


def test_provincial_building_types_read_only_the_txt_files_it_can_open(tmp_path):
    buildings = tmp_path / "common" / "buildings"
    _write(
        buildings / "00_buildings.txt",
        _script(
            "buildings = {",
            "\tnaval_base = {",
            "\t\tlevel_cap = { province_max = 5 }",
            "\t}",
            "\tinfrastructure = {",
            "\t\tlevel_cap = { state_max = 5 }",
            "\t}",
            "}",
        ),
    )
    _write(buildings / "notes.md", "not a buildings file\n")
    (buildings / "a_directory.txt").mkdir()

    assert checker._provincial_building_types(str(tmp_path)) == frozenset(
        {"naval_base"}
    )


def test_commented_province_max_does_not_make_a_building_provincial(tmp_path):
    write_under_str(
        tmp_path,
        "common/buildings/00_buildings.txt",
        _script(
            "buildings = {",
            "\tindustrial_complex = {",
            "\t\tbase_cost = 100",
            "\t\t# province_max = 5 would make this provincial",
            "\t\tlevel_cap = { state_max = 25 }",
            "\t}",
            "\tnaval_base = {",
            "\t\tlevel_cap = { province_max = 10 }",
            "\t}",
            "}",
        ),
    )
    lines = [line.replace("naval_base", "industrial_complex") for line in _NAVAL_BASE]

    assert checker._provincial_building_types(str(tmp_path)) == frozenset(
        {"naval_base"}
    )
    assert checker._check_building_missing_province(lines, str(tmp_path)) == []


def test_missing_buildings_file_falls_back_to_the_known_list(tmp_path):
    missing = str(tmp_path / "does-not-exist")

    assert "naval_base" in checker._provincial_building_types(missing)
    assert len(checker._check_building_missing_province(_NAVAL_BASE, missing)) == 1


def test_missing_common_directories_disable_the_definition_checks(fake_mod_root):
    bonus = [
        "\tadd_equipment_bonus = {\n",
        "\t\tbonus = { not_a_real_bonus_type = 0.1 }\n",
        "\t}\n",
    ]

    issues = checker._check_equipment_bonus(bonus)

    assert len(issues) == 1
    assert "has no name = <loc key>" in issues[0][1]
    assert (
        checker._check_equipment_type_defined(
            ["\tadd_equipment_to_stockpile = { type = made_up_gun amount = 1 }\n"]
        )
        == []
    )
    assert (
        checker._check_active_decision_defined(
            ["\thas_active_decision = made_up_decision\n"]
        )
        == []
    )
    assert (
        checker._check_modifier_ref_defined(
            [
                "\tadd_opinion_modifier = { target = USA modifier = made_up }\n",
                "\tadd_relation_modifier = { target = USA modifier = made_up }\n",
            ]
        )
        == []
    )


def test_definition_lookups_skip_entries_they_cannot_use(fake_mod_root):
    _write(
        fake_mod_root / "common" / "script_enums.txt",
        _script("script_enum_some_other_thing = {", "\tvalue", "}"),
    )
    equipment = fake_mod_root / "common" / "units" / "equipment"
    _write(
        equipment / "infantry.txt",
        _script(
            "equipments = {",
            "\treal_gun = {",
            "\t\tyear = 2000",
            "\t}",
            "\tduplicate_archetypes = {",
            "\t\tclone_without_a_base = {",
            "\t\t\tyear = 2000",
            "\t\t}",
            "\t}",
            "}",
        ),
    )
    (equipment / "a_directory.txt").mkdir()

    assert checker._equipment_bonus_enum() is None
    assert checker._equipment_names() == frozenset({"real_gun", "duplicate_archetypes"})
