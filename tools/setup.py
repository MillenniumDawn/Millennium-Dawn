#!/usr/bin/env python3
"""
setup.py — One-command developer environment setup for Millennium Dawn.

Usage:
    python3 tools/setup.py          Set up mod development (pre-commit + tools)
    python3 tools/setup.py --docs   Also set up the docs site (Node.js + Bun)
    python3 tools/setup.py --check  Check if everything is installed without changing anything

Run this after cloning the repo. It will:
  1. Check Python version (3.10+ required, 3.12+ recommended)
  2. Install pre-commit and set up git hooks
  3. Install Python tool dependencies (requests, pillow)
  4. Optionally set up the docs site (Node.js 24+, Bun)
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
DOCS_DIR = REPO_ROOT / "docs"

MIN_PYTHON = (3, 10)
REC_PYTHON = (3, 12)
MIN_NODE = 24


def run(
    cmd: list[str], check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=capture, text=True)


def check_mark(ok: bool) -> str:
    return "OK" if ok else "MISSING"


def get_version(cmd: list[str]) -> str | None:
    try:
        result = run(cmd, check=False, capture=True)
        return result.stdout.strip().split()[-1] if result.returncode == 0 else None
    except FileNotFoundError:
        return None


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
    ver = get_version(["pre-commit", "--version"])
    installed = ver is not None
    print(f"  pre-commit: {ver if installed else 'not installed'}")
    return installed


def check_hooks_installed() -> bool:
    hook_file = REPO_ROOT / ".git" / "hooks" / "pre-commit"
    installed = hook_file.exists() and "pre-commit" in hook_file.read_text(
        errors="replace"
    )
    print(f"  Git hooks: {check_mark(installed)}")
    return installed


def check_pip_packages() -> bool:
    reqs_file = TOOLS_DIR / "requirements.txt"
    if not reqs_file.exists():
        print("  Tool dependencies: requirements.txt not found")
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
        print(f"  Tool dependencies: missing {', '.join(missing)}")
        return False
    print("  Tool dependencies: OK")
    return True


def check_node() -> tuple[bool, str | None]:
    ver = get_version(["node", "--version"])
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
    ver = get_version(["bun", "--version"])
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
    result = run([sys.executable, "-m", "pip", "install", "pre-commit"], check=False)
    if result.returncode != 0:
        # Try with --user flag
        result = run(
            [sys.executable, "-m", "pip", "install", "--user", "pre-commit"],
            check=False,
        )
    return result.returncode == 0


def install_hooks() -> bool:
    print("Installing git hooks...")
    result = run(["pre-commit", "install"], check=False)
    return result.returncode == 0


def install_pip_packages() -> bool:
    print("Installing tool dependencies...")
    reqs = str(TOOLS_DIR / "requirements.txt")
    result = run([sys.executable, "-m", "pip", "install", "-r", reqs], check=False)
    if result.returncode != 0:
        result = run(
            [sys.executable, "-m", "pip", "install", "--user", "-r", reqs], check=False
        )
    return result.returncode == 0


def install_docs_deps() -> bool:
    print("Installing docs dependencies...")
    result = run(["bun", "install"], check=False)
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

    print("Millennium Dawn Developer Setup")
    print("=" * 40)
    print()

    # --- Check phase ---
    print("Checking environment:")
    py_ok = check_python()
    pc_ok = check_pre_commit()
    hooks_ok = check_hooks_installed()
    deps_ok = check_pip_packages()

    docs_ready = True
    if args.docs or args.check:
        print()
        print("Checking docs environment:")
        node_ok, _ = check_node()
        bun_ok = check_bun()
        docs_deps_ok = check_docs_deps()
        docs_ready = node_ok and bun_ok and docs_deps_ok

    if args.check:
        print()
        all_ok = py_ok and pc_ok and hooks_ok and deps_ok
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
            import os

            saved = os.getcwd()
            os.chdir(DOCS_DIR)
            ok = install_docs_deps() and ok
            os.chdir(saved)

    print()
    print("=" * 40)
    if ok:
        print("Setup complete. You're ready to develop.")
        print()
        print("Quick reference:")
        print("  git commit           Pre-commit hooks run automatically")
        print("  python3 tools/run.py --list    See available dev tools")
        if args.docs:
            print("  cd docs && bun run dev         Preview docs site")
    else:
        print("Setup finished with some issues. Check the output above.")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
