"""Guards every text-mode write in tools/ against Windows newline translation.

Python's text mode rewrites each "\\n" as "\\r\\n" on Windows unless the caller
passes newline="". A tool that reads an LF file, rewrites it, and hands back a
CRLF file makes the mixed-line-ending pre-commit hook bounce the next commit
that touches it — see AGENTS.md (Formatting).

Path.write_text is rejected outright: it grew a newline parameter only in
3.10 and reads as safe at a glance, so an explicit open(..., newline="") is
required instead.
"""

import ast
import os

from shared.paths import REPO_ROOT
from shared.paths import TOOLS_DIR as TOOLS_ROOT
from shared_utils import read_text_under

# Deliberate exemptions, as "<repo-relative path>:<line>". Add an entry only for
# a write whose consumer genuinely requires platform-native line endings, and
# say why — never to silence a real offender.
_ALLOWLIST: set[str] = set()

_WRITE_MODES = set("wax")


def _mode_arg(call: ast.Call) -> ast.expr | None:
    """Return the mode argument node (positional or keyword), if present."""
    if len(call.args) >= 2:
        return call.args[1]
    for kw in call.keywords:
        if kw.arg == "mode":
            return kw.value
    return None


def _is_text_write(call: ast.Call) -> bool:
    mode_node = _mode_arg(call)
    if mode_node is None:
        return False  # open() defaults to "r"
    mode = getattr(mode_node, "value", None)
    if not isinstance(mode, str):
        # A computed mode could be anything — require the kwarg rather than guess.
        return True
    return "b" not in mode and bool(_WRITE_MODES & set(mode))


def _callee_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _has_newline_kwarg(call: ast.Call) -> bool:
    return any(kw.arg == "newline" for kw in call.keywords)


def _python_sources():
    for dirpath, dirnames, filenames in os.walk(TOOLS_ROOT):
        dirnames[:] = [d for d in dirnames if d not in ("tests", "__pycache__")]
        for filename in filenames:
            if filename.endswith(".py") and not filename.endswith("_test.py"):
                yield os.path.join(dirpath, filename)


def _offenders():
    found = []
    for path in _python_sources():
        tree = ast.parse(
            read_text_under(path, TOOLS_ROOT, encoding="utf-8", errors="strict"),
            filename=path,
        )
        rel = os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _callee_name(node)
            if isinstance(node.func, ast.Attribute) and name == "write_text":
                reason = "Path.write_text — use open(..., newline='') instead"
            elif (
                name == "open" and _is_text_write(node) and not _has_newline_kwarg(node)
            ):
                reason = "text-mode open() without newline=''"
            else:
                continue
            location = f"{rel}:{node.lineno}"
            if location in _ALLOWLIST:
                continue
            found.append(f"{location}: {reason}")
    return found


def test_no_untranslated_text_writes():
    offenders = _offenders()
    assert not offenders, "Text writes that will emit CRLF on Windows:\n" + "\n".join(
        sorted(offenders)
    )


def test_allowlist_entries_still_exist():
    """A stale allowlist entry silently exempts whatever moves onto that line."""
    live = set()
    for path in _python_sources():
        rel = os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
        tree = ast.parse(
            read_text_under(path, TOOLS_ROOT, encoding="utf-8", errors="strict"),
            filename=path,
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _callee_name(node) in (
                "open",
                "write_text",
            ):
                live.add(f"{rel}:{node.lineno}")
    assert not (
        _ALLOWLIST - live
    ), f"Allowlist entries no longer exist: {_ALLOWLIST - live}"
