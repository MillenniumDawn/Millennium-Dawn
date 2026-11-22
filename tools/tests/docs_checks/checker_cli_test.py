"""The command line every docs checker shares: main() hands its arguments to
run(), prints the report and exits 0 or 1."""

import sys
from pathlib import Path

import check_accessibility_basics
import check_content_html
import check_dev_diaries
import check_docs_hygiene
import check_flag_images
import check_link_syntax
import check_og_images
import check_perf_budgets
import check_site_links
import pytest

_SITE = ["--site-dir", "site"]
# checker, argv, what run() is given, the stream a failing report goes to
_CHECKERS = [
    (check_accessibility_basics, _SITE, (Path("site"),), "out"),
    (check_content_html, [], (), "err"),
    (check_dev_diaries, [], (), "out"),
    (check_docs_hygiene, [], (Path("."), Path("docs")), "out"),
    (
        check_docs_hygiene,
        ["--repo-root", "repo", "--docs-dir", "site"],
        (Path("repo"), Path("site")),
        "out",
    ),
    (check_flag_images, [], (), "err"),
    (check_link_syntax, [], (), "err"),
    (check_og_images, _SITE, (Path("site"), ""), "out"),
    (check_og_images, [*_SITE, "--baseurl", "/base"], (Path("site"), "/base"), "out"),
    (check_perf_budgets, _SITE, (Path("site"),), "out"),
    (check_site_links, _SITE, (Path("site"), ""), "out"),
    (check_site_links, [*_SITE, "--baseurl", "/base"], (Path("site"), "/base"), "out"),
]
# The pre-commit hook runs this one, so it prints nothing when it passes.
_QUIET_ON_PASS = {check_link_syntax}


def _id(value):
    return getattr(value, "__name__", None)


@pytest.mark.parametrize(("checker", "argv", "args", "stream"), _CHECKERS, ids=_id)
def test_main_reports_the_verdict_of_run(
    monkeypatch, capsys, checker, argv, args, stream
):
    calls = []
    verdicts = iter([(True, "all fine"), (False, "went wrong")])
    monkeypatch.setattr(
        checker, "run", lambda *given: calls.append(given) or next(verdicts)
    )
    monkeypatch.setattr(sys, "argv", [f"{checker.__name__}.py", *argv])

    assert checker.main() == 0
    passing = capsys.readouterr()
    assert checker.main() == 1
    failing = capsys.readouterr()

    assert calls == [args, args]
    assert passing.out == ("" if checker in _QUIET_ON_PASS else "all fine\n")
    assert passing.err == ""
    assert getattr(failing, stream) == "went wrong\n"


@pytest.mark.parametrize(
    ("checker", "self_test"),
    [
        (check_accessibility_basics, "run_self_test"),
        (check_content_html, "self_test"),
        (check_dev_diaries, "self_test"),
        (check_link_syntax, "self_test"),
    ],
    ids=_id,
)
def test_self_test_flag_runs_the_self_test_alone(monkeypatch, checker, self_test):
    calls = []
    monkeypatch.setattr(checker, self_test, lambda: 7)
    monkeypatch.setattr(checker, "run", lambda *given: calls.append(given))
    monkeypatch.setattr(sys, "argv", [f"{checker.__name__}.py", "--self-test"])

    assert checker.main() == 7
    assert calls == []
