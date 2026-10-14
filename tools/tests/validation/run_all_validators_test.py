"""Output-contract tests for run_all_validators without content scans."""

import builtins
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import run_all_validators as runner
from shared.suite import write_text
from validator_batches import ALL_SPECS


class _Process:
    def __init__(self, returncode=0):
        self.returncode = returncode

    def wait(self):
        return self.returncode


def _args(format_, output=None, strict=False, persist_results=None):
    return SimpleNamespace(
        format=format_,
        output=output,
        strict=strict,
        no_color=True,
        persist_results=persist_results,
    )


def _run_stub(tmp_path, args):
    validators = [("stub", "validate_stub.py", "Stub")]
    return runner._run_suite(args, [], str(tmp_path), validators, str(tmp_path))


def _launcher_with(issues, returncode=0, stderr_log=""):
    def launch(_script, _flags, output_dir, name, _mod_path):
        # Mirror BaseValidator.save_output: a validator with no findings
        # writes no JSON sidecar at all.
        if issues:
            try:
                with open(f"{output_dir}/{name}.json", "w", encoding="utf-8") as stream:
                    json.dump(issues, stream)
            except OSError:
                raise
        if stderr_log:
            write_text(Path(output_dir) / f"{name}.stderr.log", stderr_log)
        return _Process(returncode), io.StringIO()

    return launch


def _run_main(monkeypatch, tmp_path, *argv, stale=False, pruned=()):
    """Run main() with the cache and the suite stubbed; return their calls."""
    calls = []
    cache = runner.disk_cache
    for color in ("RED", "GREEN", "YELLOW", "CYAN", "ENDC"):
        monkeypatch.setattr(runner.Colors, color, getattr(runner.Colors, color))
    monkeypatch.setattr(runner, "discover_validators", lambda: [])
    monkeypatch.setattr(cache, "clear", lambda path: calls.append(("clear", path)))
    monkeypatch.setattr(
        cache, "stamp_created", lambda path: calls.append(("stamp", path))
    )
    monkeypatch.setattr(
        cache, "clear_if_stale", lambda path, age: calls.append(("stale", age)) or stale
    )
    monkeypatch.setattr(cache, "prune_old_versions", lambda path: list(pruned))
    monkeypatch.setattr(
        runner, "_run_suite", lambda *args: calls.append(("run", args[1])) or 0
    )
    monkeypatch.setattr(sys, "argv", ["runner", "--path", str(tmp_path), *argv])

    with pytest.raises(SystemExit) as exc:
        runner.main()

    assert exc.value.code == 0
    return calls


def test_collect_all_issues_uses_report_dedupe_and_escalation(tmp_path):
    warning = {
        "severity": "warning",
        "category": "same",
        "message": "same finding",
        "file": "a.txt",
        "line": 1,
    }
    error = {**warning, "severity": "error"}
    (tmp_path / "one.json").write_text(json.dumps([warning]), encoding="utf-8")
    (tmp_path / "two.json").write_text(json.dumps([error]), encoding="utf-8")

    issues = runner.collect_all_issues(
        str(tmp_path),
        [("one", "one.py", "One"), ("two", "two.py", "Two")],
    )

    assert len(issues) == 1
    assert issues[0]["severity"] == "error"
    assert issues[0]["detected_by"] == ["two"]


@pytest.mark.parametrize(
    "sidecar",
    [
        pytest.param("{broken", id="not JSON"),
        pytest.param('{"issue": {}}', id="not a list"),
        pytest.param('["finding"]', id="a list of something else"),
    ],
)
def test_collect_all_issues_rejects_malformed_sidecar(tmp_path, sidecar):
    (tmp_path / "stub.json").write_text(sidecar, encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed validator sidecar"):
        runner.collect_all_issues(str(tmp_path), [("stub", "stub.py", "Stub")])


def test_a_line_that_is_not_a_number_sorts_first_in_its_file():
    issues = [{"file": "a.txt", "line": 3}, {"file": "a.txt", "line": "bad"}]

    assert sorted(issues, key=runner._issue_sort_key)[0]["line"] == "bad"


@pytest.mark.parametrize(
    ("source", "label"),
    [
        pytest.param('TITLE = "EVENT CHAIN VALIDATION"\n', "EVENT CHAIN", id="TITLE"),
        pytest.param(
            "class ExampleValidator(Base):\n    pass\n", "Example", id="class"
        ),
        pytest.param("# no metadata\n", "Event Chain", id="script name"),
        pytest.param(None, "Event Chain", id="unreadable script"),
    ],
)
def test_validator_label_comes_from_the_script(tmp_path, write_path, source, label):
    script = tmp_path / "validate_event_chain.py"
    if source is not None:
        write_path(tmp_path, script.name, source)

    assert runner._extract_label_from_script(str(script), "event-chain") == label


def test_discovery_names_validators_from_their_scripts_in_name_order(
    tmp_path, monkeypatch, write_path
):
    scripts = [
        str(write_path(tmp_path, name, 'TITLE = "STUB VALIDATION"\n'))
        for name in ("validate_b_two.py", "validate_a.py")
    ]
    monkeypatch.setattr(runner.glob, "glob", lambda _pattern: scripts)

    assert runner.discover_validators() == [
        ("a", "validate_a.py", "STUB"),
        ("b-two", "validate_b_two.py", "STUB"),
    ]


def test_launch_validator_passes_each_flag_once_and_logs_stderr(tmp_path, monkeypatch):
    captured = {}

    def popen(command, **kwargs):
        captured.update(kwargs, command=command)
        return _Process()

    monkeypatch.setattr(runner.subprocess, "Popen", popen)

    # focus-tree already gets --missing-icons from _VALIDATOR_EXTRA_FLAGS.
    process, stderr = runner.launch_validator(
        "validate_focus_tree.py",
        ["--missing-icons", "--staged"],
        str(tmp_path),
        "focus-tree",
        str(tmp_path),
    )
    stderr.close()

    assert isinstance(process, _Process)
    assert captured["command"][2:] == [
        "--path",
        str(tmp_path),
        "--output",
        str(tmp_path / "focus-tree.txt"),
        "--missing-icons",
        "--staged",
    ]
    assert captured["stderr"] is stderr
    assert stderr.name == str(tmp_path / "focus-tree.stderr.log")


def test_launch_validator_closes_the_stderr_log_when_the_launch_fails(
    tmp_path, monkeypatch
):
    handles = []

    def popen(_command, **kwargs):
        handles.append(kwargs["stderr"])
        raise OSError("cannot launch")

    monkeypatch.setattr(runner.subprocess, "Popen", popen)

    with pytest.raises(OSError, match="cannot launch"):
        runner.launch_validator(
            "validate_stub.py", [], str(tmp_path), "stub", str(tmp_path)
        )

    assert handles[0].closed


@pytest.mark.parametrize(
    ("sidecar", "counts"),
    [
        pytest.param(
            json.dumps(
                [{"severity": s} for s in ("error", "error", "warning", "info")]
            ),
            (2, 1),
            id="errors and warnings are counted",
        ),
        pytest.param("not json", (0, 0), id="unreadable sidecar"),
    ],
)
def test_read_validator_counts(tmp_path, write_path, sidecar, counts):
    write_path(tmp_path, "stub.json", sidecar)

    assert runner.read_validator_counts(str(tmp_path), "stub") == counts


def test_suite_bounds_concurrency_and_passes_a_worker_budget(tmp_path, monkeypatch):
    # Six validators on a budget that allows two at a time: the suite must not
    # launch all six at once, each with a pool of its own.
    monkeypatch.setattr(runner, "split_cpu_budget", lambda tasks: (2, 3))

    live = []
    peak = []
    flags = []

    def launch(_script, child_flags, _output_dir, name, _mod_path):
        flags.append(list(child_flags))
        live.append(name)
        peak.append(len(live))

        class _Tracked(_Process):
            def wait(self):
                live.remove(name)
                return 0

        return _Tracked(), io.StringIO()

    monkeypatch.setattr(runner, "launch_validator", launch)
    validators = [(f"v{i}", f"v{i}.py", f"V{i}") for i in range(6)]
    runner._run_suite(_args("text"), [], str(tmp_path), validators, str(tmp_path))

    assert max(peak) == 2
    assert all(f[-2:] == ["--workers", "3"] for f in flags)


def test_manual_texture_audit_is_not_auto_discovered():
    scripts = {script for _name, script, _label in runner.discover_validators()}
    assert "validate_unused_textures.py" not in scripts


def test_variables_run_passes_the_redundant_focus_flag_scan():
    assert runner._VALIDATOR_EXTRA_FLAGS["variables"] == ["--redundant-focus-flags"]


def test_decisions_run_passes_the_unannounced_category_scan():
    assert runner._VALIDATOR_EXTRA_FLAGS["decisions"] == ["--unannounced-categories"]


def test_ideas_run_passes_the_same_flags_as_the_ci_batch():
    spec = next(spec for spec in ALL_SPECS if spec.name == "ideas")
    assert runner._VALIDATOR_EXTRA_FLAGS["ideas"] == list(spec.args)
    assert spec.args == ("--missing-name-loc",)


def test_math_expressions_run_passes_the_clamp_bounds_check():
    assert runner._VALIDATOR_EXTRA_FLAGS["math-expressions"] == ["--clamp-bounds"]


def test_oob_units_run_does_not_enable_missing_equipment_factor():
    assert "oob-units" not in runner._VALIDATOR_EXTRA_FLAGS


def test_summary_totals_use_deduplicated_issues(tmp_path, monkeypatch):
    finding = {
        "severity": "error",
        "category": "same",
        "message": "same finding",
        "file": "a.txt",
        "line": 1,
    }
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([finding]))

    report_path = tmp_path / "report.json"
    code = runner._run_suite(
        _args("json", str(report_path), strict=True),
        [],
        str(tmp_path),
        [("one", "one.py", "One"), ("two", "two.py", "Two")],
        str(tmp_path),
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert code == 1
    assert payload["total_errors"] == 1
    assert payload["total_warnings"] == 0
    assert len(payload["issues"]) == 1


def test_clean_both_writes_text_and_json_reports(tmp_path, monkeypatch):
    report_path = tmp_path / "report.txt"
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = _run_stub(tmp_path, _args("both", str(report_path)))

    assert code == 0
    assert "ALL VALIDATIONS PASSED" in report_path.read_text(encoding="utf-8")
    try:
        json_text = (tmp_path / "report.json").read_text(encoding="utf-8")
    except OSError:
        raise
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise AssertionError("combined JSON report is invalid") from exc
    assert payload["total_errors"] == 0
    assert payload["issues"] == []


def test_json_output_honors_exact_output_path(tmp_path, monkeypatch):
    report_path = tmp_path / "report.json"
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = _run_stub(tmp_path, _args("json", str(report_path)))

    assert code == 0
    assert report_path.exists()
    assert not (tmp_path / "report.json.json").exists()
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError("JSON report is missing or invalid") from exc
    assert payload["total_errors"] == 0


def test_both_output_without_extension_uses_distinct_files(tmp_path, monkeypatch):
    report_path = tmp_path / "report"
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = _run_stub(tmp_path, _args("both", str(report_path)))

    assert code == 0
    assert "COMBINED VALIDATION REPORT" in report_path.read_text(encoding="utf-8")
    try:
        payload = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError("combined JSON report is missing or invalid") from exc
    assert payload["total_errors"] == 0


def test_json_without_output_prints_json_for_findings(tmp_path, monkeypatch, capsys):
    issues = [
        {
            "severity": "error",
            "category": "test-finding",
            "message": "broken café",
            "file": "test.txt",
            "line": 3,
        }
    ]
    monkeypatch.setattr(runner, "launch_validator", _launcher_with(issues, 1))

    code = _run_stub(tmp_path, _args("json", strict=True))

    captured = capsys.readouterr()
    try:
        payload = json.loads(captured.out)
    except json.JSONDecodeError as exc:
        raise AssertionError("stdout is not valid JSON") from exc
    assert code == 1
    assert payload["total_errors"] == 1
    assert payload["issues"][0]["message"] == "broken café"
    assert "VALIDATION FAILED" in captured.err


def test_persist_results_copies_json_sidecars(tmp_path, monkeypatch):
    issues = [
        {
            "severity": "error",
            "category": "test-finding",
            "message": "finding",
            "file": "test.txt",
            "line": 1,
        }
    ]
    monkeypatch.setattr(runner, "launch_validator", _launcher_with(issues))
    persist_dir = tmp_path / "persisted"

    code = _run_stub(tmp_path, _args("both", persist_results=str(persist_dir)))

    assert code == 0
    try:
        payload = json.loads((persist_dir / "stub.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError("persisted sidecar is missing or invalid") from exc
    assert payload == issues
    assert (persist_dir / runner.PERSISTENCE_MARKER).read_text(encoding="utf-8") == (
        "complete\n"
    )


def test_persist_results_writes_completion_marker_when_clean(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))
    persist_dir = tmp_path / "persisted"
    persist_dir.mkdir()
    (persist_dir / "stale.json").write_text("[]", encoding="utf-8")

    code = _run_stub(tmp_path, _args("both", persist_results=str(persist_dir)))

    assert code == 0
    assert list(persist_dir.glob("*.json")) == []
    assert (persist_dir / runner.PERSISTENCE_MARKER).read_text(encoding="utf-8") == (
        "complete\n"
    )


def test_persist_results_copy_failure_propagates(tmp_path, monkeypatch):
    # A copy failure must fail the run, never silently save a truncated
    # baseline under a valid-looking meta.
    issues = [
        {
            "severity": "error",
            "category": "test-finding",
            "message": "finding",
            "file": "test.txt",
            "line": 1,
        }
    ]
    monkeypatch.setattr(runner, "launch_validator", _launcher_with(issues))

    def broken_copy(_src, _dst):
        raise OSError("disk full")

    monkeypatch.setattr(runner.shutil, "copyfile", broken_copy)
    persist_dir = tmp_path / "persisted"
    marker = write_text(persist_dir / runner.PERSISTENCE_MARKER, "complete\n")

    with pytest.raises(OSError, match="disk full"):
        _run_stub(tmp_path, _args("both", persist_results=str(persist_dir)))

    # The marker of an earlier run must not vouch for this one.
    assert not marker.exists()


def test_crashed_validator_fails_run_without_strict(tmp_path, monkeypatch, capsys):
    # A validator that exits non-zero with no findings crashed. That is
    # infrastructure failure and must fail the run even when --strict is off.
    monkeypatch.setattr(
        runner,
        "launch_validator",
        _launcher_with([], returncode=2, stderr_log="Traceback\nlast line\n"),
    )

    code = _run_stub(tmp_path, _args("both", strict=False))

    stdout = capsys.readouterr().out
    assert code == 1
    assert "(crashed, exit code 2)" in stdout
    assert "    last line" in stdout


def test_clean_run_passes_without_strict(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([], returncode=0))

    code = _run_stub(tmp_path, _args("both", strict=False))

    assert code == 0


def test_findings_without_strict_do_not_fail(tmp_path, monkeypatch):
    # Ordinary findings (validator exits 0, reports errors) stay advisory in
    # non-strict mode — only crashes and --strict escalate to a non-zero exit.
    issues = [
        {
            "severity": "error",
            "category": "test-finding",
            "message": "finding",
            "file": "test.txt",
            "line": 1,
        }
    ]
    monkeypatch.setattr(
        runner, "launch_validator", _launcher_with(issues, returncode=0)
    )

    code = _run_stub(tmp_path, _args("both", strict=False))

    assert code == 0


def test_both_without_output_prints_json_and_human_report(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = _run_stub(tmp_path, _args("both"))

    stdout = capsys.readouterr().out
    assert code == 0
    assert '"total_errors": 0' in stdout
    assert "COMBINED VALIDATION REPORT" in stdout
    assert "ALL VALIDATIONS PASSED" in stdout


def test_warnings_only_run_reports_completed_with_warnings(
    tmp_path, monkeypatch, capsys
):
    warning = {
        "severity": "warning",
        "category": "advisory",
        "message": "worth a look",
        "file": "a.txt",
        "line": 4,
    }
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([warning]))

    code = _run_stub(tmp_path, _args("text", strict=True))

    stdout = capsys.readouterr().out
    assert code == 0
    assert "COMPLETED WITH WARNINGS" in stdout
    assert "1 warning(s)" in stdout


def test_launch_validator_reports_an_unwritable_output_dir(tmp_path):
    with pytest.raises(OSError):
        runner.launch_validator(
            "validate_stub.py", [], str(tmp_path / "gone"), "stub", str(tmp_path)
        )


def test_print_stderr_tail_stays_silent_for_an_empty_log(tmp_path, capsys, write_path):
    write_path(tmp_path, "stub.stderr.log", "\n\n")

    runner._print_stderr_tail(str(tmp_path), "stub")

    assert capsys.readouterr().out == ""


def test_print_stderr_tail_prints_only_the_last_lines(tmp_path, capsys, write_path):
    write_path(tmp_path, "stub.stderr.log", "one\ntwo\nthree\n")

    runner._print_stderr_tail(str(tmp_path), "stub", max_lines=2)

    assert capsys.readouterr().out == "    two\n    three\n"


def test_report_lists_errors_warnings_and_crashed_validators(tmp_path, write_path):
    issues = [
        {
            "severity": "error",
            "category": "cat",
            "message": "bad",
            "file": "a.txt",
            "line": 2,
        },
        {
            "severity": "warning",
            "category": "warn",
            "message": "care",
            "file": "b.txt",
            "line": 0,
        },
    ]
    write_path(tmp_path, "one.json", json.dumps(issues))

    report = runner.generate_combined_report(
        str(tmp_path), [("one", "one.py", "One")], ["Crashed"], use_colors=False
    )

    assert "1 ERROR(S)\n\n  a.txt (1 issue(s))\n    - a.txt:2: [cat] bad" in report
    # A finding with no line number is listed by file alone.
    assert "1 WARNING(S)\n\n  b.txt (1 issue(s))\n    - b.txt: [warn] care" in report
    assert "1 VALIDATOR(S) CRASHED (no output produced)\n\n  - Crashed" in report


def test_report_groups_several_issues_under_one_file(tmp_path, write_path):
    issues = [
        {
            "severity": "error",
            "category": "cat",
            "message": f"finding {n}",
            "file": "a.txt",
            "line": n,
        }
        for n in (2, 1)
    ]
    write_path(tmp_path, "one.json", json.dumps(issues))

    report = runner.generate_combined_report(
        str(tmp_path), [("one", "one.py", "One")], [], use_colors=False
    )

    assert "  a.txt (2 issue(s))" in report
    assert report.index("finding 1") < report.index("finding 2")


def test_json_report_write_failure_propagates(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    with pytest.raises(OSError):
        _run_stub(tmp_path, _args("json", str(tmp_path / "gone" / "report.json")))


def test_text_report_write_failure_propagates(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    with pytest.raises(OSError):
        _run_stub(tmp_path, _args("text", str(tmp_path / "gone" / "report.txt")))


def test_persist_results_makedirs_failure_propagates(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))
    monkeypatch.setattr(
        runner.os,
        "makedirs",
        lambda *a, **k: (_ for _ in ()).throw(OSError("read-only")),
    )

    with pytest.raises(OSError, match="read-only"):
        _run_stub(tmp_path, _args("both", persist_results=str(tmp_path / "persisted")))


def test_persist_results_tolerates_a_stale_sidecar_vanishing(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))
    persist_dir = tmp_path / "persisted"
    persist_dir.mkdir()
    (persist_dir / "stale.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(
        runner.os,
        "unlink",
        lambda path: (_ for _ in ()).throw(FileNotFoundError(path)),
    )

    assert _run_stub(tmp_path, _args("both", persist_results=str(persist_dir))) == 0


def test_persist_results_marker_write_failure_propagates(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))
    real_open = builtins.open

    def failing_open(file, *args, **kwargs):
        if str(file).endswith(runner.PERSISTENCE_MARKER):
            raise OSError("disk full")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", failing_open)

    with pytest.raises(OSError, match="disk full"):
        _run_stub(tmp_path, _args("both", persist_results=str(tmp_path / "persisted")))


def test_main_stays_quiet_when_the_cache_is_fresh(tmp_path, monkeypatch, capsys):
    calls = _run_main(monkeypatch, tmp_path)

    stdout = capsys.readouterr().out
    assert calls == [("stale", 7.0), ("run", [])]
    assert "Pruned stale" not in stdout
    assert "cleared and rebuilding" not in stdout


def test_main_reports_a_stale_cache_and_pruned_versions(tmp_path, monkeypatch, capsys):
    calls = _run_main(
        monkeypatch,
        tmp_path,
        "--cache-max-age-days",
        "2",
        stale=True,
        pruned=["v4", "v3"],
    )

    stdout = capsys.readouterr().out
    assert ("stale", 2.0) in calls
    assert "Cache older than 2 day(s)" in stdout
    assert "Pruned stale cache version(s): v3, v4" in stdout


def test_main_clear_cache_clears_and_restamps_instead_of_checking_age(
    tmp_path, monkeypatch, capsys
):
    calls = _run_main(monkeypatch, tmp_path, "--clear-cache", pruned=["v4"])

    stdout = capsys.readouterr().out
    assert calls[:2] == [("clear", str(tmp_path)), ("stamp", str(tmp_path))]
    assert [name for name, _value in calls] == ["clear", "stamp", "run"]
    assert "Cleared .validation_cache/" in stdout
    assert "Pruned stale" not in stdout


def test_main_forwards_the_run_flags_to_every_validator(tmp_path, monkeypatch):
    calls = _run_main(monkeypatch, tmp_path, "--staged", "--strict", "--no-color")

    assert calls[-1] == ("run", ["--staged", "--strict", "--no-color"])


def test_main_no_cache_sets_the_env_child_validators_inherit(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)

    _run_main(monkeypatch, tmp_path, "--no-cache")

    assert runner.os.environ["MD_NO_CACHE"] == "1"


@pytest.mark.parametrize("format_", ["text", "json"])
def test_main_prints_unicode_with_windows_pipe_encoding(tmp_path, monkeypatch, format_):
    buffers = [io.BytesIO(), io.BytesIO()]
    streams = [io.TextIOWrapper(buffer, encoding="cp1252") for buffer in buffers]
    monkeypatch.setattr(sys, "stdout", streams[0])
    monkeypatch.setattr(sys, "stderr", streams[1])
    monkeypatch.setattr(
        sys,
        "argv",
        ["runner", "--path", str(tmp_path), "--format", format_, "--no-color"],
    )
    monkeypatch.setattr(
        runner, "discover_validators", lambda: [("stub", "validate_stub.py", "Stub")]
    )
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    with pytest.raises(SystemExit) as exc:
        runner.main()

    for stream in streams:
        stream.flush()
    output = [buffer.getvalue().decode("utf-8") for buffer in buffers]
    assert exc.value.code == 0
    assert "✓ Stub" in output[format_ == "json"]
    if format_ == "json":
        assert json.loads(output[0])["total_errors"] == 0
