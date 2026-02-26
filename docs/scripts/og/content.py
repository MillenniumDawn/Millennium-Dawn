"""Content discovery and metadata extraction for OG generation."""

from __future__ import annotations

import re
from pathlib import Path

from .config import SECTION_DEFAULT_SUBTITLE, SITE_DESCRIPTION, SOURCE_PATTERNS


def load_site_description(config_path: Path) -> str:
    if not config_path.exists():
        return SITE_DESCRIPTION

    text = config_path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        match = re.match(r"^\s*description:\s*(.+?)\s*$", line)
        if not match:
            continue
        raw_value = match.group(1).strip()
        if (raw_value.startswith('"') and raw_value.endswith('"')) or (
            raw_value.startswith("'") and raw_value.endswith("'")
        ):
            return raw_value[1:-1]
        return raw_value

    return SITE_DESCRIPTION


def parse_front_matter(text: str) -> dict[str, object]:
    if not text.startswith("---"):
        return {}

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}

    front_lines = lines[1:end_idx]
    data: dict[str, object] = {}
    i = 0
    while i < len(front_lines):
        line = front_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue

        match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not match:
            i += 1
            continue

        key = match.group(1)
        raw_value = match.group(2).strip()

        if raw_value in {"|", ">"}:
            i += 1
            while i < len(front_lines):
                next_line = front_lines[i]
                if next_line.startswith(" ") or next_line.startswith("\t"):
                    i += 1
                    continue
                break
            continue

        value: object
        if raw_value.lower() == "false":
            value = False
        elif raw_value.lower() == "true":
            value = True
        elif (raw_value.startswith('"') and raw_value.endswith('"')) or (
            raw_value.startswith("'") and raw_value.endswith("'")
        ):
            value = raw_value[1:-1]
        else:
            value = raw_value

        data[key] = value
        i += 1

    return data


def load_css_hex_tokens(variables_scss_path: Path) -> dict[str, tuple[int, int, int]]:
    tokens: dict[str, tuple[int, int, int]] = {}
    if not variables_scss_path.exists():
        return tokens

    pattern = re.compile(r"^\s*--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;")
    for line in variables_scss_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        name = match.group(1)
        hex_value = match.group(2).lstrip("#")
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)
        tokens[name] = (r, g, b)
    return tokens


def iter_source_files(docs_dir: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in SOURCE_PATTERNS:
        files.update(path for path in docs_dir.glob(pattern) if path.is_file())
    return sorted(files)


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    normalized = normalized.strip("-")
    return normalized or "page"


def og_id_for_path(rel_path: Path) -> str:
    parts = list(rel_path.with_suffix("").parts)
    normalized_parts: list[str] = []
    for part in parts:
        clean = part.lstrip("_")
        normalized = slugify(clean)
        if normalized:
            normalized_parts.append(normalized)
    if not normalized_parts:
        return "page"
    return "-".join(normalized_parts)


def section_for_path(rel_path: Path) -> str | None:
    first = rel_path.parts[0] if rel_path.parts else ""
    if first == "_countries":
        return "countries"
    if first == "_changelog_sections":
        return "changelogs"
    if first == "player-tutorials":
        return "tutorials"
    if first == "dev-resources":
        return "resources"
    if first == "pages" and len(rel_path.parts) > 1:
        second = rel_path.parts[1]
        if second in SECTION_DEFAULT_SUBTITLE:
            return second
    return None


def subtitle_for_page(data: dict[str, object], rel_path: Path, site_description: str) -> str:
    description = str(data.get("description") or "").strip()
    if description:
        return description

    kind = str(data.get("kind") or "").strip()
    if kind:
        return kind

    section = section_for_path(rel_path)
    if section and section in SECTION_DEFAULT_SUBTITLE:
        return SECTION_DEFAULT_SUBTITLE[section]

    return site_description


def is_seo_enabled(data: dict[str, object]) -> bool:
    seo = data.get("seo")
    if seo is None:
        return True
    if isinstance(seo, bool):
        return seo
    return str(seo).strip().lower() != "false"


def normalize_permalink(value: str) -> str:
    value = value.strip()
    if not value:
        return "/"
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        return value
    if not value.startswith("/"):
        value = "/" + value
    value = re.sub(r"/{2,}", "/", value)
    if value != "/" and not value.endswith("/") and not value.endswith(".html"):
        value += "/"
    return value


def page_path_for_og(rel_path: Path, data: dict[str, object]) -> str:
    permalink = str(data.get("permalink") or "").strip()
    if permalink:
        return normalize_permalink(permalink)

    stem = rel_path.stem
    first = rel_path.parts[0] if rel_path.parts else ""

    if first == "_countries":
        slug = str(data.get("slug") or stem).strip() or stem
        return f"/countries/{slug}/"

    if first == "_changelog_sections":
        return f"/changelogs/{stem}/"

    if first == "pages":
        sub = Path(*rel_path.parts[1:]).with_suffix("")
        if sub.as_posix() == "index":
            return "/"
        clean_parts = [part for part in sub.parts if part != "index"]
        if not clean_parts:
            return "/"
        return "/" + "/".join(clean_parts) + "/"

    sub = rel_path.with_suffix("")
    clean_parts = list(sub.parts)
    if clean_parts and clean_parts[-1] == "index":
        clean_parts = clean_parts[:-1]
    if not clean_parts:
        return "/"
    return "/" + "/".join(clean_parts) + "/"

