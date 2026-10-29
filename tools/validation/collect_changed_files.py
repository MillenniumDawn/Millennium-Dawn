"""Convert `git diff --name-status -z` output into one path per line.

Renames surface as old and new paths, so a renamed validator is dropped from
the impact selection while its replacement is selected. Reads stdin, writes
stdout — the impact workflow pipes straight through."""

import sys


def parse_name_status(data: bytes) -> list:
    fields = data.decode("utf-8", "replace").split("\0")
    paths = []
    index = 0
    while index < len(fields):
        status = fields[index]
        if not status:
            index += 1
            continue
        # R/C records carry the old and the new path.
        count = 2 if status[0] in "RC" else 1
        paths.extend(fields[index + 1 : index + 1 + count])
        index += 1 + count
    return paths


def main() -> int:
    paths = parse_name_status(sys.stdin.buffer.read())
    with open(sys.stdout.fileno(), "w", encoding="utf-8", newline="") as handle:
        for path in paths:
            handle.write(path + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
