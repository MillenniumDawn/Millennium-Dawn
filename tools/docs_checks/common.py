"""Shared paths and helpers for the docs-site checks.

All check scripts live under `tools/docs_checks/` and import their path
constants from here so the docs root is resolved in exactly one place.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

# tools/docs_checks/common.py -> parents[2] is the repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = REPO_ROOT / "docs"
CONTENT_ROOT = DOCS_ROOT / "src" / "content"
DIST_DIR = DOCS_ROOT / "dist"

# Must match SITE_BASE_PATH in docs/src/shared/config/site.ts. The built site
# prefixes every internal URL with this, so the link/OG checks need it to map a
# URL back to a file in dist/.
SITE_BASEURL = "/Millennium-Dawn"

# Must match SITE_FALLBACK_ORIGIN in docs/src/shared/config/site.ts. Used to tell
# a same-origin absolute URL (which maps to a file in dist/) from a genuinely
# external one (a CDN, say) that shouldn't be checked against the local build.
SITE_ORIGIN = "https://millenniumdawn.github.io"

MARKDOWN_GLOBS = ("**/*.md", "**/*.mdx")


@dataclass
class CheckResult:
    name: str
    passed: bool
    output: str
    duration: float


def run_cmd(name: str, cmd: list[str], cwd: Path = DOCS_ROOT) -> CheckResult:
    """Run a subprocess and capture it as a CheckResult."""
    start = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    duration = time.monotonic() - start
    output = (proc.stdout + proc.stderr).strip()
    return CheckResult(
        name=name, passed=proc.returncode == 0, output=output, duration=duration
    )


def iter_markdown(root: Path = CONTENT_ROOT):
    """Yield every Markdown / MDX file under ``root`` in a stable order."""
    seen: set[Path] = set()
    for glob in MARKDOWN_GLOBS:
        for path in sorted(root.glob(glob)):
            if path not in seen:
                seen.add(path)
                yield path
