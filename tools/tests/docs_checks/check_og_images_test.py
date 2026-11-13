"""Open Graph and Twitter image metadata in the built site."""

import check_og_images as og
import pytest
from shared.suite import write_text

SITE = "https://millenniumdawn.github.io"
CDN = "https://cdn.example.com/og.png"

_GOOD = {
    "og:image": "/base/image.png",
    "og:image:width": "1",
    "og:image:height": "1",
    "og:image:alt": "alt",
    "twitter:image": "/base/image.png",
}
_ALL_MISSING = [f"missing meta '{key}'" for key in _GOOD]


def _head(meta):
    tags = "".join(
        f'<meta property="{key}" content="{value}">' for key, value in meta.items()
    )
    return f'<head><meta property="og:title" content="Title">{tags}</head>'


def _issues(tmp_path, html):
    """Issues for index.html in a site served under /base that has image.png."""
    write_text(tmp_path / "image.png", "")
    page = write_text(tmp_path / "index.html", html)
    return og.check_html_file(tmp_path, page, "/base")


def test_meta_tags_are_collected_by_lowercased_property_or_name():
    parser = og.MetaCollector()

    parser.feed(
        '<link name="skipped" content="not a meta tag"><meta content="no key">'
        '<meta PROPERTY="OG:Title" content=" Title "><meta name="x" content="y">'
    )

    assert parser.meta == {"og:title": "Title", "x": "y"}


@pytest.mark.parametrize(
    ("raw", "baseurl", "expected"),
    [
        # Same-origin absolute URL: host dropped, base path stripped.
        (f"{SITE}/Millennium-Dawn/og.png", "/Millennium-Dawn", "/og.png"),
        ("/Millennium-Dawn/x.png", "/Millennium-Dawn", "/x.png"),
        ("/Millennium-Dawn", "/Millennium-Dawn", "/"),
        ("/a/../b.png", "", "/b.png"),
        # An external host is not ours to validate.
        (CDN, "/Millennium-Dawn", None),
        # Neither a data URI nor the bare origin has a path with a leading slash.
        ("data:image/png;base64,AAAA", "", None),
        (SITE, "", None),
        ("", "", None),
    ],
)
def test_normalize_meta_image_to_path(raw, baseurl, expected):
    assert og.normalize_meta_image_to_path(raw, baseurl=baseurl) == expected


@pytest.mark.parametrize(
    ("changes", "issues"),
    [
        pytest.param({}, [], id="complete"),
        pytest.param({"og:image": "/base"}, [], id="the site root is index.html"),
        pytest.param(
            {"og:image:width": ""},
            ["missing meta 'og:image:width'"],
            id="empty content counts as missing",
        ),
        pytest.param(
            {"og:image": CDN},
            [f"og:image is not a site-local URL: {CDN}"],
            id="og:image on another host",
        ),
        pytest.param(
            {"og:image": "/missing.png"},
            ["og:image target does not exist in site output: /missing.png"],
            id="og:image file missing",
        ),
        pytest.param(
            {"twitter:image": CDN},
            [f"twitter:image is not a site-local URL: {CDN}"],
            id="twitter:image on another host",
        ),
        pytest.param(
            {"twitter:image": "/missing.png"},
            ["twitter:image target does not exist in site output: /missing.png"],
            id="twitter:image file missing",
        ),
    ],
)
def test_image_meta_of_a_page(tmp_path, changes, issues):
    assert _issues(tmp_path, _head({**_GOOD, **changes})) == issues


def test_a_page_with_no_seo_meta_is_not_checked(tmp_path):
    assert _issues(tmp_path, "<head><title>Title</title></head>") == []


def test_any_seo_signal_makes_every_image_tag_required(tmp_path):
    card = '<meta name="twitter:card" content="summary">'

    assert _issues(tmp_path, card) == _ALL_MISSING


def test_meta_tags_in_the_body_are_ignored(tmp_path):
    body = '<body><meta property="og:image" content="/missing.png"></body>'

    assert _issues(tmp_path, _head(_GOOD) + body) == []


def test_run_lists_the_issues_of_each_page(tmp_path):
    write_text(tmp_path / "image.png", "")
    write_text(tmp_path / "clean.html", "<head><title>Title</title></head>")
    bad = write_text(tmp_path / "bad.html", _head({**_GOOD, "og:image:alt": ""}))

    assert og.run(tmp_path, "/base") == (
        False,
        f"OG metadata checks failed:\n- {bad.resolve()}: missing meta 'og:image:alt'",
    )


def test_run_passes_a_site_with_no_pages(tmp_path):
    assert og.run(tmp_path) == (
        True,
        f"OG metadata checks passed for {tmp_path.resolve()}",
    )


def test_run_fails_when_the_site_directory_is_missing(tmp_path):
    passed, report = og.run(tmp_path / "missing")

    assert not passed
    assert report.startswith("ERROR: site directory does not exist")
