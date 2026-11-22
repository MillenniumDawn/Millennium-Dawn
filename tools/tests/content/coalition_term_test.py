"""Exercise coalition formation and term settlement against synthetic governments."""

import pytest
from ai_race_state_model_test import _parse_race_script
from shared.paths import REPO_ROOT
from shared.suite import only_block
from stalker_script_model_test import StalkerModel

POLITICS = (
    REPO_ROOT / "common/scripted_effects/00_MD_politicsview_scripted_effects.txt"
).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("limit", "term", "election", "winner", "expected_term", "replacements"),
    [
        (2, 1, True, 1, 2, 0),  # Incumbent may serve the final term.
        (2, 2, True, 1, 1, 1),
        (1, 1, True, 2, 1, 1),  # No second succession on installing the winner.
        (0, 4, True, 1, 5, 0),
        (2, 2, False, 1, 2, 0),  # A reshuffle is not an election.
        (2, 2, False, 2, 0, 1),  # A midterm successor serves a partial term.
    ],
)
def test_coalition_term(limit, term, election, winner, expected_term, replacements):
    model = StalkerModel(tags=("---", "TST"))
    for effect in (
        "form_timeout_government",
        "change_ruling_party_effect",
        "settle_coalition_term",
        "advance_elected_term",
    ):
        body = only_block(POLITICS, effect)
        model.effects.update(_parse_race_script(f"{effect} = {{ {body} }}"))
    # Replace the country-specific roster with one observable succession.
    model.effects.update(
        _parse_race_script(
            "set_leader = { add_to_variable = { replacements = 1 } "
            "set_variable = { current_term = 1 } }"
        )
    )
    model.stubs.update(
        {
            "custom_effect_tooltip",
            "set_politics",
            "update_government_coalition_strength",
            "update_set_politics",
            "IP_idea_configuration",
            "mb_refresh_relations_effect",
            "force_update_map_mode",
        }
    )
    country = model.countries[1]
    country["vars"].update(ruling_party=1, current_term=term, term_limit=limit)
    if election:
        country["flags"]["coalition_election_term_pending"] = None
    model.temps["rul_party_temp"] = winner
    model.run("form_timeout_government", 1)
    model.run("settle_coalition_term", 1)
    model.run("settle_coalition_term", 1)
    assert country["vars"]["ruling_party"] == winner
    assert country["vars"]["current_term"] == expected_term
    assert country["vars"].get("replacements", 0) == replacements
