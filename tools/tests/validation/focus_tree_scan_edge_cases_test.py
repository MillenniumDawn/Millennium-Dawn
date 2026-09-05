"""Parser and pool-worker edge cases in validate_focus_tree.

Focus files are parsed by brace matching, so an empty block (`focus = {}`), a
block that never balances, or a file that cannot be read has to fall through
quietly. A worker that raises takes the whole pool down and the check then
reports nothing at all.
"""

import pytest
import validate_focus_tree as V
from shared_utils import write_text_under

MISSING = "common/national_focus/gone.txt"


def _write(tmp_path, name, body):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    write_text_under(str(p), str(tmp_path), body)
    return str(p)


# ---------------------------------------------------------------------------
# Unreadable files
# ---------------------------------------------------------------------------


def test_read_mod_text_returns_empty_instead_of_raising(tmp_path):
    assert V._read_mod_text(str(tmp_path / MISSING), str(tmp_path)) == ""
    outside = str(tmp_path.parent / "outside.txt")
    assert V._read_mod_text(outside, str(tmp_path)) == ""


@pytest.mark.parametrize(
    "worker",
    [
        V._extract_focus_icons,
        V._extract_tech_bonuses,
        V._extract_pp_malus,
        V._extract_focus_search_filters,
    ],
)
def test_worker_returns_empty_for_an_unreadable_file(tmp_path, worker):
    assert worker((str(tmp_path / MISSING), str(tmp_path))) == []


def test_payload_workers_return_empty_for_an_unreadable_file(tmp_path):
    path = str(tmp_path / MISSING)
    assert V._extract_ai_guard_data((path, str(tmp_path), {}, frozenset())) == []
    assert V._extract_cross_country_fires((path, str(tmp_path), frozenset())) == []


def test_parse_focus_file_returns_an_empty_structure_for_an_unreadable_file(tmp_path):
    path = str(tmp_path / MISSING)
    assert V.parse_focus_file((path, str(tmp_path))) == {
        "filepath": path,
        "trees": [],
        "shared_defs": {},
    }


# ---------------------------------------------------------------------------
# Empty and malformed blocks
# ---------------------------------------------------------------------------


EMPTY_BLOCKS = """focus_tree = {}
shared_focus = {}
shared_focus = {
\tx = 0
}
shared_focus = {
\tid = TAG_shared_s
\tx = 0
\ty = 0
\tcost = 1
\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\tprerequisite = { }
}
focus_tree = {
\tid = test_tree
\tshared_focus = TAG_shared_s
\tfocus = {}
\tfocus = {
\t\tx = 0
\t}
\tfocus = {
\t\tid = TAG_focus_a
\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\t\tprerequisite = { }
\t\tcompletion_reward = {
\t\t\tadd_building_construction = {}
\t\t\tadd_tech_bonus = {}
\t\t}
\t\tai_will_do = {}
\t}
\tfocus = {
\t\tid = TAG_focus_b
\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\t\tcompletion_reward = {}
\t\tai_will_do = {
\t\t\tbase = 1
\t\t\tmodifier = {}
\t\t}
\t}
\tfocus = {
\t\tid = TAG_focus_c
\t\tsearch_filters = { FOCUS_FILTER_POLITICAL }
\t\tcompletion_reward = { add_political_power = 10 }
\t}
}
"""


def test_empty_blocks_and_id_less_focuses_are_skipped_by_the_parser(tmp_path):
    path = _write(tmp_path, "common/national_focus/test.txt", EMPTY_BLOCKS)
    parsed = V.parse_focus_file((path, str(tmp_path)))

    assert parsed["shared_defs"] == {
        "TAG_shared_s": {"line": 6, "filepath": path, "prereq_groups": []}
    }
    assert len(parsed["trees"]) == 1
    tree = parsed["trees"][0]
    assert [f[0] for f in tree["focuses"]] == [
        "TAG_focus_a",
        "TAG_focus_b",
        "TAG_focus_c",
    ]
    assert tree["shared_refs"] == {"TAG_shared_s"}
    assert all(f[2] == [] for f in tree["focuses"])


def test_empty_blocks_are_skipped_by_the_per_focus_workers(tmp_path):
    path = _write(tmp_path, "common/national_focus/test.txt", EMPTY_BLOCKS)
    args = (path, str(tmp_path))

    assert V._extract_focus_icons(args) == []
    assert V._extract_tech_bonuses(args) == []
    assert V._extract_pp_malus(args) == []
    assert V._extract_focus_search_filters(args) == []


def test_empty_reward_and_ai_will_do_blocks_yield_no_guard_facts(tmp_path):
    path = _write(tmp_path, "common/national_focus/test.txt", EMPTY_BLOCKS)
    data = V._extract_ai_guard_data((path, str(tmp_path), {}, frozenset()))

    assert [d["id"] for d in data] == [
        "TAG_shared_s",
        "TAG_focus_a",
        "TAG_focus_b",
        "TAG_focus_c",
    ]
    assert all(d["buildings"] == set() and d["guards"] == set() for d in data)
    assert all(d["has_cost"] is False for d in data)


CROSS_COUNTRY_EMPTY = """focus_tree = {
\tid = test_tree
\tcountry = {}
\tfocus = {
\t\tx = 0
\t}
\tfocus = {
\t\tid = TAG_focus_a
\t\tcompletion_reward = {
\t\t\tGER = { country_event = foo.1 }
\t\t}
\t}
}
"""


def test_cross_country_worker_handles_an_empty_country_block(tmp_path):
    """With no owner tag declared, a literal tag scope is still foreign."""
    path = _write(tmp_path, "common/national_focus/test.txt", CROSS_COUNTRY_EMPTY)
    data = V._extract_cross_country_fires((path, str(tmp_path), frozenset()))
    assert [d["id"] for d in data] == ["TAG_focus_a"]


# ---------------------------------------------------------------------------
# Block-label and effect_tooltip helpers
# ---------------------------------------------------------------------------


def test_anonymous_block_has_no_label():
    body = "color = { { 1 } }"
    label, opener = V._enclosing_block_label(body, body.index("1"))
    assert label is None
    assert body[opener] == "{"


def test_effect_tooltip_span_needs_a_body_inside_the_bounds():
    empty = "effect_tooltip = {}\nadd_political_power = -5\n"
    assert V._effect_tooltip_spans(empty, 0, len(empty)) == []

    overrun = "effect_tooltip = { add_political_power = -5 }"
    assert V._effect_tooltip_spans(overrun, 0, 20) == []


# ---------------------------------------------------------------------------
# Money-cost accounting
# ---------------------------------------------------------------------------


def _cost(body, money=frozenset()):
    return V._body_money_cost(body, money)


def test_mutating_treasury_change_by_a_variable_is_an_unknown_cost():
    body = (
        "set_temp_variable = { treasury_change = -4 }\n"
        "add_to_temp_variable = { treasury_change = extra_cost }\n"
        "modify_treasury_effect = yes\n"
    )
    assert _cost(body) == (0.0, True, True)


def test_apply_with_no_preceding_set_is_an_unknown_cost():
    """`treasury_change` is a temp var set elsewhere — the amount is unknowable."""
    assert _cost("modify_treasury_effect = yes\n") == (0.0, True, True)


def test_reading_treasury_change_is_not_a_write():
    """`check_variable` inspects the running value; it neither sets nor spends."""
    assert _cost("check_variable = { treasury_change = 0 }\n") == (0.0, False, False)


def test_modify_debt_effect_is_an_unknown_cost():
    assert _cost("modify_debt_effect = yes\n") == (0.0, True, True)


def test_modify_debt_effect_inside_a_preview_is_not_a_cost():
    body = "effect_tooltip = { modify_debt_effect = yes }\n"
    assert _cost(body) == (0.0, False, False)


def test_money_scripted_effect_found_after_unrelated_reward_keys():
    body = "add_political_power = 5\nspend_money_effect = yes\n"
    assert _cost(body, frozenset({"spend_money_effect"})) == (0.0, True, True)


def test_reward_with_no_money_key_costs_nothing():
    body = "add_political_power = 5\nadd_stability = 0.05\n"
    assert _cost(body, frozenset({"spend_money_effect"})) == (0.0, False, False)


# ---------------------------------------------------------------------------
# Scripted-effect parsing
# ---------------------------------------------------------------------------


def test_scripted_effect_parser_skips_empty_blocks():
    text = (
        "empty_effect = {}\n"
        "builder = {\n"
        "\tadd_building_construction = {}\n"
        "\tadd_building_construction = {\n"
        "\t\ttype = arms_factory\n"
        "\t}\n"
        "}\n"
    )
    bodies, staffable, money = V._parse_scripted_effect_file(text)

    assert "empty_effect" not in bodies
    assert staffable == {"builder": frozenset({"arms_factory"})}
    assert money == frozenset()


# ---------------------------------------------------------------------------
# Notification-event indexing
# ---------------------------------------------------------------------------


def test_flavor_only_bails_on_an_unbalanced_inert_block():
    """An option that cannot be parsed counts as carrying an outcome, so the
    cross-country tooltip check stays noisy rather than silently exempting it."""
    assert (
        V._is_flavor_only(["\n\tname = foo.1.a\n\tai_chance = { base = 10\n"]) is False
    )


STAFF_GUARD_UNDER_OR = """focus_tree = {
\tid = test_tree
\tfocus = {
\t\tid = TAG_focus_a
\t\tcompletion_reward = {
\t\t\tadd_building_construction = { type = arms_factory level = 1 }
\t\t}
\t\tai_will_do = {
\t\t\tbase = 1
\t\t\tmodifier = {
\t\t\t\tfactor = 0
\t\t\t\tOR = {
\t\t\t\t\tNOT = { can_staff_an_arms_industry = yes }
\t\t\t\t\thas_country_flag = TAG_flag
\t\t\t\t}
\t\t\t}
\t\t}
\t}
}
"""


def test_negated_staff_guard_under_or_is_not_a_veto(tmp_path):
    """An OR branch can be satisfied by something else, so the factor = 0 does
    not fire specifically on the staffing check."""
    path = _write(tmp_path, "common/national_focus/test.txt", STAFF_GUARD_UNDER_OR)
    data = V._extract_ai_guard_data((path, str(tmp_path), {}, frozenset()))

    assert data[0]["buildings"] == {"arms_factory"}
    assert data[0]["guards"] == set()


NOTIFICATION_EVENTS = """country_event = {}
country_event = {
\tis_triggered_only = yes
\toption = { name = noid.a }
\toption = { name = noid.b }
}
country_event = {
\tid = quoted.1
\tdesc = "option = { fake"
\toption = { name = quoted.1.a }
\toption = { name = quoted.1.b }
}
country_event = {
\tid = answerable.1
\toption = { name = answerable.1.a add_political_power = 5 }
\toption = { name = answerable.1.b add_stability = 0.05 }
}
country_event = {
\tid = unclosed.1
\toption = { name = unclosed.1.a add_political_power = 5 }
\toption = { name = unclosed.1.b add_stability = 0.05 }
"""


def test_notification_index_skips_unparseable_events(tmp_path):
    """An empty, id-less or never-closing block yields nothing; an option opener
    hidden in a quoted string aborts option parsing, so the event stays a
    notification."""
    _write(tmp_path, "events/Empty.txt", "")
    _write(tmp_path, "events/Ev.txt", NOTIFICATION_EVENTS)
    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)

    assert v._notification_event_ids() == frozenset({"quoted.1"})
