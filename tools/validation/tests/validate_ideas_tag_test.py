"""Tests for the tag-vs-original_tag check in idea `allowed` blocks.

`tag = XXX` in an idea's `allowed` block breaks for civil-war split-offs
(their runtime tag changes); `original_tag` is stable. The check must:
- extract the `allowed` block with brace balancing (so a `tag =` after a
  nested block is still seen),
- fire in a slotless category too, where the whole block is redundant anyway,
- flag a redundant `original_tag` + `tag` pair.

Cases default to `political_reforms` because that is where an `allowed` block
still belongs; a slotless category has none left to check.
"""

from validate_ideas import _parse_ideas_from_text


def _issue_types(text):
    _defined, issues = _parse_ideas_from_text(text)
    return {i.issue_type for i in issues}


def _wrap(body, category="political_reforms"):
    return "ideas = {\n\t" + category + " = {\n" + body + "\n\t}\n}\n"


def test_bare_tag_flagged():
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = { tag = ISR }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}"
    )
    assert "tag-not-original-tag" in _issue_types(text)


def test_original_tag_not_flagged():
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = { original_tag = ISR }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}"
    )
    types = _issue_types(text)
    assert "tag-not-original-tag" not in types
    assert "redundant-tag-and-original-tag" not in types


def test_runtime_tag_flagged():
    # A civil-war runtime tag (longer than 3 chars) must still be caught.
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = { tag = ISR_CW_0 }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}"
    )
    assert "tag-not-original-tag" in _issue_types(text)


def test_tag_after_nested_block_flagged():
    # A nested block before the tag = line closes `[^}]*` early in the old
    # regex; brace-balanced extraction still sees the tag.
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = {\n"
        "\t\t\t\tNOT = { has_global_flag = x }\n"
        "\t\t\t\ttag = ISR\n"
        "\t\t\t}\n"
        "\t\t}"
    )
    assert "tag-not-original-tag" in _issue_types(text)


def test_redundant_tag_and_original_tag_flagged():
    text = _wrap(
        "\t\tmy_idea = {\n\t\t\tallowed = { original_tag = ISR tag = ISR }\n\t\t}"
    )
    assert "redundant-tag-and-original-tag" in _issue_types(text)


def test_bare_tag_flagged_in_slotless_category():
    # The cases above use political_reforms, the only category where an
    # `allowed` block belongs. The check must still fire in a slotless one,
    # where the whole block is redundant but the tag is the worse problem.
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = { tag = ISR }\n"
        "\t\t\tpicture = GFX_idea_x\n"
        "\t\t}",
        category="country",
    )
    assert "tag-not-original-tag" in _issue_types(text)


def test_tag_and_original_tag_in_different_or_branches_not_redundant():
    # A shared multi-country idea: tag and original_tag are OR alternatives,
    # not redundant siblings. Still a bare-tag warning, never "redundant".
    text = _wrap(
        "\t\tmy_idea = {\n"
        "\t\t\tallowed = {\n"
        "\t\t\t\tOR = {\n"
        "\t\t\t\t\toriginal_tag = ISR\n"
        "\t\t\t\t\ttag = USA\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t}"
    )
    types = _issue_types(text)
    assert "redundant-tag-and-original-tag" not in types
    assert "tag-not-original-tag" in types
