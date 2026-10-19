"""The docs check runner: what each check runs, the build and dist gating, the
report and the command line."""

import sys
from concurrent.futures import Future

import check_docs
import pytest
from check_docs import Check, CheckResult


def _result(name, passed, output=""):
    return CheckResult(name, passed, output, 0.0)


def _check(name):
    return next(check for check in check_docs.ALL_CHECKS if check.name == name)


@pytest.mark.parametrize(
    ("name", "module", "args"),
    [
        ("link-syntax", "_link_syntax", ()),
        ("content-html", "_content_html", ()),
        ("flags", "_flags", ()),
        ("hygiene", "_hygiene", ("REPO_ROOT",)),
        ("dev-diaries", "_dev_diaries", ()),
        ("links", "_links", ("DIST_DIR", "SITE_BASEURL")),
        ("og", "_og", ("DIST_DIR", "SITE_BASEURL")),
        ("a11y", "_a11y", ("DIST_DIR",)),
        ("perf", "_perf", ("DIST_DIR",)),
    ],
)
def test_each_check_runs_its_own_module(tmp_path, monkeypatch, name, module, args):
    """`args` names the check_docs constants the module's run() is given."""
    calls = []
    monkeypatch.setattr(check_docs, "DIST_DIR", tmp_path)
    monkeypatch.setattr(
        getattr(check_docs, module),
        "run",
        lambda *given: calls.append(given) or (True, f" {name} report "),
    )
    check = _check(name)

    # A worker process runs a dist check by its name.
    dist = check.phase == "dist"
    result = check_docs._run_dist_check(name) if dist else check.fn()

    assert (result.name, result.passed, result.output) == (name, True, f"{name} report")
    assert calls == [tuple(getattr(check_docs, arg) for arg in args)]
    assert not dist or check_docs._DIST_CHECK_FNS[name] is check.fn


@pytest.mark.parametrize(
    ("name", "script"),
    [("lint:md", "lint:md"), ("astro check", "check"), ("build", "build")],
)
def test_bun_checks_run_their_package_script(monkeypatch, name, script):
    calls = []
    monkeypatch.setattr(
        check_docs, "run_cmd", lambda *given: calls.append(given) or _result(name, True)
    )

    assert _check(name).fn() == _result(name, True)
    assert calls == [(name, ["bun", "run", script])]


def test_a_check_that_raises_is_a_failed_result(monkeypatch):
    def boom():
        raise ValueError("boom")

    monkeypatch.setattr(check_docs._flags, "run", boom)

    result = check_docs.check_flags()

    assert (result.passed, result.output) == (False, "Exception: boom")


def test_a_dist_check_fails_without_a_built_site(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(check_docs, "DIST_DIR", tmp_path / "missing")
    monkeypatch.setattr(check_docs._links, "run", lambda *given: calls.append(given))

    assert check_docs.check_links() == _result(
        "links", False, "dist/ not found. Run build first."
    )
    assert calls == []


def test_a_worker_that_raises_is_a_failed_result_named_after_its_check():
    def worker_error():
        raise RuntimeError("worker")

    checks = [
        Check("ok", "sources", lambda: _result("ok", True)),
        Check("bad", "sources", worker_error),
    ]

    results = check_docs._run_parallel(checks, 2)

    assert sorted(results, key=lambda result: result.name) == [
        _result("bad", False, "Exception: worker"),
        _result("ok", True),
    ]


def test_dist_checks_go_to_the_process_pool_by_name(monkeypatch):
    pools = []

    class FakePool:
        def __init__(self, max_workers):
            pools.append(max_workers)

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return False

        def submit(self, fn, name):
            future = Future()
            future.set_result(fn(name))
            return future

    monkeypatch.setattr(check_docs, "ProcessPoolExecutor", FakePool)
    monkeypatch.setattr(
        check_docs, "_run_dist_check", lambda name: _result(name, True, "by name")
    )
    # The check's own fn is a closure, which a worker process cannot unpickle.
    checks = [Check("links", "dist", lambda: _result("links", False, "by fn"))]

    assert check_docs._run_dist_parallel(checks, 2) == [
        _result("links", True, "by name")
    ]
    assert pools == [2]


@pytest.mark.parametrize(
    ("checks", "skip_build", "expected"),
    [
        pytest.param(
            [("astro check", "build", False), ("build", "build", True)],
            False,
            [("astro check", False, ""), ("build", True, ""), ("links", True, "ran")],
            id="a failing astro check does not skip dist",
        ),
        pytest.param(
            [("astro check", "build", False)],
            False,
            [("astro check", False, ""), ("links", True, "ran")],
            id="a failing astro check with no build selected",
        ),
        pytest.param(
            [("build", "build", False)],
            False,
            [("build", False, ""), ("links", False, "skipped: build failed")],
            id="a failing build skips dist",
        ),
        pytest.param(
            [("source", "sources", True), ("build", "build", False)],
            True,
            [("source", True, ""), ("links", True, "ran")],
            id="skip_build leaves the build phase out",
        ),
    ],
)
def test_run_checks_gates_dist_on_the_build(monkeypatch, checks, skip_build, expected):
    """`checks` is (name, phase, passed), run ahead of a `links` dist check."""
    monkeypatch.setattr(
        check_docs,
        "_run_dist_parallel",
        lambda dist, _workers: [_result(check.name, True, "ran") for check in dist],
    )
    selected = [
        Check(name, phase, lambda name=name, passed=passed: _result(name, passed))
        for name, phase, passed in checks
    ]
    selected.append(Check("links", "dist", lambda: _result("links", True)))

    results = check_docs.run_checks(selected, skip_build=skip_build, max_workers=1)

    assert [(r.name, r.passed, r.output) for r in results] == expected


def test_report_shows_the_last_thirty_lines_of_a_failed_check(capsys):
    output = "\n".join(f"line{number}" for number in range(1, 32))

    check_docs.print_report([_result("ok", True), _result("bad", False, output)])

    report = capsys.readouterr().out
    assert "FAILED (1 of 2 checks)" in report
    assert "  line31\n" in report and "  line2\n" in report
    assert "  line1\n" not in report


def test_report_says_when_every_check_passed(capsys):
    check_docs.print_report([_result("ok", True)])

    assert "ALL PASSED (1 checks)." in capsys.readouterr().out


def _main(monkeypatch, *argv, passed=True):
    """Run main() with run_checks stubbed; return the exit code and its calls."""
    calls = []

    def run_checks(checks, skip_build, max_workers):
        calls.append(([check.name for check in checks], skip_build, max_workers))
        return [_result("x", passed)]

    monkeypatch.setattr(check_docs, "run_checks", run_checks)
    monkeypatch.setattr(sys, "argv", ["check_docs.py", *argv])
    return check_docs.main(), calls


def test_main_runs_every_check_by_default(monkeypatch):
    names = [check.name for check in check_docs.ALL_CHECKS]

    assert _main(monkeypatch) == (0, [(names, False, 4)])


def test_main_passes_the_selection_and_options_on(monkeypatch):
    code, calls = _main(
        monkeypatch, "--no-build", "--only", "og, link-syntax", "--max-workers", "1"
    )

    assert (code, calls) == (0, [(["link-syntax", "og"], True, 1)])


def test_main_exits_one_when_a_check_fails(monkeypatch, capsys):
    assert _main(monkeypatch, passed=False)[0] == 1
    assert "FAILED (1 of 1 checks)" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("argv", "code", "message"),
    [
        (["--list"], 0, "links                 (phase: dist)"),
        (["--only", "og,nope"], 1, "Unknown checks: nope"),
    ],
)
def test_main_exits_before_running_anything(monkeypatch, capsys, argv, code, message):
    assert _main(monkeypatch, *argv) == (code, [])
    assert message in capsys.readouterr().out
