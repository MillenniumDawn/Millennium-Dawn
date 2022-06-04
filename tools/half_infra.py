# Written by Yard1
# Usage: python half_infra.py "PATH_TO_HISTORY/STATES"

from pathlib import Path
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("path", type=Path)
args = parser.parse_args()

pathlist = args.path.glob("*.txt")
for path in pathlist:
    with open(path, "r") as f:
        data = f.read()
    with open(path, "w") as f:
        f.write(
            re.sub(
                r"(infrastructure\s*=\s*)(\d+)",
                lambda m: f"{m.group(1)}{int(m.group(2))//2}",
                data,
            )
        )