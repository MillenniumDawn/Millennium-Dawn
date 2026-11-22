"""Blocked raw HTML and duplicate hero titles in docs content. The module's
own SELF_TEST_CASES hold the masking cases; the tables here add the rest."""

from pathlib import Path

import check_content_html as content_html
import pytest
from shared.suite import write_text, write_tree

_PAGE = str(Path("content", "tutorials", "page.md"))
_DUPLICATE = (
    f"{_PAGE}: body starts with '# Same' but layout already renders H1 "
    "from frontmatter title"
)


@pytest.fixture
def content_root(tmp_path, monkeypatch):
    monkeypatch.setattr(content_html, "CONTENT_ROOT", tmp_path / "content")
    return tmp_path


def test_self_test_cases_pass():
    assert content_html.self_test() == 0


def test_self_test_reports_a_case_that_goes_wrong(monkeypatch, capsys):
    monkeypatch.setattr(content_html, "SELF_TEST_CASES", (("<script>", False),))

    assert content_html.self_test() == 1
    assert "FAILED" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("text", "issues"),
    [
        pytest.param(
            "`<script>`\n<iframe x>\n<object>\n<embed>\n<div onclick=x>",
            [
                "t.md:2: blocked <iframe>",
                "t.md:3: blocked <object>",
                "t.md:4: blocked <embed>",
                "t.md:5: blocked inline event handler",
            ],
            id="every blocked pattern, by line",
        ),
        pytest.param(
            "```\n<script>\n```\n<embed>",
            ["t.md:4: blocked <embed>"],
            id="a masked backtick fence keeps the line numbers",
        ),
        pytest.param(
            "~~~\n<script>\n~~~\n<embed>",
            ["t.md:4: blocked <embed>"],
            id="a masked tilde fence keeps the line numbers",
        ),
    ],
)
def test_scan_blocked_html(text, issues):
    assert content_html.scan_blocked_html(text, "t.md") == issues


@pytest.mark.parametrize(
    ("path", "text", "flagged"),
    [
        pytest.param(_PAGE, '---\ntitle: "Same"\n---\n# Same', True, id="repeated"),
        pytest.param(
            _PAGE,
            "---\ntitle: SAME\n---\n\n# Same\n",
            True,
            id="case and leading blank lines do not matter",
        ),
        pytest.param(
            _PAGE,
            "---\ntitle: Same\n---\n```\n# Other\n```\n# Same",
            True,
            id="a heading in fenced code is not the first heading",
        ),
        pytest.param(
            _PAGE, "---\ntitle: Same\n---\nIntro\n# Same", False, id="not first"
        ),
        pytest.param(_PAGE, "---\ntags: x\n---\n# Same", False, id="no title"),
        pytest.param(_PAGE, "# Same", False, id="no frontmatter"),
        pytest.param(
            "content/unlisted/page.md",
            "---\ntitle: Same\n---\n# Same",
            False,
            id="a collection with no hero title",
        ),
        pytest.param(
            "elsewhere/page.md",
            "---\ntitle: Same\n---\n# Same",
            False,
            id="outside the content root",
        ),
    ],
)
def test_duplicate_hero_title(content_root, path, text, flagged):
    issues = content_html.check_duplicate_hero_title(content_root / path, text)

    assert issues == ([_DUPLICATE] if flagged else [])


def test_check_file_reports_both_kinds_of_issue(content_root):
    page = write_text(
        content_root / _PAGE, '---\ntitle: "Same"\n---\n# Same\nRaw <script>'
    )

    assert content_html.check_file(page) == [
        f"{_PAGE}:5: blocked <script>",
        _DUPLICATE,
    ]


@pytest.mark.parametrize(
    ("files", "report"),
    [
        pytest.param(
            {"content/misc/clean.md": "---\ntitle: T\n---\ntext"},
            (
                True,
                "No blocked raw HTML patterns or duplicate hero titles found in "
                "content.",
            ),
            id="clean",
        ),
        pytest.param(
            {
                "content/misc/clean.md": "text",
                "content/tutorials/page.md": "<embed>",
                "content/tutorials/also.mdx": "<object>",
            },
            (
                False,
                "Content HTML / heading checks failed:\n"
                f"  {Path('content', 'tutorials', 'also.mdx')}:1: blocked <object>\n"
                f"  {_PAGE}:1: blocked <embed>",
            ),
            id="md and mdx files, in path order",
        ),
    ],
)
def test_run_scans_the_content_tree(content_root, files, report):
    write_tree(content_root, files)

    assert content_html.run() == report
