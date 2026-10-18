"""Markdown link syntax check. The module's own SELF_TEST_CASES hold most of
the link shapes; the tables here add what they leave out."""

import sys

import check_link_syntax as link_syntax
import pytest
from shared.suite import write_text


def test_self_test_cases_pass():
    assert link_syntax.self_test() == 0


def test_self_test_reports_a_case_that_goes_wrong(monkeypatch, capsys):
    monkeypatch.setattr(link_syntax, "SELF_TEST_CASES", (("bad [x](/x", False),))

    assert link_syntax.self_test() == 1
    assert "FAILED" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("text", "errors"),
    [
        pytest.param(
            "fine\n  Empty [x]()  ",
            ["t.md:2: empty link target `]()` -- Empty [x]()"],
            id="empty target, with its line",
        ),
        pytest.param(
            "[ok](/x) [bad](/y",
            ["t.md:1:14: link missing closing `)` -- [ok](/x) [bad](/y"],
            id="the column is the unclosed link, not the first one",
        ),
        pytest.param(
            "`a` [bad](/y",
            ["t.md:1:9: link missing closing `)` -- `a` [bad](/y"],
            id="masked inline code keeps the column",
        ),
        pytest.param(
            "```\n[x](/hidden\n~~~\n[x](/also-hidden\n```",
            [],
            id="a tilde run does not close a backtick fence",
        ),
    ],
)
def test_scan_text(text, errors):
    assert link_syntax.scan_text(text, "t.md") == errors


@pytest.mark.parametrize(
    ("folder", "name"),
    [
        pytest.param("content", "bad.mdx", id="under the content root"),
        pytest.param("elsewhere", None, id="outside it, the full path"),
    ],
)
def test_scan_paths_names_files_from_the_content_root(
    tmp_path, monkeypatch, folder, name
):
    monkeypatch.setattr(link_syntax, "CONTENT_ROOT", tmp_path / "content")
    path = write_text(tmp_path / folder / "bad.mdx", "[x]()")

    (error,) = link_syntax.scan_paths([path])

    assert error.startswith(f"{name or path}:1: empty link target")


@pytest.mark.parametrize(
    ("text", "report"),
    [
        ("[x](/x)", (True, "No malformed Markdown links found.")),
        (
            "[x]()",
            (
                False,
                "Malformed Markdown links found:\n"
                "page.md:1: empty link target `]()` -- [x]()",
            ),
        ),
    ],
)
def test_run_scans_the_content_tree(tmp_path, monkeypatch, text, report):
    page = write_text(tmp_path / "page.md", text)
    monkeypatch.setattr(link_syntax, "CONTENT_ROOT", tmp_path)
    monkeypatch.setattr(link_syntax, "iter_markdown", lambda: [page])

    assert link_syntax.run() == report


@pytest.mark.parametrize(
    ("name", "code"),
    [
        pytest.param("bad.md", 1, id="markdown is scanned"),
        pytest.param("bad.txt", 0, id="other files are ignored"),
    ],
)
def test_main_scans_only_the_markdown_files_it_is_given(
    tmp_path, monkeypatch, capsys, name, code
):
    path = write_text(tmp_path / name, "[x]()")
    monkeypatch.setattr(sys, "argv", ["check_link_syntax.py", str(path)])

    assert link_syntax.main() == code
    assert ("empty link target" in capsys.readouterr().err) is bool(code)
