#!/usr/bin/env python3
import os, sys, fnmatch, re
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
gc = gspread.authorize(creds)

startTime = time.time()

__version__ = 1.0

def get_tags(rootDir):
    tags = []
    pos =0
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                hasTag = re.match(r'^[A-Z]{3}', line, re.M | re.I)  # If it's a tag
                if hasTag:
                    tags.append(hasTag.group())
                    pos +=1
    #input()
    return tags

def get_sheet_tags (sheet):
    sheet_tags = []

    for y, x in enumerate(sheet[0]):
        if x != "":
            sheet_tags.append(x)

    return sheet_tags

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
                            content += " " + b +"."+"Neutral_Green:0 \"£generic_Neutral_Green_small "+d +"\"\n"
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


def main():
    sheet = gc.open('Copy of Politics').sheet1
    content = sheet.get_all_values()

    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))
    tags = get_tags(rootDir + "/common/country_tags/00_countries.txt")
    sheetTags =  get_sheet_tags(content)

    #print(content)
    #input()

    #print(content)
    #input()

    for x in tags:
         if x not in sheetTags:
            print (str(x) + " is a country in game but wasn't found in the politics partyname sheet")

    #input()
    createPartNameLoc(rootDir, content)

    #print(len(sheet.row_values(1)))
    #data = sheet.get_all_records()

    print('The script took {0} second!'.format(time.time() - startTime))


if __name__ == "__main__":
    sys.exit(main())