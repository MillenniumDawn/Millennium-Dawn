#!/usr/bin/env python3
"""Resize decision art that validate_decisions.py reports as wrong-slot.

The decision view draws every icon at its texture's native size, so a category
icon (52x40) on a decision, or a decision icon (33x32) on a category, renders
at the wrong size. This clears `decision-icon-slot-mismatch` findings:

- A sprite whose texture serves no other purpose (only wrong-slot uses in
  common/decisions/, no other reference in the repo, texture not shared) is
  resized in place; no script changes.
- Anything else (also used in its own slot, vanilla-owned, idea/faction/agency
  art) gets a resized sibling: a new .dds next to the source, a spriteType in
  interface/MD_decisions.gfx, and every wrong-slot reference repointed.
- Art used as a category `picture` (114x101) is only reported: a 33x32 icon
  cannot become a banner without redrawing.

Textures are fit-scaled (never cropped) and centred on a transparent canvas of
the slot's size, written as uncompressed ARGB DDS like the rest of MD's icons.

    python3 tools/assets/resize_decision_icons.py --dry-run
    python3 tools/assets/resize_decision_icons.py
"""

import argparse
import glob
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validation"))

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install --group runtime")

from image_size import read_image_size
from shared_utils import find_hoi4_install
from sprite_index import build_sprite_index, build_sprite_texture_index
from validate_decisions import (
    _DEC_ICON_BLOCK_RE,
    _DEC_ICON_KEY_RE,
    _DEC_ICON_SIMPLE_RE,
    _DEC_PICTURE_RE,
    _extract_decision_icons,
    _resolved_sprite,
    _slot_for_size,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GFX_FILE = Path("interface/MD_decisions.gfx")
SIBLING_DIR = Path("gfx/interface/decisions")

SLOT_SIZES = {"decision": (33, 32), "category_icon": (52, 40)}
_OWN_PREFIXES = ("GFX_decision_", "GFX_decisions_")
_DECISION_PREFIXES = (
    "GFX_decisions_category_",
    "GFX_decision_category_",
    "GFX_decision_cat_",
    "GFX_decision_",
)
# Repo-wide reference scan for the in-place test. .gfx files are excluded: a
# sprite's own definition is not a use, and shared textures are caught via
# the texture index instead.
_REFERENCE_EXTENSIONS = {".txt", ".gui", ".yml", ".lua"}
_REFERENCE_SKIP_DIRS = {".git", "resources", "tools", "common/decisions"}


class Ref:
    __slots__ = ("file", "kind", "value", "line")

    def __init__(self, file: str, kind: str, value: str, line: int):
        self.file = file
        self.kind = kind
        self.value = value
        self.line = line


class Job:
    """One offending sprite and what to do about it."""

    def __init__(self, sprite: str, texture: str, size: Tuple[int, int], actual: str):
        self.sprite = sprite
        self.texture = texture
        self.size = size
        self.actual = actual
        self.wrong: Dict[str, List[Ref]] = defaultdict(list)
        self.correct = 0
        self.action = ""
        self.sibling = ""
        self.sibling_texture = ""
        self.reuse = False
        self.reason = ""


def _decision_files(root: Path) -> List[str]:
    return sorted(
        glob.glob(str(root / "common" / "decisions" / "**" / "*.txt"), recursive=True)
    )


def _is_under(path: str, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _repo_references(root: Path, names: Set[str]) -> Set[str]:
    """Sprite names referenced anywhere outside common/decisions and the .gfx files."""
    if not names:
        return set()
    pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in names) + r")\b")
    hits: Set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root).replace("\\", "/")
        rel = "" if rel == "." else rel
        dirnames[:] = [
            d
            for d in dirnames
            if (f"{rel}/{d}" if rel else d) not in _REFERENCE_SKIP_DIRS
            and not d.startswith(".")
        ]
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() not in _REFERENCE_EXTENSIONS:
                continue
            try:
                with open(
                    os.path.join(dirpath, filename),
                    encoding="utf-8-sig",
                    errors="replace",
                ) as fh:
                    text = fh.read()
            except OSError:
                continue
            hits.update(pattern.findall(text))
            if len(hits) == len(names):
                return hits
    return hits


def collect_jobs(root: Path, textures: Dict[str, str]) -> List[Job]:
    jobs: Dict[str, Job] = {}
    for path in _decision_files(root):
        rel = os.path.relpath(path, root).replace("\\", "/")
        for _owner, kind, value, line in _extract_decision_icons((path, str(root))):
            if "[" in value or "]" in value:
                continue
            sprite = _resolved_sprite(kind, value, textures)
            if sprite is None:
                continue
            size = read_image_size(textures[sprite])
            if size is None:
                continue
            actual = _slot_for_size(*size)
            if actual is None:
                continue
            job = jobs.get(sprite)
            if job is None:
                job = jobs[sprite] = Job(sprite, textures[sprite], size, actual)
            if actual == kind:
                job.correct += 1
            else:
                job.wrong[kind].append(Ref(rel, kind, value, line))
    return [j for j in jobs.values() if j.wrong]


def _shared_textures(textures: Dict[str, str]) -> Set[str]:
    by_path: Dict[str, List[str]] = defaultdict(list)
    for name, path in textures.items():
        by_path[os.path.normcase(os.path.normpath(path))].append(name)
    return {n for names in by_path.values() if len(names) > 1 for n in names}


def _sibling_base(sprite: str) -> str:
    for prefix in _DECISION_PREFIXES:
        if sprite.startswith(prefix):
            base = sprite[len(prefix) :]
            break
    else:
        base = sprite[4:] if sprite.startswith("GFX_") else sprite
    if base.endswith("_decision_category"):
        base = base[: -len("_decision_category")]
    return base


def _sibling_name(
    sprite: str, target: str, taken: Set[str], slot_of: Callable[[str], Optional[str]]
) -> Tuple[str, bool]:
    """Return (name, reuse). A same-subject sprite whose art already sits in
    the target slot (*slot_of*) is repointed to instead of duplicated."""
    base = _sibling_base(sprite)
    if target == "decision":
        candidates = [f"GFX_decision_{base}", f"GFX_decision_{base}_small"]
    else:
        candidates = [
            f"GFX_decision_category_{base}",
            f"GFX_decision_category_{base}_icon",
        ]
    for name in candidates:
        if name != sprite and slot_of(name) == target:
            return name, True
        if name not in taken:
            return name, False
    raise SystemExit(
        f"No free sibling name for {sprite} ({target}): tried {candidates}"
    )


def classify(
    root: Path, jobs: List[Job], textures: Dict[str, str], taken: Set[str]
) -> None:
    shared = _shared_textures(textures)
    referenced = _repo_references(root, {j.sprite for j in jobs})
    for job in jobs:
        kinds = list(job.wrong)
        if "category_picture" in kinds:
            picture_only = kinds == ["category_picture"]
            if picture_only:
                job.action = "manual"
                job.reason = (
                    "used as a category picture; needs banner art, not a resize"
                )
                continue
            kinds.remove("category_picture")
        target = kinds[0] if len(kinds) == 1 else ""
        if not target:
            job.action = "sibling"
            job.reason = "wrong in two slots"
            continue
        if not _is_under(job.texture, root):
            job.reason = "vanilla texture"
        elif not job.sprite.startswith(_OWN_PREFIXES):
            job.reason = "not decision-family art"
        elif job.correct:
            job.reason = f"used correctly x{job.correct}"
        elif job.sprite in shared:
            job.reason = "texture shared with another sprite"
        elif job.sprite in referenced:
            job.reason = "referenced outside common/decisions"
        else:
            job.action = "in-place"
            job.reason = ""
            continue
        job.action = "sibling"
    # Slot an existing sprite's art will be in once this run is done: in-place
    # resizes move to their target, everything else stays as read from disk.
    moved = {j.sprite: _target_kind(j) for j in jobs if j.action == "in-place"}

    def slot_after_run(name: str) -> Optional[str]:
        if name in moved:
            return moved[name]
        path = textures.get(name)
        size = read_image_size(path) if path else None
        return _slot_for_size(*size) if size else None

    # Give every sibling job its name and texture path; two sources landing on
    # the same name build it once, from whichever source needs the least scaling.
    by_name: Dict[str, List[Job]] = defaultdict(list)
    for job in jobs:
        if job.action != "sibling":
            continue
        target = _target_kind(job)
        job.sibling, job.reuse = _sibling_name(
            job.sprite, target, taken, slot_after_run
        )
        if job.reuse:
            job.reason += f"; repointed to existing {job.sibling}"
            continue
        by_name[job.sibling].append(job)
    for name, group in by_name.items():
        taken.add(name)
        target_edge = max(SLOT_SIZES[_target_kind(group[0])])
        builder = min(
            group,
            key=lambda j: (max(j.size) < target_edge, abs(max(j.size) - target_edge)),
        )
        for job in group:
            job.sibling_texture = _sibling_texture_path(root, builder, name)
            if job is not builder:
                job.reason += f"; built from {builder.sprite}"


def _target_kind(job: Job) -> str:
    kinds = [k for k in job.wrong if k != "category_picture"]
    return kinds[0]


def _sibling_texture_path(root: Path, source: Job, name: str) -> str:
    """Beside the source when that is decision art; otherwise (vanilla, idea,
    event or faction art) under gfx/interface/decisions/."""
    filename = name[4:] + ".dds"
    directory = Path(source.texture).parent
    if not _is_under(source.texture, root / SIBLING_DIR):
        directory = root / SIBLING_DIR
    return os.path.relpath(directory / filename, root).replace("\\", "/")


def render(source: str, target: str) -> Image.Image:
    size = SLOT_SIZES[target]
    art = Image.open(source).convert("RGBA")
    scale = min(size[0] / art.width, size[1] / art.height)
    scaled = art.resize(
        (max(1, round(art.width * scale)), max(1, round(art.height * scale))),
        Image.LANCZOS,
    )
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(
        scaled, ((size[0] - scaled.width) // 2, (size[1] - scaled.height) // 2)
    )
    return canvas


def _write_dds(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="DDS")


def _rewrite_references(root: Path, jobs: Sequence[Job]) -> List[str]:
    """Repoint every wrong-slot reference of a sibling job; returns files touched."""
    per_file: Dict[str, Dict[Tuple[str, str], str]] = defaultdict(dict)
    for job in jobs:
        if job.action != "sibling":
            continue
        for kind, refs in job.wrong.items():
            if kind == "category_picture":
                continue
            for ref in refs:
                per_file[ref.file][(kind, ref.value)] = job.sibling
    touched = []
    for rel, mapping in sorted(per_file.items()):
        path = root / rel
        with open(path, encoding="utf-8-sig", newline="") as fh:
            text = fh.read()
        new = _rewrite_text(text, mapping)
        if new != text:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(new)
            touched.append(rel)
    return touched


def _rewrite_text(text: str, mapping: Dict[Tuple[str, str], str]) -> str:
    def swap(match: "re.Match[str]", kind: str) -> str:
        target = mapping.get((kind, match.group(1)))
        if target is None:
            return match.group(0)
        whole = match.group(0)
        start = match.start(1) - match.start()
        end = match.end(1) - match.start()
        return whole[:start] + target + whole[end:]

    icon_kind = (
        "category_icon" if any(k == "category_icon" for k, _ in mapping) else "decision"
    )
    text = _DEC_ICON_SIMPLE_RE.sub(lambda m: swap(m, icon_kind), text)
    text = _DEC_PICTURE_RE.sub(lambda m: swap(m, "category_picture"), text)

    # Dynamic `icon = { key = X trigger = { ... } }` blocks carry one key per
    # branch; only the key lines inside the block are rewritten.
    out = []
    pos = 0
    for match in _DEC_ICON_BLOCK_RE.finditer(text):
        if match.start() < pos:
            continue
        end = _block_end(text, match)
        out.append(text[pos : match.start()])
        out.append(
            _DEC_ICON_KEY_RE.sub(
                lambda m: swap(m, icon_kind), text[match.start() : end]
            )
        )
        pos = end
    out.append(text[pos:])
    return "".join(out)


def _block_end(text: str, match: "re.Match[str]") -> int:
    depth = 0
    for i in range(match.end() - 1, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def _append_sprites(root: Path, entries: List[Tuple[str, str]]) -> None:
    if not entries:
        return
    path = root / GFX_FILE
    with open(path, encoding="utf-8-sig", newline="") as fh:
        text = fh.read()
    body = text.rstrip()
    if not body.endswith("}"):
        raise SystemExit(f"{GFX_FILE} does not end with a closing brace")
    body = body[:-1].rstrip()
    blocks = [
        f'\tspriteType = {{\n\t\tname = "{name}"\n\t\ttexturefile = "{texture}"\n\t}}'
        for name, texture in entries
    ]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(body + "\n\n" + "\n\n".join(blocks) + "\n\n}\n")


def apply(root: Path, jobs: List[Job], dry_run: bool) -> Dict[str, int]:
    counts = {"in-place": 0, "sibling": 0, "manual": 0, "refs": 0}
    built: Set[str] = set()
    entries: List[Tuple[str, str]] = []
    for job in jobs:
        counts[job.action] += 1
        if job.action == "in-place":
            target = _target_kind(job)
            if not dry_run:
                _write_dds(render(job.texture, target), Path(job.texture))
        elif job.action == "sibling":
            counts["refs"] += sum(
                len(r) for k, r in job.wrong.items() if k != "category_picture"
            )
            if job.reuse or job.sibling in built:
                continue
            built.add(job.sibling)
            if (root / job.sibling_texture).exists():
                raise SystemExit(f"{job.sibling_texture} already exists")
            entries.append((job.sibling, job.sibling_texture))
            if not dry_run:
                _write_dds(
                    render(job.texture, _target_kind(job)), root / job.sibling_texture
                )
    if not dry_run:
        _append_sprites(root, entries)
        _rewrite_references(root, jobs)
    return counts


def _describe(job: Job, root: Path) -> str:
    wrong = ", ".join(f"{k} x{len(v)}" for k, v in job.wrong.items())
    texture = (
        os.path.relpath(job.texture, root).replace("\\", "/")
        if _is_under(job.texture, root)
        else "vanilla"
    )
    head = f"{job.action:8s} {job.sprite} {job.size[0]}x{job.size[1]} ({job.actual}) -> {wrong}"
    if job.action == "sibling":
        head += f"  => {job.sibling}" + (
            "" if job.reuse else f" [{job.sibling_texture}]"
        )
    if job.reason:
        head += f"  ({job.reason})"
    if job.action == "manual":
        head += "".join(
            f"\n           {r.file}:{r.line}"
            for refs in job.wrong.values()
            for r in refs
        )
    return head + (
        "" if texture == "vanilla" or job.action != "in-place" else f"  [{texture}]"
    )


def main(argv: Optional[List[str]] = None, root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--path", default=str(root), help="mod root (default: repo root)"
    )
    parser.add_argument("--hoi4", help="HOI4 install (default: auto-detected)")
    parser.add_argument(
        "--dry-run", action="store_true", help="report actions, write nothing"
    )
    args = parser.parse_args(argv)
    root = Path(args.path).resolve()
    if args.hoi4:
        os.environ["HOI4_PATH"] = args.hoi4
    install = find_hoi4_install()
    print(f"HOI4 install: {install or 'not found (vanilla-art sites will be skipped)'}")

    textures = build_sprite_texture_index(str(root))
    taken = set(build_sprite_index(str(root), gfx_only=True))
    jobs = collect_jobs(root, textures)
    classify(root, jobs, textures, taken)
    jobs.sort(key=lambda j: (j.action, j.sprite))
    for job in jobs:
        print(_describe(job, root))
    counts = apply(root, jobs, args.dry_run)
    print(
        f"\n{'Would resize' if args.dry_run else 'Resized'} {counts['in-place']} textures in place, "
        f"{counts['sibling']} sprites via sibling ({counts['refs']} references), "
        f"{counts['manual']} left for manual work"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
