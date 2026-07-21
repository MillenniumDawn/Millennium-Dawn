"""Tests for the cross-country event tooltip check in validate_focus_tree
(AGENTS.md "Cross-country event tooltips").

A completion_reward that fires a country_event into another nation's scope
should carry custom_effect_tooltip = TT_IF_THEY_ACCEPT. Fires to self (bare,
ROOT/THIS, or the owner's own tag) are not flagged, and neither are fires at an
event the target cannot answer.
"""

import validate_focus_tree as vft
from validate_focus_tree import (
    _country_event_target_is_foreign,
    _extract_cross_country_fires,
    _is_tag_routed,
)

OWNER = frozenset({"BUL"})


def _write_focus_file(tmp_path, content):
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True, exist_ok=True)
    fpath = nf_dir / "test.txt"
    fpath.write_text(content, encoding="utf-8")
    return fpath


TREE_TEMPLATE = """focus_tree = {{
	id = test_tree
	country = {{
		factor = 0
		modifier = {{
			add = 20
			tag = BUL
		}}
	}}
	focus = {{
		id = BUL_focus_a
		x = 0
		y = 0
		cost = 1
		completion_reward = {{
			{reward}
		}}
	}}
}}
"""


def _ids(tmp_path, reward, notifications=frozenset()):
    fpath = _write_focus_file(tmp_path, TREE_TEMPLATE.format(reward=reward))
    return {
        d["id"]
        for d in _extract_cross_country_fires(
            (str(fpath), str(tmp_path), notifications)
        )
    }


# --- classifier unit cases ---


def test_literal_foreign_tag_is_foreign():
    body = "GER = { country_event = { id = x.1 } }"
    assert _country_event_target_is_foreign(body, body.index("country_event"), OWNER)


def test_bare_fire_is_self():
    body = "country_event = x.1"
    assert not _country_event_target_is_foreign(
        body, body.index("country_event"), OWNER
    )


def test_root_scope_is_self():
    body = "ROOT = { country_event = x.1 }"
    assert not _country_event_target_is_foreign(
        body, body.index("country_event"), OWNER
    )


def test_owner_tag_is_self():
    body = "BUL = { country_event = x.1 }"
    assert not _country_event_target_is_foreign(
        body, body.index("country_event"), OWNER
    )


def test_if_wrapped_foreign_fire():
    body = "if = { limit = { country_exists = TUR } TUR = { country_event = x.1 } }"
    assert _country_event_target_is_foreign(body, body.index("country_event"), OWNER)


def test_control_flow_wrapper_walked_through():
    body = "random = { FRA = { country_event = x.1 } }"
    assert _country_event_target_is_foreign(body, body.index("country_event"), OWNER)


def test_hidden_effect_swallows_the_tooltip():
    body = "hidden_effect = { FRA = { country_event = x.1 } }"
    assert not _country_event_target_is_foreign(
        body, body.index("country_event"), OWNER
    )


def test_hidden_effect_above_a_wrapper_still_wins():
    body = (
        "hidden_effect = { if = { limit = { x = y } FRA = { country_event = x.1 } } }"
    )
    assert not _country_event_target_is_foreign(
        body, body.index("country_event"), OWNER
    )


def test_country_iterator_is_foreign():
    body = "every_other_country = { country_event = x.1 }"
    assert _country_event_target_is_foreign(body, body.index("country_event"), OWNER)


def test_event_target_scope_is_foreign():
    body = "event_target:foe = { country_event = x.1 }"
    assert _country_event_target_is_foreign(body, body.index("country_event"), OWNER)


def test_logic_keyword_not_treated_as_tag():
    body = "NOT = { country_event = x.1 }"
    assert not _country_event_target_is_foreign(
        body, body.index("country_event"), OWNER
    )


# --- worker integration cases ---


def test_worker_flags_foreign_fire_without_tooltip(tmp_path):
    assert _ids(tmp_path, "GER = { country_event = { id = x.1 days = 1 } }") == {
        "BUL_focus_a"
    }


def test_worker_clears_fire_with_tooltip(tmp_path):
    reward = (
        "GER = { country_event = { id = x.1 days = 1 } }\n"
        "\t\t\tcustom_effect_tooltip = TT_IF_THEY_ACCEPT"
    )
    assert _ids(tmp_path, reward) == set()


def test_worker_ignores_self_owner_tag(tmp_path):
    assert _ids(tmp_path, "BUL = { country_event = x.1 }") == set()


def test_worker_reads_owner_from_original_tag(tmp_path):
    tree = TREE_TEMPLATE.replace("tag = BUL", "original_tag = BUL").format(
        reward="BUL = { country_event = x.1 }"
    )
    fpath = _write_focus_file(tmp_path, tree)
    assert _extract_cross_country_fires((str(fpath), str(tmp_path), frozenset())) == []


def test_worker_ignores_bare_self_fire(tmp_path):
    assert _ids(tmp_path, "country_event = x.1") == set()


def test_worker_skips_notification_target(tmp_path):
    reward = "GER = { country_event = { id = x.1 days = 1 } }"
    assert _ids(tmp_path, reward, notifications=frozenset({"x.1"})) == set()


def test_worker_skips_bare_notification_target(tmp_path):
    assert _ids(tmp_path, "GER = { country_event = x.1 }", frozenset({"x.1"})) == set()


def test_worker_flags_unknown_target(tmp_path):
    reward = "GER = { country_event = { id = x.1 days = 1 } }"
    assert _ids(tmp_path, reward, notifications=frozenset({"other.9"})) == {
        "BUL_focus_a"
    }


# --- notification index ---

EVENTS = """country_event = {
	id = offer.1
	option = { name = offer.1.a }
	option = { name = offer.1.b }
}

country_event = {
	id = notice.1
	option = { name = notice.1.a }
}

country_event = {
	id = quiet.1
	hidden = yes
	option = { name = quiet.1.a }
	option = { name = quiet.1.b }
}

country_event = {
	id = fires_others.1
	option = {
		name = fires_others.1.a
		GER = { country_event = { id = nested.1 days = 1 } }
	}
	option = { name = fires_others.1.b }
}

country_event = {
	id = routed.1
	option = {
		name = routed.1.a
		trigger = { original_tag = UKR }
	}
	option = {
		name = routed.1.b
		trigger = { original_tag = SOV }
	}
}

country_event = {
	id = routed_shared.1
	option = {
		name = routed_shared.1.a
		trigger = { tag = UKR }
	}
	option = {
		name = routed_shared.1.b
		trigger = { OR = { tag = UKR tag = SOV } }
	}
}

country_event = {
	id = routed_negated.1
	option = {
		name = routed_negated.1.a
		trigger = { tag = UKR }
	}
	option = {
		name = routed_negated.1.b
		trigger = { NOT = { tag = UKR } }
	}
}

country_event = {
	id = half_routed.1
	option = {
		name = half_routed.1.a
		trigger = { tag = UKR }
	}
	option = { name = half_routed.1.b }
}
"""


def _notifications(tmp_path):
    ev_dir = tmp_path / "events"
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / "test_events.txt").write_text(EVENTS, encoding="utf-8")
    return vft.Validator(str(tmp_path))._notification_event_ids()


def test_notification_index_marks_single_option(tmp_path):
    assert "notice.1" in _notifications(tmp_path)


def test_notification_index_marks_hidden(tmp_path):
    assert "quiet.1" in _notifications(tmp_path)


def test_notification_index_skips_answerable_event(tmp_path):
    assert "offer.1" not in _notifications(tmp_path)


def test_notification_index_ignores_nested_fire(tmp_path):
    """A `country_event = { id = x }` inside an option is a fire, not a
    definition — indexing it would mark x as an optionless notification."""
    found = _notifications(tmp_path)
    assert "nested.1" not in found
    assert "fires_others.1" not in found


# --- tag-routed options ---


def test_notification_index_marks_tag_routed(tmp_path):
    """Two options, one per recipient tag: nobody gets a choice."""
    assert "routed.1" in _notifications(tmp_path)


def test_tag_routed_needs_disjoint_tags():
    """UKR matches both options, so UKR really does choose."""
    assert not _is_tag_routed(
        ["trigger = { tag = UKR }", "trigger = { OR = { tag = UKR tag = SOV } }"]
    )


def test_tag_routed_bails_on_negation():
    """`NOT = { tag = UKR }` is not a tag claim — stay noisy rather than guess."""
    assert not _is_tag_routed(
        ["trigger = { tag = UKR }", "trigger = { NOT = { tag = UKR } }"]
    )


def test_tag_routed_needs_every_option_gated():
    assert not _is_tag_routed(["trigger = { tag = UKR }", "name = x"])


def test_tag_routed_ignores_single_option():
    assert not _is_tag_routed(["trigger = { tag = UKR }"])


def test_notification_index_skips_partly_routed(tmp_path):
    found = _notifications(tmp_path)
    assert "routed_shared.1" not in found
    assert "routed_negated.1" not in found
    assert "half_routed.1" not in found
