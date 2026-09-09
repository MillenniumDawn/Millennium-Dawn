#!/usr/bin/env python3
import os
import sys
import tempfile
from pathlib import Path

country_tag_list: list[str] = []
inputpath = ""

# Anchor to the repo (tools/generators/ -> repo root) with OS-correct
# separators; the old `"..\\common\\country_tags"` literals were dead on Linux.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)
from shared_utils import atomic_write_bytes, read_text_strict

TAG_DIR = os.path.join(REPO_ROOT, "common", "country_tags")
newline = "\n\t\t\t"
newline2 = "\n\t\t\t\t"
modifiers = "\n\t\t\t\tcic_to_target_factor = 0.2\n\t\t\t\textra_trade_to_target_factor = 0.2\n\t\t\t\ttrade_cost_for_target_factor = -0.2\n\t\t\t"


def main():
    for _required in (
        os.path.join(TAG_DIR, "00_countries.txt"),
        os.path.join(TAG_DIR, "zz_dynamic_countries.txt"),
        os.path.join(REPO_ROOT, "common", "ideas"),
        os.path.join(REPO_ROOT, "localisation", "english"),
    ):
        if not os.path.exists(_required):
            sys.exit(
                f"ERROR: required path not found: {_required}\n"
                "generate_tribute_ideas.py must run from within the "
                "Millennium Dawn repository."
            )

    country_tag_list = createcountrytaglist()
    country_tag_list.extend(pulldynamictags())

    idea_lines = ["ideas = {\n\tcountry = {\n\t\t"]
    loc_lines = ["l_english:\n"]
    for fname in country_tag_list:
        idea_lines.extend(
            [
                f"tribute_idea_{fname} = {{{newline}",
                f'on_add = {{ log = "[GetDateText]: [Root.GetName]: add idea tribute_idea_{fname}" }}{newline}',
                f"name = {fname}_tribute{newline}",
                f"picture = international_treaty2{newline}allowed = {{ always = no }}{newline}allowed_civil_war = {{ always = yes }}{newline}",
                f"targeted_modifier = {{{newline2}tag = {fname}{modifiers}}}",
                "\n\t\t}\n\t\t",
            ]
        )
        loc_lines.append(
            f' {fname}_tribute: "Economic Exploitation by [{fname}.GetName]"\n'
        )
    idea_lines.append("}\n}")

    print("Creating Tribute Idea List")
    with tempfile.TemporaryDirectory(prefix="md_tribute_") as temp_dir:
        idea_temp = os.path.join(temp_dir, "tribute_ideas.txt")
        loc_temp = os.path.join(temp_dir, "MD_tribute_ideas_l_english.yml")
        with open(idea_temp, "w", encoding="utf-8", newline="") as handle:
            handle.write("".join(idea_lines))
        with open(loc_temp, "w", encoding="utf-8-sig", newline="") as handle:
            handle.write("".join(loc_lines))
        atomic_write_bytes(
            os.path.join(REPO_ROOT, "common", "ideas", "tribute_ideas.txt"),
            Path(idea_temp).read_bytes(),
        )
        atomic_write_bytes(
            os.path.join(
                REPO_ROOT,
                "localisation",
                "english",
                "MD_tribute_ideas_l_english.yml",
            ),
            Path(loc_temp).read_bytes(),
        )
    print("Tribute ideas complete")


def createcountrytaglist():
    tag_path = os.path.join(TAG_DIR, "00_countries.txt")
    lines = read_text_strict(tag_path).splitlines()
    return sorted(line[:3] for line in lines if line and not line.startswith("#"))


def pulldynamictags():
    tag_path = os.path.join(TAG_DIR, "zz_dynamic_countries.txt")
    lines = read_text_strict(tag_path).splitlines()
    return sorted(
        line[:3]
        for line in lines
        if line and not line.startswith("#") and not line.startswith("dyn")
    )


if __name__ == "__main__":
    main()
