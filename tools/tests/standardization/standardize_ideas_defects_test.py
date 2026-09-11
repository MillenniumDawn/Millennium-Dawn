"""Regressions for three idea-standardizer defects.

(a) single-line idea bodies were gutted (`foo = { modifier = { ... } }` on one
    line lost its body);
(b) non-wrapper law categories (internal_factions, religion, ...) were mistaken
    for ideas and their child ideas flattened into one mangled block;
(c) single-line on_add/on_remove blocks were non-idempotent — the injected log
    landed outside the block and re-injected on the next run.

Also guards opener-line comment preservation and that log-only single-line
lifecycle blocks are not silently stripped.
"""

from standardize_ideas import IdeaStandardizer


def _standardize_idea(lines):
    std = IdeaStandardizer()
    props = std.extract_properties([line + "\n" for line in lines])
    return std.format_block(props, "\t")


def _process(lines):
    std = IdeaStandardizer()
    return std._process_lines([line + "\n" for line in lines], 0)


def test_single_line_idea_body_preserved():
    # (a) whole idea on one line must keep its modifier body.
    out = _standardize_idea(
        ["\tMICROSTATE_fix = { modifier = { custom_modifier_tooltip = FIX_tt } }"]
    )
    text = "\n".join(out)
    assert "modifier = {" in text
    assert "custom_modifier_tooltip = FIX_tt" in text


def test_single_line_on_add_preserved_and_idempotent():
    # (a)+(c) single-line on_add keeps its effect, gets a log inside the block,
    # and round-trips.
    lines = [
        "\tmy_idea = { on_add = { set_variable = { global.x = ROOT.id } } }",
    ]
    first = _standardize_idea(lines)
    text = "\n".join(first)
    assert "set_variable = {" in text
    assert "global.x = ROOT.id" in text
    # Log injected inside the on_add block, not as a sibling of the idea.
    on_add_idx = next(i for i, ln in enumerate(first) if "on_add = {" in ln)
    log_idx = next(i for i, ln in enumerate(first) if "log =" in ln)
    assert log_idx > on_add_idx

    second = IdeaStandardizer().format_block(
        IdeaStandardizer().extract_properties([ln + "\n" for ln in first]), "\t"
    )
    assert first == second


def test_opener_line_comment_preserved():
    out = _standardize_idea(
        [
            "\tKOR_divided_military_3 = { #DDR Programs",
            "\t\tpicture = army_problems",
            "\t}",
        ]
    )
    assert any("#DDR Programs" in line for line in out)


def test_log_only_single_line_on_remove_not_stripped():
    out = _standardize_idea(
        [
            "\tfoo = {",
            "\t\tpicture = x",
            '\t\ton_remove = { log = "[GetDateText]: [Root.GetName]: remove idea foo" }',
            "\t}",
        ]
    )
    text = "\n".join(out)
    assert "remove idea foo" in text


def test_packed_single_line_category_child_not_duplicated():
    # A packed one-line category child of `ideas` must not be emitted twice (the
    # raw opener/closer path duplicated the single physical line, growing the file
    # on every run).
    src = [
        "ideas = {",
        "\tinternal_factions = { first_faction = { cost = 1500 } }",
        "}",
    ]
    out = _process(src)
    text = "\n".join(out)
    assert text.count("internal_factions = {") == 1
    assert text.count("first_faction = {") == 1
    assert text.count("cost = 1500") == 1
    # Re-processing the output is a no-op (round-trips, no exponential growth).
    assert _process(out) == out


def test_quoted_brace_in_idea_prop_does_not_drop_lines():
    # (defect) a `{` inside a quoted value must not be counted as a block opener
    # — doing so sent extract_block negative and silently deleted every line from
    # there to the idea's closer.
    out = _standardize_idea(
        [
            "\tfoo = {",
            '\t\tsome_prop = "has { brace"',
            "\t\tpicture = x",
            "\t}",
        ]
    )
    text = "\n".join(out)
    assert 'some_prop = "has { brace"' in text
    assert "picture = x" in text


def test_empty_single_line_on_add_dropped():
    # (defect) an empty single-line on_add must be dropped, not emit a stray log
    # outside the block (which accumulated one bogus idea-level log per run).
    out = _standardize_idea(
        [
            "\tfoo = {",
            "\t\tpicture = x",
            "\t\ton_add = { }",
            "\t}",
        ]
    )
    text = "\n".join(out)
    assert "on_add" not in text
    assert "log =" not in text
    second = IdeaStandardizer().format_block(
        IdeaStandardizer().extract_properties([ln + "\n" for ln in out]), "\t"
    )
    assert out == second


def test_law_category_children_not_flattened():
    # (b) a non-wrapper law category must be recursed into, so each child idea is
    # formatted separately rather than merged into one mangled block.
    out = _process(
        [
            "ideas = {",
            "\tinternal_factions = {",
            "\t\tlaw = yes",
            "\t\tfirst_faction = {",
            "\t\t\tcost = 1500",
            "\t\t\tallowed = { original_tag = SOO }",
            "\t\t}",
            "\t\tsecond_faction = {",
            "\t\t\tcost = 2000",
            "\t\t\tallowed = { original_tag = NIG }",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    text = "\n".join(out)
    # Both idea headers survive as distinct blocks and the category header stays.
    assert "internal_factions = {" in text
    assert "first_faction = {" in text
    assert "second_faction = {" in text
    # Not flattened: the two allowed blocks are not both dumped under one idea —
    # each idea keeps its own allowed.
    assert text.count("allowed = { original_tag = SOO }") == 1
    assert text.count("allowed = { original_tag = NIG }") == 1
    # first_faction closes before second_faction opens (proper nesting).
    assert text.index("first_faction") < text.index("second_faction")
    assert text.index("cost = 1500") < text.index("second_faction")


def test_law_category_header_props_preserved():
    out = _process(
        [
            "ideas = {",
            "\treligion = {",
            "\t\tlaw = yes",
            "\t\tuse_list_view = yes",
            "\t\tsunni = {",
            "\t\t\tpicture = sunni_idea",
            "\t\t}",
            "\t}",
            "}",
        ]
    )
    text = "\n".join(out)
    assert "law = yes" in text
    assert "use_list_view = yes" in text
    assert "sunni = {" in text


def test_nested_wrapper_idea_recursed_not_flattened():
    # A genuine 3-level nesting (category > wrapper key > idea) must recurse into
    # the middle wrapper so each child idea is standardized. Treating the wrapper
    # as one idea instead preserves its children verbatim (no tag rewrite, blocks
    # collapsed) -- the bug this guards against.
    src = [
        "ideas = {",
        "\tcountry = {",
        "\t\tpolitical_advisor = {",
        "\t\t\tTAG_advisor_one = {",
        "\t\t\t\tallowed = { tag = SOO }",
        "\t\t\t}",
        "\t\t\tTAG_advisor_two = {",
        "\t\t\t\tallowed = { tag = NIG }",
        "\t\t\t}",
        "\t\t}",
        "\t}",
        "}",
    ]
    out = _process(src)
    text = "\n".join(out)
    # The middle wrapper survives and both ideas stay distinct blocks.
    assert "political_advisor = {" in text
    assert "TAG_advisor_one = {" in text
    assert "TAG_advisor_two = {" in text
    assert text.index("TAG_advisor_one") < text.index("TAG_advisor_two")
    # Recursed and standardized: each child idea's `tag` became `original_tag`.
    assert "original_tag = SOO" in text
    assert "original_tag = NIG" in text
    assert "{ tag = SOO }" not in text
    assert "{ tag = NIG }" not in text
    # Re-processing the output is a no-op (round-trips).
    assert _process(out) == out
