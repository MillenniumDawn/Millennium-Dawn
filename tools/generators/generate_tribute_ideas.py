#!/usr/bin/env python3
import codecs
import os
import shutil
import sys

country_tag_list = []
inputpath = ""

# Anchor to the repo (tools/generators/ -> repo root) with OS-correct
# separators; the old `"..\\common\\country_tags"` literals were dead on Linux.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
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

    print("Creating Tribute Idea List")
    with open("tribute_ideas.txt", "w") as ffile:
        ffile.write("ideas = {\n\tcountry = {\n\t\t")
        for fname in country_tag_list:
            ffile.write(f"tribute_idea_{fname} = {{{newline}")
            ffile.write(
                f'on_add = {{ log = "[GetDateText]: [Root.GetName]: add idea tribute_idea_{fname}" }}{newline}'
            )
            ffile.write(f"name = {fname}_tribute{newline}")
            ffile.write(
                f"picture = international_treaty2{newline}allowed = {{ always = no }}{newline}allowed_civil_war = {{ always = yes }}{newline}"
            )
            ffile.write(f"targeted_modifier = {{{newline2}tag = {fname}{modifiers}}}")
            ffile.write("\n\t\t}\n\t\t")
        ffile.write("}\n}")
    with codecs.open("MD_tribute_ideas_l_english.yml", "w", "utf-8-sig") as ffile:
        ffile.write("l_english:\n")
        for fname in country_tag_list:
            ffile.write(
                f' {fname}_tribute: "Economic Exploitation by [{fname}.GetName]"\n'
            )
    print("Tribute ideas complete")
    shutil.copy("tribute_ideas.txt", os.path.join(REPO_ROOT, "common", "ideas"))
    os.remove("tribute_ideas.txt")
    shutil.copy(
        "MD_tribute_ideas_l_english.yml",
        os.path.join(REPO_ROOT, "localisation", "english"),
    )
    os.remove("MD_tribute_ideas_l_english.yml")


def createcountrytaglist():
    temp_array = []
    tag_path = os.path.join(TAG_DIR, "00_countries.txt")
    read_tags = open(tag_path, "r")
    lines = read_tags.readlines()
    bad_line = 0
    for l in lines:
        temp_tag = l[0:3]
        if l[0] == "#":
            bad_line += 1
        elif l[0] == "\n":
            bad_line += 1
        else:
            temp_array.append(temp_tag)
            temp_array.sort()
    return temp_array


def pulldynamictags():
    temp_array = []
    tag_path = os.path.join(TAG_DIR, "zz_dynamic_countries.txt")
    read_tags = open(tag_path, "r")
    lines = read_tags.readlines()
    bad_line = 0
    for l in lines:
        temp_tag = l[0:3]
        if l[0] == "#":
            bad_line += 1
        elif l[0] == "\n":
            bad_line += 1
        elif l[0:3] == "dyn":
            bad_line += 1
        else:
            temp_array.append(temp_tag)
            temp_array.sort()
    return temp_array


if __name__ == "__main__":
    main()
