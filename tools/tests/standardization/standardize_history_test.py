"""Tests for the history standardizer.

The transform is documented as lossless: repeated statements (two add_equipment,
two set_country_flag) are semantically meaningful in HOI4 history files and must
all survive. It is also idempotent, and must preserve quoted strings and
comments verbatim.
"""

from standardize_history import (
    HistoryStandardizer,
    _detect_mod_root,
    _load_idea_classification,
    _load_modifier_variables,
    _variable_name,
)


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


# Modeled on real history/countries structure: a dated block with duplicate
# flags, duplicate special projects, a quoted string, and comments.
_HISTORY = """\
capital = 652

2000.1.1 = {
	set_country_flag = TST_alpha
	set_country_flag = TST_alpha
	set_country_flag = TST_beta

	complete_special_project = sp:sp_space_program
	complete_special_project = sp:sp_space_program

	# keep this standalone comment
	create_country_leader = {
		name = "Mark Rutte"
		picture = "gfx_leader_HOL"
	}

	add_equipment_to_stockpile = { type = infantry_equipment_0 amount = 100 } # inline note
	add_equipment_to_stockpile = { type = infantry_equipment_0 amount = 100 }
}
"""


def _standardize(path):
    std = HistoryStandardizer(idea_law=set(), idea_faction=set(), modifier_vars={})
    std.standardize_file(str(path), str(path))
    return path.read_text(encoding="utf-8")


def test_repeated_statements_all_retained(tmp_path):
    src = tmp_path / "hist.txt"
    src.write_text(_HISTORY, encoding="utf-8")
    out = _standardize(src)
    assert out.count("set_country_flag = TST_alpha") == 2
    assert out.count("complete_special_project = sp:sp_space_program") == 2
    assert out.count("add_equipment_to_stockpile") == 2


def test_idempotent(tmp_path):
    src = tmp_path / "hist.txt"
    src.write_text(_HISTORY, encoding="utf-8")
    run1 = _standardize(src)
    run2 = _standardize(src)
    assert run1 == run2


def test_quoted_string_and_comments_preserved(tmp_path):
    src = tmp_path / "hist.txt"
    src.write_text(_HISTORY, encoding="utf-8")
    out = _standardize(src)
    assert 'name = "Mark Rutte"' in out
    assert "# keep this standalone comment" in out
    assert "# inline note" in out


def test_mod_root_search_gives_up_after_twelve_levels(tmp_path):
    deep = tmp_path.joinpath(*[f"level{i}" for i in range(13)])
    deep.mkdir(parents=True)
    assert _detect_mod_root(str(deep)) is None


_ODD_IDEAS = """top_double = { name = top_double } }
ideas = {
\tlaw_category = {
\t\tlaw = yes
\t\tlaw_single = { name = law_single }
\t\tlaw_double = { name = law_double } }
}
}
{
"""

_ODD_MODIFIERS = """TST_modifier = {
\tvalue = TST_modifier_value
}
TST_inline = { value = TST_inline_value }
TST_double = { value = TST_double_value } }
}
{
"""


def test_loaders_skip_unreadable_entries_and_survive_stray_braces(tmp_path):
    root = tmp_path / "mod"
    ideas = root / "common" / "ideas"
    modifiers = root / "common" / "dynamic_modifiers"
    ideas.mkdir(parents=True)
    modifiers.mkdir(parents=True)
    # `*.txt` globs match directories, which cannot be read.
    (ideas / "a_directory.txt").mkdir()
    (modifiers / "a_directory.txt").mkdir()
    _write(ideas / "AA_law_odd.txt", _ODD_IDEAS)
    _write(modifiers / "odd.txt", _ODD_MODIFIERS)

    law, faction = _load_idea_classification(str(root))
    assert law == {"law_single", "law_double"}
    assert faction == set()

    assert _load_modifier_variables(str(root)) == {
        "TST_modifier": {"TST_modifier_value"}
    }


def test_variable_name_reads_both_assignment_shapes():
    assert _variable_name(["set_variable = { var = TST_x value = 1 }"]) == "TST_x"
    assert _variable_name(["set_variable = { TST_y = 1 }"]) == "TST_y"
    assert _variable_name(["set_variable = { }"]) is None


_ROUTING_HISTORY = [
    "2000.1.1 = {\n",
    "\t# above the ideas\n",
    "\tadd_ideas = {\n",
    "\t\t# inside the ideas\n",
    "\t\tTST_country_idea\n",
    "\t}\n",
    "\tadd_dynamic_modifier = { modifier = TST_modifier }\n",
    "\tadd_dynamic_modifier = { modifier = TST_modifier }\n",
    "\tif = { limit = { has_dlc = yes } create_equipment_variant = { type = airframe } }\n",
    "\trandom = { chance = 50 add_stability = 0.01 }\n",
    "\t# trailing note with nothing after it\n",
    "}\n",
]


def test_statement_routing_and_comment_retention():
    standardizer = HistoryStandardizer(
        idea_law=set(), idea_faction=set(), modifier_vars={}
    )
    out = standardizer.format_block(standardizer.extract_properties(_ROUTING_HISTORY))
    # The second add_dynamic_modifier is folded into the first slot, so only one
    # is emitted.
    assert out == [
        "2000.1.1 = {",
        "",
        "\tadd_ideas = {",
        "\t# above the ideas",
        "\t\t# inside the ideas",
        "\t\t# Country Content",
        "\t\tTST_country_idea",
        "\t}",
        "",
        "\t# Dynamic Modifiers",
        "\tadd_dynamic_modifier = { modifier = TST_modifier }",
        "",
        "\t# Air Force Equipment",
        "\tif = { limit = { has_dlc = yes } create_equipment_variant = { type = airframe } }",
        "",
        "\t# Other",
        "\trandom = { chance = 50 add_stability = 0.01 }",
        "\t# trailing note with nothing after it",
        "}",
    ]
