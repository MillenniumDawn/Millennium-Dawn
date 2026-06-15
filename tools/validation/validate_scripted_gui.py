#!/usr/bin/env python3
"""Cross-reference scripted GUIs against interface/*.gui, *.gfx, and localisation.

Surfaces silent failures where a name typo or missing reference loads without
error but does nothing at runtime.
"""
import os
import re
import sys
from typing import Dict, FrozenSet, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from shared_utils import extract_block_from_text
from validator_common import (
    BaseValidator,
    Severity,
    run_validator_main,
    should_skip_file,
)

# --- Regex constants ---

# Match a containerWindowType / buttonType / iconType / etc. definition opener:
#   <type> = { ... name = "X" ... }
_GUI_TYPE_OPENER = re.compile(
    r"\b(containerWindowType|buttonType|iconType|instantTextBoxType|editBoxType|"
    r"smallTextBoxType|gridBoxType|listboxType|positionType|scrollbarType|"
    r"checkboxType|comboBoxType|barType|OverlappingElementsBoxType|HtmlType|"
    r"textBoxType|instantTextboxType)\s*=\s*\{",
    re.IGNORECASE,
)

# Inside a GUI element, match `name = "..."` or `name = ...`
_GUI_NAME = re.compile(r"\bname\s*=\s*\"?([A-Za-z0-9_]+)\"?")

# scripted_gui block opener:   <name> = {
# Match identifier directly followed by = { in the scripted_guis context.
_SGUI_BLOCK_OPENER = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", re.MULTILINE)

# Scripted GUI trigger / effect name pattern:
#   <element_name>_<modifier_chain>_click[_enabled]  OR  <element_name>_visible/_hover
# Modifier chain: any combination of alt_/control_/shift_/right_ prefixes.
# Element is matched lazily so the longest valid modifier-chain wins.
_SGUI_HANDLER = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*?)_("
    r"(?:alt_|control_|shift_|right_)*click(?:_enabled)?|visible|hover"
    r")\s*=\s*\{",
    re.MULTILINE,
)

# context_type = ...
_SGUI_CONTEXT = re.compile(r"\bcontext_type\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")

# window_name = "..." (or unquoted)
_SGUI_WINDOW = re.compile(r"\bwindow_name\s*=\s*\"?([A-Za-z0-9_]+)\"?")

# parent_window_name = "..." / parent_window_token = X
_SGUI_PARENT_NAME = re.compile(r"\bparent_window_name\s*=\s*\"?([A-Za-z0-9_]+)\"?")
_SGUI_PARENT_TOKEN = re.compile(r"\bparent_window_token\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")

# dynamic_lists block — entry_container reference
_SGUI_ENTRY_CONTAINER = re.compile(r"\bentry_container\s*=\s*\"?([A-Za-z0-9_]+)\"?")

# dirty = ... — the variable the GUI refreshes on (may be scope-qualified, e.g. global.X)
_SGUI_DIRTY = re.compile(r"\bdirty\s*=\s*([A-Za-z_][A-Za-z0-9_.]*)")

# Variable write operations across the mod — capture the assignment target (LHS),
# optionally scope-qualified. Used to tell whether a dirty var is ever written and
# in which namespace it lives.
_VAR_WRITE = re.compile(
    r"\b(?:set_global_variable|set_variable|add_to_variable|subtract_from_variable|"
    r"multiply_variable|divide_variable|clamp_variable|round_variable)\s*=\s*\{\s*"
    r"(?:var\s*=\s*)?"
    r"((?:global\.|ROOT\.|PREV\.|THIS\.|FROM\.|OWNER\.|CONTROLLER\.|[A-Z]{2,4}\.)?"
    r"[A-Za-z_][A-Za-z0-9_]*)"
)

# global.X reference anywhere (read or write) — marks X as a global-namespace variable.
_GLOBAL_REF = re.compile(r"\bglobal\.([A-Za-z_][A-Za-z0-9_]*)")

# A `dirty = global.X` declaration — stripped before counting global refs so a
# global var that appears ONLY as a dirty line still reads as undefined.
_SGUI_DIRTY_GLOBAL = re.compile(r"\bdirty\s*=\s*global\.[A-Za-z_][A-Za-z0-9_]*")

# ai_test_scopes — value (can appear multiple times in one scripted_gui block)
_SGUI_AI_TEST_SCOPES = re.compile(r"\bai_test_scopes\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")

# [!trigger_name] loc formatter — captures the trigger name
_LOC_BANG_REF = re.compile(r"\[!([A-Za-z_][A-Za-z0-9_]*)\]")

# Loc key extraction (matching validator_common's pattern):
#   key: "value"
_LOC_KEY = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.@]+)\s*:[0-9]?\s*\"", re.MULTILINE)

# --- Valid enum values ---

# Valid context_type values per HOI4 docs
_VALID_CONTEXT_TYPES: FrozenSet[str] = frozenset(
    {
        "player_context",
        "selected_country_context",
        "selected_state_context",
        "decision_category",
        "diplomatic_action",
        "national_focus_context",
        "country_mapicon",
        "state_mapicon",
    }
)

# Valid ai_test_scopes by context_type
_VALID_AI_TEST_SCOPES: Dict[str, FrozenSet[str]] = {
    "selected_country_context": frozenset(
        {
            "test_self_country",
            "test_enemy_countries",
            "test_ally_countries",
            "test_neighbouring_countries",
            "test_neighbouring_ally_countries",
            "test_neighbouring_enemy_countries",
            "test_if_only_major",
            "test_if_only_coastal",
        }
    ),
    "selected_state_context": frozenset(
        {
            "test_self_owned_states",
            "test_enemy_owned_states",
            "test_ally_owned_states",
            "test_self_controlled_states",
            "test_enemy_controlled_states",
            "test_ally_controlled_states",
            "test_neighbouring_states",
            "test_neighbouring_enemy_states",
            "test_neighbouring_ally_states",
            "test_our_neighbouring_states",
            "test_our_neighbouring_states_against_allies",
            "test_our_neighbouring_states_against_enemies",
            "test_contesded_states",
            "test_if_only_major",
            "test_if_only_coastal",
        }
    ),
}

# Known vanilla HOI4 container windows we cannot verify locally — referenced
# as parent_window_name in MD scripted GUIs but defined by base game / DLC.
_VANILLA_PARENT_WINDOWS: FrozenSet[str] = frozenset(
    {
        "templatedeploymentwindow",
        "countryinternationalmarketview",
        "armylist",
        "production_tabs",
        "construction_tabs",
        "trade_tabs",
        "research_tabs",
        "logistics_tabs",
        "navy_logistics",
        "diplomacy_tabs",
        "decision_tab",
        "politics_tab",
        "top_bar",
        "characters_tab",
    }
)

# Template substitution markers in container/element names. When we see these
# in entry_container or element refs, skip — the real name is substituted at
# runtime via meta_effect or scripted-loc dispatch.
_TEMPLATE_MARKERS: Tuple[str, ...] = ("_TAG_", "_PLACEHOLDER_", "_TEMPLATE_")


def _looks_like_template(name: str) -> bool:
    """Heuristic: name contains a template marker or ends in an underscore
    (truncated name typically completed by meta_effect substitution)."""
    if name.endswith("_"):
        return True
    return any(marker in name for marker in _TEMPLATE_MARKERS)


def _normalise_path(p: str) -> str:
    """Normalise path for staged-file comparison (forward slashes, no leading ./)."""
    return p.replace("\\", "/").lstrip("./")


# Module-level so disk_cache results stay picklable and the parse is computed
# only from the file's text.


def _parse_gui_text(text: str, rel: str) -> Dict:
    """Parse one .gui file's text. Returns the GUI-element data this file
    contributes, keyed by collection name. Mutates nothing."""
    elements: Dict[str, Tuple[str, str, int]] = {}
    element_files: Dict[str, str] = {}
    containers: List[str] = []

    for m in _GUI_TYPE_OPENER.finditer(text):
        type_name = m.group(1)
        block_start = m.end()
        block, end = extract_block_from_text(text, block_start - 1)
        if end == -1:
            continue
        line_no = text.count("\n", 0, m.start()) + 1
        name_m = _GUI_NAME.search(block)
        if not name_m:
            continue
        name = name_m.group(1)
        elements[name] = (type_name, rel, line_no)
        element_files[name] = rel
        if type_name.lower() == "containerwindowtype":
            containers.append(name)

    return {
        "elements": elements,
        "element_files": element_files,
        "containers": containers,
    }


def _parse_one_sgui_block(name: str, body: str, file: str, line: int) -> Dict:
    """Build a single scripted_gui block dict from its body text."""
    block = {
        "name": name,
        "file": file,
        "line": line,
        "window_name": None,
        "parent_window_name": None,
        "parent_window_token": None,
        "context_type": None,
        "dirty": None,
        "ai_test_scopes": [],
        "handlers": set(),
        "entry_containers": [],
    }
    m = _SGUI_CONTEXT.search(body)
    if m:
        block["context_type"] = m.group(1)
    m = _SGUI_WINDOW.search(body)
    if m:
        block["window_name"] = m.group(1)
    m = _SGUI_PARENT_NAME.search(body)
    if m:
        block["parent_window_name"] = m.group(1)
    m = _SGUI_PARENT_TOKEN.search(body)
    if m:
        block["parent_window_token"] = m.group(1)
    m = _SGUI_DIRTY.search(body)
    if m:
        block["dirty"] = m.group(1)
    for sm in _SGUI_AI_TEST_SCOPES.finditer(body):
        block["ai_test_scopes"].append(sm.group(1))
    for ec in _SGUI_ENTRY_CONTAINER.finditer(body):
        block["entry_containers"].append(ec.group(1))
    for hm in _SGUI_HANDLER.finditer(body):
        elem = hm.group(1)
        kind = hm.group(2)
        block["handlers"].add((elem, kind))
    return block


def _parse_scripted_gui_text(text: str, rel: str) -> Tuple[List[Dict], Set[str]]:
    """Parse one scripted_gui .txt file's text. Returns
    (list_of_block_dicts, set_of_trigger_names). Mutates nothing."""
    blocks: List[Dict] = []
    trigger_names: Set[str] = set()

    outer = re.search(r"\bscripted_gui\s*=\s*\{", text)
    if not outer:
        return blocks, trigger_names
    outer_start = outer.end()
    outer_body, outer_end = extract_block_from_text(text, outer_start - 1)
    if outer_end == -1:
        return blocks, trigger_names

    i = 0
    n = len(outer_body)
    while i < n:
        m = _SGUI_BLOCK_OPENER.search(outer_body, i)
        if not m:
            break
        name = m.group(1)
        inner_start = m.end()
        body, inner_end = extract_block_from_text(outer_body, inner_start - 1)
        if inner_end == -1:
            break
        line_no = text.count("\n", 0, outer_start + m.start()) + 1
        block = _parse_one_sgui_block(name, body, rel, line_no)
        for elem, kind in block["handlers"]:
            trigger_names.add(f"{elem}_{kind}")
        blocks.append(block)
        i = inner_end

    return blocks, trigger_names


def _parse_var_writes_text(text: str) -> Tuple[Set[str], Set[str]]:
    """Parse one .txt file's text for variable writes. Returns
    (written_var_names, global_ref_names) with scope prefixes stripped to the
    bare variable name. Mutates nothing."""
    written: Set[str] = set()
    global_refs: Set[str] = set()
    for m in _VAR_WRITE.finditer(text):
        written.add(m.group(1).rsplit(".", 1)[-1])
    scan = _SGUI_DIRTY_GLOBAL.sub("", text)
    for m in _GLOBAL_REF.finditer(scan):
        global_refs.add(m.group(1))
    return written, global_refs


class ScriptedGuiValidator(BaseValidator):
    TITLE = "SCRIPTED GUI VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".gui", ".yml"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache the staged-files set for fast filtering
        self._staged_set: Set[str] = set(self.staged_files or [])
        # Populated by parsing passes
        self._gui_elements: Dict[str, Tuple[str, str, int]] = {}
        # name -> (type, file, line)
        self._gui_containers: Set[str] = set()
        self._gui_element_files: Dict[str, str] = {}
        # element_name -> .gui file path

        self._sgui_blocks: List[Dict] = []
        # Each: { name, window_name, parent_window_name, parent_window_token,
        #         context_type, dirty, ai_test_scopes (list), handlers (set of (elem, kind)),
        #         entry_containers (set), file, line }
        self._sgui_trigger_names: Set[str] = set()
        # All <element>_click_enabled / _visible style trigger names (for [!] resolution)

        self._loc_keys: FrozenSet[str] = frozenset()
        # Variable-write index (built lazily, only when a dirty var needs checking)
        self._written_names: Set[str] = set()
        self._global_ref_names: Set[str] = set()

    def add_issue(
        self, severity: str, category: str, message: str, file: str = "", line: int = 0
    ) -> None:
        """Override: in staged_only mode, suppress issues whose file isn't in
        the staged set so pre-commit only reports on what the commit changes."""
        if self.staged_only:
            if not self._staged_set or _normalise_path(file) not in self._staged_set:
                return
        super().add_issue(severity, category, message, file, line)

    # ------------------------------------------------------------------
    # Parse passes
    # ------------------------------------------------------------------

    def _parse_gui_files(self) -> None:
        self._log_section("Parsing interface/*.gui files")
        gui_dir = os.path.join(self.mod_path, "interface")
        if not os.path.isdir(gui_dir):
            return
        files = []
        for root, _, names in os.walk(gui_dir):
            for n in names:
                if n.endswith(".gui"):
                    files.append(os.path.join(root, n))

        for filepath in sorted(files):
            self._parse_one_gui_file(filepath)

        self.log(
            f"  Indexed {len(self._gui_elements)} GUI elements across "
            f"{len(files)} .gui files"
        )

    def _parse_one_gui_file(self, filepath: str) -> None:
        try:
            with open(filepath, "r", encoding="utf-8-sig") as fh:
                text = fh.read()
        except Exception as e:
            self.log(f"  ! could not read {filepath}: {e}", "warning")
            return

        rel = os.path.relpath(filepath, self.mod_path)
        data = disk_cache.per_file_cached_by_content(
            self.mod_path,
            "sgui.gui2",
            filepath,
            text,
            lambda: _parse_gui_text(text, rel),
        )
        self._gui_elements.update(data["elements"])
        self._gui_element_files.update(data["element_files"])
        self._gui_containers.update(data["containers"])

    def _parse_scripted_gui_files(self) -> None:
        self._log_section("Parsing common/scripted_guis/*.txt files")
        sgui_dir = os.path.join(self.mod_path, "common", "scripted_guis")
        if not os.path.isdir(sgui_dir):
            return
        files = [
            os.path.join(sgui_dir, f)
            for f in os.listdir(sgui_dir)
            if f.endswith(".txt") and not should_skip_file(f)
        ]
        for filepath in sorted(files):
            self._parse_one_scripted_gui_file(filepath)

        self.log(
            f"  Indexed {len(self._sgui_blocks)} scripted_gui blocks, "
            f"{len(self._sgui_trigger_names)} trigger names"
        )

    def _parse_one_scripted_gui_file(self, filepath: str) -> None:
        try:
            with open(filepath, "r", encoding="utf-8-sig") as fh:
                text = fh.read()
        except Exception as e:
            self.log(f"  ! could not read {filepath}: {e}", "warning")
            return

        rel = os.path.relpath(filepath, self.mod_path)
        blocks, trigger_names = disk_cache.per_file_cached_by_content(
            self.mod_path,
            "sgui.scripted3",
            filepath,
            text,
            lambda: _parse_scripted_gui_text(text, rel),
        )
        self._sgui_blocks.extend(blocks)
        self._sgui_trigger_names.update(trigger_names)

    def _index_variable_writes(self) -> None:
        """Walk common/ and events/ once, collecting every variable-write target
        and every global.X reference. Used by the dirty check to tell whether a
        dirty var is ever written and which namespace it lives in. Skipped when
        no scripted_gui declares a dirty var."""
        if not any(b["dirty"] for b in self._sgui_blocks):
            return
        self._log_section("Indexing variable writes (for dirty checks)")
        roots = [
            os.path.join(self.mod_path, "common"),
            os.path.join(self.mod_path, "events"),
        ]
        files: List[str] = []
        for base in roots:
            if not os.path.isdir(base):
                continue
            for root, _, names in os.walk(base):
                for n in names:
                    if n.endswith(".txt"):
                        files.append(os.path.join(root, n))
        for filepath in sorted(files):
            try:
                with open(filepath, "r", encoding="utf-8-sig") as fh:
                    text = fh.read()
            except Exception:
                continue
            written, global_refs = disk_cache.per_file_cached_by_content(
                self.mod_path,
                "sgui.varwrites2",
                filepath,
                text,
                lambda text=text: _parse_var_writes_text(text),
            )
            self._written_names.update(written)
            self._global_ref_names.update(global_refs)
        self.log(
            f"  Indexed {len(self._written_names)} written vars, "
            f"{len(self._global_ref_names)} global refs"
        )

    def _load_loc_keys_and_cache(self) -> FrozenSet[str]:
        """Walk English loc once; cache (filepath, text) for downstream checks
        that need to scan the same content (avoids a second filesystem walk
        in _check_bang_trigger_refs)."""
        self._log_section("Loading English localisation keys")
        loc_dir = os.path.join(self.mod_path, "localisation", "english")
        keys: Set[str] = set()
        self._loc_file_texts: List[Tuple[str, str]] = []
        if not os.path.isdir(loc_dir):
            return frozenset()
        for root, _, names in os.walk(loc_dir):
            for n in names:
                if not n.endswith(".yml"):
                    continue
                fp = os.path.join(root, n)
                try:
                    with open(fp, "r", encoding="utf-8-sig") as fh:
                        text = fh.read()
                except Exception:
                    continue
                self._loc_file_texts.append((fp, text))
                for m in _LOC_KEY.finditer(text):
                    keys.add(m.group(1))
        self.log(
            f"  Indexed {len(keys)} loc keys across {len(self._loc_file_texts)} files"
        )
        return frozenset(keys)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def _check_handler_element_refs(self) -> None:
        """Tier 1.1 — every <element>_click_enabled / _visible / _click / etc.
        in scripted_gui triggers/effects must match a button/icon defined in
        any .gui file."""
        self._log_section("Checking scripted_gui handler element references")
        all_gui_names = set(self._gui_elements.keys())
        seen: Set[Tuple[str, str, str, int]] = set()
        for block in self._sgui_blocks:
            for elem, kind in block["handlers"]:
                if elem in all_gui_names:
                    continue
                # Skip placeholder / template patterns (meta_effect substitution)
                if "[" in elem or "]" in elem:
                    continue
                key = (elem, kind, block["file"], block["line"])
                if key in seen:
                    continue
                seen.add(key)
                self.add_issue(
                    Severity.ERROR,
                    "DEAD_HANDLER",
                    f"Scripted GUI in '{block['name']}' references '{elem}_{kind}' "
                    f"but no button/icon named '{elem}' exists in any .gui file",
                    file=block["file"],
                    line=block["line"],
                )

    def _check_bang_trigger_refs(self) -> None:
        """Tier 1.3 — every [!trigger_name] in loc strings must match a
        scripted_gui trigger name. Reuses the loc-file text cache populated
        in _load_loc_keys_and_cache so the loc directory is walked once."""
        self._log_section("Checking [!trigger_name] formatter references in loc")
        seen: Set[Tuple[str, str, int]] = set()
        for fp, text in self._loc_file_texts:
            rel = os.path.relpath(fp, self.mod_path)
            for m in _LOC_BANG_REF.finditer(text):
                trig = m.group(1)
                if trig in self._sgui_trigger_names:
                    continue
                line_no = text.count("\n", 0, m.start()) + 1
                key = (trig, rel, line_no)
                if key in seen:
                    continue
                seen.add(key)
                self.add_issue(
                    Severity.ERROR,
                    "DEAD_BANG_REF",
                    f"[!{trig}] in loc but no scripted_gui trigger named "
                    f"'{trig}' is defined — formatter will produce empty text",
                    file=rel,
                    line=line_no,
                )

    def _check_window_refs(self) -> None:
        """Tier 1.4 — window_name / parent_window_name / parent_window_token
        reference real containers."""
        self._log_section("Checking window_name / parent_window references")
        for block in self._sgui_blocks:
            if block["window_name"]:
                if block["window_name"] not in self._gui_containers:
                    self.add_issue(
                        Severity.ERROR,
                        "MISSING_WINDOW",
                        f"Scripted GUI '{block['name']}' references "
                        f"window_name = \"{block['window_name']}\" but no "
                        f"containerWindowType with that name exists",
                        file=block["file"],
                        line=block["line"],
                    )
            if block["parent_window_name"]:
                pwn = block["parent_window_name"]
                if pwn in self._gui_containers:
                    continue
                base = pwn.replace("_instance", "")
                if base in self._gui_containers:
                    continue
                # Skip vanilla containers we don't define locally
                if (
                    pwn.lower() in _VANILLA_PARENT_WINDOWS
                    or base.lower() in _VANILLA_PARENT_WINDOWS
                ):
                    continue
                self.add_issue(
                    Severity.WARNING,
                    "MISSING_PARENT_WINDOW",
                    f"Scripted GUI '{block['name']}' references "
                    f'parent_window_name = "{pwn}" but no containerWindowType '
                    f"with that name (or its base form) exists in MD .gui files "
                    f"(may be a vanilla container)",
                    file=block["file"],
                    line=block["line"],
                )

    def _check_entry_containers(self) -> None:
        """Tier 1.5 — dynamic_lists entry_container references a real container.
        Template patterns (containing _TAG_, ending in _) are skipped — those
        are completed at runtime by meta_effect substitution."""
        self._log_section("Checking dynamic_lists entry_container references")
        for block in self._sgui_blocks:
            for ec in block["entry_containers"]:
                if ec in self._gui_containers:
                    continue
                if _looks_like_template(ec):
                    continue
                self.add_issue(
                    Severity.ERROR,
                    "MISSING_ENTRY_CONTAINER",
                    f"Scripted GUI '{block['name']}' references entry_container = "
                    f'"{ec}" but no containerWindowType with that name exists — '
                    f"dynamic list will render blank",
                    file=block["file"],
                    line=block["line"],
                )

    def _check_context_type_enum(self) -> None:
        """Tier 1.6 — context_type is a valid enum."""
        self._log_section("Checking context_type enum values")
        for block in self._sgui_blocks:
            ct = block["context_type"]
            if not ct:
                continue
            if ct not in _VALID_CONTEXT_TYPES:
                self.add_issue(
                    Severity.ERROR,
                    "INVALID_CONTEXT_TYPE",
                    f"Scripted GUI '{block['name']}' has context_type = "
                    f"{ct} which is not a valid value. Valid: "
                    f"{', '.join(sorted(_VALID_CONTEXT_TYPES))}",
                    file=block["file"],
                    line=block["line"],
                )

    def _check_dirty_var(self) -> None:
        """Tier 2.1 — a dirty var must actually be written somewhere (or the GUI
        never refreshes), and its scope must match the mechanic. A country-scope
        dirty var for a variable that lives in the global namespace can't track a
        shared mechanic's updates. A scripted_gui without a dirty var is fine —
        only declared dirty vars are checked."""
        self._log_section("Checking dirty variable scope / definition")
        for block in self._sgui_blocks:
            d = block["dirty"]
            if not d or d in ("yes", "no"):
                continue
            if "[" in d or "]" in d:  # runtime-substituted name, can't resolve
                continue
            base = d.rsplit(".", 1)[-1]
            if d.startswith("global."):
                # A global dirty var is live if anything writes it or reads it as
                # global.X (engine-provided globals like global.year are only read).
                if (
                    base not in self._written_names
                    and base not in self._global_ref_names
                ):
                    self.add_issue(
                        Severity.WARNING,
                        "DIRTY_VAR_UNDEFINED",
                        f"Scripted GUI '{block['name']}' has dirty = {d} but no "
                        f"effect ever writes or reads that variable — the GUI "
                        f"never refreshes",
                        file=block["file"],
                        line=block["line"],
                    )
            elif base in self._global_ref_names:
                self.add_issue(
                    Severity.WARNING,
                    "DIRTY_SCOPE_MISMATCH",
                    f"Scripted GUI '{block['name']}' has dirty = {d} (country "
                    f"scope) but '{base}' is a global variable (global.{base}); a "
                    f"shared mechanic should use dirty = global.{base} so every "
                    f"open instance refreshes",
                    file=block["file"],
                    line=block["line"],
                )
            elif base not in self._written_names:
                self.add_issue(
                    Severity.WARNING,
                    "DIRTY_VAR_UNDEFINED",
                    f"Scripted GUI '{block['name']}' has dirty = {d} but no effect "
                    f"ever writes that variable — the GUI never refreshes",
                    file=block["file"],
                    line=block["line"],
                )

    def _check_ai_test_scopes(self) -> None:
        """Tier 2.2 — ai_test_scopes values must match context_type."""
        self._log_section("Checking ai_test_scopes vs context_type")
        for block in self._sgui_blocks:
            if not block["ai_test_scopes"]:
                continue
            ct = block["context_type"]
            valid = _VALID_AI_TEST_SCOPES.get(ct, frozenset())
            if not valid:
                # Either no context_type set (caught elsewhere) or
                # context doesn't support ai_test_scopes — flag the latter
                if ct and ct in _VALID_CONTEXT_TYPES:
                    self.add_issue(
                        Severity.WARNING,
                        "AI_TEST_SCOPES_NOT_APPLICABLE",
                        f"Scripted GUI '{block['name']}' uses ai_test_scopes but "
                        f"context_type = {ct} doesn't support them — only "
                        f"selected_country_context and selected_state_context do",
                        file=block["file"],
                        line=block["line"],
                    )
                continue
            for scope in block["ai_test_scopes"]:
                if scope not in valid:
                    self.add_issue(
                        Severity.ERROR,
                        "INVALID_AI_TEST_SCOPE",
                        f"Scripted GUI '{block['name']}' (context_type = {ct}) "
                        f"has ai_test_scopes = {scope}, which isn't valid for "
                        f"that context",
                        file=block["file"],
                        line=block["line"],
                    )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run_validations(self) -> None:
        # Phase 1: parse all sources
        self._parse_gui_files()
        self._parse_scripted_gui_files()
        self._index_variable_writes()
        self._loc_keys = self._load_loc_keys_and_cache()

        # Phase 2: cross-reference checks
        self._check_handler_element_refs()
        self._check_bang_trigger_refs()
        self._check_window_refs()
        self._check_entry_containers()
        self._check_context_type_enum()
        self._check_dirty_var()
        self._check_ai_test_scopes()


def main() -> int:
    return run_validator_main(
        ScriptedGuiValidator,
        description="Validate scripted GUI cross-references against .gui and loc files.",
    )


if __name__ == "__main__":
    sys.exit(main())
