"""Tests for the slotless-category `allowed` stripper.

The blocks it removes are unreachable gates, but the ones it leaves alone are
load-bearing: an `allowed` in a slotted category filters the pool that slot
draws from, so removing it there would change what the player can pick.
"""

from strip_idea_allowed_gates import strip_allowed_blocks

SLOTLESS = frozenset({"country", "hidden_ideas"})


def _strip(text):
    out, removed = strip_allowed_blocks(text.split("\n"), SLOTLESS)
    return "\n".join(out), removed


def test_removes_one_line_allowed_in_country():
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            "\t\t\tallowed = { original_tag = FOO }",
            "\t\t\tpicture = gold",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    assert removed == 1
    assert "allowed" not in out
    assert "picture = gold" in out


def test_removes_multiline_allowed_in_hidden_ideas():
    text = "\n".join(
        [
            "ideas = {",
            "\thidden_ideas = {",
            "\t\tFOO_idea = {",
            "\t\t\tallowed = {",
            "\t\t\t\tOR = {",
            "\t\t\t\t\toriginal_tag = FOO",
            "\t\t\t\t\toriginal_tag = BAR",
            "\t\t\t\t}",
            "\t\t\t}",
            "\t\t\tpicture = gold",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    assert removed == 1
    assert "original_tag" not in out
    assert out.count("{") == out.count("}") == 3


def test_keeps_allowed_in_slotted_category():
    text = "\n".join(
        [
            "ideas = {",
            "\ttank_manufacturer = {",
            "\t\tFOO_designer = {",
            "\t\t\tallowed = { original_tag = FOO }",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    assert removed == 0
    assert "allowed = { original_tag = FOO }" in out


def test_keeps_allowed_civil_war():
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            "\t\t\tallowed_civil_war = { always = yes }",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    assert removed == 0
    assert "allowed_civil_war" in out


def test_keeps_nested_allowed_inside_another_block():
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            "\t\t\ton_add = {",
            "\t\t\t\tallowed = { original_tag = FOO }",
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    assert removed == 0
    assert "allowed = { original_tag = FOO }" in out


def test_brace_depth_survives_quoted_brace():
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            '\t\t\ton_add = { log = "a { b" }',
            "\t\t\tallowed = { original_tag = FOO }",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    assert removed == 1
    assert 'log = "a { b"' in out


def test_ignores_commented_out_allowed():
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            "\t\t\t# allowed = { original_tag = FOO }",
            "\t\t\tpicture = gold",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    assert removed == 0
    assert "# allowed = { original_tag = FOO }" in out


def test_removes_every_allowed_in_a_multi_idea_file():
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            "\t\t\tallowed = { original_tag = FOO }",
            "\t\t}",
            "",
            "\t\tBAR_idea = {",
            "\t\t\tallowed = {",
            "\t\t\t\toriginal_tag = BAR",
            "\t\t\t}",
            "\t\t\tpicture = gold",
            "\t\t}",
            "\t}",
            "\ttank_manufacturer = {",
            "\t\tBAZ_designer = {",
            "\t\t\tallowed = { original_tag = BAZ }",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    assert removed == 2
    assert "original_tag = BAZ" in out
    assert "original_tag = FOO" not in out
    assert "original_tag = BAR" not in out


def test_is_idempotent():
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            "\t\t\tallowed = { original_tag = FOO }",
            "\t\t\tpicture = gold",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    once, _ = _strip(text)
    twice, removed = _strip(once)
    assert removed == 0
    assert twice == once
