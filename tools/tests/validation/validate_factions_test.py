"""Behavior tests for the faction cross-reference validator."""

import runpy
import sys

import pytest
import validate_factions
from shared.suite import write_text as _write_text
from validate_factions import (
    Validator,
    extract_default_rules_block,
    extract_goal_categories,
    extract_goals_block,
    extract_group_rule_ids,
    extract_upgrade_group_ids,
    find_faction_scope_cache_reads,
)


def test_extract_template_goal_and_rule_references():
    content = """
template_alpha = {
\tgoals = {
\t\tgoal_one
\t\tgoal_two
\t}
\tdefault_rules = {
\t\trule_one
\t}
}
"""

    assert extract_goals_block(content, "template_alpha") == ["goal_one", "goal_two"]
    assert extract_default_rules_block(content, "template_alpha") == ["rule_one"]


def test_extract_rule_and_upgrade_groups():
    content = """
rule_group = {
\trules = {
\t\trule_one
\t\trule_two
\t}
}
upgrade_group = {
\tupgrades = {
\t\tupgrade_one
\t}
}
"""

    assert extract_group_rule_ids(content) == {"rule_group": ["rule_one", "rule_two"]}
    assert extract_upgrade_group_ids(content) == {"upgrade_group": ["upgrade_one"]}


def _write_faction_fixture(tmp_path, manifest="manifest_one"):
    faction_root = tmp_path / "common" / "factions"
    for directory in ("templates", "goals", "rules", "upgrades", "member_upgrades"):
        (faction_root / directory).mkdir(parents=True, exist_ok=True)
    (faction_root / "icons").mkdir(parents=True, exist_ok=True)
    (tmp_path / "interface").mkdir()

    _write_text(
        faction_root / "templates" / "templates.txt",
        "template_alpha = {\n"
        f"\tmanifest = {manifest}\n"
        "\tgoals = { goal_one }\n"
        "\tdefault_rules = { rule_one }\n"
        "\ticon = GFX_faction_alpha\n"
        "}\n",
    )
    _write_text(
        faction_root / "goals" / "goals.txt",
        "goal_one = { is_manifest = yes }\n",
    )
    _write_text(
        faction_root / "rules" / "rules.txt",
        "rule_one = { type = joining_rules }\n",
    )
    _write_text(faction_root / "icons" / "pool.txt", "GFX_faction_alpha\n")
    _write_text(
        tmp_path / "interface" / "factions.gfx",
        'spriteType = { name = "GFX_faction_alpha" }\n',
    )


def test_extract_goal_categories_uses_top_level_assignment():
    content = """
goal_one = {
\tcategory = short_term
\tvisible = {
\t\tcategory = long_term
\t}
}
goal_two = {
\tcategory = medium_term
}
goal_three = {
\tvisible = {
\t\tcategory = long_term
\t}
}
manifest_one = {
\tis_manifest = yes
}
"""

    assert extract_goal_categories(content) == {
        "goal_one": "short_term",
        "goal_two": "medium_term",
    }


def test_collect_definitions_includes_manifest_and_interface_icons(tmp_path):
    _write_faction_fixture(tmp_path)
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator._collect_definitions()

    assert validator.template_ids == {"template_alpha": "templates.txt"}
    assert validator.goal_ids == {"goal_one"}
    assert validator.manifest_ids == {"goal_one"}
    assert validator.rule_ids == {"rule_one"}
    assert "GFX_faction_alpha" in validator.icon_ids
    assert validator.interface_icon_count == 1


def test_template_goal_category_limit_is_reported(tmp_path):
    _write_faction_fixture(tmp_path)
    faction_root = tmp_path / "common" / "factions"
    goal_ids = [
        f"{category}_{index}"
        for category in ("short_term", "medium_term", "long_term")
        for index in range(3)
    ]
    _write_text(
        faction_root / "templates" / "templates.txt",
        "template_alpha = {\n\tgoals = { " + " ".join(goal_ids) + " }\n}\n",
    )
    _write_text(
        faction_root / "goals" / "goals.txt",
        "".join(
            f"{goal_id} = {{ category = {goal_id.rsplit('_', 1)[0]} }}\n"
            for goal_id in goal_ids
        ),
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator._collect_definitions()

    validator._validate_template_goal_limits()

    assert len(validator._issues) == 3
    assert all("maximum 2" in issue.message for issue in validator._issues)
    assert {issue.message.split()[3] for issue in validator._issues} == {
        "short_term",
        "medium_term",
        "long_term",
    }


def test_template_with_two_goals_per_category_passes_limit(tmp_path):
    _write_faction_fixture(tmp_path)
    faction_root = tmp_path / "common" / "factions"
    _write_text(
        faction_root / "templates" / "templates.txt",
        "template_alpha = {\n\tgoals = { short_one short_two }\n}\n",
    )
    _write_text(
        faction_root / "goals" / "goals.txt",
        "short_one = { category = short_term }\n"
        "short_two = { category = short_term }\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator._collect_definitions()

    validator._validate_template_goal_limits()

    assert not validator._issues


def test_missing_template_manifest_is_reported(tmp_path):
    _write_faction_fixture(tmp_path, manifest="missing_manifest")
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator._collect_definitions()

    validator._validate_template_manifests()

    assert len(validator._issues) == 1
    assert "missing_manifest" in validator._issues[0].message


def test_extract_blocks_return_empty_for_absent_template_and_absent_block():
    content = "template_alpha = {\n\ticon = GFX_faction_alpha\n}\n"

    assert extract_goals_block(content, "template_beta") == []
    assert extract_default_rules_block(content, "template_beta") == []
    assert extract_goals_block(content, "template_alpha") == []
    assert extract_default_rules_block(content, "template_alpha") == []


def _faction_dirs(tmp_path):
    root = tmp_path / "common" / "factions"
    for directory in (
        "templates",
        "goals",
        "rules/groups",
        "upgrades/groups",
        "member_upgrades/member_groups",
        "icons",
    ):
        (root / directory).mkdir(parents=True, exist_ok=True)
    (tmp_path / "interface").mkdir(exist_ok=True)
    return root


def _write_broken_tree(tmp_path):
    root = _faction_dirs(tmp_path)
    _write_text(
        root / "templates" / "a.txt",
        "template_alpha = {\n"
        "\tmanifest = goal_manifest\n"
        "\tgoals = { goal_one missing_goal }\n"
        "\tdefault_rules = { rule_one missing_rule }\n"
        "\ticon = GFX_faction_alpha\n"
        "}\n",
    )
    _write_text(
        root / "templates" / "b.txt",
        "template_alpha = {\n\tmanifest = missing_manifest\n}\n",
    )
    _write_text(
        root / "goals" / "a.txt",
        "goal_manifest = { is_manifest = yes }\ngoal_one = { category = short_term }\n",
    )
    _write_text(
        root / "goals" / "b.txt",
        "goal_one = { category = long_term }\n"
        "orphan_manifest = { is_manifest = yes }\n",
    )
    _write_text(root / "rules" / "a.txt", "rule_one = { type = joining_rules }\n")
    _write_text(root / "rules" / "b.txt", "rule_one = { type = bogus_rules }\n")
    _write_text(
        root / "rules" / "groups" / "rule_groups.txt",
        "joining = {\n\trules = {\n\t\trule_one\n\t\tmissing_group_rule\n\t}\n}\n",
    )
    _write_text(root / "upgrades" / "a.txt", "upgrade_one = {\n\tcost = 1\n}\n")
    _write_text(
        root / "upgrades" / "groups" / "g.txt",
        "upgrade_group = {\n\tupgrades = {\n\t\tupgrade_one\n\t\tmissing_upgrade\n\t}\n}\n",
    )
    _write_text(
        root / "member_upgrades" / "m.txt", "member_upgrade_one = {\n\tcost = 1\n}\n"
    )
    _write_text(
        root / "member_upgrades" / "member_groups" / "g2.txt",
        "member_group = {\n"
        "\tupgrades = {\n\t\tmember_upgrade_one\n\t\tmissing_member_upgrade\n\t}\n}\n",
    )
    _write_text(root / "icons" / "pool.txt", "GFX_faction_alpha\n")
    _write_text(
        tmp_path / "interface" / "factions.gfx",
        'spriteType = { name = "GFX_faction_alpha" }\n',
    )
    return root


def test_full_run_reports_every_broken_reference(tmp_path):
    _write_broken_tree(tmp_path)
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert sorted(issue.message for issue in validator._issues) == [
        "Duplicate goal 'goal_one' in b.txt (first in a.txt)",
        "Duplicate rule 'rule_one' in b.txt (first in a.txt)",
        "Duplicate template 'template_alpha' in b.txt (first in a.txt)",
        "a.txt (template_alpha): goal 'missing_goal' not found",
        "a.txt (template_alpha): rule 'missing_rule' not found",
        "b.txt: manifest 'missing_manifest' not found in any goal file",
        "b.txt: unknown rule type 'bogus_rules'",
        "g.txt (upgrade_group): upgrade 'missing_upgrade' not found",
        "g2.txt (member_group): upgrade 'missing_member_upgrade' not found",
        "rule_groups.txt (joining): rule 'missing_group_rule' not found",
    ]
    assert validator.errors_found == 10
    assert "  orphan_manifest" in validator.output_lines


def test_full_run_on_a_consistent_tree_is_silent(tmp_path):
    root = _faction_dirs(tmp_path)
    _write_text(
        root / "templates" / "a.txt",
        "template_alpha = {\n"
        "\tmanifest = goal_manifest\n"
        "\tgoals = { goal_one }\n"
        "\tdefault_rules = { rule_one }\n"
        "\ticon = GFX_faction_alpha\n"
        "}\n",
    )
    _write_text(
        root / "goals" / "a.txt",
        "goal_manifest = { is_manifest = yes }\ngoal_one = { category = short_term }\n",
    )
    _write_text(root / "rules" / "a.txt", "rule_one = { type = joining_rules }\n")
    _write_text(
        root / "rules" / "groups" / "rule_groups.txt",
        "joining = {\n\trules = { rule_one }\n}\n",
    )
    _write_text(root / "upgrades" / "a.txt", "upgrade_one = {\n\tcost = 1\n}\n")
    _write_text(
        root / "upgrades" / "groups" / "g.txt",
        "upgrade_group = {\n\tupgrades = { upgrade_one }\n}\n",
    )
    _write_text(root / "icons" / "pool.txt", "GFX_faction_alpha\n")
    _write_text(
        tmp_path / "interface" / "factions.gfx",
        'spriteType = { name = "GFX_faction_alpha" }\n'
        'spriteType = { name = "GFX_faction_spare" }\n',
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()

    assert validator._issues == []
    assert validator.errors_found == 0
    assert not [line for line in validator.output_lines if line.startswith("Warning:")]


def test_missing_icon_source_replaces_per_template_icon_errors(tmp_path):
    root = _faction_dirs(tmp_path)
    _write_text(
        root / "templates" / "a.txt",
        "template_alpha = {\n\ticon = GFX_faction_alpha\n}\n",
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator._collect_definitions()

    validator._validate_template_icons()

    assert [issue.message for issue in validator._issues] == [
        "faction icon source did not load "
        "(interface/factions/factions.gfx missing or unreadable); "
        "skipping per-template icon checks"
    ]


def test_unreadable_interface_file_is_named_in_the_icon_report(tmp_path):
    root = _faction_dirs(tmp_path)
    _write_text(
        root / "templates" / "a.txt",
        "template_alpha = {\n\ticon = GFX_faction_alpha\n}\n",
    )
    _write_text(root / "icons" / "pool.txt", "GFX_faction_alpha\n")
    # A directory named *.gfx makes the read raise instead of returning text.
    unreadable = tmp_path / "interface" / "factions.gfx"
    unreadable.mkdir()
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator._collect_definitions()

    validator._validate_template_icons()

    assert validator.interface_read_failures == [str(unreadable)]
    assert [issue.message for issue in validator._issues] == [
        f"faction icon source did not load ({unreadable}); "
        "skipping per-template icon checks"
    ]


def test_undefined_icon_is_reported_when_the_source_loaded(tmp_path):
    root = _faction_dirs(tmp_path)
    _write_text(
        root / "templates" / "a.txt",
        "template_alpha = {\n\ticon = GFX_faction_missing\n}\n",
    )
    _write_text(
        tmp_path / "interface" / "factions.gfx",
        'spriteType = { name = "GFX_faction_alpha" }\n'
        'spriteType = { name = "GFX_faction_beta" }\n',
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator._collect_definitions()

    validator._validate_template_icons()

    assert [issue.message for issue in validator._issues] == [
        "a.txt: icon 'GFX_faction_missing' not found in pool or interface"
    ]


def test_rule_group_check_is_skipped_without_a_rule_groups_file(tmp_path):
    root = _faction_dirs(tmp_path)
    _write_text(root / "rules" / "a.txt", "rule_one = { type = joining_rules }\n")
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator._collect_definitions()

    validator._validate_rule_groups()

    assert validator._issues == []


def test_duplicate_rule_scan_skips_rules_files_named_for_a_collection(tmp_path):
    # Any rules path containing "groups" is excluded, so a collection file that
    # re-lists an existing rule ID never reads as a duplicate definition.
    root = _faction_dirs(tmp_path)
    _write_text(root / "rules" / "a.txt", "rule_one = { type = joining_rules }\n")
    _write_text(
        root / "rules" / "member_groups.txt", "rule_one = { type = member_rules }\n"
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator._validate_duplicate_rules()

    assert validator._issues == []


def _goal(completed: str) -> str:
    return f"goal_one = {{\n\tcompleted = {{\n{completed}\n\t}}\n}}\n"


@pytest.mark.parametrize(
    "completed, expected",
    [
        (
            "\t\tscope:faction = {\n"
            "\t\t\tcheck_variable = {\n"
            "\t\t\t\tvar = goal_tanks_cache\n"
            "\t\t\t\tvalue = 10\n"
            "\t\t\t\tcompare = greater_than_or_equals\n"
            "\t\t\t}\n"
            "\t\t}",
            [(5, "goal_tanks_cache")],
        ),
        (
            "\t\tscope:faction = { check_variable = { goal_tanks_cache > 1 } }",
            [(3, "goal_tanks_cache")],
        ),
        (
            "\t\tscope:faction = { has_variable = goal_tanks_cache }",
            [(3, "goal_tanks_cache")],
        ),
        (
            "\t\tscope:faction = {\n"
            "\t\t\tcustom_trigger_tooltip = {\n"
            "\t\t\t\ttooltip = goal_tt\n"
            "\t\t\t\tOR = {\n"
            "\t\t\t\t\tcheck_variable = { goal_tanks_cache = 1 }\n"
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}",
            [(7, "goal_tanks_cache")],
        ),
        (
            "\t\tscope:faction = {\n"
            '\t\t\thas_global_flag = "stray } brace"\n'
            "\t\t\tcheck_variable = { goal_tanks_cache = 1 }\n"
            "\t\t}",
            [(5, "goal_tanks_cache")],
        ),
        (
            "\t\tscope:faction = { count_triggers = { amount = 1"
            " check_variable = { goal_tanks_cache > 1 } } }",
            [(3, "goal_tanks_cache")],
        ),
        (
            "\t\tscope:faction = { count_triggers = { amount = 1"
            " has_variable = goal_tanks_cache } }",
            [(3, "goal_tanks_cache")],
        ),
        (
            "\t\tscope:faction = {\n"
            "\t\t\tcount_triggers = {\n"
            "\t\t\t\tamount = 1\n"
            "\t\t\t\tcheck_variable = {\n"
            "\t\t\t\t\tvar = goal_tanks_cache\n"
            "\t\t\t\t\tvalue = 10\n"
            "\t\t\t\t\tcompare = greater_than_or_equals\n"
            "\t\t\t\t}\n"
            "\t\t\t}\n"
            "\t\t}",
            [(7, "goal_tanks_cache")],
        ),
    ],
)
def test_cache_read_in_faction_scope_is_found(completed, expected):
    assert find_faction_scope_cache_reads(_goal(completed)) == expected


@pytest.mark.parametrize(
    "completed",
    [
        "\t\tfaction_leader = { check_variable = { goal_tanks_cache = 1 } }",
        "\t\tcheck_variable = { goal_tanks_cache = 1 }",
        "\t\tscope:faction = {\n"
        "\t\t\tfaction_leader = { check_variable = { goal_tanks_cache = 1 } }\n"
        "\t\t}",
        "\t\tscope:faction = { count_triggers = { amount = 1"
        " faction_leader = { check_variable = { goal_tanks_cache > 1 } } } }",
        "\t\tscope:faction = { check_variable = { goal_tanks_cached = 1 } }",
        "\t\tscope:faction = { check_variable = { ROOT.goal_tanks_cache = 1 } }",
        "\t\tscope:faction = { set_temp_variable = { goal_tanks_cache = 1 } }",
        "\t\tscope:faction = { goal_update_tanks_cache = yes }",
    ],
)
def test_cache_read_outside_faction_scope_is_not_found(completed):
    assert find_faction_scope_cache_reads(_goal(completed)) == []


def test_goal_cache_scope_check_reports_file_and_line(tmp_path):
    root = _faction_dirs(tmp_path)
    _write_text(
        root / "goals" / "a.txt",
        _goal("\t\tscope:faction = { check_variable = { goal_tanks_cache = 1 } }"),
    )
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator._validate_goal_cache_scope()

    assert [
        (issue.category, issue.file, issue.line) for issue in validator._issues
    ] == [("faction-goal-cache-scope", "common/factions/goals/a.txt", 3)]
    assert "goal_tanks_cache" in validator._issues[0].message
    assert validator.errors_found == 1


def test_script_entry_point_exits_nonzero_under_strict(tmp_path, monkeypatch):
    _write_broken_tree(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            validate_factions.__file__,
            "--path",
            str(tmp_path),
            "--strict",
            "--workers",
            "1",
            "--no-color",
        ],
    )

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(validate_factions.__file__, run_name="__main__")

    assert exit_info.value.code == 1
