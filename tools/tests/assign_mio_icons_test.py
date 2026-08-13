"""Behavior tests for MIO trait modifier selection."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

from assign_mio_icons import winning_modifier  # noqa: E402


def test_winning_modifier_uses_absolute_value():
    block = """
    equipment_bonus = {
        soft_attack = -0.4
        hard_attack = 0.6
    }
    production_bonus = {
        production_speed = 0.5
    }
    """

    assert winning_modifier(block) == "hard_attack"


def test_winning_modifier_returns_none_without_supported_modifiers():
    assert winning_modifier("limit_to_equipment_type = tank") is None
