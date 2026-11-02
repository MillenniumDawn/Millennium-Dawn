"""Cuba's focuses must remain siblings with their own reward logs."""

import re

from check_common_mistakes import _check_focus_log_id
from equipment_module_slots import _iter_blocks, blank_comments
from shared.paths import REPO_ROOT


def test_cuba_focus_blocks_and_logs():
    text = blank_comments(
        (REPO_ROOT / "common/national_focus/05_cuba.txt").read_text(encoding="utf-8")
    )
    trees = list(_iter_blocks(text, 0, len(text)))
    assert len(trees) == 1
    name, lo, hi, _ = trees[0]
    assert name == "focus_tree"
    assert hi == text.rfind("}")
    focuses = [
        text[blo:bhi]
        for key, blo, bhi, _ in _iter_blocks(text, lo, hi)
        if key == "focus"
    ]
    assert len(focuses) == len(re.findall(r"^\s*focus\s*=\s*\{", text, re.MULTILINE))
    assert not _check_focus_log_id(text.splitlines(keepends=True))
