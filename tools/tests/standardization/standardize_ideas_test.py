"""Tests for the idea standardizer.

Regression guard for the content-loss bug where body comments were silently
dropped and unknown / nested blocks (``available``, ``ai_will_do``, ...) were
flattened line-by-line into a single indent level. The standardizer must keep
every comment, preserve nested block structure (balanced braces, intact
nesting), and round-trip idempotently.
"""

import re
import sys

import standardize_ideas
from standardize_ideas import IdeaStandardizer


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _read(path):
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _idea(lines):
    """Wrap idea-block body lines (header + closing brace) as newline-terminated input."""
    return [line + "\n" for line in lines]


def _standardize(lines):
    """Run extract_properties + format_block on a single idea block, base indent one tab."""
    std = IdeaStandardizer()
    props = std.extract_properties(lines)
    return std.format_block(props, "\t")


def _brace_balanced(out_lines):
    text = "\n".join(out_lines)
    return text.count("{") == text.count("}")


def test_body_comment_preserved():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\tpicture = test_picture",
            "\t\t# a load-bearing body comment",
            "\t\tcost = 80",
            "\t}",
        ]
    )
    out = _standardize(block)
    assert any("# a load-bearing body comment" in line for line in out)
    assert any("cost = 80" in line for line in out)


def test_body_comment_follows_its_property_through_reordering():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\t# scales with the coalition",
            "\t\tmodifier = { stability_factor = 0.05 }",
            "\t\tpicture = test_picture",
            "\t}",
        ]
    )
    out = _standardize(block)
    comment = out.index("\t\t# scales with the coalition")
    assert "modifier" in out[comment + 1]


def test_comment_on_a_dropped_always_no_block_survives():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\tpicture = test_picture",
            "\t\t# why this was gated off",
            "\t\tcancel = { always = no }",
            "\t}",
        ]
    )
    out = _standardize(block)
    assert any("# why this was gated off" in line for line in out)
    assert not any("always = no" in line for line in out)


def test_allowed_always_no_is_kept():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\tpicture = test_picture",
            "\t\tallowed = { always = no }",
            "\t}",
        ]
    )
    out = _standardize(block)
    assert any("allowed = { always = no }" in line for line in out)


def test_unknown_nested_block_preserved_and_indented():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\tpicture = test_picture",
            "\t\tavailable = {",
            "\t\t\thas_war = no",
            "\t\t\tif = {",
            "\t\t\t\tlimit = { original_tag = TAG }",
            "\t\t\t\tset_country_flag = foo",
            "\t\t\t}",
            "\t\t}",
            "\t}",
        ]
    )
    out = _standardize(block)
    text = "\n".join(out)

    assert _brace_balanced(out)
    for token in (
        "available = {",
        "has_war = no",
        "if = {",
        "limit = { original_tag = TAG }",
        "set_country_flag = foo",
    ):
        assert token in text, token

    # Nesting intact: the inner effect is indented deeper than the block header.
    def depth(line):
        return len(line) - len(line.lstrip("\t"))

    avail = next(line for line in out if "available = {" in line)
    inner = next(line for line in out if "set_country_flag = foo" in line)
    assert depth(inner) > depth(avail)


def test_known_modifier_multichild_stays_multiline():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\tmodifier = {",
            "\t\t\tstability_factor = 0.05",
            "\t\t\twar_support_factor = 0.05",
            "\t\t}",
            "\t}",
        ]
    )
    out = _standardize(block)
    text = "\n".join(out)
    assert "stability_factor = 0.05" in text
    assert "war_support_factor = 0.05" in text
    # Two leaves: not collapsed onto the `modifier = {` line.
    assert not any(
        "stability_factor" in line and "war_support_factor" in line for line in out
    )


def test_ai_will_do_inner_comments_preserved():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\tai_will_do = {",
            "\t\t\tbase = 1",
            "\t\t\t# Killswitch for the AI",
            "\t\t\tmodifier = {",
            "\t\t\t\tfactor = 0",
            "\t\t\t\thas_war = yes",
            "\t\t\t}",
            "\t\t}",
            "\t}",
        ]
    )
    out = _standardize(block)
    text = "\n".join(out)
    assert "# Killswitch for the AI" in text
    assert "factor = 0" in text
    assert _brace_balanced(out)


def test_quoted_string_preserved_byte_exact():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            '\t\tname = "My Fancy Idea, with punctuation."',
            "\t\ton_add = {",
            '\t\t\tlog = "[GetDateText]: [Root.GetName]: custom message"',
            "\t\t\tadd_stability = 0.05",
            "\t\t}",
            "\t}",
        ]
    )
    out = _standardize(block)
    text = "\n".join(out)
    assert '"My Fancy Idea, with punctuation."' in text
    assert '"[GetDateText]: [Root.GetName]: custom message"' in text


def test_allowed_tag_rewritten_to_original_tag():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\tallowed = {",
            "\t\t\ttag = TAG",
            "\t\t}",
            "\t}",
        ]
    )
    out = _standardize(block)
    text = "\n".join(out)
    assert "original_tag = TAG" in text
    assert not any(line.strip() == "tag = TAG" for line in out)


def test_ledger_emitted_after_allowed_but_before_modifier():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\tmodifier = { stability_factor = 0.05 }",
            "\t\tledger = army",
            "\t\tallowed = {",
            "\t\t\toriginal_tag = TAG",
            "\t\t}",
            "\t\tai_will_do = { base = 1 }",
            "\t}",
        ]
    )
    out = _standardize(block)
    allowed_idx = next(
        i for i, line in enumerate(out) if line.strip().startswith("allowed")
    )
    ledger_idx = next(
        i for i, line in enumerate(out) if line.strip() == "ledger = army"
    )
    modifier_idx = next(
        i for i, line in enumerate(out) if line.strip().startswith("modifier")
    )
    assert allowed_idx < ledger_idx < modifier_idx


def test_idempotent():
    block = _idea(
        [
            "\tTAG_test_idea = {",
            "\t\tpicture = test_picture",
            "\t\tallowed = {",
            "\t\t\toriginal_tag = TAG",
            "\t\t}",
            "\t\t# body comment kept",
            "\t\tavailable = {",
            "\t\t\thas_war = no",
            "\t\t\tif = {",
            "\t\t\t\tlimit = { original_tag = TAG }",
            "\t\t\t\tset_country_flag = foo",
            "\t\t\t}",
            "\t\t}",
            "\t\tmodifier = {",
            "\t\t\tstability_factor = 0.05",
            "\t\t\twar_support_factor = 0.05",
            "\t\t}",
            "\t\tcost = 80",
            "\t}",
        ]
    )
    first = _standardize(block)
    second = _standardize([line + "\n" for line in first])
    assert first == second
    assert any("# body comment kept" in line for line in first)
    assert _brace_balanced(first)


def test_block_pattern_matches_an_idea_opener():
    pattern = IdeaStandardizer().get_block_pattern()
    assert re.match(pattern, "\tTAG_test_idea = {")
    assert not re.match(pattern, "\t# TAG_test_idea = {")


def test_packed_opener_keeps_later_comments_and_plain_lines():
    out = _standardize(
        _idea(
            [
                "\tTAG_packed = { picture = test_picture",
                "\t\t# a note above the modifier",
                "\t\tmodifier = { stability_factor = 0.05 } # keep this",
                "\t\tname = TAG_packed_name",
                "\t}",
            ]
        )
    )
    text = "\n".join(out)
    assert "picture = test_picture" in text
    assert "name = TAG_packed_name" in text
    assert "# a note above the modifier" in text
    assert "# keep this" in text
    assert _brace_balanced(out)


def test_blank_body_lines_are_dropped():
    out = _standardize(
        _idea(
            [
                "\tTAG_spaced = {",
                "\t\tpicture = test_picture",
                "",
                "\t\tname = TAG_spaced_name",
                "\t}",
            ]
        )
    )
    assert out == [
        "\tTAG_spaced = {",
        "\t\tname = TAG_spaced_name",
        "\t\tpicture = test_picture",
        "\t}",
    ]


def test_idea_without_a_readable_id_falls_back_to_idea():
    standardizer = IdeaStandardizer()
    props = standardizer.extract_properties(["{\n", "\tpicture = x\n", "}\n"])
    assert props["id"] == ""
    assert standardizer.format_block(props, "\t")[0] == "\tidea = {"


def test_empty_log_block_detection():
    standardizer = IdeaStandardizer()
    assert standardizer.is_empty_log_block([])
    assert standardizer.is_empty_log_block(
        ["on_add = {", "\t# only a note", '\tlog = ""', "}"]
    )
    assert not standardizer.is_empty_log_block(
        ["on_add = {", "\tadd_stability = 0.05", "}"]
    )


def test_meaningful_effect_detection_of_an_empty_block():
    assert not IdeaStandardizer().has_meaningful_effects([])


def test_always_no_filter_only_applies_to_gate_properties():
    standardizer = IdeaStandardizer()
    block = ["cancel = {", "\talways = no", "}"]
    assert not standardizer.is_always_no_block(block, "modifier")
    assert not standardizer.is_always_no_block(block, "allowed")
    assert standardizer.is_always_no_block(block, "cancel")


def test_compact_block_boundaries():
    standardizer = IdeaStandardizer()
    assert standardizer.compact_block([]) == []
    assert standardizer.compact_block(
        ["on_add = {", "", "\tadd_stability = 0.05", "}"], "\t\t"
    ) == ["\t\ton_add = {", "\t\t\tadd_stability = 0.05", "\t\t}"]


def test_single_line_on_add_with_effects_is_exploded_and_logged():
    out = _standardize(
        _idea(
            [
                "\tTAG_lifecycle = {",
                "\t\tpicture = x",
                "\t\ton_add = { add_stability = 0.05 }",
                "\t}",
            ]
        )
    )
    assert out == [
        "\tTAG_lifecycle = {",
        "\t\tpicture = x",
        "\t\ton_add = {",
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Idea TAG_lifecycle added"',
        "\t\t\tadd_stability = 0.05",
        "\t\t}",
        "\t}",
    ]
    assert _standardize([line + "\n" for line in out]) == out


def test_effectless_lifecycle_blocks_are_dropped():
    out = _standardize(
        _idea(
            [
                "\tTAG_lifecycle = {",
                "\t\tpicture = x",
                "\t\ton_add = {",
                "\t\t}",
                "\t\ton_remove = {",
                '\t\t\tlog = "[GetDateText]: [Root.GetName]: Idea TAG_lifecycle removed"',
                "\t\t}",
                "\t}",
            ]
        )
    )
    assert out == ["\tTAG_lifecycle = {", "\t\tpicture = x", "\t}"]


_IDEAS_FILE = """ideas = {
\tcountry = {
\t\tTST_idea = {
\t\t\tpicture = test_picture
\t\t\tallowed = { tag = TST }
\t\t}
\t}
}
"""


def test_standardize_file_rewrites_nested_ideas(tmp_path):
    source = tmp_path / "ideas.txt"
    output = tmp_path / "out.txt"
    _write(source, _IDEAS_FILE)

    standardizer = IdeaStandardizer()
    assert standardizer.standardize_file(str(source), str(output))
    assert standardizer.processed_count == 1
    once = _read(output)
    assert once == (
        "ideas = {\n"
        "\tcountry = {\n"
        "\t\tTST_idea = {\n"
        "\t\t\tpicture = test_picture\n"
        "\t\t\tallowed = { original_tag = TST }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )

    assert IdeaStandardizer().standardize_file(str(output), str(output))
    assert _read(output) == once


def test_standardize_file_reports_a_missing_input(tmp_path):
    assert not IdeaStandardizer().standardize_file(
        str(tmp_path / "absent.txt"), str(tmp_path / "out.txt")
    )


def test_main_standardizes_the_named_file(tmp_path, monkeypatch):
    source = tmp_path / "ideas.txt"
    _write(source, _IDEAS_FILE)
    monkeypatch.setattr(sys, "argv", ["standardize_ideas.py", str(source)])

    standardize_ideas.main()

    assert "original_tag = TST" in _read(source)
