#!/usr/bin/env python3
import fnmatch
import os
import re
import sys
import time

startTime = time.time()

__version__ = 1.0


def get_tag(text):
    isValidTag = re.match(
        r"^([A-Z]{3}).*.txt", text, re.M | re.I
    )  # If filename has a tag in it
    tag = "blank"
    if isValidTag:
        tag = isValidTag.group(1)

    return tag


def analyzeMyOOB(filename, root, rootDir):
    newContent = ""
    oldContent = ""
    with open(
        os.path.join(root, filename), "r", encoding="utf-8", errors="ignore"
    ) as file:
        content = file.readlines()
        newContent = ""
        startDate = 0
        for line in content:

            newContent += line
            if "2000.1.1" in line:
                startDate = 1
            if startDate == 1:
                if "oob =" in line:
                    newFile = (
                        rootDir
                        + "/"
                        + "history"
                        + "/units"
                        + "/"
                        + get_tag(filename)
                        + "_2000_naval_mtg.txt"
                    )
                    if os.path.isfile(newFile):
                        # print(newFile)
                        # input()
                        newContent += "\tif = {\n"
                        newContent += "\t\tlimit = {\n"
                        newContent += '\t\t\thas_dlc = "Man the Guns"\n'
                        newContent += "\t\t}\n"
                        newContent += (
                            '\t\tset_naval_oob = "'
                            + get_tag(filename)
                            + '_2000_naval_mtg"\n'
                        )
                        newContent += "\t\telse = {\n"
                        newContent += (
                            '\t\t\tset_naval_oob = "'
                            + get_tag(filename)
                            + '_2000_naval_legacy"\n'
                        )
                        newContent += "\t\t}\n"
                        newContent += "\t}\n"
                        # print(newContent)
                        # input()
            if "2017.1.1" in line:
                startDate = 2
            if startDate == 2:
                if "oob =" in line:
                    newFile = (
                        rootDir
                        + "/"
                        + "history"
                        + "/units"
                        + "/"
                        + get_tag(filename)
                        + "_2017_naval_mtg.txt"
                    )
                    if os.path.isfile(newFile):
                        newContent += "\tif = {\n"
                        newContent += "\t\tlimit = {\n"
                        newContent += '\t\t\thas_dlc = "Man the Guns"\n'
                        newContent += "\t\t}\n"
                        newContent += (
                            '\t\tset_naval_oob = "'
                            + get_tag(filename)
                            + '_2017_naval_mtg"\n'
                        )
                        newContent += "\t\telse = {\n"
                        newContent += (
                            '\t\t\tset_naval_oob = "'
                            + get_tag(filename)
                            + '_2017_naval_legacy"\n'
                        )
                        newContent += "\t\t}\n"
                        newContent += "\t}\n"
                        # print(newContent)
                        # input()

    with open(
        os.path.join(root, filename), "w", encoding="utf-8", errors="ignore"
    ) as file:
        file.write(newContent)

    return filename


def main():

    bad_count = 0
    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))
    global totalErrors
    totalErrors = 0
    for root, dirnames, filenames in os.walk(
        rootDir + "/" + "history" + "/countries" + "/"
    ):
        for filename in fnmatch.filter(filenames, "*.txt"):
            analyzeMyOOB(filename, root, rootDir)
            # input()

    print(
        "The script took {0} second!".format(time.time() - startTime)
        + " therea are a total of: "
        + str(totalErrors)
        + " errors."
    )

    return bad_count


if __name__ == "__main__":
    sys.exit(main())
