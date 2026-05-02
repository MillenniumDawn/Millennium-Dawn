#!/usr/bin/env python3
"""
setup.py — One-command developer environment setup for Millennium Dawn.

Usage:
    python3 tools/setup.py          Set up mod development (pre-commit + tools + test deps)
    python3 tools/setup.py --docs   Also set up the docs site (Node.js + Bun)
    python3 tools/setup.py --check  Check if everything is installed without changing anything

Prerequisites
-------------
- Python 3.10+ (3.12+ recommended)
- Git
- (Optional for --docs) Node.js 24+ and Bun (https://bun.sh/)

The script will auto-create a local ``.venv`` if your system Python is
externally managed (PEP 668 on Debian/Ubuntu and similar).

Run this after cloning the repo. It will:
  1. Check Python version (3.10+ required, 3.12+ recommended)
  2. Install pre-commit and set up git hooks
  3. Install Python tool dependencies (requests, pillow)
  4. Install Python dev/test dependencies (pytest) so `pytest tools/` works locally
  5. Optionally set up the docs site (Node.js 24+, Bun)
"""

import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

# Force line-buffered stdout so prints appear in the correct order
# even when subprocesses write directly to the fd.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
DOCS_DIR = REPO_ROOT / "docs"

MIN_PYTHON = (3, 10)
REC_PYTHON = (3, 12)
MIN_NODE = 24


def run(
    cmd: list[str], check: bool = True, capture: bool = False, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=capture, text=True, cwd=cwd)


def check_mark(ok: bool) -> str:
    return "OK" if ok else "MISSING"


def get_version(cmd: list[str]) -> str | None:
    try:
        result = run(cmd, check=False, capture=True)
        return result.stdout.strip().split()[-1] if result.returncode == 0 else None
    except FileNotFoundError:
        return None


def _resolve_tool(name: str) -> list[str]:
    """Return a command list that prefers full paths found in common install locations."""
    home = Path.home()
    candidates: list[Path] = []

    if name == "node":
        candidates = [
            home / ".nvm" / "versions" / "node" / "v24.15.0" / "bin" / "node",
            *sorted(
                (home / ".nvm" / "versions" / "node").glob("*/bin/node"), reverse=True
            ),
            Path("/usr/local/bin/node"),
            Path("/opt/node/bin/node"),
        ]
    elif name == "bun":
        candidates = [
            home / ".bun" / "bin" / "bun",
            Path("/usr/local/bin/bun"),
            home / ".local" / "bin" / "bun",
        ]

    for p in candidates:
        if p.exists() and os.access(p, os.X_OK):
            return [str(p)]

    return [name]


def in_virtualenv() -> bool:
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def is_externally_managed() -> bool:
    """Detect PEP 668 externally-managed Python installations."""
    marker = Path(sysconfig.get_path("stdlib")) / "EXTERNALLY-MANAGED"
    return marker.exists()


def venv_python_path() -> Path | None:
    venv_dir = REPO_ROOT / ".venv"
    if not venv_dir.exists():
        return None
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    ext = ".exe" if os.name == "nt" else ""
    py = venv_dir / bin_dir / f"python{ext}"
    return py if py.exists() else None


def create_venv() -> Path:
    venv_dir = REPO_ROOT / ".venv"
    bin_dir = "Scripts" if os.name == "nt" else "bin"
    ext = ".exe" if os.name == "nt" else ""
    py = venv_dir / bin_dir / f"python{ext}"
    if py.exists():
        print("Using existing local virtual environment (.venv)...")
        return py
    print("Creating local virtual environment (.venv)...")
    run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    if not py.exists():
        raise RuntimeError(f"Failed to create venv: {py} not found after creation")
    return py


def reexec_with(python: Path) -> None:
    print(f"Switching to venv Python: {python}")
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(str(python), [str(python), __file__] + sys.argv[1:])


def check_python() -> bool:
    v = sys.version_info
    print(f"  Python: {v.major}.{v.minor}.{v.micro}", end="")
    if v >= REC_PYTHON:
        print(" (recommended)")
    elif v >= MIN_PYTHON:
        print(f" (works, but {REC_PYTHON[0]}.{REC_PYTHON[1]}+ recommended)")
    else:
        print(f" (too old — need {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+)")
        return False
    return True


def check_pre_commit() -> bool:
    ver = get_version([sys.executable, "-m", "pre_commit", "--version"])
    # Only fall back to PATH when we're not using a local venv.
    if ver is None and not venv_python_path():
        ver = get_version(["pre-commit", "--version"])
    installed = ver is not None
    print(f"  pre-commit: {ver if installed else 'not installed'}")
    return installed


def check_hooks_installed() -> bool:
    # Detect git core.hooksPath override (pre-commit refuses to install when set)
    try:
        hooks_path = run(
            ["git", "config", "core.hooksPath"], check=False, capture=True
        ).stdout.strip()
        if hooks_path:
            print(
                f"  Git hooks: {check_mark(False)} (core.hooksPath is set to '{hooks_path}')"
            )
            return False
    except FileNotFoundError:
        pass

    hook_file = REPO_ROOT / ".git" / "hooks" / "pre-commit"
    if not hook_file.exists():
        print(f"  Git hooks: {check_mark(False)}")
        return False
    text = hook_file.read_text(errors="replace")
    has_pre_commit = "pre-commit" in text
    # When using a local venv the hook should point to our python so that
    # commits work even when the venv is not activated.
    if in_virtualenv() and venv_python_path():
        points_to_us = sys.executable in text
        ok = has_pre_commit and points_to_us
    else:
        ok = has_pre_commit
    print(f"  Git hooks: {check_mark(ok)}")
    return ok


def _check_requirements_file(reqs_file: Path, label: str) -> bool:
    """Return True if every package in ``reqs_file`` can be imported."""
    if not reqs_file.exists():
        print(f"  {label}: {reqs_file.name} not found")
        return False
    missing = []
    for line in reqs_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            # pillow imports as PIL
            if pkg.lower() == "pillow":
                try:
                    __import__("PIL")
                    continue
                except ImportError:
                    pass
            missing.append(pkg)
    if missing:
        print(f"  {label}: missing {', '.join(missing)}")
        return False
    print(f"  {label}: OK")
    return True


def check_pip_packages() -> bool:
    return _check_requirements_file(TOOLS_DIR / "requirements.txt", "Tool dependencies")


def check_dev_packages() -> bool:
    return _check_requirements_file(
        TOOLS_DIR / "report_lib" / "requirements-dev.txt", "Dev/test dependencies"
    )


def check_node() -> tuple[bool, str | None]:
    ver = get_version(_resolve_tool("node") + ["--version"])
    if ver:
        # Parse "v24.1.0" -> 24
        major = int(ver.lstrip("v").split(".")[0])
        ok = major >= MIN_NODE
        status = "OK" if ok else f"too old (need v{MIN_NODE}+)"
        print(f"  Node.js: {ver} ({status})")
        return ok, ver
    print("  Node.js: not installed")
    return False, None


def check_bun() -> bool:
    ver = get_version(_resolve_tool("bun") + ["--version"])
    installed = ver is not None
    print(f"  Bun: {ver if installed else 'not installed'}")
    return installed


def check_docs_deps() -> bool:
    node_modules = DOCS_DIR / "node_modules"
    installed = node_modules.is_dir() and any(node_modules.iterdir())
    print(f"  Docs dependencies: {check_mark(installed)}")
    return installed


def install_pre_commit() -> bool:
    print("\nInstalling pre-commit...")
    if not in_virtualenv() and is_externally_managed():
        venv_py = create_venv()
        reexec_with(venv_py)
    result = run([sys.executable, "-m", "pip", "install", "pre-commit"], check=False)
    if result.returncode != 0:
        result = run(
            [sys.executable, "-m", "pip", "install", "--user", "pre-commit"],
            check=False,
        )
    return result.returncode == 0


def _ensure_hooks_path_unset() -> None:
    """Remove a redundant core.hooksPath that points to the default hooks directory."""
    try:
        result = run(["git", "config", "core.hooksPath"], check=False, capture=True)
        hooks_path = result.stdout.strip()
        if hooks_path:
            default = str(REPO_ROOT / ".git" / "hooks")
            if hooks_path == default:
                print("Unsetting redundant core.hooksPath...")
                run(["git", "config", "--unset-all", "core.hooksPath"], check=False)
    except FileNotFoundError:
        pass


def install_hooks() -> bool:
    print("Installing git hooks...")
    _ensure_hooks_path_unset()
    result = run([sys.executable, "-m", "pre_commit", "install"], check=False)
    return result.returncode == 0


def _pip_install(reqs_file: Path, label: str) -> bool:
    """Install ``-r <reqs_file>`` with a --user fallback for PEP 668 systems."""
    print(f"Installing {label}...")
    reqs = str(reqs_file)
    if not in_virtualenv() and is_externally_managed():
        venv_py = create_venv()
        reexec_with(venv_py)
    result = run([sys.executable, "-m", "pip", "install", "-r", reqs], check=False)
    if result.returncode != 0:
        result = run(
            [sys.executable, "-m", "pip", "install", "--user", "-r", reqs], check=False
        )
    return result.returncode == 0


def install_pip_packages() -> bool:
    return _pip_install(TOOLS_DIR / "requirements.txt", "tool dependencies")


def install_dev_packages() -> bool:
    return _pip_install(
        TOOLS_DIR / "report_lib" / "requirements-dev.txt", "dev/test dependencies"
    )


def install_docs_deps() -> bool:
    print("Installing docs dependencies...")
    result = run(_resolve_tool("bun") + ["install"], check=False, cwd=DOCS_DIR)
    return result.returncode == 0


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Set up the Millennium Dawn development environment."
    )
    parser.add_argument(
        "--docs",
        action="store_true",
        help="Also set up the docs site (requires Node.js 24+ and Bun)",
    )
    parser.add_argument(
        "--check", action="store_true", help="Check status without installing anything"
    )
    args = parser.parse_args()

    # If there's a local venv and we're not already inside it, switch into it
    # so that all package checks and installs are consistent.
    venv_py = venv_python_path()
    if venv_py and not in_virtualenv():
        reexec_with(venv_py)

    print("Millennium Dawn Developer Setup\n" + ("=" * 40) + "\n")

    # --- Check phase ---
    print("Checking environment:")
    py_ok = check_python()
    pc_ok = check_pre_commit()
    hooks_ok = check_hooks_installed()
    deps_ok = check_pip_packages()
    dev_deps_ok = check_dev_packages()

    docs_ready = True
    if args.docs or args.check:
        print("\nChecking docs environment:")
        node_ok, _ = check_node()
        bun_ok = check_bun()
        docs_deps_ok = check_docs_deps()
        docs_ready = node_ok and bun_ok and docs_deps_ok

    if args.check:
        all_ok = py_ok and pc_ok and hooks_ok and deps_ok and dev_deps_ok
        if args.docs:
            all_ok = all_ok and docs_ready
        if all_ok:
            print("Everything is set up.")
        else:
            print("Some components need setup. Run without --check to install.")
        sys.exit(0 if all_ok else 1)

    if not py_ok:
        print(
            f"\nPython {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required. Please install it first."
        )
        sys.exit(1)

    # --- Install phase ---
    ok = True

    if not pc_ok:
        ok = install_pre_commit() and ok

    if not hooks_ok:
        ok = install_hooks() and ok

    if not deps_ok:
        ok = install_pip_packages() and ok

    if not dev_deps_ok:
        ok = install_dev_packages() and ok

    if args.docs:
        node_ok_now, _ = check_node() if not node_ok else (True, None)
        bun_ok_now = check_bun() if not bun_ok else True

        if not node_ok_now:
            print(
                f"\nNode.js {MIN_NODE}+ is required for docs. Install it from https://nodejs.org/"
            )
            ok = False
        elif not bun_ok_now:
            print("\nBun is required for docs. Install it from https://bun.sh/")
            ok = False
        elif not docs_deps_ok:
            ok = install_docs_deps() and ok

    print("\n" + ("=" * 40))
    if ok:
        print("Setup complete. You're ready to develop.")
        if venv_python_path():
            print("\nNote: A local .venv is used. Activate it in your shell:")
            if os.name == "nt":
                print(f"  {REPO_ROOT / '.venv' / 'Scripts' / 'activate.bat'}  (cmd)")
                print(
                    f"  {REPO_ROOT / '.venv' / 'Scripts' / 'Activate.ps1'}  (PowerShell)"
                )
            else:
                print(f"  source {REPO_ROOT / '.venv' / 'bin' / 'activate'}")
        print("\nQuick reference:")
        print(
            "  git commit                               Pre-commit hooks run automatically"
        )
        print("  python3 tools/run.py --list              See available dev tools")
        print("  pytest tools/report_lib tools/validation Run tool test suite")
        if args.docs:
            print("  cd docs && bun run dev                   Preview docs site")
    else:
        print("Setup finished with some issues. Check the output above.")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
