#!/usr/bin/env python3
"""Generate HOI4 MIO traits from a Mermaid flowchart in markdown.

Usage:
    python tools/generators/mio_mermaid_to_traits.py \
        <source_mio_markdown> <mermaid_start_line> \
        <destination_mio_file> <destination_insert_line>
"""

import argparse
import os
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "types"))

from equipment import Equipment
from mio import EquipmentGroup
from shared.paths import REPO_ROOT
from shared_utils import atomic_write_text, read_text_strict

MUTUAL_EXCLUSIVE_LABEL = "mutually exclusive"
ROOT_START_X = 2
ROOT_START_Y = 0
ROOT_X_STEP = 3
DEFAULT_ICON = "GFX_generic_mio_trait_icon_design"
MIO_FILE_RE = re.compile(r"MD_([A-Z0-9]{3})_organizations\.txt$")
NODE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s*\["(.*)"\]\s*$')
EDGE_RE = re.compile(
    r"^\s*([A-Za-z0-9_]+)\s*(-->|-.->|-.-)\s*(?:\|([^|]+)\|)?\s*([A-Za-z0-9_]+)\s*$"
)
LOC_KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+):\d*\s", re.M)
BONUS_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*([+-])\s*([0-9]+(?:\.[0-9]+)?)%?\s*$")

ORGANIZATION_BONUS_ALIASES = {
    "mio_research": "military_industrial_organization_research_bonus",
    "research": "military_industrial_organization_research_bonus",
    "research_speed": "military_industrial_organization_research_bonus",
    "mio_funds_gain": "military_industrial_organization_funds_gain",
    "design_team_assign_cost": "military_industrial_organization_design_team_assign_cost",
    "design_team_change_cost": "military_industrial_organization_design_team_change_cost",
    "industrial_manufacturer_assign_cost": "military_industrial_organization_industrial_manufacturer_assign_cost",
    "mio_size_up_requirement": "military_industrial_organization_size_up_requirement",
    "mio_task_capacity": "military_industrial_organization_task_capacity",
}

PRODUCTION_BONUS_ALIASES = {
    "production_capacity": "production_capacity_factor",
    "production_output": "production_capacity_factor",
    "production_cost": "production_cost_factor",
    "production_efficiency_cap": "production_efficiency_cap_factor",
    "production_efficiency_gain": "production_efficiency_gain_factor",
    "production_conversion_speed": "production_conversion_speed_factor",
    "production_resource_need": "production_resource_need_factor",
    "production_resource_penalty": "production_resource_penalty_factor",
}

EQUIPMENT_BONUS_ALIASES = {
    "build_cost": "build_cost_ic",
    "max_speed": "maximum_speed",
    "air_defense": "air_defence",
    "anti_air": "anti_air_attack",
    "naval_strike_targeting": "naval_strike_targetting",
}

TARGET_ALIASES = {
    "screen_ships": ["corvette", "stealth_corvette", "mio_cat_frigates"],
}


class ToolError(Exception):
    pass


@dataclass
class TraitSpec:
    """Intermediate trait model used before rendering HOI4 script.

    Attributes:
        node_id: Mermaid node identifier.
        title: Human-readable trait title.
        token: Generated HOI4 token for the trait.
        scoped_targets: Equipment types/categories limited by this trait.
        equipment_bonus: Parsed equipment bonus modifiers.
        production_bonus: Parsed production bonus modifiers.
        organization_modifier: Parsed organization modifier bonuses.
        parents: Parent trait tokens (resolved later).
        children: Child Mermaid node identifiers.
        all_parents: Whether this trait requires all listed parents.
        relative_to: Token of parent trait used for relative positioning.
        x: Horizontal position or offset.
        y: Vertical position or offset.
    """

    node_id: str
    title: str
    token: str
    scoped_targets: list[str] = field(default_factory=list)
    equipment_bonus: dict[str, float] = field(default_factory=dict)
    production_bonus: dict[str, float] = field(default_factory=dict)
    organization_modifier: dict[str, float] = field(default_factory=dict)
    parents: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)
    all_parents: bool = True
    relative_to: Optional[str] = None
    x: int = 0
    y: int = 0


def normalize_token(text: str) -> str:
    """Normalize display text into a token-safe identifier.

    Args:
        text: Source text to normalize.

    Returns:
        A lowercase underscore-separated token.
    """

    token = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return token or "trait"


def parse_mermaid_block(source_path: Path, start_line: int) -> list[str]:
    """Extract the Mermaid code block starting at or after a source line.

    Args:
        source_path: Markdown file path containing the diagram.
        start_line: 1-based line where search for ```mermaid begins.

    Returns:
        The lines inside the Mermaid fence.
    """

    lines = read_text_strict(str(source_path), encoding="utf-8").splitlines()
    if start_line < 1 or start_line > len(lines):
        raise ToolError(f"start line {start_line} is outside source file bounds")

    start_index = start_line - 1
    fence_start = None
    for index in range(start_index, len(lines)):
        if lines[index].strip().lower() == "```mermaid":
            fence_start = index + 1
            break
    if fence_start is None:
        raise ToolError("could not find ```mermaid after the given start line")

    for index in range(fence_start, len(lines)):
        if lines[index].strip() == "```":
            return lines[fence_start:index]
    raise ToolError("unterminated mermaid code block")


def parse_nodes_and_edges(
    mermaid_lines: list[str],
) -> tuple[dict[str, str], list[str], list[tuple[str, str]], set[frozenset[str]]]:
    """Parse Mermaid nodes and edges into structured graph data.

    Args:
        mermaid_lines: Mermaid block lines without code fences.

    Returns:
        Tuple of:
            - node id -> node content map
            - node declaration order
            - directed trait edges (source, target)
            - undirected mutually exclusive node pairs
    """

    nodes: dict[str, str] = {}
    declaration_order: list[str] = []
    edges: list[tuple[str, str]] = []
    mutual_exclusive_pairs: set[frozenset[str]] = set()

    for raw_line in mermaid_lines:
        line = raw_line.strip()
        if not line or line.startswith("%%") or line.startswith("flowchart"):
            continue

        node_match = NODE_RE.match(line)
        if node_match:
            node_id, content = node_match.groups()
            nodes[node_id] = content
            declaration_order.append(node_id)
            continue

        edge_match = EDGE_RE.match(line)
        if edge_match:
            source, operator, label, target = edge_match.groups()
            if operator == "-.-" or (
                label and label.strip().lower() == MUTUAL_EXCLUSIVE_LABEL
            ):
                mutual_exclusive_pairs.add(frozenset((source, target)))
                continue
            edges.append((source, target))
    if not nodes:
        raise ToolError("no Mermaid node declarations were found")
    return nodes, declaration_order, edges, mutual_exclusive_pairs


def classify_bonus_key(raw_key: str) -> tuple[str, str]:
    """Classify a raw bonus key into output section and normalized key.

    Args:
        raw_key: Bonus key text from Mermaid.

    Returns:
        Tuple of (section_name, normalized_key).
    """

    normalized = raw_key.strip()
    organization_key = ORGANIZATION_BONUS_ALIASES.get(normalized, normalized)
    if organization_key in ORGANIZATION_BONUS_ALIASES.values():
        return "organization_modifier", organization_key

    production_key = PRODUCTION_BONUS_ALIASES.get(normalized, normalized)
    if production_key in PRODUCTION_BONUS_ALIASES.values():
        return "production_bonus", production_key

    return "equipment_bonus", EQUIPMENT_BONUS_ALIASES.get(normalized, normalized)


def parse_bonus_value(
    raw_key: str, raw_sign: str, raw_number: str
) -> tuple[str, str, float]:
    """Parse one signed percent bonus into section/key/decimal value.

    Args:
        raw_key: Bonus key text.
        raw_sign: Sign token ('+' or '-').
        raw_number: Numeric percentage text.

    Returns:
        Tuple of (section_name, normalized_key, decimal_value).
    """

    section, key = classify_bonus_key(raw_key)
    number = float(raw_number) / 100.0
    if raw_sign == "-":
        number = -number
    return section, key, number


def merge_bonus(target: dict[str, float], key: str, value: float) -> None:
    """Accumulate a bonus value into a destination map.

    Args:
        target: Destination bonus map.
        key: Bonus key to update.
        value: Decimal value to add.
    """

    target[key] = target.get(key, 0.0) + value


def parse_targets(raw_targets: str, known_tokens: set[str]) -> list[str]:
    """Parse and expand scoped equipment targets from Mermaid text.

    Args:
        raw_targets: Comma-separated target list before ':' in a bonus clause.
        known_tokens: Known equipment and equipment-group tokens.

    Returns:
        Ordered, deduplicated target tokens after alias expansion.
    """

    parsed: list[str] = []
    for token in [item.strip() for item in raw_targets.split(",") if item.strip()]:
        for expanded in TARGET_ALIASES.get(token, [token]):
            parsed.append(expanded)
            if expanded == "corvette" and "stealth_corvette" in known_tokens:
                parsed.append("stealth_corvette")
            elif expanded == "stealth_corvette" and "corvette" in known_tokens:
                parsed.append("corvette")
            elif expanded == "destroyer" and "stealth_destroyer" in known_tokens:
                parsed.append("stealth_destroyer")
            elif expanded == "stealth_destroyer" and "destroyer" in known_tokens:
                parsed.append("destroyer")

    deduped: list[str] = []
    seen: set[str] = set()
    for token in parsed:
        if token in seen:
            continue
        deduped.append(token)
        seen.add(token)
    return deduped


def parse_trait_content(
    content: str, known_tokens: set[str]
) -> tuple[str, list[str], dict[str, float], dict[str, float], dict[str, float]]:
    """Parse one Mermaid trait payload into normalized trait components.

    Args:
        content: Node content string containing title and bonus clauses.
        known_tokens: Known equipment and equipment-group tokens.

    Returns:
        Tuple of:
            - trait title
            - scoped target tokens
            - equipment bonus map
            - production bonus map
            - organization modifier map
    """

    if "<br/>" not in content:
        raise ToolError(
            f"trait node '{content}' is missing '<br/>' bonus specification separator"
        )
    title, details = content.split("<br/>", 1)
    title = title.strip()
    detail_parts = [part.strip() for part in details.split(";") if part.strip()]
    if not detail_parts:
        raise ToolError(f"trait node '{title}' has no bonus details")

    scoped_targets: list[str] = []
    current_targets: list[str] = []
    equipment_bonus: dict[str, float] = {}
    production_bonus: dict[str, float] = {}
    organization_modifier: dict[str, float] = {}

    for part in detail_parts:
        expression = part
        if ":" in part:
            target_str, expression = part.split(":", 1)
            current_targets = parse_targets(target_str.strip(), known_tokens)
            for token in current_targets:
                if token not in scoped_targets:
                    scoped_targets.append(token)
            expression = expression.strip()
        match = BONUS_RE.match(expression)
        if not match:
            raise ToolError(
                f"could not parse bonus expression '{expression}' in '{title}'"
            )
        key, sign, number = match.groups()
        section, normalized_key, value = parse_bonus_value(key, sign, number)
        if section == "equipment_bonus":
            merge_bonus(equipment_bonus, normalized_key, value)
        elif section == "production_bonus":
            merge_bonus(production_bonus, normalized_key, value)
        else:
            merge_bonus(organization_modifier, normalized_key, value)

    return title, scoped_targets, equipment_bonus, production_bonus, organization_modifier


def build_trait_specs(
    nodes: dict[str, str],
    declaration_order: list[str],
    edges: list[tuple[str, str]],
    mutual_exclusive_pairs: set[frozenset[str]],
    mio_token: str,
    known_tokens: set[str],
) -> tuple[list[TraitSpec], list[tuple[str, str, str]]]:
    """Build trait specs, relationships, and header mappings from parsed graph.

    Args:
        nodes: Mermaid node id -> node content map.
        declaration_order: Node ids in source declaration order.
        edges: Directed graph edges.
        mutual_exclusive_pairs: Node pairs connected by mutually exclusive links.
        mio_token: Destination MIO token prefix.
        known_tokens: Known equipment and equipment-group tokens.

    Returns:
        Tuple of:
            - ordered trait specifications
            - mapped headers as (header_key, root_node_id, header_text)
    """

    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        outgoing[source].append(target)
        incoming[target].append(source)

    headers: list[tuple[str, str]] = []
    trait_node_ids: list[str] = []
    for node_id in declaration_order:
        content = nodes[node_id]
        if "<br/>" in content:
            trait_node_ids.append(node_id)
        else:
            headers.append((node_id, content.strip()))

    traits_by_id: dict[str, TraitSpec] = {}
    for node_id in trait_node_ids:
        title, scoped_targets, equipment_bonus, production_bonus, organization_modifier = (
            parse_trait_content(nodes[node_id], known_tokens)
        )
        token = f"{mio_token}_{normalize_token(title)}"
        traits_by_id[node_id] = TraitSpec(
            node_id=node_id,
            title=title,
            token=token,
            scoped_targets=scoped_targets,
            equipment_bonus=equipment_bonus,
            production_bonus=production_bonus,
            organization_modifier=organization_modifier,
            parents=list(incoming.get(node_id, [])),
            children=list(outgoing.get(node_id, [])),
        )

    if not traits_by_id:
        raise ToolError("no trait nodes were found in the Mermaid block")

    roots = [node_id for node_id in trait_node_ids if not incoming.get(node_id)]
    if not roots:
        raise ToolError("the Mermaid graph has no head nodes")

    roots.sort(key=trait_node_ids.index)
    for index, root_id in enumerate(roots):
        root_trait = traits_by_id[root_id]
        root_trait.x = ROOT_START_X + (index * ROOT_X_STEP)
        root_trait.y = ROOT_START_Y
        root_trait.relative_to = None

    depth = compute_depths(roots, outgoing)
    for parent_id in trait_node_ids:
        child_ids = [
            child for child in outgoing.get(parent_id, []) if child in traits_by_id
        ]
        if not child_ids:
            continue
        offsets = sibling_offsets(len(child_ids))
        for index, child_id in enumerate(child_ids):
            child_trait = traits_by_id[child_id]
            if child_trait.relative_to is None and child_id not in roots:
                child_trait.relative_to = traits_by_id[parent_id].token
                child_trait.x = offsets[index]
                child_trait.y = 1

    token_by_node_id = {
        node_id: traits_by_id[node_id].token for node_id in trait_node_ids
    }  # Node-id to generated token for parent relationships.
    exclusive_token_pairs = {
        frozenset((token_by_node_id[left], token_by_node_id[right]))
        for pair in mutual_exclusive_pairs
        if len(pair) == 2
        for left, right in [tuple(pair)]
        if left in token_by_node_id and right in token_by_node_id
    }  # Pair of generated tokens marked as mutually exclusive in Mermaid.
    for node_id in trait_node_ids:
        trait = traits_by_id[node_id]
        parent_tokens = [
            traits_by_id[parent].token for parent in trait.parents if parent in traits_by_id
        ]
        trait.parents = parent_tokens
        if len(parent_tokens) > 1:
            parent_pairs = {
                frozenset((parent_tokens[left], parent_tokens[right]))
                for left in range(len(parent_tokens))
                for right in range(left + 1, len(parent_tokens))
            }  # Unique parent pairs for this child.
            trait.all_parents = not parent_pairs.issubset(exclusive_token_pairs)
        elif len(parent_tokens) == 1:
            trait.all_parents = True

        if trait.relative_to is None and node_id not in roots:
            parent_id = incoming.get(node_id, [None])[0]
            if parent_id and parent_id in traits_by_id:
                trait.relative_to = traits_by_id[parent_id].token
                trait.x = 0
                trait.y = max(1, depth.get(node_id, 1) - depth.get(parent_id, 0))

    header_pairs = map_headers_to_roots(
        headers,
        declaration_order,
        roots,
        mio_token,
    )
    return [traits_by_id[node_id] for node_id in trait_node_ids], header_pairs


def map_headers_to_roots(
    headers: list[tuple[str, str]],
    declaration_order: list[str],
    roots: list[str],
    mio_token: str,
) -> list[tuple[str, str, str]]:
    """Attach header declarations to the next declared root trait.

    Args:
        headers: Header node tuples (node_id, header_text).
        declaration_order: Original node declaration order.
        roots: Root trait node ids.
        mio_token: Destination MIO token prefix.

    Returns:
        Header mappings as (header_key, root_node_id, header_text).
    """

    header_by_id = dict(headers)
    pending: deque[str] = deque()
    mapped: list[tuple[str, str, str]] = []
    root_set = set(roots)

    for node_id in declaration_order:
        if node_id in header_by_id:
            pending.append(node_id)
            continue
        if node_id not in root_set:
            continue
        if not pending:
            continue
        header_id = pending.popleft()
        header_text = header_by_id[header_id]
        header_key = f"{mio_token}_header_{normalize_token(header_text)}"
        mapped.append((header_key, node_id, header_text))
    return mapped


def compute_depths(roots: list[str], outgoing: dict[str, list[str]]) -> dict[str, int]:
    """Compute longest-path depth for each node reachable from roots.

    Args:
        roots: Root node identifiers.
        outgoing: Adjacency map of node -> children.

    Returns:
        Node id -> depth map.
    """

    depth: dict[str, int] = {root: 0 for root in roots}
    queue: deque[str] = deque(roots)
    while queue:
        current = queue.popleft()
        current_depth = depth[current]
        for child in outgoing.get(current, []):
            next_depth = current_depth + 1
            if next_depth > depth.get(child, -1):
                depth[child] = next_depth
                queue.append(child)
    return depth


def sibling_offsets(count: int) -> list[int]:
    """Return centered x offsets for a sibling group.

    Args:
        count: Number of siblings.

    Returns:
        Integer offsets centered around zero.
    """

    if count <= 1:
        return [0]
    if count % 2 == 1:
        start = -(count // 2)
        return [start + index for index in range(count)]
    half = count // 2
    return [*range(-half, 0), *range(1, half + 1)]


def infer_mio_token(destination_path: Path, insert_line: int) -> str:
    """Infer enclosing MIO token at a destination insertion line.

    Args:
        destination_path: Target MIO script file.
        insert_line: 1-based line index where content will be inserted.

    Returns:
        Enclosing MIO block token.
    """

    lines = read_text_strict(str(destination_path), encoding="utf-8").splitlines()
    if insert_line < 1 or insert_line > len(lines) + 1:
        raise ToolError(f"destination insert line {insert_line} is out of bounds")

    target_index = insert_line - 1
    brace_stack: list[Optional[str]] = []
    opener_re = re.compile(r"^\s*([A-Za-z0-9_:.@-]+)\s*=\s*\{\s*$")
    for line in lines[:target_index]:
        opener = opener_re.match(line)
        named_opener = opener.group(1) if opener else None
        opens = line.count("{")
        closes = line.count("}")
        if opens:
            if named_opener is not None:
                brace_stack.append(named_opener)
                opens -= 1
            for _ in range(opens):
                brace_stack.append(None)
        for _ in range(closes):
            if brace_stack:
                brace_stack.pop()

    for entry in reversed(brace_stack):
        if entry:
            return entry
    if not brace_stack:
        raise ToolError("could not infer containing MIO token at destination line")
    raise ToolError("could not infer named MIO token at destination line")


def format_bonus_block(name: str, values: dict[str, float], base_indent: str) -> list[str]:
    """Render one formatted HOI4 bonus block.

    Args:
        name: Block name (e.g. equipment_bonus).
        values: Bonus key/value map.
        base_indent: Indentation prefix.

    Returns:
        Rendered lines for the block, or an empty list when values is empty.
    """

    if not values:
        return []
    lines = [f"{base_indent}{name} = {{"]
    for key in sorted(values):
        value_text = f"{values[key]:.4f}".rstrip("0").rstrip(".")
        lines.append(f"{base_indent}\t{key} = {value_text}")
    lines.append(f"{base_indent}}}")
    return lines


def format_traits(
    traits: list[TraitSpec],
    header_pairs: list[tuple[str, str, str]],
    traits_by_id: dict[str, TraitSpec],
) -> tuple[str, dict[str, str]]:
    """Render trait/header script and localization entries.

    Args:
        traits: Ordered generated trait specs.
        header_pairs: Header mappings as (header_key, root_node_id, header_text).
        traits_by_id: Trait specs keyed by Mermaid node id.

    Returns:
        Tuple of (rendered_script_text, localization_key_to_text_map).
    """

    lines: list[str] = []
    loc_entries: dict[str, str] = {}

    for header_key, root_id, header_text in header_pairs:
        root_trait = traits_by_id[root_id]
        lines.extend(
            [
                "tree_header_text = {",
                f"\ttext = {header_key}",
                f"\tx = {root_trait.x}",
                "}",
                "",
            ]
        )
        loc_entries[header_key] = header_text

    for trait in traits:
        loc_entries[trait.token] = trait.title
        lines.extend(
            [
                "trait = {",
                f"\ttoken = {trait.token}",
                f"\tname = {trait.token}",
                f"\ticon = {DEFAULT_ICON}",
                "",
            ]
        )

        if trait.parents:
            parent_key = "all_parents" if trait.all_parents else "any_parent"
            lines.append(f"\t{parent_key} = {{")
            for parent in trait.parents:
                lines.append(f"\t\t{parent}")
            lines.append("\t}")
            lines.append("")

        if trait.relative_to is None:
            lines.append(f"\tposition = {{ x = {trait.x} y = {trait.y} }}")
        else:
            lines.append(f"\tposition = {{ x = {trait.x} y = {trait.y} }}")
            lines.append(f"\trelative_position_id = {trait.relative_to}")
        lines.append("")

        if trait.scoped_targets:
            lines.append("\tlimit_to_equipment_type = {")
            for token in trait.scoped_targets:
                lines.append(f"\t\t{token}")
            lines.append("\t}")
            lines.append("")

        for block_name, payload in (
            ("equipment_bonus", trait.equipment_bonus),
            ("production_bonus", trait.production_bonus),
            ("organization_modifier", trait.organization_modifier),
        ):
            block_lines = format_bonus_block(block_name, payload, "\t")
            if not block_lines:
                continue
            lines.extend(block_lines)
            lines.append("")

        lines.append("\ton_complete = { expenditure_for_mio_upgrade = yes }")
        lines.append("}")
        lines.append("")

    output = "\n".join(lines).rstrip() + "\n"
    return output, loc_entries


def insert_text_at_line(path: Path, insert_line: int, text_to_insert: str) -> None:
    """Insert text into a file at a given 1-based line.

    Args:
        path: File to mutate.
        insert_line: 1-based insertion line.
        text_to_insert: Prepared text block to insert.
    """

    content = read_text_strict(str(path), encoding="utf-8")
    lines = content.splitlines(keepends=True)
    if insert_line < 1 or insert_line > len(lines) + 1:
        raise ToolError(f"destination insert line {insert_line} is out of bounds")

    insertion_index = insert_line - 1
    insertion = text_to_insert
    if insertion_index > 0 and not lines[insertion_index - 1].endswith("\n"):
        insertion = "\n" + insertion
    if insertion_index < len(lines) and not insertion.endswith("\n"):
        insertion = insertion + "\n"

    new_content = "".join(lines[:insertion_index]) + insertion + "".join(lines[insertion_index:])
    atomic_write_text(str(path), new_content, encoding="utf-8", bom=False)


def infer_country_tag(destination_path: Path) -> str:
    """Extract destination country tag from MIO filename.

    Args:
        destination_path: Destination MIO script file.

    Returns:
        Three-letter country tag parsed from filename.
    """

    match = MIO_FILE_RE.search(destination_path.name)
    if not match:
        raise ToolError(
            "destination file name must match MD_<TAG>_organizations.txt to infer localisation file"
        )
    return match.group(1)


def update_localisation(
    repo_root: Path, country_tag: str, entries: dict[str, str]
) -> Path:
    """Append missing English localization entries for generated keys.

    Args:
        repo_root: Repository root path.
        country_tag: Destination country tag.
        entries: Generated localization key -> text map.

    Returns:
        Path to the localization file updated (or left unchanged).
    """

    loc_path = repo_root / "localisation" / "english" / f"MD_focus_{country_tag}_l_english.yml"
    if loc_path.exists():
        content = read_text_strict(str(loc_path), encoding="utf-8-sig")
    else:
        content = "l_english:\n"

    existing_keys = set(LOC_KEY_RE.findall(content))
    missing = {key: value for key, value in entries.items() if key not in existing_keys}
    if not missing:
        return loc_path

    if not content.endswith("\n"):
        content += "\n"
    for key in sorted(missing):
        escaped = missing[key].replace('"', '\\"')
        content += f' {key}: "{escaped}"\n'

    atomic_write_text(str(loc_path), content, encoding="utf-8-sig", bom=True)
    return loc_path


def known_equipment_tokens() -> set[str]:
    """Load known equipment and equipment-group tokens.

    Returns:
        Set of valid equipment/equipment-group tokens for scope resolution.
    """

    tokens: set[str] = set()
    tokens.update(Equipment.get_equipment_index().keys())
    tokens.update(EquipmentGroup.from_file().keys())
    return tokens


def run(
    source_md_path: str,
    source_start_line: int,
    destination_path: str,
    destination_insert_line: int,
) -> tuple[Path, Path]:
    """Run Mermaid parsing and trait/localization generation pipeline.

    Args:
        source_md_path: Source markdown path, relative to repo root.
        source_start_line: 1-based line where Mermaid search begins.
        destination_path: Destination MIO script path, relative to repo root.
        destination_insert_line: 1-based insertion line in destination file.

    Returns:
        Tuple of (destination_mio_path, destination_localisation_path).
    """

    source = (REPO_ROOT / source_md_path).resolve()
    destination = (REPO_ROOT / destination_path).resolve()
    repo_root = REPO_ROOT.resolve()

    if not source.is_file():
        raise ToolError(f"source markdown file not found: {source}")
    if not destination.is_file():
        raise ToolError(f"destination file not found: {destination}")
    if repo_root not in source.parents and source != repo_root:
        raise ToolError("source file must live under the repository root")
    if repo_root not in destination.parents and destination != repo_root:
        raise ToolError("destination file must live under the repository root")

    mermaid_lines = parse_mermaid_block(source, source_start_line)
    nodes, declaration_order, edges, mutual_exclusive_pairs = parse_nodes_and_edges(
        mermaid_lines
    )
    mio_token = infer_mio_token(destination, destination_insert_line)
    known_tokens = known_equipment_tokens()
    traits, header_pairs = build_trait_specs(
        nodes,
        declaration_order,
        edges,
        mutual_exclusive_pairs,
        mio_token,
        known_tokens,
    )
    traits_by_id = {trait.node_id: trait for trait in traits}
    generated_text, loc_entries = format_traits(traits, header_pairs, traits_by_id)
    insert_text_at_line(destination, destination_insert_line, generated_text)

    country_tag = infer_country_tag(destination)
    loc_path = update_localisation(repo_root, country_tag, loc_entries)
    return destination, loc_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source_md_path")
    parser.add_argument("source_start_line", type=int)
    parser.add_argument("destination_path")
    parser.add_argument("destination_insert_line", type=int)
    args = parser.parse_args(argv)

    try:
        destination, loc_path = run(
            args.source_md_path,
            args.source_start_line,
            args.destination_path,
            args.destination_insert_line,
        )
    except ToolError as error:
        sys.exit(f"ERROR: {error}")

    rel_destination = destination.relative_to(REPO_ROOT).as_posix()
    rel_loc = loc_path.relative_to(REPO_ROOT).as_posix()
    print(f"wrote generated traits to {rel_destination}")
    print(f"updated localisation keys in {rel_loc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
