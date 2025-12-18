#!/usr/bin/env python3
import fnmatch
import os
import re
import sys
import time

######################
# The directory with all the files

scriptDir = os.path.realpath(__file__)
rootDir = os.path.dirname(os.path.dirname(scriptDir))

files = []

######################
# Finds all files


for root, dirnames, filenames in os.walk(
    rootDir + "/" + "history" + "/countries" + "/"
):
    for filename in fnmatch.filter(filenames, "*.txt"):
        files.append(os.path.join(root, filename))

ideas = []
seen = set()

######################
# Finds all ideas that exist

for F in files:
    file = open(F, "r", encoding="utf-8")
    setupfound = False
    donefound = False
    ideasfound = False
    for line in file:
        # print(line)
        line.strip()
        if line == "}\n":
            setupfound = False
            donefound = False
        if line == "\t}\n":
            ideasfound = False
        if (setupfound == True or donefound == True) and ideasfound == True:
            if line not in seen:
                seen.add(line)
                ideas.append(line)
        if line == "\ufeff2000.1.1 = {\n":
            setupfound = True
        if line == "2017.1.1 = {\n":
            donefound = True
        if line == "\tadd_ideas = {\n":
            ideasfound = True

    file.close()

######################
# Sorts all values in categoized arrays
gdp = []
tax_cost = []
pop = []
corruption = []
youth_radicalization = []
growth = []
defence = []
edu = []
health = []
social = []
bureau = []
police = []
army = []
women = []
intervention = []
officers = []
press = []
cartel = []
religion = []
law = []
unions = []
meetings = []
trade = []
parties = []
borders = []
industries = []
other = []

# categories = [gdp,tax_cost,pop,corruption,growth,defence,edu,health,social,bureau,police,army,women,intervention,officers,press,law,unions,meetings,religion,trade,cartel]

######################
# Took the keywords from localization mostly

for idea in ideas:
    if "gdp" in idea:
        gdp.append(idea)
    elif "tax_cost" in idea:
        tax_cost.append(idea)
    elif "pop" in idea:
        pop.append(idea)
    elif "corruption" in idea:
        corruption.append(idea)
    elif "defence" in idea:
        defence.append(idea)
    elif "edu" in idea:
        edu.append(idea)
    elif "health" in idea:
        health.append(idea)
    elif "social" in idea:
        social.append(idea)
    elif "bureau" in idea:
        bureau.append(idea)
    elif "police" in idea:
        police.append(idea)
    elif "army" in idea or "no_military" in idea:
        army.append(idea)
    elif "women" in idea:
        women.append(idea)
    elif "intervention" in idea:
        intervention.append(idea)
    elif (
        "growth" in idea
        or "boom" in idea
        or "stagnation" in idea
        or "recession" in idea
        or "depression" in idea
    ):
        growth.append(idea)
    elif "cartel" in idea:
        cartel.append(idea)
    elif "press" in idea:
        press.append(idea)
    elif "officer" in idea:
        officers.append(idea)
    elif "union" in idea:
        unions.append(idea)
    elif "meeting" in idea:
        meetings.append(idea)
    elif (
        "economy" in idea and "opium" not in idea
    ):  # there is an Opium Economy idea which is not part of trade
        trade.append(idea)
    elif (
        "theocracy" in idea
        or "state_religion" in idea
        or "secular" in idea
        or "atheist" in idea
    ):
        religion.append(idea)
    elif "law" in idea or "hybrid" in idea or "tribalism" in idea:
        law.append(idea)
    elif "border" in idea or "love_it_or" in idea or "visa" in idea or "haven" in idea:
        borders.append(idea)
    elif "parties" in idea or "gerrymandering" in idea or "ballots" in idea:
        parties.append(idea)
    elif "###" not in idea:
        other.append(idea)


# So now to the editing

categories = [
    gdp,
    tax_cost,
    pop,
    corruption,
    growth,
    defence,
    edu,
    health,
    social,
    bureau,
    police,
    army,
    women,
    intervention,
    officers,
    press,
    law,
    unions,
    meetings,
    religion,
    trade,
    borders,
    parties,
    cartel,
]
# dict = {"gdp": "","tax_cost": "","pop": "","corruption": "","growth": "","defence": "","edu": "","health": "","social": "","bureau": "","police": "","army": "","women": "","intervention": "",


for F in files:

    indexed = []
    values = []
    others = []
    File = []
    # init_values = []
    late_values = []

    ######################
    # Reads File

    file = open(F, "r", encoding="utf-8")

    ######################
    # Used to keep track of location within file

    setupfound = False
    donefound = False
    ideasfound = False
    removefound = False

    found = False
    # i = 0
    # j = 0
    # ints = 999
    for line in file:
        # print(line)
        line.strip()
        if line == "}\n":
            setupfound = False
            donefound = False
        if line == "\t}\n":
            ideasfound = False
        if "}" in line:
            removefound = False
        if donefound == True and "remove_ideas = {" in line:
            print(
                F
            )  # Because of how I progammed it it messes up countries that already have remove_ideas thing :(
            removefound = True

        ######################
        # Copies Ideas within 2000 add_ideas = {} in values/others

        if setupfound == True and ideasfound == True:
            for cat in categories:
                for idea in cat:
                    if line == idea:
                        values.append(line)
                        # init_values.append(line)
                        indexed.append(categories.index(cat))
            for idea in other:
                if line == idea:
                    others.append(line)
                    # init_values.append(line)

        ######################
        # Copies Ideas within 2017 add_ideas = {} in late_values and in values (if no newer value was provided in 2000) and in others if they dont already exist

        if donefound == True and ideasfound == True:

            for cat in categories:
                for c in cat:
                    if line == c:
                        if categories.index(cat) not in indexed:
                            values.append(line)
                            indexed.append(categories.index(cat))
                            found = True
                        late_values.append(line)
            if found == True:
                found = False
            else:
                for idea in other:
                    if line == idea:
                        if line not in others:
                            others.append(line)
                        late_values.append(line)

        ######################
        # Puts (almost) all line in a List so it can write them later
        # Ignores the add_ideas and remove_ideas things

        if ideasfound == False and not (donefound == True and removefound == True):
            File.append(line)
            # print(line)

        ######################
        # Note: order for these things is important
        ##### if(donefound == True and "remove_ideas = {" in line):
        #####     removefound = True
        # Was at the beggining of the file so the actual "remove_ideas = {" line will NOT be added in the file, while add_ideas will

        if line == "\ufeff2000.1.1 = {\n":
            setupfound = True
        if line == "2017.1.1 = {\n":
            donefound = True
        if line == "\tadd_ideas = {\n":
            ideasfound = True
            # if(j<ints):
            # ints = j

        # j = j+1

    file.close()

    # print(indexed)

    # print(File)

    # categories = [gdp,tax_cost,pop,corruption,growth,defence,edu,health,social,bureau,police,army,women,intervention]

    ######################
    # Checks if any necessary values are missing
    # Could be used to assign defaults as well

    if 0 not in indexed:
        values.append("\t\t### No GDP laws added\n")
    if 1 not in indexed:
        values.append("\t\t### No Tax_cost laws added!!\n")
        # print(F)
    if 2 not in indexed:
        values.append("\t\t### No POP laws added\n")
    if 3 not in indexed:
        values.append("\t\t### No corruption laws added\n")
    if 4 not in indexed:
        values.append("\t\t### No GROWTH laws added\n")
    if 5 not in indexed:
        values.append("\t\t### No defence laws added\n")
    if 6 not in indexed:
        values.append("\t\t### No edu laws added\n")
    if 7 not in indexed:
        values.append("\t\t### No health laws added\n")
    if 8 not in indexed:
        values.append("\t\t### No social laws added\n")
    if 9 not in indexed:
        values.append("\t\t### No bureau laws added\n")
    if 10 not in indexed:
        values.append("\t\t### No police laws added\n")
    if 11 not in indexed:
        values.append("\t\t### No army laws added\n")
    if 12 not in indexed:
        values.append("\t\t### No women army laws added\n")
    if 13 not in indexed:
        values.append("\t\t### No intervention laws added\n")
    if 14 not in indexed:
        values.append("\t\t### No officer laws added\n")
    if 15 not in indexed:
        values.append("\t\t### No press laws added\n")
    if 16 not in indexed:
        values.append("\t\t### No law laws added\n")
    if 17 not in indexed:
        values.append("\t\t### No unions laws added\n")
    if 18 not in indexed:
        values.append("\t\t### No meetings laws added\n")
    if 19 not in indexed:
        values.append("\t\t### No religion laws added\n")
    if 20 not in indexed:
        values.append("\t\t### No trade laws added\n")
    if 21 not in indexed:
        values.append("\t\t### No borders laws added\n")
    if 22 not in indexed:
        values.append("\t\t### No party laws added\n")
    # categories = [gdp,tax_cost,pop,corruption,growth,defence,edu,health,social,bureau,police,army,women,intervention,officers,press,law,unions,meetings,religion,trade,cartel]

    # print(values)
    # print(others)

    ######################
    # Note: it's the same file; the loop did not end yet

    ######################
    # Wites the File from scratch

    file = open(F, "w", encoding="utf-8")
    donefound = False
    ideasfound = False
    for line in File:
        # print(line)
        # line.strip()

        ######################
        # adds the 2000 ideas

        if donefound == False and ideasfound == True:
            # print("#####")
            # print(F)
            # print(values)
            # file.write("\t\t########\n")
            # print ("wtf")
            for val in values:
                # print(val)
                file.write(val)
                # print (val)
            for val in others:
                file.write(val)
            ideasfound = False

        ######################
        # adds the 2017 ideas

        if donefound == True and ideasfound == True:
            # print("Hi")
            for val in late_values:
                if (val not in values) and (val not in others):
                    if "###" not in val:
                        file.write(val)
                        # print("hi")
            ideasfound = False

        if "2017.1.1 = {" in line:
            donefound = True
            # print("done")
        if "add_ideas = {" in line:
            ideasfound = True
            # print("ideas")
        if "}" in line:
            ideasfound = False
            # print("##")

        ######################
        # Again, order is imprtant; This gets written before the "add_ideas = {" line
        # It writes the remove_ideas part

        if donefound == True and ideasfound == True:
            file.write("\tremove_ideas = {\n")
            for val in values:
                if val not in late_values:
                    if "###" not in val:
                        file.write(val)
            for val in others:
                if val not in late_values:
                    if "###" not in val:
                        file.write(val)
            file.write("\t}\n")

        file.write(line)

    file.close()

    values.clear()
    others.clear()
    indexed.clear()
    File.clear()
    late_values.clear()

    ######################
    # My Debug part

    # print(late_values)
    # print(values)
    # print(others)
    # print(values)

# print (File)

# for line in File:
#     print (line)

# print(others)

# print(values)

# for val in values:
#     print(val)
# for val in others:
#     print(val)

# print(gdp)
# print("############")
# print(tax_cost)
# print(pop)
# print(corruption)
# print(growth)
# print(defence)
# print(edu)
# print(health)
# print(social)
# print(bureau)
# print(police)
# print(army)
# print(women)
# print(intervention)
# print(industries)
# print(other)


# print(ideas)


print("Done!")
