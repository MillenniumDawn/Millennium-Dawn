"""Accessibility baseline of the built pages. The module's own
SELF_TEST_FIXTURES hold the new-tab label cases."""

import sys

import check_accessibility_basics as a11y
import pytest
from shared.suite import write_text

_NEW_TAB = '<a> labeled "(opens in new tab)" without target="_blank" at line(s): 2'


def _page(body, html='<html lang="en">'):
    return f"{html}<main><h1>Title</h1>\n{body}</main></html>"


def test_self_test_fixtures_pass():
    assert a11y.run_self_test() == 0


def test_self_test_reports_a_fixture_that_goes_wrong(monkeypatch, capsys):
    monkeypatch.setattr(a11y, "SELF_TEST_FIXTURES", [("<a>x</a>", 1)])

    assert a11y.run_self_test() == 1
    assert "self-test failed" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("html", "issues"),
    [
        # A closing tag with no opening one and text outside a link are fine.
        pytest.param(_page("text</a>"), [], id="complete page"),
        pytest.param(
            _page("", html="<html>"), ['missing <html lang="...">'], id="no lang"
        ),
        pytest.param(
            _page("", html='<html lang=" ">'),
            ['missing <html lang="...">'],
            id="blank lang",
        ),
        pytest.param(
            '<html lang="en"><h2>Title</h2></html>',
            ["expected exactly one <main>, found 0"],
            id="no main",
        ),
        pytest.param(
            _page("</main><main>"),
            ["expected exactly one <main>, found 2"],
            id="two mains",
        ),
        pytest.param(
            '<html lang="en"><main></main></html>',
            ["page has no heading elements (<h1>-<h6>)"],
            id="no heading",
        ),
        pytest.param(
            _page('<img src="a">\n<img src="b" alt="">\n<img src="c">'),
            ["<img> without alt attribute at line(s): 2, 4"],
            id="images without alt, an empty alt is fine",
        ),
        pytest.param(
            _page("<a>Docs <span>(opens in new tab)</span></a>"),
            [_NEW_TAB],
            id="new tab label on a link that stays in the tab",
        ),
    ],
)
def test_check_file(tmp_path, html, issues):
    assert a11y.check_file(write_text(tmp_path / "page.html", html)) == issues


def test_run_lists_the_issues_of_each_page(tmp_path):
    write_text(tmp_path / "good.html", _page(""))
    bad = write_text(tmp_path / "bad.html", _page("", html="<html>")).resolve()
    # A directory named like a page is not read.
    (tmp_path / "folder.html").mkdir()

    assert a11y.run(tmp_path) == (
        False,
        'Accessibility baseline checks failed:\n- {}: missing <html lang="...">'.format(
            bad
        ),
    )


def test_run_passes_a_site_with_no_pages(tmp_path):
    assert a11y.run(tmp_path) == (
        True,
        f"Accessibility baseline checks passed for {tmp_path.resolve()}",
    )


def test_run_fails_when_the_site_directory_is_missing(tmp_path):
    passed, report = a11y.run(tmp_path / "missing")

    assert not passed
    assert report.startswith("ERROR: site directory does not exist")


def test_main_needs_a_site_directory(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["check_accessibility_basics.py"])

    assert a11y.main() == 2
    assert "--site-dir is required" in capsys.readouterr().out
