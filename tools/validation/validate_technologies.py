#!/usr/bin/env python3
"""Validate technology category consistency in Millennium Dawn.

Rules from .claude/docs/focus-tree-reference.md + AGENTS.md category rules:
  * A generation tech (one whose id matches a parent's id after stripping
    digits and underscores) must carry every category its parent carries.
  * A gen dropping a category its whole lineage has is a copy-paste slip that
    silently mis-tags the tech in the research tree (e.g. a special-project
    gated gen losing CAT_Military).
  * Techs whose id does not share the parent's stripped stem (branches into a
    distinct subtype, e.g. countermeasures vs. air weapons, or Anti_Air vs.
    AA_upgrade) are intentionally different and are NOT flagged.
"""

import glob
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from validator_common import BaseValidator, run_validator_main, strip_comments

TECH_DIR = "common/technologies"

# `TAG = {` at one tab indent, inside `technologies = {`.
TECH_DEF_RE = re.compile(r"(?m)^\t([A-Za-z0-9_]+) = \{")
CATS_RE = re.compile(r"categories\s*=\s*\{(.*?)\}", re.DOTALL)
LEADS_RE = re.compile(r"leads_to_tech\s*=\s*([A-Za-z0-9_]+)")


def stem(tid: str) -> str:
    """Family stem: id with digits and underscores removed, lowercased."""
    return re.sub(r"[\d_]", "", tid).lower()


def _block(text: str, start: int) -> Tuple[int, int]:
    """Return (start_of_body, end) of the brace block starting at `start`."""
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return start, i


def _parse_file(text: str) -> Dict[str, Dict]:
    techs: Dict[str, Dict] = {}
    for m in TECH_DEF_RE.finditer(text):
        tid = m.group(1)
        start = m.end()
        body_start, end = _block(text, start)
        body = text[body_start : end - 1]
        cats = CATS_RE.search(body)
        cat_list = cats.group(1).split() if cats else []
        leads = LEADS_RE.findall(body)
        techs[tid] = {
            "cats": cat_list,
            "leads": leads,
            "line": text.count("\n", 0, m.start()) + 1,
        }
    return techs


class Validator(BaseValidator):
    TITLE = "TECHNOLOGIES"
    STAGED_EXTENSIONS = (".txt",)

    def run_validations(self):
        pattern = str(Path(self.mod_path) / TECH_DIR / "*.txt")
        files = sorted(glob.glob(pattern))
        if not files:
            return

        all_techs: Dict[str, Dict] = {}
        file_techs: Dict[str, List[str]] = {}
        for path in files:
            rel = Path(path).relative_to(self.mod_path).as_posix()
            try:
                text = Path(path).read_text(encoding="utf-8")
            except OSError:
                continue
            clean = strip_comments(text)
            parsed = _parse_file(clean)
            all_techs.update(parsed)
            file_techs[rel] = list(parsed.keys())

        parents: Dict[str, List[str]] = {}
        for tid, t in all_techs.items():
            for child in t["leads"]:
                parents.setdefault(child, []).append(tid)

        staged: Optional[Set[Path]] = None
        if self.staged_only:
            staged = {Path(f).resolve() for f in self.staged_files or []}
        findings = 0
        for tid in sorted(all_techs):
            rel = _path_for(tid, file_techs)
            if (
                staged is not None
                and Path(self.mod_path).joinpath(rel).resolve() not in staged
            ):
                continue
            for parent in parents.get(tid, []):
                if parent not in all_techs:
                    continue
                if stem(parent) != stem(tid):
                    continue
                missing = sorted(
                    set(all_techs[parent]["cats"]) - set(all_techs[tid]["cats"])
                )
                for cat in missing:
                    findings += 1
                    self.add_error(
                        "category-missing",
                        f"tech '{tid}' is missing category '{cat}' that its "
                        f"parent '{parent}' carries",
                        rel,
                        all_techs[tid]["line"],
                    )
        self.log(
            f"  Scanned {len(files)} files | {len(all_techs)} techs | {findings} findings"
        )


def _path_for(tid: str, file_techs: Dict[str, List[str]]) -> str:
    for rel, ids in file_techs.items():
        if tid in ids:
            return rel
    return ""


if __name__ == "__main__":
    run_validator_main(Validator, "Validate technology category consistency")
