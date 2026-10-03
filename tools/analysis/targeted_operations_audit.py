"""Run the focused Targeted Operations generation and contract checks."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str]) -> int:
    print("+ " + " ".join(command), flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def main() -> int:
    generator = [
        sys.executable,
        "tools/generators/generate_targeted_operations.py",
        "--check",
    ]
    if run(generator):
        return 1

    tests = sorted((ROOT / "tools/tests").glob("targeted_operations*_test.py"))
    basetemp = (ROOT / ".pytest_cache" / "targeted-operations-audit").resolve()
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    pytest = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--basetemp",
        str(basetemp),
        *(path.relative_to(ROOT).as_posix() for path in tests),
    ]
    return run(pytest)


if __name__ == "__main__":
    raise SystemExit(main())
