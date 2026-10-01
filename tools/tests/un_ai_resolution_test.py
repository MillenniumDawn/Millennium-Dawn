"""Guards for the UN AI proposal paths in 01_international_systems_effects.txt."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "01_international_systems_effects.txt"
)


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"Missing effect {name}"
    opening = text.index("{", match.start())
    depth = 0
    for index in range(opening, len(text)):
        character = text[index]
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    raise AssertionError(f"Unclosed block {name}")


SC_CONSIDER_ACTION = _named_block(
    EFFECTS_PATH.read_text(encoding="utf-8"), "un_ai_sc_consider_action"
)


def _tension_ladder(block: str) -> list[tuple[int, int]]:
    """Pairs of (tension threshold, action type) in the order the chain tests them."""
    pattern = re.compile(
        r"check_variable\s*=\s*\{\s*has_added_tension_amount\s*>\s*(\d+)\s*\}"
        r".*?set_temp_variable\s*=\s*\{\s*sc_ai_action_type\s*=\s*(\d+)\s*\}",
        re.S,
    )
    return [(int(t), int(a)) for t, a in pattern.findall(block)]


def test_security_council_tension_ladder_is_ordered_high_to_low():
    ladder = _tension_ladder(SC_CONSIDER_ACTION)

    assert len(ladder) >= 2, ladder
    thresholds = [threshold for threshold, _ in ladder]
    assert thresholds == sorted(thresholds, reverse=True), (
        "An else_if chain tests branches in order, so a lower tension threshold "
        f"placed first shadows every stricter branch after it: {ladder}"
    )
    assert len(set(thresholds)) == len(thresholds), f"Duplicate threshold: {ladder}"


def test_arms_embargo_stays_reachable_and_is_not_reproposed():
    ladder = _tension_ladder(SC_CONSIDER_ACTION)
    types = [action for _, action in ladder]

    assert 4 in types, f"Arms embargo branch missing: {ladder}"
    embargo = next(threshold for threshold, action in ladder if action == 4)
    sanctions = next(threshold for threshold, action in ladder if action == 2)
    assert (
        embargo > sanctions
    ), f"Arms embargo needs the stricter threshold: embargo {embargo}, sanctions {sanctions}"
    assert "NOT = { has_idea = unsc_arms_embargo }" in SC_CONSIDER_ACTION


def test_proposal_marks_the_subject_so_it_cannot_be_double_queued():
    assert "set_global_flag = sc_action_against@THIS" in SC_CONSIDER_ACTION
    assert "NOT = { has_global_flag = sc_action_against@THIS }" in SC_CONSIDER_ACTION
    assert SC_CONSIDER_ACTION.index(
        "NOT = { has_global_flag = sc_action_against@THIS }"
    ) < SC_CONSIDER_ACTION.index("set_global_flag = sc_action_against@THIS")
