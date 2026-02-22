"""Shared configuration and constants for OG generation."""

from __future__ import annotations


SITE_DESCRIPTION = (
    "Documentation for the Millennium Dawn: A Modern Day mod for the game Hearts of Iron IV."
)

SECTION_DEFAULT_SUBTITLE = {
    "countries": "National content overview and focus tree information for Millennium Dawn.",
    "tutorials": "Gameplay tutorial for Millennium Dawn.",
    "resources": "Developer resource for Millennium Dawn.",
    "changelogs": "Detailed changelog and release notes for Millennium Dawn.",
}

SOURCE_PATTERNS = (
    "pages/**/*.md",
    "pages/**/*.html",
    "dev-diaries/**/*.md",
    "dev-diaries/**/*.html",
    "player-tutorials/**/*.md",
    "player-tutorials/**/*.html",
    "dev-resources/**/*.md",
    "dev-resources/**/*.html",
    "misc/**/*.md",
    "misc/**/*.html",
    "_countries/*.md",
    "_countries/*.html",
    "_changelog_sections/*.md",
    "_changelog_sections/*.html",
    "*.md",
    "*.html",
)

# Visual tuning
HERO_OPACITY = 140  # 0-255. Lower = more transparent hero.
GRADIENT_FADE_START = 0.35
GRADIENT_VERT_WEIGHT = 0.78
GRADIENT_HORIZ_WEIGHT = 0.22
GRADIENT_CURVE = 1.2
GRADIENT_MAX_ALPHA = 235
GRADIENT_COLOR_TOKEN = "color-header-bg"
TOKEN_HEADER_BG = "color-header-bg"
TOKEN_HEADER_BG_END = "color-header-bg-end"

