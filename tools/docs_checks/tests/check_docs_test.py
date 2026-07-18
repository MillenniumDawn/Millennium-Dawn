"""Unit tests for the docs-site checks' pure helpers.

Covers the edge cases hardened in the docs audit: inline-code / fenced-code
masking in the link-syntax scanner, and same-origin vs external URL handling
in the OG image normalizer.
"""

import check_link_syntax as link_syntax
import check_og_images as og
import pytest


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
