"""Behaviour tests for tools/shared/suite.py."""

import json

import pytest
from shared.paths import TOOLS_DIR
from shared.suite import (
    EconomicScriptFixture,
    assert_findings,
    collecting_validator,
    initialize_git_repository,
    issue_dict,
    make_issue,
    make_results_tree,
    run_git,
    script_block,
    write_slug_json,
    write_text,
)


def test_economic_fixture_branches_observe_prior_writes_and_nested_chains():
    script = EconomicScriptFixture({"balance": 10})
    script.execute("""if = { limit = { check_variable = { balance > 5 } }
            set_variable = { balance = 3 }
            if = { limit = { check_variable = { balance < 4 } }
                multiply_variable = { balance = 2 }
            } else = { set_variable = { balance = 100 } }
        } else_if = { limit = { check_variable = { balance > 0 } }
            set_variable = { balance = 200 }
        } else = { set_variable = { balance = 300 } }
        if = { limit = { check_variable = { balance = 6 } }
            set_variable = { result = { value = balance add = 2 multiply = 3 } }
        }""")
    assert script.values == {"balance": 6, "result": 24}


# case: (source, expected exception text)
_ECONOMIC_REJECTION_CASES = {
    "unknown effect": ("treasury_change = 5", "Unsupported effect"),
    "unbound numeric input": (
        "set_variable = { x = missing }",
        "Missing numeric input",
    ),
    "unknown arithmetic": (
        "set_variable = { x = { value = 1 divide = 2 } }",
        "Unsupported arithmetic",
    ),
    "fractional native rounding": (
        "set_variable = { x = 1.5 } round_variable = x",
        "Native fractional rounding",
    ),
    "unknown predicate": (
        "if = { limit = { unknown_trigger = yes } set_variable = { x = 1 } }",
        "Unsupported predicate",
    ),
    "unpaired else": ("else = { set_variable = { x = 1 } }", "Unpaired else"),
    "invalid effect operator": ("set_variable > { x = 1 }", "effect operator"),
    "invalid arithmetic operator": (
        "set_variable = { x = { value = 1 multiply < 2 } }",
        "arithmetic operator",
    ),
    "bare unknown effect": ("unknown_effect", "Malformed or unconsumed"),
    "unclosed assignment": ("set_variable = {", "Malformed or unconsumed"),
}


@pytest.mark.parametrize(
    "source,message", _ECONOMIC_REJECTION_CASES.values(), ids=_ECONOMIC_REJECTION_CASES
)
def test_economic_fixture_rejects_unmodeled_behavior(source, message):
    with pytest.raises(AssertionError, match=message):
        EconomicScriptFixture({}).execute(source)


@pytest.mark.parametrize("source", ["", "x = {} x = {}", "x > {}"])
def test_script_block_requires_one_definition(source):
    with pytest.raises(AssertionError):
        script_block(source, "x")


def test_economic_fixture_rejects_invalid_predicate_and_weight_operators():
    script = EconomicScriptFixture({}, predicates={"is_ai": True})
    with pytest.raises(AssertionError, match="predicate operator"):
        script.condition("is_ai > yes")
    with pytest.raises(AssertionError, match="weight operator"):
        script.weight("base > 10")


class _Stub:
    def __init__(self, *args, **kwargs):
        pass

    def _report(self, results, ok_msg, fail_msg, severity=None, category=""):
        raise AssertionError("unwrapped _report should not run")


def test_collecting_validator_appends_results_and_severity():
    wrapped = collecting_validator(_Stub)("/tmp")
    wrapped._report(["a", "b"], "ok", "fail", severity="error", category="x")
    assert wrapped.collected == ["a", "b"]
    assert wrapped.last_severity == "error"


@pytest.mark.parametrize(
    ("results", "expected", "passes"),
    (
        (["a - b"], ["a - b"], True),
        (["a - b"], [("a", "b")], True),
        (["a - b"], ["a"], False),
        (["a - b"], [], False),
        ([], [("a",)], False),
        (["a - b"], [("a",), ("b",)], False),
    ),
    ids=(
        "whole finding",
        "fragments",
        "string is not a fragment",
        "extra finding",
        "missing finding",
        "one finding for two entries",
    ),
)
def test_assert_findings_matches_each_finding_once(results, expected, passes):
    if passes:
        assert_findings(results, expected)
    else:
        with pytest.raises(AssertionError):
            assert_findings(results, expected)


def test_issue_dict_defaults():
    assert issue_dict("warning") == {
        "severity": "warning",
        "category": "c",
        "message": "m",
        "file": "a.txt",
        "line": 1,
    }


def test_make_issue_defaults_and_overrides():
    issue = make_issue()
    assert issue.severity == "error"
    assert issue.category == "missing_key"
    assert issue.message == "key FOO not found"
    assert issue.file == "events/MD_x.txt"
    assert issue.line == 212
    assert issue.validator == "events"
    assert make_issue(file="other.txt", line=3).file == "other.txt"


def test_write_text_creates_parents_and_returns_path(tmp_path):
    path = write_text(tmp_path / "nested" / "file.txt", "hello\n")
    assert path.read_text(encoding="utf-8") == "hello\n"
    assert path == tmp_path / "nested" / "file.txt"


def test_write_slug_json_writes_the_array(tmp_path):
    payload = [{"severity": "error"}]
    write_slug_json(tmp_path, "events", payload)
    assert json.loads((tmp_path / "events.json").read_text(encoding="utf-8")) == payload


def test_make_results_tree_writes_log_and_sidecar(tmp_path):
    issues = [{"severity": "warning", "message": "m"}]
    root = make_results_tree(tmp_path, {"events": {"log": "ok\n", "issues": issues}})
    sub = root / "validation-events-results"
    assert (sub / "validation-events.log").read_text(encoding="utf-8") == "ok\n"
    assert (
        json.loads((sub / "validation-events.json").read_text(encoding="utf-8"))
        == issues
    )


def test_make_results_tree_log_only_skips_sidecar(tmp_path):
    root = make_results_tree(tmp_path, {"events": {"log": "ok\n"}})
    sub = root / "validation-events-results"
    assert (sub / "validation-events.log").is_file()
    assert not (sub / "validation-events.json").exists()


def test_initialize_git_repository_commits_added_paths(tmp_path):
    tracked = tmp_path / "history" / "units"
    tracked.mkdir(parents=True)
    write_text(tracked / "oob.txt", "units = { }\n")
    initialize_git_repository(tmp_path, "history/units")
    names = run_git(tmp_path, "ls-files").stdout.splitlines()
    assert "history/units/oob.txt" in names


def test_suite_module_lives_in_shared_not_tests_root():
    assert (TOOLS_DIR / "shared" / "suite.py").is_file()
    assert not (TOOLS_DIR / "suite_helpers.py").exists()
