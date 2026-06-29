#!/usr/bin/python
import os
import re
import shutil

#############################1
###
### HOI 4 GFX file generator by AngriestBird, originally for Millennium Dawn Mod
### Written in Python 3.11.1
###
### Copyright (c) 2023 Ken McCormick (AngriestBird)
### Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
### The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###
### Instructions:
### 1. PLace this file in HOI4/mod/DEV_FOLDER/tools
### 2. Update line 41 and 42 to be the name of your mod
### 3. Run script as below:
### usage: python gfx_entry_generator.py
### Follow the prompts from there. This script will not function properly if it is not sitting in the proper folder.
###
### Given an input selection number of 1 through 4 recurisvely search and save path for graphical assets.
### It then generates the requires .gfx code and ports it into readable script for the game.
###
###
###########################

# Global Init
# ddslist: List of files that are .dds
# pnglist: List of files that are .png
# tgalist: List of files that are .tga
# ddsdict: Dictionary of all file names and their paths
# country_tag_list: Country Tag List
ddslist = []
ddsdict = {}
pnglist = []
tgalist = []
country_tag_list = []

# Modfolder = the mod folder name
# mod = The mod name
modfolder = "Millennium-Dawn\\"
mod = "Millennium-Dawn"

TITLEBAR_REL = "gfx/interface/focusview/titlebar"

GFX_BEGIN = "# === BEGIN GENERATED JOINT TITLE BARS (managed by gfx_entry_generator.py) ==="
GFX_END = "# === END GENERATED JOINT TITLE BARS ==="
STYLE_BEGIN = "# === BEGIN GENERATED JOINT TITLE BAR STYLES (managed by gfx_entry_generator.py) ==="
STYLE_END = "# === END GENERATED JOINT TITLE BAR STYLES ==="

TITLEBAR_FILE_RE = re.compile(
    r"^focus_(unavailable|can_start|completed)_joint_(?P<suffix>.+)_bg\.dds$"
)
_JOINT_NAME_RE = re.compile(
    r"^GFX_focus_(unavailable|can_start|current|completed)_joint_(.+)$"
)
_COMMENT_LINE_RE = re.compile(r"^[ \t]*#.*$", re.MULTILINE)


def main():
    # Get the mod root directory (parent of the tools directory)
    mod_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # country_tag_list = createcountrytaglist()

    while True:
        try:
            selection_input = input(
                "Main Menu:\n1. Retrieve and generate goals.gfx\n2. Retrieve and generate event pictures\n3. Retrieve and generate MD_ideas.gfx. This also generates defence company entries.\n4. Retrieve and generate MD_technologies.gfx (DO NOT USE. WIP)\n5. Retrieve and generate MD_parties_icons.gfx.\n6. Retrieve and generate intelligence agency icons\n7. Retrieve and generate MD_decisions.gfx\n8. Retrieve and generate Focus Title Bars (This also updates the titlebar_styles.txt file)\nPlease enter the number of the option you'd like: "
            ).strip()

            if not selection_input:
                print(
                    f"{bcolors.WARNING}Input cannot be empty. Please enter a number between 1 and 8.{bcolors.RESET}\n"
                )
                continue

            selection = int(selection_input)
            break
        except ValueError:
            print(
                f"{bcolors.WARNING}Invalid input. Please enter a number between 1 and 8.{bcolors.RESET}\n"
            )
            continue

    if selection == 1:
        path = os.path.join(mod_root, "gfx", "interface", "goals")
        print(path)
        getfiles(path)
    elif selection == 2:
        path = os.path.join(mod_root, "gfx", "event_pictures")
        print(path)
        getfiles(path)
    elif selection == 3:
        path = os.path.join(mod_root, "gfx", "interface", "ideas")
        print(path)
        getfiles(path)
    elif selection == 4:
        path = os.path.join(mod_root, "gfx", "interface", "technologies")
        print(path)
        getfiles(path)
    elif selection == 5:
        path = os.path.join(mod_root, "gfx", "texticons", "parties_icons")
        print(path)
        getfiles(path)
    elif selection == 6:
        path = os.path.join(mod_root, "gfx", "interface", "operatives", "agencies")
        print(path)
        getfiles(path)
    elif selection == 7:
        path = os.path.join(mod_root, "gfx", "interface", "decisions")
        print(path)
        getfiles(path)
    elif selection == 8:
        generate_focus_titlebars(mod_root)
        return
    else:
        print(
            f"{bcolors.FAIL}Invalid selection: {bcolors.RESET}{bcolors.INFO}{selection}{bcolors.RESET}{bcolors.FAIL} is not an option. Please enter a number between 1 and 8 and run the script again.\n{bcolors.RESET}"
        )
        return

    print(
        f"{bcolors.OK}There are {bcolors.RESET}"
        + str(len(ddslist))
        + f"{bcolors.OK} .dds, .png or .tga files available in this directory{bcolors.RESET}\n"
    )
    print(
        "There are "
        + str(len(pnglist))
        + " that are PNG.\nThere are "
        + str(len(tgalist))
        + " that are TGA.\n"
    )

    # Variable Init Section
    file_location = ""  # File Location: It is only used to parse out the path
    texture_path = ""  # Texture Path: becomes the path that is implemented texturefile
    file_utility = ""  # File Utility: Used to "sort" for a file
    texture_name = (
        ""  # Texture name: The actual name of the file for use of the texture
    )
    tag_of_nation = ""  # Tag of the Nation: Country Tag Use

    # Creation of the .gfx files
    while selection != 0:
        if selection == 1:
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
                    if gfxbool not in [0, 1]:
                        print(
                            f"{bcolors.WARNING}Please enter either 1 or 0.{bcolors.RESET}\n"
                        )
                        continue
                    break
                except ValueError:
                    print(
                        f"{bcolors.WARNING}Invalid input. Please enter 1 or 0.{bcolors.RESET}\n"
                    )
                    continue

            print(f"{bcolors.OK}Generating goals.gfx...{bcolors.RESET}\n")
            with open("goals.gfx", "w") as ffile:
                ffile.write("spriteTypes = {\n")
                ffile.write("\t#Vanilla DO NOT DELETE\n")
                ffile.write(
                    '\tspriteType = {\n\t\tname = "GFX_goal_unknown"\n\t\ttexturefile = "gfx/interface/goals/goal_unknown.dds"\n\t\tlegacy_lazy_load = no\n\t}\n'
                )
                for fname in ddsdict:
                    file_location = fname
                    file_location = file_location.split(modfolder)
                    texture_path = file_location[1]  # Should Retrieve the Path
                    file_utility = texture_path
                    texture_path = texture_path.replace("\\", "/")
                    file_utility = file_utility.replace("gfx\\interface\\goals\\", "")
                    file_utility = file_utility.split("\\")

                    texture_name = createitemcall(file_utility)

                    if gfxbool == 0:
                        ffile.write(
                            '\tspriteType = {\n\t\tname = "'
                            + texture_name
                            + '"\n\t\ttexturefile = "'
                            + texture_path
                            + '"\n\t}\n'
                        )
                    else:
                        ffile.write(
                            '\tspriteType = {\n\t\tname = "GFX_'
                            + texture_name
                            + '"\n\t\ttexturefile = "'
                            + texture_path
                            + '"\n\t}\n'
                        )
                ffile.write("}")
            print(
                "Generation of goals.gfx is complete.\n\nGenerating goals_shine.gfx...\n"
            )
            with open("goals_shine.gfx", "w") as ffile:
                ffile.write("spriteTypes = {\n")
                ffile.write("\t#Vanilla DO NOT DELETE \n")
                ffile.write(
                    '\tspriteType = {\n\t\tname = "GFX__shine"\n\t\ttexturefile = "gfx/interface/goals/goal_unknown.dds"\n\t\teffectFile = "gfx/FX/buttonstate.lua"\n\t\tanimation = {\n\t\t\tanimationmaskfile = "gfx/interface/goals/goal_unknown.dds"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\n\t\tanimation = {\n\t\t\tanimationmaskfile = "gfx/interface/goals/goal_unknown.dds"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n'
                )
                for fname in ddsdict:
                    file_location = fname
                    file_location = file_location.split(modfolder)
                    texture_path = file_location[1]  # Should Retrieve the Path
                    file_utility = texture_path
                    texture_path = texture_path.replace("\\", "/")
                    file_utility = file_utility.replace("gfx\\interface\\goals\\", "")
                    file_utility = file_utility.split("\\")

                    texture_name = createitemcall(file_utility)

                    if gfxbool == 0:
                        ffile.write(
                            '\tspriteType = { \n\t\tname = "'
                            + texture_name
                            + '_shine"\n\t\ttexturefile = "'
                            + texture_path
                            + '"\n\t\teffectfile = "gfx/FX/buttonstate.lua"\n\t\tanimation = {\n\t\t\tanimationmaskfile = "'
                            + texture_path
                            + '"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tanimation = {\n\t\t\tanimationmaskfile = "'
                            + texture_path
                            + '"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.tga"\n\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n'
                        )
                    else:
                        ffile.write(
                            '\tspriteType = { \n\t\tname = "GFX_'
                            + texture_name
                            + '_shine"\n\t\ttexturefile = "'
                            + texture_path
                            + '"\n\t\teffectfile = "gfx/FX/buttonstate.lua"\n\t\tanimation = {\n\t\t\tanimationmaskfile = "'
                            + texture_path
                            + '"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.dds"\n\t\t\tanimationrotation = -90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tanimation = {\n\t\t\tanimationmaskfile = "'
                            + texture_path
                            + '"\n\t\t\tanimationtexturefile = "gfx/interface/goals/shine_overlay.tga"\n\t\t\tanimationrotation = 90.0\n\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = "add"\n\t\t\tanimationtype = "scrolling"\n\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n\t\tlegacy_lazy_load = no\n\t}\n'
                        )
                ffile.write("}")
            print("Generation of goals_shine.gfx is complete.\n")
            movefilestointerface("goals.gfx", "goals_shine.gfx")
            print(
                "goals.gfx and goals_shine.gfx have been generated for "
                + str(len(ddslist))
                + " icons.\n\nThe files have been outputted into the interface files."
            )
            return
        elif selection == 2:
            print("Generating event_pictures.gfx...")
            with open("MD_eventpictures.gfx", "w") as ffile:
                ffile.write("spriteTypes = {\n")
                for fname in ddsdict:
                    file_location = fname
                    file_location = file_location.split(modfolder)
                    texture_path = file_location[1]  # Should Retrieve the Path
                    file_utility = texture_path
                    texture_path = texture_path.replace("\\", "/")
                    file_utility = file_utility.replace("gfx\\event_pictures\\", "")
                    file_utility = file_utility.split("\\")

                    texture_name = createitemcall(file_utility)

                    if "GFX_" in texture_name:
                        ffile.write(
                            '\tspriteType = {\n\t\tname = "'
                            + texture_name
                            + '"\n\t\ttexturefile = "'
                            + texture_path
                            + '"\n\t}\n'
                        )
                    else:
                        ffile.write(
                            '\tspriteType = {\n\t\tname = "GFX_'
                            + texture_name
                            + '"\n\t\ttexturefile = "'
                            + texture_path
                            + '"\n\t}\n'
                        )

                ffile.write("}")
            print("Generation of event_pictures.gfx is complete.")
            movefilestointerface("MD_eventpictures.gfx")
            print(
                f'\neventpictures.gfx has been generated for {len(ddslist)} event pictures.\n\nThe file "MD_eventpictures.gfx" has been outputted to the interface directory.'
            )
            return
        elif selection == 3:
            print("Generating MD_ideas.gfx...")
            with open("MD_ideas.gfx", "w") as ffile:
                ffile.write("spriteTypes = {\n")
                ffile.write(
                    '\n\t## DO NOT REMOVE\n\tspriteType={\n\t\tname = "GFX_idea_traits_strip"\n\t\ttexturefile = "gfx/interface/ideas/idea_traits_strip.dds"\n\t\tnoOfFrames = 18\n\t}\n'
                )
                for fname in ddsdict:
                    file_location = fname
                    file_location = file_location.split(modfolder)
                    texture_path = file_location[1]  # Should Retrieve the Path
                    file_utility = texture_path
                    texture_path = texture_path.replace("\\", "/")
                    file_utility = file_utility.replace("gfx\\interface\\ideas\\", "")
                    file_utility = file_utility.split("\\")

                    if "traits_strip" in fname:
                        print("Utility Idea GFX... skipping")
                    else:
                        texture_name = createitemcall(file_utility, type=1)
                        ffile.write(
                            '\tspriteType ={\n\t\tname = "GFX_idea_'
                            + texture_name
                            + '"\n\t\ttexturefile = "'
                            + texture_path
                            + '"\n\t}\n'
                        )
                ffile.write("}")
            print("Generation of the MD_ideas.gfx...")
            movefilestointerface("MD_ideas.gfx")
            print(
                "\nMD_ideas.gfx has been generated for "
                + str(len(ddslist))
                + " idea pictures.\n\nThe files have been outputted into the interface files."
            )
            return
        elif selection == 4:  # Technology Icons
            print("Generating technologies.gfx...")
            with open("technologies.gfx", "w") as ffile:
                # Overarching Clause
                count = 0
                ffile.write("spriteTypes = {\n")
                for fname in ddsdict:
                    if "Generic" in fname:
                        count += 1
                    elif "modules" in fname:
                        count += 1
                    else:
                        if any(
                            (match := substring) in fname
                            for substring in country_tag_list
                        ):
                            tag_of_nation = match
                        file_location = fname
                        file_location = file_location.split(modfolder)
                        texture_path = file_location[1]  # Should Retrieve the Path
                        file_utility = texture_path
                        texture_path = texture_path.replace("\\", "/")
                        file_utility = file_utility.replace(
                            "gfx\\interface\\technologies\\", ""
                        )
                        file_utility = file_utility.split("\\")

                        texture_name = createitemcall(file_utility)

                        # Write the spriteType
                        if tag_of_nation is None:
                            ffile.write(
                                '\tspriteType ={\n\t\tname = "GFX_'
                                + texture_name
                                + '"\n\t\ttexturefile = "'
                                + texture_path
                                + '"\n\t}\n'
                            )
                        else:
                            ffile.write(
                                '\tspriteType ={\n\t\tname = "GFX_'
                                + tag_of_nation
                                + "_"
                                + texture_name
                                + '"\n\t\ttexturefile = "'
                                + texture_path
                                + '"\n\t}\n'
                            )
                # End Clause
                ffile.write("}")
            print(
                f"{bcolors.INFO} {count} files were skipped due to being generic or module files.{bcolors.RESET}"
            )
            print("Generation of the technologies.gfx...")
            return
        elif selection == 5:  # Party Icons
            print("Generating MD_parties_icons.gfx...")
            with open("MD_parties_icons.gfx", "w") as ffile:
                ffile.write("spriteTypes = {\n")
                for fname in ddsdict:
                    file_location = fname
                    file_location = file_location.split(modfolder)
                    texture_path = file_location[1]  # Should Retrieve the Path
                    file_utility = texture_path
                    texture_path = texture_path.replace("\\", "/")
                    file_utility = file_utility.replace(
                        "gfx\\texticons\\parties_icons\\", ""
                    )
                    file_utility = file_utility.split("\\")

                    texture_name = createitemcall(file_utility)

                    ffile.write(
                        '\tspriteType = {\n\t\tname = "GFX_'
                        + texture_name
                        + '"\n\t\ttexturefile = "'
                        + texture_path
                        + '"\n\t\tlegacy_lazy_load = no\n\t}\n'
                    )

                ffile.write("}")
            print("Generation of MD_parties_icons is complete.")
            movefilestointerface("MD_parties_icons.gfx")
            print(
                f'\nMD_parties_icons.gfx has been generated for {len(ddslist)} party icons.\n\nThe file "MD_parties_icons.gfx" has been outputted to the interface directory.'
            )
            return
        elif selection == 6:  # Intelligence Agency
            print("Generating MD_intelligence_icons.gfx...")
            with open("MD_intelligence_icons.gfx", "w") as ffile:
                ffile.write("spriteTypes = {\n")
                for fname in ddsdict:
                    file_location = fname
                    file_location = file_location.split(modfolder)
                    texture_path = file_location[1]  # Should Retrieve the Path
                    file_utility = texture_path
                    texture_path = texture_path.replace("\\", "/")
                    file_utility = file_utility.replace(
                        "gfx\\interface\\operatives\\agencies", ""
                    )
                    file_utility = file_utility.split("\\")

                    texture_name = createitemcall(file_utility)
                    texture_tuple = tuple(map(str, texture_name.split("_")))

                    ffile.write(
                        '\tspriteType = {\n\t\tname = "GFX_intelligence_agency_logo_'
                        + texture_tuple[2]
                        + '"\n\t\ttexturefile = "'
                        + texture_path
                        + '"\n\t\tnoOfFrames = 2\n\t}\n'
                    )

                ffile.write("}")
            print("Generation of MD_intelligence_icons is complete.")
            movefilestointerface("MD_intelligence_icons.gfx")
            print(
                f'\nMD_intelligence_icons.gfx has been generated for {len(ddslist)} intelligence agencies.\n\nThe file "MD_intelligence_icons.gfx" has been outputted to the interface directory.'
            )
            return
        elif selection == 7:  # Decisions
            print("Generating MD_decisions.gfx...")
            with open("MD_decisions.gfx", "w") as ffile:
                ffile.write("spriteTypes = {\n")
                ffile.write("\n\t### categories\n\n\n")
                for fname in ddsdict:
                    file_location = fname
                    file_location = file_location.split(modfolder)
                    texture_path = file_location[1]  # Should Retrieve the Path
                    file_utility = texture_path
                    texture_path = texture_path.replace("\\", "/")
                    file_utility = file_utility.replace(
                        "gfx\\interface\\decisions\\", ""
                    )
                    file_utility = file_utility.split("\\")

                    texture_name = createitemcall(file_utility)

                    if (
                        "decision_category_" in texture_name
                        or "decision_" in texture_name
                        or "decisions_" in texture_name
                        or "decisions_category_" in texture_name
                    ):
                        ffile.write(
                            '\tspriteType = {\n\t\tname = "GFX_'
                            + texture_name
                            + '"\n\t\ttexturefile = "'
                            + texture_path
                            + '"\n\t}\n\n'
                        )
                    else:
                        ffile.write(
                            '\tspriteType = {\n\t\tname = "GFX_decision_'
                            + texture_name
                            + '"\n\t\ttexturefile = "'
                            + texture_path
                            + '"\n\t}\n\n'
                        )
                ffile.write("}")
            print("Generation of the MD_decisions.gfx...")
            movefilestointerface("MD_decisions.gfx")
            print(
                "\nMD_decisions.gfx has been generated for "
                + str(len(ddslist))
                + " decision pictures.\n\nThe files have been outputted into the interface files."
            )
            return
        else:
            print(
                f"{bcolors.FAIL}Invalid selection: {bcolors.RESET}{bcolors.INFO}{selection}{bcolors.RESET}{bcolors.FAIL} is not an option. Please enter a number between 1 and 7 and run the script again.\n{bcolors.RESET}"
            )
            return


class bcolors:
    OK = "\033[92m"  # GREEN
    WARNING = "\033[93m"  # YELLOW
    FAIL = "\x1b[31;1m"  # RED
    RESET = "\033[0m"  # RESET COLOR
    INFO = "\x1b[33;25m"  # INFO COLOR


def movefilestointerface(filename, filename2=""):
    print(f"Moving {filename} from tools to the interface directory")
    shutil.copy(filename, "../interface")
    os.remove(filename)
    if filename2 != "":
        shutil.copy(filename2, "../interface")
        os.remove(filename2)
        print(
            f"{filename} && {filename2} has been moved successfully to the interface directory."
        )
    else:
        print(f"{filename} has been moved successfully to the interface directory")


def createitemcall(filecall, type=0):
    util = ""
    # Create the Item "Call"
    for i in range(len(filecall)):
        if ".dds" in filecall[i]:
            util = filecall[i]
        elif ".png" in filecall[i]:
            util = filecall[i]
        elif ".tga" in filecall[i]:
            util = filecall[i]
    if ".dds" in util:
        util = util.replace(".dds", "")
    elif ".png" in util:
        util = util.replace(".png", "")
    elif ".tga" in util:
        util = util.replace(".tga", "")

    if type == 1:
        if "idea_" in util:
            util = util.replace("idea_", "")
        elif "GFX_idea_" in util:
            util = util.replace("GFX_idea_", "")

    return util


def createcountrytaglist():
    temp_array = []
    # Country Tag List Array Creation
    mod_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tag_path = os.path.join(mod_root, "common", "country_tags", "00_countries.txt")
    read_tags = open(tag_path, "r")
    lines = read_tags.readlines()
    bad_line = 0
    for l in lines:
        temp_tag = l[0:3]
        if l[0] == "#":
            bad_line += 1
        elif l[0] == "\n":
            bad_line += 1
        elif l[0:3] == "NAV":
            bad_line += 1
        else:
            temp_array.append(temp_tag)
            temp_array.sort()
    return temp_array


def getfiles(path):
    for filename in os.listdir(path):
        f = os.path.join(path, filename)
        if os.path.isfile(f):
            if ".dds" in f:
                ddsdict[f] = filename
                ddslist.append(filename)
            elif ".png" in f:
                ddsdict[f] = filename
                ddslist.append(filename)
                pnglist.append(filename)
            elif ".tga" in f:
                ddsdict[f] = filename
                ddslist.append(filename)
                tgalist.append(filename)
        else:
            getfiles(f)


# --- Focus title-bar generation -------------------------------------------


def _titlebar_tex(state, suffix):
    return f"{TITLEBAR_REL}/focus_{state}_joint_{suffix}_bg.dds"


def _basic_sprite(state, suffix):
    name = f"GFX_focus_{state}_joint_{suffix}"
    return (
        "\tspriteType = {\n"
        f'\t\tname = "{name}"\n'
        f'\t\ttextureFile = "{_titlebar_tex(state, suffix)}"\n'
        "\t}\n"
    )


def _current_sprite(suffix):
    # current reuses the can_start background and overlays the ongoing animation.
    return (
        "\tSpriteType = {\n"
        f'\t\tname = "GFX_focus_current_joint_{suffix}"\n'
        f'\t\ttexturefile = "{_titlebar_tex("can_start", suffix)}"\n'
        '\t\teffectFile = "gfx/FX/buttonstate_onlydisable.lua"\n'
        "\t\tanimation = {\n"
        f'\t\t\tanimationmaskfile = "{TITLEBAR_REL}/focus_ongoing_mask2.dds"\n'
        f'\t\t\tanimationtexturefile = "{TITLEBAR_REL}/focus_ongoing_texture.dds"\n'
        "\t\t\tanimationrotation = -90.0\n"
        "\t\t\tanimationlooping = yes\n"
        "\t\t\tanimationtime = 20.0\n"
        "\t\t\tanimationdelay = 0.2\n"
        '\t\t\tanimationblendmode = "add"\n'
        '\t\t\tanimationtype = "rotating"\n'
        "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
        "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
        "\t\t}\n"
        "\t\tanimation = {\n"
        f'\t\t\tanimationmaskfile = "{TITLEBAR_REL}/focus_ongoing_mask4.dds"\n'
        f'\t\t\tanimationtexturefile = "{TITLEBAR_REL}/focus_ongoing_texture.dds"\n'
        "\t\t\tanimationrotation = 90.0\n"
        "\t\t\tanimationlooping = yes\n"
        "\t\t\tanimationtime = 15.0\n"
        "\t\t\tanimationdelay = 0.2\n"
        '\t\t\tanimationblendmode = "add"\n'
        '\t\t\tanimationtype = "rotating_ccw"\n'
        "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
        "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
        "\t\t}\n"
        "\t\tlegacy_lazy_load = no\n"
        "\t}\n"
    )


def _completed_sprite(suffix):
    return (
        "\tSpriteType = {\n"
        f'\t\tname = "GFX_focus_completed_joint_{suffix}"\n'
        f'\t\ttexturefile = "{_titlebar_tex("completed", suffix)}"\n'
        '\t\teffectFile = "gfx/FX/buttonstate_onlydisable.lua"\n'
        "\t\tanimation = {\n"
        f'\t\t\tanimationmaskfile = "{TITLEBAR_REL}/focus_completed_mask.dds"\n'
        f'\t\t\tanimationtexturefile = "{TITLEBAR_REL}/focus_completed_texture.dds"\n'
        "\t\t\tanimationrotation = 0.0\n"
        "\t\t\tanimationlooping = yes\n"
        "\t\t\tanimationtime = 26.0\n"
        "\t\t\tanimationdelay = 0.0\n"
        '\t\t\tanimationblendmode = "add"\n'
        '\t\t\tanimationtype = "scrolling"\n'
        "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n"
        "\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n"
        "\t\t}\n"
        "\t\tlegacy_lazy_load = no\n"
        "\t}\n"
    )


def _set_block(suffix, present):
    parts = [f"\t### {suffix} ###\n"]
    if "unavailable" in present:
        parts.append(_basic_sprite("unavailable", suffix))
    if "can_start" in present:
        parts.append(_basic_sprite("can_start", suffix))
        parts.append("\n")
        parts.append(_current_sprite(suffix))
    if "completed" in present:
        parts.append("\n")
        parts.append(_completed_sprite(suffix))
    return "".join(parts)


def _style_block(suffix):
    return (
        "style = {\n"
        f"\tname = JOINT_{suffix}_focus_style\n"
        "\n"
        f"\tunavailable = GFX_focus_unavailable_joint_{suffix}\n"
        f"\tcompleted = GFX_focus_completed_joint_{suffix}\n"
        f"\tavailable = GFX_focus_can_start_joint_{suffix}\n"
        f"\tcurrent = GFX_focus_current_joint_{suffix}\n"
        "}\n"
    )


def _read_lf(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _newline_of(text):
    return "\r\n" if "\r\n" in text else "\n"


def _write_with_newline(path, text, newline):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if newline == "\r\n":
        text = text.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _match_brace(text, open_idx):
    depth = 0
    i = open_idx
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError(f"Unmatched opening brace at offset {open_idx}")


def _iter_sprite_blocks(text):
    for m in re.finditer(r"[sS]priteType\s*=\s*\{", text):
        open_idx = text.index("{", m.start())
        try:
            end = _match_brace(text, open_idx) + 1
        except ValueError:
            continue
        block = text[m.start():end]
        nm = re.search(r'name\s*=\s*"([^"]+)"', block)
        tx = re.search(r'texture[fF]ile\s*=\s*"([^"]+)"', block)
        yield nm.group(1) if nm else None, tx.group(1) if tx else None


def _remove_block_by_name(text, name):
    needle = f'name = "{name}"'
    idx = text.find(needle)
    if idx == -1:
        return text, False
    kw = max(text.rfind("spriteType", 0, idx), text.rfind("SpriteType", 0, idx))
    if kw == -1:
        return text, False
    line_start = text.rfind("\n", 0, kw) + 1
    open_idx = text.index("{", kw)
    try:
        end = _match_brace(text, open_idx) + 1
    except ValueError:
        return text, False
    if end < len(text) and text[end] == "\n":
        end += 1
    return text[:line_start] + text[end:], True


def _remove_tag_headers(text, suffixes):
    suffix_set = set(suffixes)
    kept = []
    for line in text.split("\n"):
        m = re.match(r"^#+\s*([A-Za-z0-9_]+)\s*#+$", line.strip())
        if m and m.group(1) in suffix_set:
            continue
        kept.append(line)
    return "\n".join(kept)


def _strip_region(text, begin, end):
    s = text.find(begin)
    if s == -1:
        return text
    line_start = text.rfind("\n", 0, s) + 1
    e = text.find(end, s)
    if e == -1:
        # END marker absent: strip from BEGIN to EOF to prevent double-BEGIN on next run.
        return text[:line_start]
    e += len(end)
    if e < len(text) and text[e] == "\n":
        e += 1
    return text[:line_start] + text[e:]


def _collapse_blanks(text):
    return re.sub(r"\n{3,}", "\n\n", text)


def generate_focus_titlebars(mod_root):
    titlebar_dir = os.path.join(
        mod_root, "gfx", "interface", "focusview", "titlebar"
    )
    gfx_file = os.path.join(mod_root, "interface", "nationalfocusview.gfx")
    styles_file = os.path.join(
        mod_root, "common", "national_focus", "00_titlebar_styles.txt"
    )

    if not os.path.isdir(titlebar_dir):
        print(f"{bcolors.FAIL}Titlebar directory not found: {titlebar_dir}{bcolors.RESET}")
        return
    for required in (gfx_file, styles_file):
        if not os.path.isfile(required):
            print(f"{bcolors.FAIL}Missing file: {required}{bcolors.RESET}")
            return

    # 1. Discover sets from the source .dds files.
    folder = {}
    for fn in os.listdir(titlebar_dir):
        m = TITLEBAR_FILE_RE.match(fn)
        if m:
            folder.setdefault(m.group("suffix"), set()).add(m.group(1))

    # 2. Parse existing joint entries in the .gfx.
    gfx_text = _read_lf(gfx_file)
    gfx_nl = _newline_of(gfx_text)
    gfx_text = gfx_text.replace("\r\n", "\n").replace("\r", "\n")

    existing = {}
    for nm, tx in _iter_sprite_blocks(_COMMENT_LINE_RE.sub("", gfx_text)):
        if not nm:
            continue
        mm = _JOINT_NAME_RE.match(nm)
        if mm:
            existing.setdefault(mm.group(2), {})[mm.group(1)] = tx

    def is_regular(suffix, states):
        for st in ("unavailable", "can_start", "completed"):
            if st in states and states[st] != _titlebar_tex(st, suffix):
                return False
        if "current" in states and states["current"] != _titlebar_tex("can_start", suffix):
            return False
        return bool(states)

    regular_existing = {s for s, st in existing.items() if is_regular(s, st)}
    irregular_existing = sorted(set(existing) - regular_existing)
    managed = sorted(set(folder) | regular_existing)

    def present_states(suffix):
        p = set(folder.get(suffix, set()))
        ex = existing.get(suffix, {})
        for st in ("unavailable", "can_start", "completed"):
            if st in ex:
                p.add(st)
        if "current" in ex:
            p.add("can_start")
        return p

    # 3. Build the managed .gfx block; skip sets without a can_start source.
    blocks = []
    skipped = set()
    incomplete = []
    for suffix in managed:
        present = present_states(suffix)
        if "can_start" not in present:
            skipped.add(suffix)
            continue
        if present != {"unavailable", "can_start", "completed"}:
            incomplete.append(suffix)
        blocks.append(_set_block(suffix, present))
    emitted = [s for s in managed if s not in skipped]
    body = "\n\n".join(b.rstrip("\n") for b in blocks)
    managed_gfx = f"{GFX_BEGIN}\n\n{body}\n\n{GFX_END}\n"

    # 4. Read and parse styles_file before writing anything, so a read failure
    # does not leave gfx_file already overwritten with no rollback.
    styles_text = _read_lf(styles_file)
    styles_nl = _newline_of(styles_text)
    styles_text = styles_text.replace("\r\n", "\n").replace("\r", "\n")
    styles_text_stripped = _strip_region(styles_text, STYLE_BEGIN, STYLE_END)
    styled = set(
        re.findall(r"available\s*=\s*GFX_focus_can_start_joint_(\S+)", styles_text_stripped)
    )
    need_style = [s for s in emitted if s not in styled]
    if need_style:
        style_body = "\n\n".join(_style_block(s).rstrip("\n") for s in need_style)
        managed_styles = f"{STYLE_BEGIN}\n\n{style_body}\n\n{STYLE_END}\n"
        styles_text_out = styles_text_stripped.rstrip("\n") + "\n\n" + managed_styles
    else:
        styles_text_out = styles_text_stripped
    styles_text_out = _collapse_blanks(styles_text_out)

    # 5. All source data is ready — now write both files.
    gfx_text = _strip_region(gfx_text, GFX_BEGIN, GFX_END)
    removed = 0
    for suffix in emitted:
        for state in ("unavailable", "can_start", "current", "completed"):
            nm = f"GFX_focus_{state}_joint_{suffix}"
            while True:
                gfx_text, ok = _remove_block_by_name(gfx_text, nm)
                if not ok:
                    break
                removed += 1
    gfx_text = _remove_tag_headers(gfx_text, emitted)
    gfx_text = _collapse_blanks(gfx_text)

    insert_at = gfx_text.rfind("}")
    head = gfx_text[:insert_at].rstrip("\n")
    tail = gfx_text[insert_at:]
    gfx_text = f"{head}\n\n{managed_gfx}{tail}"
    _write_with_newline(gfx_file, gfx_text, gfx_nl)
    _write_with_newline(styles_file, styles_text_out, styles_nl)

    # 6. Report.
    print(
        f"{bcolors.OK}Title bars: {len(emitted)} managed set(s); "
        f"{removed} spriteType block(s) consolidated; "
        f"{len(need_style)} new style(s) added.{bcolors.RESET}"
    )
    if need_style:
        print(f"{bcolors.OK}New styles: {', '.join(need_style)}{bcolors.RESET}")
    if incomplete:
        print(
            f"{bcolors.WARNING}Incomplete sets (missing a state): "
            f"{', '.join(incomplete)}{bcolors.RESET}"
        )
    if skipped:
        print(
            f"{bcolors.FAIL}Skipped (no can_start source): "
            f"{', '.join(sorted(skipped))}{bcolors.RESET}"
        )
    if irregular_existing:
        print(
            f"{bcolors.INFO}Left untouched (irregular, hand-authored): "
            f"{', '.join(irregular_existing)}{bcolors.RESET}"
        )


if __name__ == "__main__":
    main()
