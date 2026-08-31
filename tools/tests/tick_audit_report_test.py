"""Behavioural tests for tick_audit's report pipeline, call tree, and CLI.

A tiny synthetic mod (one on_actions file, one scripted_effects file, two
events files, one decisions file) is written under tmp_path and REPO_ROOT is
pointed at it, so every assertion below is about what the audit reports for a
known input rather than about the live mod.
"""

import json
import os
import sys

import pytest
import tick_audit as ta

ON_ACTIONS = """on_actions = {
	on_daily = {
		effect = {
			log = "daily tick"
			daily_shared_effect = yes
			country_event = { id = tick.1 days = 3 }
			country_event = { id = ghost.9 }
		}
	}
	on_weekly_USA = {
		effect = {
			weekly_usa_effect = yes
			news_event = tick.2
			random_events = {
				100 = 0
				10 = tick.2
				5 = tick.3
			}
		}
	}
	on_monthly = {
		effect = {
			placeholder_effect = yes
			events = { tick.4 }
		}
	}
}
"""

SCRIPTED_EFFECTS = """daily_shared_effect = {
	add_stability = 0.01
	nested_effect = yes
	country_event = { id = tick.5 }
}

nested_effect = {
	add_political_power = 1
	daily_shared_effect = yes
}

weekly_usa_effect = {
	set_variable = { usa_counter = 1 }
	country_event = { id = tick.4 }
	country_event = { id = tick.4 days = 5 }
	random_events = {
		20 = tick.3
		10 = tick.4
	}
}

placeholder_effect = {
	# nothing wired up yet
}

unused_effect = {
	add_manpower = 1
}
"""

EVENTS = """add_namespace = tick

country_event = {
	id = tick.1
	title = tick.1.t
	is_triggered_only = yes
	immediate = {
		country_event = { id = tick.1 days = 7 }
	}
	option = { name = tick.1.a }
}

news_event = {
	id = tick.2
	title = tick.2.t
	option = { name = tick.2.a }
}

country_event = {
	id = tick.3
	title = tick.3.t
	option = {
		name = tick.3.a
		country_event = { id = tick.3 days = 45 }
	}
}

country_event = {
	id = tick.4
	title = tick.4.t
	option = { name = tick.4.a }
}

country_event = {
	id = tick.5
	title = tick.5.t
	option = { name = tick.5.a }
}
"""

MALFORMED_EVENTS = """country_event = {
	title = nameless.t
	option = { name = nameless.a }
}

not_an_event = {
	value = 1
}
"""

DECISIONS = """tick_category = {
	daily_decision = {
		days_re_enable = 1
		fire_only_once = no
		complete_effect = {
			country_event = { id = tick.4 days = 28 }
		}
	}

	monthly_decision = {
		days_mission_timeout = 30
		days_remove = 60
	}

	variable_decision = {
		days_remove = ROOT.timer_var
	}

	plain_decision = {
		cost = 10
	}
}
"""


def _write_script(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


@pytest.fixture
def mod_root(tmp_path, monkeypatch):
    _write_script(tmp_path, "common/on_actions/hooks.txt", ON_ACTIONS)
    _write_script(tmp_path, "common/scripted_effects/effects.txt", SCRIPTED_EFFECTS)
    _write_script(tmp_path, "events/tick_events.txt", EVENTS)
    _write_script(tmp_path, "events/malformed.txt", MALFORMED_EVENTS)
    _write_script(tmp_path, "common/decisions/timers.txt", DECISIONS)
    _write_script(tmp_path, "common/on_actions/notes.md", "not a script file\n")
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    return tmp_path


@pytest.fixture
def report(mod_root):
    return ta.build_report()


# --- indexing ---------------------------------------------------------------


def test_index_events_skips_idless_and_non_event_blocks(mod_root):
    events = ta.index_events()
    assert sorted(events) == ["tick.1", "tick.2", "tick.3", "tick.4", "tick.5"]
    assert events["tick.2"]["type"] == "news_event"
    assert events["tick.1"]["file"] == "events/tick_events.txt"
    assert events["tick.1"]["line"] == 3


def test_index_scripted_effects_and_locations(mod_root):
    effects = ta.index_scripted_effects()
    assert sorted(effects) == [
        "daily_shared_effect",
        "nested_effect",
        "placeholder_effect",
        "unused_effect",
        "weekly_usa_effect",
    ]
    locations = ta.index_effect_locations()
    assert locations["nested_effect"] == "common/scripted_effects/effects.txt:7"


def test_empty_repo_reports_zero_work(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    assert list(ta._iter_txt("common/scripted_effects")) == []

    empty = ta.build_report()
    assert empty["hooks"] == []
    assert empty["per_country"] == []
    assert empty["global_work_by_cadence"] == {"daily": 0, "weekly": 0, "monthly": 0}

    assert ta.main(["--no-color"]) == 0
    assert "Indexed 0 scripted_effects, 0 events." in capsys.readouterr().out


@pytest.mark.skipif(
    sys.platform == "win32", reason="symlink creation needs privileges on Windows"
)
def test_iter_txt_skips_unreadable_files(tmp_path, monkeypatch):
    _write_script(
        tmp_path,
        "common/scripted_effects/good.txt",
        "good_effect = { add_stability = 0.01 }\n",
    )
    os.symlink(
        "missing_target.txt",
        str(tmp_path / "common" / "scripted_effects" / "dangling.txt"),
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    assert sorted(ta.index_scripted_effects()) == ["good_effect"]


# --- hook collection (the accuracy contract) --------------------------------


def test_collect_hooks_attributes_only_direct_fires(mod_root):
    effects = ta.index_scripted_effects()
    events = ta.index_events()
    hooks = {
        h["scope"] + "/" + h["cadence"]: h
        for h in ta.collect_hooks(effects, events, {})
    }

    daily = hooks["GLOBAL/daily"]
    assert daily["events_direct"] == ["tick.1"]
    # tick.5 fires deep inside daily_shared_effect, so it is work but not a fire.
    assert "tick.5" not in daily["events_direct"]
    # ghost.9 has no definition anywhere, so it is not reported at all.
    assert "ghost.9" not in daily["events_direct"]
    assert daily["reached_effects"] == ["daily_shared_effect", "nested_effect"]
    assert daily["call_edges"] == 3
    assert daily["file"] == "common/on_actions/hooks.txt"
    assert daily["line"] == 2

    weekly = hooks["USA/weekly"]
    assert weekly["events_direct"] == ["tick.2"]
    assert weekly["events_random"] == ["tick.2", "tick.3"]

    monthly = hooks["GLOBAL/monthly"]
    assert monthly["events_direct"] == ["tick.4"]


def test_collect_hooks_skips_unclosed_hook_blocks(tmp_path, monkeypatch):
    _write_script(
        tmp_path,
        "common/on_actions/hooks.txt",
        "on_daily = { add_stability = 0.01 }\non_weekly = { add_political_power = 1\n",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    hooks = ta.collect_hooks({}, {}, {})
    assert [h["cadence"] for h in hooks] == ["daily"]


def test_hook_work_units_include_reached_effects(mod_root):
    effects = ta.index_scripted_effects()
    hooks = ta.collect_hooks(effects, ta.index_events(), {})
    daily = next(h for h in hooks if h["cadence"] == "daily")
    nested_ops = ta.count_statements(effects["nested_effect"])
    assert nested_ops > 0
    assert daily["work_units"] > nested_ops
    assert daily["work_units"] == 14


# --- timed decisions --------------------------------------------------------


def test_collect_timed_decisions_buckets_and_ignores_nested_days(mod_root):
    timed = {d["name"]: d for d in ta.collect_timed_decisions()}
    assert sorted(timed) == ["daily_decision", "monthly_decision", "variable_decision"]

    assert timed["daily_decision"]["bucket"] == "daily"
    assert timed["daily_decision"]["timer_field"] == "days_re_enable"
    assert timed["daily_decision"]["recurring"] is True

    # Shortest literal timer wins, and fire_only_once defaults to non-recurring.
    assert timed["monthly_decision"]["timer_field"] == "days_mission_timeout"
    assert timed["monthly_decision"]["days"] == 30
    assert timed["monthly_decision"]["recurring"] is False

    assert timed["variable_decision"]["bucket"] == "variable"
    assert timed["variable_decision"]["days"] is None
    assert timed["variable_decision"]["timer_value"] == "ROOT.timer_var"

    assert timed["daily_decision"]["file"] == "common/decisions/timers.txt"
    assert timed["daily_decision"]["line"] == 2


# --- report aggregation -----------------------------------------------------


def test_build_report_cadence_summary(report):
    assert report["totals"] == {
        "scripted_effects_indexed": 5,
        "events_indexed": 5,
    }

    daily = report["cadences"]["daily"]
    assert daily["global_hooks"] == 1
    assert daily["per_country_hooks"] == 0
    assert daily["countries_with_own_hook"] == []
    assert daily["global_work_units"] > 0

    weekly = report["cadences"]["weekly"]
    assert weekly["global_hooks"] == 0
    assert weekly["per_country_hooks"] == 1
    assert weekly["countries_with_own_hook"] == ["USA"]
    # No GLOBAL weekly hook exists, so nothing is charged to every country.
    assert weekly["global_work_units"] == 0
    assert weekly["events_random_pool"] == ["tick.2", "tick.3"]

    assert [d["name"] for d in daily["timed_decisions"]] == ["daily_decision"]
    assert [e["id"] for e in weekly["event_loops"]] == ["tick.1"]


def test_build_report_per_country_adds_global_work(report):
    rows = {row["tag"]: row for row in report["per_country"]}
    assert sorted(rows) == ["USA"]
    usa = rows["USA"]
    globals_ = report["global_work_by_cadence"]
    assert usa["own_hooks"] == 1
    assert usa["by_cadence"]["daily"] == globals_["daily"]
    assert usa["by_cadence"]["weekly"] > globals_["weekly"]
    assert usa["total_work_units"] == sum(usa["by_cadence"].values())


def test_build_report_event_fires_record_every_hook(report):
    fires = report["event_fires"]
    assert sorted(fires) == ["tick.1", "tick.2", "tick.3", "tick.4"]
    assert fires["tick.2"]["type"] == "news_event"
    assert fires["tick.2"]["def"] == "events/tick_events.txt:13"
    kinds = sorted(f["kind"] for f in fires["tick.2"]["fired_by"])
    assert kinds == ["direct", "random"]
    assert {f["scope"] for f in fires["tick.2"]["fired_by"]} == {"USA"}


def test_build_report_event_loops_split_auto_from_player(report):
    loops = {e["id"]: e for e in report["event_loops"]}
    assert loops["tick.1"]["trigger"] == "immediate"
    assert loops["tick.1"]["bucket"] == "weekly"
    assert loops["tick.1"]["days"] == 7
    # A self-fire reachable only from an option is player-driven, never a tick.
    assert loops["tick.3"]["trigger"] == "option"
    assert loops["tick.3"]["bucket"] == "player"


def test_build_report_tag_filter_keeps_global_hooks(mod_root):
    focused = ta.build_report(tag_filter="USA")
    assert focused["focus_tag"] == "USA"
    assert {h["scope"] for h in focused["focus_hooks"]} == {"GLOBAL", "USA"}

    other = ta.build_report(tag_filter="GER")
    assert {h["scope"] for h in other["focus_hooks"]} == {"GLOBAL"}


# --- text rendering ---------------------------------------------------------


def test_render_text_summarizes_every_cadence(report):
    text = ta.render_text(report, top=20, cadence_filter=None, use_colors=False)
    assert "MILLENNIUM DAWN - RECURRING TICK AUDIT" in text
    assert "Indexed 5 scripted_effects, 5 events." in text
    for header in ("== DAILY", "== WEEKLY", "== MONTHLY"):
        assert header in text
    assert "HEAVIEST COUNTRIES" in text
    assert "  USA   " in text
    assert (
        "Timed decisions: 1 daily, 0 weekly, 1 monthly, 1 variable, 0 other"
        "  (total 3; 1 recurring / fire_only_once=no)"
    ) in text
    assert (
        "Self-rescheduling event loops (immediate=auto): "
        "0 daily, 1 weekly, 0 monthly, 0 other, 1 player  (total 2; 1 auto)"
    ) in text
    assert "\033[" not in text


def test_render_text_cadence_filter_drops_country_table(report):
    text = ta.render_text(report, top=20, cadence_filter="weekly", use_colors=False)
    assert "== WEEKLY" in text
    assert "== DAILY" not in text
    assert "HEAVIEST COUNTRIES" not in text
    # Weekly has a loop but no weekly-bucketed timed decision.
    assert "Self-rescheduling event loops:" in text
    assert "Timed decisions (days~7):" not in text


def test_render_text_top_limits_country_rows(report):
    text = ta.render_text(report, top=0, cadence_filter=None, use_colors=False)
    assert "HEAVIEST COUNTRIES" in text
    assert "  USA   " not in text


def test_render_text_colors_wrap_values(report):
    text = ta.render_text(report, top=20, cadence_filter=None, use_colors=True)
    assert ta.Colors.BOLD in text
    assert ta.Colors.ENDC in text


# --- list rendering ---------------------------------------------------------


def test_render_list_all_sections(report):
    text = ta.render_list(report, ["all"], None, None, 50, False)
    for header in (
        "== HOOKS (recurring on_action blocks)",
        "== EVENTS fired directly by recurring hooks",
        "== TIMED DECISIONS (real timer fields)",
        "== SELF-RESCHEDULING EVENT LOOPS",
    ):
        assert header in text
    assert "[daily  ] GLOBAL" in text
    assert "common/on_actions/hooks.txt:2" in text
    assert "tick.2 [weekly] by USA (direct,random)" in text
    assert "variable_decision  days_remove=ROOT.timer_var [variable]" in text
    assert "daily_decision  days_re_enable=1 [daily] recurring" in text
    assert "tick.3  option days=45 [player]" in text


def test_render_list_tag_filter_hides_other_countries(report):
    text = ta.render_list(report, ["hooks", "events"], None, "GER", 50, False)
    assert "GLOBAL" in text
    assert "USA" not in text
    assert "tick.2" not in text
    assert "tick.1" in text


def test_render_list_cadence_filter_applies_to_buckets(report):
    text = ta.render_list(report, ["decisions", "loops"], "monthly", None, 50, False)
    assert "monthly_decision" in text
    assert "daily_decision" not in text
    assert "SELF-RESCHEDULING EVENT LOOPS" in text
    assert "(none)" in text


def test_render_list_limit_reports_truncation(report):
    text = ta.render_list(report, ["hooks"], None, None, 1, False)
    assert (
        text.count("[daily  ]") + text.count("[weekly ]") + text.count("[monthly]") == 1
    )
    assert "... 2 more (raise --limit)" in text

    unlimited = ta.render_list(report, ["hooks"], None, None, 0, False)
    assert "raise --limit" not in unlimited


# --- call tree and flamegraph ----------------------------------------------


def test_build_call_tree_shapes_cadences_and_marks_recursion(mod_root):
    effects = ta.index_scripted_effects()
    events = ta.index_events()
    root = ta.build_call_tree(effects, events, ta.index_effect_locations())

    assert [c["name"] for c in root["children"]] == ["DAILY", "WEEKLY", "MONTHLY"]
    assert root["total"] == sum(c["total"] for c in root["children"])
    assert root["ops"] == 0

    daily = root["children"][0]
    hook = daily["children"][0]
    assert hook["name"] == "on_daily"
    assert hook["scope"] == "GLOBAL"
    assert hook["file"] == "common/on_actions/hooks.txt:2"
    assert hook["total"] == hook["ops"] + sum(c["total"] for c in hook["children"])

    names = {c["name"]: c for c in hook["children"]}
    assert names["tick.1"]["kind"] == "event"
    assert "ghost.9" not in names
    shared = names["daily_shared_effect"]
    nested = next(c for c in shared["children"] if c["name"] == "nested_effect")
    back_edge = next(
        c for c in nested["children"] if c["name"] == "daily_shared_effect"
    )
    assert back_edge["recursive"] is True
    assert back_edge["children"] == []

    weekly_hook = root["children"][1]["children"][0]
    assert weekly_hook["name"] == "on_weekly_USA"
    kinds = {c["name"]: c["kind"] for c in weekly_hook["children"]}
    assert kinds["tick.2"] == "event"
    assert kinds["tick.3"] == "random_event"

    # An event fired twice, then again from a random pool, is one leaf.
    weekly_effect = next(
        c for c in weekly_hook["children"] if c["name"] == "weekly_usa_effect"
    )
    leaves = [(c["name"], c["kind"]) for c in weekly_effect["children"]]
    assert sorted(leaves) == [("tick.3", "random_event"), ("tick.4", "event")]


def test_build_call_tree_children_sorted_by_total(mod_root):
    root = ta.build_call_tree(
        ta.index_scripted_effects(), ta.index_events(), ta.index_effect_locations()
    )
    for cadence in root["children"]:
        for hook in cadence["children"]:
            totals = [c["total"] for c in hook["children"]]
            assert totals == sorted(totals, reverse=True)


def test_build_call_tree_budget_truncates_deep_chains(mod_root):
    root = ta.build_call_tree(
        ta.index_scripted_effects(),
        ta.index_events(),
        ta.index_effect_locations(),
        max_depth=1,
    )
    hook = root["children"][0]["children"][0]
    shared = next(c for c in hook["children"] if c["name"] == "daily_shared_effect")
    assert shared["truncated"] is True
    assert shared["children"] == []

    # A stub with no statements is cut off silently, not flagged as truncated.
    monthly_hook = root["children"][2]["children"][0]
    stub = next(
        c for c in monthly_hook["children"] if c["name"] == "placeholder_effect"
    )
    assert "truncated" not in stub
    assert stub["total"] == 0


def test_write_flamegraph_substitutes_every_placeholder(mod_root, tmp_path):
    root = ta.build_call_tree(
        ta.index_scripted_effects(), ta.index_events(), ta.index_effect_locations()
    )
    out = tmp_path / "flame.html"
    ta.write_flamegraph(root, str(out), str(mod_root))
    html = out.read_text(encoding="utf-8")

    assert "/*DATA*/null" not in html
    assert "__REPO__" not in html
    assert "__TOTAL__" not in html
    assert "TOTAL=" + str(root["total"]) + ";" in html
    assert 'REPO="' + str(mod_root).replace("\\", "/") + '"' in html
    assert "on_weekly_USA" in html
    assert html.startswith("<!doctype html>")


# --- expansion helpers ------------------------------------------------------


def test_expand_effect_unknown_name_is_empty():
    assert ta.expand_effect("no_such_effect", {}, {}, set()) == (set(), 0)


def test_expand_effect_memoizes_repeat_lookups():
    effects = {"a": "b = yes", "b": "c = yes", "c": "add_stability = 0.01"}
    cache = {}
    first = ta.expand_effect("a", effects, cache, set())
    assert first == ({"b", "c"}, 2)
    assert "b" in cache
    assert ta.expand_effect("a", effects, cache, set()) == first


def test_expand_effect_survives_cycles():
    effects = {"loop_a": "loop_b = yes", "loop_b": "loop_a = yes"}
    assert ta.expand_effect("loop_a", effects, {}, set()) == ({"loop_a", "loop_b"}, 2)


def test_expand_effect_bounds_recursion_depth():
    effects = {
        "chain_%d" % i: "chain_%d = yes" % (i + 1) for i in range(ta.MAX_DEPTH + 20)
    }
    reached, edges = ta.expand_effect("chain_0", effects, {}, set())
    assert len(reached) == ta.MAX_DEPTH + 1
    assert edges == ta.MAX_DEPTH + 1


# --- parser edge cases ------------------------------------------------------


def test_count_statements_counts_effects_and_checks():
    assert ta.count_statements("limit = { has_war = yes }\nadd_stability = 0.01") == 3


def test_parse_int_rejects_non_numeric():
    assert ta._parse_int("12") == 12
    assert ta._parse_int("ROOT.timer_var") is None
    assert ta._parse_int(None) is None


def test_top_level_blocks_stops_on_unclosed_block():
    assert list(ta._top_level_blocks("cat = { decision = { days_remove = 7 }")) == []


def test_extract_direct_event_fires_skips_unclosed_and_idless_blocks():
    body = (
        "country_event = { days = 3 }\n"
        "news_event = { id = ok.1 }\n"
        "state_event = { id = broken.1\n"
    )
    assert ta.extract_direct_event_fires(body) == [("ok.1", None)]


def test_extract_random_events_ignores_unclosed_pool():
    assert ta.extract_random_events("random_events = { 10 = pool.1") == []


def test_extract_plain_events_block_reads_ids():
    body = "events = { alpha.1 beta.2 }\nevents = { gamma.3\n"
    assert ta.extract_plain_events_block(body) == ["alpha.1", "beta.2"]


def test_named_subblock_missing_key_is_empty():
    assert ta._named_subblock("option = { name = a }", "immediate") == ""
    assert ta._named_subblock("immediate = { x = 1", "immediate") == ""


# --- CLI --------------------------------------------------------------------


def test_main_default_prints_text_report(mod_root, capsys):
    assert ta.main([]) == 0
    out = capsys.readouterr().out
    assert "MILLENNIUM DAWN - RECURRING TICK AUDIT" in out
    assert "HEAVIEST COUNTRIES" in out


def test_main_cadence_and_top_flags(mod_root, capsys):
    assert ta.main(["--cadence", "monthly", "--top", "1", "--no-color"]) == 0
    out = capsys.readouterr().out
    assert "== MONTHLY" in out
    assert "== DAILY" not in out


def test_main_list_with_tag_and_limit(mod_root, capsys):
    assert ta.main(["--list", "hooks", "--tag", "USA", "--limit", "0"]) == 0
    out = capsys.readouterr().out
    assert "== HOOKS" in out
    assert "USA" in out
    assert "HEAVIEST COUNTRIES" not in out


def test_main_json_writes_full_report(mod_root, tmp_path, capsys):
    out_path = tmp_path / "audit.json"
    assert ta.main(["--json", str(out_path)]) == 0
    assert "Wrote " + str(out_path) in capsys.readouterr().out
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["totals"]["scripted_effects_indexed"] == 5
    assert [row["tag"] for row in payload["per_country"]] == ["USA"]


def test_main_flamegraph_and_tree_only_skip_the_text_report(mod_root, tmp_path, capsys):
    html = tmp_path / "flame.html"
    tree = tmp_path / "tree.json"
    assert ta.main(["--flamegraph", str(html), "--tree", str(tree)]) == 0
    out = capsys.readouterr().out
    assert "Wrote " + str(tree) in out
    assert "total ops)" in out
    assert "MILLENNIUM DAWN - RECURRING TICK AUDIT" not in out
    assert json.loads(tree.read_text(encoding="utf-8"))["kind"] == "root"
    assert html.exists()


def test_main_tree_only_skips_the_text_report(mod_root, tmp_path, capsys):
    tree = tmp_path / "tree.json"
    assert ta.main(["--tree", str(tree)]) == 0
    out = capsys.readouterr().out
    assert "Wrote " + str(tree) in out
    assert "MILLENNIUM DAWN - RECURRING TICK AUDIT" not in out
    assert json.loads(tree.read_text(encoding="utf-8"))["kind"] == "root"


def test_main_flamegraph_with_list_still_renders_the_report(mod_root, tmp_path, capsys):
    html = tmp_path / "flame.html"
    assert ta.main(["--flamegraph", str(html), "--list", "loops"]) == 0
    out = capsys.readouterr().out
    assert "== SELF-RESCHEDULING EVENT LOOPS" in out
    assert html.exists()
