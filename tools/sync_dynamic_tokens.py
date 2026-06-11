#!/usr/bin/env python3
import argparse
import os
import re

DEFAULT_LOG = os.path.expanduser(
    "~/.local/share/Paradox Interactive/Hearts of Iron IV/logs/error.log"
)
DEFAULT_OUTPUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "common",
    "synchronized_dynamic_tokens",
    "MD_tokens.txt",
)

TOKEN_RE = re.compile(r"Token (\S+) is a dynamic token")


def main():
    parser = argparse.ArgumentParser(
        description="Append dynamic-token OOS warnings from a HOI4 error log to a tokens file."
    )
    parser.add_argument(
        "log", nargs="?", default=DEFAULT_LOG, help="path to error.log (default: HOI4 logs dir)"
    )
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT, help="tokens file to append to (default: MD_tokens.txt)"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.log):
        parser.error(f"Log file not found: {args.log}")

    found = {}  # ordered set: token -> None
    saw_phrase = False
    with open(args.log, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "dynamic token" not in line:
                continue
            saw_phrase = True
            m = TOKEN_RE.search(line)
            if m:
                found[m.group(1)] = None

    if not found:
        if saw_phrase:
            print("Found 'dynamic token' lines but none matched the expected format; the log wording may have changed.")
        else:
            print("No dynamic-token warnings found in the log.")
        return

    raw = ""
    if os.path.isfile(args.output):
        with open(args.output, encoding="utf-8", errors="replace") as f:
            raw = f.read()
    existing = {ln.strip() for ln in raw.splitlines() if ln.strip()}

    missing = [t for t in found if t not in existing]
    if not missing:
        print(f"All {len(found)} tokens already present. Nothing to add.")
        return

    with open(args.output, "a", encoding="utf-8") as f:
        if raw and not raw.endswith("\n"):
            f.write("\n")
        for t in missing:
            f.write(t + "\n")

    print(f"Added {len(missing)} new token(s) to {args.output}:")
    for t in missing:
        print(f"  {t}")


if __name__ == "__main__":
    main()
