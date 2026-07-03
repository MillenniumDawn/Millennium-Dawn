#!/usr/bin/env python3

"""
Standardizer for HOI4 history/countries files.

Reorders the contents of every dated history block (e.g. ``2000.1.1 = { ... }``)
into a fixed, readable grouping without changing anything semantically. The
transform is lossless (no statement dropped) and idempotent (running twice is a
no-op). Content outside dated blocks (``capital = ...``, naval OOB, equipment
variants) is passed through untouched.

Target ordering inside each dated block:
  1. Consolidated ``add_ideas`` with # Laws / # MD Ideas / # Internal Factions /
     # Country Content sub-groups.
  2. # Dynamic Modifiers   - each add_dynamic_modifier followed by the
     set/add_variable lines whose variable its definition reads.
  3. # System Variables    - remaining MD-system vars + add_to_array global.*
  4. # Special Projects
  5. # Technologies         - set_technology + DLC-conditional if blocks.
  6. # Country Variables / # Power Balance / # State Setup / # Country Flags /
     # Other.

Classification is data-driven: idea groups are scanned from common/ideas and the
modifier->variable map from common/dynamic_modifiers, so the tool works for any
country, not just CHI.
"""

import glob
import os
import re
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import extract_block, log_message, strip_inline_comment

from common_utils import BaseStandardizer, collapse_blank_runs, run_standardizer

# --------------------------------------------------------------------------- #
# Classification loaders (cached per mod root)
# --------------------------------------------------------------------------- #

_IDEA_CACHE: Dict[str, Tuple[set, set]] = {}
_MODIFIER_CACHE: Dict[str, Dict[str, set]] = {}

_OPENER_RE = re.compile(r"^([\w:]+)\s*=\s*\{")
_LAW_RE = re.compile(r"law\s*=\s*yes\b")
_LAWFILE_RE = re.compile(r"^AA_(law_|corruption|religion)", re.IGNORECASE)
_TAG_PREFIX_RE = re.compile(r"^[A-Z]{3}_")


def _detect_mod_root(start: str) -> Optional[str]:
    """Walk up from *start* until a directory holding both common/ and history/."""
    path = os.path.abspath(start)
    if os.path.isfile(path):
        path = os.path.dirname(path)
    for _ in range(12):
        if os.path.isdir(os.path.join(path, "common")) and os.path.isdir(
            os.path.join(path, "history")
        ):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return None


def _load_idea_classification(mod_root: str) -> Tuple[set, set]:
    """Return ``(law_tokens, faction_tokens)`` scanned from common/ideas/*.txt.

    A token is a Law when its category carries ``law = yes`` or it is defined in
    an ``AA_law_*`` / corruption / religion file (excluding internal_factions).
    A token is an internal faction when it sits in the ``internal_factions``
    category.
    """
    key = os.path.abspath(mod_root)
    cached = _IDEA_CACHE.get(key)
    if cached is not None:
        return cached

    category_of_token: Dict[str, str] = {}
    file_is_lawfile: Dict[str, bool] = {}
    law_categories: set = set()

    ideas_dir = os.path.join(mod_root, "common", "ideas")
    for path in glob.glob(os.path.join(ideas_dir, "*.txt")):
        is_lawfile = bool(_LAWFILE_RE.match(os.path.basename(path)))
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            continue
        stack: List[str] = []
        for raw in lines:
            code = strip_inline_comment(raw)
            stripped = code.strip()
            if _LAW_RE.match(stripped) and len(stack) >= 2:
                law_categories.add(stack[1])
            m = _OPENER_RE.match(stripped)
            nopen = code.count("{")
            nclose = code.count("}")
            if m:
                name = m.group(1)
                if len(stack) == 2:  # ideas > category > token
                    category_of_token[name] = stack[1]
                    file_is_lawfile[name] = is_lawfile
                stack.append(name)
                net = nopen - nclose
                for _ in range(1 - net):
                    if stack:
                        stack.pop()
            else:
                net = nopen - nclose
                if net < 0:
                    for _ in range(-net):
                        if stack:
                            stack.pop()
                elif net > 0:
                    stack.extend(["?"] * net)

    faction_tokens = {
        t for t, c in category_of_token.items() if c == "internal_factions"
    }
    law_tokens = {
        t
        for t, c in category_of_token.items()
        if c != "internal_factions"
        and (c in law_categories or file_is_lawfile.get(t, False))
    }

    _IDEA_CACHE[key] = (law_tokens, faction_tokens)
    return law_tokens, faction_tokens


def _load_modifier_variables(mod_root: str) -> Dict[str, set]:
    """Return ``{modifier_name: {variable_name, ...}}`` from common/dynamic_modifiers.

    For each top-level modifier block, collect the bare-identifier right-hand
    sides of ``field = variable`` lines. Spurious entries (icon names, etc.) are
    harmless: they never match a real ``set_variable`` left-hand side.
    """
    key = os.path.abspath(mod_root)
    cached = _MODIFIER_CACHE.get(key)
    if cached is not None:
        return cached

    assign_re = re.compile(r"^(\w+)\s*=\s*([A-Za-z_]\w*)\b")
    mods: Dict[str, set] = {}

    dm_dir = os.path.join(mod_root, "common", "dynamic_modifiers")
    for path in glob.glob(os.path.join(dm_dir, "*.txt")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            continue
        stack: List[str] = []
        for raw in lines:
            code = strip_inline_comment(raw)
            stripped = code.strip()
            nopen = code.count("{")
            nclose = code.count("}")
            m = _OPENER_RE.match(stripped)
            if m:
                stack.append(m.group(1))
                net = nopen - nclose
                for _ in range(1 - net):
                    if stack:
                        stack.pop()
                continue
            a = assign_re.match(stripped)
            if a and stack:
                field, value = a.group(1), a.group(2)
                if field != "icon" and value not in ("yes", "no", "x", "always"):
                    mods.setdefault(stack[0], set()).add(value)
            net = nopen - nclose
            if net < 0:
                for _ in range(-net):
                    if stack:
                        stack.pop()
            elif net > 0:
                stack.extend(["?"] * net)

    _MODIFIER_CACHE[key] = mods
    return mods


# --------------------------------------------------------------------------- #
# Comment / statement helpers
# --------------------------------------------------------------------------- #

# Structural section headers we re-emit ourselves. Stripped on input so a second
# pass does not accumulate duplicate headers (keeps the transform idempotent).
_BOILERPLATE_HEADERS = {
    "set ideas",
    "set variables and dynamic modifiers",
    "set variables",
    "set countryflags",
    "set country flags",
    "special projects",
    "state specific",
    "misc",
    # headers this tool emits:
    "ideas",
    "dynamic modifiers",
    "system variables",
    "technologies",
    "country variables",
    "power balance",
    "state setup",
    "country flags",
    "other",
    "laws",
    "md ideas",
    "internal factions",
    "country content",
    "army equipment",
    "air force equipment",
    "naval equipment",
    "opinion modifiers",
}

_DATE_BLOCK_RE = r"^\s*\d{1,4}\.\d{1,2}\.\d{1,2}\s*=\s*\{"
_HEAD_RE = re.compile(r"^([\w:]+|\d+)\s*=")
_VAR_TYPES = {
    "set_variable",
    "add_to_variable",
    "subtract_from_variable",
    "multiply_variable",
    "divide_variable",
    "set_temp_variable",
    "add_to_temp_variable",
    "clamp_variable",
}


def _is_boilerplate_comment(text: str) -> bool:
    norm = text.strip().lstrip("#").strip().lower()
    return norm in _BOILERPLATE_HEADERS


def _head_token(lines: List[str]) -> str:
    if not lines:
        return ""
    s = strip_inline_comment(lines[0]).strip()
    m = _HEAD_RE.match(s)
    return m.group(1) if m else ""


def _variable_name(lines: List[str]) -> Optional[str]:
    text = " ".join(strip_inline_comment(l).strip() for l in lines)
    m = re.search(r"\{\s*var\s*=\s*([\w.]+)", text)
    if m:
        return m.group(1)
    m = re.search(r"=\s*\{\s*([A-Za-z_][\w.]*)\s*=", text)
    return m.group(1) if m else None


def _modifier_name(lines: List[str]) -> Optional[str]:
    text = " ".join(strip_inline_comment(l).strip() for l in lines)
    m = re.search(r"modifier\s*=\s*([A-Za-z_]\w*)", text)
    return m.group(1) if m else None


# --------------------------------------------------------------------------- #
# Standardizer
# --------------------------------------------------------------------------- #


class HistoryStandardizer(BaseStandardizer):
    """Reorder the contents of dated history blocks into a fixed grouping."""

    def __init__(
        self,
        verbose: bool = False,
        mod_root: Optional[str] = None,
        idea_law: Optional[set] = None,
        idea_faction: Optional[set] = None,
        modifier_vars: Optional[Dict[str, set]] = None,
    ):
        super().__init__(verbose=verbose)
        self._mod_root = mod_root
        self._law = idea_law
        self._faction = idea_faction
        self._modvars = modifier_vars

    # -- classification bootstrap ------------------------------------------- #

    def _ensure_classification(self, input_file: str) -> None:
        if self._law is not None and self._faction is not None and self._modvars is not None:
            return
        root = self._mod_root or _detect_mod_root(input_file)
        if root:
            law, faction = _load_idea_classification(root)
            self._law = law if self._law is None else self._law
            self._faction = faction if self._faction is None else self._faction
            self._modvars = (
                _load_modifier_variables(root) if self._modvars is None else self._modvars
            )
            log_message("INFO", f"Mod root: {root}", self.verbose)
        else:
            log_message(
                "WARNING",
                "Could not detect mod root; idea/modifier grouping degraded",
            )
            self._law = self._law or set()
            self._faction = self._faction or set()
            self._modvars = self._modvars or {}

    def standardize_file(self, input_file: str, output_file: str) -> bool:
        self._ensure_classification(input_file)
        return super().standardize_file(input_file, output_file)

    # -- BaseStandardizer interface ----------------------------------------- #

    def get_block_pattern(self) -> str:
        return _DATE_BLOCK_RE

    def _equipment_domain(self, lines: List[str]) -> int:
        """0 = army, 1 = air force, 2 = navy - by oob marker then equipment `type`."""
        text = "\n".join(lines)
        if (
            "set_air_oob" in text
            or "airframe" in text
            or re.search(r"\b(?:AS_Fighter|Strike_fighter)", text)
        ):
            return 1
        if "set_naval_oob" in text or "_hull" in text:
            return 2
        return 0

    def _classify_idea(self, token: str) -> str:
        if _TAG_PREFIX_RE.match(token):
            return "country"
        if token in (self._faction or set()):
            return "faction"
        if token in (self._law or set()):
            return "law"
        return "md"

    def _split_statements(self, body: List[str]) -> List[Dict[str, List[str]]]:
        """Split block body into statements, each carrying its leading comments."""
        statements: List[Dict[str, List[str]]] = []
        pending: List[str] = []
        i = 0
        n = len(body)
        while i < n:
            raw = body[i]
            code = strip_inline_comment(raw)
            stripped = code.strip()
            if stripped == "" and raw.strip() == "":
                i += 1
                continue
            if raw.lstrip().startswith("#"):
                text = raw.rstrip()
                if not _is_boilerplate_comment(text):
                    pending.append(text)
                i += 1
                continue
            nopen = code.count("{")
            nclose = code.count("}")
            if nopen > 0 and (nopen - nclose) > 0:
                block, next_i = extract_block(body, i)
                lines = [l.rstrip() for l in block]
                i = next_i
            else:
                lines = [raw.rstrip()]
                i += 1
            statements.append({"comments": pending, "lines": lines})
            pending = []
        if pending:
            statements.append({"comments": pending, "lines": []})
        return statements

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        open_line = block_lines[0].rstrip()
        close_line = block_lines[-1].rstrip() if len(block_lines) > 1 else "}"
        lead_ws = open_line[: len(open_line) - len(open_line.lstrip())]
        indent = lead_ws + "\t"

        body = block_lines[1:-1]
        statements = self._split_statements(body)

        props: Dict[str, Any] = {
            "id": open_line.split("=")[0].strip(),
            "open_line": open_line,
            "close_line": close_line,
            "indent": indent,
            "leader_top": [],  # start_politics_input / startup_politics / create_country_leader
            "politics_top": [],  # set_popularities / set_politics
            "equipment": [],  # list of (domain_rank, stmt)
            "opinion": [],  # add_opinion_modifier / reverse_add_opinion_modifier
            "ideas": [],  # list of (token, text)
            "ideas_extra_comments": [],
            "modifiers": OrderedDict(),  # name -> {"stmt": stmt, "vars": [stmt,...]}
            "system_vars": [],
            "country_vars": [],
            "special_projects": [],
            "technologies": [],
            "power_balance": [],
            "states": [],
            "flags": [],
            "other": [],
        }

        # Pass 1 - record added modifiers (in first-seen order) and build the
        # variable -> modifier claim map restricted to those modifiers.
        modvars = self._modvars or {}
        claim: Dict[str, str] = {}
        for stmt in statements:
            if _head_token(stmt["lines"]) == "add_dynamic_modifier":
                name = _modifier_name(stmt["lines"])
                if name and name not in props["modifiers"]:
                    props["modifiers"][name] = {"stmt": stmt, "vars": []}
                    for var in modvars.get(name, ()):  # type: ignore[arg-type]
                        claim.setdefault(var, name)

        # Pass 2 - route every statement into exactly one bucket.
        for stmt in statements:
            lines = stmt["lines"]
            head = _head_token(lines)
            if not lines:
                props["other"].append(stmt)
                continue
            if head == "add_ideas":
                self._collect_ideas(stmt, props)
            elif head == "add_dynamic_modifier":
                pass  # already slotted in pass 1; vars attach below
            elif head in _VAR_TYPES:
                var = _variable_name(lines)
                if var and var in claim:
                    props["modifiers"][claim[var]]["vars"].append(stmt)
                elif var and _TAG_PREFIX_RE.match(var):
                    props["country_vars"].append(stmt)
                else:
                    props["system_vars"].append(stmt)
            elif head in ("add_to_array", "remove_from_array"):
                props["system_vars"].append(stmt)
            elif head == "complete_special_project" or head.startswith("sp:"):
                props["special_projects"].append(stmt)
            elif head == "set_technology":
                props["technologies"].append(stmt)
            elif head == "create_equipment_variant":
                props["equipment"].append((self._equipment_domain(lines), stmt))
            elif head in ("set_oob", "set_air_oob", "set_naval_oob"):
                props["equipment"].append((self._equipment_domain(lines), stmt))
            elif head in ("start_politics_input", "startup_politics", "create_country_leader"):
                props["leader_top"].append(stmt)
            elif head in ("set_popularities", "set_politics"):
                props["politics_top"].append(stmt)
            elif head in ("add_opinion_modifier", "reverse_add_opinion_modifier"):
                props["opinion"].append(stmt)
            elif head in ("if", "random", "random_list"):
                text = "\n".join(lines)
                if "create_equipment_variant" in text:
                    props["equipment"].append((self._equipment_domain(lines), stmt))
                elif "set_technology" in text or "has_dlc" in text:
                    props["technologies"].append(stmt)
                else:
                    props["other"].append(stmt)
            elif head == "set_power_balance":
                props["power_balance"].append(stmt)
            elif head.isdigit():
                props["states"].append(stmt)
            elif head in ("set_country_flag", "clr_country_flag"):
                props["flags"].append(stmt)
            else:
                props["other"].append(stmt)

        return props

    def _collect_ideas(self, stmt: Dict[str, List[str]], props: Dict[str, Any]) -> None:
        # add_ideas comments become idea-block stray comments (kept, not dropped).
        for c in stmt["comments"]:
            if not _is_boilerplate_comment(c):
                props["ideas_extra_comments"].append(c)
        for raw in stmt["lines"]:
            code = strip_inline_comment(raw)
            if raw.lstrip().startswith("#"):
                if not _is_boilerplate_comment(raw):
                    props["ideas_extra_comments"].append(raw.rstrip())
                continue
            for tok in code.replace("{", " ").replace("}", " ").split():
                if "=" in tok or tok == "add_ideas":
                    continue
                props["ideas"].append((tok, tok))

    # -- formatting --------------------------------------------------------- #

    def _emit_stmt(self, stmt: Dict[str, List[str]], out: List[str], seen: set) -> None:
        key = "\n".join(stmt["lines"]).strip()
        if key and key in seen:
            log_message("DEBUG", f"Collapsed duplicate: {key[:60]}", self.verbose)
            return
        if key:
            seen.add(key)
        out.extend(c for c in stmt["comments"] if c.strip())
        out.extend(stmt["lines"])

    def _emit_group(
        self, header: str, stmts: List[Dict[str, List[str]]], indent: str, out: List[str]
    ) -> None:
        if not stmts:
            return
        rendered: List[str] = []
        seen: set = set()
        for stmt in stmts:
            self._emit_stmt(stmt, rendered, seen)
        if not rendered:
            return
        out.append("")
        out.append(f"{indent}# {header}")
        out.extend(rendered)

    def _emit_top(self, stmts: List[Dict[str, List[str]]], out: List[str]) -> None:
        if not stmts:
            return
        out.append("")
        seen: set = set()
        for stmt in stmts:
            self._emit_stmt(stmt, out, seen)

    def _emit_equipment(self, props: Dict[str, Any], indent: str, out: List[str]) -> None:
        if not props["equipment"]:
            return
        labels = {0: "Army Equipment", 1: "Air Force Equipment", 2: "Naval Equipment"}
        for dom in (0, 1, 2):
            stmts = [s for d, s in props["equipment"] if d == dom]
            self._emit_group(labels[dom], stmts, indent, out)

    def _emit_ideas(self, props: Dict[str, Any], indent: str, out: List[str]) -> None:
        if not props["ideas"]:
            return
        inner = indent + "\t"
        out.append("")
        out.append(f"{indent}add_ideas = {{")
        out.extend(props["ideas_extra_comments"])
        groups = OrderedDict(
            [
                ("law", "Laws"),
                ("md", "MD Ideas"),
                ("faction", "Internal Factions"),
                ("country", "Country Content"),
            ]
        )
        classified: Dict[str, List[str]] = {k: [] for k in groups}
        seen: set = set()
        for token, _text in props["ideas"]:
            if token in seen:
                continue
            seen.add(token)
            classified[self._classify_idea(token)].append(token)
        for key, header in groups.items():
            items = classified[key]
            if not items:
                continue
            out.append(f"{inner}# {header}")
            out.extend(f"{inner}{token}" for token in items)
        out.append(f"{indent}}}")

    def format_block(self, props: Dict[str, Any]) -> List[str]:
        indent = props["indent"]
        out: List[str] = [props["open_line"]]

        self._emit_top(props["leader_top"], out)
        self._emit_top(props["politics_top"], out)
        self._emit_ideas(props, indent, out)

        # Dynamic modifiers, each with its associated variables beneath it.
        if props["modifiers"]:
            out.append("")
            out.append(f"{indent}# Dynamic Modifiers")
            seen: set = set()
            for name, slot in props["modifiers"].items():
                self._emit_stmt(slot["stmt"], out, seen)
                for var_stmt in slot["vars"]:
                    self._emit_stmt(var_stmt, out, seen)

        self._emit_group("System Variables", props["system_vars"], indent, out)
        self._emit_group("Special Projects", props["special_projects"], indent, out)
        self._emit_group("Technologies", props["technologies"], indent, out)
        self._emit_equipment(props, indent, out)
        self._emit_group("Country Variables", props["country_vars"], indent, out)
        self._emit_group("Power Balance", props["power_balance"], indent, out)
        self._emit_group("State Setup", props["states"], indent, out)
        self._emit_group("Country Flags", props["flags"], indent, out)
        self._emit_group("Opinion Modifiers", props["opinion"], indent, out)
        self._emit_group("Other", props["other"], indent, out)

        out.append(props["close_line"])
        return collapse_blank_runs(out)


if __name__ == "__main__":
    run_standardizer(
        HistoryStandardizer,
        "Standardize HOI4 history/countries files according to Millennium Dawn coding standards",
    )
