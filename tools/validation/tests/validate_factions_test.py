"""Behavior tests for the faction cross-reference validator."""

from validate_factions import (
    Validator,
    extract_default_rules_block,
    extract_goal_categories,
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


def _write_text(path, content):
    with path.open("w", encoding="utf-8", newline="") as file:
        file.write(content)


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
