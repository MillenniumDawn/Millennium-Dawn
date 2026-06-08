#!/usr/bin/env python3
# Treat common/intelligence_agency_upgrades/*.txt as the source of truth and
# verify every defined upgrade is fully integrated across the mod: the
# auto-agency registry arrays, the loc key triples, the GFX sprites, and the
# scripted-GUI prerequisites. When a contributor adds a new upgrade, this flags
# every place it must also be wired up so nothing silently falls out of the
# auto-agency system. It also cross-checks every create_intelligence_agency and
# upgrade_intelligence_agency call mod-wide to confirm icons and upgrade names
# are valid.
import glob
import re
from pathlib import Path
from typing import Dict, List, Set

import disk_cache
from validator_common import BaseValidator, Colors, run_validator_main, strip_comments

ON_ACTIONS_FILE = "common/on_actions/MD_auto_agency_on_actions.txt"
UPGRADES_DIR = "common/intelligence_agency_upgrades"
SCRIPTED_GUI_FILE = "common/scripted_guis/00_MD_auto_agency_scripted_gui.txt"
LOC_FILE = "localisation/english/MD_auto_agency_l_english.yml"

# global.agency_upgrades^12 = token:MD_auto_agency_12_upgrade_commando_training
AGENCY_UPGRADE_SET_RE = re.compile(
    r"global\.agency_upgrades\^(\d+)\s*=\s*token:(MD_auto_agency_\d+_\S+)"
)
AGENCY_NAMES_SET_RE = re.compile(
    r"global\.agency_names\^(\d+)\s*=\s*token:(MD_auto_agency_\d+_\S+)"
)
AGENCY_GFX_SET_RE = re.compile(
    r"global\.agency_gfx\^(\d+)\s*=\s*token:(MD_auto_agency_\d+_\S+)"
)
AGENCY_MAX_SET_RE = re.compile(r"global\.agency_max_upgrades\^(\d+)\s*=\s*(\d+)")
RESIZE_ARRAY_RE = re.compile(
    r"resize_array\s*=\s*\{\s*array\s*=\s*global\.agency_\w+\s+value\s*=\s*\d+\s+size\s*=\s*(\d+)\s*\}"
)

# Top-level upgrade definition: a single-tab-indented `upgrade_foo = {`
UPGRADE_DEF_RE = re.compile(r"^\t(upgrade_\w+)\s*=\s*\{", re.MULTILINE)
# Picture field for an upgrade (second-tab-level)
UPGRADE_PICTURE_RE = re.compile(r"^\t\tpicture\s*=\s*(GFX_\w+)", re.MULTILINE)

LOC_KEY_RE = re.compile(r"^\s*(MD_auto_agency_\d+_\S+?):\s*\"([^\"]*)\"", re.MULTILINE)

HAS_DONE_RE = re.compile(r"has_done_agency_upgrade\s*=\s*(\w+)")

# create_intelligence_agency = { ... icon = GFX_x ... } — spans multiple lines
CREATE_AGENCY_RE = re.compile(
    r"create_intelligence_agency\s*=\s*\{([^{}]*?)\}",
    re.DOTALL,
)
AGENCY_ICON_RE = re.compile(r"icon\s*=\s*\"?(GFX_\w+)\"?")

# upgrade_intelligence_agency = upgrade_x (effect call, not ai_strategy block)
# The ai_strategy definitions use `upgrade_intelligence_agency = {` which is
# excluded here by requiring a word character (not `{`) on the RHS.
UPGRADE_CALL_RE = re.compile(r"upgrade_intelligence_agency\s*=\s*(upgrade_\w+)")

GFX_NAME_RE = re.compile(r'name\s*=\s*"(GFX_\w+)"')


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def _line_of(text: str, offset: int) -> int:
    """1-based line number for a character offset in text."""
    return text.count("\n", 0, offset) + 1


def _scan_agency_calls(stripped: str, filepath: str):
    create_icons = []
    for m in CREATE_AGENCY_RE.finditer(stripped):
        body = m.group(1)
        icon_match = AGENCY_ICON_RE.search(body)
        if not icon_match:
            continue
        gfx = icon_match.group(1)
        # Line number of the icon match within the original file
        abs_offset = m.start() + body.find(icon_match.group(0))
        line = _line_of(stripped, abs_offset)
        create_icons.append((filepath, line, gfx))

    upgrade_calls = []
    for m in UPGRADE_CALL_RE.finditer(stripped):
        upgrade = m.group(1)
        line = _line_of(stripped, m.start())
        upgrade_calls.append((filepath, line, upgrade))

    return create_icons, upgrade_calls


def process_file_for_agency_calls(args):
    """Return (create_icons, upgrade_calls) as lists of (relpath, line, value)."""
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
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # upgrade_X -> (source_file, level_count, picture_gfx)
        self.upgrade_defs: Dict[str, Dict] = {}
        # index -> upgrade_X token (short, e.g. 'upgrade_army_department')
        self.registered_upgrades: Dict[int, str] = {}
        self.registered_names: Dict[int, str] = {}
        self.registered_gfx: Dict[int, str] = {}
        self.max_levels: Dict[int, int] = {}
        self.loc_keys: Dict[str, str] = {}
        self.gfx_defined: Set[str] = set()

    # ---- Collection ----

    @staticmethod
    def _short_token(long_token: str) -> str:
        """MD_auto_agency_12_upgrade_commando_training -> upgrade_commando_training."""
        m = re.match(r"MD_auto_agency_\d+_(upgrade_\S+?)(?:_name|_gfx)?$", long_token)
        return m.group(1) if m else long_token

    def _collect_upgrade_defs(self) -> None:
        """Scan every *.txt in common/intelligence_agency_upgrades/."""
        pattern = str(Path(self.mod_path) / UPGRADES_DIR / "*.txt")
        for filepath in glob.iglob(pattern):
            text = _read(Path(filepath))
            if not text:
                continue
            stripped = strip_comments(text)
            matches = list(UPGRADE_DEF_RE.finditer(stripped))
            for i, m in enumerate(matches):
                name = m.group(1)
                start = m.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(stripped)
                body = stripped[start:end]
                level_count = len(
                    re.findall(r"^\t\tlevel\s*=\s*\{", body, re.MULTILINE)
                )
                picture_match = UPGRADE_PICTURE_RE.search(body)
                self.upgrade_defs[name] = {
                    "source": Path(filepath).relative_to(self.mod_path).as_posix(),
                    "levels": level_count,
                    "picture": picture_match.group(1) if picture_match else None,
                }

    def _collect_registry(self) -> None:
        text = strip_comments(_read(Path(self.mod_path) / ON_ACTIONS_FILE))
        if not text:
            return
        for idx, tok in AGENCY_UPGRADE_SET_RE.findall(text):
            self.registered_upgrades[int(idx)] = tok
        for idx, tok in AGENCY_NAMES_SET_RE.findall(text):
            self.registered_names[int(idx)] = tok
        for idx, tok in AGENCY_GFX_SET_RE.findall(text):
            self.registered_gfx[int(idx)] = tok
        for idx, val in AGENCY_MAX_SET_RE.findall(text):
            self.max_levels[int(idx)] = int(val)
        # Implicit default for max_upgrades is 1 for any registered index
        for idx in self.registered_upgrades:
            self.max_levels.setdefault(idx, 1)

    def _collect_loc(self) -> None:
        text = _read(Path(self.mod_path) / LOC_FILE)
        for key, value in LOC_KEY_RE.findall(text):
            self.loc_keys[key] = value

    def _collect_gfx(self) -> None:
        for gfx_file in glob.iglob(
            str(Path(self.mod_path) / "interface" / "**" / "*.gfx"), recursive=True
        ):
            text = _read(Path(gfx_file))
            for name in GFX_NAME_RE.findall(text):
                self.gfx_defined.add(name)

    # ---- Validations ----

    def _validate_registry_coverage(self) -> None:
        self._log_section(
            "Checking every defined upgrade is registered in the auto-agency system..."
        )

        results: List[str] = []
        registered_short: Set[str] = {
            self._short_token(t) for t in self.registered_upgrades.values()
        }

        # Every defined upgrade must appear in the registry.
        for name in sorted(self.upgrade_defs):
            src = self.upgrade_defs[name]["source"]
            if name not in registered_short:
                results.append(
                    f"{src}: upgrade '{name}' is defined but not registered in "
                    f"{ON_ACTIONS_FILE} (add global.agency_upgrades/_names/_gfx/_max_upgrades entries)"
                )

        # Every registry entry must point to a real upgrade.
        for idx, long_tok in sorted(self.registered_upgrades.items()):
            short = self._short_token(long_tok)
            if short not in self.upgrade_defs:
                results.append(
                    f"{ON_ACTIONS_FILE}: global.agency_upgrades^{idx} registers "
                    f"'{short}' but no upgrade with that name is defined in {UPGRADES_DIR}/"
                )

        # All three parallel arrays must use the same token per index.
        all_indices = (
            set(self.registered_upgrades)
            | set(self.registered_names)
            | set(self.registered_gfx)
        )
        for idx in sorted(all_indices):
            up = self.registered_upgrades.get(idx)
            nm = self.registered_names.get(idx)
            gf = self.registered_gfx.get(idx)
            if up is None:
                results.append(
                    f"{ON_ACTIONS_FILE}: index ^{idx} missing in global.agency_upgrades"
                )
            if nm is None:
                results.append(
                    f"{ON_ACTIONS_FILE}: index ^{idx} missing in global.agency_names"
                )
            elif up and nm != f"{up}_name":
                results.append(
                    f"{ON_ACTIONS_FILE}: global.agency_names^{idx} = '{nm}' but "
                    f"global.agency_upgrades^{idx} = '{up}' (name should be '{up}_name')"
                )
            if gf is None:
                results.append(
                    f"{ON_ACTIONS_FILE}: index ^{idx} missing in global.agency_gfx"
                )
            elif up and gf != f"{up}_gfx":
                results.append(
                    f"{ON_ACTIONS_FILE}: global.agency_gfx^{idx} = '{gf}' but "
                    f"global.agency_upgrades^{idx} = '{up}' (gfx should be '{up}_gfx')"
                )

        self._report(
            results,
            "✓ All defined upgrades are registered and parallel arrays are consistent",
            "Registry coverage / consistency issues:",
            category="agency-upgrades-registry",
        )

    def _validate_max_levels(self) -> None:
        self._log_section("Checking agency_max_upgrades vs level block count...")

        results: List[str] = []
        for idx, long_tok in sorted(self.registered_upgrades.items()):
            short = self._short_token(long_tok)
            actual = self.upgrade_defs.get(short, {}).get("levels")
            if actual is None:
                continue  # missing def already reported
            declared = self.max_levels.get(idx, 1)
            if declared != actual:
                results.append(
                    f"{ON_ACTIONS_FILE}: global.agency_max_upgrades^{idx} = {declared} "
                    f"but '{short}' has {actual} level block(s)"
                )

        self._report(
            results,
            "✓ All agency_max_upgrades values match level counts",
            "max_upgrades/level-count mismatches:",
            category="agency-upgrades-max-levels",
        )

    def _validate_loc_and_gfx(self) -> None:
        self._log_section("Checking loc key triples and GFX references...")

        results: List[str] = []

        # Validate every defined upgrade's picture resolves to a real sprite.
        for name, info in sorted(self.upgrade_defs.items()):
            picture = info["picture"]
            if not picture:
                results.append(
                    f"{info['source']}: upgrade '{name}' has no `picture =` field"
                )
            elif picture not in self.gfx_defined:
                results.append(
                    f"{info['source']}: upgrade '{name}' references "
                    f"picture '{picture}' not defined in any .gfx file"
                )

        # Validate every registered index has the three loc keys and that the
        # _gfx loc value matches the definition's picture.
        for idx, long_tok in sorted(self.registered_upgrades.items()):
            base = long_tok
            short = self._short_token(long_tok)
            if base not in self.loc_keys:
                results.append(f"{LOC_FILE}: missing key '{base}' for index {idx}")
            name_key = f"{base}_name"
            if name_key not in self.loc_keys:
                results.append(f"{LOC_FILE}: missing key '{name_key}' for index {idx}")
            gfx_key = f"{base}_gfx"
            if gfx_key not in self.loc_keys:
                results.append(f"{LOC_FILE}: missing key '{gfx_key}' for index {idx}")
                continue
            gfx_value = self.loc_keys[gfx_key]
            if gfx_value and gfx_value not in self.gfx_defined:
                results.append(
                    f"{LOC_FILE}: '{gfx_key}' references sprite '{gfx_value}' "
                    f"not defined in any .gfx file"
                )
            # Definition picture and loc _gfx should agree so the queue popup
            # icon matches the stock agency view icon.
            def_picture = self.upgrade_defs.get(short, {}).get("picture")
            if def_picture and gfx_value and def_picture != gfx_value:
                results.append(
                    f"{LOC_FILE}: '{gfx_key}' = '{gfx_value}' does not match "
                    f"'{short}' picture = '{def_picture}'"
                )

        self._report(
            results,
            "✓ All loc keys and GFX references resolve and match",
            "Loc/GFX integration issues:",
            category="agency-upgrades-loc-gfx",
        )

    def _validate_array_size(self) -> None:
        self._log_section("Checking resize_array size vs registered index count...")

        text = strip_comments(_read(Path(self.mod_path) / ON_ACTIONS_FILE))
        declared_sizes = [int(s) for s in RESIZE_ARRAY_RE.findall(text)]
        expected = max(self.registered_upgrades) + 1 if self.registered_upgrades else 0

        results: List[str] = []
        for size in declared_sizes:
            if size != expected:
                results.append(
                    f"{ON_ACTIONS_FILE}: resize_array size = {size} but "
                    f"{expected} indices are registered (0..{expected - 1})"
                )
        if self.registered_upgrades:
            missing = [
                i
                for i in range(max(self.registered_upgrades) + 1)
                if i not in self.registered_upgrades
            ]
            for i in missing:
                results.append(
                    f"{ON_ACTIONS_FILE}: index ^{i} is not registered "
                    f"(gap in global.agency_upgrades)"
                )

        self._report(
            results,
            "✓ Array sizes match and indices are contiguous",
            "Array size or index gap issues:",
            category="agency-upgrades-array-size",
        )

    def _validate_agency_calls(self) -> None:
        """Scan the whole mod for create_intelligence_agency and
        upgrade_intelligence_agency calls; validate icons and upgrade names."""
        self._log_section(
            "Checking create_intelligence_agency icons and upgrade_intelligence_agency calls..."
        )

        files = self._collect_files(
            [
                "common/**/*.txt",
                "events/**/*.txt",
                "history/**/*.txt",
            ]
        )
        scan_results = self._pool_map(
            process_file_for_agency_calls,
            [(f, self.mod_path) for f in files],
            chunksize=50,
        )

        create_icons: List = []
        upgrade_calls: List = []
        for icons, calls in scan_results:
            create_icons.extend(icons)
            upgrade_calls.extend(calls)

        results: List[str] = []
        known_upgrades = set(self.upgrade_defs)
        for filepath, line, gfx in create_icons:
            if gfx not in self.gfx_defined:
                rel = Path(filepath).relative_to(self.mod_path).as_posix()
                results.append(
                    f"{rel}:{line} - create_intelligence_agency icon '{gfx}' "
                    f"not defined in any .gfx file"
                )
        for filepath, line, upgrade in upgrade_calls:
            if upgrade not in known_upgrades:
                rel = Path(filepath).relative_to(self.mod_path).as_posix()
                results.append(
                    f"{rel}:{line} - upgrade_intelligence_agency references "
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

    def _validate_scripted_gui_prereqs(self) -> None:
        self._log_section("Checking scripted_gui prerequisite references...")

        text = strip_comments(_read(Path(self.mod_path) / SCRIPTED_GUI_FILE))
        if not text:
            self.log(
                f"{Colors.YELLOW if self.use_colors else ''}Missing {SCRIPTED_GUI_FILE} — skipping{Colors.ENDC if self.use_colors else ''}",
                "warning",
            )
            return

        results: List[str] = []
        known = set(self.upgrade_defs)
        for ref in sorted(set(HAS_DONE_RE.findall(text))):
            if ref not in known:
                results.append(
                    f"{SCRIPTED_GUI_FILE}: has_done_agency_upgrade references "
                    f"'{ref}' but no such upgrade is defined"
                )

        self._report(
            results,
            "✓ All has_done_agency_upgrade references resolve",
            "Unknown prerequisite references:",
            category="agency-upgrades-prereqs",
        )

    def run_validations(self):
        if self.staged_only and not self.staged_files:
            self.log(
                "No staged files found — skipping agency upgrade validation",
                "warning",
            )
            return

        self._collect_upgrade_defs()
        self._collect_registry()
        self._collect_loc()
        self._collect_gfx()

        self.log(
            f"  Defined upgrades: {len(self.upgrade_defs)} | "
            f"Registered indices: {len(self.registered_upgrades)} | "
            f"Loc keys: {len(self.loc_keys)} | "
            f"GFX sprites: {len(self.gfx_defined)}"
        )

        self._validate_registry_coverage()
        self._validate_max_levels()
        self._validate_loc_and_gfx()
        self._validate_array_size()
        self._validate_scripted_gui_prereqs()
        self._validate_agency_calls()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate intelligence agency upgrade integration")
