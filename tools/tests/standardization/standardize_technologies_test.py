"""Tests for the technology standardizer."""

import re

import pytest
from shared.paths import REPO_ROOT
from standardize_api import standardize_text
from standardize_technologies import TechnologyStandardizer

_TECH_DIR = REPO_ROOT / "common" / "technologies"


def _format(source):
    std = TechnologyStandardizer()
    lines = [line + "\n" for line in source.strip("\n").splitlines()]
    return std.format_block(std.extract_properties(lines))


def _file(text):
    return standardize_text("technology", text)


def test_space_skeleton_reorders_into_fixed_layout():
    assert (
        _format("""
	sat_1 = {
		research_cost = 2
		start_year = 2000
		show_equipment_icon = yes
		enable_equipments = {
			sat_1
		}
		folder = {
			name = space_folder
			position = { x = @row1 y = @2000 }
		}
		path = {
			leads_to_tech = sat_2
			research_cost_coeff = 1
		}
		categories = {
			CAT_space
			CAT_Civilian
		}
		special_project_specialization = { specialization_air }
		ai_will_do = {
			factor = 1
		}
	}
""")
        == [
            "\tsat_1 = {",
            "\t\tenable_equipments = { sat_1 }",
            "\t\tshow_equipment_icon = yes",
            "",
            "\t\tresearch_cost = 2",
            "\t\tstart_year = 2000",
            "",
            "\t\tpath = {",
            "\t\t\tleads_to_tech = sat_2",
            "\t\t\tresearch_cost_coeff = 1",
            "\t\t}",
            "\t\tfolder = {",
            "\t\t\tname = space_folder",
            "\t\t\tposition = { x = @row1 y = @2000 }",
            "\t\t}",
            "\t\tcategories = {",
            "\t\t\tCAT_space",
            "\t\t\tCAT_Civilian",
            "\t\t}",
            "\t\tspecial_project_specialization = { specialization_air }",
            "",
            "\t\tai_will_do = { factor = 1 }",
            "\t}",
        ]
    )


def test_free_modifiers_keep_source_order_and_carry_comments():
    assert (
        _format("""
	night_vision_1 = {
		research_cost = 2
		# the stat this tech is about
		land_night_attack = 0.05
		category_MR_fighter = {
			maximum_speed = 0.10
			#build_cost_ic = 0.05
		}
		Arty_Bat = {
			max_organisation = 0.1
			plains = { attack = 0.05 defence = 0.1 }
		}
		custom_modifier_tooltip = nv_tt
		army_personnel_cost_multiplier_modifier = 0.02
		allow = {
			original_tag = UKR
		}
	}
""")
        == [
            "\tnight_vision_1 = {",
            "\t\tallow = { original_tag = UKR }",
            "",
            "\t\t# the stat this tech is about",
            "\t\tland_night_attack = 0.05",
            "\t\tcategory_MR_fighter = {",
            "\t\t\tmaximum_speed = 0.10",
            "\t\t\t#build_cost_ic = 0.05",
            "\t\t}",
            "\t\tArty_Bat = {",
            "\t\t\tmax_organisation = 0.1",
            "\t\t\tplains = { attack = 0.05 defence = 0.1 }",
            "\t\t}",
            "\t\tarmy_personnel_cost_multiplier_modifier = 0.02",
            "\t\tcustom_modifier_tooltip = nv_tt",
            "",
            "\t\tresearch_cost = 2",
            "\t}",
        ]
    )


def test_token_lists_collapse_only_for_single_tokens():
    assert (
        _format("""
	awacs_2 = {
		enable_equipment_modules = { weap_buff_awacs_2 }
		dependencies = {
			awacs_1 = 1
		}
		sub_technologies = {
			CV_awacs_2
		}
		categories = { CAT_air_eqp CAT_awacs }
		XOR = {
			wimax
		}
		enable_building = {
			building = infrastructure
			level = 6
		}
	}
""")
        == [
            "\tawacs_2 = {",
            "\t\tdependencies = { awacs_1 = 1 }",
            "\t\tXOR = { wimax }",
            "",
            "\t\tenable_equipment_modules = { weap_buff_awacs_2 }",
            "\t\tenable_building = {",
            "\t\t\tbuilding = infrastructure",
            "\t\t\tlevel = 6",
            "\t\t}",
            "\t\tsub_technologies = { CV_awacs_2 }",
            "",
            "\t\tcategories = {",
            "\t\t\tCAT_air_eqp",
            "\t\t\tCAT_awacs",
            "\t\t}",
            "\t}",
        ]
    )


def test_repeated_paths_and_remaining_slots():
    assert (
        _format("""
	MR_upgrade_1 = {
		ai_will_do = { factor = 1 }
		path = {
			leads_to_tech = MR_Fighter3
			research_cost_coeff = 1
		}
		on_research_complete = {
			custom_effect_tooltip = COLD_WAR_TECH_CANT_TAKE
		}
		path = {
			leads_to_tech = MR_Fighter4
			research_cost_coeff = 1
		}
		on_research_complete_limit = { ROOT = { num_of_naval_factories > 0 } }
		xp_research_bonus = 1.50
		xp_unlock_cost = 50
		xp_research_type = army
		doctrine = yes
		ai_research_weights = {
			oil = -2.0
		}
		is_special_project_tech = yes
		# leftover
	}
""")
        == [
            "\tMR_upgrade_1 = {",
            "\t\tis_special_project_tech = yes",
            "\t\tdoctrine = yes",
            "",
            "\t\ton_research_complete_limit = { ROOT = { num_of_naval_factories > 0 } }",
            "\t\ton_research_complete = { custom_effect_tooltip = COLD_WAR_TECH_CANT_TAKE }",
            "",
            "\t\txp_research_type = army",
            "\t\txp_unlock_cost = 50",
            "\t\txp_research_bonus = 1.50",
            "",
            "\t\tpath = {",
            "\t\t\tleads_to_tech = MR_Fighter3",
            "\t\t\tresearch_cost_coeff = 1",
            "\t\t}",
            "\t\tpath = {",
            "\t\t\tleads_to_tech = MR_Fighter4",
            "\t\t\tresearch_cost_coeff = 1",
            "\t\t}",
            "",
            "\t\tai_research_weights = { oil = -2.0 }",
            "\t\tai_will_do = { factor = 1 }",
            "",
            "\t\t# leftover",
            "\t}",
        ]
    )


_FILE = """\
#Written by someone
technologies = {
	@1965 = 0
	@row1 = -8.5



	###Infantry Weapons###
	#1965
			infantry_weapons_1 = {
				enable_equipments = { infantry_weapons_1 } # opener note
				research_cost = 1
				folder = {
					name = infantry_folder
					position = { x = @row1 y = @1965 }
				}
			}
	#1975
	packed = { research_cost = 1 start_year = 1965 }


}
"""


def test_file_passes_wrapper_through_and_reindents_bodies():
    assert _file(_FILE) == (
        "#Written by someone\n"
        "technologies = {\n"
        "\t@1965 = 0\n"
        "\t@row1 = -8.5\n"
        "\n"
        "\t###Infantry Weapons###\n"
        "\t#1965\n"
        "\tinfantry_weapons_1 = {\n"
        "\t\tenable_equipments = { infantry_weapons_1 } # opener note\n"
        "\n"
        "\t\tresearch_cost = 1\n"
        "\n"
        "\t\tfolder = {\n"
        "\t\t\tname = infantry_folder\n"
        "\t\t\tposition = { x = @row1 y = @1965 }\n"
        "\t\t}\n"
        "\t}\n"
        "\n"
        "\t#1975\n"
        "\tpacked = {\n"
        "\t\tresearch_cost = 1\n"
        "\t\tstart_year = 1965\n"
        "\t}\n"
        "}\n"
    )


def test_file_is_idempotent():
    first = _file(_FILE)
    assert _file(first) == first


def test_opener_comment_survives():
    assert _format("\tfoo = { # keep me\n\t\tresearch_cost = 1\n\t}\n")[0] == (
        "\tfoo = { # keep me"
    )


def _tech_ids(text):
    ids = []
    depth = 0
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        match = re.match(r"\s*(\w+)\s*=\s*\{", code)
        if match and depth == 1:
            ids.append(match.group(1))
        depth += code.count("{") - code.count("}")
    return ids


@pytest.mark.parametrize(
    "path",
    sorted(_TECH_DIR.glob("*.txt")) if _TECH_DIR.is_dir() else [],
    ids=lambda p: p.name,
)
def test_real_files_round_trip(path):
    text = path.read_text(encoding="utf-8")
    first = _file(text)
    assert first is not None
    assert first.count("{") == first.count("}")
    assert _tech_ids(first) == _tech_ids(text)
    assert _file(first) == first
