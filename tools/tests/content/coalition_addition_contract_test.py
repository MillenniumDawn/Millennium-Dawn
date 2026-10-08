from pathlib import Path

import pytest
from shared.suite import read_text
from shared_utils import (
    extract_block_from_text,
    iter_statement_ops,
    iter_statements,
    strip_comments,
)

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def coalition_addition():
    script = strip_comments(
        read_text(
            ROOT / "common/scripted_effects/00_MD_politicsview_scripted_effects.txt"
        )
    )
    effect, end = extract_block_from_text(
        script, script.index("add_coalition_members_effect = {")
    )
    assert end > 0
    [(keyword, _, body)] = list(iter_statements(effect))
    assert keyword == "if"
    assert body is not None
    statements = list(iter_statements(body))
    guard = next(block for key, _, block in statements if key == "limit")
    assert guard is not None
    return guard, statements


def _can_add(guard, ruling_party, candidate, coalition):
    variables = {"ruling_party": ruling_party, "add_col_one": candidate}
    results = []
    for keyword, _, block in iter_statements(guard):
        assert keyword == "NOT"
        assert block is not None
        [(trigger, _, arguments)] = list(iter_statements(block))
        assert arguments is not None
        [(left, operator, right, nested)] = list(iter_statement_ops(arguments))
        assert operator == "="
        assert right is not None
        assert nested is None
        if trigger == "check_variable":
            blocked = variables[left] == variables[right]
        else:
            assert trigger == "is_in_array"
            assert left == "gov_coalition_array"
            blocked = variables[right] in coalition
        results.append(not blocked)
    return all(results)


@pytest.mark.parametrize("candidate", range(24))
@pytest.mark.parametrize(
    "ruling_offset,partner_offsets,allowed",
    [
        pytest.param(0, (), False, id="ruling-party"),
        pytest.param(1, (0,), False, id="existing-partner"),
        pytest.param(1, (), True, id="new-partner-empty-coalition"),
        pytest.param(1, (2,), True, id="new-partner-existing-coalition"),
    ],
)
def test_coalition_addition_guard(
    coalition_addition, candidate, ruling_offset, partner_offsets, allowed
):
    guard, _ = coalition_addition
    ruling_party = (candidate + ruling_offset) % 24
    coalition = [(candidate + offset) % 24 for offset in partner_offsets]
    assert _can_add(guard, ruling_party, candidate, coalition) is allowed


def test_coalition_addition_guards_tooltip_membership_and_recalculation(
    coalition_addition,
):
    _, statements = coalition_addition
    effects = [
        (key, scalar, block.strip() if block is not None else None)
        for key, scalar, block in statements
        if key != "limit"
    ]
    assert effects == [
        ("custom_effect_tooltip", "add_coalition_members_effect_TT", None),
        ("add_to_array", None, "gov_coalition_array = add_col_one"),
        ("hidden_effect", None, "update_government_coalition_strength = yes"),
    ]
