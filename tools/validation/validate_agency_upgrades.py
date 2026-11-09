#!/usr/bin/env python3
"""Validate intelligence agency upgrade definitions and their mod-wide references."""

import glob
import re
from pathlib import Path
from typing import Dict, List, Set

import disk_cache
from validator_common import BaseValidator, line_of, run_validator_main, strip_comments

UPGRADES_DIR = "common/intelligence_agency_upgrades"

UPGRADE_DEF_RE = re.compile(r"^\t(upgrade_\w+)\s*=\s*\{", re.MULTILINE)
UPGRADE_PICTURE_RE = re.compile(r"^\t\tpicture\s*=\s*(GFX_\w+)", re.MULTILINE)
CREATE_AGENCY_RE = re.compile(
    r"create_intelligence_agency\s*=\s*\{([^{}]*?)\}", re.DOTALL
)
AGENCY_ICON_RE = re.compile(r'icon\s*=\s*"?(GFX_\w+)"?')
UPGRADE_CALL_RE = re.compile(r"upgrade_intelligence_agency\s*=\s*(upgrade_\w+)")
GFX_NAME_RE = re.compile(r'name\s*=\s*"(GFX_\w+)"')


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def _scan_agency_calls(stripped: str, filepath: str):
    create_icons = []
    for match in CREATE_AGENCY_RE.finditer(stripped):
        body = match.group(1)
        icon_match = AGENCY_ICON_RE.search(body)
        if not icon_match:
            continue
        offset = match.start() + body.find(icon_match.group(0))
        create_icons.append((filepath, line_of(stripped, offset), icon_match.group(1)))

    upgrade_calls = []
    for match in UPGRADE_CALL_RE.finditer(stripped):
        upgrade_calls.append(
            (filepath, line_of(stripped, match.start()), match.group(1))
        )

    return create_icons, upgrade_calls


def process_file_for_agency_calls(args):
    """Return create-agency icons and upgrade-agency calls from one file."""
    filepath, mod_path = args
    try:
        raw = Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return [], []
    stripped = strip_comments(raw)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        "agency.calls",
        filepath,
        stripped,
        lambda: _scan_agency_calls(stripped, filepath),
    )


class Validator(BaseValidator):
    TITLE = "AGENCY UPGRADES"
    STAGED_EXTENSIONS = [".txt", ".gfx"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.upgrade_defs: Dict[str, Dict] = {}
        self.duplicate_defs: Dict[str, List[Dict]] = {}
        self.gfx_defined: Set[str] = set()

    def _collect_upgrade_defs(self) -> None:
        pattern = str(Path(self.mod_path) / UPGRADES_DIR / "*.txt")
        for filepath in glob.iglob(pattern):
            text = _read(Path(filepath))
            if not text:
                continue
            stripped = strip_comments(text)
            matches = list(UPGRADE_DEF_RE.finditer(stripped))
            for index, match in enumerate(matches):
                end = (
                    matches[index + 1].start()
                    if index + 1 < len(matches)
                    else len(stripped)
                )
                picture_match = UPGRADE_PICTURE_RE.search(stripped, match.end(), end)
                info = {
                    "source": Path(filepath).relative_to(self.mod_path).as_posix(),
                    "line": line_of(stripped, match.start()),
                    "picture": picture_match.group(1) if picture_match else None,
                }
                name = match.group(1)
                if name in self.upgrade_defs:
                    self.duplicate_defs.setdefault(
                        name, [self.upgrade_defs[name]]
                    ).append(info)
                else:
                    self.upgrade_defs[name] = info

    def _collect_gfx(self) -> None:
        pattern = str(Path(self.mod_path) / "interface" / "**" / "*.gfx")
        for filepath in glob.iglob(pattern, recursive=True):
            self.gfx_defined.update(GFX_NAME_RE.findall(_read(Path(filepath))))

    def _validate_duplicates(self) -> None:
        self._log_section("Checking duplicate agency upgrade IDs...")
        results = []
        for name, definitions in sorted(self.duplicate_defs.items()):
            locations = ", ".join(
                f"{item['source']}:{item['line']}" for item in definitions
            )
            results.append(f"upgrade '{name}' is defined more than once: {locations}")
        self._report(
            results,
            "✓ Agency upgrade IDs are unique",
            "Duplicate agency upgrade IDs:",
            category="agency-upgrades-duplicates",
        )

    def _validate_pictures(self) -> None:
        self._log_section("Checking agency upgrade pictures...")
        results = []
        for name, info in sorted(self.upgrade_defs.items()):
            picture = info["picture"]
            location = f"{info['source']}:{info['line']}"
            if not picture:
                results.append(
                    f"{location} - upgrade '{name}' has no `picture =` field"
                )
            elif picture not in self.gfx_defined:
                results.append(
                    f"{location} - upgrade '{name}' references picture '{picture}' "
                    "not defined in any .gfx file"
                )
        self._report(
            results,
            "✓ All agency upgrade pictures resolve",
            "Missing or invalid agency upgrade pictures:",
            category="agency-upgrades-pictures",
        )

    def _validate_agency_calls(self) -> None:
        self._log_section(
            "Checking create_intelligence_agency icons and "
            "upgrade_intelligence_agency calls..."
        )
        files = self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        )
        scan_results = self._pool_map(
            process_file_for_agency_calls,
            [(filepath, self.mod_path) for filepath in files],
            chunksize=50,
        )

        create_icons: List = []
        upgrade_calls: List = []
        for icons, calls in scan_results:
            create_icons.extend(icons)
            upgrade_calls.extend(calls)

        results = []
        for filepath, line, gfx in create_icons:
            if gfx not in self.gfx_defined:
                relpath = Path(filepath).relative_to(self.mod_path).as_posix()
                results.append(
                    f"{relpath}:{line} - create_intelligence_agency icon '{gfx}' "
                    "not defined in any .gfx file"
                )
        for filepath, line, upgrade in upgrade_calls:
            if upgrade not in self.upgrade_defs:
                relpath = Path(filepath).relative_to(self.mod_path).as_posix()
                results.append(
                    f"{relpath}:{line} - upgrade_intelligence_agency references "
                    f"'{upgrade}' but no such upgrade is defined in {UPGRADES_DIR}/"
                )

        self.log(
            f"  Scanned {len(files)} files | "
            f"create_intelligence_agency icon refs: {len(create_icons)} | "
            f"upgrade_intelligence_agency calls: {len(upgrade_calls)}"
        )
        self._report(
            results,
            "✓ All agency icons and upgrade calls are valid",
            "Invalid agency icons or upgrade call targets:",
            category="agency-upgrades-calls",
        )

    def run_validations(self):
        if self.staged_only and not self.staged_files:
            self.log(
                "No staged files found — skipping agency upgrade validation", "warning"
            )
            return

        self._collect_upgrade_defs()
        self._collect_gfx()
        self.log(
            f"  Defined upgrades: {len(self.upgrade_defs)} | "
            f"GFX sprites: {len(self.gfx_defined)}"
        )
        self._validate_duplicates()
        self._validate_pictures()
        self._validate_agency_calls()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate intelligence agency upgrades")
