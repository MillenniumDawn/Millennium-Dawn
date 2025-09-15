#!/usr/bin/env python3
import codecs
import fnmatch
import os
import re
import string
import sys
import time
from pathlib import Path

import gspread
import unidecode
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
gc = gspread.authorize(creds)

startTime = time.time()

__version__ = 1.0


# returns all tags from /common/country_tags/00_countries.txt
def get_tags(rootDir):
    tags = []
    pos = 0
    with open(rootDir, "r", encoding="utf8", errors="ignore") as file:
        content = file.readlines()
        for line in content:
            if not line.startswith("#") or line.startswith(
                ""
            ):  # If the line doesn't start with a comment or blank
                hasTag = re.match(r"^[A-Z]{3}", line, re.M | re.I)  # If it's a tag
                if hasTag:
                    tags.append([[[hasTag.group()]]])
                    pos += 1
    # input()
    return tags


# returns all sheet tags - may need to be fixed after picture fields were added
def get_sheet_tags(sheet):
    sheet_tags = []

    for y, x in enumerate(sheet):
        if y >= 3:
            if x[1] != "":
                sheet_tags.append(x[1])
                # print(x[1])
    return sheet_tags


# Creates the influence variables
def createInfluenceVariables2000(rootDir, sheet, filename):
    content = ""
    filepath = rootDir + "/Modding resources/generated/" + filename
    for y, x in enumerate(sheet):
        if y >= 3:
            if x[2] != "" and x[2] != 0:
                content += "\t### " + x[1] + " ###\n\t#Influence system\n"
                for c in range(0, 24):
                    if c not in [0, 3, 6, 9, 12, 15, 18, 21, 24]:
                        if x[c] != "":
                            if c in [4, 7, 10, 13, 16, 19, 22]:
                                tag = x[c]
                            if c == 2:
                                content += (
                                    "\tset_variable = { var = domestic_influence_amount value = "
                                    + x[c]
                                    + " }\n"
                                )
                            if c == 5:
                                content += (
                                    "\tset_variable = { var = influencer1"
                                    " value = " + tag + ".id }\n"
                                )
                                content += (
                                    "\tset_variable = { var = influencer1_amount value = "
                                    + x[c]
                                    + " }\n"
                                )
                            if c == 8:
                                content += (
                                    "\tset_variable = { var = influencer2"
                                    " value = " + tag + ".id }\n"
                                )
                                content += (
                                    "\tset_variable = { var = influencer2_amount value = "
                                    + x[c]
                                    + " }\n"
                                )
                            if c == 11:
                                content += (
                                    "\tset_variable = { var = influencer3"
                                    " value = " + tag + ".id }\n"
                                )
                                content += (
                                    "\tset_variable = { var = influencer3_amount value = "
                                    + x[c]
                                    + " }\n"
                                )
                            if c == 14:
                                content += (
                                    "\tset_variable = { var = influencer4"
                                    " value = " + tag + ".id }\n"
                                )
                                content += (
                                    "\tset_variable = { var = influencer4_amount value = "
                                    + x[c]
                                    + " }\n"
                                )
                            if c == 17:
                                content += (
                                    "\tset_variable = { var = influencer5"
                                    " value = " + tag + ".id }\n"
                                )
                                content += (
                                    "\tset_variable = { var = influencer5_amount value = "
                                    + x[c]
                                    + " }\n"
                                )
                            if c == 20:
                                content += (
                                    "\tset_variable = { var = influencer6"
                                    " value = " + tag + ".id }\n"
                                )
                                content += (
                                    "\tset_variable = { var = influencer6_amount value = "
                                    + x[c]
                                    + " }\n"
                                )
                            if c == 23:
                                content += (
                                    "\tset_variable = { var = influencer7"
                                    " value = " + tag + ".id }\n"
                                )
                                content += (
                                    "\tset_variable = { var = influencer7_amount value = "
                                    + x[c]
                                    + " }\n"
                                )
                content += "\tstartup_influence = yes\n\n"
                # print(content)
                # input()

    f = open(filepath, "w+")
    with open(filepath, "w+", encoding="utf8", errors="ignore") as file:
        file.write(content)
        file.close()


def main():
    sheet = gc.open("influence")  # Opens the politics sheet
    worksheet = sheet.worksheet("2000 Influence")  # sets active worksheet as party Name
    content = worksheet.get_all_values()  # downloads content of worksheet

    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))

    # Retrieves all in game tags
    tags = get_tags(rootDir + "/common/country_tags/00_countries.txt")

    # Retrieves all sheet tags
    sheetTags = get_sheet_tags(content)

    for y, x in enumerate(tags):
        if x[0][0][0] not in sheetTags:
            print("No entry in influence sheet for " + x[0][0][0])
            # input()

    createInfluenceVariables2000(rootDir, content, "influence_values_2000.txt")

    worksheet = sheet.worksheet("2017 Influence")  # sets active worksheet as party Name
    content = worksheet.get_all_values()  # downloads content of worksheet
    sheetTags = get_sheet_tags(content)

    for y, x in enumerate(tags):
        if x[0][0][0] not in sheetTags:
            print("No entry in influence sheet for " + x[0][0][0])
            # input()

    createInfluenceVariables2000(rootDir, content, "influence_values_2017.txt")

    print("The script took {0} second!".format(time.time() - startTime))


if __name__ == "__main__":
    sys.exit(main())
