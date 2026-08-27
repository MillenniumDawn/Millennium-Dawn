"""Tests for the slotless-category `allowed` stripper.

The blocks it removes are unreachable gates, but the ones it leaves alone are
load-bearing: an `allowed` in a slotted category filters the pool that slot
draws from, so removing it there would change what the player can pick.
"""

from strip_idea_allowed_gates import process_file, strip_allowed_blocks

SLOTLESS = frozenset({"country", "hidden_ideas"})


def _strip(text):
    out, removed, _skipped = strip_allowed_blocks(text.split("\n"), SLOTLESS)
    return "\n".join(out), removed


def _strip_full(text):
    out, removed, skipped = strip_allowed_blocks(text.split("\n"), SLOTLESS)
    return "\n".join(out), removed, skipped


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


def test_closer_shared_with_the_idea_own_brace_keeps_that_brace():
    # `allowed = { ... } }` puts the idea's own closer on the same line. A
    # per-line depth counter stops at "reached zero" and eats both, renesting
    # every block after it.
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            "\t\t\tallowed = { original_tag = FOO } }",
            "\t\tBAR_idea = {",
            "\t\t\tallowed = { original_tag = BAR }",
            "\t\t\tpicture = gold",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    # The second block proves the category stack did not drift a level deeper
    # when the shared closer was emitted.
    assert removed == 2
    assert out.count("{") == out.count("}")
    assert "BAR_idea" in out
    assert "original_tag" not in out
    # The surviving `}` keeps the opener's indent, not column zero.
    assert out.split("\n")[3] == "\t\t\t }"


def test_removed_block_leaves_no_blank_against_the_idea_braces():
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            "\t\t\tallowed = { original_tag = FOO }",
            "",
            "\t\t\tpicture = gold",
            "",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    out, removed = _strip(text)
    assert removed == 1
    assert out.split("\n") == [
        "ideas = {",
        "\tcountry = {",
        "\t\tFOO_idea = {",
        "\t\t\tpicture = gold",
        "",
        "\t\t}",
        "\t}",
        "}",
    ]


def test_unbalanced_block_is_left_alone():
    # A source file whose braces never close must not be rewritten from the
    # opener to EOF.
    text = "\n".join(
        [
            "ideas = {",
            "\tcountry = {",
            "\t\tFOO_idea = {",
            "\t\t\tallowed = {",
            "\t\t\t\toriginal_tag = FOO",
        ]
    )
    out, removed, skipped = _strip_full(text)
    assert (removed, skipped) == (0, 1)
    assert out == text


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


_SAMPLE = (
    "ideas = {\n\tcountry = {\n\t\tFOO_idea = {\n"
    "\t\t\tallowed = { original_tag = FOO }\n"
    "\t\t\tpicture = gold\n\t\t}\n\t}\n}\n"
)


def _write(path, text, newline=""):
    with open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)


def test_dry_run_reports_without_writing(tmp_path):
    path = tmp_path / "test.txt"
    _write(path, _SAMPLE)

    assert process_file(str(path), SLOTLESS, dry_run=True, backup=False) == (
        1,
        0,
        False,
    )
    with open(path, "r", encoding="utf-8", newline="") as handle:
        assert handle.read() == _SAMPLE


def test_crlf_survives_the_rewrite(tmp_path):
    path = tmp_path / "test.txt"
    _write(path, _SAMPLE.replace("\n", "\r\n"))

    process_file(str(path), SLOTLESS, dry_run=False, backup=False)
    with open(path, "rb") as handle:
        data = handle.read()
    assert b"\r\n" in data
    assert b"\n" not in data.replace(b"\r\n", b"")
    assert b"allowed" not in data


def test_unreadable_file_is_reported_not_raised(tmp_path):
    missing = str(tmp_path / "missing.txt")
    assert process_file(missing, SLOTLESS, False, False) == (0, 0, True)
