"""Unit tests for the docs-site checks' pure helpers.

Covers the edge cases hardened in the docs audit: inline-code / fenced-code
masking in the link-syntax scanner, same-origin vs external URL handling
in the OG image normalizer, and the build/dist gating in run_checks().
"""

import check_content_html as content_html
import check_docs
import check_link_syntax as link_syntax
import check_og_images as og
import pytest
from check_docs import Check, run_checks

from common import CheckResult


@pytest.mark.parametrize(
    "text, should_fail",
    [
        ("See the [Guide](/dev-resources/guide/).", False),
        ('A titled [link](/x/ "Title here").', False),
        ("Broken [Guide](/dev-resources/guide/", True),
        ("Empty [link]() here.", True),
        # Inline code is masked, so a `](` inside backticks is not a link.
        ("Inline code `[x](y` is not a link.", False),
        # Fenced code is skipped entirely.
        ("```\n[Guide](/broken/\n```", False),
        # A shorter run inside a longer fence does not close it.
        ("````\n[Guide](/broken/\n```\n[More](/broken2/\n````", False),
    ],
)
def test_scan_text(text, should_fail):
    assert bool(link_syntax.scan_text(text, "t.md")) is should_fail


def test_mask_inline_code_preserves_length():
    line = "a `code` b"
    masked = link_syntax.mask_inline_code(line)
    assert len(masked) == len(line)
    assert "code" not in masked


def test_link_syntax_self_test_passes():
    assert link_syntax.self_test() == 0


@pytest.mark.parametrize(
    "text, should_flag",
    [
        # Balanced inline code with angle brackets is masked, not flagged.
        ("Inline `<script>` in code is safe.", False),
        ("Sample `<button onclick=x>` in code.", False),
        # A <script> between stray unpaired backticks must still be flagged.
        ("Stray ``<script> between backticks.", True),
        ("A ` span ` and a real <script> tag.", True),
        ("Raw <script>alert(1)</script> tag.", True),
    ],
)
def test_scan_blocked_html(text, should_flag):
    assert bool(content_html.scan_blocked_html(text, "t.md")) is should_flag


def test_mask_code_preserves_length():
    text = "a `<x>` b"
    masked = content_html.mask_code(text)
    assert len(masked) == len(text)
    assert "<x>" not in masked


def test_content_html_self_test_passes():
    assert content_html.self_test() == 0


SITE = "https://millenniumdawn.github.io"


@pytest.mark.parametrize(
    "raw, baseurl, expected",
    [
        # Same-origin absolute URL: host dropped, base path stripped.
        (f"{SITE}/Millennium-Dawn/og.png", "/Millennium-Dawn", "/og.png"),
        # Root-relative URL with the base path.
        ("/Millennium-Dawn/x.png", "/Millennium-Dawn", "/x.png"),
        # External host is not ours to validate.
        ("https://cdn.example.com/og.png", "/Millennium-Dawn", None),
        # Non-path schemes (data URIs) have no leading-slash path.
        ("data:image/png;base64,AAAA", "", None),
        ("", "", None),
    ],
)
def test_normalize_meta_image_to_path(raw, baseurl, expected):
    assert og.normalize_meta_image_to_path(raw, baseurl=baseurl) == expected


def _result(name, passed, output=""):
    return CheckResult(name, passed, output, 0.0)


def _dist_stub(calls):
    def stub(checks, max_workers):
        calls.append([c.name for c in checks])
        return [_result(c.name, True) for c in checks]

    return stub


def test_astro_check_failure_does_not_skip_dist_when_build_passes(monkeypatch):
    calls = []
    monkeypatch.setattr(check_docs, "_run_dist_parallel", _dist_stub(calls))
    checks = [
        Check("astro check", "build", lambda: _result("astro check", False, "boom")),
        Check("build", "build", lambda: _result("build", True)),
        Check("links", "dist", lambda: _result("links", True)),
    ]

    results = run_checks(checks)

    assert calls == [["links"]]
    assert not any(r.output == "skipped: build failed" for r in results)


def test_build_failure_skips_dist(monkeypatch):
    calls = []
    monkeypatch.setattr(check_docs, "_run_dist_parallel", _dist_stub(calls))
    checks = [
        Check("build", "build", lambda: _result("build", False, "boom")),
        Check("links", "dist", lambda: _result("links", True)),
    ]

    results = run_checks(checks)

    assert calls == []
    dist_results = [r for r in results if r.name == "links"]
    assert dist_results == [CheckResult("links", False, "skipped: build failed", 0.0)]


def test_astro_check_failure_without_build_selected_still_runs_dist(monkeypatch):
    calls = []
    monkeypatch.setattr(check_docs, "_run_dist_parallel", _dist_stub(calls))
    checks = [
        Check("astro check", "build", lambda: _result("astro check", False, "boom")),
        Check("links", "dist", lambda: _result("links", True)),
    ]

    results = run_checks(checks)

    assert calls == [["links"]]
    assert not any(r.output == "skipped: build failed" for r in results)
