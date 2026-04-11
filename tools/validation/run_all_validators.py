#!/usr/bin/env python
###############################################################################
# Run all validation scripts in parallel (cross-platform)
# Usage:
#   python run_all_validators.py [--staged] [--strict] [--no-color]
###############################################################################
import argparse
import os
import subprocess
import sys
import tempfile

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPTS_DIR)

# name -> (script filename, human-readable label)
VALIDATORS = [
    ("variables", "validate_variables.py", "Variable and event target validation"),
    (
        "scripted-localisation",
        "validate_scripted_localisation.py",
        "Scripted localisation validation",
    ),
    ("cosmetic-tags", "validate_cosmetic_tags.py", "Cosmetic tag validation"),
    ("decisions", "validate_decisions.py", "Decision validation"),
    ("localisation", "validate_localisation.py", "Localisation validation"),
    ("events", "validate_events.py", "Event validation"),
    (
        "history-techs",
        "validate_history_techs.py",
        "History technology dependency validation",
    ),
    (
        "unused-scripted",
        "validate_unused_scripted.py",
        "Unused scripted effects/triggers validation",
    ),
    ("oob-units", "validate_oob_units.py", "OOB unit name validation"),
    (
        "defines",
        "validate_defines.py",
        "Defines validation (dead/namespace/duplicate)",
    ),
    (
        "ai-navy",
        "validate_ai_navy.py",
        "AI navy validation (ship types, missions, fleet refs)",
    ),
    (
        "ai-equipment",
        "validate_ai_equipment.py",
        "AI equipment coverage validation (naval/land/air)",
    ),
    ("ai-roles", "validate_ai_roles.py", "AI role reference validation"),
    ("factions", "validate_factions.py", "Faction system validation"),
]


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"


def main():
    parser = argparse.ArgumentParser(description="Run all MD validators in parallel")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    if args.no_color:
        Colors.RED = ""
        Colors.GREEN = ""
        Colors.YELLOW = ""
        Colors.CYAN = ""
        Colors.NC = ""

    extra_flags = []
    if args.staged:
        extra_flags.append("--staged")
    if args.strict:
        extra_flags.append("--strict")
    if args.no_color:
        extra_flags.append("--no-color")

    output_dir = tempfile.mkdtemp()

    print(
        f"{Colors.CYAN}{'=' * 80}{Colors.NC}\n"
        f"{Colors.CYAN}Running Millennium Dawn Validation Suite (parallel){Colors.NC}\n"
        f"{Colors.CYAN}{'=' * 80}{Colors.NC}\n"
    )

    # Launch all validators in parallel
    processes = {}
    for name, script, _label in VALIDATORS:
        script_path = os.path.join(SCRIPTS_DIR, script)
        output_path = os.path.join(output_dir, f"{name}.txt")
        cmd = [
            sys.executable,
            script_path,
            *extra_flags,
            "--output",
            output_path,
        ]
        processes[name] = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Collect results in order
    total_errors = 0
    for name, _script, label in VALIDATORS:
        returncode = processes[name].wait()
        if returncode != 0:
            print(f"{Colors.RED}\u2717 {label}{Colors.NC}")
            total_errors += 1
        else:
            print(f"{Colors.GREEN}\u2713 {label}{Colors.NC}")

    print(f"\n{Colors.CYAN}{'=' * 80}{Colors.NC}")
    if total_errors == 0:
        print(f"{Colors.GREEN}\u2713 ALL VALIDATIONS PASSED{Colors.NC}")
        # Clean up temp dir
        for name, _, _ in VALIDATORS:
            path = os.path.join(output_dir, f"{name}.txt")
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(output_dir)
        sys.exit(0)
    else:
        print(
            f"{Colors.RED}\u2717 VALIDATION FAILED \u2014 {total_errors} script(s) "
            f"reported issues{Colors.NC}"
        )
        print(f"\n{Colors.YELLOW}Detailed reports saved to: {output_dir}{Colors.NC}")
        sys.exit(1 if args.strict else 0)


if __name__ == "__main__":
    main()
