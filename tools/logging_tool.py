#!/usr/bin/env python3

"""
Logging Tool

Adds or removes debug log lines in the mod's focus, event, idea, decision, and
technology files. A log is only added as the first statement of an existing
effect block that runs something; an empty or log-only block is never created
or filled (#4456).

Usage:
    python3 logging_tool.py <mod_path> [--remove]
"""

import argparse
import builtins
import functools
import io
import os
import re
import sys
import time
from os import listdir

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_utils import (
    atomic_write_text,
    blank_quoted_strings,
    extract_block,
    strip_inline_comment,
)

_builtin_open = builtins.open
_pending_outputs: list["_AtomicOutput"] = []

_OPENER_RE = re.compile(r"^\s*(\w+)\s*=\s*\{")
_ID_RE = re.compile(r"^\s*id\s*=\s*(\S+)")
_LOG_RE = re.compile(r'log\s*=\s*"')
_TARGETED_RE = re.compile(r"^\s*(target_trigger|targets)\s*=")


class _AtomicOutput(io.StringIO):
    def __init__(self, path, encoding):
        super().__init__()
        self.path = path
        self._encoding = encoding
        _pending_outputs.append(self)

    def close(self):
        if not self.closed:
            atomic_write_text(self.path, self.getvalue(), encoding=self._encoding)
        super().close()


def open(path, mode="r", *args, **kwargs):
    if "w" in mode and "b" not in mode:
        return _AtomicOutput(path, kwargs.get("encoding", "utf-8"))
    return _builtin_open(path, mode, *args, **kwargs)


def _flush_atomic_outputs(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        start = len(_pending_outputs)
        try:
            return function(*args, **kwargs)
        finally:
            outputs = _pending_outputs[start:]
            del _pending_outputs[start:]
            for output in outputs:
                output.close()

    return wrapped


def _read_lines_if_large_enough(path, *, min_size=100):
    try:
        if os.path.getsize(path) < min_size:
            return None
        with open(path, "r", encoding="utf-8") as input_file:
            return input_file.readlines()
    except OSError:
        return None


def _read_lines_or_warn(path, filename, *, min_size=100, encoding="utf-8"):
    try:
        if os.path.getsize(path) < min_size:
            return None
        with open(path, "r", encoding=encoding) as input_file:
            return input_file.readlines()
    except (OSError, UnicodeError) as e:
        print(f"Could not read {filename}: {e}")
        return None


def _iter_directory_paths(cpath, *parts):
    directory = os.path.join(cpath, *parts)
    for filename in listdir(directory):
        yield filename, os.path.join(directory, filename)


def _open_output(path, *, dry_run):
    if dry_run:
        return io.StringIO()
    try:
        return open(path, "w", encoding="utf-8", newline="")
    except OSError:
        raise


def _open_output_or_raise(path, filename, *, dry_run):
    try:
        return _open_output(path, dry_run=dry_run)
    except OSError as e:
        print(f"Could not write {filename}: {e}")
        raise


def _update_brace_level(level, line):
    code = blank_quoted_strings(line)
    if "{" in code:
        level += code.count("{")
    if "}" in code:
        level -= code.count("}")
    return level


def _needs_log(block):
    """True when an effect block runs something and does not log it yet."""
    body = "\n".join(strip_inline_comment(line) for line in block)
    if "}" not in body:
        return False
    inner = body[body.index("{") + 1 : body.rindex("}")]
    runs_effect = False
    for line in inner.splitlines():
        stripped = line.strip()
        if _LOG_RE.match(stripped):
            return False
        if stripped:
            runs_effect = True
    return runs_effect


def _find_effect_targets(lines, *, entity, effect_keys):
    """Yield (entity_index, effect_index, key) for every effect block, nested one
    level under an entity, that runs something but has no log."""
    level = 0
    entity_index = None
    entity_level = None
    for index, source_line in enumerate(lines):
        if source_line.strip().startswith("#"):
            continue
        line = strip_inline_comment(source_line)
        match = _OPENER_RE.match(line)
        if match and entity(match.group(1), level):
            entity_index = index
            entity_level = level
        elif (
            match
            and entity_index is not None
            and level == entity_level + 1
            and match.group(1) in effect_keys
            and _needs_log(extract_block(lines, index)[0])
        ):
            yield entity_index, index, match.group(1)
        level = _update_brace_level(level, line)


def _entity_id(lines, entity_index, effect_index):
    """The `id = ...` value declared between an entity's opener and its effect block."""
    for line in lines[entity_index + 1 : effect_index]:
        match = _ID_RE.match(strip_inline_comment(line))
        if match:
            return match.group(1)
    return None


def _entity_name(lines, entity_index):
    return _OPENER_RE.match(lines[entity_index]).group(1)


def _logged_opener(line, log_text):
    """Return the opener with the log as its first statement; a packed block is
    exploded so the log lands inside its braces."""
    code = strip_inline_comment(line)
    indent = code[: len(code) - len(code.lstrip("\t"))]
    log_line = f'{indent}\tlog = "[GetDateText]: [Root.GetName]: {log_text}"\n'
    head, inner = code.split("{", 1)
    if "}" not in inner:
        return line + log_line
    comment = line[len(code) :].strip()
    inner = inner[: inner.rindex("}")].strip()
    opener = f"{head}{{" + (f" {comment}" if comment else "") + "\n"
    return f"{opener}{log_line}{indent}\t{inner}\n{indent}}}\n"


def _add_logs(
    cpath,
    parts,
    *,
    entity,
    effect_keys,
    log_text,
    encoding="utf-8",
    skip=None,
    dry_run=False,
):
    changes = 0
    for filename, path in _iter_directory_paths(cpath, *parts):
        if not filename.endswith(".txt") or (skip and skip(filename)):
            continue
        lines = _read_lines_or_warn(path, filename, encoding=encoding)
        if lines is None:
            continue
        targets = {}
        for entity_index, effect_index, key in _find_effect_targets(
            lines, entity=entity, effect_keys=effect_keys
        ):
            text = log_text(lines, entity_index, effect_index, key)
            if text is not None:
                targets[effect_index] = text
        if not targets:
            continue
        with _open_output_or_raise(path, filename, dry_run=dry_run) as outputfile:
            for index, line in enumerate(lines):
                if index in targets:
                    outputfile.write(_logged_opener(line, targets[index]))
                else:
                    outputfile.write(line)
        changes += len(targets)
    return changes


def _focus_log_text(lines, entity_index, effect_index, key):
    focus_id = _entity_id(lines, entity_index, effect_index)
    return None if focus_id is None else f"Focus {focus_id}"


@_flush_atomic_outputs
def focus_add(cpath, dry_run=False):
    return _add_logs(
        cpath,
        ("common", "national_focus"),
        entity=lambda key, level: key in ("focus", "shared_focus"),
        effect_keys={"completion_reward"},
        log_text=_focus_log_text,
        dry_run=dry_run,
    )


@_flush_atomic_outputs
def focus_remove(cpath, dry_run=False):
    changes = 0
    for filename, path in _iter_directory_paths(cpath, "common", "national_focus"):
        if ".txt" in filename:
            lines = _read_lines_if_large_enough(path)
            if lines is None:
                continue
            outputfile = _open_output(path, dry_run=dry_run)
            outputfile.truncate()
            for line in lines:
                if 'log = "[GetDateText]' not in line:
                    outputfile.write(line)
                else:
                    outputfile.write("")
                    changes += 1
    return changes


def _event_log_text(lines, entity_index, effect_index, key):
    event_id = _entity_id(lines, entity_index, effect_index)
    return None if event_id is None else f"event {event_id}"


@_flush_atomic_outputs
def event_add(cpath, dry_run=False):
    return _add_logs(
        cpath,
        ("events",),
        entity=lambda key, level: level == 0,
        effect_keys={"immediate"},
        log_text=_event_log_text,
        encoding="utf-8-sig",
        dry_run=dry_run,
    )


@_flush_atomic_outputs
def event_remove(cpath, dry_run=False):
    changes = 0
    for filename, path in _iter_directory_paths(cpath, "events"):
        if ".txt" in filename:
            lines = _read_lines_or_warn(path, filename, encoding="utf-8-sig")
            if lines is None:
                continue
            outputfile = _open_output(path, dry_run=dry_run)
            outputfile.truncate()
            for line in lines:
                if 'log = "[GetDateText]' not in line:
                    outputfile.write(line)
                else:
                    changes += 1
    return changes


def _idea_log_text(lines, entity_index, effect_index, key):
    verb = "add" if key == "on_add" else "remove"
    return f"{verb} idea {_entity_name(lines, entity_index)}"


@_flush_atomic_outputs
def idea_add(cpath, dry_run=False):
    return _add_logs(
        cpath,
        ("common", "ideas"),
        entity=lambda key, level: level == 2,
        effect_keys={"on_add", "on_remove"},
        log_text=_idea_log_text,
        skip=lambda filename: filename.startswith("_"),
        dry_run=dry_run,
    )


@_flush_atomic_outputs
def idea_remove(cpath, dry_run=False):
    changes = 0
    for filename, path in _iter_directory_paths(cpath, "common", "ideas"):
        if ".txt" in filename and not filename.startswith("_"):
            try:
                size = os.path.getsize(path)
                with open(path, "r", encoding="utf-8") as input_file:
                    lines = input_file.readlines()
            except OSError as e:
                print(f"Could not read {filename}: {e}")
                continue
            if size < 100:
                continue
            outputfile = _open_output_or_raise(path, filename, dry_run=dry_run)
            outputfile.truncate()
            for line in lines:
                if 'log = "[GetDateText]' not in line:
                    outputfile.write(line)
                else:
                    outputfile.write("")
                    changes += 1
    return changes


_DECISION_LOG_PREFIX = {
    "complete_effect": "Decision",
    "remove_effect": "Decision remove",
    "timeout_effect": "Decision timeout",
}


def _decision_log_text(lines, entity_index, effect_index, key):
    name = _entity_name(lines, entity_index)
    decision = extract_block(lines, entity_index)[0]
    if any(_TARGETED_RE.match(line) for line in decision):
        name += " target: [From.GetName]"
    return f"{_DECISION_LOG_PREFIX[key]} {name}"


@_flush_atomic_outputs
def decision_add(cpath, dry_run=False):
    return _add_logs(
        cpath,
        ("common", "decisions"),
        entity=lambda key, level: level == 1,
        effect_keys=set(_DECISION_LOG_PREFIX),
        log_text=_decision_log_text,
        skip=lambda filename: "categories" in filename,
        dry_run=dry_run,
    )


@_flush_atomic_outputs
def decision_remove(cpath, dry_run=False):
    changes = 0
    for filename, path in _iter_directory_paths(cpath, "common", "decisions"):
        if ".txt" in filename and "categories" not in filename:
            lines = _read_lines_or_warn(path, filename)
            if lines is None:
                continue
            outputfile = _open_output_or_raise(path, filename, dry_run=dry_run)
            outputfile.truncate()
            for line in lines:
                if 'log = "[GetDateText]' not in line:
                    outputfile.write(line)
                else:
                    changes += 1
                    if "complete_effect" in line:
                        outputfile.write("complete_effect = {\n\t\t}\n")
                    else:
                        outputfile.write("")
    return changes


def _tech_log_text(lines, entity_index, effect_index, key):
    return f"add tech {_entity_name(lines, entity_index)}"


@_flush_atomic_outputs
def tech_add(cpath, dry_run=False):
    return _add_logs(
        cpath,
        ("common", "technologies"),
        entity=lambda key, level: level == 1,
        effect_keys={"on_research_complete"},
        log_text=_tech_log_text,
        dry_run=dry_run,
    )


@_flush_atomic_outputs
def tech_remove(cpath, dry_run=False):
    changes = 0
    for filename, path in _iter_directory_paths(cpath, "common", "technologies"):
        if ".txt" in filename:
            lines = _read_lines_or_warn(path, filename)
            if lines is None:
                continue
            outputfile = _open_output_or_raise(path, filename, dry_run=dry_run)
            outputfile.truncate()
            for x in range(len(lines)):
                line = lines[x]
                if 'log = "[GetDateText]' in line:
                    outputfile.write("")
                    changes += 1
                elif (
                    "on_research_complete" in line
                    and 'log = "[GetDateText]' in lines[x + 1]
                    and ("}" in lines[x + 2] or "}" in lines[x + 1])
                ):
                    print("Deleted logging at line", x, "in file", filename)
                    outputfile.write("")
                    changes += 1
                elif 'log = "[GetDateText]' in lines[x - 1] and "}" in line:
                    outputfile.write("")
                    changes += 1
                else:
                    outputfile.write(line)
    return changes


def main():
    parser = argparse.ArgumentParser(
        description="Add or remove logging from HOI4 mod files"
    )
    parser.add_argument("path", help="Path to the mod directory")
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove existing logs instead of adding them",
    )
    parser.add_argument(
        "--skip-events", action="store_true", help="Skip processing events"
    )
    parser.add_argument(
        "--skip-focus", action="store_true", help="Skip processing national focus"
    )
    parser.add_argument(
        "--skip-ideas", action="store_true", help="Skip processing ideas"
    )
    parser.add_argument(
        "--skip-decisions", action="store_true", help="Skip processing decisions"
    )
    parser.add_argument(
        "--skip-tech", action="store_true", help="Skip processing technologies"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without modifying any files",
    )

    args = parser.parse_args()

    # argparse splits an unquoted path on spaces; rejoin the pieces here.
    cpath = args.path
    if len(sys.argv) > 2:
        path_start = None
        for i, arg in enumerate(sys.argv[1:], 1):
            if not arg.startswith("--") and path_start is None:
                path_start = i
                break
        if path_start and not os.path.exists(cpath):
            path_parts = [cpath]
            for arg in sys.argv[path_start + 1 :]:
                if not arg.startswith("--"):
                    path_parts.append(arg)
                else:
                    break
            cpath = " ".join(path_parts)

    print(f"Processing mod at: {cpath}")
    mode = "Removing" if args.remove else "Adding"
    print(f"Mode: {mode} logs{' (dry run)' if args.dry_run else ''}")

    total_changes = 0
    start = time.time()

    if not args.skip_events:
        print("Processing events...")
        fn = event_remove if args.remove else event_add
        total_changes += fn(cpath, dry_run=args.dry_run)

    if not args.skip_focus:
        print("Processing national focus...")
        fn = focus_remove if args.remove else focus_add
        total_changes += fn(cpath, dry_run=args.dry_run)

    if not args.skip_ideas:
        print("Processing ideas...")
        fn = idea_remove if args.remove else idea_add
        total_changes += fn(cpath, dry_run=args.dry_run)

    if not args.skip_decisions:
        print("Processing decisions...")
        fn = decision_remove if args.remove else decision_add
        total_changes += fn(cpath, dry_run=args.dry_run)

    if not args.skip_tech:
        print("Processing technologies...")
        fn = tech_remove if args.remove else tech_add
        total_changes += fn(cpath, dry_run=args.dry_run)

    print("Total Time: %.3f ms" % ((time.time() - start) * 1000))
    verb = "Would modify" if args.dry_run else "Modified"
    print(f"{verb} {total_changes} entries")
    print("Processing complete!")


if __name__ == "__main__":
    main()
