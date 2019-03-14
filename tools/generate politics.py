#!/usr/bin/env python3
import os, sys, fnmatch, re
import time
import gspread
import unidecode
import string
from pathlib import Path
from oauth2client.service_account import ServiceAccountCredentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
gc = gspread.authorize(creds)

startTime = time.time()

__version__ = 1.0

#returns all tags from /common/country_tags/00_countries.txt
def get_tags(rootDir):
    tags = []
    pos =0
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                hasTag = re.match(r'^[A-Z]{3}', line, re.M | re.I)  # If it's a tag
                if hasTag:
                    tags.append([[[hasTag.group()]]])
                    pos +=1
    #input()
    return tags

#returns all sheet tags - may need to be fixed after picture fields were added
def get_sheet_tags (sheet):
    sheet_tags = []

    for y, x in enumerate(sheet[0]):
        if x != "":
            sheet_tags.append(x)

    return sheet_tags

#turns row numbers into excel/sheets drive row numbers e.g column 3 = column c in excel/sheets
def num_to_col_letters(num):
    letters = ''
    while num:
        mod = (num - 1) % 26
        letters += chr(mod + 65)
        num = (num - 1) // 26
    return ''.join(reversed(letters))

#Retrieves the tag from a filename (e/g ENG - United Kingdom.txt) and returns the index of said tag in the tag list
def get_tagPos(text, tags):
    isValidTag = re.match(r'^([A-Z]{3})\s.*-', text, re.M | re.I)  # If filename has a tag in it
    tagPos = -1
    b = ""
    if isValidTag:
        for pos, x in enumerate(tags):
            for y in x:
                # pos = 0
                for z in y:
                    for b in z:
                        if b == isValidTag.group(1):
                            tagPos = pos
                            return tagPos, b

#Returns the index of the tag in the tag list
def get_tagPos2(tag,tags):
    tagPos = -1
    for pos, x in enumerate(tags):
        for y in x:
            # pos = 0
            for z in y:
                for b in z:
                    if b == tag:
                        tagPos = pos
                        return tagPos

#Creates the localisation for the party names
def createPartNameLoc (rootDir, sheet):
    content = ""
    filepath = rootDir + "/localisation/MD_subideology_names.yml"
    content = "l_english:\n"
    for a, b in enumerate(sheet[0]):
        if b != "" or a != 0:
            for c in range(0,36):

                if c not in [0,1,2,3,9,17,31,37]:
                    if c > 36:
                        break
                    d = sheet[c][a]
                    #print(d)
                    #input()
                    #western
                    if not d.isspace():
                        if c == 4 and d != "":
                            content += " " + b +"."+"conservatism:0 \"£generic_conservatism_small "+d +"\"\n"
                            content += " " + b +"."+"conservatism_desc:0 \"" +"\"\n"
                        elif c == 5 and d != "":
                            content += " " + b +"."+"liberalism:0 \"£generic_liberalism_small "+d +"\"\n"
                            content += " " + b +"."+"liberalism_desc:0 \""+"\"\n"
                        elif c == 6 and d != "":
                            content += " " + b +"."+"socialism:0 \"£generic_socialism_small "+d +"\"\n"
                            content += " " + b +"."+"socialism_desc:0 \""+"\"\n"
                        elif c == 7 and d != "":
                            content += " " + b +"."+"Western_Autocracy:0 \"£generic_Western_Autocracy_small "+d +"\"\n"
                            content += " " + b +"."+"Western_Autocracy_desc:0 \"" +"\"\n"

                        #Emerging
                        elif c == 10 and d != "":
                            content += " " + b +"."+"Communist-State:0 \"£generic_Communist_State_small "+d +"\"\n"
                            content += " " + b +"."+"Communist-State_desc:0 \"" +"\"\n"
                        elif c == 11 and d != "":
                            content += " " + b +"."+"Conservative:0 \"£generic_Conservative_small "+d +"\"\n"
                            content += " " + b +"."+"Conservative_desc:0 \"" +"\"\n"
                        elif c == 12 and d != "":
                            content += " " + b +"."+"Autocracy:0 \"£generic_Autocracy_small "+d +"\"\n"
                            content += " " + b +"."+"Autocracy_desc:0 \"" +"\"\n"
                        elif c == 13 and d != "":
                            content += " " + b +"."+"Vilayat_e_Faqih:0 \"£generic_Vilayat_e_Faqih_small "+d +"\"\n"
                            content += " " + b +"."+"Vilayat_e_Faqih_desc:0 \"" +"\"\n"
                        elif c == 14 and d != "":
                            content += " " + b +"."+"Mod_Vilayat_e_Faqih:0 \"£generic_Mod_Vilayat_e_Faqih_small "+d +"\"\n"
                            content += " " + b +"."+"Mod_Vilayat_e_Faqih_desc:0 \"" +"\"\n"
                        elif c == 15 and d != "":
                            content += " " + b +"."+"anarchist_communism:0 \"£generic_anarchist_communism_small "+d +"\"\n"
                            content += " " + b +"."+"anarchist_communism:0 \"" +"\"\n"

                        #Salafist
                        elif c == 18 and d != "":
                            content += " " + b +"."+"Caliphate:0 \"£generic_Caliphate_small "+d +"\"\n"
                            content += " " + b +"."+"Caliphate_desc:0 \"" +"\"\n"
                        elif c == 19 and d != "":
                            content += " " + b +"."+"Kingdom:0 \"£generic_Kingdom_small "+d +"\"\n"
                            content += " " + b +"."+"Kingdom_desc:0 \"" +"\"\n"

                        #Non-Alligned
                        elif c == 22 and d != "":
                            content += " " + b +"."+"Neutral_conservatism:0 \"£generic_Neutral_conservatism_small "+d +"\"\n"
                            content += " " + b +"."+"Neutral_conservatism_desc:0 \"" +"\"\n"
                        elif c == 23 and d != "":
                            content += " " + b +"."+"oligarchism:0 \"£generic_oligarchism_small "+d +"\"\n"
                            content += " " + b +"."+"oligarchism_desc:0 \"" +"\"\n"
                        elif c == 24 and d != "":
                            content += " " + b +"."+"neutral_Social:0 \"£generic_neutral_Social_small "+d +"\"\n"
                            content += " " + b +"."+"neutral_Social_desc:0 \"" +"\"\n"
                        elif c == 25 and d != "":
                            content += " " + b +"."+"Neutral_Libertarian:0 \"£generic_Neutral_Libertarian_small "+d +"\"\n"
                            content += " " + b +"."+"Neutral_Libertarian_desc:0 \"" +"\"\n"
                        elif c == 26 and d != "":
                            content += " " + b +"."+"Neutral_Autocracy:0 \"£generic_Neutral_Autocracy_small "+d +"\"\n"
                            content += " " + b +"."+"Neutral_Autocracy_desc:0 \"" +"\"\n"
                        elif c == 27 and d != "":
                            content += " " + b +"."+"Neutral_Communism:0 \"£generic_Neutral_Communism_small "+d +"\"\n"
                            content += " " + b +"."+"Neutral_Communism_desc:0 \"" +"\"\n"
                        elif c == 28 and d != "":
                            content += " " + b +"."+"Neutral_Muslim_Brotherhood:0 \"£muslim_brotherhood_small "+d +"\"\n"
                            content += " " + b +"."+"Neutral_Muslim_Brotherhood_desc:0 \"" +"\"\n"
                        elif c == 29 and d != "":
                            content += " " + b +"."+"Neutral_green:0 \"£generic_Neutral_Green_small "+d +"\"\n"
                            content += " " + b +"."+"Neutral_Green_desc:0 \"" +"\"\n"

                        #Nationalist
                        elif c == 32 and d != "":
                            content += " " + b +"."+"Nat_Autocracy:0 \"£generic_Nat_Autocracy_small "+d +"\"\n"
                            content += " " + b +"."+"Nat_Autocracy_desc:0 \"" +"\"\n"
                        elif c == 33 and d != "":
                            content += " " + b +"."+"Nat_Fascism:0 \"£generic_Nat_Fascism_small "+d +"\"\n"
                            content += " " + b +"."+"Nat_Fascism_desc:0 \"" +"\"\n"
                        elif c == 34 and d != "":
                            content += " " + b +"."+"Nat_Populism:0 \"£generic_Nat_Populism_small "+d +"\"\n"
                            content += " " + b +"."+"Nat_Populism_desc:0 \"" +"\"\n"
                        elif c == 35 and d != "":
                            content += " " + b +"."+"Monarchist:0 \"£generic_Monarchist_small "+d +"\"\n"
                            content += " " + b +"."+"Monarchist_desc:0 \"" +"\"\n"








                    #input()

    f = open(filepath, "w")
    with open(filepath, 'w', encoding='utf-8', errors='ignore') as file:
        file.write(content)

#Called by createPartyLeaders and Returns the country_leader = {... content
def generateLeaderContent(content, rowInSheet, leaderName, picName, extraLeaders, tagPos):
    ideology = ""
    if rowInSheet == 2:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = conservatism\n"
            content += "\ttraits = {\n"
            content += "\t\twestern_conservatism\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "conservatism"
        subIdeology = "western_conservatism"

    elif rowInSheet == 3:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = liberalism\n"
            content += "\ttraits = {\n"
            content += "\t\twestern_liberalism\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "liberalism"
        subIdeology = "western_liberalism"

    elif rowInSheet == 4:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = socialism\n"
            content += "\ttraits = {\n"
            content += "\t\twestern_socialism\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "socialism"
        subIdeology = "western_socialism"

    elif rowInSheet == 5:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Western_Autocracy\n"
            content += "\ttraits = {\n"
            content += "\t\twestern_Western_Autocracy\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Western_Autocracy"
        subIdeology = "western_Western_Autocracy"

    # Emerging
    elif rowInSheet == 7:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Communist-State\n"
            content += "\ttraits = {\n"
            content += "\t\temerging_Communist-State\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Communist-State"
        subIdeology = "emerging_Communist"

    elif rowInSheet == 8:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Conservative\n"
            content += "\ttraits = {\n"
            content += "\t\temerging_Conservative\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "emerging_Conservative"
        subIdeology = "Monarchist"

    elif rowInSheet == 9:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Autocracy\n"
            content += "\ttraits = {\n"
            content += "\t\temerging_Autocracy\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Autocracy"
        subIdeology = "emerging_Autocracy"

    elif rowInSheet == 10:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Vilayat_e_Faqih\n"
            content += "\ttraits = {\n"
            content += "\t\temerging_Vilayat_e_Faqih\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Vilayat_e_Faqih"
        subIdeology = "emerging_Vilayat_e_Faqih"

    elif rowInSheet == 11:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Mod_Vilayat_e_Faqih\n"
            content += "\ttraits = {\n"
            content += "\t\temerging_Vilayat_e_Faqih_ref\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Mod_Vilayat_e_Faqih"
        subIdeology = "emerging_Vilayat_e_Faqih_ref"

    elif rowInSheet == 12:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = anarchist_communism\n"
            content += "\ttraits = {\n"
            content += "\t\temerging_anarchist_communism\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "anarchist_communism"
        subIdeology = "emerging_anarchist_communism"

    # Salafist
    elif rowInSheet == 14:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Caliphate\n"
            content += "\ttraits = {\n"
            content += "\t\tsalafist_Caliphate\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Caliphate"
        subIdeology = "salafist_Caliphate"

    elif rowInSheet == 15:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Kingdom\n"
            content += "\ttraits = {\n"
            content += "\t\tsalafist_Kingdom\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Kingdom"
        subIdeology = "salafist_Kingdom"


    # Non-Alligned
    elif rowInSheet == 17:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Neutral_conservatism\n"
            content += "\ttraits = {\n"
            content += "\t\tneutrality_Neutral_conservatism\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Neutral_conservatism"
        subIdeology = "neutrality_Neutral_conservatism"

    elif rowInSheet == 18:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = oligarchism\n"
            content += "\ttraits = {\n"
            content += "\t\tneutrality_oligarchism\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "oligarchism"
        subIdeology = "neutrality_oligarchism"

    elif rowInSheet == 19:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = neutral_Social\n"
            content += "\ttraits = {\n"
            content += "\t\tneutrality_neutral_Social\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "neutral_Social"
        subIdeology = "neutrality_neutral_Social"

    elif rowInSheet == 20:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Neutral_Libertarian\n"
            content += "\ttraits = {\n"
            content += "\t\tneutrality_Neutral_Libertarian\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Neutral_Libertarian"
        subIdeology = "neutrality_Neutral_Libertarian"

    elif rowInSheet == 21:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Neutral_Autocracy\n"
            content += "\ttraits = {\n"
            content += "\t\tneutrality_Neutral_Autocracy\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Neutral_Autocracy"
        subIdeology = "neutrality_Neutral_Autocracy"

    elif rowInSheet == 22:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Neutral_Communism\n"
            content += "\ttraits = {\n"
            content += "\t\tneutrality_Neutral_Communism\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Neutral_Communism"
        subIdeology = "neutrality_Neutral_Communism"

    elif rowInSheet == 23:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Neutral_Muslim_Brotherhood\n"
            content += "\ttraits = {\n"
            content += "\t\tneutrality_Neutral_Muslim_Brotherhood\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Neutral_Muslim_Brotherhood"
        subIdeology = "neutrality_Neutral_Muslim_Brotherhood"

    elif rowInSheet == 24:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Neutral_green\n"
            content += "\ttraits = {\n"
            content += "\t\tneutrality_Neutral_green\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Neutral_green"
        subIdeology = "neutrality_Neutral_green"


    # Nationalist
    elif rowInSheet == 26:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Nat_Autocracy\n"
            content += "\ttraits = {\n"
            content += "\t\tnationalist_Nat_Autocracy\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Nat_Autocracy"
        subIdeology = "nationalist_Nat_Autocracy"

    elif rowInSheet == 27:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Nat_Fascism\n"
            content += "\ttraits = {\n"
            content += "\t\tnationalist_Nat_Fascism\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Nat_Fascism"
        subIdeology = "nationalist_Nat_Fascism"

    elif rowInSheet == 28:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Nat_Populism\n"
            content += "\ttraits = {\n"
            content += "\t\tnationalist_Nat_Populism\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Nat_Populism"
        subIdeology = "nationalist_Nat_Populism"

    elif rowInSheet == 29:
        if leaderName != "":
            content += "create_country_leader = {\n"
            content += "\tname = \"" + leaderName + "\"\n"
            content += "\tpicture = \"" + picName + "\"\n"
            content += "\tideology = Monarchist\n"
            content += "\ttraits = {\n"
            content += "\t\tnationalist_Monarchist\n"
            content += "\t}\n"
            content += "}\n"
        ideology = "Monarchist"
        subIdeology = "nationalist_Monarchist"

    #content = generateLeaderContent(content, rowInSheet, leaderName, picName, extraLeaders, tagPos)

    if ideology != "" and tagPos is not None:
        found = 0
        extraLeaderName = ""
        extraLeaderPic = ""
        for pos, x in enumerate(extraLeaders[tagPos]):
            for pos2, y in enumerate(x):
                if found == 0:
                    for pos3, z in enumerate(y):
                        #print(z)
                        #input()
                        #if pos2 == 1:
                            #print(z)
                        #if pos2 == 4:
                            #print(z)
                            #print(d + " " + ideology)
                            if z == ideology:
                                #print("###Duplicate ideology " + z)
                                #print(extraLeaders[tagPos][pos][1][0])
                                #input()
                                found = 1
                                try:

                                    extraLeaderName = extraLeaders[tagPos][pos][1][0]
                                except:
                                    time.sleep(0)
                                try:
                                    extraLeaderPic = extraLeaders[tagPos][pos][2][0]
                                except:
                                    time.sleep(0)

                                content += "create_country_leader = {\n"
                                content += "\tname = \"" + extraLeaderName + "\"\n"
                                content += "\tpicture = " + extraLeaderPic + "\n"
                                content += "\tideology = " + ideology + "\n"
                                content += "\ttraits = {\n"
                                content += "\t\t" + subIdeology + "\n"
                                content += "\t}\n"
                                content += "}\n"

        #input()
    return content

#Returns correctly formated leader name (e.g removing accents) and returns leaderpics list
def generateLeaderPic(leaderName, picList):
    if leaderName.isspace() and leaderName == "":
        picList.append("")
    else:
        leaderName = leaderName.replace('\r', '')
        leaderName = leaderName.replace('\n', '')
        leaderName = leaderName.replace('\t', '')
        leaderName = leaderName.lstrip()
        leaderName = leaderName.rstrip()
        picName = leaderName.replace('.', '')
        picName = picName.replace(',', '')
        picName = picName.replace('-', '_')
        picName = picName.replace('’', '')
        picName = picName.replace('Dr', '')
        picName = picName.replace('Adm', '')
        picName = picName.replace('Sir', '')
        picName = unidecode.unidecode(picName)
        picName = picName.replace(' ', '_') + ".dds"
        picName = picName.lstrip('_')
        picName = picName.rstrip('_')
        if picName == ".dds":
            picList.append("")
        else:
            picList.append(picName.lower())

    return leaderName, picList

#Writes the formatted leaderNames and leaderPics to the excel sheet. No longer used, was used at start of project
def leadersToSheet(a, b, blank, picList, worksheet):
    if a & 1:
        # print(a)
        # print(num_to_col_letters(int(a+2)))
        #print("Updating portrait file names in spreadsheet for " + b)
        z = 0

        for x in picList:
            # print(str(z) + ": " + x)
            z += 1
            if x != "":
                blank = 1

        if blank == 1:
            cellTop = str(num_to_col_letters(int(a + 2))) + "2"
            cellBot = str(num_to_col_letters(int(a + 2))) + "30"

            # print(cellTop + ":" + cellBot)
            ## Select a cell range
            cell_list = worksheet.range(cellTop + ":" + cellBot)

            # Update values
            g = 0
            for cell in cell_list:
                cell.value = picList[g]
                g += 1

            # Send update in batch mode
            worksheet.update_cells(cell_list)
            time.sleep(1.5)

#Will check the leaders pulled from game files vs the leaders in the spreadsheet and removes extra's from the
#Extra leaders list
def delExtraLeaders(sheet, extraLeaders, tags):
    for a, b in enumerate(sheet[0]):
        if b != "" or a != 0:
            for c in range(0,31):

                if len(b) ==3 and c not in [0,1,6,13,16,25]:
                    if c > 36:
                        break
                    d = sheet[c][a]
                    tagPos = get_tagPos2(b,tags)
                    found = 0
                    if tagPos is not None and d != "":
                        found = 0
                        for pos, x in enumerate(extraLeaders[tagPos]):
                            for pos2, y in enumerate(x):
                                if found == 0:
                                    for pos3, z in enumerate(y):
                                        if pos2 == 1:
                                            if z == d:
                                                print("Found a duplicate leader in extra leaders: " + z)
                                                #print(extraLeaders[tagPos][pos])
                                                try:
                                                    del extraLeaders[tagPos][pos][0:6]
                                                    #print(extraLeaders[tagPos][pos])
                                                    #input
                                                except:
                                                    time.sleep(0)
                                                break


                                else:
                                    break
                            if found == 1:
                                break

    return extraLeaders

#Writes the extra leaders to the sheet
def extraLeadersToSheet(extraLeaders, sheet, sheetName, tags):
    rows = 0
    country = []
    leaderName = []
    leaderPicture = []
    expire = []
    ideology = []
    traits = []
    for a, tag in enumerate(tags):
        for pos, x in enumerate(extraLeaders[a]):
            #print(x)
            #input()
            for pos2, y in enumerate(x):
                #print(x)

                #print(rows)
                #input()
                for pos3, z in enumerate(y):
                    text = str(z)
                    text = text.replace('"', '')
                    found = 0
                    if pos2 == 0:

                        #input()
                        rows += 1
                        # print(z)
                        # input()
                        try:
                            country.append(text)
                        except:
                            country.append("")

                        try:
                            extraLeaders[a][pos][pos2+1][pos3]
                        except:
                            leaderName.append("")
                            #print(extraLeaders)
                            #print(extraLeaders[a])
                            #print(extraLeaders[a][pos])
                            #print("WTF")
                            #input()
                        else:
                            text = extraLeaders[a][pos][pos2 + 1][pos3]
                            text = text.replace('"', '')
                            leaderName.append(text)

                        try:
                            extraLeaders[a][pos][pos2+2][pos3]
                        except:
                            leaderPicture.append("")
                        else:
                            text = extraLeaders[a][pos][pos2 + 2][pos3]
                            text = text.replace('"', '')
                            leaderPicture.append(text)

                        try:
                            extraLeaders[a][pos][pos2+3][pos3]
                        except:
                            expire.append("")
                        else:
                            text = extraLeaders[a][pos][pos2 + 3][pos3]
                            text = text.replace('"', '')
                            expire.append(text)


                        try:
                            extraLeaders[a][pos][pos2+4][pos3]
                        except:
                            ideology.append("")
                        else:
                            text = extraLeaders[a][pos][pos2 + 4][pos3]
                            text = text.replace('"', '')
                            ideology.append(text)

                        try:
                            extraLeaders[a][pos][pos2 + 5][pos3][0]
                        except:
                            traits.append("")
                        else:
                            #print(extraLeaders[a][pos][pos2 + 5][pos3][0])
                            #input()
                            text = ""
                            for x in extraLeaders[a][pos][pos2 + 5][pos3]:
                                text += x + " "
                                #print(x)
                            print(extraLeaders[a][pos][pos2 + 1][pos3])
                            print(text)
                            traits.append(text)

    #print(rows)
    #input()

    worksheet = sheet.worksheet(sheetName)
    #worksheet = sheet.add_worksheet(title=sheetName, rows=rows, cols="20")
    for x in range(1,7):
        cellTop = str(num_to_col_letters(int(x))) + "1"
        cellBot = str(num_to_col_letters(int(x))) + str(rows)

        print(cellTop)
        print(cellBot)

        # print(cellTop + ":" + cellBot)
        ## Select a cell range
        cell_list = worksheet.range(cellTop + ":" + cellBot)

        if x == 1:
            value = country
        if x == 2:
            value = leaderName
        if x == 3:
            value = leaderPicture
        if x == 4:
            value = expire
        if x == 5:
            value = ideology
        if x == 6:
            value = traits
        # Update values
        g = 0
        for cell in cell_list:

           # try:
                #print(value[g])
            cell.value = value[g]
                #print("did this")
            #except:
            #    cell.value = ""
            g += 1

        # Send update in batch mode
        worksheet.update_cells(cell_list)
        #time.sleep(1.5)
        print("updated column")

    print("done updating")
    return extraLeaders

###Main Function used to begin writting leaders to in game text files###
def createPartyLeaders (rootDir, sheet, filepath, extraLeaders, tags):
    extraLeaders = delExtraLeaders(sheet, extraLeaders, tags)
    content = ""
    for a, b in enumerate(sheet[0]):
        if (b != "" or a != 0) and len(b) == 3:
            picList = []
            content += "###" + b + "###\n"
            for c in range(0,31):

                if c not in [0,1,6,13,16,25]:
                    if c > 36:
                        break
                    leaderName = sheet[c][a]
                    try:
                        picName = sheet[c][a+1]
                    except:
                        picName = ""
                    leaderName, picList = generateLeaderPic(leaderName, picList)
                    filePic = Path(rootDir + "/gfx/leaders/" + b + "/" + picName)
                    if picName != "" and not os.path.isfile(rootDir + "/gfx/leaders/" + b + "/" + picName) and not os.path.isfile(rootDir + "/gfx/leaders/" + b + "/" + picName.lower()):
                        print("Expected a picture for " + b + " leader " + leaderName + " named " + "/gfx/leaders/"+b+"/"+picName)
                    tagPos = get_tagPos2(b,tags)
                    content = generateLeaderContent(content, c, leaderName, picName, extraLeaders, tagPos)
                    #print("done here")
                    #input()
                elif c in [1,6,13,16,25]:
                    picList.append("")

            blank = 0
            #
            #leadersToSheet(a, b, blank, picList, worksheet)





    #worksheet = sheet.worksheet('Extra Leaders')



    f = open(filepath, "w")
    with open(filepath, 'w', encoding='utf-8', errors='ignore') as file:
        file.write(content)

    return extraLeaders

###Main Function used to pull spreadsheet voter popularity & turn it into subideology values & write to ingame txt file
def createSubIdeologyValues (rootDir, sheet, filepath, worksheet):
    content = ""
    for a, b in enumerate(sheet[0]):
        if b != "" or a != 0:
            subIdeology = []
            content += "###" + b + "###\n"
            for c in range(0,30):
                if c not in [1,6,13,16,26]:
                    if c > 36:
                        break
                    d = sheet[c][a]
                    #print(d)
                    #input()
                    #western
                    if c == 2 and d != "" and not d.isspace():
                       subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 3 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 4 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 5 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    #Emerging
                    elif c == 7 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 8 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 9 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 10 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 11 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 12 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    #Salafist
                    elif c == 14 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 15 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    #Non-Alligned
                    elif c == 17 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 18 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 19 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 20 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 21 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 22 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 23 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 24 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    #Nationalist
                    elif c == 26 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 27 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 28 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    elif c == 29 and d != "" and not d.isspace():
                        subIdeology.append(str(round((0.01 * float(d)),3)))
                    else:
                        subIdeology.append("0")

            del subIdeology[0]
            democratic = float(subIdeology[0]) + float(subIdeology[1]) + float(subIdeology[2]) + float(subIdeology[3])
            communism = float(subIdeology[4]) + float(subIdeology[4]) + float(subIdeology[5]) + float(subIdeology[6]) + float(subIdeology[7]) + float(subIdeology[8]) + float(subIdeology[9])
            Salafist = float(subIdeology[10]) + float(subIdeology[11])
            neutrality = float(subIdeology[12]) + float(subIdeology[13]) + float(subIdeology[14]) + float(subIdeology[15]) \
                         + float(subIdeology[16]) + float(subIdeology[17]) + float(subIdeology[18]) + float(subIdeology[19])
            nationalist = float(subIdeology[20]) + float(subIdeology[21]) + float(subIdeology[22]) + float(subIdeology[23])

            content += "set_politics = {\n"
            content += "\tparties = {\n"
            content += "\t\tdemocratic = { #western\n"
            content += "\t\t\tpopularity = " + str(round ((100 * democratic),2)) + " \n"
            content += "\t\t}\n"
            content += "\t\tcommunism = { #Emerging\n"
            content += "\t\t\tpopularity = " + str(round ((100 * communism),2)) + " \n"
            content += "\t\t}\n"
            content += "\t\tfascism = { #Salafist\n"
            content += "\t\t\tpopularity = " + str(round ((100 * Salafist),2)) + " \n"
            content += "\t\t}\n"
            content += "\t\tneutrality = { #neutrality\n"
            content += "\t\t\tpopularity = " + str(round ((100 * neutrality),2)) + " \n"
            content += "\t\t}\n"
            content += "\t\tnationalist = { #nationalist\n"
            content += "\t\t\tpopularity = " + str(round ((100 * nationalist),2)) + " \n"
            content += "\t\t}\n"
            content += "\t}\n"
            content += "\truling_party = \n"
            content += "\tlast_election = \"\"\n"
            content += "\telection_frequency = \"\"\n"
            content += "\telections_allowed = \"\"\n"
            content += "}\n"
            #western
            content += "set_variable = { conservatism_pop = " + subIdeology[0] + " }\n"
            content += "set_variable = { liberalism_pop = " + subIdeology[1] + " }\n"
            content += "set_variable = { socialism_pop = " + subIdeology[2] + " }\n"
            content += "set_variable = { Western_Autocracy_pop = " + subIdeology[3] + " }\n"
            #emerging
            content += "set_variable = { Communist-State = " + subIdeology[4] + " }\n"
            content += "set_variable = { Conservative_pop = " + subIdeology[5] + " }\n"
            content += "set_variable = { Autocracy_pop = " + subIdeology[6] + " }\n"
            content += "set_variable = { Vilayat_e_Faqih_pop = " + subIdeology[7] + " }\n"
            content += "set_variable = { Mod_Vilayat_e_Faqih_pop = " + subIdeology[8] + " }\n"
            content += "set_variable = { anarchist_communism_pop = " + subIdeology[9] + " }\n"
            #salafist
            content += "set_variable = { Caliphate_pop = " + subIdeology[10] + " }\n"
            content += "set_variable = { Kingdom_pop = " + subIdeology[11] + " }\n"
            #non-alligned
            content += "set_variable = { Neutral_conservatism_pop = " + subIdeology[12] + " }\n"
            content += "set_variable = { oligarchism_pop = " + subIdeology[13] + " }\n"
            content += "set_variable = { neutral_Social_pop = " + subIdeology[14] + " }\n"
            content += "set_variable = { Neutral_Libertarian_pop = " + subIdeology[15] + " }\n"
            content += "set_variable = { Neutral_Autocracy_pop = " + subIdeology[16] + " }\n"
            content += "set_variable = { Neutral_Communism_pop = " + subIdeology[17] + " }\n"
            content += "set_variable = { Neutral_Muslim_Brotherhood_pop = " + subIdeology[18] + " }\n"
            #nationalist
            content += "set_variable = { Neutral_Green_pop = " + subIdeology[19] + " }\n"
            content += "set_variable = { Nat_Autocracy_pop = " + subIdeology[20] + " }\n"
            content += "set_variable = { Nat_Fascism_pop = " + subIdeology[21] + " }\n"
            content += "set_variable = { Nat_Populism_pop = " + subIdeology[22] + " }\n"
            content += "set_variable = { Monarchist_pop = " + subIdeology[23] + " }\n"
            content += "recalculate_party = yes\n\n\n"








                    #input()
    f = open(filepath, "w")
    with open(filepath, 'w', encoding='utf-8', errors='ignore') as file:
        file.write(content)

#Pulls extra 2000 leaders from in game history/country files, formats them & creates new list
def getExtraLeaders2000(rootDir, tags, tagPos, tag):
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        foundLeader = 0
        openBrace = 0
        startDate = 0
        leaders = tags

        #leaders[tagPos].append([[]]) #LeaderPictures
        #leaders[tagPos].append([[]]) #LeaderExpire
        #leaders[tagPos].append([[]]) #leaderIdeology
        #leaders[tagPos].append([[]]) #leaderTraits
        leaderCount = -1
        #print(tag)
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                if "2000.1.1" in line:
                    startDate = 1
                if "2017.1.1" in line:
                    startDate = 2
                if startDate == 1:
                    if "create_country_leader" in line:
                        foundLeader = 1
                        hasTraits = 0
                        traits = []
                        hasTraits = 0
                        leaderCount += 1
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])

                    if foundLeader ==1:
                        if "{" in line:
                            openBrace +=1
                        if "}" in line:
                            openBrace -= 1
                    if openBrace ==0 and foundLeader == 1 :
                        foundLeader = 0
                        leaders[tagPos].append([])
                        #print(leaders[tagPos])
                        #input()
                        if traits:
                            leaders[tagPos][leaderCount][5].append(traits)

                    if openBrace ==1:
                        #and ("name" in line or "type" in line):
                        leaderName = re.search(r'name\s?=\s?\"(.*)\"', line, re.M | re.I)  # If it's a tag
                        leaderPicture = re.search(r'picture\s?=\s?(.*)', line, re.M | re.I)  # If it's a tag
                        leaderExpire = re.search(r'expire\s?=\s?\"(.*)\"', line, re.M | re.I)  # If it's a tag
                        leaderIdeology = re.search(r'ideology\s?=\s?\b(.*)\b', line, re.M | re.I)  # If it's a tag



                        if leaderName:
                            leaders[tagPos][leaderCount][1].append(leaderName.group(1))
                            newtag = [tag]
                            leaders[tagPos][leaderCount][0] = newtag


                        if leaderPicture:
                            leaders[tagPos][leaderCount][2].append(leaderPicture.group(1))
                            #print(leaderPicture.group(1))
                            #input()
                        if leaderExpire:
                            leaders[tagPos][leaderCount][3].append(leaderExpire.group(1))
                            #print(leaderExpire.group(1))
                            #input()
                        if leaderIdeology:
                           # print(leaders[tagPos])
                            leaders[tagPos][leaderCount][4].append(leaderIdeology.group(1))
                            #print(leaderIdeology.group(1))
                            #input()


                    if openBrace == 2:

                        if hasTraits ==1:
                            #print("has traits")
                            leaderTraits = re.search(r'\s\b(.*)\b', line, re.M | re.I)  # If it's a tag
                            if leaderTraits:
                                traits.append(leaderTraits.group(1))
                                #print(leaderTraits.group(1))
                                #input()
                        if "traits" in line:
                            hasTraits = 1


    return leaders

#Pulls extra 2017 leaders from in game history/country files, formats them & creates new list
def getExtraLeaders2017(rootDir, tags, tagPos, tag):
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        foundLeader = 0
        openBrace = 0
        startDate = 0
        leaders = tags

        #leaders[tagPos].append([[]]) #LeaderPictures
        #leaders[tagPos].append([[]]) #LeaderExpire
        #leaders[tagPos].append([[]]) #leaderIdeology
        #leaders[tagPos].append([[]]) #leaderTraits
        leaderCount = -1
        #print(tag)
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                if "2017.1.1" in line:
                    startDate = 2
                if startDate == 2:
                    if "create_country_leader" in line:
                        foundLeader = 1
                        hasTraits = 0
                        traits = []
                        hasTraits = 0
                        leaderCount += 1
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])
                        leaders[tagPos][leaderCount].append([])

                    if foundLeader ==1:
                        if "{" in line:
                            openBrace +=1
                        if "}" in line:
                            openBrace -= 1
                    if openBrace ==0 and foundLeader == 1 :
                        foundLeader = 0
                        leaders[tagPos].append([])
                        if traits:
                            leaders[tagPos][leaderCount][5].append(traits)

                    if openBrace ==1:
                        #and ("name" in line or "type" in line):
                        leaderName = re.search(r'name\s?=\s?\"(.*)\"', line, re.M | re.I)  # If it's a tag
                        leaderPicture = re.search(r'picture\s?=\s?(.*)', line, re.M | re.I)  # If it's a tag
                        leaderExpire = re.search(r'expire\s?=\s?\"(.*)\"', line, re.M | re.I)  # If it's a tag
                        leaderIdeology = re.search(r'ideology\s?=\s?\b(.*)\b', line, re.M | re.I)  # If it's a tag
                        if leaderName:
                            leaders[tagPos][leaderCount][1].append(leaderName.group(1))
                            newtag = [tag]
                            leaders[tagPos][leaderCount][0] = newtag


                        if leaderPicture:
                            leaders[tagPos][leaderCount][2].append(leaderPicture.group(1))
                            #print(leaderPicture.group(1))
                            #input()
                        if leaderExpire:
                            leaders[tagPos][leaderCount][3].append(leaderExpire.group(1))
                            #print(leaderExpire.group(1))
                            #input()
                        if leaderIdeology:
                           # print(leaders[tagPos])
                            leaders[tagPos][leaderCount][4].append(leaderIdeology.group(1))
                            #print(leaderIdeology.group(1))
                            #input()


                    if openBrace == 2:

                        if hasTraits ==1:
                            #print("has traits")
                            leaderTraits = re.search(r'\s\b(.*)\b', line, re.M | re.I)  # If it's a tag
                            if leaderTraits:
                                traits.append(leaderTraits.group(1))
                                #print(leaderTraits.group(1))
                                #input()
                        if "traits" in line:
                            hasTraits = 1



    return leaders

def createPartyContent2 (organizedLeaders, tag, ideology):
    content = ""
    leader = 1
    leaderCounter2 = 0
    for pos2, b in enumerate(organizedLeaders):
        if organizedLeaders[pos2][0][0] == tag:
            #print ("here")
            if organizedLeaders[pos2][4][0] == ideology:
                #print("here2")
                if leader ==1:
                    content += "\t\tif = { limit = { check_variable = { " + ideology + "_leader = " + str(leader - 1) + " } }\n"
                else:
                    content += "\t\tif = { limit = { check_variable = { " + ideology + "_leader = " + str(leader - 1) + " NOT = { check_variable = { b = 1 } } } }\n"
                content += "\t\t\tset_variable = { " + ideology + "_leader = 1 }\n"
                content += "\t\t\tkill_country_leader = yes\n\n"
                content += "\t\t\tcreate_country_leader = {\n"
                content += "\t\t\t\tname = \"" + organizedLeaders[pos2][2][0] + "\"\n"
                content += "\t\t\t\tpicture = \"" + organizedLeaders[pos2][3][0] + "\"\n"
                content += "\t\t\t\tideology = " + organizedLeaders[pos2][4][0] + "\n"
                content += "\t\t\t\ttraits = {\n"
                content += ""
                content += "\t\t\t\t}\n"
                content += "\t\t\t}\n\n"
                content += "\t\t\tif = { limit = { has_country_flag = do_not_retire } subtract_from_variable = {" + ideology + "_leader = 1 } }\n"
                if organizedLeaders[pos2][1][0] == "2017":
                    content += "\t\t\tset_temp_variable = { b = 1 }\n"
                else:
                    content += "\t\t\tif = { limit = { date < 2016.1.2 } set_temp_variable = { b = 1 } } #skip if 2017\n"
                content += "\t\t}\n"

                leader += 1
                try:
                    del organizedLeaders[pos2][0:5]
                except:
                    time.sleep(0)
                #print("here3")
    content += "\t}\n"

    return content

def createPartyLeaders2 (rootDir, organizedLeaders):
    inGameTags = get_tags(rootDir + "/common/country_tags/00_countries.txt")

    for tag in inGameTags:
        content = ""
        count = 1
        for pos, a in enumerate(organizedLeaders):
            #print(tag[0][0][0])
            #print(organizedLeaders[pos][0][0])
            #input()

            if tag[0][0][0] == organizedLeaders[pos][0][0]:
                ideology = organizedLeaders[pos][4][0]

                if count != 1 and ideology == organizedLeaders[pos][4][0]:
                    content += "\telse_if = { limit = { has_country_flag = set_" + ideology + " }\n"
                    content += createPartyContent2(organizedLeaders, tag[0][0][0], ideology)
                    #print(organizedLeaders[pos])

                if count ==1:
                    count += 1


                    #print("hello")
                    content += "set_leader_" + tag[0][0][0] +" = {\n\n"
                    content += "\tif = { limit = { has_country_flag = set_" + ideology + " }\n\n"

                    content += createPartyContent2( organizedLeaders, tag[0][0][0], ideology)

        content += "}"
        print(content)
        input()


    return "hello"

#Returns the ideology and trait dependent on the row in the spreadsheet, similar to what is used in generateLeaderContent
def getIdeology(c):
    ideology = ""
    traits = ""

    if c == 2:
        ideology = "conservatism"
        traits = "western_conservatism"

    elif c == 3:
        ideology = "liberalism"
        traits = "western_liberalism"

    elif c == 4:
        ideology = "socialism"
        traits = "western_socialism"

    elif c == 5:
        ideology = "Western_Autocracy"
        traits = "western_Western_Autocracy"

    # Emerging
    elif c == 7:
        ideology = "Communist-State"
        traits = "emerging_Communist"

    elif c == 8:
        ideology = "emerging_Conservative"
        traits = "Monarchist"

    elif c == 9:
        ideology = "Autocracy"
        traits = "emerging_Autocracy"

    elif c == 10:
        ideology = "Vilayat_e_Faqih"
        traits = "emerging_Vilayat_e_Faqih"

    elif c == 11:
        ideology = "Mod_Vilayat_e_Faqih"
        traits = "emerging_Vilayat_e_Faqih_ref"

    elif c == 12:
        ideology = "anarchist_communism"
        traits = "emerging_anarchist_communism"

        # Salafist
    elif c == 14:
        ideology = "Caliphate"
        traits = "salafist_Caliphate"

    elif c == 15:
        ideology = "Kingdom"
        traits = "salafist_Kingdom"

        # Non-Alligned
    elif c == 17:
        ideology = "Neutral_conservatism"
        traits = "neutrality_Neutral_conservatism"

    elif c == 18:
        ideology = "oligarchism"
        traits = "neutrality_oligarchism"

    elif c == 19:
        ideology = "neutral_Social"
        traits = "neutrality_neutral_Social"

    elif c == 20:
        ideology = "Neutral_Libertarian"
        traits = "neutrality_Neutral_Libertarian"

    elif c == 21:
        ideology = "Neutral_Autocracy"
        traits = "neutrality_Neutral_Autocracy"

    elif c == 22:
        ideology = "Neutral_Communism"
        traits = "neutrality_Neutral_Communism"

    elif c == 23:
        ideology = "Neutral_Muslim_Brotherhood"
        traits = "neutrality_Neutral_Muslim_Brotherhood"

    elif c == 24:
        ideology = "Neutral_green"
        traits = "neutrality_Neutral_green"

        # Nationalist
    elif c == 26:
        ideology = "Nat_Autocracy"
        traits = "nationalist_Nat_Autocracy"

    elif c == 27:
        ideology = "Nat_Fascism"
        traits = "nationalist_Nat_Fascism"

    elif c == 28:
        ideology = "Nat_Populism"
        traits = "nationalist_Nat_Populism"

    elif c == 29:
        ideology = "Monarchist"
        traits = "nationalist_Monarchist"
    else:
        ideology = "ERROR"
        traits = "ERROR"

    return ideology, traits

#Will return the index of the tag in the organizedLeader list
def getTagPos3(organizedLeaders, tag, startDate):
    lastPos = 0

    for pos, a in enumerate(organizedLeaders):
        #print(organizedLeaders[pos][1][0])
        #print(organizedLeaders[pos][0][0])
        #print(tag)
        if organizedLeaders[pos][0][0] == tag:
            #print(organizedLeaders[pos][0][0])
            #print(tag)
            #input()
            lastPos = pos
            if organizedLeaders[pos][1][0] == startDate:
                lastPos = pos
            #if startDate == "2017":
                #print("get tag pos3")
                #print(organizedLeaders[pos][1][0])
                #print(organizedLeaders[pos][0][0])
                #print(tag)
                #print(pos)
                #print("end of get tag pos 3")

    #print(tag)
    #print(len(organizedLeaders))
    #print(pos)
    #input()
    #print(lastPos)
    #input()
    return lastPos

#Sorts and organizes all leaders into a new organized list
def sortLeaders(leaders2000, leaders2017, extraLeaders2000, extraLeaders2017, organizedLeaders):




    for a, b in enumerate(leaders2000[0]):
        if (b != "" or a != 0) and len(b) == 3:
            for c in range(0, 31):
                if c not in [0, 1, 6, 13, 16, 25]:
                    if c > 36:
                        break
                    leaderName = leaders2000[c][a]
                    if leaders2000[c][a+1] != "":
                        leaderPic = leaders2000[c][a+1]
                    else:
                        leaderPic = "generic.dds"

                    ideology, traits = getIdeology(c)


                    if leaderName != "":
                        organizedLeaders.append([[b], ["2000"] ,[leaderName],[leaderPic], [ideology],[traits]])

    for a, b in enumerate(extraLeaders2000):
        if extraLeaders2000[a][1] != "":
            startDate = "2000"
            tag = extraLeaders2000[a][0]
            leaderName = extraLeaders2000[a][1]
            if extraLeaders2000[a][2] != "":
                leaderPic = extraLeaders2000[a][2]
            else:
                leaderPic = "generic.dds"
            if extraLeaders2000[a][4] != "":
                ideology = extraLeaders2000[a][4]
            else:
                ideology = "ERROR"
            if extraLeaders2000[a][5] != "":
                hasTraits = re.findall(r'[A-Za-z0-9_]+', extraLeaders2000[a][5])
                traits = hasTraits
                #input()
            else:
                traits = "ERROR"

            pos = getTagPos3(organizedLeaders, tag, startDate)
            if pos == 0:

                organizedLeaders.insert(len(organizedLeaders) +1, [[tag], [startDate], [leaderName], [leaderPic], [ideology], [traits]])
                #print(len(organizedLeaders))
                #print("ERROR")
                #input()
            else:
                organizedLeaders.insert(pos+1,[[tag],[startDate],[leaderName],[leaderPic],[ideology],[traits]])
                #print(pos)
                #print(leaderName)
                #print(organizedLeaders[pos])
                #print(organizedLeaders[pos+1])
                #input()


    for a, b in enumerate(leaders2017[0]):
        if (b != "" or a != 0) and len(b) == 3:
            for c in range(0, 31):
                if c not in [0, 1, 6, 13, 16, 25]:
                    if c > 36:
                        break
                    leaderName = leaders2017[c][a]
                    if leaders2017[c][a+1] != "":
                        leaderPic = leaders2017[c][a+1]
                    else:
                        leaderPic = "generic.dds"

                    ideology, traits = getIdeology(c)


                    if leaderName != "":
                        startDate = "2017"
                        tag = b
                        pos = getTagPos3(organizedLeaders, tag, startDate)
                        if pos == 0:

                            organizedLeaders.insert(len(organizedLeaders) + 1,
                                                    [[b], ["2017"] ,[leaderName],[leaderPic], [ideology],[traits]])
                            #print("ERROR")
                            #print(len(organizedLeaders))
                            #print(pos)
                            #print(organizedLeaders[-2])
                            #print(organizedLeaders[-1])
                            #input()
                        else:
                            organizedLeaders.insert(pos + 1, [[b], ["2017"] ,[leaderName],[leaderPic], [ideology],[traits]])
                            #print(len(organizedLeaders))
                           # print(pos)
                            #print(leaderName)
                            #print(organizedLeaders[pos])
                            #print(organizedLeaders[pos + 1])
                            #input()



    print("done")
    #input()
    return organizedLeaders

def main():
    sheet = gc.open('Politics') #Opens the politics sheet
    worksheet = sheet.worksheet('Party Name') #sets active worksheet as party Name
    content = worksheet.get_all_values() #downloads content of worksheet

    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))

    # Retrieves all in game tags
    tags = get_tags(rootDir + "/common/country_tags/00_countries.txt")

    # Retrieves all sheet tags
    sheetTags = get_sheet_tags(content)

    # Create party name localiastion
    createPartNameLoc(rootDir, content)

    organizedLeaders = []

    extraLeaders = []

    for root, dirnames, filenames in os.walk(rootDir + '/' + 'history' + '/countries' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            tagPos, tag = get_tagPos(filename, tags)
            if tagPos != -1:
                #print(filename)
                extraLeaders += getExtraLeaders2000(os.path.join(root, filename), tags, tagPos, tag)

    worksheet = sheet.worksheet('Party Leader 2000')
    content = worksheet.get_all_values()
    leaders2000 = worksheet.get_all_values()
    worksheet = sheet.worksheet('Party Leader 2017')
    leaders2017 = worksheet.get_all_values()
    worksheet = sheet.worksheet('2000 Extra Leaders')
    extraLeaders2000 = worksheet.get_all_values()
    worksheet = sheet.worksheet('2017 Extra Leaders')
    extraLeaders2017 = worksheet.get_all_values()
    organizedLeaders = sortLeaders(leaders2000, leaders2017, extraLeaders2000, extraLeaders2017, organizedLeaders)

    createPartyLeaders2(rootDir, organizedLeaders)
    print("fini")
    input()
    extraLeaders = createPartyLeaders(rootDir, content, (rootDir + "/Modding resources/generated/generated_2000_leaders.txt"),
                       extraLeaders, tags)

    print("done")
    input()
    input()
    input()

    sheetName = "2000 Extra Leaders"
    extraLeadersToSheet(extraLeaders, sheet, sheetName, tags)


    tags = get_tags(rootDir + "/common/country_tags/00_countries.txt")
    tag = ""
    extraLeaders = []
    for root, dirnames, filenames in os.walk(rootDir + '/' + 'history' + '/countries' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            tagPos, tag = get_tagPos(filename, tags)
            if tagPos != -1:
                #print(filename)
                extraLeaders += getExtraLeaders2017(os.path.join(root, filename), tags, tagPos, tag)

    worksheet = sheet.worksheet('Party Leader 2017')
    content = worksheet.get_all_values()
    extraLeaders = createPartyLeaders(rootDir, content, (rootDir + "/Modding resources/generated/generated_2017_leaders.txt"),
                       extraLeaders, tags)

    sheetName = "2017 Extra Leaders"
    extraLeadersToSheet(extraLeaders, sheet, sheetName, tags)

    worksheet = sheet.worksheet('Vote Share 2000')
    content = worksheet.get_all_values()
    createSubIdeologyValues(rootDir, content,(rootDir + "/Modding resources/generated/generated_2000_politics.txt"),worksheet)

    worksheet = sheet.worksheet('Vote Share 2017')
    content = worksheet.get_all_values()
    createSubIdeologyValues(rootDir, content,(rootDir + "/Modding resources/generated/generated_2017_politics.txt"),worksheet)

    #print(len(sheet.row_values(1)))
    #data = sheet.get_all_records()

    print('The script took {0} second!'.format(time.time() - startTime))


if __name__ == "__main__":
    sys.exit(main())