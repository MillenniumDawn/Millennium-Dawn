#!/usr/bin/env python3
import os, sys, fnmatch, re
import time

startTime = time.time()

__version__ = 1.0

def get_tags (rootDir):
    tags = []
    with open(rootDir, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                hasTag = re.match(r'^[A-Z]{3}', line, re.M | re.I)  # If it's a tag
                if hasTag:
                    tags.append(hasTag.group())
    return tags


def check_focus_tree_file_name (focus_tree_files):
    bad_count_file = 0
    for file in focus_tree_files:
        rightFormet = re.match(r'^[A-Z]{3}_.*', file, re.M | re.I)  # If it's a tag
        if not rightFormet:
            bad_count_file += 1
            #print ("ERROR: The filename of " + file + " does not meet our standards. Rename the file to TAG_focus_name.txt")

    return bad_count_file


def check_ideas (filename):
    bad_count_file = 0
    notanidea = ["allowed", "modifier", "country", "allowed_civil_war", "OR", "AND", "ideas", "NOT", "CANCEL",
        "on_add", "available", "ai_will_do", "rule"]

    notanidea = [element.lower() for element in notanidea]
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        for line in content:
            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                hasIdea = re.search(r'([A-Za-z0-9_-]+) = {', line, re.M | re.I)  # If it's a tag
                if hasIdea:
                    idea = hasIdea.group(1)
                    #if str.lower(hasIdea.group(1)) not in notanidea:
                        #print (hasIdea.group(1))

    return bad_count_file


def findPdxSyntax (filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        typeOfCode = 0 #1 = trigger, 2 = effects
        for line in content:
            if "TRIGGER DOCUMENTATION" in line: #check for triggers
                typeOfCode = 1
                print(typeOfCode)
            if typeOfCode == 1:
                isTrigger = re.search(r'^([A-Z_-]+)', line, re.M | re.I)  # If it's a tag
                #print ("test")
                print(isTrigger.group(1))


    return typeOfCode
def main():
    print("Validating Basic Style - Secondary Check")

    files_list = []
    nation_focus_files = []
    idea_files = []
    bad_count = 0
    tags = []
    global countryTriggers
    global stateTriggers

    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))

    tags = get_tags(rootDir + "/common/country_tags/00_countries.txt")
    findPdxSyntax(rootDir + "/Modding resources/List of triggers and effects 1_5_4.txt")
    #for i in tags:
    #   print(i)



    for root, dirnames, filenames in os.walk(rootDir + '/'+ 'common' + '/national_focus' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            nation_focus_files.append(os.path.join(root, filename))
    bad_count = bad_count + check_focus_tree_file_name(nation_focus_files)

    for root, dirnames, filenames in os.walk(rootDir + '/' + 'common' + '/ideas' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            bad_count = bad_count + check_ideas(os.path.join(root, filename))
    #bad_count = bad_count + check_focus_tree_file_name(nation_focus_files)

    #for root, dirnames, filenames in os.walk(rootDir + '/'+ 'common' + '/' + 'national_focus' + '/'):
    #    for filename in fnmatch.filter(filenames, '*.txt'):
     #       files_list.append(os.path.join(root, filename))
    #for root, dirnames, filenames in os.walk(rootDir + '/'+ 'common' + '/' + 'national_focus' + '/'):
    #   for filename in fnmatch.filter(filenames, '*.txt'):
    #       files_list.append(os.path.join(root, filename))

    #for root, dirnames, filenames in os.walk(rootDir + '/'+ 'events' + '/'):
    #    for filename in fnmatch.filter(filenames, '*.txt'):
    #        files_list.append(os.path.join(root, filename))

    #for root, dirnames, filenames in os.walk(rootDir + '/'+ 'history' + '/'):
     #   for filename in fnmatch.filter(filenames, '*.txt'):
     #       files_list.append(os.path.join(root, filename))

    #for filename in files_list:
    #    bad_count = bad_count + check_basic_style(filename)

    print("------\nChecked {0} files\nErrors detected: {1}".format(len(files_list), bad_count))
    if (bad_count == 0):
        print("File validation PASSED")
    else:
        print("File validation FAILED")

    print ('The script took {0} second!'.format(time.time() - startTime))
    
    return bad_count
    
if __name__ == "__main__":
    sys.exit(main())
