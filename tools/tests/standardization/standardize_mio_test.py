"""Tests for the MIO standardizer.

Regression: a trait `parent = { traits = { A B } }` wraps a nested block. The
token-list normalizer used to flatten its inner `=`/`{`/`}` into stray tokens,
which reformatted differently on a second run (non-idempotent). The standardizer
must leave nested blocks intact and produce run2 == run1 exactly.
"""

import sys

import standardize_mio
from standardize_mio import MIOStandardizer

# A realistic organization block with a trait whose `parent` wraps a nested
# `traits = { ... }` block (the non-idempotency trigger).
_MIO = """\
TST_utility_vehicle_manufacturer = {
	allowed = { original_tag = TST }
	name = TST_utility_vehicle_manufacturer
	icon = GFX_idea_generic_manufacturer

	research_categories = {
		armor
	}

	trait = {
		token = TST_ya126_heritage
		name = TST_ya126_heritage
		icon = GFX_generic_mio_trait_icon_reliability

		position = { x = 0 y = 0 }

		equipment_bonus = { reliability = 0.05 }

		on_complete = { expenditure_for_mio_upgrade = yes }

		ai_will_do = { base = 1 }
	}

	trait = {
		token = TST_field_reliability
		name = TST_field_reliability
		icon = GFX_generic_mio_trait_icon_reliability

		parent = { traits = { TST_multifuel_engine TST_hdrive_traction } }
		relative_position_id = TST_ya126_heritage
		position = { x = 0 y = 2 }

		equipment_bonus = { reliability = 0.05 }

		on_complete = { expenditure_for_mio_upgrade = yes }

		ai_will_do = { base = 1 }
	}
}
"""


def _standardize(path):
    std = MIOStandardizer()
    std.standardize_file(str(path), str(path))
    return path.read_text(encoding="utf-8")


def test_nested_parent_block_idempotent(tmp_path):
    src = tmp_path / "mio.txt"
    src.write_text(_MIO, encoding="utf-8")
    run1 = _standardize(src)
    run2 = _standardize(src)
    assert run1 == run2


def test_nested_parent_block_content_preserved(tmp_path):
    src = tmp_path / "mio.txt"
    src.write_text(_MIO, encoding="utf-8")
    out = _standardize(src)
    # The nested block survives intact, not flattened into stray `=`/`{`/`}` tokens.
    assert "parent = { traits = { TST_multifuel_engine TST_hdrive_traction } }" in out
    assert out.count("token = TST_ya126_heritage") == 1
    assert out.count("token = TST_field_reliability") == 1
    # No line degenerates to a lone `=` (the old flattening symptom).
    assert not any(line.strip() == "=" for line in out.splitlines())


def _format(source_lines):
    standardizer = MIOStandardizer()
    return standardizer.format_block(standardizer.extract_properties(source_lines))


def test_sparse_org_needs_no_leading_blank_and_keeps_stray_lines():
    assert _format(
        [
            "TST_org = {\n",
            "\ttask_capacity = 3\n",
            "\tfixed_something = yes\n",
            "}\n",
        ]
    ) == [
        "TST_org = {",
        "\ttask_capacity = 3",
        "",
        "\tfixed_something = yes",
        "}",
    ]


def test_repeated_token_list_blocks_are_blank_separated():
    assert _format(
        [
            "TST_org = {\n",
            "\tequipment_type = { infantry_weapons }\n",
            "\tequipment_type = { artillery }\n",
            "}\n",
        ]
    ) == [
        "TST_org = {",
        "\tequipment_type = { infantry_weapons }",
        "",
        "\tequipment_type = { artillery }",
        "}",
    ]


def test_format_nested_block_skips_blanks_and_realigns_stacked_closers():
    assert MIOStandardizer().format_nested_block(
        ["available = {", "", "\tOR = {", "\t\thas_war = no", "} }"], "\t"
    ) == ["\tavailable = {", "\t\tOR = {", "\t\t\thas_war = no", "\t} }"]


def test_normalize_on_complete_leaves_unrelated_blocks_alone():
    standardizer = MIOStandardizer()
    foreign = ["ai_will_do = { base = 1 }"]
    assert standardizer.normalize_on_complete(foreign) == foreign
    plain = ["on_complete = { add_political_power = 1 }"]
    assert standardizer.normalize_on_complete(plain) == plain


def test_normalize_on_complete_drops_pick_grants_and_keeps_the_rest():
    block = [
        "\t\ton_complete = {",
        "",
        "\t\t\texpenditure_for_mio_upgrade = yes",
        "\t\t\tadd_political_power = 1",
        "\t\t\tif = {",
        "\t\t\t\tlimit = { has_war = no }",
        "\t\t\t\tfree_trait_picks = 1",
        "\t\t\t}",
        "\t\t\thidden_effect = {",
        "",
        "\t\t\t\tset_country_flag = TST_done",
        "\t\t\t}",
        "\t\t}",
    ]
    assert MIOStandardizer().normalize_on_complete(block) == [
        "\t\ton_complete = {",
        "\t\t\tadd_political_power = 1",
        "\t\t\thidden_effect = {",
        "\t\t\t\tset_country_flag = TST_done",
        "\t\t\t}",
        "\t\t\texpenditure_for_mio_upgrade = yes",
        "\t\t}",
    ]


def test_token_list_reads_a_brace_on_the_next_line():
    assert MIOStandardizer()._normalize_token_list(
        ["equipment_type =", "{", "\tinfantry_weapons", "\tartillery", "}"],
        "equipment_type",
        "\t",
    ) == ["\tequipment_type = {", "\t\tinfantry_weapons", "\t\tartillery", "\t}"]


def test_token_list_of_an_empty_block_is_empty():
    assert MIOStandardizer()._normalize_token_list([], "equipment_type", "\t") == []


def test_modifier_block_falls_back_to_verbatim_compaction():
    standardizer = MIOStandardizer()
    assert standardizer._normalize_modifier_block(
        ["ai_will_do = {", "\tbase = 1", "}"], "equipment_bonus", "\t"
    ) == ["ai_will_do = {", "\tbase = 1", "}"]
    assert standardizer._normalize_modifier_block(
        ["equipment_bonus = { }"], "equipment_bonus", "\t"
    ) == ["equipment_bonus = { }"]
    # A comparison operator is not a `stat = value` pair, so nothing is rebuilt.
    assert standardizer._normalize_modifier_block(
        ["equipment_bonus = { reliability > 0.1 }"], "equipment_bonus", "\t"
    ) == ["equipment_bonus = { reliability > 0.1 }"]


def test_modifier_block_with_a_nested_block_is_collapsed_not_flattened():
    assert MIOStandardizer()._normalize_modifier_block(
        ["equipment_bonus = {", "\tinstant = { reliability = 0.1 }", "}"],
        "equipment_bonus",
        "\t",
    ) == ["\tequipment_bonus = { instant = { reliability = 0.1 } }"]


def test_modifier_merge_skips_empty_blocks():
    assert MIOStandardizer()._merge_and_normalize_modifier_blocks(
        [["equipment_bonus = { }"], ["equipment_bonus = { armor = 0.2 }"]],
        "equipment_bonus",
        "\t",
    ) == ["\tequipment_bonus = { armor = 0.2 }"]


def test_modifier_merge_of_only_empty_blocks_keeps_the_first():
    assert MIOStandardizer()._merge_and_normalize_modifier_blocks(
        [["equipment_bonus = { }"], ["equipment_bonus = { }"]],
        "equipment_bonus",
        "\t",
    ) == ["equipment_bonus = { }"]


def test_modifier_merge_bails_per_block_when_a_block_is_opaque():
    standardizer = MIOStandardizer()
    good = ["equipment_bonus = { armor = 0.2 }"]
    cases = (
        ["equipment_bonus = {", "\t# keep this note", "\treliability = 0.1", "}"],
        ["ai_will_do = { base = 1 }"],
        ["equipment_bonus = { instant = { reliability = 0.1 } }"],
        ["equipment_bonus = { reliability = }"],
        ["equipment_bonus = { reliability > 0.1 }"],
    )
    for opaque in cases:
        merged = standardizer._merge_and_normalize_modifier_blocks(
            [opaque, good], "equipment_bonus", "\t"
        )
        # Fallback emits both blocks separately instead of one merged block.
        assert merged[-1] == "\tequipment_bonus = { armor = 0.2 }"
        assert len(merged) > 1


def test_format_trait_block_boundaries():
    standardizer = MIOStandardizer()
    assert standardizer.format_trait_block([]) == []
    assert standardizer.format_trait_block(
        [
            "\ttrait = {",
            "\t\ttoken = TST_trait",
            "\t\ticon = {",
            "\t\t\ttexture = GFX_trait",
            "\t\t}",
            "\t\tparent = TST_parent",
            "\t}",
        ]
    ) == [
        "\ttrait = {",
        "\t\ttoken = TST_trait",
        "\t\ticon = {",
        "\t\t\ttexture = GFX_trait",
        "\t\t}",
        "",
        "\t\tparent = TST_parent",
        "\t}",
    ]


def test_compact_allowed_block_boundaries():
    standardizer = MIOStandardizer()
    assert standardizer.compact_allowed_block([]) == "\tallowed = { }"
    assert standardizer.compact_allowed_block(["allowed = original_tag"]) == (
        "\tallowed = { }"
    )


def test_add_comments_skips_blank_lines():
    lines = []
    MIOStandardizer()._add_comments(lines, ["\t# note\n", "  \n"])
    assert lines == ["\t# note"]


def test_clean_blank_lines_collapses_runs():
    assert MIOStandardizer()._clean_blank_lines(["a", "", "", "b"]) == ["a", "", "b"]


def test_main_standardizes_the_named_file(tmp_path, monkeypatch):
    source = tmp_path / "mio.txt"
    output = tmp_path / "out.txt"
    with open(source, "w", encoding="utf-8", newline="") as handle:
        handle.write(_MIO)
    monkeypatch.setattr(
        sys, "argv", ["standardize_mio.py", str(source), "-o", str(output)]
    )

    standardize_mio.main()

    with open(output, "r", encoding="utf-8", newline="") as handle:
        assert "allowed = { original_tag = TST }" in handle.read()
