#!/usr/bin/env python3
import os, sys, fnmatch, re
import time
import requests

startTime = time.time()

__version__ = 1.0

class Mod:

    def __init__(self, scriptDir):
        self.scriptDir = os.path.realpath(scriptDir)
        self.rootDir = os.path.dirname(os.path.dirname(scriptDir))

        self.tags = self.get_tags(self.rootDir + "/common/country_tags/")

    def get_tags(self, dir):
        tags = []
        for file in os.listdir(dir):
            with open(dir + file, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.readlines()
                for line in content:
                    if not line.startswith("#") or line.startswith(
                            ""):  # If the line doesn't start with a comment or blank
                        hasTag = re.match(r'^[A-Z]{3}', line, re.M | re.I)  # If it's a tag
                        if hasTag:
                            tags.append(hasTag.group())
        #print(tags)
        return tags


class Utility:

    @staticmethod
    def ReturnMatch(self, text, expr):

        match = re.match(r'{}'.format(expr), text, re.M | re.I)
        if match:
            return match.group()

    @staticmethod
    def GetData(self, dir, expr, variable, braceCheck):

        for file in os.listdir(dir):
            with open(dir + file, 'r', encoding='utf-8', errors='ignore') as file:
                brace = 0
                content = file.readlines()

                for line in content:
                    if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or is blank
                        if "{" in line or "}" in line:

                            if brace == braceCheck:
                                match = re.match(r'{}'.format(expr), line, re.M | re.I)
                                if match:
                                    variable.append(match.group())

                            if "#" in line:
                                match = re.match(r'#.*[{}]+', line, re.M | re.I)
                                if match:
                                    brace += line.count("{")
                                    brace -= line.count("}")
                            else:
                                brace += line.count("{")
                                brace -= line.count("}")





def main():

    thisMod = Mod(__file__)

    print('The script took {0} second!'.format(time.time() - startTime))








if __name__ == "__main__":
    sys.exit(main())
