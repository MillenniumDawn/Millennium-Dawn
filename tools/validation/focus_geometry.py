"""Tree-scoped static focus geometry, independent of parsing and game state."""

from collections import defaultdict, deque
from itertools import combinations, product


def _key(focus):
    return focus["id"], focus["file"], focus["line"]


def _shared_index(files):
    shared = defaultdict(list)
    dependents = defaultdict(set)
    requirements = {}
    for file in files:
        for focus in file["shared"]:
            shared[focus["id"]].append(focus)
    for name, definitions in shared.items():
        required = {
            parent
            for focus in definitions
            for group in focus["prerequisites"]
            for parent in group
            if parent in shared
        }
        requirements[name] = required
        for parent in required:
            dependents[parent].add(name)
    return shared, dependents, requirements


def _assemble(tree, shared, dependents, requirements):
    missing = set(tree["shared_refs"]) - shared.keys()
    imported = set(tree["shared_refs"]) - missing
    pending = deque(sorted(imported))
    remaining = {}
    while pending:
        name = pending.popleft()
        for child in sorted(dependents.get(name, ())):
            if child in imported:
                continue
            if child not in remaining:
                remaining[child] = requirements[child] - imported
            else:
                remaining[child].discard(name)
            if not remaining[child]:
                imported.add(child)
                pending.append(child)
    focuses = list(tree["focuses"])
    for name in sorted(imported):
        focuses.extend(shared.get(name, ()))
    return sorted(focuses, key=_key), missing


def _hidden_ids(index):
    children = defaultdict(set)
    hidden = set()
    for name, definitions in index.items():
        for focus in definitions:
            if focus["allow_branch"]:
                hidden.add(name)
            for group in focus["prerequisites"]:
                for parent in group:
                    children[parent].add(name)
    pending = deque(sorted(hidden))
    while pending:
        for child in children[pending.popleft()] - hidden:
            hidden.add(child)
            pending.append(child)
    return hidden


def _positions(index):
    """Memoize both coordinates and failed chains without Python recursion."""
    positions = {}
    failures = {}
    for start in sorted(index):
        path = []
        active = set()
        current = start
        while current not in positions:
            if current in active:
                cycle = path[path.index(current) :]
                root = min(cycle)
                failures[("cycle", root)] = (
                    index[root][0],
                    "relative-position cycle involving " + ", ".join(sorted(cycle)),
                )
                positions[current] = None
                break
            if current not in index:
                root = path[-1]
                failures[("missing", current)] = (
                    index[root][0],
                    f"relative anchor '{current}' is absent from this tree",
                )
                positions[current] = None
                break
            definitions = index[current]
            focus = definitions[0]
            if len(definitions) != 1:
                failures[("ambiguous", current)] = (
                    focus,
                    f"focus '{current}' has ambiguous duplicate definitions",
                )
                positions[current] = None
                break
            if focus["x"] is None or focus["y"] is None:
                failures[("coordinates", current)] = (
                    focus,
                    f"focus '{current}' has missing or nonnumeric coordinates",
                )
                positions[current] = None
                break
            path.append(current)
            active.add(current)
            if not focus["relative"]:
                positions[current] = (focus["x"], focus["y"], focus["offset"])
                break
            current = focus["relative"]
        for name in reversed(path):
            if name in positions:
                continue
            focus = index[name][0]
            anchor = positions[focus["relative"]]
            positions[name] = (
                None
                if anchor is None
                else (
                    anchor[0] + focus["x"],
                    anchor[1] + focus["y"],
                    anchor[2] or focus["offset"],
                )
            )
    return positions, failures


def _overlaps(eligible):
    rows = defaultdict(lambda: defaultdict(list))
    for focus, position in eligible:
        rows[position[1]][position[0]].append(focus)
    for y, cells in sorted(rows.items()):
        columns = sorted(cells)
        for index, x in enumerate(columns):
            focuses = cells[x]
            for left, right in combinations(focuses, 2):
                yield left, right, (x, y), (x, y)
            neighbor = index + 1
            while neighbor < len(columns) and columns[neighbor] - x < 2:
                other_x = columns[neighbor]
                for left, right in product(focuses, cells[other_x]):
                    yield left, right, (x, y), (other_x, y)
                neighbor += 1


def _point(position):
    return f"({position[0]}, {position[1]})"


def analyze_layout(files: list[dict], reportable: set[str] | None = None) -> dict:
    """Return deterministic warnings and counts for selected assembled trees.

    Missing coordinates remain unknown. Any gated prerequisite ancestry or
    offset-bearing relative ancestry is excluded rather than evaluated.
    """
    counts = dict.fromkeys(
        (
            "selected_trees",
            "missing_shared_refs",
            "instances",
            "resolved",
            "unresolved",
            "dynamic_skipped",
            "gated",
            "offset",
            "static_eligible",
            "overlap_pairs",
            "trees_with_overlaps",
        ),
        0,
    )
    findings = []
    unresolved = []
    shared, dependents, requirements = _shared_index(files)
    for file in sorted(files, key=lambda item: item["filepath"]):
        for tree in sorted(file["trees"], key=lambda item: (item["id"], item["line"])):
            focuses, missing = _assemble(tree, shared, dependents, requirements)
            # Post-edit membership cannot reveal removed shared dependencies.
            if reportable is not None and not (
                file["filepath"] in reportable
                or (tree["shared_refs"] and reportable)
                or any(focus["file"] in reportable for focus in focuses)
            ):
                continue
            counts["selected_trees"] += 1
            counts["missing_shared_refs"] += len(missing)
            counts["instances"] += len(focuses)
            index = defaultdict(list)
            for focus in focuses:
                index[focus["id"]].append(focus)
            hidden = _hidden_ids(index)
            positions, failures = _positions(index)
            label = f"Focus tree '{tree['id']}'"
            for name in sorted(missing):
                unresolved.append(
                    (
                        f"{label}: imported shared focus '{name}' has no definition",
                        file["filepath"],
                        tree["line"],
                    )
                )
            for focus, reason in failures.values():
                unresolved.append((f"{label}: {reason}", focus["file"], focus["line"]))
            eligible = []
            for focus in focuses:
                position = positions[focus["id"]]
                if position is None:
                    counts["unresolved"] += 1
                    continue
                counts["resolved"] += 1
                gated = focus["id"] in hidden
                offset = position[2]
                counts["gated"] += int(gated)
                counts["offset"] += int(offset)
                if gated or offset:
                    counts["dynamic_skipped"] += 1
                else:
                    eligible.append((focus, position))
            counts["static_eligible"] += len(eligible)
            pairs = list(_overlaps(eligible))
            counts["overlap_pairs"] += len(pairs)
            counts["trees_with_overlaps"] += bool(pairs)
            for left, right, left_xy, right_xy in pairs:
                findings.append(
                    (
                        f"{label}: '{left['id']}' at {_point(left_xy)} "
                        f"({left['file']}:{left['line']}) overlaps "
                        f"'{right['id']}' at {_point(right_xy)} "
                        f"({right['file']}:{right['line']}); "
                        "same-row focus spacing must be at least 2",
                        left["file"],
                        left["line"],
                    )
                )
    return {
        "findings": sorted(findings),
        "unresolved": sorted(unresolved),
        "counts": counts,
    }
