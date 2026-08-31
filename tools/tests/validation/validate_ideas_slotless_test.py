"""Tests for the `allowed`/`available`-in-a-slotless-category checks.

`country` and `hidden_ideas` have no slot, so nothing ever picks from them and
`add_idea` is the only way in. It consults neither block, which makes both dead.
A category that still has a slot draws from a pool those blocks filter, so they
stay load-bearing there. `allowed_civil_war` and `cancel` are the live
alternatives and are never flagged.
"""

import pytest
from validate_ideas import (
    IdeaIssue,
    Validator,
    _parse_ideas_from_file,
    _parse_ideas_from_text,
)

GATES = ("allowed", "available")
# The two gates take different trigger shapes in the wild; cover one of each.
GATE_TRIGGERS = (
    ("allowed", "{ original_tag = ISR }"),
    ("available", "{ emerging_communist_state_are_in_power = yes }"),
)
SLOTLESS_CATEGORIES = frozenset({"country", "hidden_ideas"})


def _slotless(gate):
    return f"{gate}-in-slotless-category"


def _every_slotless_issue():
    return {_slotless(gate) for gate in GATES}


def _issue_types(text):
    _defined, issues = _parse_ideas_from_text(text, SLOTLESS_CATEGORIES)
    return {i.issue_type for i in issues}


def _wrap(body, category="country"):
    return "ideas = {\n\t" + category + " = {\n" + body + "\n\t}\n}\n"


def _idea(*lines):
    body = "".join("\t\t\t" + line + "\n" for line in lines)
    return "\t\tmy_idea = {\n" + body + "\t\t\tpicture = GFX_idea_x\n\t\t}"


@pytest.mark.parametrize(("gate", "trigger"), GATE_TRIGGERS)
def test_gate_in_country_flagged(gate, trigger):
    text = _wrap(_idea(f"{gate} = {trigger}"))
    assert _slotless(gate) in _issue_types(text)


@pytest.mark.parametrize("gate", GATES)
def test_gate_in_hidden_ideas_flagged(gate):
    body = _idea(f"{gate} = {{", "\thas_country_flag = some_flag", "}")
    assert _slotless(gate) in _issue_types(_wrap(body, category="hidden_ideas"))


@pytest.mark.parametrize("gate", GATES)
def test_gate_in_slotted_category_not_flagged(gate):
    body = _idea(f"{gate} = {{ original_tag = ISR }}")
    text = _wrap(body, category="tank_manufacturer")
    assert _slotless(gate) not in _issue_types(text)


def test_idea_without_a_gate_not_flagged():
    text = _wrap("\t\tmy_idea = {\n\t\t\tpicture = GFX_idea_x\n\t\t}")
    assert not _issue_types(text) & _every_slotless_issue()


@pytest.mark.parametrize("live_gate", ("allowed_civil_war", "cancel"))
def test_live_alternative_alone_not_flagged(live_gate):
    text = _wrap(_idea(f"{live_gate} = {{ always = yes }}"))
    assert not _issue_types(text) & _every_slotless_issue()


def test_always_no_allowed_in_slotless_reports_only_the_broader_rule():
    # A slotless idea never gets two findings for the same block.
    text = _wrap(_idea("allowed = { always = no }"))
    assert _issue_types(text) == {_slotless("allowed")}


def test_always_no_allowed_in_a_slotted_category_is_not_this_parsers_job():
    # An ideas file groups slotted ideas by SLOT name, never by category, so a
    # group key can only ever be a slot or a slotless category. That leaves no
    # reachable input for an always-no rule keyed on the category, and
    # check_common_mistakes.py covers the half that is reachable.
    text = _wrap(_idea("allowed = { always = no }"), category="political_advisor")
    assert _issue_types(text) == set()


def test_always_yes_available_in_slotless_still_flagged():
    text = _wrap(_idea("available = { always = yes }"))
    assert _issue_types(text) == {_slotless("available")}


def test_both_gates_flagged_in_country():
    body = _idea("allowed = { original_tag = ISR }", "available = { always = yes }")
    assert _issue_types(_wrap(body)) == _every_slotless_issue()


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _custom_slotless_idea(gate):
    return _wrap(
        "\t\tmy_idea = {\n\t\t\t" + gate + " = { always = yes }\n\t\t}",
        category="custom_slotless",
    )


@pytest.mark.parametrize("gate", GATES)
def test_validator_uses_target_root_and_reports_error(tmp_path, gate):
    _write(
        tmp_path / "common" / "idea_tags" / "00_idea.txt",
        "idea_categories = {\n\tcustom_slotless = { type = national_spirit }\n}\n",
    )
    _write(tmp_path / "common" / "ideas" / "test.txt", _custom_slotless_idea(gate))

    validator = Validator(
        str(tmp_path), use_colors=False, workers=1, unused_ideas=False
    )
    _defined, issues_by_file, _ideas_by_file = validator._parse_all_ideas()

    assert {
        issue.issue_type for issues in issues_by_file.values() for issue in issues
    } == {_slotless(gate)}
    validator.validate_idea_quality(issues_by_file)
    assert validator.errors_found == 1


@pytest.mark.parametrize("gate", GATES)
def test_category_set_is_part_of_parser_cache_key(tmp_path, gate):
    idea_file = tmp_path / "common" / "ideas" / "test.txt"
    _write(idea_file, _custom_slotless_idea(gate))

    _defined, first = _parse_ideas_from_file(str(idea_file), str(tmp_path), frozenset())
    _defined, second = _parse_ideas_from_file(
        str(idea_file), str(tmp_path), frozenset({"custom_slotless"})
    )

    assert first == []
    assert {issue.issue_type for issue in second} == {_slotless(gate)}


def test_staged_idea_tags_change_runs_full_quality_scan():
    validator = Validator("/nonexistent", use_colors=False, workers=1)
    validator.staged_only = True
    validator.staged_files = ["common/idea_tags/00_idea.txt"]
    issue = IdeaIssue("my_idea", "country", 1, _slotless("allowed"))
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
