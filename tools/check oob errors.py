#!/usr/bin/env python3
import os, sys, fnmatch, re
import time

startTime = time.time()

__version__ = 1.0


def get_tags(rootDir):
    tags = []
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                hasTag = re.match(r'^[A-Z]{3}', line, re.M | re.I)  # If it's a tag
                if hasTag:
                    tags.append(hasTag.group())
    return tags

def get_2000_tech(rootDir):
    tech = []
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        foundTech = 0
        openBrace = 0
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank

                if "set_technology" in line:
                    foundTech = 1
                if foundTech ==1:
                    if "{" in line:
                        openBrace =1
                    if "}" in line:
                        openBrace = 0
                        foundTech = 0
                        break
                if foundTech ==1 and openBrace ==1:
                    hasTech = re.match(r'\s(.*)\s=\s1', line, re.M | re.I)  # If it's a tag
                    #if hasTech:
                        #print(hasTech.group(1))
    #input()
    return tech

def get_tech(rootDir, tags):
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        foundTech = 0
        openBrace = 0
        startDate = 0
        updatedTags = tags
        updatedTags = [tags,[[]]]
        print(updatedTags[0])
        print(updatedTags[0][1])
        print(updatedTags[1][0])

        input()
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                if "2000.1.1" in line:
                    startDate = 1
                if startDate == 1:
                    if "set_technology" in line:
                        foundTech = 1
                    if foundTech ==1:
                        if "{" in line:
                            openBrace =1
                        if "}" in line:
                            openBrace = 0
                            foundTech = 0

                    if openBrace ==1:
                        hasTech = re.match(r'\s(.*)\s=\s1', line, re.M | re.I)  # If it's a tag
                        if hasTech:
                            #print(hasTech.group(1))
                            updatedTags[tagPos].append(["abc"])
                if "2017.1.1" in line:
                    startDate = 2
                if startDate == 2:
                    if "set_technology" in line:
                        foundTech = 1
                    if foundTech ==1:
                        if "{" in line:
                            openBrace =1
                        if "}" in line:
                            openBrace = 0
                            foundTech = 0

                    if openBrace ==1:
                        hasTech = re.match(r'\s(.*)\s=\s1', line, re.M | re.I)  # If it's a tag
                        if hasTech:
                            #print(hasTech.group(1))
                            updatedTags.insert(tagPos, [[hasTech.group(1)]])
    #print(tech[0][0])
    #print(tech[1][0])


    #input()
    return updatedTags

def get_2000_variants(rootDir):
    tech = []
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        foundTech = 0
        openBrace = 0
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank

                if "set_technology" in line:
                    foundTech = 1
                if foundTech == 1:
                    if "{" in line:
                        openBrace = 1
                    if "}" in line:
                        openBrace = 0
                        foundTech = 0
                        break
                if foundTech == 1 and openBrace == 1:
                    hasTech = re.match(r'\s(.*)\s=\s1', line, re.M | re.I)  # If it's a tag
                    # if hasTech:
                    # print(hasTech.group(1))
    # input()
    return tech


def main():
    files_list = []
    nation_focus_files = []
    idea_files = []
    bad_count = 0
    tags = []
    hasAirBases = []
    global tagPos
    tagPos = -1
    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))

    tags = get_tags(rootDir + "/common/country_tags/00_countries.txt")
    #tags.append(temp)
    #for pos, x in enumerate(temp):
     #   tags.append(x[])

    #print(tags)
    #print(tags[0])
    #print(tags[0][0])
    #print(tags[0][0][0])
    #input()

    for root, dirnames, filenames in os.walk(rootDir + '/' + 'history' + '/countries' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            print(filename)
            isValidTag = re.match(r'^([A-Z]{3})\s.*-', filename, re.M | re.I)  # If filename has a tag in it
            if isValidTag and isValidTag.group(1) in tags:
             #print("valid tag")
             #input()
             tagPos = -1
             #print(isValidTag.group(1))
             for position, item in enumerate(tags):
                if item == isValidTag.group(1):
                    tagPos = position
            if tagPos != -1:
                tags = get_tech((os.path.join(root, filename)), tags)
                print(tags[tagPos][0][0])
                print(tags[tagPos][1][0])

                #for x in temp:
                    #tags[tagPos][0][0].append(x)





    print('The script took {0} second!'.format(time.time() - startTime))

    return bad_count


if __name__ == "__main__":
    sys.exit(main())