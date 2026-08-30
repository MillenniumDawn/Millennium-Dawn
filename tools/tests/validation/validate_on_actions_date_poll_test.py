"""Tests for deterministic date polling in pulse on-actions."""

from validate_on_actions import scan_deterministic_date_polls


def test_deterministic_monthly_date_poll_detected():
    text = """on_actions = {
	on_monthly_TAG = {
		effect = {
			if = {
				limit = { date > 2005.1.1 }
				country_event = historical.1
			}
		}
	}
}
"""

    assert scan_deterministic_date_polls(text, "common/on_actions/test.txt") == [
        ("historical.1", "on_monthly_TAG", 6, "common/on_actions/test.txt")
    ]


def test_deterministic_else_if_date_poll_detected():
    text = """on_actions = {
	on_monthly_TAG = {
		effect = {
			else_if = {
				limit = { date > 2005.1.1 }
				country_event = historical.1
			}
		}
	}
}
"""

    assert scan_deterministic_date_polls(text, "common/on_actions/test.txt") == [
        ("historical.1", "on_monthly_TAG", 6, "common/on_actions/test.txt")
    ]


def test_non_pulse_date_gate_ignored():
    text = """on_actions = {
	on_new_term_election = {
		effect = {
			if = {
				limit = { date > 2005.1.1 }
				country_event = election.1
			}
		}
	}
}
"""

    assert scan_deterministic_date_polls(text, "common/on_actions/test.txt") == []


def test_state_driven_date_poll_ignored():
    text = """on_actions = {
	on_monthly_AST = {
		effect = {
			if = {
				limit = { date > 2011.8.10 has_focus_tree = ruddgov_focus }
				country_event = state_driven.1
			}
		}
	}
}
"""

    assert scan_deterministic_date_polls(text, "common/on_actions/test.txt") == []


def test_custom_state_date_poll_ignored():
    text = """on_actions = {
	on_weekly_TAG = {
		effect = {
			if = {
				limit = { date > 2005.1.1 TAG_system_live = yes }
				country_event = state_driven.1
			}
		}
	}
}
"""

    assert scan_deterministic_date_polls(text, "common/on_actions/test.txt") == []


def test_static_dlc_date_poll_detected():
    text = """on_actions = {
	on_monthly_TAG = {
		effect = {
			if = {
				limit = { date > 2005.1.1 has_dlc = "Arms Against Tyranny" }
				country_event = historical.1
			}
		}
	}
}
"""

    assert scan_deterministic_date_polls(text, "common/on_actions/test.txt") == [
        ("historical.1", "on_monthly_TAG", 6, "common/on_actions/test.txt")
    ]


def test_chance_rolled_date_poll_ignored():
    text = """on_actions = {
	on_weekly_TAG = {
		effect = {
			if = {
				limit = { date > 2005.1.1 }
				random = {
					chance = 10
					country_event = flavor.1
				}
			}
		}
	}
}
"""

    assert scan_deterministic_date_polls(text, "common/on_actions/test.txt") == []


def test_weighted_random_list_date_poll_ignored():
    text = """on_actions = {
	on_monthly_TAG = {
		effect = {
			if = {
				limit = { date > 2005.1.1 }
				random_list = {
					50 = { country_event = flavor.1 }
					50 = { news_event = flavor.2 }
				}
			}
		}
	}
}
"""

    assert scan_deterministic_date_polls(text, "common/on_actions/test.txt") == []


def test_chance_roll_does_not_exempt_deterministic_sibling():
    text = """on_actions = {
	on_weekly_TAG = {
		effect = {
			if = {
				limit = { date > 2005.1.1 }
				random = {
					chance = 10
					country_event = flavor.1
				}
				if = {
					limit = { has_country_flag = ready }
					country_event = historical.1
				}
			}
		}
	}
}
"""

    assert scan_deterministic_date_polls(text, "common/on_actions/test.txt") == [
        ("historical.1", "on_weekly_TAG", 12, "common/on_actions/test.txt")
    ]
