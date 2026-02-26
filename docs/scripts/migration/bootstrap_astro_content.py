#!/usr/bin/env python3
"""Bootstrap Astro content structure from legacy Jekyll docs sources."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import yaml


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    data = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return data, body


def dump_markdown(path: Path, data: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=10_000).strip()
    out = f"---\n{fm}\n---\n\n{body.rstrip()}\n"
    path.write_text(out, encoding="utf-8")


def sanitize_front_matter(data: dict[str, Any]) -> dict[str, Any]:
    # Astro 5 content collections do not support frontmatter layout.
    clean = dict(data or {})
    clean.pop("layout", None)
    return clean


def clean_liquid_links(text: str) -> str:
    # {{ "/x" | relative_url }} -> /x
    text = re.sub(r"\{\{\s*['\"]([^'\"]+)['\"]\s*\|\s*relative_url\s*\}\}", r"\1", text)
    # {{ "/x" | absolute_url }} -> https://millenniumdawn.github.io/Millennium-Dawn/x
    text = re.sub(
        r"\{\{\s*['\"]([^'\"]+)['\"]\s*\|\s*absolute_url\s*\}\}",
        lambda m: f"https://millenniumdawn.github.io/Millennium-Dawn{m.group(1)}",
        text,
    )
    return text


def clean_generic_liquid(text: str) -> str:
    text = clean_liquid_links(text)
    text = re.sub(r"\{\%\s*include\s+[^%]+\%\}\n?", "", text)
    text = re.sub(r"\{\%\s*capture\s+md\s*\%\}\n?", "", text)
    text = re.sub(r"\{\%\s*endcapture\s*\%\}\n?", "", text)
    text = re.sub(r"\{\{\s*md\s*\|\s*markdownify\s*\}\}\n?", "", text)
    return text


def strip_unhandled_liquid_lines(text: str) -> str:
    fence_marker = re.compile(r"^\s*```")
    in_fence = False
    lines = []
    for line in text.splitlines():
        if fence_marker.match(line):
            in_fence = not in_fence
            lines.append(line)
            continue
        if in_fence:
            lines.append(line)
            continue
        if "{%" in line or "{{" in line:
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def markdown_table(columns: list[str], rows: list[list[Any]]) -> str:
    header = "| " + " | ".join(col.replace("|", r"\|") for col in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        cells = [str(cell).replace("|", r"\|") for cell in row]
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep, *body])


def convert_country(source: Path, target: Path) -> None:
    data, body = parse_front_matter(source.read_text(encoding="utf-8"))
    data = sanitize_front_matter(data)

    sections = data.pop("sections", []) or []
    lead = (data.pop("lead", "") or "").strip()

    chunks: list[str] = []
    if lead:
        chunks.append(lead)

    for section in sections:
        heading = str(section.get("heading", "Section")).strip()
        if heading:
            chunks.append(f"## {heading}")

        section_body = str(section.get("body", "") or "").strip()
        if section_body:
            chunks.append(section_body)

        spirits = section.get("spirits") or []
        if spirits:
            chunks.append("### Spirits")
            spirit_lines: list[str] = []
            for spirit in spirits:
                name = str(spirit.get("name", "Unknown")).strip()
                spirit_type = str(spirit.get("type", "neutral")).strip()
                desc = str(spirit.get("desc", "") or "").strip()
                line = f"- **{name}** ({spirit_type})"
                if desc:
                    line += f": {desc}"
                spirit_lines.append(line)
            chunks.append("\n".join(spirit_lines))

        items = section.get("items") or []
        if items:
            chunks.append("\n".join(f"- {str(item).strip()}" for item in items))

        table = section.get("table") or {}
        columns = table.get("columns") or []
        rows = table.get("rows") or []
        if columns and rows:
            chunks.append(markdown_table(columns, rows))

        callout = section.get("callout") or {}
        callout_text = str(callout.get("text", "") or "").strip()
        callout_type = str(callout.get("type", "info") or "info").strip().upper()
        if callout_text:
            chunks.append(f"> **{callout_type}:** {callout_text}")

    cleaned_body = clean_generic_liquid(body).strip()
    if cleaned_body:
        chunks.append(cleaned_body)

    final_body = "\n\n".join(chunk.strip() for chunk in chunks if chunk.strip()) + "\n"
    dump_markdown(target, data, final_body)


def convert_standard(source: Path, target: Path, strip_liquid_lines: bool = False) -> None:
    data, body = parse_front_matter(source.read_text(encoding="utf-8"))
    data = sanitize_front_matter(data)
    body = clean_generic_liquid(body)
    if strip_liquid_lines:
        body = strip_unhandled_liquid_lines(body)
    dump_markdown(target, data, body)


def remove_country_focus_grid_block(text: str) -> str:
    return re.sub(
        r"<div class=\"country-focus-grid\"[^>]*>[\s\S]*?</div>",
        "",
        text,
        flags=re.MULTILINE,
    )


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=10_000),
        encoding="utf-8",
    )


def copy_data_files(docs_dir: Path, content_dir: Path) -> None:
    mapping = {
        docs_dir / "_data" / "site" / "navigation.yml": content_dir / "navigation" / "index.yml",
        docs_dir / "_data" / "site" / "release.yml": content_dir / "release" / "index.yml",
        docs_dir / "_data" / "site" / "sections.yml": content_dir / "sections" / "index.yml",
        docs_dir / "_data" / "content" / "home.yml": content_dir / "home" / "index.yml",
        docs_dir / "_data" / "content" / "dev_diaries.yml": content_dir / "devDiaryArchive" / "index.yml",
        docs_dir / "_data" / "content" / "known_submods.yml": content_dir / "knownSubmods" / "index.yml",
    }
    for src, dst in mapping.items():
        dump_yaml(dst, load_yaml(src))


def build_known_submods_page(docs_dir: Path, target: Path) -> None:
    source = docs_dir / "misc" / "known-submods.md"
    data, body = parse_front_matter(source.read_text(encoding="utf-8"))
    data = sanitize_front_matter(data)
    known_submods = load_yaml(docs_dir / "_data" / "content" / "known_submods.yml")

    chunks = [clean_generic_liquid(body).split("{% for group", 1)[0].strip()]
    for group in known_submods.get("groups", []):
        chunks.append(f"## {group['title']}")
        if group.get("note"):
            chunks.append(group["note"])
        lines = [f"- [{item['title']}]({item['url']})" for item in group.get("items", [])]
        chunks.append("\n".join(lines))

    body_out = "\n\n".join(chunk for chunk in chunks if chunk).strip() + "\n"
    dump_markdown(target, data, body_out)


def convert_pages(docs_dir: Path, content_dir: Path) -> None:
    # Keep pages collection concise and contributor-friendly.
    page_map = {
        docs_dir / "pages" / "faq" / "index.md": content_dir / "pages" / "faq.md",
        docs_dir / "pages" / "getting-started" / "index.md": content_dir / "pages" / "getting-started.md",
        docs_dir / "pages" / "countries" / "index.md": content_dir / "pages" / "countries.md",
    }

    for src, dst in page_map.items():
        convert_standard(src, dst, strip_liquid_lines=True)

    countries_page = content_dir / "pages" / "countries.md"
    data, body = parse_front_matter(countries_page.read_text(encoding="utf-8"))
    body = remove_country_focus_grid_block(body)
    dump_markdown(countries_page, data, body)


def convert_collections(docs_dir: Path, content_dir: Path) -> None:
    for src in sorted((docs_dir / "_countries").glob("*.md")):
        convert_country(src, content_dir / "countries" / src.name)

    for src in sorted((docs_dir / "_changelog_sections").glob("*.md")):
        convert_standard(src, content_dir / "changelogSections" / src.name)

    for src in sorted((docs_dir / "player-tutorials").glob("*.md")):
        convert_standard(src, content_dir / "tutorials" / src.name)

    for src in sorted((docs_dir / "dev-resources").glob("*.md")):
        convert_standard(src, content_dir / "resources" / src.name)

    for src in sorted((docs_dir / "dev-diaries").glob("*.md")):
        convert_standard(src, content_dir / "devDiaries" / src.name)

    for src in sorted((docs_dir / "misc").glob("*.md")):
        if src.name == "known-submods.md":
            continue
        convert_standard(src, content_dir / "misc" / src.name)

    build_known_submods_page(docs_dir, content_dir / "misc" / "known-submods.md")


def create_redirect_entries(content_dir: Path) -> None:
    redirects = [
        {
            "file": "countries-list.md",
            "title": "Countries Redirect",
            "permalink": "/countries-list/",
            "redirect_to": "/countries/",
            "seo": False,
            "robots": "noindex, nofollow",
            "toc": "off",
        },
        {
            "file": "dev-diaries-list.md",
            "title": "Dev Diaries Redirect",
            "permalink": "/dev-diaries-list/",
            "redirect_to": "/dev-diaries/",
            "seo": False,
            "robots": "noindex, nofollow",
            "toc": "off",
        },
        {
            "file": "team-resources.md",
            "title": "Resources Redirect",
            "permalink": "/team-resources/",
            "redirect_to": "/resources/",
            "seo": False,
            "robots": "noindex, nofollow",
            "toc": "off",
        },
        {
            "file": "technical-support.md",
            "title": "Support Redirect",
            "permalink": "/technical-support/",
            "redirect_to": "/support/",
            "seo": False,
            "robots": "noindex, nofollow",
            "toc": "off",
        },
    ]

    for entry in redirects:
        body = f"This page has moved to [{entry['redirect_to']}]({entry['redirect_to']}).\n"
        dump_markdown(content_dir / "redirects" / entry["file"], {k: v for k, v in entry.items() if k != "file"}, body)


def copy_assets(docs_dir: Path) -> None:
    public_dir = docs_dir / "public"
    assets_src = docs_dir / "assets"
    assets_dst = public_dir / "assets"

    if assets_dst.exists():
        shutil.rmtree(assets_dst)
    shutil.copytree(assets_src, assets_dst)

    compiled_css = docs_dir / "_site" / "assets" / "css" / "main.css"
    if compiled_css.exists():
        css_dst = assets_dst / "css" / "main.css"
        css_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(compiled_css, css_dst)

    compiled_map = docs_dir / "_site" / "assets" / "css" / "main.css.map"
    if compiled_map.exists():
        shutil.copy2(compiled_map, assets_dst / "css" / "main.css.map")

    # Client runtime is bundled from src/scripts via Astro/Vite.
    legacy_js_dir = assets_dst / "js"
    if legacy_js_dir.exists():
        shutil.rmtree(legacy_js_dir)


def copy_client_scripts(docs_dir: Path) -> None:
    # Client runtime scripts are source-controlled TypeScript modules in src/scripts.
    # Keep this hook for backward compatibility with older migration flows.
    legacy_site_js = docs_dir / "src" / "scripts" / "site.js"
    if legacy_site_js.exists():
        legacy_site_js.unlink()


def run() -> None:
    docs_dir = Path(__file__).resolve().parents[2]
    content_dir = docs_dir / "src" / "content"

    # Clean generated content folders from previous runs.
    generated_folders = [
      "pages",
      "countries",
      "changelogSections",
      "tutorials",
      "resources",
      "devDiaries",
      "misc",
      "redirects",
      "navigation",
      "release",
      "sections",
      "home",
      "devDiaryArchive",
      "knownSubmods",
    ]
    for folder in generated_folders:
        target = content_dir / folder
        if target.exists():
            shutil.rmtree(target)

    copy_data_files(docs_dir, content_dir)
    convert_pages(docs_dir, content_dir)
    convert_collections(docs_dir, content_dir)
    create_redirect_entries(content_dir)
    copy_assets(docs_dir)
    copy_client_scripts(docs_dir)

    print("Astro content bootstrap complete.")


if __name__ == "__main__":
    run()
