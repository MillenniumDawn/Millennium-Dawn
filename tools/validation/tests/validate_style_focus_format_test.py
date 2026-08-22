"""Tests for `validate_style.py` focus ID format exemptions."""

import validate_style as V


def test_shared_focus_prefixes_are_exempt():
    assert V._has_focus_format("USoE_focus_x")
    assert V._has_focus_format("POTEF_focus_x")
    assert V._has_focus_format("AFRICAN_UNION_focus_x")
    assert V._has_focus_format("GENERIC_focus_x")
    assert V._has_focus_format("EH_whole_new_dawn")


def test_tag_focus_format_still_required():
    assert V._has_focus_format("FIJ_focus_economic_relief_fund")
    assert not V._has_focus_format("fiji_focus_economic_relief_fund")


def test_dummy_focus_placeholder_is_exempt():
    assert V._has_focus_format("dummy_focus")
