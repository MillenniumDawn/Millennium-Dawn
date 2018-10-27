#!/usr/bin/env python3
import os, sys, fnmatch, re

__version__ = 1.0


def check_basic_style(filepath):
    bad_count_file = 0

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
        lineNum = 0
        openBraces = [0, 0]
        for line in content:
            lineNum += 1
            hasComment = re.search(r'#.*?[{}]+?', line, re.M | re.I)  # If comment at the start or before bracket
            hasOpenBrace = re.search(r'{', line, re.M | re.I)
            hasCloseBrace = re.search(r'}', line, re.M | re.I)
            if not hasComment:  # Don't waste cycles comment if comment at the start or before open bracket
                # print ("comment at line: ", lineNum)
                if hasOpenBrace:
                    openBraces[0] += len(re.findall('{', line))
                    openBraces[1] = lineNum
                # print ("OPEN brace on line:", lineNum, "open brace = ", openbraces)

                if hasCloseBrace:
                    openBraces[0] += -len(re.findall('}', line))
                # print ("CLOSE brace on line:", lineNum, "open brace = ", openbraces)

                if openBraces[0] <= -1:
                    print(filepath);
                    print("ERROR: Closing bracket on line:", lineNum, "with no matching opening bracket")
                    openBraces[0] = 0
                    bad_count_file += 1
                # input("Press Enter to continue...")
        else:
            if openBraces[0] < 0:
                print(filepath);
                print("Closing bracket on line:", lineNum, "with no matching opening bracket")
                bad_count_file += 1
            elif openBraces[0] > 0:
                print(filepath);
                print("Open bracket on line:", openBraces[1], "has no matching closing bracket")
    # input("Press Enter to continue...")

    return bad_count_file


def main():
    print("Validating Basic Style")

    files_list = []
    leaderID = 0

    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))

    for root, dirnames, filenames in os.walk(rootDir + '/' + 'history/countries/test/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            files_list.append(os.path.join(root, filename))
            print(filename)

    for filename in files_list:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.readlines()
            for line in content:
                hasSkill = re.search(r'([ \t]+)skill[ \t]+?=[ \t]+?([0-9]+)', line, re.M | re.I)
                if hasSkill:
                    leaderID+=1
                    print (leaderID)


if __name__ == "__main__":
    sys.exit(main())
