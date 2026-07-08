"""Tests for the cross-country event tooltip check in validate_focus_tree
(AGENTS.md "Cross-country event tooltips").

A completion_reward that fires a country_event into another nation's scope
should carry custom_effect_tooltip = TT_IF_THEY_ACCEPT. Fires to self (bare,
ROOT/THIS, or the owner's own tag) are not flagged.
"""

from validate_focus_tree import (
    _country_event_target_is_foreign,
    _extract_cross_country_fires,
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


def _ids(tmp_path, reward):
    fpath = _write_focus_file(tmp_path, TREE_TEMPLATE.format(reward=reward))
    return {d["id"] for d in _extract_cross_country_fires((str(fpath), str(tmp_path)))}


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
    body = "hidden_effect = { FRA = { country_event = x.1 } }"
    assert _country_event_target_is_foreign(body, body.index("country_event"), OWNER)


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


def test_worker_ignores_bare_self_fire(tmp_path):
    assert _ids(tmp_path, "country_event = x.1") == set()
