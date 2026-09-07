"""Adapt standalone CI checks to the impact artifact contract."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List

SOURCES = {
    "localization-encoding": "validate_localization_encoding.py",
    "mod-encoding": "validate_mod_encoding.py",
}


def _files(mod_path: Path, validator: str) -> List[str]:
    if validator == "localization-encoding":
        patterns = (
            mod_path / "localisation" / "english" / "*.yml",
            mod_path / "localisation" / "*_l_english.yml",
        )
        files = {
            path for pattern in patterns for path in pattern.parent.glob(pattern.name)
        }
        files.update((mod_path / "localisation" / "english").rglob("*.yml"))
        return [str(path) for path in sorted(files)]
    return [
        str(path)
        for path in sorted(mod_path.rglob("*.mod"))
        if "resources" not in path.parts
    ]


def _issues(text: str, mod_path: Path, validator: str) -> list:
    issues = []
    for line in text.splitlines():
        line = line.strip()
        if ": " not in line:
            continue
        filename, message = line.split(": ", 1)
        path = Path(filename)
        if not path.is_absolute():
            continue
        try:
            relative = path.resolve().relative_to(mod_path.resolve()).as_posix()
        except ValueError:
            continue
        issues.append(
            {
                "severity": "error",
                "category": validator,
                "message": message,
                "file": relative,
                "line": 0,
                "validator": validator,
            }
        )
    return issues


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validator", choices=sorted(SOURCES), required=True)
    parser.add_argument("--path", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--workers", type=int)
    args = parser.parse_args(argv)

    mod_path = Path(args.path).resolve()
    source = Path(__file__).resolve().parents[1] / "linting" / SOURCES[args.validator]
    command = [sys.executable, str(source), *_files(mod_path, args.validator)]
    result = subprocess.run(command, cwd=mod_path, capture_output=True, text=True)
    log = result.stdout + result.stderr
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8", newline="") as handle:
        handle.write(log)
    with open(output.with_suffix(".json"), "w", encoding="utf-8", newline="") as handle:
        json.dump(_issues(result.stderr, mod_path, args.validator), handle)
        handle.write("\n")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
