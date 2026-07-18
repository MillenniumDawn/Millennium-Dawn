"""Regression test for the decisions block matcher and a stray `\t}` line.

`_DECISIONS_BLOCK_RE` confines a decision's name to its own line (`[^\t#\n]`).
Before that, the name could span newlines, so a dangling tab-indented `}`
(a malformed extra brace) let the non-greedy match jump across a blank line and
the next column-0 `category = {` header, swallowing an unrelated block.
"""

import re

import validate_decisions as V


def _names(text):
    return [
        V._DECISION_TOKEN_LINE_RE.findall(b)[0]
        for b in V._DECISIONS_BLOCK_RE.findall(text)
    ]


def test_stray_tab_brace_does_not_jump_into_column_zero_block():
    text = (
        "cat_one = {\n"
        "\talpha_decision = {\n"
        "\t\tdays_remove = 5\n"
        "\t}\n"
        "\t}\n"  # stray dangling tab-brace (malformed extra)
        "}\n"
        "\n"
        "cat_two = {\n"
        "\tbeta_decision = {\n"
        "\t\tdays_remove = 5\n"
        "\t}\n"
        "}\n"
    )
    blocks = V._DECISIONS_BLOCK_RE.findall(text)

    # Both real decisions are found, each with its own name line.
    assert _names(text) == ["alpha_decision", "beta_decision"]
    # No extracted block swallowed a column-0 `category = {` header — that is the
    # signature of the matcher jumping out of its decision into another block.
    assert not any(re.search(r"^\w+ = \{", b, re.MULTILINE) for b in blocks)
