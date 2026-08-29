"""Tests for the focus standardizer's block formatting.

A focus may declare war on several targets, so will_lead_to_war_with can appear
multiple times. The standardizer must preserve every occurrence, in order.
Log injection must also survive an id line carrying a trailing comment.
"""

import standardize_focus_tree as focus_tree_module
from shared_utils import strip_inline_comment
from standardize_focus_tree import (
    extract_focus_properties,
    format_focus_block,
    reindent_by_brace_depth,
    standardize_focus_tree,
    validate_modifier_naming,
)


def _code_braces_balanced(lines):
    code = "\n".join(strip_inline_comment(line) for line in lines)
    return code.count("{") == code.count("}")


def _focus_with_war_targets(targets):
    lines = ["\tfocus = {\n", "\t\tid = TST_invade\n", "\n"]
    for tag in targets:
        lines.append(f"\t\twill_lead_to_war_with = {tag}\n")
    lines.append("\t}\n")
    return lines


def test_single_war_target_preserved():
    props = extract_focus_properties(_focus_with_war_targets(["MOR"]))
    assert props["will_lead_to_war_with"] == ["will_lead_to_war_with = MOR"]


def test_multiple_war_targets_all_preserved_in_order():
    props = extract_focus_properties(_focus_with_war_targets(["MOR", "TUN", "LBA"]))
    assert props["will_lead_to_war_with"] == [
        "will_lead_to_war_with = MOR",
        "will_lead_to_war_with = TUN",
        "will_lead_to_war_with = LBA",
    ]


def test_every_empty_commented_placeholder_is_dropped():
    # The stylization guide's example focus writes these as slot markers; the
    # formatter drops all of them rather than keeping some and re-sorting them.
    placeholders = (
        "allow_branch",
        "available",
        "bypass",
        "bypass_effect",
        "cancel",
        "mutually_exclusive",
        "visible",
    )
    lines = ["\tfocus = {\n", "\t\tid = TST_slots\n"]
    lines.extend(f"\t\t# {name} = {{ }}\n" for name in placeholders)
    lines.append("\t}\n")
    out = format_focus_block(extract_focus_properties(lines))
    assert not [line for line in out if "#" in line]


def test_no_war_target():
    props = extract_focus_properties(["\tfocus = {\n", "\t\tid = TST_peace\n", "\t}\n"])
    assert props["will_lead_to_war_with"] == []


def test_round_trip_emits_one_line_per_target():
    props = extract_focus_properties(_focus_with_war_targets(["MOR", "TUN"]))
    out = format_focus_block(props)
    war_lines = [l.strip() for l in out if "will_lead_to_war_with" in l]
    assert war_lines == [
        "will_lead_to_war_with = MOR",
        "will_lead_to_war_with = TUN",
    ]
    # Re-parsing the emitted block yields the same two targets (idempotent).
    reparsed = extract_focus_properties([l + "\n" for l in out])
    assert reparsed["will_lead_to_war_with"] == [
        "will_lead_to_war_with = MOR",
        "will_lead_to_war_with = TUN",
    ]


def test_comments_stay_with_repeated_property_entries():
    lines = [
        "\tfocus = {\n",
        "\t\tid = TST_repeated\n",
        "\t\ticon = first_icon\n",
        "\t\t# second icon\n",
        "\t\ticon = second_icon\n",
        "\t\tx = 0\n",
        "\t\ty = 0\n",
        "\t\toffset = { x = 1 }\n",
        "\t\t# second offset\n",
        "\t\toffset = { x = 2 }\n",
        "\t\tcost = 5\n",
        "\t\tprerequisite = { focus = TST_first }\n",
        "\t\t# second prerequisite\n",
        "\t\tprerequisite = { focus = TST_second }\n",
        "\t\tmutually_exclusive = { focus = TST_third }\n",
        "\t\t# second mutually exclusive\n",
        "\t\tmutually_exclusive = { focus = TST_fourth }\n",
        "\t\twill_lead_to_war_with = MOR\n",
        "\t\t# second war target\n",
        "\t\twill_lead_to_war_with = TUN\n",
        "\t}\n",
    ]

    out = format_focus_block(extract_focus_properties(lines))
    expected_properties = {
        "second icon": "icon = second_icon",
        "second offset": "offset = { x = 2 }",
        "second prerequisite": "prerequisite = { focus = TST_second }",
        "second mutually exclusive": "mutually_exclusive = { focus = TST_fourth }",
        "second war target": "will_lead_to_war_with = TUN",
    }
    for comment, property_line in expected_properties.items():
        comment_index = next(i for i, line in enumerate(out) if comment in line)
        assert out[comment_index + 1].strip() == property_line

    assert (
        format_focus_block(extract_focus_properties([f"{line}\n" for line in out]))
        == out
    )


def _focus_with_offset(trigger_lines):
    lines = [
        "\tfocus = {\n",
        "\t\tid = TST_joint\n",
        "\n",
        "\t\tx = 86\n",
        "\t\ty = 10\n",
        "\t\toffset = {\n",
        "\t\t\tx = -70\n",
        "\t\t\ty = -10\n",
    ]
    lines.extend(trigger_lines)
    lines.append("\t\t}\n")
    lines.append("\t}\n")
    return lines


def test_offset_single_line_trigger_preserved():
    # A single-line offset trigger must keep its contents (regression: the old
    # reindent sliced [1:-1] and emitted an empty `trigger = { }`).
    props = extract_focus_properties(
        _focus_with_offset(["\t\t\ttrigger = { original_tag = NKO }\n"])
    )
    out = format_focus_block(props)
    offset_lines = [l.strip() for l in out if "trigger" in l]
    assert offset_lines == ["trigger = { original_tag = NKO }"]


def test_single_line_offset_block_contents_preserved():
    # The property loops read block_lines[1:-1], which is empty for a one-line
    # block — the whole offset used to be emitted as `offset = { }`.
    props = extract_focus_properties(
        [
            "\tfocus = {\n",
            "\t\tid = TST_joint\n",
            "\t\toffset = { trigger = { original_tag = HOL } x = 70 }\n",
            "\t}\n",
        ]
    )
    out = format_focus_block(props)
    assert "\t\toffset = { trigger = { original_tag = HOL } x = 70 }" in out
    assert _code_braces_balanced(out)


def test_offset_multi_line_trigger_preserved():
    props = extract_focus_properties(
        _focus_with_offset(
            [
                "\t\t\ttrigger = {\n",
                "\t\t\t\toriginal_tag = NKO\n",
                "\t\t\t\thas_war = no\n",
                "\t\t\t}\n",
            ]
        )
    )
    out = format_focus_block(props)
    body = "\n".join(out)
    assert "original_tag = NKO" in body
    assert "has_war = no" in body


def test_duplicate_available_blocks_merged_not_dropped():
    props = extract_focus_properties(
        [
            "\tfocus = {\n",
            "\t\tid = TST_gated\n",
            "\t\tavailable = {\n",
            "\t\t\tNOT = { has_government = communism }\n",
            "\t\t}\n",
            "\t\tavailable = {\n",
            "\t\t\thas_country_flag = TST_flag\n",
            "\t\t}\n",
            "\t}\n",
        ]
    )
    inner = [l.strip() for l in props["available"] if l.strip() not in ("", "}")]
    assert "NOT = { has_government = communism }" in " ".join(inner)
    assert "has_country_flag = TST_flag" in " ".join(inner)
    out = format_focus_block(props)
    assert sum(1 for l in out if l.strip().startswith("available")) == 1


def test_duplicate_single_line_available_blocks_merged():
    props = extract_focus_properties(
        [
            "\tfocus = {\n",
            "\t\tid = TST_gated\n",
            "\t\tavailable = { has_country_flag = TST_a }\n",
            "\t\tavailable = { has_country_flag = TST_b }\n",
            "\t}\n",
        ]
    )
    out = format_focus_block(props)
    assert sum(1 for l in out if l.strip().startswith("available")) == 1
    body = "\n".join(out)
    assert "has_country_flag = TST_a" in body
    assert "has_country_flag = TST_b" in body
    assert _code_braces_balanced(out)


def test_duplicate_single_line_blocks_with_comment_braces_not_merged():
    # A `}` inside a trailing comment must not be mistaken for the block's
    # closing brace — merging is skipped and both blocks survive verbatim.
    props = extract_focus_properties(
        [
            "\tfocus = {\n",
            "\t\tid = TST_gated\n",
            "\t\tavailable = { has_country_flag = TST_a } # old: checked { something } here\n",
            "\t\tavailable = { has_country_flag = TST_b }\n",
            "\t}\n",
        ]
    )
    out = format_focus_block(props)
    assert _code_braces_balanced(out)
    assert sum(1 for l in out if l.strip().startswith("available")) == 2
    assert (
        "\t\tavailable = { has_country_flag = TST_a } # old: checked { something } here"
        in out
    )


def test_single_line_effect_blocks_with_trailing_comments_get_log():
    cases = (
        ("completion_reward", "# reward note"),
        ("select_effect", "# was { 100 }"),
        ("bypass_effect", "# old }"),
    )
    for block_name, comment in cases:
        props = extract_focus_properties(
            [
                "\tfocus = {\n",
                "\t\tid = TST_reward\n",
                f"\t\t{block_name} = {{ add_political_power = 50 }} {comment}\n",
                "\t}\n",
            ]
        )
        out = format_focus_block(props)
        assert _code_braces_balanced(out)
        block_start = next(
            i for i, line in enumerate(out) if line.strip().startswith(block_name)
        )
        assert out[block_start].strip() == f"{block_name} = {{"
        assert out[block_start + 1].strip() == (
            'log = "[GetDateText]: [Root.GetName]: Focus TST_reward"'
        )
        assert out[block_start + 2].strip() == "add_political_power = 50"
        assert out[block_start + 3].strip() == f"}} {comment}"


def test_single_line_effect_block_gets_log_inside_braces():
    props = extract_focus_properties(
        [
            "\tfocus = {\n",
            "\t\tid = TST_reward\n",
            "\t\tcompletion_reward = { add_political_power = 50 }\n",
            "\t}\n",
        ]
    )
    out = format_focus_block(props)
    assert _code_braces_balanced(out)
    reward_start = next(
        i for i, l in enumerate(out) if l.strip().startswith("completion_reward")
    )
    assert out[reward_start].strip() == "completion_reward = {"
    assert out[reward_start + 1].strip() == (
        'log = "[GetDateText]: [Root.GetName]: Focus TST_reward"'
    )
    assert out[reward_start + 2].strip() == "add_political_power = 50"
    assert out[reward_start + 3].strip() == "}"


def test_hyphenated_focus_id_log_corrected():
    props = extract_focus_properties(
        [
            "\tfocus = {\n",
            "\t\tid = TST_austria-este\n",
            "\t\tcompletion_reward = {\n",
            '\t\t\tlog = "[GetDateText]: [Root.GetName]: TST_Austria-este"\n',
            "\t\t}\n",
            "\t}\n",
        ]
    )
    out = format_focus_block(props)
    log_lines = [l for l in out if "log =" in l]
    assert len(log_lines) == 1
    assert '[Root.GetName]: Focus TST_austria-este"' in log_lines[0]


def test_id_line_comment_kept_out_of_log():
    props = extract_focus_properties(
        [
            "\tfocus = {\n",
            "\t\tid = TST_coup #Infiltrate Lebanon\n",
            "\t\tcompletion_reward = {\n",
            "\t\t\tadd_political_power = 50\n",
            "\t\t}\n",
            "\t}\n",
        ]
    )
    out = format_focus_block(props)
    log_lines = [l.strip() for l in out if "log =" in l]
    assert log_lines == ['log = "[GetDateText]: [Root.GetName]: Focus TST_coup"']


def test_comment_brace_does_not_shift_indent():
    # A brace inside a comment must not count toward brace depth during reindent,
    # or every line after it is pushed one level too deep.
    block = [
        "shared_focus = {",
        "id = TST_x",
        "completion_reward = {",
        "# TODO fix { this unbalanced brace",
        "add_political_power = 10",
        "}",
        "ai_will_do = { base = 1 }",
        "}",
    ]
    out = reindent_by_brace_depth(block)
    by_text = {line.strip(): line for line in out}
    # Statement after the comment stays inside completion_reward (two tabs), and
    # the closing brace returns to one tab — not shifted by the comment's `{`.
    assert by_text["add_political_power = 10"] == "\t\tadd_political_power = 10"
    assert by_text["# TODO fix { this unbalanced brace"].startswith("\t\t#")
    assert out[-1] == "}"
    assert out[-2] == "\tai_will_do = { base = 1 }"
    # Overall brace balance is preserved across the emitted code (comments,
    # which may carry an unbalanced brace, are excluded from the count).
    code = "\n".join(line.split("#", 1)[0] for line in out)
    assert code.count("{") == code.count("}")


def test_country_modifier_names_must_be_snake_case():
    for block_type in ("focus", "shared_focus", "joint_focus"):
        valid = [
            f"{block_type} = {{\n",
            "\tid = TST_valid\n",
            "\tcustom_effect_tooltip = { MODIFIER = TST_valid_modifier }\n",
            "}\n",
        ]
        invalid = [
            f"{block_type} = {{\n",
            "\tid = TST_invalid\n",
            "\tcustom_effect_tooltip = { MODIFIER = TST_Invalid_modifier }\n",
            "}\n",
        ]

        assert validate_modifier_naming(valid, "valid.txt") == 0
        assert validate_modifier_naming(invalid, "invalid.txt") == 1


def test_shared_modifier_second_tag_segment_is_valid():
    """CHI_NKO_shared_modifier — a joint modifier carries a second uppercase tag."""
    lines = [
        "focus = {\n",
        "\tid = TST_joint_modifier\n",
        "\tcustom_effect_tooltip = { MODIFIER = CHI_NKO_shared_modifier }\n",
        "}\n",
    ]
    assert validate_modifier_naming(lines, "joint.txt") == 0


def test_camel_case_after_second_tag_segment_is_rejected():
    lines = [
        "focus = {\n",
        "\tid = TST_joint_modifier\n",
        "\tcustom_effect_tooltip = { MODIFIER = CHI_NKO_Shared_modifier }\n",
        "}\n",
    ]
    assert validate_modifier_naming(lines, "joint.txt") == 1


def test_modifier_inside_quoted_string_is_ignored():
    lines = [
        "focus = {\n",
        "\tid = TST_quoted\n",
        '\tlog = "MODIFIER = TST_Not_A_Reference"\n',
        "}\n",
    ]
    assert validate_modifier_naming(lines, "quoted.txt") == 0


def test_commented_out_modifier_is_ignored():
    lines = [
        "focus = {\n",
        "\tid = TST_commented\n",
        "\t# custom_effect_tooltip = { MODIFIER = TST_Old_Name }\n",
        "}\n",
    ]
    assert validate_modifier_naming(lines, "commented.txt") == 0


def test_modifier_key_suffix_does_not_substring_match():
    lines = [
        "focus = {\n",
        "\tid = TST_suffix\n",
        "\tCUSTOM_MODIFIER = TST_Not_The_Key\n",
        "}\n",
    ]
    assert validate_modifier_naming(lines, "suffix.txt") == 0


def test_suggested_fix_keeps_second_tag_segment_case(capsys):
    lines = [
        "focus = {\n",
        "\tid = TST_joint\n",
        "\tcustom_effect_tooltip = { MODIFIER = CHI_NKO_Shared_modifier }\n",
        "}\n",
    ]
    assert validate_modifier_naming(lines, "joint.txt") == 1
    assert "CHI_NKO_shared_modifier" in capsys.readouterr().err


def test_reported_focus_id_excludes_trailing_comment(capsys):
    lines = [
        "focus = {\n",
        "\tid = TST_commented #Infiltrate Lebanon\n",
        "\tcustom_effect_tooltip = { MODIFIER = TST_Invalid_modifier }\n",
        "}\n",
    ]
    assert validate_modifier_naming(lines, "commented.txt") == 1
    assert "'TST_commented'" in capsys.readouterr().err


def test_check_naming_disabled_skips_validation():
    lines = [
        "focus = {\n",
        "\tid = TST_invalid\n",
        "\tcustom_effect_tooltip = { MODIFIER = TST_Invalid_modifier }\n",
        "}\n",
    ]
    assert validate_modifier_naming(lines, "invalid.txt", check_naming=False) == 0


def test_shared_and_joint_focuses_are_reindented_at_top_level(tmp_path):
    for block_type in ("shared_focus", "joint_focus"):
        source = tmp_path / f"{block_type}.txt"
        output = tmp_path / f"{block_type}-output.txt"
        source.write_text(
            f"""\t{block_type} = {{
\t\tid = TST_{block_type}
\t\tcompletion_reward = {{
\t\t\tadd_political_power = 1
\t\t}}
\t}}
""",
            encoding="utf-8",
        )

        assert standardize_focus_tree(str(source), str(output)) is True

        lines = output.read_text(encoding="utf-8").splitlines()
        assert lines[0] == f"{block_type} = {{"
        assert f"\tid = TST_{block_type}" in lines
        assert "\t\tadd_political_power = 1" in lines
        assert lines[-1] == "}"


_INVALID_MODIFIER_TREE = """focus_tree = {
\tfocus = {
\t\tid = TST_invalid
\t\tcustom_effect_tooltip = { MODIFIER = TST_Invalid_modifier }
\t}
}
"""


def test_invalid_modifier_name_rejects_standardization_without_writing(tmp_path):
    source = tmp_path / "focus.txt"
    output = tmp_path / "output.txt"
    source.write_text(_INVALID_MODIFIER_TREE, encoding="utf-8")

    assert standardize_focus_tree(str(source), str(output), check_naming=True) is False
    assert not output.exists()


def test_naming_check_is_opt_in(tmp_path):
    source = tmp_path / "focus.txt"
    output = tmp_path / "output.txt"
    source.write_text(_INVALID_MODIFIER_TREE, encoding="utf-8")

    assert standardize_focus_tree(str(source), str(output)) is True
    assert "TST_Invalid_modifier" in output.read_text(encoding="utf-8")


_COMMENTED_FOCUS = [
    "\tfocus = {\n",
    "\t\tid = TST_x\n",
    "\n",
    "\t\tcost = 5\n",
    "\n",
    "\t\tcompletion_reward = {\n",
    '\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus TST_x"\n',
    "\t\t\tadd_political_power = 50\n",
    "\t\t}\n",
    "\n",
    "\t\t# Only the Pan-Thai AI should push for this, so the base stays 0\n",
    "\t\t# for everyone else.\n",
    "\t\tai_will_do = {\n",
    "\t\t\tbase = 0\n",
    "\t\t}\n",
    "\t}\n",
]


def _standardize_focus(lines):
    return format_focus_block(extract_focus_properties(lines))


def test_comment_stays_with_the_block_it_describes():
    # (defect) every unrecognized line landed in `other`, which is emitted before
    # completion_reward — so an ai_will_do comment resurfaced above the reward.
    out = _standardize_focus(_COMMENTED_FOCUS)
    comment_idx = next(i for i, ln in enumerate(out) if "Pan-Thai AI" in ln)
    ai_idx = next(i for i, ln in enumerate(out) if ln.strip().startswith("ai_will_do"))
    reward_idx = next(
        i for i, ln in enumerate(out) if ln.strip().startswith("completion_reward")
    )
    assert reward_idx < comment_idx < ai_idx


def test_wrapped_comment_lines_stay_adjacent():
    # (defect) `other` kept the raw source line including its trailing newline;
    # the writer then appends another, splitting a wrapped comment with a blank.
    out = _standardize_focus(_COMMENTED_FOCUS)
    assert not any("\n" in line for line in out)
    first = next(i for i, ln in enumerate(out) if "Pan-Thai AI" in ln)
    assert out[first + 1].strip() == "# for everyone else."


def test_commented_focus_standardization_idempotent():
    once = _standardize_focus(_COMMENTED_FOCUS)
    twice = _standardize_focus([f"{line}\n" for line in once])
    assert once == twice


_TWO_COMMENTED_OTHERS = [
    "\tfocus = {\n",
    "\t\tid = TST_x\n",
    "\t\t# first\n",
    "\t\tdynamic = yes\n",
    "\t\t# second\n",
    "\t\tbypass_if_unavailable = yes\n",
    "\t}\n",
]


def test_each_other_property_keeps_its_own_comment():
    # (defect) `other` claimed comments into one unindexed bucket, so both
    # comments were emitted above the first property.
    out = _standardize_focus(_TWO_COMMENTED_OTHERS)
    expected = {"# first": "dynamic = yes", "# second": "bypass_if_unavailable = yes"}
    for comment, property_line in expected.items():
        idx = out.index(f"\t\t{comment}")
        assert out[idx + 1].strip() == property_line

    assert _standardize_focus([f"{line}\n" for line in out]) == out


_SPARSE_FOCUS = [
    "\tfocus = {\n",
    "\t\tid = TST_sparse\n",
    "\t\ticon = GFX_goal_generic_demand_territory\n",
    "\t\tcost = 5\n",
    "\t\tai_will_do = { base = 1 }\n",
    "\t}\n",
]


def test_absent_property_costs_no_blank_line():
    # (defect) the position and cost separators were emitted unconditionally, so
    # a focus with no x/y still paid a blank line for the group it never had.
    out = _standardize_focus(_SPARSE_FOCUS)
    assert out == [
        "\tfocus = {",
        "\t\tid = TST_sparse",
        "\t\ticon = GFX_goal_generic_demand_territory",
        "",
        "\t\tcost = 5",
        "",
        "\t\tai_will_do = { base = 1 }",
        "\t}",
    ]


def test_no_blank_line_before_closing_brace():
    out = _standardize_focus(_COMMENTED_FOCUS)
    assert out[-1] == "\t}"
    assert out[-2].strip() != ""


def test_sparse_focus_idempotent():
    once = _standardize_focus(_SPARSE_FOCUS)
    assert _standardize_focus([f"{line}\n" for line in once]) == once


def test_failed_write_leaves_original_intact_and_no_temp_file(tmp_path, monkeypatch):
    target = tmp_path / "focus.txt"
    original = "focus_tree = {\n\tfocus = {\n\t\tid = TST_x\n\t}\n}\n"
    target.write_text(original, encoding="utf-8")

    def _boom(_path, _text):
        raise OSError("disk full")

    monkeypatch.setattr(focus_tree_module, "atomic_write_text", _boom)

    assert standardize_focus_tree(str(target), str(target)) is False
    assert target.read_text(encoding="utf-8") == original
    assert not (tmp_path / "focus.txt.tmp").exists()
