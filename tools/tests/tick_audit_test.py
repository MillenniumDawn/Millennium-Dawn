"""Unit tests for tick_audit's parsing and accuracy guarantees.

These cover the pure helpers where correctness lives — brace-aware block
extraction, direct-only event attribution, decision-timer detection that
ignores nested `days`, and the immediate-vs-option loop classification. They do
not touch the live mod, so they stay fast and deterministic.
"""

import pytest

from tools.analysis import tick_audit as ta

# --- brace-depth field reading ---------------------------------------------


def test_depth0_assignments_ignores_nested():
    body = """
        days_re_enable = 30
        timeout_effect = {
            set_country_flag = { flag = x value = 1 days = 28 }
            country_event = { id = foo.1 days = 5 }
        }
        fire_only_once = no
    """
    fields = ta._depth0_assignments(body)
    assert fields["days_re_enable"] == "30"
    assert fields["fire_only_once"] == "no"
    # The nested `days = 28` / `days = 5` must NOT surface as a decision field.
    assert "days" not in fields


def test_depth0_assignments_reads_variable_timer():
    fields = ta._depth0_assignments("days_mission_timeout = ROOT.battery_park_time")
    assert fields["days_mission_timeout"] == "ROOT.battery_park_time"


# --- event-fire extraction --------------------------------------------------


def test_extract_direct_event_fires_block_and_bare():
    body = """
        country_event = { id = econvent.1 days = 3 }
        news_event = germany.5
    """
    fires = dict(ta.extract_direct_event_fires(body))
    assert fires["econvent.1"] == 3
    assert fires["germany.5"] is None


def test_random_events_pool_ids():
    body = """
        random_events = {
            1500 = 0
            25 = econvent.1
            10 = econvent.4
        }
    """
    assert ta.extract_random_events(body) == ["econvent.1", "econvent.4"]


def test_scripted_calls_only_known_names():
    effects = {"recalculate_party": "", "update_mafia_strength": ""}
    body = "recalculate_party = yes\n add_stability = 0.1\n update_mafia_strength = yes"
    assert ta.extract_scripted_calls(body, effects) == {
        "recalculate_party",
        "update_mafia_strength",
    }


# --- top-level block parsing ------------------------------------------------


def test_top_level_blocks_depth0_only():
    text = """
    cat = {
        decision_a = { days_remove = 7 }
        decision_b = { available = { always = yes } }
    }
    """
    names = [n for n, _b, _s in ta._top_level_blocks(text)]
    assert names == ["cat"]  # nested decisions are not depth 0


# --- decision timers (accuracy: real fields, not nested days) ---------------


def test_timed_decision_bucketing():
    assert ta.bucket_for_days(1) == "daily"
    assert ta.bucket_for_days(7) == "weekly"
    assert ta.bucket_for_days(30) == "monthly"
    assert ta.bucket_for_days(90) == "other"
    assert ta.bucket_for_days(None) == "other"


# --- self-loop classification (immediate=auto vs option=player) -------------


def test_event_loop_immediate_is_auto():
    events = {
        "loop.1": {
            "type": "country_event",
            "file": "e.txt",
            "line": 1,
            "body": "immediate = { country_event = { id = loop.1 days = 7 } }",
        }
    }
    loops = ta.collect_event_loops(events)
    assert len(loops) == 1
    assert loops[0]["trigger"] == "immediate"
    assert loops[0]["bucket"] == "weekly"


def test_event_loop_option_is_player():
    events = {
        "loop.2": {
            "type": "country_event",
            "file": "e.txt",
            "line": 1,
            "body": (
                "option = { name = a "
                "hidden_effect = { country_event = { id = loop.2 days = 1 } } }"
            ),
        }
    }
    loops = ta.collect_event_loops(events)
    assert len(loops) == 1
    assert loops[0]["trigger"] == "option"
    # Player-driven: never attributed to a daily/weekly/monthly tick.
    assert loops[0]["bucket"] == "player"


def test_non_self_firing_event_is_not_a_loop():
    events = {
        "chain.1": {
            "type": "country_event",
            "file": "e.txt",
            "line": 1,
            "body": "immediate = { country_event = { id = chain.2 days = 1 } }",
        }
    }
    assert ta.collect_event_loops(events) == []


def _spot_file(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def test_spot_check_context_and_schema(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/on_actions/test.txt",
        "on_daily = { every_country = { limit = { always = yes } } }\non_startup = { every_country = { } }",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    report = ta.scan_spot_checks(["common/on_actions/test.txt"])
    assert report["schema_version"] == 1
    assert set(
        ("tool", "mode", "filters", "summary", "findings", "diagnostics")
    ) <= set(report)
    assert report["findings"][0]["context"]["reachability"] == "recurring"
    assert report["findings"][0]["severity"] == "critical"


def test_focus_and_gui_rules(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/national_focus/test.txt",
        "focus = { completion_reward = { every_country = { } } }",
    )
    _spot_file(
        tmp_path, "common/scripted_guis/test.txt", "gui = { dirty = global.date }"
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    report = ta.scan_spot_checks(["common/national_focus", "common/scripted_guis"])
    assert any(
        f["severity"] == "medium" and f["operation"] == "every_country"
        for f in report["findings"]
    )
    assert any(
        f["severity"] == "critical" and f["rule"] == "gui-date-dirty"
        for f in report["findings"]
    )


def test_spot_check_path_rejection_and_determinism(tmp_path, monkeypatch):
    _spot_file(tmp_path, "common/on_actions/a.txt", "on_daily = { every_state = { } }")
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    first = ta.scan_spot_checks(["common/on_actions/a.txt"])
    second = ta.scan_spot_checks(["common/on_actions/a.txt"])
    assert first == second
    rejected = ta.scan_spot_checks(["resources"])
    assert rejected["findings"] == []
    assert rejected["diagnostics"]


def test_decision_visible_and_transitive_effect_context(tmp_path, monkeypatch):
    _spot_file(tmp_path, "common/on_actions/a.txt", "on_weekly = { shared = yes }")
    _spot_file(
        tmp_path, "common/scripted_effects/a.txt", "shared = { every_country = { } }"
    )
    _spot_file(
        tmp_path,
        "common/decisions/a.txt",
        "cat = { d = { visible = { every_country = { } } } }",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    report = ta.scan_spot_checks(
        ["common/on_actions", "common/scripted_effects", "common/decisions"]
    )
    assert any(f["context"]["reachability"] == "recurring" for f in report["findings"])
    assert any(
        f["context"]["kind"] == "decision_visible" and f["severity"] == "high"
        for f in report["findings"]
    )


def test_spot_check_fail_threshold(tmp_path, monkeypatch):
    _spot_file(
        tmp_path, "common/on_actions/a.txt", "on_daily = { every_country = { } }"
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    assert (
        ta.main(
            [
                "--spot-check",
                "common/on_actions/a.txt",
                "--fail-on",
                "high",
                "--no-color",
            ]
        )
        == 1
    )
    assert (
        ta.main(
            [
                "--spot-check",
                "common/on_actions/a.txt",
                "--fail-on",
                "none",
                "--no-color",
            ]
        )
        == 0
    )


def test_real_wrappers_multiple_objects_and_shared_contexts(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/on_actions/a.txt",
        "on_actions = { on_daily = { shared = yes } on_startup = { shared = yes } }",
    )
    _spot_file(
        tmp_path, "common/scripted_effects/a.txt", "shared = { every_country = { } }"
    )
    _spot_file(
        tmp_path,
        "common/national_focus/a.txt",
        "focus_tree = { F_one = { completion_reward = { every_country = { } } } F_two = { completion_reward = { every_state = { } } } }",
    )
    _spot_file(
        tmp_path,
        "common/decisions/a.txt",
        "category = { D_one = { visible = { every_country = { } } } D_two = { available = { every_state = { } } } }",
    )
    _spot_file(
        tmp_path,
        "common/scripted_guis/a.txt",
        "scripted_gui = { G_one = { dirty = global.date } G_two = { effects = { x = yes } } }",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    report = ta.scan_spot_checks()
    recurring = [
        f for f in report["findings"] if f["context"].get("reachability") == "recurring"
    ]
    assert len(recurring) == 1
    assert not any(
        finding["context"].get("reachability") == "one-shot"
        and finding["context"].get("kind") == "scripted_effect"
        for finding in report["findings"]
    )
    assert {
        f["context"]["name"]
        for f in report["findings"]
        if f["context"]["kind"] == "focus_completion"
    } == {"F_one", "F_two"}
    assert {
        f["context"]["name"]
        for f in report["findings"]
        if f["context"]["kind"].startswith("decision_")
    } == {"D_one", "D_two"}
    assert any(
        f["rule"] == "gui-date-dirty" and f["context"]["name"] == "G_one"
        for f in report["findings"]
    )


def test_spot_check_quotes_malformed_offsets_and_nested_unsupported(
    tmp_path, monkeypatch
):
    _spot_file(
        tmp_path,
        "common/on_actions/a.txt",
        'on_daily = { log = "quoted { } # text"\n every_country = { } }\n',
    )
    _spot_file(tmp_path, "common/on_actions/b.txt", "on_weekly = { every_state = { ")
    _spot_file(tmp_path, "common/on_actions/notes.yml", "ignored")
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    report = ta.scan_spot_checks(["common/on_actions"])
    assert report["findings"][0]["line"] == 2
    assert any("malformed" in d["message"] for d in report["diagnostics"])
    assert not any("notes.yml" in d["file"] for d in report["diagnostics"])


def test_spot_check_json_output_uses_atomic_writer(tmp_path, monkeypatch):
    _spot_file(
        tmp_path, "common/on_actions/a.txt", "on_daily = { every_country = { } }"
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))
    output = tmp_path / "report.json"
    writes = []
    original_write = ta.atomic_write_text

    def atomic_write(path, text):
        writes.append((path, text))
        original_write(path, text)

    monkeypatch.setattr(ta, "atomic_write_text", atomic_write)
    assert (
        ta.main(
            [
                "--spot-check",
                "common/on_actions/a.txt",
                "--json",
                str(output),
                "--format",
                "json",
            ]
        )
        == 0
    )
    assert output.exists()
    assert writes and writes[0][0] == str(output)
    assert not list(tmp_path.glob(".report.json.*"))


def test_spot_check_json_failure_preserves_existing_output(tmp_path, monkeypatch):
    output = tmp_path / "report.json"
    output.write_text("original\n", encoding="utf-8")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr(ta.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        ta._write_json_atomic(str(output), {"schema_version": 1})

    assert output.read_text(encoding="utf-8") == "original\n"
    assert not list(tmp_path.glob(".report.json.*"))


def test_spot_check_severity_uses_execution_frequency(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/on_actions/a.txt",
        """on_actions = {
	on_daily = { every_country = { } }
	on_monthly = { every_country = { } }
	on_daily_USA = { every_country = { } }
	on_startup = { every_country = { } }
}
""",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))

    report = ta.scan_spot_checks(["common/on_actions/a.txt"])
    severities = {
        finding["context"]["name"]: finding["severity"]
        for finding in report["findings"]
    }

    assert severities == {
        "on_daily": "critical",
        "on_monthly": "high",
        "on_daily_USA": "high",
    }
    assert report["summary"]["suppressed"] == 1


def test_spot_check_preserves_shared_effect_contexts_and_cycles(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/on_actions/a.txt",
        """on_actions = {
	on_daily = { shared = yes }
	on_weekly_USA = { shared = yes }
}
""",
    )
    _spot_file(
        tmp_path,
        "common/scripted_effects/a.txt",
        """shared = {
	nested = yes
	every_country = { }
}
nested = {
	shared = yes
	force_update_dynamic_modifier = yes
}
unreachable = { every_state = { } }
""",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))

    report = ta.scan_spot_checks(["common/on_actions", "common/scripted_effects"])
    shared = [
        finding
        for finding in report["findings"]
        if finding["context"]["name"] == "shared"
    ]

    assert {(item["context"]["cadence"], item["severity"]) for item in shared} == {
        ("daily", "critical"),
        ("weekly", "high"),
    }
    assert all(item["line"] == 3 for item in shared)
    assert not any(
        finding["context"]["name"] == "unreachable" for finding in report["findings"]
    )


def test_spot_check_real_focus_and_decision_contexts(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/national_focus/a.txt",
        """focus_tree = {
	focus = {
		id = F_one
		completion_reward = { every_country = { } }
	}
	focus = {
		id = F_two
		completion_reward = { every_state = { } }
	}
}
""",
    )
    _spot_file(
        tmp_path,
        "common/decisions/a.txt",
        """category = {
	D_one = { visible = { every_country = { } } }
	D_two = { ai_will_do = { every_state = { } } }
}
""",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))

    report = ta.scan_spot_checks(["common/national_focus", "common/decisions"])
    by_name = {finding["context"]["name"]: finding for finding in report["findings"]}

    assert by_name["F_one"]["severity"] == "medium"
    assert by_name["F_two"]["severity"] == "medium"
    assert by_name["D_one"]["severity"] == "high"
    assert by_name["D_two"]["severity"] == "medium"


def test_spot_check_gui_dirty_rules_are_context_aware(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/scripted_guis/a.txt",
        """scripted_gui = {
	G_missing = {
		context_type = decision_category
		effects = { click = { set_variable = { x = 1 } } }
	}
	G_other = {
		context_type = player_context
		effects = { click = { set_variable = { x = 1 } } }
	}
	G_date = {
		context_type = decision_category
		dirty = global.num_days
	}
}
""",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))

    report = ta.scan_spot_checks(["common/scripted_guis"])
    rules = {(item["rule"], item["context"]["name"]) for item in report["findings"]}

    assert ("gui-missing-dirty", "G_missing") in rules
    assert ("gui-date-dirty", "G_date") in rules
    assert not any(name == "G_other" for _rule, name in rules)


def test_spot_named_blocks_preserves_repeated_sibling_bodies():
    blocks = list(
        ta._spot_named_blocks("BOS = { has_war = yes }\nBOS = { has_war = yes }\n")
    )

    assert [name for name, _body, _start, _body_start in blocks] == ["BOS", "BOS"]
    assert blocks[0][1] == blocks[1][1]
    assert ta._spot_repeated_foreign_scopes(
        "BOS = { has_war = yes }\nBOS = { has_war = yes }\n"
    ) == [("BOS", blocks[1][2])]


def test_spot_check_division_force_update_and_invariant_reads(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/on_actions/a.txt",
        """on_actions = {
	on_daily = {
		clamp_temp_variable = { var = safe min = 0.01 }
		divide_temp_variable = { result = safe }
		divide_temp_variable = { result = unsafe }
		divide_temp_variable = { result = 2 }
		force_update_dynamic_modifier = yes
		while_loop_effect = {
			limit = { check_variable = { i < 5 } }
			add_to_temp_variable = { i = 1 }
		}
	}
	on_weekly_USA = {
		every_state = {
			BOS = { has_war = yes }
			BOS = { has_war = yes }
		}
	}
}
""",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))

    report = ta.scan_spot_checks(["common/on_actions"])
    rules = [item["rule"] for item in report["findings"]]

    assert rules.count("unclamped-division") == 1
    assert "force-update-dynamic-modifier" in rules
    assert "repeated-invariant-scope" in rules
    assert any(
        item["operation"] == "while_loop_effect" and item["severity"] == "medium"
        for item in report["findings"]
    )


def test_invariant_scope_comparison_preserves_quoted_values(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/on_actions/a.txt",
        """on_actions = {
	on_weekly_USA = {
		every_state = {
			BOS = { log = "AA" }
			BOS = { log = "BB" }
		}
	}
}
""",
    )
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))

    report = ta.scan_spot_checks(["common/on_actions"])

    assert not any(
        item["rule"] == "repeated-invariant-scope" for item in report["findings"]
    )


def test_spot_check_suppression_defaults_and_invalid_path(tmp_path, monkeypatch):
    _spot_file(
        tmp_path,
        "common/on_actions/a.txt",
        """on_actions = {
	on_daily = {
		can_staff_an_factory = {
			check_variable = { workers > required }
		}
	}
}
""",
    )
    _spot_file(tmp_path, "notes.md", "unsupported")
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))

    report = ta.scan_spot_checks()

    assert report["filters"]["paths"] == list(ta.SPOT_DEFAULT_PATHS)
    assert report["summary"]["suppressed"] == 1
    assert report["assumptions"] == list(ta.SPOT_ASSUMPTIONS)
    assert ta.main(["--spot-check", "notes.md"]) == 2


def test_spot_check_unreadable_source_exits_two(tmp_path, monkeypatch):
    source = tmp_path / "common" / "on_actions" / "bad.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"on_daily = {\xff}")
    monkeypatch.setattr(ta, "REPO_ROOT", str(tmp_path))

    report = ta.scan_spot_checks(["common/on_actions/bad.txt"])

    assert report["diagnostics"][0]["fatal"] is True
    assert ta.main(["--spot-check", "common/on_actions/bad.txt"]) == 2
