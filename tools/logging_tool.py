#!/usr/bin/env python3

"""
Logging Tool

Adds or removes debug log lines in the mod's focus, event, idea, decision, and
technology files.

Usage:
    python3 logging_tool.py <mod_path> [--remove]
"""

import argparse
import io
import os
import re
import sys
import time
from codecs import open
from os import listdir

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared_utils import strip_inline_comment


def check_triggered(line_number, lines):
    if (
        line_number == len(lines)
        or line_number == len(lines) - 1
        or line_number == len(lines) - 2
    ):
        return True
    if "}" in lines[line_number + 2] or "days" in lines[line_number + 2]:
        return True
    if "}" in lines[line_number + 1] or "days" in lines[line_number + 1]:
        return True
    if "}" in lines[line_number] or "days" in lines[line_number]:
        return True
    for i in range(line_number, len(lines)):
        string = lines[i].strip()
        if string.startswith("#") is True:
            continue
        if string.startswith("}") is True or "days" in string:
            return True
        elif string != "":
            return False
    return False


def focus_add(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "common", "national_focus")):
        if ".txt" in filename:
            file = open(
                os.path.join(cpath, "common", "national_focus", filename), "r", "utf-8"
            )
            size = os.path.getsize(
                os.path.join(cpath, "common", "national_focus", filename)
            )
            if size < 100:
                continue
            lines = file.readlines()
            line_number = 0
            ids = []
            idss = []
            new_focus = False
            find_coml = False
            shared_focus = False
            shared_focuseseses = []
            for line in lines:
                line_number += 1
                if line.strip().startswith("#"):
                    continue
                if "#" in line:
                    line = strip_inline_comment(line)
                if "focus = {" in line:
                    if "shared_focus" in line:
                        shared_focus = True
                    new_focus = True
                    if find_coml is True:
                        find_coml = False
                        ids.pop()
                if line.strip().startswith("id") and new_focus is True:
                    new_focus = False
                    find_coml = True
                    focus_id = line.split("=")[1].strip()
                    if "#" in focus_id:
                        focus_id = strip_inline_comment(focus_id).strip()
                    ids.append(focus_id)
                    if shared_focus:
                        shared_focuseseses.append(focus_id)
                        shared_focus = False
                if "completion_reward" in line and find_coml is True:
                    find_coml = False
                    idss.append(line_number)
                if 'log = "[GetDateText]:' in line:
                    if idss != [] or ids != []:
                        idss.pop()
                        ids.pop()
            line_number = 0
            file.close()
            outputfile = (
                io.StringIO()
                if dry_run
                else open(
                    os.path.join(cpath, "common", "national_focus", filename),
                    "w",
                    "utf-8",
                )
            )
            outputfile.truncate()
            for line in lines:
                line_number += 1
                if line_number in idss:
                    whitespace = "\t\t"
                    focus_id = ids[idss.index(line_number)]
                    if focus_id in ["{", "}"]:
                        focus_id = "Error, focus name not found"
                    if focus_id in shared_focuseseses:
                        whitespace = whitespace[: len(whitespace) - 1]
                    if "}" in line:
                        temp = line.split("{")
                        replacement_text = (
                            temp[0]
                            + "{\n"
                            + whitespace
                            + '\tlog = "[GetDateText]: [Root.GetName]: Focus '
                            + focus_id
                            + '"\n'
                            + "{".join(temp)[len(temp[0]) + 1 :]
                            + "\n"
                        )
                    else:
                        replacement_text = (
                            whitespace
                            + "completion_reward = {\n"
                            + whitespace
                            + '\tlog = "[GetDateText]: [Root.GetName]: Focus '
                            + focus_id
                            + '"\n'
                        )
                    outputfile.write(replacement_text)
                    changes += 1
                else:
                    outputfile.write(line)
    return changes


def focus_remove(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "common", "national_focus")):
        if ".txt" in filename:
            outputfile = open(
                os.path.join(cpath, "common", "national_focus", filename), "r", "utf-8"
            )
            size = os.path.getsize(
                os.path.join(cpath, "common", "national_focus", filename)
            )
            if size < 100:
                continue
            lines = outputfile.readlines()
            outputfile.close()
            outputfile = (
                io.StringIO()
                if dry_run
                else open(
                    os.path.join(cpath, "common", "national_focus", filename),
                    "w",
                    "utf-8",
                )
            )
            outputfile.truncate()
            for line in lines:
                if 'log = "[GetDateText]' not in line:
                    outputfile.write(line)
                else:
                    outputfile.write("")
                    changes += 1
    return changes


def event_add(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "events")):
        if ".txt" in filename:
            file = open(os.path.join(cpath, "events", filename), "r", "utf-8-sig")
            try:
                lines = file.readlines()
            except UnicodeDecodeError:
                print(filename)
                continue
            size = os.path.getsize(os.path.join(cpath, "events", filename))
            if size < 100:
                continue
            event_id = None
            line_number = 0
            triggered = False
            ids = []
            idss = []

            for line in lines:
                line_number += 1
                if line.strip().startswith("#") or "immediate = {log = " in line:
                    continue
                if "#" in line:
                    line = strip_inline_comment(line)
                if (
                    "country_event" in line
                    or "news_event" in line
                    or "unit_leader_event" in line
                    or "state_event" in line
                ):
                    if check_triggered(line_number, lines) is False:
                        if "}" not in line or "days" not in line:
                            new_event = True
                            if event_id is not None:
                                triggered = False
                        else:
                            triggered = True
                            new_event = False
                    else:
                        triggered = True
                        new_event = False
                if (
                    line.strip().startswith("id")
                    and new_event is True
                    and "immediate = {log =" not in lines[line_number + 1]
                ):
                    if "log = " not in lines[line_number + 1]:
                        if triggered is False:
                            new_event = False
                            event_id = line.split("=")[1].strip()
                            idss.append(event_id)
                            ids.append(line_number)
                        else:
                            triggered = False
            line_number = 0
            file.close()
            outputfile = (
                io.StringIO()
                if dry_run
                else open(os.path.join(cpath, "events", filename), "w", "utf-8-sig")
            )
            outputfile.truncate()
            for line in lines:
                line_number += 1
                if line_number in ids:
                    extra = ""
                    event_id = idss[ids.index(line_number)]
                    if "#" in line:
                        extra = " #" + line.split("#")[len(line.split("#")) - 1].strip()
                    if "." not in event_id:
                        outputfile.write(line)
                        continue
                    replacement_text = (
                        "\tid = "
                        + event_id
                        + extra
                        + '\n\timmediate = {log = "[GetDateText]: [Root.GetName]: event '
                        + event_id
                        + '"}\n'
                    )
                    outputfile.write(replacement_text)
                    changes += 1
                else:
                    outputfile.write(line)
    return changes


def event_remove(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "events")):
        if ".txt" in filename:
            outputfile = open(os.path.join(cpath, "events", filename), "r", "utf-8-sig")
            size = os.path.getsize(os.path.join(cpath, "events", filename))
            if size < 100:
                continue
            try:
                lines = outputfile.readlines()
            except UnicodeDecodeError:
                print(filename)
                continue
            outputfile.close()
            outputfile = (
                io.StringIO()
                if dry_run
                else open(os.path.join(cpath, "events", filename), "w", "utf-8-sig")
            )
            outputfile.truncate()
            for line in lines:
                if "immediate = {log = " not in line:
                    outputfile.write(line)
                else:
                    changes += 1
                    if "}" in line:
                        outputfile.write("")
                    else:
                        outputfile.write("\timmediate = {\n")
    return changes


def idea_add(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "common", "ideas")):
        if ".txt" in filename and filename.startswith("_") is False:
            file = open(os.path.join(cpath, "common", "ideas", filename), "r", "utf-8")
            size = os.path.getsize(os.path.join(cpath, "common", "ideas", filename))
            if size < 100:
                continue
            level = 0
            line_number = 0
            ids = []
            lines = file.readlines()
            for line in lines:
                line_number += 1
                if "#" in line:
                    if line.strip().startswith("#") is True:
                        continue
                    else:
                        line = strip_inline_comment(line)
                re.sub(r'".+?"', "", line)
                if "= {" in line:
                    if level == 2:
                        if "on_add = { log = " not in lines[line_number]:
                            ids.append(line_number)
                if "{" in line:
                    level += line.count("{")
                if "}" in line:
                    level -= line.count("}")
            file.close()
            line_number = 0
            outputfile = (
                io.StringIO()
                if dry_run
                else open(
                    os.path.join(cpath, "common", "ideas", filename), "w", "utf-8"
                )
            )
            outputfile.truncate()
            for line in lines:
                line_number += 1
                if line_number in ids:
                    extra = ""
                    if "#" in line:
                        line = line.strip()
                        extra = "#" + line.split("#")[len(line.split("#")) - 1].strip()
                    idea_id = line.split("=")[0].strip()
                    replacement_text = (
                        "\t\t"
                        + idea_id
                        + " = { "
                        + extra
                        + '\n\t\t\ton_add = { log = "[GetDateText]: [Root.GetName]: add idea '
                        + idea_id
                        + '" }\n'
                    )
                    outputfile.write(replacement_text)
                    changes += 1
                else:
                    outputfile.write(line)
    return changes


def idea_remove(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "common", "ideas")):
        if ".txt" in filename and filename.startswith("_") is False:
            outputfile = open(
                os.path.join(cpath, "common", "ideas", filename), "r", "utf-8"
            )
            size = os.path.getsize(os.path.join(cpath, "common", "ideas", filename))
            if size < 100:
                continue
            lines = outputfile.readlines()
            outputfile.close()
            outputfile = (
                io.StringIO()
                if dry_run
                else open(
                    os.path.join(cpath, "common", "ideas", filename), "w", "utf-8"
                )
            )
            outputfile.truncate()
            for line in lines:
                if "on_add = { log = " not in line:
                    outputfile.write(line)
                else:
                    outputfile.write("")
                    changes += 1
    return changes


def decision_add(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "common", "decisions")):
        if "categories" in filename:
            continue
        if ".txt" in filename:
            with open(
                os.path.join(cpath, "common", "decisions", filename), "r", "utf-8"
            ) as file:
                if (
                    os.path.getsize(
                        os.path.join(cpath, "common", "decisions", filename)
                    )
                    < 100
                ):
                    continue
                lines = file.readlines()
                level = 0
                found_decisions = {}
                for line_number, line in enumerate(lines):
                    if "#" in line:
                        if line.strip().startswith("#") is True:
                            continue
                        else:
                            line = strip_inline_comment(line)
                    if ("= {" in line or "={" in line) and level == 1:
                        latest_found = line_number
                        found_decisions[line_number] = [0, 0, 0, False]
                    if "complete_effect" in line:
                        found_decisions[latest_found][0] = line_number
                    elif "remove_effect" in line:
                        found_decisions[latest_found][1] = line_number
                    elif "timeout_effect" in line:
                        found_decisions[latest_found][2] = line_number
                    elif "target_trigger" in line or "targets" in line:
                        found_decisions[latest_found][3] = True
                    if "{" in line:
                        level += line.count("{")
                    if "}" in line:
                        level -= line.count("}")

            if found_decisions == {}:
                continue

            id = ""
            index = [-1, -1, -1, False]
            main_line_numbers = list(found_decisions.keys())

            outputfile = (
                io.StringIO()
                if dry_run
                else open(
                    os.path.join(cpath, "common", "decisions", filename), "w", "utf-8"
                )
            )
            with outputfile:
                outputfile.truncate()
                for line_number, line in enumerate(lines):
                    if line.strip().startswith("#"):
                        outputfile.write(line)
                        continue
                    replacement_text = line
                    if line_number in main_line_numbers:
                        index = found_decisions[line_number]
                        id = line.split("=")[0].strip()
                        if index[3] is True:
                            id += " target: [From.GetName]"
                    elif line_number == index[0]:
                        changes += 1
                        if "}" in line:
                            temp = line.split("{")
                            replacement_text = (
                                temp[0]
                                + '{\n\n\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision '
                                + id
                                + '"\n'
                                + "{".join(temp)[len(temp[0]) + 1 :]
                                + "\n"
                            )
                        else:
                            replacement_text = (
                                '\t\tcomplete_effect = {\n\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision '
                                + id
                                + '"\n'
                            )
                    elif line_number == index[1]:
                        changes += 1
                        if "}" in line:
                            temp = line.split("{")
                            replacement_text = (
                                temp[0]
                                + '{\n\n\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision remove '
                                + id
                                + '"\n'
                                + "{".join(temp)[len(temp[0]) + 1 :]
                                + "\n"
                            )
                        else:
                            replacement_text = (
                                '\t\tremove_effect = {\n\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision remove '
                                + id
                                + '"\n'
                            )
                    elif line_number == index[2]:
                        changes += 1
                        if "}" in line:
                            temp = line.split("{")
                            replacement_text = (
                                temp[0]
                                + '{\n\n\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision timeout '
                                + id
                                + '"\n'
                                + "{".join(temp)[len(temp[0]) + 1 :]
                                + "\n"
                            )
                        else:
                            replacement_text = (
                                '\t\ttimeout_effect = {\n\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision timeout '
                                + id
                                + '"\n'
                            )
                    outputfile.write(replacement_text)
    return changes


def decision_remove(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "common", "decisions")):
        if ".txt" in filename and "categories" not in filename:
            outputfile = open(
                os.path.join(cpath, "common", "decisions", filename), "r", "utf-8"
            )
            size = os.path.getsize(os.path.join(cpath, "common", "decisions", filename))
            if size < 100:
                continue
            lines = outputfile.readlines()
            outputfile.close()
            outputfile = (
                io.StringIO()
                if dry_run
                else open(
                    os.path.join(cpath, "common", "decisions", filename), "w", "utf-8"
                )
            )
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


def tech_add(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "common", "technologies")):
        if ".txt" in filename:
            file = open(
                os.path.join(cpath, "common", "technologies", filename), "r", "utf-8"
            )
            size = os.path.getsize(
                os.path.join(cpath, "common", "technologies", filename)
            )
            if size < 100:
                continue
            lines = file.readlines()
            line_number = 0
            level = 0
            ids = []
            for line in lines:
                line_number += 1
                if "#" in line:
                    if line.strip().startswith("#") is True:
                        continue
                    else:
                        line = strip_inline_comment(line)
                if "= {" in line:
                    if level == 1:
                        if "on_research_complete = { log = " not in lines[line_number]:
                            ids.append(line_number)
                if "{" in line:
                    level += line.count("{")
                if "}" in line:
                    level -= line.count("}")
            file.close()
            line_number = 0
            outputfile = (
                io.StringIO()
                if dry_run
                else open(
                    os.path.join(cpath, "common", "technologies", filename),
                    "w",
                    "utf-8",
                )
            )
            outputfile.truncate()
            for line in lines:
                line_number += 1
                if line_number in ids:
                    extra = ""
                    if "#" in line:
                        extra = "#" + line.split("#")[1].strip()
                    idea_id = line.split("=")[0].strip()
                    replacement_text = (
                        "\t"
                        + idea_id
                        + " = { "
                        + extra
                        + '\n\t\ton_research_complete = {log = "[GetDateText]: [Root.GetName]: add tech '
                        + idea_id
                        + '" }\n'
                    )
                    outputfile.write(replacement_text)
                    changes += 1
                else:
                    outputfile.write(line)
    return changes


def tech_remove(cpath, dry_run=False):
    changes = 0
    for filename in listdir(os.path.join(cpath, "common", "technologies")):
        if ".txt" in filename:
            outputfile = open(
                os.path.join(cpath, "common", "technologies", filename), "r", "utf-8"
            )
            size = os.path.getsize(
                os.path.join(cpath, "common", "technologies", filename)
            )
            if size < 100:
                continue
            lines = outputfile.readlines()
            outputfile.close()
            outputfile = (
                io.StringIO()
                if dry_run
                else open(
                    os.path.join(cpath, "common", "technologies", filename),
                    "w",
                    "utf-8",
                )
            )
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
