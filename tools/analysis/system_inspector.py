#!/usr/bin/env python3
"""Inspect one mod system: its files, definitions, hooks, dependencies and loose ends.

Built for coding agents that need a structured map of a system such as Targeted Operations
before changing it.

    python tools/analysis/system_inspector.py --list
    python tools/analysis/system_inspector.py top
    python tools/analysis/system_inspector.py top --section unresolved
    python tools/analysis/system_inspector.py --path-pattern corporate_history --prefix corporate_history_ --json

A system is the set of files whose repository path matches a regex; every other file is
outside it. The report is read-only and reads the working tree.

Sections:
  files         the system's files by kind, with line counts
  definitions   what the system defines, by kind
  hooks         outside files that reference the system's definitions
  dependencies  outside definitions the system uses, by kind
  unresolved    calls, events, localisation and globals that point at nothing
  unused        system effects, triggers and triggered-only events nothing references
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ("common", "events", "interface", "history", "localisation/english")
SCAN_SUFFIXES = (".txt", ".gui", ".gfx", ".yml")
SECTIONS = ("files", "definitions", "hooks", "dependencies", "unresolved", "unused")


@dataclass(frozen=True)
class Preset:
    path_pattern: str
    prefixes: tuple[str, ...]
    description: str


PRESETS = {
    "top": Preset(
        r"targeted_operations|Targeted Operations|military_raids|^common/raids/",
        ("TOP_",),
        "Targeted Operations and its native raids",
    ),
}

# (kind, path prefix, brace depth of the defining key). The first matching prefix wins.
DEFINITION_RULES = (
    ("scripted_effect", "common/scripted_effects/", 0),
    ("scripted_trigger", "common/scripted_triggers/", 0),
    ("decision_category", "common/decisions/categories/", 0),
    ("decision", "common/decisions/", 1),
    ("idea", "common/ideas/", 2),
    ("dynamic_modifier", "common/dynamic_modifiers/", 0),
    ("opinion_modifier", "common/opinion_modifiers/", 1),
    ("scripted_gui", "common/scripted_guis/", 1),
    ("game_rule", "common/game_rules/", 0),
    ("modifier_definition", "common/modifier_definitions/", 0),
    ("mio", "common/military_industrial_organization/organizations/", 0),
    ("character", "common/characters/", 1),
    ("focus", "common/national_focus/", 1),
    ("raid_category", "common/raids/categories/", 1),
    ("raid", "common/raids/", 1),
    ("ai_strategy", "common/ai_strategy/", 0),
    ("ai_strategy_plan", "common/ai_strategy_plans/", 0),
    ("ai_equipment", "common/ai_equipment/", 1),
    ("balance_of_power", "common/bop/", 0),
    ("technology", "common/technologies/", 1),
    ("country_leader_trait", "common/country_leader/", 1),
    ("unit_leader_trait", "common/unit_leader/", 1),
)
# Kinds whose names other files reference by bare token, so hooks and dependencies are meaningful.
LINKED_KINDS = (
    "scripted_effect",
    "scripted_trigger",
    "event",
    "decision_category",
    "decision",
    "idea",
    "dynamic_modifier",
    "opinion_modifier",
    "scripted_gui",
    "game_rule",
    "modifier_definition",
    "mio",
    "character",
    "focus",
    "scripted_loc",
    "sprite",
    "raid_category",
    "technology",
    "balance_of_power",
    "country_leader_trait",
    "unit_leader_trait",
)

STRING_OR_COMMENT_RE = re.compile(r'"(?:\\.|[^"\\])*"|#[^\n]*')
LOG_RE = re.compile(r'\blog\s*=\s*"(?:\\.|[^"\\])*"')
# [name] or a scoped [ROOT.name]; the last link is the defined text.
LOC_SUBSTITUTION_RE = re.compile(
    r"\[(?:[A-Za-z_][A-Za-z0-9_:^]*\.)*([A-Za-z_][A-Za-z0-9_]*)\]"
)
QUOTED_FIELD_RE = re.compile(r"([A-Za-z0-9_.@:\-^]+)\s*=\s*$")
# Fields whose quoted values still name definitions, references, or localisation keys.
# Lowercase: GUI keys are case-insensitive (spriteType and SpriteType both occur).
QUOTED_REFERENCE_FIELDS = {
    "add_ideas",
    "buttontext",
    "complete_national_focus",
    "custom_effect_tooltip",
    "custom_modifier_tooltip",
    "desc",
    "has_completed_focus",
    "has_idea",
    "id",
    "localisation_key",
    "localization_key",
    "pdx_tooltip",
    "pdx_tooltip_delayed",
    "quadtexturesprite",
    "remove_ideas",
    "spritetype",
    "text",
    "title",
    "tooltip",
}
FIELD_RE = re.compile(
    r"(?P<key>[A-Za-z0-9_.@:\-^]+)\s*=\s*"
    r'(?P<value>"(?:\\.|[^"\\])*"|[^\s{}=]+|\{)'
    r'|"(?:\\.|[^"\\])*"|(?P<brace>[{}])'
)
EVENT_TYPES = {
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_leader_event",
}
# Role-group fields that sit beside the templates in an AI equipment file.
AI_EQUIPMENT_FIELDS = {"roles", "priority", "available_for", "blocked_for"}
# Keys under these parents name a variable or a GUI handler, not a scripted call.
VARIABLE_EFFECT_RE = re.compile(
    r"(?:set|add_to|subtract_from|multiply|divide|modulo|clamp|round)_(?:temp_)?variable"
)
GUI_HANDLER_BLOCKS = {"effects", "triggers", "properties", "dynamic_lists"}
KEY_BLOCK_RE = re.compile(r"([A-Za-z0-9_.@:\-^]+)\s*=\s*\{|\{|\}")
# Names may start with a digit (10_percent_government_popularity) but need a letter, so numbers are not tokens.
TOKEN_RE = re.compile(r"(?=[0-9_.\-]*[A-Za-z])[A-Za-z0-9_][A-Za-z0-9_.\-]*[A-Za-z0-9_]")
# Event ids are always namespace.number, which keeps `id = TAG` in other blocks out.
EVENT_ID_RE = re.compile(r"[A-Za-z0-9_]+\.[A-Za-z0-9_.]+")
SPRITE_RE = re.compile(r'name\s*=\s*"?(GFX_[A-Za-z0-9_]+)"?')
LOC_KEY_RE = re.compile(r"^ ?([A-Za-z0-9_.\-]+):\d* ", re.M)
FIRED_EVENT_RE = re.compile(
    r"\b(?:country|news|state|unit_leader|operative_leader)_event\s*=\s*"
    r"(?:\{[^{}]*?\bid\s*=\s*([A-Za-z0-9_.]+)|([A-Za-z0-9_]+\.[A-Za-z0-9_.]+))"
)
LOC_REF_RE = re.compile(
    r"\b(?:title|desc|tooltip|custom_effect_tooltip|custom_modifier_tooltip|localization_key|localisation_key|text"
    r"|pdx_tooltip(?:_delayed)?|buttonText)"
    r"\s*=\s*\"?([A-Za-z_][A-Za-z0-9_.\-]*)\"?"
)
FLAG_SET_RE = re.compile(
    r"\bset_(country|global|state|character|project|unit_leader|mio)_flag\s*=\s*"
    r"(?:\{\s*flag\s*=\s*)?([A-Za-z0-9_]+)"
)
FLAG_READ_RE = re.compile(
    r"\bhas_(country|global|state|character|project|unit_leader|mio)_flag\s*=\s*"
    r"(?:\{\s*flag\s*=\s*)?([A-Za-z0-9_]+)"
)
GLOBAL_READ_RE = re.compile(r"\bglobal\.([A-Za-z_][A-Za-z0-9_]*)")
LOC_GLOBAL_READ_RE = re.compile(r"\[\?global\.([A-Za-z_][A-Za-z0-9_]*)")
GLOBAL_WRITE_RE = re.compile(
    r"\b(?:set|add_to|subtract_from|multiply|divide|clamp|round|modulo|randomize)_variable"
    r"(?:_to_random)?\s*=\s*\{\s*"
    r"(?:var\s*=\s*)?global\.([A-Za-z_][A-Za-z0-9_]*)"
    r"|\b(?:add_to|remove_from|resize|clear)_array\s*=\s*\{?\s*(?:array\s*=\s*)?"
    r"global\.([A-Za-z_][A-Za-z0-9_]*)"
)


@dataclass
class Tree:
    """Every scanned file's text, with comments and literal prose removed from code."""

    root: Path
    raw: dict[str, str] = field(default_factory=dict)
    code: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def strip_comments(text: str) -> str:
    return STRING_OR_COMMENT_RE.sub(
        lambda m: m.group(0) if m.group(0).startswith('"') else "", text
    )


def reference_code(text: str, rel: str = "") -> str:
    code = LOG_RE.sub('log = ""', strip_comments(text))

    def keep_identifier(match: re.Match) -> str:
        value = match.group(0)[1:-1]
        assignment = QUOTED_FIELD_RE.search(code, 0, match.start())
        field = assignment.group(1) if assignment else ""
        name_is_reference = field == "name" and (
            rel.startswith(
                ("common/scripted_localisation/", "events/", "common/game_rules/")
            )
            or rel.endswith(".gfx")
        )
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", value) and (
            field.lower() in QUOTED_REFERENCE_FIELDS
            or field.isdecimal()
            or name_is_reference
        ):
            return match.group(0)
        return '"' + " ".join(LOC_SUBSTITUTION_RE.findall(value)) + '"'

    return STRING_OR_COMMENT_RE.sub(keep_identifier, code)


def read_tree(root: Path) -> Tree:
    tree = Tree(root)
    for base in SCAN_DIRS:
        folder = root / base
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
                continue
            rel = path.relative_to(root).as_posix()
            data = path.read_bytes()
            try:
                text = data.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = data.decode("utf-8-sig", errors="replace")
                tree.warnings.append(f"{rel}: not valid UTF-8, read with replacement")
            tree.raw[rel] = text
            tree.code[rel] = text if rel.endswith(".yml") else reference_code(text, rel)
    return tree


def loc_substitutions(text: str) -> set[str]:
    """Bracketed calls in active localisation values; comments are skipped."""
    names: set[str] = set()
    for line in text.splitlines():
        if "[" in line:
            for match in STRING_OR_COMMENT_RE.finditer(line):
                if match.group(0).startswith('"'):
                    names.update(LOC_SUBSTITUTION_RE.findall(match.group(0)))
    return names


def is_identifier(name: str) -> bool:
    """Exclude reserved script words without discarding valid bare definitions."""
    return name.lower() not in {"yes", "no", "from", "for"}


def keys_at_depth(code: str, depth: int) -> list[str]:
    found, current = [], 0
    for match in KEY_BLOCK_RE.finditer(code):
        token = match.group(0)
        if token == "}":
            current -= 1
        elif token == "{":
            current += 1
        else:
            if current == depth:
                found.append(match.group(1))
            current += 1
    return found


def definitions_in(rel: str, code: str) -> dict[str, list[str]]:
    """Names the file defines, by kind."""
    found: dict[str, list[str]] = defaultdict(list)
    for kind, prefix, depth in DEFINITION_RULES:
        if rel.startswith(prefix):
            if kind == "focus":
                found[kind] += [
                    value
                    for parents, key, value in script_fields(code)
                    if key == "id"
                    and parents
                    and parents[-1][0] in {"focus", "shared_focus", "joint_focus"}
                ]
            else:
                found[kind] += [
                    name
                    for name in keys_at_depth(code, depth)
                    if kind != "ai_equipment" or name not in AI_EQUIPMENT_FIELDS
                ]
            break
    if rel.startswith("events/"):
        found["event"] += [ident for ident, _ in event_blocks(code)]
    if rel.startswith("common/scripted_localisation/"):
        found["scripted_loc"] += [
            value
            for parents, key, value in script_fields(code)
            if key == "name" and parents and parents[-1][0] == "defined_text"
        ]
    if rel.endswith(".gfx"):
        found["sprite"] += SPRITE_RE.findall(code)
    if rel.endswith(".yml"):
        found["loc"] += LOC_KEY_RE.findall(code)
    return found


def script_fields(code: str) -> Iterator[tuple[list[tuple[str, int]], str, str]]:
    parents: list[tuple[str, int]] = []
    for match in FIELD_RE.finditer(code):
        key, value = match.group("key", "value")
        if key is not None:
            yield parents, key, value.strip('"')
            if value == "{":
                parents.append((key, match.start()))
        elif match.group("brace") == "{":
            parents.append(("", match.start()))
        elif match.group("brace") == "}" and parents:
            parents.pop()


def event_blocks(code: str) -> list[tuple[str, bool]]:
    """Read direct fields of top-level events, excluding nested dispatches."""
    events: dict[int, dict[str, str]] = defaultdict(dict)
    for parents, key, value in script_fields(code):
        if len(parents) == 1 and parents[0][0] in EVENT_TYPES:
            events[parents[0][1]][key] = value
    return [
        (fields["id"], fields.get("is_triggered_only") == "yes")
        for fields in events.values()
        if EVENT_ID_RE.fullmatch(fields.get("id", ""))
    ]


def event_option_labels(code: str) -> set[str]:
    return {
        value
        for parents, key, value in script_fields(code)
        if key == "name"
        and len(parents) == 2
        and parents[0][0] in EVENT_TYPES
        and parents[1][0] == "option"
    }


def game_rule_labels(code: str) -> set[str]:
    """A rule's name and group are localisation keys; an option's name is a token."""
    return {
        value
        for parents, key, value in script_fields(code)
        if key in {"name", "group"} and len(parents) == 1
    }


def scripted_calls(rel: str, code: str) -> set[str]:
    # Top-level keys in any other common/ file define something (name lists, templates).
    definition_depth = next(
        (depth for _, prefix, depth in DEFINITION_RULES if rel.startswith(prefix)),
        0 if rel.startswith("common/") else None,
    )
    gui = rel.startswith("common/scripted_guis/")

    def is_call(parents: list[tuple[str, int]]) -> bool:
        if definition_depth is not None and len(parents) <= definition_depth:
            return False
        parent = parents[-1][0] if parents else ""
        # Raids name their custom success factors under success_factors = { success = { ... } }.
        factor = len(parents) > 1 and parents[-2][0] == "success_factors"
        return not (
            factor
            or VARIABLE_EFFECT_RE.fullmatch(parent)
            or (gui and parent in GUI_HANDLER_BLOCKS)
        )

    return {
        key
        for parents, key, value in script_fields(code)
        if value in {"yes", "no", "{"} and is_call(parents)
    }


def inspect(
    tree: Tree, path_pattern: str | re.Pattern[str], prefixes: tuple[str, ...]
) -> dict:
    pattern = (
        re.compile(path_pattern) if isinstance(path_pattern, str) else path_pattern
    )
    system = sorted(rel for rel in tree.code if pattern.search(rel))
    inside = set(system)

    defined_by: dict[str, dict[str, str]] = defaultdict(dict)
    system_defs: dict[str, set[str]] = defaultdict(set)
    # Each definition uses up one occurrence of its own name in its file, of whatever kind.
    file_defs: dict[str, Counter[str]] = defaultdict(Counter)
    for rel, code in tree.code.items():
        for kind, names in definitions_in(rel, code).items():
            for name in names:
                defined_by[kind].setdefault(name, rel)
                if rel in inside:
                    system_defs[kind].add(name)
                if kind != "loc":
                    file_defs[rel][name] += 1
    loc_calls = {
        rel: loc_substitutions(text)
        for rel, text in tree.raw.items()
        if rel.endswith(".yml")
    }

    # An outside file that never mentions a prefix stem cannot reference the system's
    # prefixed names, so it is not tokenized. With no prefix, every file is.
    stems = tuple(sorted({p.strip("_") for p in prefixes if p.strip("_")}))
    other_names = {
        name
        for kind in LINKED_KINDS
        for name in system_defs.get(kind, ())
        if is_identifier(name) and not any(stem in name for stem in stems)
    }
    tokens_by_file = {
        rel: TOKEN_RE.findall(code)
        for rel, code in tree.code.items()
        if not rel.endswith(".yml")
        and (
            rel in inside
            or not stems
            or any(stem in code for stem in stems)
            or any(name in code for name in other_names)
        )
    }
    token_sets = {rel: set(tokens) for rel, tokens in tokens_by_file.items()}

    def names_it(rel: str, name: str) -> bool:
        defined = file_defs[rel][name]
        return not defined or tokens_by_file[rel].count(name) > defined

    files = defaultdict(list)
    for rel in system:
        kind = next((k for k, p, _ in DEFINITION_RULES if rel.startswith(p)), None)
        kind = kind or rel.split("/")[0]
        files[kind].append({"path": rel, "lines": len(tree.raw[rel].splitlines())})

    linked_system = {
        name: kind
        for kind in LINKED_KINDS
        for name in system_defs.get(kind, ())
        if is_identifier(name)
    }
    hooks = {}
    for rel in sorted(token_sets.keys() | loc_calls.keys()):
        if rel in inside:
            continue
        if rel.endswith(".yml"):
            used = sorted(loc_calls[rel] & system_defs.get("scripted_loc", set()))
        else:
            used = sorted(
                name
                for name in token_sets[rel] & linked_system.keys()
                if names_it(rel, name)
            )
        if used:
            hooks[rel] = used

    script_files = [rel for rel in system if not rel.endswith(".yml")]
    system_refs: Counter[str] = Counter()
    for rel in script_files:
        system_refs.update(tokens_by_file[rel])
        system_refs.subtract(file_defs[rel])
    system_tokens = {name for name, count in system_refs.items() if count > 0}
    system_loc_calls = set().union(
        *(loc_calls[rel] for rel in system if rel.endswith(".yml"))
    )
    calls_by_file = {rel: scripted_calls(rel, tree.code[rel]) for rel in script_files}
    system_calls = set().union(*calls_by_file.values())
    dependencies: dict[str, list[dict[str, str]]] = {}
    for kind in LINKED_KINDS:
        outside_names = {
            name: rel
            for name, rel in defined_by[kind].items()
            if rel not in inside and is_identifier(name)
        }
        if kind in {"scripted_effect", "scripted_trigger"}:
            references = system_calls
        elif kind == "scripted_loc":
            references = system_tokens | system_loc_calls
        else:
            references = system_tokens
        used = sorted(references & outside_names.keys() - system_defs.get(kind, set()))
        if used:
            dependencies[kind] = [
                {"name": n, "defined_in": outside_names[n]} for n in used
            ]

    all_effects = set(defined_by["scripted_effect"]) | set(
        defined_by["scripted_trigger"]
    )
    all_events = set(defined_by["event"])
    loc_keys = set(defined_by["loc"])
    scripted_locs = set(defined_by["scripted_loc"])
    flags_set = set()
    globals_written = set()
    for rel, code in tree.code.items():
        if rel.endswith(".yml"):
            continue
        if "_flag" in code:
            flags_set.update(FLAG_SET_RE.findall(code))
        if "global." in code:
            for written in GLOBAL_WRITE_RE.findall(code):
                globals_written.update(name for name in written if name)

    calls, fired, loc_refs, flags_read, globals_read = (set() for _ in range(5))
    for rel in system:
        if rel.endswith(".yml"):
            for match in STRING_OR_COMMENT_RE.finditer(tree.raw[rel]):
                if match.group(0).startswith('"'):
                    globals_read.update(LOC_GLOBAL_READ_RE.findall(match.group(0)))
            continue
        code = tree.code[rel]
        calls.update(calls_by_file[rel])
        for by_id, bare in FIRED_EVENT_RE.findall(code):
            fired.add(by_id or bare)
        fired.update(
            value
            for parents, key, value in script_fields(code)
            if parents
            and parents[-1][0] == "random_events"
            and key.isdecimal()
            and EVENT_ID_RE.fullmatch(value)
        )
        if rel.startswith(("common/", "events/")) or (
            rel.startswith("interface/") and rel.endswith(".gui")
        ):
            loc_refs.update(LOC_REF_RE.findall(code))
        if rel.startswith("events/"):
            loc_refs.update(event_option_labels(code))
        if rel.startswith("common/game_rules/"):
            loc_refs.update(game_rule_labels(code))
        flags_read.update(FLAG_READ_RE.findall(code))
        globals_read.update(GLOBAL_READ_RE.findall(code))

    unresolved = {
        "calls": sorted(
            c for c in calls if c.startswith(prefixes) and c not in all_effects
        ),
        "events": sorted(e for e in fired if e not in all_events),
        "localisation": sorted(
            key
            # Bracketed engine calls such as GetName never carry a system prefix.
            for key in loc_refs | system_loc_calls
            if "." in key or key.startswith(prefixes)
            if key not in loc_keys and key not in scripted_locs
        ),
        "flags_never_set": sorted(
            f"{kind}:{name}"
            for kind, name in flags_read
            if name.startswith(prefixes) and (kind, name) not in flags_set
        ),
        "globals_never_written": sorted(
            g
            for g in globals_read
            if g.startswith(prefixes) and g not in globals_written
        ),
    }
    if not prefixes:
        unresolved["note"] = (
            "No prefix given: calls, flags and globals are only checked against a prefix."
        )

    # A definition is used when a file names it more often than that file defines it.
    candidates = {
        name: defined_by[kind][name]
        for kind in ("scripted_effect", "scripted_trigger")
        for name in system_defs.get(kind, ())
    }
    events_only = {}
    for rel in system:
        if rel.startswith("events/"):
            for ident, only in event_blocks(tree.code[rel]):
                if only:
                    events_only[ident] = rel
    candidates.update(events_only)
    referenced = set()
    for rel, names in token_sets.items():
        for name in names & candidates.keys():
            if names_it(rel, name):
                referenced.add(name)
    if stems:
        skipped = [
            code
            for rel, code in tree.code.items()
            if rel not in token_sets and not rel.endswith(".yml")
        ]
        for name in candidates.keys() - referenced:
            if not any(stem in name for stem in stems) and any(
                name in code for code in skipped
            ):
                referenced.add(name)
    unused = {
        "scripted_effects_and_triggers": sorted(
            name for name in candidates.keys() - referenced if name not in events_only
        ),
        "triggered_only_events": sorted(events_only.keys() - referenced),
    }

    return {
        "path_pattern": pattern.pattern,
        "prefixes": list(prefixes),
        "warnings": tree.warnings,
        "files": dict(files),
        "definitions": {
            kind: sorted(names) for kind, names in sorted(system_defs.items())
        },
        "hooks": hooks,
        "dependencies": dependencies,
        "unresolved": unresolved,
        "unused": unused,
    }


def render(report: dict, sections: tuple[str, ...], limit: int) -> str:
    def clip(items: list) -> str:
        shown = ", ".join(str(i) for i in items[:limit])
        extra = len(items) - limit
        return shown + (f", ... {extra} more" if extra > 0 else "")

    out = [
        f"System: {report['path_pattern']}  prefixes: {', '.join(report['prefixes']) or 'none'}"
    ]
    out += [f"warning: {w}" for w in report["warnings"]]
    if "files" in sections:
        total = sum(len(v) for v in report["files"].values())
        out.append(f"\n== files ({total})")
        for kind, entries in sorted(report["files"].items()):
            lines = sum(e["lines"] for e in entries)
            out.append(f"  {kind}: {len(entries)} files, {lines} lines")
            out += [f"    {e['path']} ({e['lines']})" for e in entries[:limit]]
    if "definitions" in sections:
        out.append("\n== definitions")
        for kind, names in report["definitions"].items():
            out.append(f"  {kind} ({len(names)}): {clip(names)}")
    if "hooks" in sections:
        out.append(f"\n== hooks ({len(report['hooks'])} outside files)")
        for rel, names in report["hooks"].items():
            out.append(f"  {rel}: {clip(names)}")
    if "dependencies" in sections:
        out.append("\n== dependencies")
        for kind, entries in report["dependencies"].items():
            out.append(
                f"  {kind} ({len(entries)}): {clip([e['name'] for e in entries])}"
            )
    if "unresolved" in sections:
        out.append("\n== unresolved")
        for key, items in report["unresolved"].items():
            out.append(
                f"  {key}: {items}"
                if key == "note"
                else f"  {key} ({len(items)}): {clip(items) or 'none'}"
            )
    if "unused" in sections:
        out.append("\n== unused")
        for key, items in report["unused"].items():
            out.append(f"  {key} ({len(items)}): {clip(items) or 'none'}")
    return "\n".join(out)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "preset", nargs="?", choices=sorted(PRESETS), help="a known system"
    )
    parser.add_argument("--list", action="store_true", help="list the presets and exit")
    parser.add_argument(
        "--path-pattern", help="regex over repository paths (instead of a preset)"
    )
    parser.add_argument(
        "--prefix", action="append", default=[], help="identifier prefix; repeatable"
    )
    parser.add_argument(
        "--section",
        action="append",
        choices=SECTIONS,
        help="limit the report; repeatable",
    )
    parser.add_argument(
        "--limit", type=int, default=25, help="items shown per list in text output"
    )
    parser.add_argument(
        "--json", action="store_true", help="print the full report as JSON"
    )
    parser.add_argument(
        "--root", type=Path, default=REPO_ROOT, help="mod root (default: this repo)"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        for name, preset in sorted(PRESETS.items()):
            print(
                f"{name:12} {preset.description}  paths /{preset.path_pattern}/  prefixes {', '.join(preset.prefixes)}"
            )
        return 0
    if args.preset:
        preset = PRESETS[args.preset]
        path_pattern = args.path_pattern or preset.path_pattern
        prefixes = tuple(args.prefix) or preset.prefixes
    elif args.path_pattern:
        path_pattern, prefixes = args.path_pattern, tuple(args.prefix)
    else:
        print("Give a preset (see --list) or --path-pattern.", file=sys.stderr)
        return 2
    try:
        pattern = re.compile(path_pattern)
    except re.error as error:
        print(f"Invalid --path-pattern {path_pattern!r}: {error}", file=sys.stderr)
        return 2
    report = inspect(read_tree(args.root), pattern, prefixes)
    if not any(report["files"].values()):
        print(f"No files under {args.root} match /{path_pattern}/.", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render(report, tuple(args.section or SECTIONS), args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
