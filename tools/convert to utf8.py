#!/usr/bin/env python3
import os, sys, fnmatch, re
import time

startTime = time.time()

__version__ = 1.0

import os;
import sys;

def main():
    bad_count = 0
    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))
    global totalErrors
    totalErrors = 0
    for root, dirnames, filenames in os.walk(rootDir + '/' + 'history' + '/units' + '/'):
        for filename in fnmatch.filter(filenames, '*.txt'):
            with open(os.path.join(root, filename), 'r', encoding='utf-8', errors='ignore') as file:
                content = file.readlines()
            with open(os.path.join(root, filename), 'w', encoding='utf-8-bom', errors='ignore') as file:
                file.write(content)

    print('The script took {0} second!'.format(time.time() - startTime) + " therea are a total of: " + str(
        totalErrors) + " errors.")

    return bad_count


if __name__ == "__main__":
    sys.exit(main())