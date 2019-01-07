#!/usr/bin/env python3
import os, sys, fnmatch, re
import time

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
                    tags.append([[hasTag.group()]])
                    pos +=1
    #input()
    return tags

def get_tech(rootDir, tags):
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        foundTech = 0
        openBrace = 0
        startDate = 0
        updatedTags = tags
        updatedTags[tagPos].append([])
        updatedTags[tagPos].append([])

        #input()
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
                        hasTech = re.search(r'[ \t]+(.*)\s=\s1', line, re.M | re.I)  # If it's a tag
                        if hasTech:
                           #updatedTags[tagPos].append([])
                           updatedTags[tagPos][1].append(hasTech.group(1))

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
                        hasTech = re.search(r'[ \t]+(.*)\s=\s1', line, re.M | re.I)  # If it's a tag
                        if hasTech:
                            #updatedTags[tagPos].append([])
                            updatedTags[tagPos][2].append(hasTech.group(1))
                            #print(updatedTags[tagPos][2])
        #print(updatedTags[tagPos][1])
        #print(updatedTags[tagPos][2])
        #input()
    return updatedTags

def get_variants(rootDir, tags):
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        foundVariant = 0
        openBrace = 0
        startDate = 0
        variants = tags
        variants[tagPos].append([[]])
        variants[tagPos].append([[]])
        variantCount = 0

        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                if "2000.1.1" in line:
                    startDate = 1
                if startDate == 1:
                    if "create_equipment_variant" in line:
                        foundVariant = 1
                    if foundVariant ==1:
                        if "{" in line:
                            openBrace +=1
                        if "}" in line:
                            openBrace -= 1
                    if openBrace ==0:
                        foundVariant = 0

                    if openBrace ==1 and ("name" in line or "type" in line):
                        variantName = re.search(r'name\s=\s\"(.*)\"', line, re.M | re.I)  # If it's a tag
                        variantType = re.search(r'type\s=\s(.*)', line, re.M | re.I)  # If it's a tag
                        if variantName:
                            variants[tagPos][3][0].append([variantName.group(1)])
                            variantCount +=1
                        if variantType:
                            variants[tagPos][3][0].append(variantType.group(1))

                if "2017.1.1" in line:
                    startDate = 2
                if startDate == 2:
                    if "create_equipment_variant" in line:
                        foundVariant = 1
                    if foundVariant ==1:
                        if "{" in line:
                            openBrace +=1
                        if "}" in line:
                            openBrace -= 1
                    if openBrace ==0:
                        foundVariant = 0

                    if openBrace ==1 and ("name" in line or "type" in line):
                        variantName = re.search(r'name\s=\s\"(.*)\"', line, re.M | re.I)  # If it's a tag
                        variantType = re.search(r'type\s=\s(.*)', line, re.M | re.I)  # If it's a tag
                        if variantName:
                            variants[tagPos][4][0].append(variantName.group(1))
                            variantCount += 1
                        if variantType:
                            variants[tagPos][4][0].append(variantType.group(1))
    return variants

def analyzeMyVariants(tags):
    variants = tags
    for pos, x in enumerate(tags[tagPos]):
        if pos ==0:
            print("~~~~tag:~~~~")
        if pos ==1:
            print("~~~2000 tech:~~~")
        if pos ==2:
            print("~~~2017 tech:~~~")
        if pos ==3:
            print("~~~2000 var:~~~")
        if pos ==4:
            print("~~~2017 var:~~~")

        for y in x:
            if pos != 3 and pos != 4:
                print (y)
            else:
                #input()
                for pos1, z in enumerate(y):
                    print(z)
                input()
    return variants

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

    for root, dirnames, filenames in os.walk(rootDir + '/' + 'history' + '/countries' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            isValidTag = re.match(r'^([A-Z]{3})\s.*-', filename, re.M | re.I)  # If filename has a tag in it

            if isValidTag:
                tagPos = -1
                for pos, x in enumerate(tags):
                    for y in x:
                        #pos = 0
                        for z in y:
                            if z == isValidTag.group(1):
                                tagPos = pos
                                tags = get_tech((os.path.join(root, filename)), tags)
                                tags = get_variants((os.path.join(root, filename)), tags)
                                tags = analyzeMyVariants(tags)





    print('The script took {0} second!'.format(time.time() - startTime))

    return bad_count


if __name__ == "__main__":
    sys.exit(main())