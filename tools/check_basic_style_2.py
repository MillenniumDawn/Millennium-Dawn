#!/usr/bin/env python3
import os, sys, fnmatch, re
import time

#startTime = time.time()

__version__ = 1.0

def check_basic_style(filepath):
    bad_count_file = 0

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        lineNum = 0
        openBraces = [0, 0]
        for line in content:
            lineNum +=1
            hasComment = re.search(r'#.*?[{}]+?', line, re.M | re.I) #If comment at the start or before bracket
            hasOpenBrace = re.search(r'{', line, re.M | re.I)
            hasCloseBrace = re.search(r'}', line, re.M | re.I)
            if not hasComment: #Don't waste cycles comment if comment at the start or before open bracket
                if hasOpenBrace:
                    openBraces[0] += len(re.findall('{', line))
                    openBraces[1]=lineNum

                if hasCloseBrace:
                    openBraces[0] += -len(re.findall('}', line))

                if openBraces[0] <= -1:
                    print("ERROR: A possible missing curly brace {{ in file {} {{line {}}}".format(filepath, lineNum))
                    openBraces[0] = 0
                    bad_count_file +=1
                #input("Press Enter to continue...")
        else:
            if openBraces[0] < 0:
                print("ERROR: A possible missing curly brace }} in file {} {{line {}}}".format(filepath, lineNum))
                bad_count_file += 1
            elif openBraces[0] > 0:
                print("ERROR: A possible missing curly brace {{ in file {} has no matching closing bracket".format(filepath, lineNum))
                bad_count_file += 1
        file.close()

    return bad_count_file


def main():
    print("Validating Basic Style - Secondary Check")

    files_list = []
    bad_count = 0
  
    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))

    for root, dirnames, filenames in os.walk(rootDir + '/'+ 'common' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            files_list.append(os.path.join(root, filename))

    for root, dirnames, filenames in os.walk(rootDir + '/'+ 'events' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            files_list.append(os.path.join(root, filename))

    for root, dirnames, filenames in os.walk(rootDir + '/'+ 'history' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            files_list.append(os.path.join(root, filename))

    for filename in files_list:
        bad_count = bad_count + check_basic_style(filename)

    print("------\nChecked {0} files\nErrors detected: {1}".format(len(files_list), bad_count))
    if (bad_count == 0):
        print("File validation PASSED")
    else:
        print("File validation FAILED")

    #print ('The script took {0} second!'.format(time.time() - startTime))
    
    return bad_count
    
if __name__ == "__main__":
    sys.exit(main())
