from pathlib import Path

import ai_path_report as report
import pytest
from shared.suite import read_text
from shared_utils import (
    extract_block_from_text,
    iter_focus_blocks,
    iter_statements,
    strip_comments,
)

ROOT = Path(__file__).resolve().parents[3]
FOCUS_SCRIPT = strip_comments(
    read_text(ROOT / "common/national_focus/05_south_korea.txt")
)
FOCUS_BODIES = {
    focus_id: body for focus_id, _, _, body in iter_focus_blocks(FOCUS_SCRIPT)
}
FOCUSES = {focus.id: focus for focus in report.parse_focus_file(FOCUS_SCRIPT, "KOR")}
PATH_TRIGGERS = report.load_path_triggers(str(ROOT), "KOR")


def _block(body, name):
    block, end = extract_block_from_text(body, body.index(f"{name} = {{"))
    assert end > 0
    return block


@pytest.mark.parametrize("historical", [False, True])
@pytest.mark.parametrize(
    "active_flag",
    [
        None,
        "KOR_HISTORICAL_FOCUS_PATH",
        "KOR_SUNSHINE_FOCUS_PATH",
        "KOR_HARDLINE_FOCUS_PATH",
        "KOR_YUSIN_FOCUS_PATH",
    ],
)
@pytest.mark.parametrize(
    "blocked_flag,rival,chosen",
    [
        (
            "KOR_HARDLINE_FOCUS_PATH",
            "KOR_expand_proportional_representation",
            "KOR_end_proportional_representation",
        ),
        (
            "KOR_YUSIN_FOCUS_PATH",
            "KOR_champion_human_rights",
            "KOR_commemorate_dictatorship",
        ),
    ],
)
def test_exclusive_rival_is_blocked_only_for_its_selected_path(
    historical, active_flag, blocked_flag, rival, chosen
):
    state = report.State(option="test", flag=active_flag, historical=historical)
    weight, _ = report.focus_weight(FOCUSES[rival], state, PATH_TRIGGERS)
    assert chosen in FOCUSES[rival].mutex
    assert rival in FOCUSES[chosen].mutex
    if active_flag == blocked_flag:
        assert weight == 0
        chosen_weight, _ = report.focus_weight(FOCUSES[chosen], state, PATH_TRIGGERS)
        assert chosen_weight > 0
    else:
        assert weight > 0


@pytest.mark.parametrize("historical", [False, True])
def test_yusin_has_a_reachable_ai_only_cure_for_starting_wartime_control(historical):
    history = strip_comments(read_text(ROOT / "history/countries/KOR - Korea.txt"))
    starting_ideas = _block(_block(history, "2000.1.1"), "add_ideas").split()
    assert "KOR_wartime_control" in starting_ideas

    state = report.State(
        option="YUSIN", flag="KOR_YUSIN_FOCUS_PATH", historical=historical
    )
    assert "KOR_install_the_yusin_dictatorship" in report.live_focuses(
        list(FOCUSES.values()), FOCUSES, state, PATH_TRIGGERS
    )
    reward = _block(
        FOCUS_BODIES["KOR_install_the_yusin_dictatorship"], "completion_reward"
    )
    hidden = _block(reward, "hidden_effect")
    recovery = _block(hidden, "if")
    assert dict(
        (key, scalar) for key, scalar, _ in iter_statements(_block(recovery, "limit"))
    ) == {
        "is_ai": "yes",
        "has_global_flag": "KOR_YUSIN_FOCUS_PATH",
        "has_idea": "KOR_wartime_control",
    }
    removal = ("remove_ideas", "KOR_wartime_control", None)
    assert removal in list(iter_statements(recovery))
    assert removal not in list(iter_statements(hidden))
    assert removal not in list(iter_statements(reward))
    assert "rul_party_temp = 0" in hidden
    conservative_government = _block(
        strip_comments(
            read_text(ROOT / "common/scripted_triggers/99_KOR_scripted_triggers.txt")
        ),
        "KOR_has_conservative_government",
    )
    assert "western_autocrats_are_in_power = yes" in conservative_government
    for focus_id in ("KOR_offensive_approach", "KOR_provoke_confrontation"):
        available = _block(FOCUS_BODIES[focus_id], "available")
        assert "KOR_has_conservative_government = yes" in available
        assert "NOT = { has_idea = KOR_wartime_control }" in available
        assert focus_id in report.live_focuses(
            list(FOCUSES.values()), FOCUSES, state, PATH_TRIGGERS
        )
