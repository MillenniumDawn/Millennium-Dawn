"""Source contracts for FSA missions; engine timer behavior needs an in-game run."""

import pytest
from shared.paths import REPO_ROOT
from shared_utils import iter_statements, read_script


def _block(script, name):
    blocks = [body for key, _, body in iter_statements(script) if key == name]
    assert len(blocks) == 1 and blocks[0] is not None, name
    return blocks[0]


DECISIONS = _block(
    read_script(str(REPO_ROOT / "common/decisions/Free_syrian_army.txt")),
    "FSA_internal_revolt_category",
)
MISSIONS = {
    key: body for key, _, body in iter_statements(DECISIONS) if body is not None
}
CLOCK_ID = "FSA_defection_to_extremist"
CLOCK = MISSIONS[CLOCK_ID]
TIMEOUT = _block(CLOCK, "timeout_effect")
ACTIVE = "FSA_internal_revolt_missions_active"
IDEAS = _block(
    _block(read_script(str(REPO_ROOT / "common/ideas/Free-Syrian-Army.txt")), "ideas"),
    "country",
)


def test_mission_gate_ends_at_peace_salafist_rule_or_maximum_extremism():
    gate = _block(
        read_script(
            str(REPO_ROOT / "common/scripted_triggers/99_FSA_scripted_triggers.txt")
        ),
        ACTIVE,
    )
    statements = list(iter_statements(gate))
    assert ("has_war_with", "SYR", None) in statements
    exclusions = [
        list(iter_statements(body))
        for key, _, body in statements
        if key == "NOT" and body is not None
    ]
    assert [("has_government", "fascism", None)] in exclusions
    assert [("has_idea", "FSA_extremism5", None)] in exclusions


@pytest.mark.parametrize("mission", MISSIONS)
def test_every_mission_uses_the_same_start_and_cancel_boundary(mission):
    body = MISSIONS[mission]
    assert (ACTIVE, "yes", None) in list(iter_statements(_block(body, "activation")))
    assert (ACTIVE, "no", None) in list(iter_statements(_block(body, "cancel_trigger")))


def test_first_timeout_starts_extremism_instead_of_only_restarting_the_clock():
    assert ("add_ideas", "FSA_extremism1", None) in list(
        iter_statements(_block(TIMEOUT, "else"))
    )


@pytest.mark.parametrize("tier", [1, 2, 3, 4])
def test_each_existing_extremism_tier_advances_once(tier):
    branches = [
        body
        for key, _, body in iter_statements(TIMEOUT)
        if key in {"if", "else_if"} and body is not None
    ]
    branch = next(
        body
        for body in branches
        if ("has_idea", f"FSA_extremism{tier}", None)
        in list(iter_statements(_block(body, "limit")))
    )
    assert list(iter_statements(_block(branch, "swap_ideas"))) == [
        ("remove_idea", f"FSA_extremism{tier}", None),
        ("add_idea", f"FSA_extremism{tier + 1}", None),
    ]


def test_clock_restarts_after_escalation_only_while_the_mission_gate_is_open():
    assert ("fire_only_once", "yes", None) not in list(iter_statements(CLOCK))
    key, _, restart = list(iter_statements(TIMEOUT))[-1]
    assert key == "if" and restart is not None
    assert list(iter_statements(_block(restart, "limit"))) == [(ACTIVE, "yes", None)]
    assert ("activate_mission", CLOCK_ID, None) in list(iter_statements(restart))


@pytest.mark.parametrize("mission", [name for name in MISSIONS if name != CLOCK_ID])
def test_capture_rewards_extend_only_an_active_clock(mission):
    body = MISSIONS[mission]
    assert ("has_active_mission", CLOCK_ID, None) in list(
        iter_statements(_block(body, "activation"))
    )
    reward = _block(_block(body, "complete_effect"), "if")
    assert list(iter_statements(_block(reward, "limit"))) == [
        ("has_active_mission", CLOCK_ID, None)
    ]
    assert list(iter_statements(_block(reward, "add_days_mission_timeout"))) == [
        ("mission", CLOCK_ID, None),
        ("days", "200", None),
    ]


@pytest.mark.parametrize("tier", [1, 2, 3, 4, 5])
def test_extremism_penalties_end_at_peace_or_salafist_rule(tier):
    cancel = _block(_block(IDEAS, f"FSA_extremism{tier}"), "cancel")
    alternatives = _block(cancel, "OR")
    assert ("has_government", "fascism", None) in list(iter_statements(alternatives))
    assert list(iter_statements(_block(alternatives, "NOT"))) == [
        ("has_war_with", "SYR", None)
    ]
