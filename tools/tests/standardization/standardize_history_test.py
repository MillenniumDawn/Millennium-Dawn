"""Tests for the history standardizer.

The transform is documented as lossless: repeated statements (two add_equipment,
two set_country_flag) are semantically meaningful in HOI4 history files and must
all survive. It is also idempotent, and must preserve quoted strings and
comments verbatim.
"""

import pytest
import standardize_history as history
from shared.suite import read_text as _read
from shared.suite import write_text as _write
from standardize_history import (
    HistoryStandardizer,
    _detect_mod_root,
    _load_idea_classification,
    _load_modifier_variables,
    _variable_name,
)

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


_INFLUENCE_SETUP = """\
	# Influence system
	init_influence = yes
	set_variable = { domestic_influence_amount = 200 }
	add_to_array = { influence_array = CHI.id }
	add_to_array = { influence_array_val = 99 }
	add_to_array = {
		influence_array = USA.id
	}
	add_to_array = { influence_array_val = 40 }
	sort_influence = yes
"""
_INFLUENCE_HISTORY = (
    "capital = 652\n\n2000.1.1 = {\n"
    "\tset_country_flag = TST_alpha\n" + _INFLUENCE_SETUP + "}\n"
)
_POLITICS_HISTORY = (
    "capital = 652\n\n2000.1.1 = {\n"
    "\tstart_politics_input = yes\n"
    "\tset_variable = { party_pop_array^0 = 0.5 }\n"
    "\tset_variable = { ruling_party = 0 }\n"
    "\tstartup_politics = yes\n"
    "}\n"
)
_IDEMPOTENT_CASES = {
    "repeated statements": _HISTORY,
    "influence": _INFLUENCE_HISTORY,
    "politics": _POLITICS_HISTORY,
}


def test_influence_setup_order_preserved(tmp_path):
    src = tmp_path / "hist.txt"
    _write(src, _INFLUENCE_HISTORY)
    out = _standardize(src)
    assert _INFLUENCE_SETUP in out


def test_startup_politics_runs_after_the_party_setup_it_reads(tmp_path):
    # Issue #6247: it was hoisted above party_pop_array and ruling_party.
    src = tmp_path / "hist.txt"
    _write(src, _POLITICS_HISTORY)
    out = _standardize(src)
    assert (
        out.index("start_politics_input")
        < out.index("party_pop_array^0")
        < out.index("ruling_party = 0")
        < out.index("startup_politics")
    )


@pytest.mark.parametrize("history", _IDEMPOTENT_CASES.values(), ids=_IDEMPOTENT_CASES)
def test_idempotent(tmp_path, history):
    src = tmp_path / "hist.txt"
    _write(src, history)
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


_COUNTRY = """capital = 652
2000.1.1 = {
\t# Set Ideas
\tadd_ideas = {
\t\tlaw_income
\t\tmd_example
\t\tfaction_support
\t\tTST_country
\t\tmd_example
\t}
\tadd_dynamic_modifier = { modifier = TST_modifier }
\tset_variable = { var = TST_modifier_value value = 1 }
\tset_variable = { var = global_unclaimed value = 2 }
\tset_variable = { var = TST_country_value value = 3 }
\tadd_to_array = { array = global_array value = TST_country }
\tcomplete_special_project = sp:sp_space_program
\tset_technology = { infantry_weapons = 1 }
\tif = { limit = { has_dlc = yes } set_technology = { armor = 1 } }
\tcreate_equipment_variant = { type = infantry_equipment_0 }
\tcreate_equipment_variant = { type = airframe }
\tcreate_equipment_variant = { type = destroyer_hull }
\tset_oob = TST_army
\tset_air_oob = TST_air
\tset_naval_oob = TST_navy
\tstart_politics_input = { }
\tstartup_politics = { }
\tcreate_country_leader = { name = TST_leader }
\tset_popularities = { democratic = 0.5 }
\tset_politics = { ruling_party = democratic }
\tadd_opinion_modifier = { target = USA modifier = good }
\treverse_add_opinion_modifier = { target = USA modifier = bad }
\tset_power_balance = { id = TST_balance }
\t652 = { buildings = { infrastructure = 1 } }
\tset_country_flag = TST_started
\tclr_country_flag = TST_old
\tother_statement = yes
}
"""


def _mod(tmp_path):
    """A mod root with law and faction ideas, a dynamic modifier and one country."""
    root = tmp_path / "mod"
    _write(
        root / "common/ideas/AA_law_test.txt",
        "ideas = {\n\tlaw_category = {\n\t\tlaw = yes\n"
        "\t\tlaw_income = {\n\t\t\tname = law_income\n\t\t}\n\t}\n}\n",
    )
    _write(
        root / "common/ideas/factions.txt",
        "ideas = {\n\tinternal_factions = {\n"
        "\t\tfaction_support = {\n\t\t\tname = faction_support\n\t\t}\n\t}\n"
        "\tmd_category = {\n\t\tmd_example = {\n\t\t\tname = md_example\n\t\t}\n\t}\n}\n",
    )
    _write(
        root / "common/dynamic_modifiers/modifiers.txt",
        "TST_modifier = {\n\ticon = x\n\tvalue = TST_modifier_value\n"
        "\tnested = {\n\t\tfield = TST_nested_value\n\t}\n}\n",
    )
    return root, _write(root / "history/countries/TST.txt", _COUNTRY)


def test_mod_root_is_found_from_a_country_file(tmp_path):
    root, country = _mod(tmp_path)
    assert _detect_mod_root(str(country)) == str(root)
    assert history._iter_file_lines(str(root / "missing.txt")) is None


def test_loaders_classify_ideas_and_collect_modifier_variables(tmp_path):
    history._IDEA_CACHE.clear()
    history._MODIFIER_CACHE.clear()
    root, _country = _mod(tmp_path)
    law, factions = _load_idea_classification(str(root))
    assert "law_income" in law
    assert "faction_support" in factions
    assert _load_modifier_variables(str(root))["TST_modifier"] >= {
        "TST_modifier_value",
        "TST_nested_value",
    }


def test_a_country_file_is_grouped_by_statement_kind_and_idempotent(tmp_path):
    history._IDEA_CACHE.clear()
    history._MODIFIER_CACHE.clear()
    root, country = _mod(tmp_path)
    standardizer = HistoryStandardizer(mod_root=str(root))
    block = history.extract_block(_read(country).splitlines(keepends=True), 1)[0]
    assert standardizer.extract_properties(block)["ideas"]
    standardizer._ensure_classification(str(country))
    props = standardizer.extract_properties(block)
    assert standardizer._classify_idea("law_income") == "law"
    assert any("# Laws" in line for line in standardizer.format_block(props))

    assert standardizer.standardize_file(str(country), str(country))
    output = _read(country)
    for heading in (
        "# Laws",
        "# Internal Factions",
        "# Country Content",
        "# Dynamic Modifiers",
        "# Air Force Equipment",
        "# Naval Equipment",
    ):
        assert heading in output, heading
    assert output.count("set_country_flag = TST_started") == 1
    assert output.count("clr_country_flag = TST_old") == 1
    assert "other_statement = yes" in output
    assert standardizer.standardize_file(str(country), str(country))
    assert _read(country) == output


def test_without_a_mod_root_classification_is_empty(tmp_path):
    source = _write(
        tmp_path / "history.txt", "2000.1.1 = {\n\tset_country_flag = TST_flag\n}\n"
    )
    standardizer = HistoryStandardizer()
    assert standardizer.standardize_file(str(source), str(source))
    assert (standardizer._law, standardizer._faction, standardizer._modvars) == (
        set(),
        set(),
        {},
    )
    assert _detect_mod_root(str(tmp_path)) is None
