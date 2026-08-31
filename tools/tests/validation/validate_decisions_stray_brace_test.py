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


def test_factory_token_matches_noncanonical_header_spacing():
    canonical = "\tdecision_one = {\n\t\tdays_remove = 5\n\t}\n"
    spaced = "\tdecision_one= {\n\t\tdays_remove = 5\n\t}\n"

    assert V.DecisionFactory(dec=canonical).token == "decision_one"
    assert V.DecisionFactory(dec=spaced).token == "decision_one"


def test_quoted_brace_does_not_truncate_decision_block(tmp_path):
    # A `}` inside a multi-line quoted field lands on its own `\t}` line — the
    # exact shape the block closer `^\t\}` matches. Without neutralizing quoted
    # strings first, parse_all_decisions closes the block there and drops every
    # field after it (here `cost`).
    dec_dir = tmp_path / "common" / "decisions"
    dec_dir.mkdir(parents=True)
    (dec_dir / "quoted_brace.txt").write_text(
        "my_category = {\n"
        "\tstray_brace_decision = {\n"
        '\t\tname = "Broken\n'
        "\t}\n"
        '\tstring"\n'
        "\t\tcost = 42\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )

    decisions, _ = V.parse_all_decisions(str(tmp_path))

    assert len(decisions) == 1
    factory = V.DecisionFactory(dec=decisions[0])
    assert factory.token == "stray_brace_decision"
    assert factory.cost == "42"


def test_scan_picks_up_remove_targeted_decision_only(tmp_path):
    # File uses only `remove_targeted_decision` (no bare `remove_decision`), so
    # the substring gate must admit it or the removal scan never runs.
    f = tmp_path / "effects.txt"
    f.write_text(
        "some_effect = {\n"
        "\tremove_targeted_decision = { target = ROOT decision = my_targeted_dec }\n"
        "}\n",
        encoding="utf-8",
    )

    _, _, removals = V._scan_activations_and_removals(str(f))

    assert "my_targeted_dec" in removals
