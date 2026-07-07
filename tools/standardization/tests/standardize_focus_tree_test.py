"""Tests for the focus standardizer's handling of will_lead_to_war_with.

A focus may declare war on several targets, so will_lead_to_war_with can appear
multiple times. The standardizer must preserve every occurrence, in order.
"""

from standardize_focus_tree import extract_focus_properties, format_focus_block


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
