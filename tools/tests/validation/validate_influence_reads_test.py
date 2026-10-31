"""Country binding regressions for advisory influence reads."""

import json

import pytest
import validate_influence_reads as V
from shared.suite import (
    checks_called_by_run,
    run_tool_script,
    run_validator,
    write_tree,
)

_FOCUS = "common/national_focus/test.txt"
_HISTORY = "history/countries/CHI - China.txt"
_EVENTS = "events/test.txt"
_TRIGGERS = "common/scripted_triggers/test.txt"


def _scan(documents):
    reader = V.Reader(
        {path: V.script_nodes(text) for path, text in sorted(documents.items())}
    )
    for text in documents.values():
        for event in sorted(V.event_pool_targets(text)):
            reader._event(event, V.Scope(), "event pool (caller unresolved)")
    return reader.scan()


def _focus(body):
    return "focus = { id = test available = { tag = CHI " + body + " } }"


def _event(body, event="test.1", extra=""):
    return f"country_event = {{ id = {event} is_triggered_only = yes {extra} option = {{ {body} }} }}"


# documents, (influencer fragment, target fragment, status) for each binding
_CASES = {
    "contradictory runtime tags": (
        {_FOCUS: _focus("tag = KOR is_top3_influencer = yes")},
        [],
    ),
    "impossible literal scope guard": (
        {_HISTORY: "USA = { available = { tag = CHI is_top3_influencer = yes } }"},
        [],
    ),
    "event trigger excludes impossible recipient": (
        {
            _HISTORY: "country_event = test.1",
            _EVENTS: _event(
                "sender_is_top5_influencer = yes", extra="trigger = { tag = KOR }"
            ),
        },
        [],
    ),
    "direct self-check": (
        {_FOCUS: _focus("is_top3_influencer = yes")},
        [("CHI", "CHI", "self")],
    ),
    "ROOT to foreign target": (
        {_FOCUS: _focus("KOR = { is_top3_influencer = yes }")},
        [("CHI", "KOR", "resolved")],
    ),
    "nested PREV, not ROOT": (
        {_FOCUS: _focus("USA = { KOR = { prev_is_top3_influencer = no } }")},
        [("USA", "KOR", "resolved")],
    ),
    "neutral trigger wrappers": (
        {
            _FOCUS: _focus(
                "USA = { KOR = { NOT = { custom_trigger_tooltip = { tooltip = tt AND = { prev_is_top3_influencer = yes } } } } }"
            )
        },
        [("USA", "KOR", "resolved")],
    ),
    "ROOT reset preserves previous": (
        {_FOCUS: _focus("USA = { ROOT = { prev_is_top3_influencer = yes } }")},
        [("USA", "CHI", "resolved")],
    ),
    "THIS and PREV chain": (
        {
            _FOCUS: _focus(
                "USA = { THIS = { KOR = { PREV.PREV = { prev_is_top3_influencer = yes } } } }"
            )
        },
        [("KOR", "USA", "resolved")],
    ),
    "undotted PREVPREV": (
        {
            _FOCUS: _focus(
                "USA = { THIS = { KOR = { PREVPREV = { prev_is_top3_influencer = yes } } } }"
            )
        },
        [("KOR", "USA", "resolved")],
    ),
    "original_tag is not runtime tag": (
        {
            _FOCUS: "focus = { id = test available = { original_tag = CHI CHI = { is_top3_influencer = yes } } }"
        },
        [("ROOT[test; original_tag=CHI]", "CHI", "resolved")],
    ),
    "achievement sender is unknown": (
        {
            "common/achievements/test.txt": "achievement_test = { possible = { original_tag = HOL } happened = { USA = { sender_is_top5_influencer = yes } } }"
        },
        [("unknown", "USA", "unresolved")],
    ),
    "bound sender": (
        {
            _HISTORY: "KOR = { country_event = { id = test.1 days = 1 } }",
            _EVENTS: _event("sender_is_top5_influencer = yes"),
        },
        [("CHI", "KOR", "resolved")],
    ),
    "bound sender shorthand": (
        {
            _HISTORY: "KOR = { country_event = test.1 }",
            _EVENTS: _event("sender_influence_higher_20 = yes"),
        },
        [("CHI", "KOR", "resolved")],
    ),
    "sender uses firing ROOT, not nested scope": (
        {
            _HISTORY: "USA = { KOR = { country_event = test.1 } }",
            _EVENTS: _event("sender_influence_higher_20 = yes"),
        },
        [("CHI", "KOR", "resolved")],
    ),
    "unresolved event caller": (
        {_EVENTS: _event("sender_influence_higher_50 = yes")},
        [("unknown", "ROOT[test.1]", "unresolved")],
    ),
    "unknown and bound dispatches coexist": (
        {
            _HISTORY: "KOR = { country_event = test.1 }",
            "common/on_actions/test.txt": "on_actions = { on_startup = { effect = { KOR = { country_event = test.1 } } } }",
            _EVENTS: _event("sender_is_top5_influencer = yes"),
        },
        [("CHI", "KOR", "resolved"), ("unknown", "KOR", "unresolved")],
    ),
    "event pool does not erase bound caller": (
        {
            _HISTORY: "KOR = { country_event = test.1 }",
            "common/on_actions/test.txt": "on_actions = { on_daily = { events = { test.1 } } }",
            _EVENTS: _event("sender_is_top5_influencer = yes"),
        },
        [("CHI", "KOR", "resolved"), ("unknown", "ROOT[test.1]", "unresolved")],
    ),
    "unsupported scalar dispatch": (
        {
            "common/test.txt": "border_war = { on_win = test.1 }",
            _EVENTS: _event("sender_is_top5_influencer = yes"),
        },
        [("unknown", "ROOT[test.1]", "unresolved")],
    ),
    "event sender chain": (
        {
            _HISTORY: "KOR = { country_event = test.1 }",
            _EVENTS: _event("USA = { country_event = test.2 }")
            + _event("FROM.FROM = { sender_is_top5_influencer = yes }", "test.2"),
        },
        [("KOR", "CHI", "resolved")],
    ),
    "multiple event callers": (
        {
            _HISTORY: "USA = { country_event = test.1 }",
            "history/countries/KOR - Korea.txt": "USA = { country_event = test.1 }",
            _EVENTS: _event("sender_is_top5_influencer = yes"),
        },
        [("CHI", "USA", "resolved"), ("KOR", "USA", "resolved")],
    ),
    "scripted trigger inherits caller": (
        {
            _HISTORY: "USA = { KOR = { wrapper = no } }",
            _TRIGGERS: "wrapper = { prev_is_top3_influencer = yes }",
        },
        [("USA", "KOR", "resolved")],
    ),
    "unbound scripted trigger": (
        {_TRIGGERS: "wrapper = { KOR = { is_top3_influencer = yes } }"},
        [("unknown", "KOR", "unresolved")],
    ),
    "scripted effect carries event sender": (
        {
            _HISTORY: "wrapper = yes",
            "common/scripted_effects/test.txt": "wrapper = { KOR = { country_event = test.1 } }",
            _EVENTS: _event("sender_is_top5_influencer = yes"),
        },
        [("CHI", "KOR", "resolved")],
    ),
    "recursive helper terminates": (
        {
            _HISTORY: "wrapper = yes",
            _TRIGGERS: "wrapper = { wrapper = yes KOR = { is_top3_influencer = yes } }",
        },
        [("CHI", "KOR", "resolved")],
    ),
    "unknown block does not invent PREV": (
        {_HISTORY: "mystery = { KOR = { prev_is_top3_influencer = yes } }"},
        [("unknown", "KOR", "unresolved")],
    ),
    "state scope stays unknown": (
        {_HISTORY: "capital_scope = { is_top3_influencer = yes }"},
        [("CHI", "unknown", "unresolved")],
    ),
    "variable scope stays unknown": (
        {_HISTORY: "var:target = { is_top3_influencer = yes }"},
        [("CHI", "unknown", "unresolved")],
    ),
    "random-list outcome is not a state": (
        {_HISTORY: "random_list = { 50 = { KOR = { is_top3_influencer = yes } } }"},
        [("CHI", "KOR", "resolved")],
    ),
    "reverse-direction less-than helper": (
        {_HISTORY: "KOR = { influence_less_10 = yes }"},
        [("KOR", "CHI", "resolved")],
    ),
    "literal-country helper self": (
        {_HISTORY: "HOL = { HOL_is_top3_influencer = yes }"},
        [("HOL", "HOL", "self")],
    ),
    "literal-country helper foreign": (
        {_HISTORY: "USA = { HOL_is_top5_influencer = yes }"},
        [("HOL", "USA", "resolved")],
    ),
    "comments and quoted script ignored": (
        {
            _HISTORY: '# is_top3_influencer = yes\nlog = "is_top3_influencer = yes {"\nKOR = { is_top3_influencer = "yes" }'
        },
        [],
    ),
    "non-boolean call ignored": ({_HISTORY: "is_top3_influencer = maybe"}, []),
    "templates and previews skipped": (
        {
            _HISTORY: "effect_tooltip = { is_top3_influencer = yes } meta_effect = { text = { is_top3_influencer = yes } } custom_effect_tooltip = { is_top3_influencer = yes }"
        },
        [],
    ),
    "tooltip event is not a caller": (
        {
            _HISTORY: "effect_tooltip = { KOR = { country_event = test.1 } }",
            _EVENTS: _event("sender_is_top5_influencer = yes"),
        },
        [("unknown", "ROOT[test.1]", "unresolved")],
    ),
    "decision actor is a country": (
        {
            "common/decisions/test.txt": "category = { decision = { available = { is_top3_influencer = yes } } }"
        },
        [("ROOT[decision]", "ROOT[decision]", "self")],
    ),
    "targeted decision caller stays unknown": (
        {
            "common/decisions/test.txt": "category = { decision = { target_array = subjects available = { is_top3_influencer = yes } } }"
        },
        [("unknown", "unknown", "unresolved")],
    ),
    "unsupported root context stays unknown": (
        {
            "common/scripted_guis/test.txt": "scripted_gui = { test = { trigger = { is_top3_influencer = yes } } }"
        },
        [("unknown", "unknown", "unresolved")],
    ),
    "line numbers survive CRLF and braces in quotes": (
        {
            _HISTORY: 'log = "{ } # ignored"\r\n# comment\r\nKOR = {\r\n is_top3_influencer = yes\r\n}'
        },
        [("CHI", "KOR", "resolved")],
    ),
    "unrelated definitions ignored": ({_TRIGGERS: "unrelated = { always = yes }"}, []),
}


@pytest.mark.parametrize("documents,expected", _CASES.values(), ids=_CASES)
def test_read_bindings(documents, expected):
    rows = _scan(documents)
    remaining = list(rows)
    for influencer, target, status in expected:
        match = next(
            (
                row
                for row in remaining
                if influencer in row.influencer
                and target in row.target
                and row.status == status
            ),
            None,
        )
        assert match is not None, rows
        remaining.remove(match)
    assert not remaining


@pytest.mark.parametrize("trigger,contract", V.CONTRACTS.items())
def test_every_registered_contract_is_scanned(trigger, contract):
    scope = V.Scope("CHI", "KOR", ("USA",), ("FRA",))
    reader = V.Reader({})
    reader._walk("test.txt", V.script_nodes(f"{trigger} = no"), scope, "test caller")
    (row,) = reader.reads
    assert (row.influencer, row.target) == tuple(
        scope.resolve(token) for token in contract
    )
    assert row.trigger == trigger
    assert row.line == 1


# issue, old read, corrected read, old influencer, corrected influencer, old target, corrected target
_SCOPE_REGRESSIONS = {
    "6198 reversed-country read": (
        "USA = { is_top3_influencer = no }",
        "USA = { KOR = { prev_is_top3_influencer = no } }",
        "CHI",
        "USA",
        "USA",
        "KOR",
    ),
    "6197 sender-based achievement read": (
        "USA = { sender_is_top5_influencer = yes }",
        "USA = { is_top3_influencer = yes }",
        "unknown",
        "CHI",
        "USA",
        "USA",
    ),
}


@pytest.mark.parametrize(
    "old,new,old_source,new_source,old_target,new_target",
    _SCOPE_REGRESSIONS.values(),
    ids=_SCOPE_REGRESSIONS,
)
def test_old_and_corrected_regression_bindings(
    old, new, old_source, new_source, old_target, new_target
):
    (before,) = _scan({_HISTORY: old})
    (after,) = _scan({_HISTORY: new})
    assert (before.influencer, before.target) == (old_source, old_target)
    assert (after.influencer, after.target, after.status) == (
        new_source,
        new_target,
        "resolved",
    )
    assert before.status == ("unresolved" if old_source == "unknown" else "resolved")


def test_reported_line_is_the_call_not_its_scope():
    rows = _scan(_CASES["line numbers survive CRLF and braces in quotes"][0])
    assert rows[0].line == 4


def test_automatic_event_keeps_unknown_sender_with_a_known_caller():
    rows = _scan(
        {
            _HISTORY: "KOR = { country_event = test.1 }",
            _EVENTS: "country_event = { id = test.1 option = { sender_is_top5_influencer = yes } }",
        }
    )
    assert {(row.influencer, row.status) for row in rows} == {
        ("CHI", "resolved"),
        ("unknown", "unresolved"),
    }


def test_broadcast_does_not_assign_the_original_recipient_to_every_reader():
    rows = _scan(
        {
            _HISTORY: "KOR = { country_event = test.1 }",
            _EVENTS: _event("sender_is_top5_influencer = yes", extra="major = yes"),
        }
    )
    assert len(rows) == 2
    assert {row.target for row in rows} == {"KOR", "ROOT[test.1]@events/test.txt:1"}
    assert {row.influencer for row in rows} == {"CHI"}


def test_repeated_country_selection_is_not_a_proven_self_check():
    rows = _scan(
        {
            _HISTORY: "wrapper = yes",
            _TRIGGERS: "wrapper = { random_country = { prev_is_top3_influencer = yes wrapper = yes } }",
        }
    )
    assert rows
    assert not any(row.status == "self" for row in rows)


def test_this_keeps_the_same_selected_country():
    rows = _scan(
        {_HISTORY: "random_country = { THIS = { prev_is_top3_influencer = yes } }"}
    )
    (row,) = rows
    assert row.status == "self"
    assert row.influencer == row.target


def test_context_limit_adds_an_unknown_candidate_instead_of_dropping_paths(monkeypatch):
    monkeypatch.setattr(V, "_CONTEXT_LIMIT", 1)
    rows = _scan(
        {
            _HISTORY: "USA = { country_event = test.1 }",
            "history/countries/KOR - Korea.txt": "USA = { country_event = test.1 }",
            _EVENTS: _event("sender_is_top5_influencer = yes"),
        }
    )
    assert {row.status for row in rows} == {"resolved", "unresolved"}
    assert any("context limit" in row.caller for row in rows)


def test_run_calls_every_check(tmp_path, monkeypatch):
    validator = V.Validator(mod_path=str(tmp_path), workers=1)
    called, checks = checks_called_by_run(validator, monkeypatch)
    assert called == checks == ["validate_influence_reads"]


def test_warnings_and_bindings_have_separate_outputs(tmp_path):
    write_tree(
        tmp_path,
        {
            _HISTORY: "is_top3_influencer = yes\nKOR = { is_top3_influencer = yes }\nUSA = { sender_is_top5_influencer = yes }"
        },
    )
    output = tmp_path / "result.log"
    validator = run_validator(
        V.Validator, tmp_path, output_file=str(output), strict=True
    )
    validator.save_output()
    findings = json.loads(output.with_suffix(".json").read_text(encoding="utf-8"))
    bindings = [
        json.loads(line)
        for line in output.with_suffix(".bindings.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert validator.errors_found == 0
    assert {issue["severity"] for issue in findings} == {"warning"}
    assert {issue["category"] for issue in findings} == {
        "influence-read-self",
        "influence-read-unresolved",
    }
    assert len(findings) == 2
    assert len(bindings) == 3
    assert {row["status"] for row in bindings} == {"self", "resolved", "unresolved"}
    assert "not proof of an unset sender" in next(
        issue["message"]
        for issue in findings
        if issue["category"] == "influence-read-unresolved"
    )
    assert {issue["file"] for issue in findings} == {_HISTORY}
    assert {issue["line"] for issue in findings} == {1, 3}


def test_staged_selection_still_uses_unstaged_callers(tmp_path):
    write_tree(
        tmp_path,
        {
            _HISTORY: "KOR = { country_event = test.1 }",
            _EVENTS: _event("sender_is_top5_influencer = yes"),
            "common/achievements/test.txt": "test = { happened = { sender_is_top5_influencer = yes } }",
        },
    )
    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.staged_only = True
    validator.staged_files = [_EVENTS]
    validator.run_validations()
    (row,) = validator.bindings
    assert row.influencer == "CHI"
    assert row.target == "KOR"
    assert row.file == _EVENTS
    assert validator.warnings_found == 0


def test_unreadable_input_fails_instead_of_reporting_clean(tmp_path):
    write_tree(tmp_path, {_HISTORY: "is_top3_influencer = yes"})
    (tmp_path / _HISTORY).write_bytes(b"\xff")
    with pytest.raises(ValueError, match="Cannot scan"):
        run_validator(V.Validator, tmp_path)


def test_cli_strict_does_not_gate_advisory_findings(tmp_path):
    write_tree(tmp_path, {_HISTORY: "is_top3_influencer = yes"})
    output = tmp_path / "result.log"
    result = run_tool_script(
        "validation/validate_influence_reads.py",
        "--path",
        tmp_path,
        "--strict",
        "--no-color",
        "--output",
        output,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.with_suffix(".bindings.jsonl").is_file()
    findings = json.loads(output.with_suffix(".json").read_text(encoding="utf-8"))
    assert findings[0]["severity"] == "warning"
