"""Tests for the `allowed`-in-a-slotless-category check.

`country` and `hidden_ideas` have no slot, so nothing ever picks from them and
`add_idea` is the only way in. It does not consult `allowed`, which makes the
block dead. A category that still has a slot draws from a pool `allowed`
filters, so the block stays load-bearing there.
"""

from validate_ideas import (
    IdeaIssue,
    Validator,
    _parse_ideas_from_file,
    _parse_ideas_from_text,
)

SLOTLESS = "allowed-in-slotless-category"
SLOTLESS_CATEGORIES = frozenset({"country", "hidden_ideas"})
ALWAYS_NO_CATEGORIES = frozenset({"country", "hidden_ideas", "dynamic_modifier_slots"})


def _issue_types(text):
    _defined, issues = _parse_ideas_from_text(
        text, SLOTLESS_CATEGORIES, ALWAYS_NO_CATEGORIES
    )
    return {i.issue_type for i in issues}


def _wrap(body, category="country"):
    return "ideas = {\n\t" + category + " = {\n" + body + "\n\t}\n}\n"


def test_allowed_in_country_flagged():
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = { original_tag = ISR }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}"
    )
    assert SLOTLESS in _issue_types(text)


def test_allowed_in_hidden_ideas_flagged():
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = {\n"
        "\t\t\t\thas_country_flag = some_flag\n"
        "\t\t\t}\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}",
        category="hidden_ideas",
    )
    assert SLOTLESS in _issue_types(text)


def test_allowed_in_slotted_category_not_flagged():
    text = _wrap(
        "\t\tmy_designer = {\n"
        "\t\t\tallowed = { original_tag = ISR }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}",
        category="tank_manufacturer",
    )
    assert SLOTLESS not in _issue_types(text)


def test_idea_without_allowed_not_flagged():
    text = _wrap("\t\tmy_idea = {\n\t\t\tpicture = GFX_idea_x\n\t\t}")
    assert SLOTLESS not in _issue_types(text)


def test_allowed_civil_war_alone_not_flagged():
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed_civil_war = { always = yes }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}"
    )
    assert SLOTLESS not in _issue_types(text)


def test_always_no_in_slotless_reports_only_the_broader_rule():
    # A slotless idea never gets both findings for the same block.
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = { always = no }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}"
    )
    types = _issue_types(text)
    assert SLOTLESS in types
    assert "allowed-always-no" not in types


def test_always_no_still_fires_in_a_hidden_but_slotted_category():
    # dynamic_modifier_slots is hidden yet has a slot, so it keeps its
    # `allowed` and only the dead always = no form is redundant. Guards the
    # always-no rule against being retired by the slotless one.
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = { always = no }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}",
        category="dynamic_modifier_slots",
    )
    types = _issue_types(text)
    assert "allowed-always-no" in types
    assert SLOTLESS not in types


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def test_validator_uses_target_root_and_reports_error(tmp_path):
    _write(
        tmp_path / "common" / "idea_tags" / "00_idea.txt",
        "idea_categories = {\n\tcustom_slotless = { type = national_spirit }\n}\n",
    )
    _write(
        tmp_path / "common" / "ideas" / "test.txt",
        _wrap(
            "\t\tmy_idea = {\n\t\t\tallowed = { always = yes }\n\t\t}",
            category="custom_slotless",
        ),
    )

    validator = Validator(
        str(tmp_path), use_colors=False, workers=1, unused_ideas=False
    )
    _defined, issues_by_file, _ideas_by_file = validator._parse_all_ideas()

    assert {
        issue.issue_type for issues in issues_by_file.values() for issue in issues
    } == {SLOTLESS}
    validator.validate_idea_quality(issues_by_file)
    assert validator.errors_found == 1


def test_category_sets_are_part_of_parser_cache_key(tmp_path):
    idea_file = tmp_path / "common" / "ideas" / "test.txt"
    _write(
        idea_file,
        _wrap(
            "\t\tmy_idea = {\n\t\t\tallowed = { always = yes }\n\t\t}",
            category="custom_slotless",
        ),
    )

    _defined, first = _parse_ideas_from_file(
        str(idea_file), str(tmp_path), frozenset(), frozenset()
    )
    _defined, second = _parse_ideas_from_file(
        str(idea_file),
        str(tmp_path),
        frozenset({"custom_slotless"}),
        frozenset({"custom_slotless"}),
    )

    assert first == []
    assert {issue.issue_type for issue in second} == {SLOTLESS}


def test_staged_idea_tags_change_runs_full_quality_scan():
    validator = Validator("/nonexistent", use_colors=False, workers=1)
    validator.staged_only = True
    validator.staged_files = ["common/idea_tags/00_idea.txt"]
    issue = IdeaIssue("my_idea", "country", 1, SLOTLESS)
    all_issues = {"common/ideas/test.txt": [issue]}
    validator._parse_all_ideas = lambda: ({}, all_issues, {})
    calls = []
    validator.validate_idea_quality = lambda issues_by_file: calls.append(
        issues_by_file
    )
    validator.validate_undefined_idea_refs = lambda defined_ideas: None
    validator.validate_category_icon_frames = lambda: None
    validator.validate_missing_icons = lambda defined_ideas: None
    validator.validate_unused_ideas = lambda defined_ideas, ideas_by_file: None

    validator.run_validations()

    assert calls == [all_issues]
