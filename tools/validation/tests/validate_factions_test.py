"""Behavior tests for the faction cross-reference validator."""

from validate_factions import (
    Validator,
    extract_default_rules_block,
    extract_goals_block,
    extract_group_rule_ids,
    extract_upgrade_group_ids,
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

    (faction_root / "templates" / "templates.txt").write_text(
        "template_alpha = {\n"
        f"\tmanifest = {manifest}\n"
        "\tgoals = { goal_one }\n"
        "\tdefault_rules = { rule_one }\n"
        "\ticon = GFX_faction_alpha\n"
        "}\n",
        encoding="utf-8",
    )
    (faction_root / "goals" / "goals.txt").write_text(
        "goal_one = { is_manifest = yes }\n", encoding="utf-8"
    )
    (faction_root / "rules" / "rules.txt").write_text(
        "rule_one = { type = joining_rules }\n", encoding="utf-8"
    )
    (faction_root / "icons" / "pool.txt").write_text(
        "GFX_faction_alpha\n", encoding="utf-8"
    )
    (tmp_path / "interface" / "factions.gfx").write_text(
        'spriteType = { name = "GFX_faction_alpha" }\n', encoding="utf-8"
    )


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


def test_missing_template_manifest_is_reported(tmp_path):
    _write_faction_fixture(tmp_path, manifest="missing_manifest")
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator._collect_definitions()

    validator._validate_template_manifests()

    assert len(validator._issues) == 1
    assert "missing_manifest" in validator._issues[0].message
