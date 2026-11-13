#!/usr/bin/env python3
"""Opt-in, report-only checks for explicit AI attribution (issue #4549)."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared_utils import validation_config

TEXT_SUFFIXES = {
    ".txt",
    ".yml",
    ".yaml",
    ".md",
    ".mdx",
    ".py",
    ".lua",
    ".gui",
    ".gfx",
    ".asset",
    ".mod",
    ".json",
    ".toml",
    ".sh",
    ".ps1",
}
MAX_BYTES = 5 * 1024 * 1024
IDENTITY = re.compile(
    r"(?:claude[\s_-]*code|(?:openai[\s_-]+)?codex|chatgpt|github[\s_-]+copilot"
    r"|claude[\s_-]+(?:opus|sonnet|haiku)(?:[\s_-]+\d+(?:\.\d+)*)?"
    r"(?:\s*\(\d+[km]?\s+context\))?)",
    re.IGNORECASE,
)
ATTRIBUTION = re.compile(
    r"^(?:(?P<trailer>co[- ]authored[- ]by)\s*:\s*"
    r"|(?P<header>author)\s*(?::|\bis\b)\s*"
    r"|(?P<footer>generated\s+(?:with|by))\s+)(?P<identity>.+?)\s*$",
    re.IGNORECASE,
)
HUNK = re.compile(rb"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)


class ScanError(Exception):
    """The selected inputs could not be completely checked."""


def classify(line):
    """Recognize explicit labels, never prose style or incidental tool mentions."""
    line = line.lstrip("\ufeff \t").replace("**", "").replace("`", "")
    line = re.sub(r"^(?:<!--|/\*|//|\#+|\*|--|;)\s*", "", line)
    line = re.sub(r"\s*(?:-->|\*/)\s*$", "", line)
    line = line.removeprefix("🤖").strip()
    match = ATTRIBUTION.fullmatch(line)
    if not match:
        return None
    identity = match["identity"]
    identity = re.sub(r"\[([^\]]+)\]\([^\s)]+\)", r"\1", identity)
    identity = re.sub(r"\s*<[^<>\s]+@[^<>\s]+>\s*$", "", identity)
    identity = identity.rstrip(". ")
    if not IDENTITY.fullmatch(identity):
        return None
    kind = next(name for name in ("trailer", "header", "footer") if match[name])
    return f"ai-{kind}"


def git(repo, *args):
    result = subprocess.run(
        ["git", "--no-pager", "-C", str(repo), *args],
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode:
        # Do not echo commit contents, author metadata, or untrusted stderr.
        raise ScanError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout


def decode(data, source):
    if len(data) > MAX_BYTES:
        raise ScanError(f"input exceeds {MAX_BYTES} bytes: {source!r}")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ScanError(f"input is not UTF-8: {source!r}") from error


def findings(text, source, numbers=None):
    lines = text.split("\n")
    selected = range(1, len(lines) + 1) if numbers is None else numbers
    return [
        (source, number, rule)
        for number in selected
        if (rule := classify(lines[number - 1].rstrip("\r")))
    ]


def exemptions():
    paths = validation_config("check_ai_attribution", "exempt_paths")
    if not isinstance(paths, dict) or any(
        not isinstance(path, str) or not isinstance(reason, str) or not reason.strip()
        for path, reason in paths.items()
    ):
        raise ScanError("every attribution exemption needs a path and a reason")
    return paths


def changed_blobs(raw):
    """Parse NUL-delimited raw records, including both paths on renames."""
    parts = iter(raw.split(b"\0")[:-1])
    for record in parts:
        old_mode, new_mode, old, new, status = record.decode("ascii").split()
        path = next(parts).decode("utf-8")
        if status.startswith(("R", "C")):
            path = next(parts).decode("utf-8")
        yield old_mode[1:], new_mode, old, new, status, path


def added_findings(repo, revisions):
    raw = git(
        repo,
        "diff",
        "--raw",
        "-z",
        "--no-abbrev",
        "--find-renames",
        "--no-ext-diff",
        "--no-textconv",
        *revisions,
        "--",
    )
    results, skipped = [], []
    allowed = exemptions()
    for old_mode, mode, old, new, status, path in changed_blobs(raw):
        if status == "D":
            continue
        if status == "U":
            raise ScanError("resolve unmerged index entries before checking")
        reason = allowed.get(path)
        if reason is None and path.startswith("resources/"):
            reason = "reference-only external material"
        if reason is None and path.startswith("localisation/"):
            if not path.startswith("localisation/english/") and not path.endswith(
                "_l_english.yml"
            ):
                reason = "non-English localisation is outside review scope"
        if reason is None and mode not in {"100644", "100755"}:
            reason = "non-regular file (symlink or submodule)"
        if reason is None and Path(path).suffix.lower() not in TEXT_SUFFIXES:
            reason = "outside the prototype text suffix set"
        if reason:
            skipped.append((path, reason))
            continue
        size = int(git(repo, "cat-file", "-s", new))
        if size > MAX_BYTES:
            raise ScanError(f"text blob exceeds {MAX_BYTES} bytes: {path!r}")
        data = git(repo, "cat-file", "blob", new)
        if b"\0" in data:
            skipped.append((path, "binary blob (NUL byte)"))
            continue
        text = decode(data, path)
        numbers = None
        if status != "A" and old_mode in {"100644", "100755"}:
            patch = git(
                repo,
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--text",
                "--unified=0",
                "--inter-hunk-context=0",
                "--no-color",
                old,
                new,
                "--",
            )
            numbers = [
                number
                for match in HUNK.finditer(patch)
                for number in range(int(match[1]), int(match[1]) + int(match[2] or 1))
            ]
        results.extend(findings(text, path, numbers))
    return results, skipped


def scan(repo, base=None, head="HEAD"):
    """Check the index, or new branch messages and merge-base-to-head additions."""
    root = git(repo, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    results = []
    if base is None:
        if git(root, "ls-files", "--unmerged", "-z"):
            raise ScanError("resolve unmerged index entries before checking")
        revisions = ["--cached"]
    else:
        if git(root, "rev-parse", "--is-shallow-repository").strip() == b"true":
            raise ScanError("branch checking requires complete history; fetch it first")
        pins = [
            git(root, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
            .decode("ascii")
            .strip()
            for ref in (base, head)
        ]
        ancestor = git(root, "merge-base", *pins).decode("ascii").strip()
        commits = git(root, "rev-list", f"{pins[0]}..{pins[1]}").splitlines()
        for commit in commits:
            sha = commit.decode("ascii")
            message = git(
                root, "show", "--no-patch", "--format=%B", "--encoding=UTF-8", sha
            )
            results.extend(findings(decode(message, sha), f"commit {sha[:12]}"))
        revisions = [ancestor, pins[1]]
    added, skipped = added_findings(root, revisions)
    return results + added, skipped


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--commit-msg", type=Path, help="check a UTF-8 message file")
    modes.add_argument("--staged", action="store_true", help="check index additions")
    modes.add_argument(
        "--base", help="check new commits and additions against this base"
    )
    parser.add_argument("--head", default="HEAD", help="branch head, with --base only")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    if args.head != "HEAD" and args.base is None:
        parser.error("--head requires --base")
    try:
        if args.commit_msg:
            with args.commit_msg.open("rb") as handle:
                data = handle.read(MAX_BYTES + 1)
            if b"\0" in data:
                raise ScanError("commit message contains NUL bytes")
            results = findings(decode(data, str(args.commit_msg)), str(args.commit_msg))
            skipped = []
        else:
            results, skipped = scan(args.repo, args.base, args.head)
    except (
        ScanError,
        OSError,
        ValueError,
        KeyError,
        subprocess.TimeoutExpired,
    ) as error:
        print(
            f"ERROR: attribution check incomplete: {ascii(str(error))}", file=sys.stderr
        )
        return 2
    for source, number, rule in results:
        print(
            f"WARNING {json.dumps(source)}:{number}: {rule}: review explicit AI attribution"
        )
    for path, reason in skipped:
        print(f"SKIP {json.dumps(path)}: {reason}")
    print(
        f"Report only: {len(results)} finding(s); {len(skipped)} skipped path(s). No files changed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
