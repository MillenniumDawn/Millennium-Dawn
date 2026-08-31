import concurrent.futures
import subprocess
import sys
from pathlib import Path

import check_accessibility_basics as a11y
import check_content_html as content_html
import check_dev_diaries as diaries
import check_docs as docs
import check_docs_hygiene as hygiene
import check_flag_images as flags
import check_link_syntax as link_syntax
import check_og_images as og
import check_perf_budgets as perf
import check_site_links as links

import common


def write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return path


class TestCommon:
    def test_run_cmd_reports_result_and_failures(self, monkeypatch):
        calls = []

        def completed(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return subprocess.CompletedProcess(cmd, 3, "out\n", "err\n")

        monkeypatch.setattr(common.subprocess, "run", completed)
        result = common.run_cmd("check", ["tool", "--flag"], Path("work"), 2.5)
        assert result.name == "check"
        assert not result.passed
        assert result.output == "out\nerr"

        def successful(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, "ok\n", "")

        monkeypatch.setattr(common.subprocess, "run", successful)
        assert common.run_cmd("check", ["tool"]).passed
        assert calls == [
            (
                ["tool", "--flag"],
                {
                    "capture_output": True,
                    "text": True,
                    "cwd": Path("work"),
                    "timeout": 2.5,
                },
            )
        ]

        def missing(*_args, **_kwargs):
            raise FileNotFoundError

        monkeypatch.setattr(common.subprocess, "run", missing)
        assert "command not found: tool" in common.run_cmd("check", ["tool"]).output

        def timed_out(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(["tool"], 2.5)

        monkeypatch.setattr(common.subprocess, "run", timed_out)
        assert (
            common.run_cmd("check", ["tool"], timeout=2.5).output
            == "timed out after 2s"
        )

    def test_iter_markdown_is_stable_and_deduplicates(self, tmp_path, monkeypatch):
        first = write(tmp_path / "z.md", "")
        second = write(tmp_path / "a.mdx", "")
        monkeypatch.setattr(common, "MARKDOWN_GLOBS", ("**/*.md", "**/*.md"))
        assert list(common.iter_markdown(tmp_path)) == [first]
        monkeypatch.setattr(common, "MARKDOWN_GLOBS", ("**/*.md", "**/*.mdx"))
        assert list(common.iter_markdown(tmp_path)) == [first, second]


class TestHygiene:
    def test_git_ls_files_builds_both_commands(self, monkeypatch):
        calls = []

        def output(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return "docs/a.md\n\n"

        monkeypatch.setattr(hygiene.subprocess, "check_output", output)
        assert hygiene.git_ls_files(Path("repo")) == ["docs/a.md"]
        assert hygiene.git_ls_files(Path("repo"), "docs/") == ["docs/a.md"]
        assert calls == [
            (
                ["git", "-C", "repo", "ls-files"],
                {"text": True, "encoding": "utf-8", "timeout": 60},
            ),
            (
                ["git", "-C", "repo", "ls-files", "--", "docs/"],
                {"text": True, "encoding": "utf-8", "timeout": 60},
            ),
        ]

    def test_path_and_reference_helpers_cover_asset_kinds(self):
        prefix = "docs/"
        assert (
            hygiene.tracked_asset_to_web_path(
                "other/", "docs/public/assets/images/a.png"
            )
            is None
        )
        assert (
            hygiene.tracked_asset_to_web_path(prefix, "docs/public/assets/images/a.png")
            == "/assets/images/a.png"
        )
        assert (
            hygiene.tracked_asset_to_web_path(
                prefix, "docs/public/assets/downloads/a.zip"
            )
            == "/assets/downloads/a.zip"
        )
        assert (
            hygiene.tracked_asset_to_web_path(prefix, "docs/src/assets/images/a.png")
            == "/assets/images/a.png"
        )
        assert hygiene.tracked_asset_to_web_path(prefix, "docs/src/other/a.png") is None

        assert hygiene.reference_needles_for_web_path("/other/a.png") == [
            "/other/a.png"
        ]
        needles = hygiene.reference_needles_for_web_path("/assets/images/a.png")
        assert needles == [
            "/assets/images/a.png",
            "@/assets/images/a.png",
            "assets/images/a.png",
            "src/assets/images/a.png",
        ]
        assert hygiene.asset_is_referenced(
            "/assets/images/a.png", "src/assets/images/a.png"
        )
        assert not hygiene.asset_is_referenced("/assets/images/a.png", "no reference")
        hygiene.ALLOW_UNUSED_ASSETS.add("/other/a.png")
        try:
            assert hygiene.asset_is_referenced("/other/a.png", "")
        finally:
            hygiene.ALLOW_UNUSED_ASSETS.remove("/other/a.png")

    def test_find_unused_assets_uses_text_sources_and_ignores_assets(self, tmp_path):
        write(tmp_path / "docs/src/page.md", "assets/images/used.png")
        write(tmp_path / "docs/src/ignored.bin", "unused")
        tracked = [
            "outside.txt",
            "docs/src/page.md",
            "docs/src/ignored.bin",
            "docs/public/assets/images/used.png",
            "docs/public/assets/images/unused-temp.png",
            "docs/public/assets/downloads/file.zip",
            "docs/src/assets/images/source.png",
        ]
        issues = hygiene.find_unused_assets(tmp_path, Path("docs"), tracked)
        assert issues == [
            "Unused docs asset tracked: docs/public/assets/images/unused-temp.png",
            "Unused docs asset tracked: docs/public/assets/downloads/file.zip",
            "Unused docs asset tracked: docs/src/assets/images/source.png",
        ]

    def test_run_normalizes_absolute_docs_dir_and_reports_rules(
        self, tmp_path, monkeypatch
    ):
        repo = tmp_path / "repo"
        repo.mkdir()
        write(repo / "docs/.bundle/config", "")
        write(repo / "docs/public/assets/images/photo-temp.png", "")
        write(repo / "docs/public/assets/images/unused.png", "")
        write(repo / "docs/src/page.md", "")
        tracked = [
            "outside.txt",
            "docs/missing.md",
            "docs/.bundle/config",
            "docs/public/assets/images/photo-temp.png",
            "docs/public/assets/images/unused.png",
            "docs/src/page.md",
        ]
        monkeypatch.setattr(hygiene, "git_ls_files", lambda *_args: tracked)
        passed, report = hygiene.run(repo, repo / "docs")
        assert not passed
        assert "Bundler local config" in report
        assert "Temp-named docs asset" in report
        assert "Unused docs asset tracked" in report
        passed, report = hygiene.run(repo, tmp_path / "outside-docs")
        assert not passed
        assert "not inside repo-root" in report

    def test_run_success_and_cli_exit_paths(self, tmp_path, monkeypatch, capsys):
        repo = tmp_path / "repo"
        write(repo / "docs/src/page.md", "/assets/images/ok.png")
        write(repo / "docs/public/assets/images/ok.png", "")
        monkeypatch.setattr(
            hygiene,
            "git_ls_files",
            lambda *_args: [
                "docs/src/page.md",
                "docs/public/assets/images/ok.png",
            ],
        )
        assert hygiene.run(repo)[0]
        monkeypatch.setattr(
            sys, "argv", ["check_docs_hygiene", "--repo-root", str(repo)]
        )
        assert hygiene.main() == 0
        assert "passed" in capsys.readouterr().out
        monkeypatch.setattr(hygiene, "run", lambda *_args: (False, "bad"))
        assert hygiene.main() == 1
        assert capsys.readouterr().out == "bad\n"

    def test_parse_args(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["x", "--repo-root", "r", "--docs-dir", "d"])
        args = hygiene.parse_args()
        assert args.repo_root == "r"
        assert args.docs_dir == "d"


class TestAccessibility:
    def test_parser_collects_signals_and_new_tab_misuse(self):
        parser = a11y.A11yParser()
        parser.feed(
            '<html lang="en"><main><h1>Title</h1><h2>Sub</h2>'
            '<img src="ok" alt="ok"><img src="bad">'
            '<a target="_blank">Good <span>(opens in new tab)</span></a>'
            "<a>Bad (opens in new tab)</a><a>plain</a></main></html>"
        )
        assert parser.html_lang_seen
        assert parser.main_count == 1
        assert parser.heading_count == 2
        assert parser.images_missing_alt == [1]
        assert parser.misleading_new_tab_links == [1]
        parser.handle_endtag("a")
        parser.handle_data("outside")

        empty = a11y.A11yParser()
        empty.feed('<html lang=" "><main></main></html>')
        assert not empty.html_lang_seen

    def test_check_file_and_run_cover_clean_failure_missing_and_iteration(
        self, tmp_path
    ):
        bad = write(
            tmp_path / "bad.html",
            '<html><main><img src="x"><a>(opens in new tab)</a></main></html>',
        )
        good = write(
            tmp_path / "good.html",
            '<html lang="en"><main><h1>Ok</h1></main></html>',
        )
        (tmp_path / "directory.html").mkdir()
        issues = a11y.check_file(bad)
        assert any("missing <html lang" in issue for issue in issues)
        assert any("without alt" in issue for issue in issues)
        assert any("new tab" in issue for issue in issues)
        assert a11y.check_file(good) == []
        assert set(a11y.iter_html_files(tmp_path)) == {bad, good}
        passed, report = a11y.run(tmp_path)
        assert not passed and "bad.html" in report
        empty = tmp_path / "empty"
        empty.mkdir()
        assert a11y.run(empty)[0]
        assert not a11y.run(tmp_path / "missing")[0]

    def test_self_test_and_cli_paths(self, monkeypatch, capsys, tmp_path):
        fixtures = a11y.SELF_TEST_FIXTURES
        assert a11y.run_self_test() == 0
        monkeypatch.setattr(a11y, "SELF_TEST_FIXTURES", [("<a>x</a>", 1)])
        assert a11y.run_self_test() == 1
        assert "failed" in capsys.readouterr().out.lower()
        monkeypatch.setattr(a11y, "SELF_TEST_FIXTURES", fixtures)
        monkeypatch.setattr(sys, "argv", ["a11y", "--self-test"])
        assert a11y.main() == 0
        monkeypatch.setattr(sys, "argv", ["a11y"])
        assert a11y.main() == 2
        assert "required" in capsys.readouterr().out
        monkeypatch.setattr(a11y, "run", lambda _path: (True, "ok"))
        monkeypatch.setattr(sys, "argv", ["a11y", "--site-dir", str(tmp_path)])
        assert a11y.main() == 0
        monkeypatch.setattr(a11y, "run", lambda _path: (False, "bad"))
        assert a11y.main() == 1

    def test_parse_args(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["x", "--site-dir", "site"])
        assert a11y.parse_args().site_dir == "site"


class TestPerformance:
    def test_run_checks_budgets_and_empty_index(self, tmp_path):
        site = tmp_path / "site"
        site.mkdir()
        write(site / "small.txt", "ok")
        write(site / "small.css", "ok")
        write(site / "small.png", "ok")
        (site / "folder.html").mkdir()
        assert perf.run(site) == (
            True,
            f"Performance budget checks passed for {site.resolve()}",
        )
        assert not perf.run(tmp_path / "missing")[0]

        write(site / "index.html", "x" * (perf.INDEX_HTML_BUDGET + 1))
        write(site / "large.css", "x" * (perf.BUDGETS_BYTES[".css"] + 1))
        write(site / "large.js", "x" * (perf.BUDGETS_BYTES[".js"] + 1))
        write(site / "large.html", "x" * (perf.BUDGETS_BYTES[".html"] + 1))
        write(site / "large.jpg", "x" * (perf.MAX_IMAGE_BYTES + 1))
        passed, report = perf.run(site)
        assert not passed
        assert report.count("exceeds") == 5

    def test_cli_paths(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr(sys, "argv", ["perf", "--site-dir", str(tmp_path)])
        assert perf.main() == 0
        assert "passed" in capsys.readouterr().out
        monkeypatch.setattr(perf, "run", lambda _path: (False, "bad"))
        assert perf.main() == 1
        assert capsys.readouterr().out == "bad\n"
        monkeypatch.setattr(sys, "argv", ["perf", "--site-dir", "s"])
        assert perf.parse_args().site_dir == "s"


class TestSiteLinks:
    def test_collector_and_normalization(self, tmp_path):
        parser = links.LinkCollector()
        parser.feed(
            '<a href="/a"><img src="/image.png"></a>'
            '<script src="/script.js"></script><iframe src="/frame"></iframe>'
            '<source src="/source"></source><link href="/style.css">'
            '<link rel="stylesheet"><a target="_blank"></a><div src="ignored"></div>'
        )
        assert parser.links == [
            "/a",
            "/image.png",
            "/script.js",
            "/frame",
            "/source",
            "/style.css",
        ]
        page = write(tmp_path / "docs" / "page" / "index.html", "")
        site = tmp_path / "docs"
        assert links.normalize_target("", page, site, "") is None
        assert links.normalize_target("#", page, site, "") is None
        assert links.normalize_target("#part", page, site, "") is None
        for raw in (
            "HTTP://x",
            "https://x",
            "mailto:x",
            "tel:x",
            "javascript:x",
            "data:x",
            "//cdn/x",
        ):
            assert links.normalize_target(raw, page, site, "") is None
        assert (
            links.normalize_target("/Millennium-Dawn", page, site, "/Millennium-Dawn")
            == "/"
        )
        assert (
            links.normalize_target("/Millennium-Dawn/a", page, site, "/Millennium-Dawn")
            == "/a"
        )
        assert (
            links.normalize_target("/other", page, site, "/Millennium-Dawn") == "/other"
        )
        assert links.normalize_target("/a/../b", page, site, "") == "/b"
        assert links.normalize_target("../other", page, site, "") == "/other"
        assert links.strip_query_and_hash(" /a?x#y ") == "/a"

    def test_path_resolution_iteration_and_collection(self, tmp_path):
        site = tmp_path / "site"
        page = write(
            site / "page" / "index.html",
            '<a href="../ok"></a><img src="/asset.png"><a href="/missing"></a>',
        )
        write(site / "ok.html", "")
        write(site / "asset.png", "")
        (site / "folder.html").mkdir()
        assert links.path_exists_in_site("/", site) is False
        write(site / "index.html", "")
        assert links.path_exists_in_site("/", site)
        assert links.path_exists_in_site("/asset.png", site)
        assert links.path_exists_in_site("/ok", site)
        write(site / "folder" / "index.html", "")
        assert links.path_exists_in_site("/folder", site)
        assert not links.path_exists_in_site("/none", site)
        assert links.path_exists_in_site("/missing.css", site) is False
        assert set(links.iter_html_files(site)) == {
            site / "index.html",
            site / "ok.html",
            site / "folder" / "index.html",
            page,
        }
        errors = links.collect_broken_links(site, "")
        assert [(raw, normalized) for _, raw, normalized in errors] == [
            ("/missing", "/missing")
        ]
        assert not links.run(site)[0]
        empty = tmp_path / "empty"
        empty.mkdir()
        assert links.run(empty)[0]
        assert not links.run(tmp_path / "missing")[0]

    def test_cli_and_safe_output_paths(self, monkeypatch, capsys, tmp_path):
        links.print_safe("café")
        assert "café" in capsys.readouterr().out
        monkeypatch.setattr(
            sys,
            "argv",
            ["links", "--site-dir", str(tmp_path), "--baseurl", "/base/"],
        )
        assert links.main() == 0
        monkeypatch.setattr(links, "run", lambda *_args: (False, "bad"))
        assert links.main() == 1
        assert "bad" in capsys.readouterr().out
        monkeypatch.setattr(sys, "argv", ["links", "--site-dir", "s"])
        args = links.parse_args()
        assert args.site_dir == "s"
        assert args.baseurl == ""


class TestOgImages:
    def test_meta_collection_and_normalization(self, tmp_path):
        parser = og.MetaCollector()
        parser.feed(
            '<title>x</title><meta content="ignored"><meta PROPERTY="OG:Title" '
            'content=" Title "><meta name="x" content="y">'
        )
        assert parser.meta == {"og:title": "Title", "x": "y"}
        assert og.has_seo_meta({}) is False
        assert og.has_seo_meta({"twitter:card": "summary"})
        assert og.normalize_meta_image_to_path("", "") is None
        assert og.normalize_meta_image_to_path("https://cdn.example/x.png", "") is None
        assert (
            og.normalize_meta_image_to_path("https://millenniumdawn.github.io", "")
            is None
        )
        assert og.normalize_meta_image_to_path("relative.png", "") is None
        assert (
            og.normalize_meta_image_to_path(
                "https://millenniumdawn.github.io/Millennium-Dawn/x.png",
                "/Millennium-Dawn",
            )
            == "/x.png"
        )
        assert (
            og.normalize_meta_image_to_path("/Millennium-Dawn", "/Millennium-Dawn")
            == "/"
        )
        assert og.normalize_meta_image_to_path("/a/../b.png", "") == "/b.png"
        site = tmp_path / "site"
        write(site / "index.html", "")
        write(site / "image.png", "")
        assert og.asset_exists(site, "/")
        assert og.asset_exists(site, "/image.png")
        assert not og.asset_exists(site, "/missing.png")

    def test_check_file_run_and_cli_boundaries(self, tmp_path, monkeypatch, capsys):
        site = tmp_path / "site"
        image = write(site / "image.png", "")
        clean = write(site / "clean.html", "<head><title>Title</title></head>")
        assert og.check_html_file(site, clean, "") == []
        no_head = write(
            site / "no-head.html", '<meta property="og:title" content="Title">'
        )
        no_head_issues = og.check_html_file(site, no_head, "")
        assert "missing meta 'twitter:image'" in no_head_issues
        bad = write(
            site / "bad.html",
            '<head><meta property="og:title" content="Title">'
            '<meta property="og:image" content="https://cdn.example/x.png">'
            '<meta name="twitter:image" content="/missing.png"></head>'
            '<body><meta property="og:image" content="/ignored.png"></body>',
        )
        issues = og.check_html_file(site, bad, "")
        assert "missing meta 'og:image:width'" in issues
        assert any(
            issue.startswith("og:image is not a site-local URL") for issue in issues
        )
        assert any(
            issue.startswith("twitter:image target does not exist") for issue in issues
        )
        passing = write(
            site / "passing.html",
            '<head><meta property="og:title" content="Title">'
            '<meta property="og:image" content="/image.png">'
            '<meta property="og:image:width" content="1">'
            '<meta property="og:image:height" content="1">'
            '<meta property="og:image:alt" content="image">'
            '<meta name="twitter:image" content="/image.png"></head>',
        )
        assert passing.exists() and image.exists()
        assert not og.run(site)[0]
        empty = tmp_path / "empty"
        empty.mkdir()
        assert og.run(empty)[0]
        assert not og.run(tmp_path / "missing")[0]
        monkeypatch.setattr(
            sys, "argv", ["og", "--site-dir", str(empty), "--baseurl", "/base"]
        )
        assert og.main() == 0
        monkeypatch.setattr(og, "run", lambda *_args: (False, "bad"))
        assert og.main() == 1
        assert "bad" in capsys.readouterr().out
        monkeypatch.setattr(sys, "argv", ["og", "--site-dir", "s"])
        assert og.parse_args().baseurl == ""

    def test_missing_local_og_image_is_reported(self, tmp_path):
        site = tmp_path / "site"
        page = write(
            site / "page.html",
            '<head><meta property="og:title" content="Title">'
            '<meta property="og:image" content="/missing.png">'
            '<meta property="og:image:width" content="1">'
            '<meta property="og:image:height" content="1">'
            '<meta property="og:image:alt" content="image">'
            '<meta name="twitter:image" content="/missing.png"></head>',
        )
        issues = og.check_html_file(site, page, "")
        assert any(
            issue.startswith("og:image target does not exist") for issue in issues
        )

    def test_twitter_cdn_image_is_rejected(self, tmp_path):
        site = tmp_path / "site"
        write(site / "image.png", "")
        page = write(
            site / "page.html",
            '<head><meta property="og:title" content="Title">'
            '<meta property="og:image" content="/image.png">'
            '<meta property="og:image:width" content="1">'
            '<meta property="og:image:height" content="1">'
            '<meta property="og:image:alt" content="image">'
            '<meta name="twitter:image" content="https://cdn.example/x.png"></head>',
        )
        issues = og.check_html_file(site, page, "")
        assert any(
            issue.startswith("twitter:image is not a site-local URL") for issue in issues
        )


class TestContentHtml:
    def test_masking_and_parsing_helpers(self, tmp_path, monkeypatch):
        fenced = "before\n```\n<script>\n```\nafter"
        masked = content_html.mask_code(fenced)
        assert "<script>" not in masked
        assert masked.count("\n") == fenced.count("\n")
        assert "<x>" not in content_html.strip_fenced_code_blocks("```<x>```")
        assert "<x>" not in content_html.strip_fenced_code_blocks("~~~<x>~~~")
        assert content_html.mask_code("~~~<x>~~~") == "         "
        assert content_html.mask_code("plain") == "plain"
        assert content_html.mask_code("inline `<x>`") == "inline " + " " * 5
        assert content_html.parse_frontmatter_title("no frontmatter") is None
        assert content_html.parse_frontmatter_title("---\ntags: x\n---\n") is None
        text = '---\ntitle: "Hello"\n---\n\n# Body'
        assert content_html.parse_frontmatter_title(text) == "Hello"
        assert content_html.body_after_frontmatter(text).startswith("\n# Body")
        assert content_html.body_after_frontmatter("plain") == "plain"
        assert content_html.first_markdown_h1("\nnot a heading\n# Later") is None
        assert content_html.first_markdown_h1("\n# Later") == "Later"
        inside = write(tmp_path / "content" / "tutorials" / "one.md", "")
        second = write(tmp_path / "content" / "tutorials" / "two.mdx", "")
        outside = tmp_path / "outside.md"
        monkeypatch.setattr(content_html, "CONTENT_ROOT", tmp_path / "content")
        assert content_html.collection_name(inside) == "tutorials"
        assert content_html.collection_name(outside) is None
        assert content_html.iter_markdown_files(tmp_path / "content") == [
            inside,
            second,
        ]

    def test_checks_scans_and_run(self, tmp_path, monkeypatch, capsys):
        content_root = tmp_path / "content"
        monkeypatch.setattr(content_html, "CONTENT_ROOT", content_root)
        duplicate = write(
            content_root / "tutorials" / "page.md",
            '---\ntitle: "Same"\n---\n# Same\nRaw <script>x</script>',
        )
        clean = write(content_root / "misc" / "clean.mdx", "---\ntitle: T\n---\ntext")
        issues = content_html.check_file(duplicate)
        assert any("blocked <script>" in issue for issue in issues)
        assert any("layout already renders" in issue for issue in issues)
        assert content_html.check_file(clean) == []
        assert (
            content_html.check_duplicate_hero_title(
                content_root / "unrelated.md", '---\ntitle: "Same"\n---\n# Same'
            )
            == []
        )
        assert (
            content_html.check_duplicate_hero_title(
                content_root / "tutorials" / "no-title.md",
                "---\ntags: x\n---\n# Heading",
            )
            == []
        )
        assert content_html.scan_blocked_html(
            "`<script>`\n<iframe x>\n<object>\n<embed>\n<div onclick=x>", "x"
        )
        assert content_html.run()[0] is False
        monkeypatch.setattr(content_html, "iter_markdown_files", lambda _root: [clean])
        assert content_html.run() == (
            True,
            "No blocked raw HTML patterns or duplicate hero titles found in content.",
        )
        monkeypatch.setattr(content_html, "SELF_TEST_CASES", (("clean", False),))
        assert content_html.self_test() == 0
        monkeypatch.setattr(content_html, "SELF_TEST_CASES", (("<script>", False),))
        assert content_html.self_test() == 1
        assert "FAILED" in capsys.readouterr().out

    def test_cli_paths(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr(content_html, "self_test", lambda: 0)
        monkeypatch.setattr(sys, "argv", ["content", "--self-test"])
        assert content_html.main() == 0
        monkeypatch.setattr(content_html, "run", lambda: (True, "ok"))
        monkeypatch.setattr(sys, "argv", ["content"])
        assert content_html.main() == 0
        assert capsys.readouterr().out == "ok\n"
        monkeypatch.setattr(content_html, "run", lambda: (False, "bad"))
        assert content_html.main() == 1
        assert capsys.readouterr().err == "bad\n"


class TestLinkSyntax:
    def test_link_parser_and_masks(self):
        masked = link_syntax.mask_inline_code("`[x](bad)` [ok](/x)")
        assert masked.endswith("[ok](/x)")
        assert "[x]" not in masked
        assert link_syntax.find_unclosed_link("plain") is None
        assert link_syntax.find_unclosed_link("[ok](/a_(b)/c)") is None
        assert link_syntax.find_unclosed_link("[bad](/a_(b)/c") == 5
        assert link_syntax.find_unclosed_link('[ok](/x/ "literal (text")') is None
        assert link_syntax.find_unclosed_link("[ok](/x) [bad](/y") == 14

    def test_scan_paths_run_and_self_test(self, tmp_path, monkeypatch, capsys):
        good = write(tmp_path / "good.md", "`````\n[hidden](/x\n```\n")
        bad = write(tmp_path / "bad.mdx", "Empty [x]()\nBroken [x](/x")
        assert (
            link_syntax.scan_text(
                "```\n[x](/hidden\n~~~\n[x](/also-hidden\n```", "fence"
            )
            == []
        )
        assert link_syntax.scan_text(good.read_text(), "good") == []
        errors = link_syntax.scan_text(bad.read_text(), "bad")
        assert len(errors) == 2
        other = write(tmp_path / "other.txt", "plain")
        assert link_syntax.scan_paths([good, other]) == []
        monkeypatch.setattr(link_syntax, "CONTENT_ROOT", tmp_path)
        assert link_syntax.scan_paths([bad])[0].startswith("bad.mdx:")
        monkeypatch.setattr(link_syntax, "iter_markdown", lambda: [good])
        assert link_syntax.run()[0]
        monkeypatch.setattr(link_syntax, "iter_markdown", lambda: [bad])
        assert not link_syntax.run()[0]
        assert link_syntax.self_test() == 0
        monkeypatch.setattr(link_syntax, "SELF_TEST_CASES", (("bad [x](/x", False),))
        assert link_syntax.self_test() == 1
        assert "FAILED" in capsys.readouterr().out

    def test_cli_paths(self, monkeypatch, capsys, tmp_path):
        good = write(tmp_path / "good.md", "[x](/x)")
        bad = write(tmp_path / "bad.md", "[x]()")
        monkeypatch.setattr(sys, "argv", ["link", "--self-test"])
        assert link_syntax.main() == 0
        monkeypatch.setattr(
            sys, "argv", ["link", str(good), str(tmp_path / "ignored.txt")]
        )
        assert link_syntax.main() == 0
        monkeypatch.setattr(sys, "argv", ["link", str(bad)])
        assert link_syntax.main() == 1
        assert capsys.readouterr().err
        monkeypatch.setattr(link_syntax, "run", lambda: (True, "ignored"))
        monkeypatch.setattr(sys, "argv", ["link"])
        assert link_syntax.main() == 0
        monkeypatch.setattr(link_syntax, "run", lambda: (False, "bad"))
        assert link_syntax.main() == 1
        assert "bad" in capsys.readouterr().err


class TestDevDiaries:
    def test_parsers_and_duplicate_helpers(self):
        assert diaries._unquote("  'x' ") == "x"
        assert diaries._unquote("x") == "x"
        assert diaries.normalize_compare_url("/a/") == "/a"
        assert (
            diaries.normalize_compare_url("HTTPS://EXAMPLE.COM/Path/?x=1")
            == "https://example.com/path"
        )
        assert diaries.is_version_like_tag("V2")
        assert not diaries.is_version_like_tag("release")
        assert diaries.parse_frontmatter("plain") is None
        data = diaries.parse_frontmatter(
            "---\nversion: v2.0\npermalink: '/a/'\ntags:\n  - 'v2.0'\n  - diary\n---\n"
        )
        assert data == {
            "version": "v2.0",
            "permalink": "/a/",
            "tags": ["v2.0", "diary"],
        }
        assert diaries.parse_frontmatter("---\ntitle: x\n---\n") == {"tags": []}
        assert diaries.find_duplicate_urls(["/same"], [("Group", "/same/")])
        assert diaries.find_duplicate_urls([], [("Group", "/other")]) == []

    def test_collection_external_run_and_cli(self, tmp_path, monkeypatch, capsys):
        root = tmp_path / "content"
        diaries_dir = root / "devDiaries"
        external = root / "devDiaryExternal" / "index.yml"
        monkeypatch.setattr(diaries, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(diaries, "DEV_DIARIES_DIR", diaries_dir)
        monkeypatch.setattr(diaries, "EXTERNAL_YML", external)
        assert diaries.collect_in_repo_permalinks() == ([], [], [])
        assert diaries.collect_external_urls() == []
        write(
            diaries_dir / "good.mdx",
            "---\nversion: v1.0\npermalink: /same/\ntags:\n  - v1.0\n---\n",
        )
        write(diaries_dir / "bad.mdx", "---\nversion: wrong\n---\n")
        write(diaries_dir / "none.mdx", "no yaml")
        write(
            external,
            "- title: 'Group'\n      url: /same/\n- title: Empty\n      url:\n",
        )
        in_repo, errors, warnings = diaries.collect_in_repo_permalinks()
        assert in_repo == ["/same"]
        assert len(errors) == 2
        assert warnings == [
            "content/devDiaries/good.mdx: tag 'v1.0' looks like a version; use version frontmatter instead"
        ]
        assert diaries.collect_external_urls() == [("Group", "/same/")]
        assert not diaries.run()[0]
        write(diaries_dir / "bad.mdx", "---\nversion: v1.1\n---\n")
        write(diaries_dir / "none.mdx", "---\nversion: v1.2\n---\n")
        passed, report = diaries.run()
        assert not passed and "duplicates" in report
        external.unlink()
        passed, report = diaries.run()
        assert passed and "warning" in report
        write(
            diaries_dir / "good.mdx",
            "---\nversion: v1.0\npermalink: /same/\ntags:\n---\n",
        )
        assert diaries.run() == (True, "Dev diary checks passed")
        monkeypatch.setattr(sys, "argv", ["diaries", "--self-test"])
        assert diaries.main() == 0
        monkeypatch.setattr(diaries, "run", lambda: (False, "bad"))
        monkeypatch.setattr(sys, "argv", ["diaries"])
        assert diaries.main() == 1
        assert "bad" in capsys.readouterr().out


class TestFlagImages:
    def test_run_and_cli(self, tmp_path, monkeypatch, capsys):
        countries = tmp_path / "countries"
        assets = tmp_path / "assets"
        monkeypatch.setattr(flags, "COUNTRIES_DIR", countries)
        monkeypatch.setattr(flags, "ASSETS_ROOT", assets)
        write(countries / "one.md", "flag_image: /assets/images/one.png\nignored: x")
        write(countries / "two.mdx", "flag_image: '/assets/images/missing.png'")
        write(assets / "one.png", "")
        passed, report = flags.run()
        assert not passed and "missing.png" in report
        write(assets / "missing.png", "")
        assert flags.run() == (True, "Flag image references OK.")
        monkeypatch.setattr(sys, "argv", ["flags"])
        assert flags.main() == 0
        monkeypatch.setattr(flags, "run", lambda: (False, "bad"))
        assert flags.main() == 1
        assert "bad" in capsys.readouterr().err


class TestDocsRunner:
    def test_timed_wrappers_and_dist_check(self, monkeypatch, tmp_path):
        result = docs._timed("x", lambda: (True, " ok "))
        assert result.passed and result.output == "ok"
        failed = docs._timed("x", lambda: (_ for _ in ()).throw(ValueError("boom")))
        assert not failed.passed and "boom" in failed.output
        monkeypatch.setattr(docs, "DIST_DIR", tmp_path / "missing")
        assert not docs._dist_check("x", lambda: (True, "ok")).passed
        docs.DIST_DIR.mkdir()
        assert docs._dist_check("x", lambda: (True, " ok ")).passed
        monkeypatch.setattr(docs._link_syntax, "run", lambda: (True, "link"))
        monkeypatch.setattr(docs._content_html, "run", lambda: (True, "content"))
        monkeypatch.setattr(docs._flags, "run", lambda: (True, "flags"))
        monkeypatch.setattr(docs._hygiene, "run", lambda *_args: (True, "hygiene"))
        monkeypatch.setattr(docs._dev_diaries, "run", lambda: (True, "diaries"))
        monkeypatch.setattr(
            docs,
            "run_cmd",
            lambda name, cmd: common.CheckResult(name, True, name, 0.0),
        )
        assert all(
            fn().passed
            for fn in [
                docs.check_link_syntax,
                docs.check_content_html,
                docs.check_flags,
                docs.check_hygiene,
                docs.check_dev_diaries,
                docs.check_lint_md,
                docs.check_astro,
                docs.check_build,
            ]
        )
        monkeypatch.setattr(docs._links, "run", lambda *_args: (True, "links"))
        monkeypatch.setattr(docs._og, "run", lambda *_args: (True, "og"))
        monkeypatch.setattr(docs._a11y, "run", lambda *_args: (True, "a11y"))
        monkeypatch.setattr(docs._perf, "run", lambda *_args: (True, "perf"))
        assert all(
            fn().passed
            for fn in [
                docs.check_links,
                docs.check_og,
                docs.check_a11y,
                docs.check_perf,
            ]
        )
        assert docs._run_dist_check("links").passed

    def test_collect_parallel_and_dist_parallel(self, monkeypatch):
        successful = concurrent.futures.Future()
        successful.set_result(common.CheckResult("ok", True, "", 0.0))
        failed = concurrent.futures.Future()
        failed.set_exception(RuntimeError("worker"))
        checks = {
            successful: docs.Check(
                "ok",
                "sources",
                lambda: common.CheckResult("ok", True, "", 0.0),
            ),
            failed: docs.Check(
                "bad",
                "sources",
                lambda: common.CheckResult("bad", True, "", 0.0),
            ),
        }
        results = docs._collect_results(checks)
        assert {result.name for result in results} == {"ok", "bad"}
        assert (
            next(result for result in results if result.name == "bad").output
            == "Exception: worker"
        )
        assert docs._run_parallel(
            [
                docs.Check(
                    "one",
                    "sources",
                    lambda: common.CheckResult("one", True, "", 0.0),
                )
            ],
            1,
        )[0].passed

        class FakeExecutor:
            def __init__(self, max_workers):
                self.max_workers = max_workers
                self.futures = []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def submit(self, fn, name):
                future = concurrent.futures.Future()
                try:
                    future.set_result(fn(name))
                except Exception as exc:
                    future.set_exception(exc)
                self.futures.append(future)
                return future

        monkeypatch.setattr(docs, "ProcessPoolExecutor", FakeExecutor)
        monkeypatch.setattr(
            docs,
            "_run_dist_check",
            lambda name: common.CheckResult(name, True, "", 0.0),
        )
        result = docs._run_dist_parallel(
            [
                docs.Check(
                    "links",
                    "dist",
                    lambda: common.CheckResult("links", True, "", 0.0),
                )
            ],
            2,
        )
        assert result[0].name == "links"

    def test_run_checks_phase_boundaries(self, monkeypatch, capsys):
        def result(name, passed=True):
            return lambda: common.CheckResult(name, passed, "", 0.0)

        source = docs.Check("source", "sources", result("source"))
        astro = docs.Check("astro check", "build", result("astro check"))
        build = docs.Check("build", "build", result("build"))
        dist = docs.Check("links", "dist", result("links"))
        monkeypatch.setattr(
            docs,
            "_run_dist_parallel",
            lambda checks, _workers: [c.fn() for c in checks],
        )
        assert {
            r.name for r in docs.run_checks([source, astro, build, dist], max_workers=1)
        } == {"source", "astro check", "build", "links"}
        bad_build = docs.Check("build", "build", result("build", False))
        results = docs.run_checks([source, bad_build, dist], max_workers=1)
        assert (
            next(r for r in results if r.name == "links").output
            == "skipped: build failed"
        )
        bad_astro = docs.Check("astro check", "build", result("astro check", False))
        assert any(
            r.name == "links"
            for r in docs.run_checks([bad_astro, build, dist], max_workers=1)
        )
        assert [
            r.name
            for r in docs.run_checks([source, dist], skip_build=True, max_workers=1)
        ] == ["source", "links"]
        assert docs.run_checks([]) == []
        docs.print_report([common.CheckResult("ok", True, "", 1.0)])
        docs.print_report([common.CheckResult("bad", False, "line1\nline2", 1.0)])
        output = capsys.readouterr().out
        assert "ALL PASSED" in output
        assert "FAILED" in output
        assert "line2" in output

    def test_main_cli_paths(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["docs", "--list"])
        assert docs.main() == 0
        assert "link-syntax" in capsys.readouterr().out
        monkeypatch.setattr(sys, "argv", ["docs", "--only", "unknown"])
        assert docs.main() == 1
        assert "Unknown checks" in capsys.readouterr().out
        monkeypatch.setattr(
            docs,
            "run_checks",
            lambda *_args, **_kwargs: [common.CheckResult("x", True, "", 0.0)],
        )
        monkeypatch.setattr(sys, "argv", ["docs"])
        assert docs.main() == 0
        capsys.readouterr()
        monkeypatch.setattr(
            sys,
            "argv",
            ["docs", "--no-build", "--only", "link-syntax", "--max-workers", "1"],
        )
        assert docs.main() == 0
        monkeypatch.setattr(
            docs,
            "run_checks",
            lambda *_args, **_kwargs: [common.CheckResult("x", False, "", 0.0)],
        )
        assert docs.main() == 1
        assert "FAIL" in capsys.readouterr().out

    def test_parse_all_check_dataclass(self):
        assert docs.ALL_CHECKS[0].phase == "sources"
        assert (
            docs.Check("x", "dist", lambda: common.CheckResult("x", True, "", 0.0)).name
            == "x"
        )
