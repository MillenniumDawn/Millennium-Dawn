"""Tests for the `allowed`-in-a-slotless-category check.

`country` and `hidden_ideas` have no slot, so nothing ever picks from them and
`add_idea` is the only way in. It does not consult `allowed`, which makes the
block dead. A category that still has a slot draws from a pool `allowed`
filters, so the block stays load-bearing there.
"""

from validate_ideas import _parse_ideas_from_text

SLOTLESS = "allowed-in-slotless-category"


def _issue_types(text):
    _defined, issues = _parse_ideas_from_text(text)
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
    # The two rules partition the categories, so a slotless idea never gets
    # both findings for the same block.
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = { always = no }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}"
    )
    types = _issue_types(text)
    assert SLOTLESS in types
    assert "allowed-always-no" not in types
