"""Keep shared script shapes equivalent and stop recompiling them in consumers."""

import ast
import re
from pathlib import Path

import pytest
import shared_utils
import validator_common

_SHAPES = [
    (shared_utils.WORD_BLOCK_START_RE, r"^(\w+)\s*=\s*\{", 0),
    (shared_utils.WORD_BLOCK_LINE_RE, r"^(\w+)\s*=\s*\{", re.M),
    (shared_utils.IDENTIFIER_BLOCK_START_RE, r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", 0),
    (
        shared_utils.IDENTIFIER_BLOCK_LINE_RE,
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{",
        re.M,
    ),
    (shared_utils.COUNTRY_TAG_ASSIGNMENT_RE, r'^\s*([A-Z0-9_]{3})\s*=\s*"', 0),
    (shared_utils.COUNTRY_TAG_ASSIGNMENT_LINE_RE, r'^\s*([A-Z0-9_]{3})\s*=\s*"', re.M),
    (shared_utils.OPTION_OPEN_RE, r"\boption\s*=\s*\{", 0),
    (shared_utils.MODIFIER_OPEN_RE, r"\bmodifier\s*=\s*\{", 0),
    (shared_utils.TRIGGER_OPEN_RE, r"\btrigger\s*=\s*\{", 0),
    (shared_utils.AVAILABLE_OPEN_RE, r"\bavailable\s*=\s*\{", 0),
    (
        validator_common.BANKRUPTCY_GUARD_RE,
        r"\bhas_active_mission\s*=\s*bankruptcy_incoming_collapse\b",
        0,
    ),
]


@pytest.mark.parametrize(
    "shared,pattern,flags", _SHAPES, ids=[f"{i}" for i in range(len(_SHAPES))]
)
def test_shared_regex_preserves_pattern_flags_and_captures(shared, pattern, flags):
    original = re.compile(pattern, flags)
    assert shared.pattern == original.pattern
    assert shared.flags == original.flags
    assert shared.groups == original.groups
    assert shared.groupindex == original.groupindex


def test_shared_shapes_are_not_compiled_in_consumers():
    root = Path(shared_utils.__file__).parent
    patterns = {pattern for _, pattern, _ in _SHAPES}
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
                and node.args[0].value in patterns
            ):
                duplicates.append(f"{path.relative_to(root)}:{node.lineno}")
    assert not duplicates, "Use the shared script shape: " + ", ".join(duplicates)
