"""Regression fixtures for the localisation errors fixed by hand in #5094 and #5091.

Each pre-fix string must be reported by a validator check and its corrected
counterpart must pass (issues #5097 and #5101). USA_econ_event.22.d is the
exception: #5094 dropped the bare § that the engine read as a color code, and
the citation now uses the escaped `§§` (checked in game, 1.19.3). The strings are copied verbatim
from the commits before and after each fix; georg.1000.d is cut to the
sentences around its quote.
"""

from pathlib import Path

import pytest
from fix_loc_yaml import check_line
from shared.suite import yml_syntax
from validate_localisation import _scan_prose_text
from validate_scripted_localisation import (
    _documented_getters,
    _getter_spelling_message,
    process_file_for_getter_refs,
)

REPO = Path(__file__).resolve().parents[3]
DOCUMENTED = _documented_getters(str(REPO))

# Before #5094 (bbedbc3b0d^).
BEFORE_5094 = {
    "georg.1000.d": (
        'georg.1000.d: "It is difficult to say what was more here: the desire to help the motherland in difficult times or the longing for power and active work. I knew that if I had not returned to Georgia, she would have died,\\" Shevardnadze said. There was some truth in his words, but, unlike Heydar Aliyev, who found himself in a similar situation, he failed to consolidate society. Probably, Shevardnadze expected to be in a small country \\"a whale in an aquarium\\", before whose world authority everyone would bow in unison."'
    ),
    "GER_idea_crackheads_desc": (
        'GER_idea_crackheads_desc: "Since the legalization of all drugs across [THIS.Getname], a new epidemic of crack addiction has arisen within the poorer communities.\\n§W--------------§!\\nThis national spirit can be §RRemoved§! if we have §HAdvanced Universal Healthcare§!."'
    ),
    "IRQ_invite_to_economic_union_targeted_decision": (
        'IRQ_invite_to_economic_union_targeted_decision: "Invite [FROM.Getname]"'
    ),
    "iranian_focus.175.d": (
        'iranian_focus.175.d: "[TRK.Getname] has declined our offer for a political meeting on the Atrak River border."'
    ),
    "PER_iraq_military_industry_increase": (
        'PER_iraq_military_industry_increase: "Industrial Aid To [IRQ.GetFlag][IRQ.Getname]"'
    ),
    "PER_iraq_military_industry_increase_d": (
        'PER_iraq_military_industry_increase_d: "Industrial Aid To [IRQ.GetFlag][IRQ.Getname]"'
    ),
    "PER_syria_military_industry_increase": (
        'PER_syria_military_industry_increase: "Industrial Aid To [SYR.GetFlag][SYR.Getname]"'
    ),
    "PER_syria_military_industry_increase_d": (
        'PER_syria_military_industry_increase_d: "Industrial Aid To [SYR.GetFlag][SYR.Getname]"'
    ),
    "PER_houthis_military_industry_increase": (
        'PER_houthis_military_industry_increase: "Industrial Aid To [HOU.GetFlag][HOU.Getname]"'
    ),
    "PER_houthis_military_industry_increase_d": (
        'PER_houthis_military_industry_increase_d: "Industrial Aid To [HOU.GetFlag][HOU.Getname]"'
    ),
    "USA_econ_event.22.d": (
        'USA_econ_event.22.d: "Beginning at least as early as December 1993 and continuing until at least October 2001, the exact dates being unknown to the United States, the Defendant and co-conspirators entered into and engaged in a combination and conspiracy to suppress and eliminate competition by allocating suppliers in the purchase of ferrous and nonferrous scrap metal in Northeast Ohio. The charged combination and conspiracy unreasonably restrained interstate trade and commerce in violation of Section 1 of the Sherman Antitrust Act (15 U.S.C. § 1)."'
    ),
    "VEN_mission_arbol_desc": (
        'VEN_mission_arbol_desc: "\\"Mision Arbol\\" (\\"Tree Mission\\") from Guaraira Repano or Mount Avila looming over Venezuela\'s capital, Caracas. While planting dozens of trees with members of Venezuela\'s newly formed Conservation Committees, Chavez explained, \\"If you are going to utilize a tree, you have to do it with consciousness and respect for the environment.  If you cut down a tree you need to plant 10 more."'
    ),
    "VEN_demand_the_canal_desc": (
        'VEN_demand_the_canal_desc: "The government has issued a high-stakes diplomatic ultimatum to [PAN.getname], demanding the immediate transfer of control over the Panama Canal to Venezuela. Citing historical ties and regional dominance. This demand is underpinned by an unyielding resolve to secure the strategic waterway."'
    ),
}

# After #5094 (bbedbc3b0d).
AFTER_5094 = {
    "georg.1000.d": (
        'georg.1000.d: "It is difficult to say what was more here: the desire to help the motherland in difficult times or the longing for power and active work. "I knew that if I had not returned to Georgia, she would have died,\\" Shevardnadze said. There was some truth in his words, but, unlike Heydar Aliyev, who found himself in a similar situation, he failed to consolidate society. Probably, Shevardnadze expected to be in a small country \\"a whale in an aquarium\\", before whose world authority everyone would bow in unison."'
    ),
    "GER_idea_crackheads_desc": (
        'GER_idea_crackheads_desc: "Since the legalization of all drugs across [THIS.GetName], a new epidemic of crack addiction has arisen within the poorer communities.\\n§W--------------§!\\nThis national spirit can be §RRemoved§! if we have §HAdvanced Universal Healthcare§!."'
    ),
    "IRQ_invite_to_economic_union_targeted_decision": (
        'IRQ_invite_to_economic_union_targeted_decision: "Invite [FROM.GetName]"'
    ),
    "iranian_focus.175.d": (
        'iranian_focus.175.d: "[TRK.GetName] has declined our offer for a political meeting on the Atrak River border."'
    ),
    "PER_iraq_military_industry_increase": (
        'PER_iraq_military_industry_increase: "Industrial Aid To [IRQ.GetFlag][IRQ.GetName]"'
    ),
    "PER_iraq_military_industry_increase_d": (
        'PER_iraq_military_industry_increase_d: "Industrial Aid To [IRQ.GetFlag][IRQ.GetName]"'
    ),
    "PER_syria_military_industry_increase": (
        'PER_syria_military_industry_increase: "Industrial Aid To [SYR.GetFlag][SYR.GetName]"'
    ),
    "PER_syria_military_industry_increase_d": (
        'PER_syria_military_industry_increase_d: "Industrial Aid To [SYR.GetFlag][SYR.GetName]"'
    ),
    "PER_houthis_military_industry_increase": (
        'PER_houthis_military_industry_increase: "Industrial Aid To [HOU.GetFlag][HOU.GetName]"'
    ),
    "PER_houthis_military_industry_increase_d": (
        'PER_houthis_military_industry_increase_d: "Industrial Aid To [HOU.GetFlag][HOU.GetName]"'
    ),
    "USA_econ_event.22.d": (
        'USA_econ_event.22.d: "Beginning at least as early as December 1993 and continuing until at least October 2001, the exact dates being unknown to the United States, the Defendant and co-conspirators entered into and engaged in a combination and conspiracy to suppress and eliminate competition by allocating suppliers in the purchase of ferrous and nonferrous scrap metal in Northeast Ohio. The charged combination and conspiracy unreasonably restrained interstate trade and commerce in violation of Section 1 of the Sherman Antitrust Act (15 U.S.C. 1)."'
    ),
    "VEN_mission_arbol_desc": (
        'VEN_mission_arbol_desc: "\\"Mision Arbol\\" (\\"Tree Mission\\") from Guaraira Repano or Mount Avila looming over Venezuela\'s capital, Caracas. While planting dozens of trees with members of Venezuela\'s newly formed Conservation Committees, Chavez explained, \\"If you are going to utilize a tree, you have to do it with consciousness and respect for the environment.  If you cut down a tree you need to plant 10 more.""'
    ),
    "VEN_demand_the_canal_desc": (
        'VEN_demand_the_canal_desc: "The government has issued a high-stakes diplomatic ultimatum to [PAN.GetName], demanding the immediate transfer of control over the Panama Canal to Venezuela. Citing historical ties and regional dominance. This demand is underpinned by an unyielding resolve to secure the strategic waterway."'
    ),
}

# After #5099 (689baaf9a5): the quotes #5094 added bare, escaped.
AFTER_5099 = {
    "georg.1000.d": (
        'georg.1000.d: "It is difficult to say what was more here: the desire to help the motherland in difficult times or the longing for power and active work. \\"I knew that if I had not returned to Georgia, she would have died,\\" Shevardnadze said. There was some truth in his words, but, unlike Heydar Aliyev, who found himself in a similar situation, he failed to consolidate society. Probably, Shevardnadze expected to be in a small country \\"a whale in an aquarium\\", before whose world authority everyone would bow in unison."'
    ),
    "VEN_mission_arbol_desc": (
        'VEN_mission_arbol_desc: "\\"Mision Arbol\\" (\\"Tree Mission\\") from Guaraira Repano or Mount Avila looming over Venezuela\'s capital, Caracas. While planting dozens of trees with members of Venezuela\'s newly formed Conservation Committees, Chavez explained, \\"If you are going to utilize a tree, you have to do it with consciousness and respect for the environment.  If you cut down a tree you need to plant 10 more.\\""'
    ),
}

BLR_BEFORE_5091 = 'BLR_people_militia_desc: "But the situation is not easy. I have said more than once: every man (and not only a man) should be able, at least, to handle weapons. At least in order, if necessary, to protect your family, your home, your native corner of the earth and, if necessary, the country, without which there will be no corner, no home, nothing else. Many people understand this,\\" Alexander Lukashenko stressed."'
BLR_AFTER_5091 = 'BLR_people_militia_desc: "\\"But the situation is not easy. I have said more than once: every man (and not only a man) should be able, at least, to handle weapons. At least in order, if necessary, to protect your family, your home, your native corner of the earth and, if necessary, the country, without which there will be no corner, no home, nothing else. Many people understand this,\\" Alexander Lukashenko stressed."'

GETTER_KEYS = [key for key, line in BEFORE_5094.items() if "etname]" in line]
QUOTE_KEYS = ["georg.1000.d", "VEN_mission_arbol_desc"]


def _getter_findings(tmp_path, line):
    # FileOpener caches by path, so every fixture gets its own file.
    path = tmp_path / f"fixture{len(list(tmp_path.iterdir()))}_l_english.yml"
    path.write_text(f"l_english:\n {line}\n", encoding="utf-8-sig")
    return [
        message
        for member, _ in process_file_for_getter_refs(str(path))
        if (message := _getter_spelling_message(member, set(), DOCUMENTED))
    ]


def _quote_findings(line):
    issues = _scan_prose_text(f"l_english:\n {line}\n", "fixture_l_english.yml")
    return [issue for issue in issues if issue.category == "loc-unbalanced-quote"]


def test_every_5094_string_has_a_fixture_class():
    assert len(BEFORE_5094) == 13
    assert len(GETTER_KEYS) == 10
    assert set(GETTER_KEYS) | set(QUOTE_KEYS) | {"USA_econ_event.22.d"} == set(
        BEFORE_5094
    )


@pytest.mark.parametrize("key", GETTER_KEYS)
def test_5094_getter_typo_is_reported(tmp_path, key):
    assert _getter_findings(tmp_path, BEFORE_5094[key])
    assert _getter_findings(tmp_path, AFTER_5094[key]) == []


@pytest.mark.parametrize("key", QUOTE_KEYS)
def test_5094_missing_quote_is_reported(key):
    assert len(_quote_findings(BEFORE_5094[key])) == 1
    assert _quote_findings(AFTER_5099[key]) == []


@pytest.mark.parametrize("key", QUOTE_KEYS)
def test_5094_bare_quote_fails_the_yaml_lint(key):
    kinds = {kind for _, kind, _ in check_line(" " + AFTER_5094[key], 2)}
    assert "unescaped_quote" in kinds or "missing_close_quote" in kinds
    assert check_line(" " + AFTER_5099[key], 2) == []


def test_5091_malformed_opening_quote_is_reported():
    assert len(_quote_findings(BLR_BEFORE_5091)) == 1
    assert _quote_findings(BLR_AFTER_5091) == []


def _syntax_findings(tmp_path, line):
    path = tmp_path / f"syntax{len(list(tmp_path.iterdir()))}_l_english.yml"
    path.write_text(f"l_english:\n {line}\n", encoding="utf-8-sig")
    return yml_syntax(path, ["Y", "R", "G"])


def test_5094_bare_section_sign_is_reported(tmp_path):
    before = BEFORE_5094["USA_econ_event.22.d"]
    escaped = before.replace("(15 U.S.C. § 1)", "(15 U.S.C. §§ 1)")
    assert escaped != before
    assert len(_syntax_findings(tmp_path, before)) == 1
    assert _syntax_findings(tmp_path, AFTER_5094["USA_econ_event.22.d"]) == []
    assert _syntax_findings(tmp_path, escaped) == []
