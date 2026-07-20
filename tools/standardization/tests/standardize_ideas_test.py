"""Tests for the idea standardizer.

Regression guard for the content-loss bug where body comments were silently
dropped and unknown / nested blocks (``available``, ``ai_will_do``, ...) were
flattened line-by-line into a single indent level. The standardizer must keep
every comment, preserve nested block structure (balanced braces, intact
nesting), and round-trip idempotently.
"""

from standardize_ideas import IdeaStandardizer


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
