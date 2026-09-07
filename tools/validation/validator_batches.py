"""Shared validator selection for CI batches and impact scans."""

import ast
import os
import re
from collections import deque
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

VALIDATION_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(VALIDATION_DIR)


@dataclass(frozen=True)
class ValidatorSpec:
    """One validator's script, gate strictness, and change groups."""

    name: str
    script: str
    groups: Tuple[str, ...]
    strict: bool = True
    args: Tuple[str, ...] = ()
    runner: str = "standard"


_CORE_GROUPS = (
    "common",
    "events",
    "history",
    "localisation",
    "interface",
    "map-adjacency",
)

BATCHES: Dict[str, Tuple[ValidatorSpec, ...]] = {
    "core": (
        ValidatorSpec("common-mistakes", "validate_common_mistakes.py", _CORE_GROUPS),
        ValidatorSpec("variables", "validate_variables.py", _CORE_GROUPS),
        ValidatorSpec(
            "scripted-localisation", "validate_scripted_localisation.py", _CORE_GROUPS
        ),
        ValidatorSpec("cosmetic-tags", "validate_cosmetic_tags.py", _CORE_GROUPS),
        ValidatorSpec("localisation", "validate_localisation.py", _CORE_GROUPS),
        ValidatorSpec("events", "validate_events.py", _CORE_GROUPS),
        ValidatorSpec("history-files", "validate_history.py", _CORE_GROUPS),
        ValidatorSpec("unused-scripted", "validate_unused_scripted.py", _CORE_GROUPS),
        ValidatorSpec("agency-upgrades", "validate_agency_upgrades.py", _CORE_GROUPS),
        ValidatorSpec("ideas", "validate_ideas.py", _CORE_GROUPS),
        ValidatorSpec("set-variables", "validate_set_variables.py", _CORE_GROUPS),
        # Cross-references the committed vanilla_defines.txt manifest.
        ValidatorSpec("defines", "validate_defines.py", _CORE_GROUPS),
    ),
    "targeted-a": (
        ValidatorSpec(
            "decisions", "validate_decisions.py", ("decisions", "localisation")
        ),
        ValidatorSpec("oob-units", "validate_oob_units.py", ("oob",)),
        ValidatorSpec("equipment-upkeep", "validate_equipment_upkeep.py", ("oob",)),
        ValidatorSpec("ai-roles", "validate_ai_roles.py", ("ai-strategy",)),
        ValidatorSpec("ai-navy", "validate_ai_navy.py", ("ai-navy",)),
        ValidatorSpec("ai-equipment", "validate_ai_equipment.py", ("ai-equipment",)),
        ValidatorSpec("factions", "validate_factions.py", ("factions",)),
        ValidatorSpec("characters", "validate_characters.py", ("characters",)),
        ValidatorSpec(
            "scientist-traits", "validate_scientist_traits.py", ("scientist-traits",)
        ),
        ValidatorSpec("mios", "validate_mios.py", ("mios", "localisation")),
        ValidatorSpec(
            "scripted-gui", "validate_scripted_gui.py", ("scripted-guis", "interface")
        ),
    ),
    "targeted-b": (
        ValidatorSpec("focus-tree", "validate_focus_tree.py", ("national-focus",)),
        ValidatorSpec("on-actions", "validate_on_actions.py", ("on-actions", "events")),
        ValidatorSpec(
            "scripted-params",
            "validate_scripted_params.py",
            ("common", "events", "history"),
        ),
        ValidatorSpec(
            "gfx-references",
            "validate_gfx_references.py",
            ("interface", "common", "events", "history", "localisation"),
        ),
        ValidatorSpec("bonus-names", "validate_bonus_names.py", ("common", "events")),
        ValidatorSpec(
            "tech-categories", "validate_tech_categories.py", ("common", "events")
        ),
        ValidatorSpec("modifiers", "validate_modifiers.py", ("common",)),
        ValidatorSpec(
            "simplifications",
            "validate_simplifications.py",
            ("scripted-effects", "national-focus", "decisions", "on-actions", "events"),
            strict=False,
        ),
        ValidatorSpec(
            "building-guards",
            "validate_building_guards.py",
            ("common", "events"),
            strict=False,
        ),
        ValidatorSpec("dlc-guards", "validate_dlc_guards.py", ("common", "events")),
        ValidatorSpec("technologies", "validate_technologies.py", ("common",)),
    ),
}

ALL_SPECS: Tuple[ValidatorSpec, ...] = tuple(
    spec for batch in BATCHES.values() for spec in batch
)

# These run outside the three full-repo batches in the coding pipeline.
IMPACT_ONLY_SPECS: Tuple[ValidatorSpec, ...] = (
    ValidatorSpec("file-paths", "validate_file_paths.py", (), True),
    ValidatorSpec("style", "validate_style.py", (), True),
    ValidatorSpec("mod-descriptors", "validate_mod_descriptors.py", (), True),
    ValidatorSpec(
        "localization-encoding",
        "validate_localization_encoding.py",
        (),
        True,
        runner="standalone",
    ),
    ValidatorSpec(
        "mod-encoding", "validate_mod_encoding.py", (), True, runner="standalone"
    ),
)

_IMPACT_ONLY_BY_SCRIPT = {spec.script: spec for spec in IMPACT_ONLY_SPECS}
_IMPACT_EXCLUDED_SCRIPTS = {
    "validate_unused_textures.py",
    "validate_tools.py",
    "validate_staged.py",
}
_REFERENCE_FILES = {
    ".claude/docs/typo-watchlist.md": ("localisation",),
    "resources/documentation/modifiers_documentation.md": ("modifiers",),
}

_SCRIPT_PATH_RE = re.compile(r"^tools/validation/(validate_[\w-]+\.py)$")


def _adhoc_spec(script: str) -> ValidatorSpec:
    name = script.removeprefix("validate_").removesuffix(".py").replace("_", "-")
    return ValidatorSpec(name=name, script=script, groups=())


def _supports_standard_cli(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
    except (OSError, SyntaxError, ValueError):
        return False
    return any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "run_validator_main")
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "run_validator_main"
            )
        )
        for node in ast.walk(tree)
    )


def _tool_nodes() -> Dict[str, str]:
    """Module node (repo path under tools/, no .py) -> absolute source path."""
    nodes: Dict[str, str] = {}
    for rel_dir in ("", "validation", "linting"):
        directory = os.path.join(TOOLS_DIR, rel_dir) if rel_dir else TOOLS_DIR
        try:
            entries = sorted(os.listdir(directory))
        except OSError:
            continue
        for filename in entries:
            if filename.endswith(".py"):
                node = f"{rel_dir}/{filename}"[:-3].lstrip("/")
                nodes[node] = os.path.join(directory, filename)
    return nodes


def _node_aliases(node: str) -> Set[str]:
    """Dotted names a module can be imported by (flat and package-qualified)."""
    parts = node.split("/")
    stem = parts[-1]
    return {stem, ".".join(parts)}


def _import_names(tree: ast.AST) -> Set[str]:
    names: Set[str] = set()
    for item in ast.walk(tree):
        if isinstance(item, ast.Import):
            names.update(alias.name for alias in item.names)
        elif isinstance(item, ast.ImportFrom):
            if item.module:
                names.add(item.module)
            # Relative imports ("from . import x", "from .x import y").
            if item.level:
                names.update(alias.name for alias in item.names)
                if item.module:
                    names.add(item.module.rsplit(".", 1)[-1])
    return names


def _build_import_graph(nodes: Optional[Dict[str, str]] = None) -> Dict[str, Set[str]]:
    """Parse the validation/linting tooling into an importer graph.

    AST-based on purpose: the old regex missed comma imports
    (`import a, b`) and relative imports, and a missed edge is a validator
    that silently stops being selected."""
    nodes = _tool_nodes() if nodes is None else nodes
    by_alias: Dict[str, str] = {}
    for node in nodes:
        for alias in _node_aliases(node):
            by_alias[alias] = node

    graph: Dict[str, Set[str]] = {node: set() for node in nodes}
    for node, path in nodes.items():
        try:
            with open(path, "r", encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
        except (OSError, SyntaxError, ValueError):
            graph[node] = set()  # Conservative: treat as importing nothing.
            continue
        for name in _import_names(tree):
            target = by_alias.get(name)
            if target is not None and target != node:
                graph[node].add(target)
    return graph


def _transitive_importers(graph: Dict[str, Set[str]], node: str) -> Set[str]:
    reverse: Dict[str, Set[str]] = {n: set() for n in graph}
    for importer, imported in graph.items():
        for target in imported:
            reverse[target].add(importer)
    reached: Set[str] = set()
    queue = deque([node])
    while queue:
        current = queue.popleft()
        for importer in reverse.get(current, ()):
            if importer not in reached:
                reached.add(importer)
                queue.append(importer)
    return reached


_SPEC_BY_NODE = {f"validation/{spec.script}"[:-3]: spec for spec in ALL_SPECS}


def _validators_importing(node: str, graph: Dict[str, Set[str]]) -> Set[str]:
    return {
        spec.name
        for importer in _transitive_importers(graph, node)
        if (spec := _SPEC_BY_NODE.get(importer)) is not None
    }


def select_for_changed_files(
    changed_files: Iterable[str],
) -> Tuple[List[ValidatorSpec], List[ValidatorSpec]]:
    """Select ordinary batches, impact-only checks, and safe ad-hoc validators."""

    graph = _build_import_graph()
    selected: Set[str] = set()
    selected_impact: Set[str] = set()
    adhoc: List[ValidatorSpec] = []
    seen_adhoc: Set[str] = set()

    def add(name: str) -> None:
        selected.add(name)

    def add_all() -> None:
        selected.update(spec.name for spec in ALL_SPECS)

    def add_impact(name: str) -> None:
        selected_impact.add(name)

    def add_all_impact() -> None:
        selected_impact.update(spec.name for spec in IMPACT_ONLY_SPECS)

    for raw_path in changed_files:
        path = raw_path.replace("\\", "/")
        script = path.rsplit("/", 1)[-1]
        if path.startswith("tools/validation/") and script in _IMPACT_ONLY_BY_SCRIPT:
            if os.path.isfile(os.path.join(VALIDATION_DIR, script)):
                add_impact(_IMPACT_ONLY_BY_SCRIPT[script].name)
            continue
        if path.startswith("tools/linting/") and script in _IMPACT_ONLY_BY_SCRIPT:
            source = os.path.join(TOOLS_DIR, "linting", script)
            if os.path.isfile(source):
                add_impact(_IMPACT_ONLY_BY_SCRIPT[script].name)
            continue
        if path.startswith("tools/validation/") and script in _IMPACT_EXCLUDED_SCRIPTS:
            continue

        match = _SCRIPT_PATH_RE.match(path)
        if match:
            script = match.group(1)
            node = f"validation/{script}"[:-3]
            spec = _SPEC_BY_NODE.get(node)
            if spec is not None:
                add(spec.name)
                for name in _validators_importing(node, graph):
                    add(name)
            elif os.path.isfile(os.path.join(VALIDATION_DIR, script)):
                source = os.path.join(VALIDATION_DIR, script)
                if script not in seen_adhoc and _supports_standard_cli(source):
                    seen_adhoc.add(script)
                    adhoc.append(_adhoc_spec(script))
            continue

        if path in _REFERENCE_FILES:
            for name in _REFERENCE_FILES[path]:
                add(name)
            continue

        node = (
            path[len("tools/") : -3]
            if path.startswith("tools/") and path.endswith(".py")
            else ""
        )
        if node and node in graph:
            importers = _validators_importing(node, graph)
            for name in importers:
                add(name)
            if node in {"shared_utils", "validation/validator_common"}:
                add_impact("file-paths")
                add_impact("style")
                add_impact("mod-descriptors")
                if node == "shared_utils":
                    add_impact("localization-encoding")
            if importers:
                continue
            if node.startswith("validation/") or node == "shared_utils":
                add_all()
                add_all_impact()
            continue

        if (
            path.startswith("tools/validation/")
            or path == "tools/shared_utils.py"
            or path.startswith("tools/report_lib/")
        ):
            add_all()
            if path.startswith("tools/validation/") or path == "tools/shared_utils.py":
                add_all_impact()

    chosen = [spec for spec in ALL_SPECS if spec.name in selected]
    chosen += [spec for spec in IMPACT_ONLY_SPECS if spec.name in selected_impact]
    existing = [
        spec
        for spec in chosen
        if spec.runner != "standalone"
        and os.path.isfile(os.path.join(VALIDATION_DIR, spec.script))
    ]
    existing += [
        spec
        for spec in chosen
        if spec.runner == "standalone"
        and os.path.isfile(os.path.join(TOOLS_DIR, "linting", spec.script))
    ]
    existing_names = {spec.name for spec in existing}
    dropped = sorted({spec.name for spec in chosen} - existing_names)
    if dropped:
        print(
            "Skipping validators whose script no longer exists: " + ", ".join(dropped),
            flush=True,
        )
    return existing, adhoc
