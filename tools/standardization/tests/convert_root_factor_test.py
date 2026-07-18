"""Tests for convert_root_factor_to_base.

MD convention is ``base`` at the root of ai_will_do; ``factor`` is only valid
inside ``modifier`` children. The helper renames root factor to base without
touching modifier factors, and backs off when a root base already exists.
"""

from shared_utils import convert_root_factor_to_base
from standardize_focus_tree import extract_focus_properties, format_focus_block


def test_multiline_root_factor_converted():
    block = [
        "\t\tai_will_do = {",
        "\t\t\tfactor = 5",
        "\t\t}",
    ]
    assert convert_root_factor_to_base(block) == [
        "\t\tai_will_do = {",
        "\t\t\tbase = 5",
        "\t\t}",
    ]


def test_singleline_root_factor_converted():
    block = ["\t\tai_will_do = { factor = 1 }"]
    assert convert_root_factor_to_base(block) == ["\t\tai_will_do = { base = 1 }"]


def test_modifier_factor_untouched():
    block = [
        "\t\tai_will_do = {",
        "\t\t\tfactor = 10",
        "\t\t\tmodifier = {",
        "\t\t\t\tfactor = 0",
        "\t\t\t\thas_active_mission = bankruptcy_incoming_collapse",
        "\t\t\t}",
        "\t\t\tmodifier = { factor = 2 has_war = yes }",
        "\t\t}",
    ]
    out = convert_root_factor_to_base(block)
    assert out[1] == "\t\t\tbase = 10"
    assert out[3] == "\t\t\t\tfactor = 0"
    assert out[6] == "\t\t\tmodifier = { factor = 2 has_war = yes }"


def test_existing_root_base_leaves_factor_alone():
    block = [
        "\t\tai_will_do = {",
        "\t\t\tbase = 3",
        "\t\t\tfactor = 2",
        "\t\t}",
    ]
    assert convert_root_factor_to_base(block) == block


def test_root_base_only_unchanged():
    block = ["\t\tai_will_do = { base = 1 }"]
    assert convert_root_factor_to_base(block) == block


def test_focus_emission_converts_root_factor():
    props = extract_focus_properties(
        [
            "\tfocus = {\n",
            "\t\tid = TST_reform\n",
            "\t\tai_will_do = {\n",
            "\t\t\tfactor = 1\n",
            "\t\t}\n",
            "\t}\n",
        ]
    )
    out = format_focus_block(props)
    ai_lines = [l.strip() for l in out if "ai_will_do" in l or "base" in l]
    assert "ai_will_do = { base = 1 }" in ai_lines
    assert not any("factor" in l for l in out)
