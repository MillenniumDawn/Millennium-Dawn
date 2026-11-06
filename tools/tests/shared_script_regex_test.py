"""The shared script shapes, and that consumers do not recompile them."""

import ast
from pathlib import Path

import pytest
import shared_utils
import validator_common

_SHARED_PATTERNS = {
    shape.pattern
    for shape in (
        shared_utils.WORD_BLOCK_START_RE,
        shared_utils.IDENTIFIER_BLOCK_START_RE,
        shared_utils.COUNTRY_TAG_ASSIGNMENT_RE,
        shared_utils.OPTION_OPEN_RE,
        shared_utils.MODIFIER_OPEN_RE,
        shared_utils.TRIGGER_OPEN_RE,
        shared_utils.AVAILABLE_OPEN_RE,
        validator_common.BANKRUPTCY_GUARD_RE,
        validator_common.DEFICIT_GUARD_RE,
    )
}

# shape: (regex, text where the shape's key is part of a longer word)
_LONGER_KEYS = {
    "option": (shared_utils.OPTION_OPEN_RE, "the_nuclear_option = {"),
    "modifier": (shared_utils.MODIFIER_OPEN_RE, "add_opinion_modifier = {"),
    "trigger": (shared_utils.TRIGGER_OPEN_RE, "cancel_trigger = {"),
    "available": (shared_utils.AVAILABLE_OPEN_RE, "temp_spy_available = {"),
    "bankruptcy start": (
        validator_common.BANKRUPTCY_GUARD_RE,
        "not_has_active_mission = bankruptcy_incoming_collapse",
    ),
    "bankruptcy end": (
        validator_common.BANKRUPTCY_GUARD_RE,
        "has_active_mission = bankruptcy_incoming_collapse_timer",
    ),
    "deficit start": (
        validator_common.DEFICIT_GUARD_RE,
        "not_ai_has_high_deficit = yes",
    ),
    "deficit end": (validator_common.DEFICIT_GUARD_RE, "ai_has_high_deficit = yes_x"),
}


@pytest.mark.parametrize(("shape", "text"), _LONGER_KEYS.values(), ids=_LONGER_KEYS)
def test_shared_shapes_do_not_match_longer_keys(shape, text):
    assert shape.search(text) is None


def test_shared_shapes_are_not_compiled_in_consumers():
    root = Path(shared_utils.__file__).parent
    duplicates = []
    for path in root.rglob("*.py"):
        if "tests" in path.parts or path.name in {
            "shared_utils.py",
            "validator_common.py",
        }:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "re"
                and node.func.attr == "compile"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value in _SHARED_PATTERNS
            ):
                duplicates.append(f"{path.relative_to(root)}:{node.lineno}")
    assert not duplicates, "Use the shared script shape: " + ", ".join(duplicates)
