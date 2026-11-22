"""Internal links and assets of the built site."""

import io
import sys

import check_site_links as links
import pytest
from shared.suite import write_tree

_SKIPPED = (
    '<a href=""></a><a href="#part"></a><a href="?query"></a>'
    '<a href="HTTP://x/gone"></a><a href="https://x/gone"></a>'
    '<a href="mailto:x"></a><a href="tel:1"></a><a href="javascript:x"></a>'
    '<img src="data:x"><script src="//cdn/gone"></script>'
)
_EVERY_TAG = (
    '<a href="/m1"></a><img src="/m2"><script src="/m3"></script>'
    '<iframe src="/m4"></iframe><source src="/m5"><link href="/m6">'
    '<div src="/not-a-link"></div><a target="_blank"></a><link rel="stylesheet">'
)


def _site(tmp_path, html):
    """A site served under /base, with `html` as page/index.html."""
    return write_tree(
        tmp_path,
        {
            "index.html": "",
            "ok.html": "",
            "asset.png": "",
            "folder/index.html": "",
            "page/index.html": html,
        },
    )


@pytest.mark.parametrize(
    ("html", "broken"),
    [
        pytest.param('<a href="/ok"></a>', [], id="a page by its .html file"),
        pytest.param('<a href="/folder"></a>', [], id="a folder"),
        pytest.param('<a href="/"></a>', [], id="the root is index.html"),
        pytest.param('<a href="/base"></a>', [], id="the base path is the root"),
        pytest.param('<a href="/base/ok"></a>', [], id="the base path is dropped"),
        pytest.param('<a href="../ok"></a>', [], id="relative to the page"),
        pytest.param('<img src="/asset.png">', [], id="an asset"),
        pytest.param(_SKIPPED, [], id="empty, anchor, external and scheme links"),
        pytest.param(
            '<a href="/missing"></a>', [("/missing", "/missing")], id="no such page"
        ),
        pytest.param(
            '<link href="/ok.css">',
            [("/ok.css", "/ok.css")],
            id="a file with a suffix must exist as named",
        ),
        pytest.param(
            '<a href="/a/../gone?x=1#part"></a>',
            [("/a/../gone?x=1#part", "/gone")],
            id="query, hash and dot segments are dropped first",
        ),
        pytest.param(
            _EVERY_TAG,
            [(f"/m{n}", f"/m{n}") for n in range(1, 7)],
            id="href and src of each tag that loads something",
        ),
    ],
)
def test_links_of_a_page(tmp_path, html, broken):
    site = _site(tmp_path, html)

    errors = links.collect_broken_links(site, "/base")

    assert [(raw, target) for _page, raw, target in errors] == broken
    assert {page for page, _raw, _target in errors} <= {site / "page" / "index.html"}


def test_run_reports_each_broken_link_with_its_page(tmp_path):
    site = _site(tmp_path, '<a href="/gone"></a>').resolve()
    # A directory named like a page is not read.
    (site / "folder.html").mkdir()

    assert links.run(site) == (
        False,
        "Broken internal links/assets found:\n"
        f"- {site / 'page' / 'index.html'}: /gone -> /gone",
    )


def test_run_accepts_a_base_path_with_a_trailing_slash(tmp_path):
    site = _site(tmp_path, '<a href="/base/ok"></a>')

    assert links.run(site, "/base/") == (
        True,
        f"Link check passed for {site.resolve()}",
    )


def test_run_fails_when_the_site_directory_is_missing(tmp_path):
    passed, report = links.run(tmp_path / "missing")

    assert not passed
    assert report.startswith("ERROR: site directory does not exist")


def test_print_safe_writes_utf8_whatever_the_stream_encoding(monkeypatch):
    raw = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(raw, encoding="cp1252"))

    links.print_safe("page → target")

    assert raw.getvalue() == "page → target\n".encode("utf-8")
