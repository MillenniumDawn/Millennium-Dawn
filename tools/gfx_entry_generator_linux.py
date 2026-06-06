#!/usr/bin/env python3
import os
from pathlib import Path

###########################
###
### HOI 4 GFX file generator by AngriestBird, originally for Millennium Dawn Mod
###
### Copyright (c) 2023 Ken McCormick (AngriestBird)
### Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
### The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###
### Instructions:
### 1. Place this file in HOI4/mod/DEV_FOLDER/tools
### 2. Run: python3 gfx_entry_generator.py
### 3. Follow the prompts. Works on Linux, Mac, and Windows.
###
### Recursively searches for graphical assets (.dds, .png, .tga) and
### generates the required .gfx sprite definitions for the game engine.
###
###########################

IMAGE_EXTENSIONS = {".dds", ".png", ".tga"}


def _windows_sort_key(path):
    """Sort key matching Windows filesystem lexicographic order.
    Case-insensitive string comparison, matching the order that
    the original Windows-based script produced."""
    return str(path).lower()


class bcolors:
    OK = "\033[92m"  # GREEN
    WARNING = "\033[93m"  # YELLOW
    FAIL = "\x1b[31;1m"  # RED
    RESET = "\033[0m"  # RESET COLOR
    INFO = "\x1b[33;25m"  # INFO COLOR


def get_files(scan_path):
    """Recursively find all image files under scan_path.
    Returns (all_files, png_files, tga_files) as lists of Path objects.

    Uses depth-first traversal with case-insensitive sorting that
    interleaves files and directories by sort position, matching the
    order produced by the original Windows os.listdir-based script."""
    all_files = []
    png_files = []
    tga_files = []
    _walk_depth_first(Path(scan_path), all_files, png_files, tga_files)
    return all_files, png_files, tga_files


def _walk_depth_first(directory, all_files, png_files, tga_files):
    """Depth-first directory walk that interleaves files and subdirectories
    in case-insensitive sorted order, matching Windows os.listdir behavior."""
    try:
        entries = sorted(os.listdir(directory), key=_windows_sort_key)
    except OSError:
        return

    for entry in entries:
        full_path = directory / entry
        if full_path.is_file():
            ext = full_path.suffix.lower()
            if ext in IMAGE_EXTENSIONS:
                all_files.append(full_path)
                if ext == ".png":
                    png_files.append(full_path)
                elif ext == ".tga":
                    tga_files.append(full_path)
        elif full_path.is_dir():
            _walk_depth_first(full_path, all_files, png_files, tga_files)


def get_texture_info(file_path, mod_root):
    """Given an absolute file path and the mod root, returns:
    - texture_path: forward-slash relative path for texturefile = "..."
    - stem: filename without extension for name generation
    """
    rel = Path(file_path).relative_to(mod_root)
    return rel.as_posix(), Path(file_path).stem


def strip_idea_prefix(stem):
    """Strip redundant 'idea_' or 'GFX_idea_' prefix from an idea filename stem.
    Prevents double-prefixing when the write block prepends 'GFX_idea_'."""
    if stem.startswith("GFX_idea_"):
        return stem[len("GFX_idea_") :]
    if stem.startswith("idea_"):
        return stem[len("idea_") :]
    return stem


def write_sprite_type(f, name, texture_path, extra_lines=""):
    """Write a standard spriteType block to the output file."""
    f.write(
        f'\tspriteType = {{\n\t\tname = "{name}"\n\t\ttexturefile = "{texture_path}"\n'
    )
    if extra_lines:
        f.write(extra_lines)
    f.write("\t}\n")


def write_shine_sprite_type(f, name, texture_path):
    """Write a goals_shine spriteType block with animation definitions."""
    f.write(
        f'\tspriteType = {{ \n\t\tname = "{name}"\n'
        f'\t\ttexturefile = "{texture_path}"\n'
        f'\t\teffectfile = "gfx/FX/buttonstate.lua"\n'
        f"\t\tanimation = {{\n"
        f'\t\t\tanimationmaskfile = "{texture_path}"\n'
        f'\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n'
        f"\t\t\tanimationrotation = -90.0\n"
        f"\t\t\tanimationlooping = no\n"
        f"\t\t\tanimationtime = 0.75\n"
        f"\t\t\tanimationdelay = 0\n"
        f'\t\t\tanimationblendmode = "add"\n'
        f'\t\t\tanimationtype = "scrolling"\n'
        f"\t\t\tanimationrotationoffset = {{ x = 0.0 y = 0.0 }}\n"
        f"\t\t\tanimationtexturescale = {{ x = 1.0 y = 1.0 }}\n"
        f"\t\t}}\n"
        f"\t\tanimation = {{\n"
        f'\t\t\tanimationmaskfile = "{texture_path}"\n'
        f'\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.tga"\n'
        f"\t\t\tanimationrotation = 90.0\n"
        f"\t\t\tanimationlooping = no\n"
        f"\t\t\tanimationtime = 0.75\n"
        f"\t\t\tanimationdelay = 0\n"
        f'\t\t\tanimationblendmode = "add"\n'
        f'\t\t\tanimationtype = "scrolling"\n'
        f"\t\t\tanimationrotationoffset = {{ x = 0.0 y = 0.0 }}\n"
        f"\t\t\tanimationtexturescale = {{ x = 1.0 y = 1.0 }}\n"
        f"\t\t}}\n"
        f"\t\tlegacy_lazy_load = no\n"
        f"\t}}\n"
    )


def check_duplicate(name, seen_names, file_path):
    """Check if a sprite name has already been seen. Returns True if duplicate."""
    if name in seen_names:
        print(
            f"{bcolors.WARNING}WARNING: Duplicate icon name '{name}' "
            f"from file '{file_path}'. Skipping.{bcolors.RESET}"
        )
        return True
    seen_names.add(name)
    return False


def interface_path(mod_root, filename):
    """Return the full path to a file in the mod's interface directory."""
    return Path(mod_root) / "interface" / filename


def main():
    mod_root = Path(__file__).resolve().parent.parent

    while True:
        try:
            selection_input = input(
                "Main Menu:\n"
                "1. Retrieve and generate goals.gfx\n"
                "2. Retrieve and generate event pictures\n"
                "3. Retrieve and generate MD_ideas.gfx\n"
                "4. Retrieve and generate MD_parties_icons.gfx\n"
                "5. Retrieve and generate intelligence agency icons\n"
                "6. Retrieve and generate MD_decisions.gfx\n"
                "Please enter the number of the option you'd like: "
            ).strip()

            if not selection_input:
                print(
                    f"{bcolors.WARNING}Input cannot be empty. Please enter a number between 1 and 6.{bcolors.RESET}\n"
                )
                continue

            selection = int(selection_input)
            if selection < 1 or selection > 6:
                print(
                    f"{bcolors.FAIL}Invalid selection: {bcolors.RESET}{bcolors.INFO}{selection}{bcolors.RESET}"
                    f"{bcolors.FAIL}. Please enter a number between 1 and 6.{bcolors.RESET}\n"
                )
                continue
            break
        except ValueError:
            print(
                f"{bcolors.WARNING}Invalid input. Please enter a number between 1 and 6.{bcolors.RESET}\n"
            )
            continue

    scan_paths = {
        1: mod_root / "gfx" / "interface" / "goals",
        2: mod_root / "gfx" / "event_pictures",
        3: mod_root / "gfx" / "interface" / "ideas",
        4: mod_root / "gfx" / "texticons" / "parties_icons",
        5: mod_root / "gfx" / "interface" / "operatives" / "agencies",
        6: mod_root / "gfx" / "interface" / "decisions",
    }

    path = scan_paths[selection]
    print(path)

    if not path.exists():
        print(f"{bcolors.FAIL}Directory does not exist: {path}{bcolors.RESET}")
        return

    all_files, png_files, tga_files = get_files(path)

    print(
        f"{bcolors.OK}There are {bcolors.RESET}{len(all_files)}"
        f"{bcolors.OK} .dds, .png or .tga files available in this directory{bcolors.RESET}\n"
    )
    print(
        f"There are {len(png_files)} that are PNG.\n"
        f"There are {len(tga_files)} that are TGA.\n"
    )

    if selection == 1:
        generate_goals(all_files, mod_root)
    elif selection == 2:
        generate_event_pictures(all_files, mod_root)
    elif selection == 3:
        generate_ideas(all_files, mod_root)
    elif selection == 4:
        generate_party_icons(all_files, mod_root)
    elif selection == 5:
        generate_intelligence_icons(all_files, mod_root)
    elif selection == 6:
        generate_decisions(all_files, mod_root)


def generate_goals(all_files, mod_root):
    while True:
        try:
            gfxbool_input = input(
                'Would you like me to append "GFX_" to the front of the icon?\n1 for yes, 0 for no.\n'
            ).strip()

            if not gfxbool_input:
                print(
                    f"{bcolors.WARNING}Input cannot be empty. Please enter 1 or 0.{bcolors.RESET}\n"
                )
                continue

            gfxbool = int(gfxbool_input)
            if gfxbool not in (0, 1):
                print(f"{bcolors.WARNING}Please enter either 1 or 0.{bcolors.RESET}\n")
                continue
            break
        except ValueError:
            print(
                f"{bcolors.WARNING}Invalid input. Please enter 1 or 0.{bcolors.RESET}\n"
            )
            continue

    prefix = "GFX_" if gfxbool == 1 else ""
    seen_names = set()
    duplicate_count = 0

    print(f"{bcolors.OK}Generating goals.gfx...{bcolors.RESET}\n")
    with open(interface_path(mod_root, "goals.gfx"), "w") as ffile:
        ffile.write("spriteTypes = {\n")
        ffile.write("\t#Vanilla DO NOT DELETE\n")
        write_sprite_type(
            ffile,
            "GFX_goal_unknown",
            "gfx/interface/goals/goal_unknown.dds",
            "\t\tlegacy_lazy_load = no\n",
        )

        for file_path in all_files:
            texture_path, stem = get_texture_info(file_path, mod_root)
            name = f"{prefix}{stem}"

            if check_duplicate(name, seen_names, file_path):
                duplicate_count += 1
                continue

            write_sprite_type(ffile, name, texture_path)
        ffile.write("}")

    print("Generation of goals.gfx is complete.\n\nGenerating goals_shine.gfx...\n")

    seen_names_shine = set()
    with open(interface_path(mod_root, "goals_shine.gfx"), "w") as ffile:
        ffile.write("spriteTypes = {\n")
        ffile.write("\t#Vanilla DO NOT DELETE \n")
        ffile.write(
            '\tspriteType = {\n\t\tname = "GFX__shine"\n\t\ttexturefile = "gfx/interface/goals/goal_unknown.dds"\n'
            '\t\teffectFile = "gfx/FX/buttonstate.lua"\n'
            "\t\tanimation = {\n"
            '\t\t\tanimationmaskfile = "gfx/interface/goals/goal_unknown.dds"\n'
            '\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n'
            "\t\t\tanimationrotation = -90.0\n"
            "\t\t\tanimationlooping = no\n"
            "\t\t\tanimationtime = 0.75\n"
            "\t\t\tanimationdelay = 0\n"
            '\t\t\tanimationblendmode = "add"\n'
            '\t\t\tanimationtype = "scrolling"\n'
            "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
            "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
            "\t\t}\n\n"
            "\t\tanimation = {\n"
            '\t\t\tanimationmaskfile = "gfx/interface/goals/goal_unknown.dds"\n'
            '\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n'
            "\t\t\tanimationrotation = 90.0\n"
            "\t\t\tanimationlooping = no\n"
            "\t\t\tanimationtime = 0.75\n"
            "\t\t\tanimationdelay = 0\n"
            '\t\t\tanimationblendmode = "add"\n'
            '\t\t\tanimationtype = "scrolling"\n'
            "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
            "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
            "\t\t}\n"
            "\t\tlegacy_lazy_load = no\n"
            "\t}\n"
        )

        for file_path in all_files:
            texture_path, stem = get_texture_info(file_path, mod_root)
            shine_name = f"{prefix}{stem}_shine"

            if check_duplicate(shine_name, seen_names_shine, file_path):
                continue

            write_shine_sprite_type(ffile, shine_name, texture_path)
        ffile.write("}")

    print("Generation of goals_shine.gfx is complete.\n")

    if duplicate_count > 0:
        print(
            f"{bcolors.WARNING}{duplicate_count} duplicate icon(s) were skipped.{bcolors.RESET}"
        )
    print(
        f"goals.gfx and goals_shine.gfx have been generated for "
        f"{len(all_files)} icons.\n\nThe files have been outputted into the interface files."
    )


def generate_event_pictures(all_files, mod_root):
    print("Generating MD_eventpictures.gfx...")
    seen_names = set()
    duplicate_count = 0

    with open(interface_path(mod_root, "MD_eventpictures.gfx"), "w") as ffile:
        ffile.write("spriteTypes = {\n")
        for file_path in all_files:
            texture_path, stem = get_texture_info(file_path, mod_root)

            if stem.startswith("GFX_"):
                name = stem
            else:
                name = f"GFX_{stem}"

            if check_duplicate(name, seen_names, file_path):
                duplicate_count += 1
                continue

            write_sprite_type(ffile, name, texture_path)
        ffile.write("}")

    print("Generation of MD_eventpictures.gfx is complete.")

    if duplicate_count > 0:
        print(
            f"{bcolors.WARNING}{duplicate_count} duplicate icon(s) were skipped.{bcolors.RESET}"
        )
    print(
        f"\nMD_eventpictures.gfx has been generated for {len(all_files)} event pictures.\n\n"
        f'The file "MD_eventpictures.gfx" has been outputted to the interface directory.'
    )


def generate_ideas(all_files, mod_root):
    print("Generating MD_ideas.gfx...")
    seen_names = set()
    duplicate_count = 0

    with open(interface_path(mod_root, "MD_ideas.gfx"), "w") as ffile:
        ffile.write("spriteTypes = {\n")
        ffile.write(
            '\n\t## DO NOT REMOVE\n\tspriteType={\n\t\tname = "GFX_idea_traits_strip"\n'
            '\t\ttexturefile = "gfx/interface/ideas/idea_traits_strip.dds"\n'
            "\t\tnoOfFrames = 18\n\t}\n"
        )

        for file_path in all_files:
            texture_path, stem = get_texture_info(file_path, mod_root)

            if "traits_strip" in stem:
                print("Utility Idea GFX... skipping")
                continue

            cleaned_stem = strip_idea_prefix(stem)
            name = f"GFX_idea_{cleaned_stem}"

            if check_duplicate(name, seen_names, file_path):
                duplicate_count += 1
                continue

            ffile.write(
                f'\tspriteType ={{\n\t\tname = "{name}"\n'
                f'\t\ttexturefile = "{texture_path}"\n\t}}\n'
            )
        ffile.write("}")

    print("Generation of MD_ideas.gfx is complete.")

    if duplicate_count > 0:
        print(
            f"{bcolors.WARNING}{duplicate_count} duplicate icon(s) were skipped.{bcolors.RESET}"
        )
    print(
        f"\nMD_ideas.gfx has been generated for {len(all_files)} idea pictures.\n\n"
        f"The files have been outputted into the interface files."
    )


def generate_party_icons(all_files, mod_root):
    print("Generating MD_parties_icons.gfx...")
    seen_names = set()
    duplicate_count = 0

    with open(interface_path(mod_root, "MD_parties_icons.gfx"), "w") as ffile:
        ffile.write("spriteTypes = {\n")
        for file_path in all_files:
            texture_path, stem = get_texture_info(file_path, mod_root)
            name = f"GFX_{stem}"

            if check_duplicate(name, seen_names, file_path):
                duplicate_count += 1
                continue

            write_sprite_type(ffile, name, texture_path, "\t\tlegacy_lazy_load = no\n")
        ffile.write("}")

    print("Generation of MD_parties_icons is complete.")

    if duplicate_count > 0:
        print(
            f"{bcolors.WARNING}{duplicate_count} duplicate icon(s) were skipped.{bcolors.RESET}"
        )
    print(
        f"\nMD_parties_icons.gfx has been generated for {len(all_files)} party icons.\n\n"
        f'The file "MD_parties_icons.gfx" has been outputted to the interface directory.'
    )


def generate_intelligence_icons(all_files, mod_root):
    print("Generating MD_intelligence_icons.gfx...")
    seen_names = set()
    duplicate_count = 0
    agency_prefix = "agency_logo_"

    with open(interface_path(mod_root, "MD_intelligence_icons.gfx"), "w") as ffile:
        ffile.write("spriteTypes = {\n")
        for file_path in all_files:
            texture_path, stem = get_texture_info(file_path, mod_root)

            if stem.startswith(agency_prefix):
                tag = stem[len(agency_prefix) :]
            else:
                tag = stem

            name = f"GFX_intelligence_agency_logo_{tag}"

            if check_duplicate(name, seen_names, file_path):
                duplicate_count += 1
                continue

            write_sprite_type(ffile, name, texture_path, "\t\tnoOfFrames = 2\n")
        ffile.write("}")

    print("Generation of MD_intelligence_icons is complete.")

    if duplicate_count > 0:
        print(
            f"{bcolors.WARNING}{duplicate_count} duplicate icon(s) were skipped.{bcolors.RESET}"
        )
    print(
        f"\nMD_intelligence_icons.gfx has been generated for {len(all_files)} intelligence agencies.\n\n"
        f'The file "MD_intelligence_icons.gfx" has been outputted to the interface directory.'
    )


def generate_decisions(all_files, mod_root):
    print("Generating MD_decisions.gfx...")
    seen_names = set()
    duplicate_count = 0

    with open(interface_path(mod_root, "MD_decisions.gfx"), "w") as ffile:
        ffile.write("spriteTypes = {\n")
        ffile.write("\n\t### categories\n\n\n")
        for file_path in all_files:
            texture_path, stem = get_texture_info(file_path, mod_root)

            if any(
                prefix in stem
                for prefix in (
                    "decision_category_",
                    "decision_",
                    "decisions_category_",
                    "decisions_",
                )
            ):
                name = f"GFX_{stem}"
            else:
                name = f"GFX_decision_{stem}"

            if check_duplicate(name, seen_names, file_path):
                duplicate_count += 1
                continue

            ffile.write(
                f'\tspriteType = {{\n\t\tname = "{name}"\n'
                f'\t\ttexturefile = "{texture_path}"\n\t}}\n\n'
            )
        ffile.write("}")

    print("Generation of MD_decisions.gfx is complete.")

    if duplicate_count > 0:
        print(
            f"{bcolors.WARNING}{duplicate_count} duplicate icon(s) were skipped.{bcolors.RESET}"
        )
    print(
        f"\nMD_decisions.gfx has been generated for {len(all_files)} decision pictures.\n\n"
        f"The files have been outputted into the interface files."
    )


if __name__ == "__main__":
    main()
