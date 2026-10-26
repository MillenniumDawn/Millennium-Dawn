"""Run Targeted Operations generation, lifecycle, and behavior checks."""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(command: list[str]) -> int:
    print("+ " + " ".join(command), flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def discover_tests(root: Path) -> list[Path]:
    return sorted(
        path
        for path in (root / "tools/tests").rglob("*_test.py")
        if path.name.startswith(("targeted_operations", "top_lifecycle_probe"))
    )


def main() -> int:
    generator = [
        sys.executable,
        "tools/generators/generate_targeted_operations.py",
        "--check",
    ]
    if run(generator):
        return 1

    tests = discover_tests(ROOT)
    if not tests:
        print("No Targeted Operations tests discovered", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="targeted-operations-audit-") as temporary:
        return run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "--basetemp",
                str(Path(temporary) / "pytest"),
                *(path.relative_to(ROOT).as_posix() for path in tests),
            ]
        )


if __name__ == "__main__":
    raise SystemExit(main())
