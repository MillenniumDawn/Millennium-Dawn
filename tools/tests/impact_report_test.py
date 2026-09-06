"""Tests for the trusted workflow_run impact reporter."""

import json
import zipfile
from pathlib import Path

import impact_report as ir
import pytest
from report_lib.checks_api import _conclusion_for
from report_lib.comment import REPORT_MARKER


def _event(**overrides):
    event = {
        "name": "Validator impact",
        "path": ".github/workflows/validator-impact.yml",
        "event": "pull_request",
        "repository": {"full_name": "o/r"},
        "id": 123,
        "run_attempt": 1,
        "workflow_id": 9,
        "run_number": 1,
        "created_at": "2026-01-01T00:00:00Z",
        "head_sha": "a" * 40,
        "head_branch": "feature",
        "head_repository": {"full_name": "o/r"},
        "conclusion": "success",
    }
    event.update(overrides)
    return event


def _pr(sha="a" * 40, repo="o/r", state="open", number=7):
    return {
        "number": number,
        "state": state,
        "head": {"sha": sha, "ref": "feature", "repo": {"full_name": repo}},
    }


def _artifact(aid=55, run_id=123, name=ir.IMPACT_ARTIFACT_NAME, expired=False):
    return {"id": aid, "name": name, "expired": expired, "workflow_run": {"id": run_id}}


def _recorder(posted, key, ok=True):
    def _stub(*_args, **_kwargs):
        posted[key] = True
        return ok, f"{key}"

    return _stub


def _manifest(results=None, selected=None):
    return {
        "mode": "impact",
        "batch": None,
        "selected": selected if selected is not None else ["events"],
        "results": (
            results
            if results is not None
            else [
                {
                    "name": "events",
                    "script": "validate_events.py",
                    "strict": True,
                    "returncode": 0,
                    "status": "ok",
                }
            ]
        ),
    }


def _write_results(results_dir: Path, manifest=None, extra_files=True):
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "validation-events.log").write_text(
        "OK\n", encoding="utf-8", newline=""
    )
    (results_dir / "validation-events.json").write_text(
        "[]", encoding="utf-8", newline=""
    )
    if extra_files:
        with open(
            results_dir / ir.MANIFEST_NAME, "w", encoding="utf-8", newline=""
        ) as h:
            json.dump(manifest or _manifest(), h)


# --- workflow run identity ----------------------------------------------------


def test_verify_workflow_run_accepts_our_run():
    assert ir.verify_workflow_run(_event(), "o/r") is None


def test_verify_workflow_run_rejects_foreign_workflows():
    assert ir.verify_workflow_run(_event(name="Other"), "o/r")
    assert ir.verify_workflow_run(_event(path=".github/workflows/other.yml"), "o/r")
    assert ir.verify_workflow_run(_event(event="push"), "o/r")
    assert ir.verify_workflow_run(_event(repository={"full_name": "other/r"}), "o/r")
    assert ir.verify_workflow_run(_event(id="123"), "o/r")
    assert ir.verify_workflow_run(_event(head_sha="nothex"), "o/r")
    assert ir.verify_workflow_run(_event(workflow_id="9"), "o/r")


def test_api_run_identity_and_newer_attempt_are_checked():
    event = _event()
    assert ir.verify_api_run(event, event, "o/r") is None
    assert (
        ir.verify_workflow_definition(
            event,
            {
                "id": 9,
                "name": "Validator impact",
                "path": ".github/workflows/validator-impact.yml",
            },
            "o/r",
        )
        is None
    )
    assert ir.verify_api_run(event, {**event, "head_sha": "b" * 40}, "o/r")
    assert ir.verify_api_run(event, {**event, "head_branch": "other"}, "o/r")
    assert (
        ir.newer_run_reason(event, [{**event, "run_attempt": 2}])
        == "a newer attempt superseded this workflow run"
    )
    assert (
        ir.newer_run_reason(
            event,
            [
                {
                    **event,
                    "head_repository": {"full_name": "other/fork"},
                    "run_number": 2,
                }
            ],
        )
        is None
    )
    assert (
        ir.newer_run_reason(event, [{**event, "head_branch": "other", "run_number": 2}])
        is None
    )
    assert ir.newer_run_reason(event, [{**event, "id": 124, "run_number": 2}])


# --- PR resolution ------------------------------------------------------------


def test_select_pull_request_matches_head_and_state():
    pr, reason = ir.select_pull_request(
        [_pr(), _pr(state="closed", number=8)], _event()
    )
    assert reason is None
    assert pr is not None
    assert pr["number"] == 7


def test_select_pull_request_requires_exactly_one_match():
    pr, reason = ir.select_pull_request([], _event())
    assert pr is None
    assert reason is not None

    pr, reason = ir.select_pull_request([_pr(number=1), _pr(number=2)], _event())
    assert pr is None
    assert reason is not None


def test_select_pull_request_rejects_fork_head_repo_mismatch():
    pr, reason = ir.select_pull_request([_pr(repo="forker/repo")], _event())
    assert pr is None
    assert reason is not None and "repo" in reason


def test_select_pull_request_accepts_fork_head_repo_match():
    pr, reason = ir.select_pull_request(
        [_pr(repo="forker/repo")], _event(head_repository={"full_name": "forker/repo"})
    )
    assert reason is None
    assert pr is not None
    assert pr["number"] == 7


# --- staleness ----------------------------------------------------------------


def test_staleness_detects_moved_head():
    reason = ir.staleness_reason(_event(), _pr(sha="b" * 40))
    assert reason is not None and "moved" in reason


def test_staleness_detects_closed_pr():
    reason = ir.staleness_reason(_event(), _pr(state="closed"))
    assert reason is not None and "open" in reason


def test_current_run_is_not_stale():
    assert ir.staleness_reason(_event(), _pr()) is None


# --- manifest -----------------------------------------------------------------


def test_load_manifest_accepts_valid(tmp_path):
    path = tmp_path / ir.MANIFEST_NAME
    with open(path, "w", encoding="utf-8", newline="") as h:
        json.dump(_manifest(), h)
    assert ir.load_manifest(path)["selected"] == ["events"]


def test_load_manifest_rejects_bad_json(tmp_path):
    path = tmp_path / ir.MANIFEST_NAME
    path.write_text("{not json", encoding="utf-8")
    try:
        ir.load_manifest(path)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_load_manifest_rejects_wrong_types(tmp_path):
    for bad in (
        _manifest(selected="events"),
        _manifest(results={"name": "events"}),
        _manifest(
            results=[
                {
                    "name": 1,
                    "script": "validate_events.py",
                    "strict": True,
                    "status": "ok",
                    "returncode": 0,
                }
            ]
        ),
        _manifest(
            results=[
                {
                    "name": "events",
                    "script": "validate_events.py",
                    "strict": True,
                    "status": "bogus",
                    "returncode": 0,
                }
            ]
        ),
        _manifest(
            results=[
                {
                    "name": "events",
                    "script": "validate_events.py",
                    "strict": True,
                    "status": "ok",
                    "returncode": "0",
                }
            ]
        ),
        {**_manifest(), "mode": "unknown"},
        {**_manifest(), "selected": ["events", "events"]},
        {
            **_manifest(),
            "results": [{**_manifest()["results"][0], "strict": 1}],
        },
        {
            **_manifest(),
            "results": [{**_manifest()["results"][0], "returncode": 1}],
        },
    ):
        path = tmp_path / ir.MANIFEST_NAME
        with open(path, "w", encoding="utf-8", newline="") as h:
            json.dump(bad, h)
        try:
            ir.load_manifest(path)
            raise AssertionError(f"expected ValueError for {bad}")
        except ValueError:
            pass


# --- cross-check and execution metadata ---------------------------------------


def _run(name="events", status="passed"):
    from report_lib.models import ValidatorRun

    return ValidatorRun(name=name, title=name.title(), status=status)


def test_cross_check_flags_missing_and_extra_results():
    manifest = _manifest(
        results=[
            {
                "name": "events",
                "script": "validate_events.py",
                "strict": True,
                "returncode": 0,
                "status": "ok",
            },
            {
                "name": "ghost",
                "script": "validate_ghost.py",
                "strict": True,
                "returncode": 0,
                "status": "ok",
            },
        ],
        selected=["events", "ghost"],
    )
    problems = ir.cross_check([_run()], manifest)
    assert any("ghost" in p and "no result files" in p for p in problems)
    problems = ir.cross_check([_run("stray")], manifest)
    assert any("stray" in p for p in problems)


def test_crash_with_empty_sidecar_cannot_look_passed():
    manifest = _manifest(
        results=[
            {
                "name": "events",
                "script": "validate_events.py",
                "strict": True,
                "returncode": 3,
                "status": "findings",
            }
        ]
    )
    runs = ir.apply_execution_metadata([_run()], manifest)
    assert runs[0].status == "failed"
    assert runs[0].errors == 1
    assert ir.cross_check([_run()], manifest)


def test_clean_manifest_keeps_passed_run():
    manifest = _manifest()
    runs = ir.apply_execution_metadata([_run()], manifest)
    assert runs[0].status == "passed"
    assert ir.cross_check(runs, manifest) == []


def test_cross_check_requires_both_artifact_files(tmp_path):
    root = tmp_path / "results"
    root.mkdir()
    (root / "validation-events.json").write_text("[]", encoding="utf-8")
    problems = ir.cross_check([_run()], _manifest(), ir.artifact_members(str(root)))
    assert any("exactly one log" in problem for problem in problems)


def test_loader_surfaces_selected_missing_validator(tmp_path):
    root = tmp_path / "results"
    root.mkdir()
    manifest = _manifest(
        selected=["events", "variables"],
        results=[
            _manifest()["results"][0],
            {
                "name": "variables",
                "script": "validate_variables.py",
                "strict": True,
                "returncode": 0,
                "status": "ok",
            },
        ],
    )
    (root / ir.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
    (root / "validation-events.log").write_text("OK\n", encoding="utf-8")
    (root / "validation-events.json").write_text("[]", encoding="utf-8")

    runs = {run.name: run for run in ir.load_all(str(root))}

    assert runs["variables"].status == "failed"
    assert runs["variables"].errors == 1


# --- artifact unpacking -------------------------------------------------------


def _zip_of(members, dest):
    zip_path = dest / "artifact.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return zip_path


def test_safe_extract_takes_flat_result_files(tmp_path):
    zip_path = _zip_of(
        {
            "validation-events.log": "log",
            "validation-events.json": "[]",
            "validation-events.stderr.log": "",
            ir.MANIFEST_NAME: "{}",
        },
        tmp_path,
    )
    extracted = ir.safe_extract(zip_path, tmp_path / "out")
    assert sorted(extracted) == [
        "batch-manifest.json",
        "validation-events.json",
        "validation-events.log",
        "validation-events.stderr.log",
    ]
    assert (tmp_path / "out" / "validation-events.log").read_text(
        encoding="utf-8"
    ) == "log"


def test_safe_extract_rejects_unexpected_members(tmp_path):
    zip_path = _zip_of(
        {"validation-events.log": "log", "evil.sh": "rm -rf /"}, tmp_path
    )
    try:
        ir.safe_extract(zip_path, tmp_path / "out")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    assert not (tmp_path / "out" / "evil.sh").exists()


def test_safe_extract_rejects_path_traversal(tmp_path):
    zip_path = _zip_of(
        {"../escape.json": "[]", "nested/dir/validation-x.log": "log"}, tmp_path
    )
    try:
        ir.safe_extract(zip_path, tmp_path / "out")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    assert list((tmp_path / "out").iterdir()) == []
    assert not (tmp_path.parent / "escape.json").exists()


def test_safe_extract_rejects_oversized_members(tmp_path, monkeypatch):
    monkeypatch.setattr(ir, "MAX_MEMBER_BYTES", 10)
    zip_path = _zip_of({"validation-events.log": "x" * 100}, tmp_path)
    try:
        ir.safe_extract(zip_path, tmp_path / "out")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_safe_extract_rejects_empty_artifact(tmp_path):
    zip_path = _zip_of({}, tmp_path)
    try:
        ir.safe_extract(zip_path, tmp_path / "out")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_artifact_redirect_must_use_github_storage_without_auth():
    with pytest.raises(ValueError, match="unexpected artifact redirect"):
        ir._open_artifact_redirect("https://evil.example/artifact.zip")


# --- artifact selection -------------------------------------------------------


def test_find_artifact_needs_exactly_one_live_match():
    artifact, reason = ir.find_artifact([_artifact()])
    assert reason is None
    assert artifact is not None
    assert artifact["id"] == 55
    artifact, reason = ir.find_artifact([])
    assert artifact is None and reason
    artifact, reason = ir.find_artifact([_artifact(expired=True)])
    assert artifact is None and reason
    artifact, reason = ir.find_artifact([_artifact(aid=1), _artifact(aid=2)])
    assert artifact is None and reason


# --- report assembly ----------------------------------------------------------


def test_report_is_clean_requires_complete_passes():
    assert ir.report_is_clean([], [])
    assert not ir.report_is_clean([_run()], ["problem"])
    assert not ir.report_is_clean([_run(status="failed")], [])
    assert ir.report_is_clean([_run()], [])


def test_warnings_post_but_do_not_fail():
    warning = _run(status="warnings")
    warning.warnings = 1
    assert not ir.report_should_fail([warning], [])
    assert not ir.report_is_clean([warning], [])


def test_malformed_sidecar_cannot_clear_impact_or_be_neutral(tmp_path):
    root = tmp_path / "results"
    _write_results(
        root, _manifest(results=[{**_manifest()["results"][0], "strict": False}])
    )
    (root / "validation-events.json").write_text(
        json.dumps(
            [
                {
                    "severity": "ERROR",
                    "category": "broken",
                    "message": "bad sidecar",
                }
            ]
        ),
        encoding="utf-8",
    )

    run = ir.load_all(str(root))[0]

    assert run.execution_complete is False
    assert _conclusion_for(run) == "failure"
    assert not ir.report_is_clean([run], [])
    assert ir.report_should_fail([run], [])


def test_workflow_event_payload_extracts_only_workflow_run(tmp_path):
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"workflow_run": _event()}), encoding="utf-8")
    assert ir.load_workflow_run_event(str(event_path))["id"] == 123


def test_workflow_event_payload_rejects_direct_untrusted_object(tmp_path):
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(_event()), encoding="utf-8")
    with pytest.raises(ValueError, match="workflow_run"):
        ir.load_workflow_run_event(str(event_path))


def test_report_body_uses_impact_marker_and_title():
    ctx = ir._report_ctx(_event(), "https://run", "7", "o/r")
    body, _ = ir.build_report_body([_run()], ctx)
    assert ir.IMPACT_MARKER in body
    assert f"# {ir.IMPACT_REPORT_TITLE}" in body
    assert REPORT_MARKER not in body
    assert "PR-code preview" in body


def test_empty_impact_report_is_an_explicit_noop():
    ctx = ir._report_ctx(_event(), "https://run", "7", "o/r")
    body, step_body = ir.build_report_body([], ctx)
    assert "No validators selected" in body
    assert "Nothing to run" in step_body


# --- end-to-end with a stubbed API -------------------------------------------


def _write_event(tmp_path, event):
    with open(tmp_path / "event.json", "w", encoding="utf-8", newline="") as handle:
        json.dump({"workflow_run": event}, handle)


def _api_serving(pull_payload, current_pr=None, artifacts=()):
    def fake(url, token):
        if "/commits/" in url:
            return pull_payload
        if "/actions/runs/123/artifacts" in url:
            return {"artifacts": list(artifacts)}
        if "/actions/workflows/9" in url:
            return {
                "id": 9,
                "name": "Validator impact",
                "path": ".github/workflows/validator-impact.yml",
                "repository": {"full_name": "o/r"},
            }
        if "/actions/runs/123" in url:
            return {
                **_event(),
                "workflow_id": 9,
                "run_number": 1,
                "created_at": "2026-01-01T00:00:00Z",
            }
        if "/actions/runs?" in url:
            return {
                "workflow_runs": [
                    {
                        **_event(),
                        "workflow_id": 9,
                        "run_number": 1,
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ]
            }
        if f"/pulls/{_pr()['number']}" in url:
            return current_pr if current_pr is not None else _pr()
        raise AssertionError(f"unexpected URL {url}")

    return fake


def _artifact_zip(source_dir, names, manifest):
    def fake_download(url, token, dest):
        with zipfile.ZipFile(dest, "w") as archive:
            for name in names:
                archive.writestr(name, (source_dir / name).read_text(encoding="utf-8"))
            archive.writestr(ir.MANIFEST_NAME, json.dumps(manifest))

    return fake_download


def _posting_stubs(monkeypatch, posted, checks=()):
    monkeypatch.setattr(ir, "clear_comment", _recorder(posted, "cleared"))
    monkeypatch.setattr(ir, "post_comment", _recorder(posted, "posted"))
    monkeypatch.setattr(ir, "post_checks", lambda *a, **k: list(checks))


def _run_bridge(tmp_path, monkeypatch, step_summary=None):
    if step_summary is None:
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    else:
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(step_summary))
    return ir.main(
        [
            "--workflow-run-json",
            str(tmp_path / "event.json"),
            "--results-dir",
            str(tmp_path / "unpack"),
            "--download-dir",
            str(tmp_path / "download"),
            "--output",
            str(tmp_path / "report.md"),
            "--github-repository",
            "o/r",
            "--github-token",
            "t",
        ]
    )


def _stub_artifact_flow(tmp_path, monkeypatch, results, manifest):
    monkeypatch.setattr(ir, "_api_json", _api_serving([_pr()], artifacts=[_artifact()]))
    monkeypatch.setattr(
        ir,
        "_download_to_file",
        _artifact_zip(
            results,
            ("validation-events.log", "validation-events.json"),
            manifest,
        ),
    )


def test_full_report_flow_clean_run_clears_comment(tmp_path, monkeypatch):
    results = tmp_path / "results"
    _write_results(results)
    _write_event(tmp_path, _event())
    _stub_artifact_flow(tmp_path, monkeypatch, results, _manifest())

    posted = {}
    _posting_stubs(monkeypatch, posted, checks=[("check", True, "ok")])

    assert _run_bridge(tmp_path, monkeypatch) == 0
    assert posted == {"cleared": True}


def test_empty_impact_run_clears_only_after_valid_manifest(tmp_path, monkeypatch):
    _write_event(tmp_path, _event())
    monkeypatch.setattr(ir, "_api_json", _api_serving([_pr()], artifacts=[_artifact()]))
    monkeypatch.setattr(
        ir,
        "_download_to_file",
        _artifact_zip(tmp_path, (), _manifest(selected=[], results=[])),
    )
    posted = {}
    _posting_stubs(monkeypatch, posted)

    assert _run_bridge(tmp_path, monkeypatch) == 0
    assert posted == {"cleared": True}
    assert "No validators selected" in (tmp_path / "report.md").read_text(
        encoding="utf-8"
    )


def test_complete_warning_run_posts_and_succeeds(tmp_path, monkeypatch):
    results = tmp_path / "results"
    _write_results(results)
    (results / "validation-events.json").write_text(
        json.dumps([{"severity": "warning", "category": "c", "message": "m"}]),
        encoding="utf-8",
    )
    _write_event(tmp_path, _event())
    _stub_artifact_flow(tmp_path, monkeypatch, results, _manifest())
    posted = {}
    _posting_stubs(monkeypatch, posted, checks=[("check", True, "neutral")])

    assert _run_bridge(tmp_path, monkeypatch) == 0
    assert posted == {"posted": True}


def test_missing_artifact_reports_incomplete_and_never_clears(tmp_path, monkeypatch):
    _write_event(tmp_path, _event())
    monkeypatch.setattr(ir, "_api_json", _api_serving([_pr()], artifacts=[]))

    posted = {}
    _posting_stubs(monkeypatch, posted)

    assert _run_bridge(tmp_path, monkeypatch) == 1
    assert posted == {"posted": True}
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert ir.IMPACT_MARKER in report
    assert "Impact report verification" in report


def test_stale_run_reports_incomplete(tmp_path, monkeypatch):
    results = tmp_path / "results"
    _write_results(results)
    _write_event(tmp_path, _event())

    monkeypatch.setattr(
        ir,
        "_api_json",
        _api_serving([_pr()], current_pr=_pr(sha="b" * 40), artifacts=[_artifact()]),
    )
    monkeypatch.setattr(
        ir,
        "_download_to_file",
        _artifact_zip(
            results,
            ("validation-events.log", "validation-events.json"),
            _manifest(),
        ),
    )

    bodies = []
    step_path = tmp_path / "summary.md"

    def fake_post(owner, repo, num, body, token, **kwargs):
        bodies.append(body)
        return True, "posted"

    monkeypatch.setattr(ir, "post_comment", fake_post)
    monkeypatch.setattr(ir, "clear_comment", lambda *a, **k: (True, "cleared"))
    monkeypatch.setattr(ir, "post_checks", lambda *a, **k: [])

    code = _run_bridge(tmp_path, monkeypatch, step_summary=step_path)

    assert code == 1
    assert len(bodies) == 0
    assert "stale run" in step_path.read_text(encoding="utf-8")


def test_malformed_manifest_artifact_reports_incomplete(tmp_path, monkeypatch):
    _write_event(tmp_path, _event())
    monkeypatch.setattr(ir, "_api_json", _api_serving([_pr()], artifacts=[_artifact()]))

    def fake_download(url, token, dest):
        with zipfile.ZipFile(dest, "w") as archive:
            archive.writestr("validation-events.log", "log")
            archive.writestr(ir.MANIFEST_NAME, "{broke")

    monkeypatch.setattr(ir, "_download_to_file", fake_download)
    _posting_stubs(monkeypatch, {})

    assert _run_bridge(tmp_path, monkeypatch) == 1


def test_failed_impact_run_reports_incomplete(tmp_path, monkeypatch):
    _write_event(tmp_path, _event(conclusion="failure"))
    monkeypatch.setattr(ir, "_api_json", _api_serving([_pr()], artifacts=[_artifact()]))

    posted = {}
    monkeypatch.setattr(ir, "post_comment", _recorder(posted, "posted"))
    monkeypatch.setattr(ir, "post_checks", lambda *a, **k: [])

    assert _run_bridge(tmp_path, monkeypatch) == 1
    assert posted == {"posted": True}
