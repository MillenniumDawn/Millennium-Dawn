#!/usr/bin/env python3
import os, sys, fnmatch, re
import time

startTime = time.time()

__version__ = 1.0

def main():
    #print("test")
    #input()
    bad_count = 0
    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))
    global totalErrors
    totalErrors = 0
    for root, dirnames, filenames in os.walk(rootDir + '/' + 'common/units/names_ships/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            newContent = ""
            with open(os.path.join(rootDir + '/' + 'common/units/names_ships/', filename), 'w', encoding='utf-8',
                      errors='ignore') as file:
                file.write(newContent)



    print('The script took {0} second!'.format(time.time() - startTime) + " therea are a total of: " + str(totalErrors) + " errors.")

    return bad_count


if __name__ == "__main__":
    sys.exit(main())