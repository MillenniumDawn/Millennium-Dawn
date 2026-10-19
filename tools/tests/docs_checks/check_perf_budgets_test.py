"""Performance budgets of the built site: bundle sizes and page weight."""

import check_perf_budgets as perf
from shared.suite import write_text


def test_run_passes_small_bundles(tmp_path):
    write_text(tmp_path / "small.css", "ok")
    write_text(tmp_path / "small.js", "ok")
    # A directory named like a bundle is not measured.
    (tmp_path / "folder.css").mkdir()

    assert perf.run(tmp_path) == (
        True,
        f"Performance budget checks passed for {tmp_path.resolve()}",
    )


def test_run_reports_each_bundle_over_its_budget(tmp_path):
    site = tmp_path.resolve()
    sizes = {suffix: budget + 1 for suffix, budget in perf.BUDGETS_BYTES.items()}
    for suffix, size in sizes.items():
        write_text(site / f"large{suffix}", "x" * size)
    # Only CSS and JS bundles have a size budget.
    write_text(site / "large.txt", "x" * max(sizes.values()))

    passed, report = perf.run(site)

    assert not passed
    assert sorted(report.splitlines()[1:]) == [
        f"- {site / f'large{suffix}'}: {size} bytes exceeds {suffix} budget "
        f"of {size - 1} bytes"
        for suffix, size in sorted(sizes.items())
    ]


def test_run_fails_when_the_site_directory_is_missing(tmp_path):
    passed, report = perf.run(tmp_path / "missing")

    assert not passed
    assert report.startswith("ERROR: site directory does not exist")


def test_long_text_page_and_unused_image_pass(tmp_path):
    site = tmp_path / "site"
    entry = "<li>Fixed a bug in the economy</li>\n"
    write_text(site / "changelog/index.html", entry * 30_000)
    write_text(site / "assets/original.png", "x" * (perf.PAGE_BUDGET + 1))
    assert (site / "changelog/index.html").stat().st_size > perf.INITIAL_BUDGET

    assert perf.run(site)[0]


def test_page_budgets_split_eager_and_lazy_images(tmp_path):
    site = tmp_path / "site"
    write_text(site / "assets/big.png", "x" * (perf.INITIAL_BUDGET + 1))
    write_text(site / "assets/huge.png", "x" * (perf.PAGE_BUDGET + 1))
    write_text(site / "eager/index.html", '<img src="/base/assets/big.png">')
    write_text(
        site / "lazy/index.html", '<img src="/base/assets/big.png" loading="lazy">'
    )
    write_text(
        site / "gallery/index.html", '<img src="../assets/huge.png" loading="lazy">'
    )

    passed, report = perf.run(site, "/base")

    assert not passed
    assert report.count("exceeds") == 2
    eager, gallery = sorted(report.splitlines()[1:])
    assert "eager" in eager and "initial load budget" in eager
    assert f"assets/big.png, {perf.INITIAL_BUDGET + 1} bytes" in eager
    assert "gallery" in gallery and "page budget" in gallery


def test_weigh_page_counts_what_the_browser_fetches(tmp_path):
    site = tmp_path / "site"
    for name, size in {
        "first.avif": 10,
        "second.webp": 500,
        "fallback.png": 900,
        "small.png": 20,
        "retina.png": 70,
        "lazy.png": 3_000,
        "video.mp4": 40_000,
    }.items():
        write_text(site / name, "x" * size)
    css = write_text(site / "app.css", "body { color: red }\n" * 50)
    script = write_text(site / "app.js", "console.log('x');\n" * 50)
    preload = write_text(site / "chunk.js", "export const x = 1;\n" * 50)
    page = write_text(
        site / "page/index.html",
        '<link rel="stylesheet" href="/app.css"><link rel="icon" href="/small.png">'
        '<link rel="modulepreload" href="/chunk.js"><script src="/app.js"></script>'
        "<script>inline()</script>"
        '<picture><source srcset="/first.avif 1x, /missing.avif 2x">'
        '<source srcset="/second.webp"><img src="/fallback.png"></picture>'
        '<img src="/small.png" srcset="/small.png 1x, /retina.png 2x">'
        '<img src="/retina.png"><img src="/lazy.png" loading="lazy">'
        '<img src="/retina.png" loading="lazy">'
        '<img src="https://example.com/x.png"><img src="data:image/png;base64,AA">'
        '<img alt="no source"><video><source src="/video.mp4"></video>',
    )
    cache = {}
    text = sum(perf.transfer_size(path, {}) for path in (page, css, script, preload))

    assert perf.transfer_size(css, cache) < css.stat().st_size
    assert perf.weigh_page(page, site, "", cache) == (
        text + 10 + 70,
        text + 10 + 70 + 3_000,
        site / "lazy.png",
    )
