#!/usr/bin/env python3
import os, sys, fnmatch, re
import time
import requests
from dataclasses import dataclass

startTime = time.time()

__version__ = 1.0

class Mod:

    def __init__(self, scriptDir):
        self.scriptDir = os.path.realpath(scriptDir)
        self.rootDir = os.path.dirname(os.path.dirname(scriptDir))

        self.tags = self.GetTags(self.rootDir + "/common/country_tags/")
        self.ideologies = self.GetIdeologies(self.rootDir + "/common/ideologies/")
        self.ideas = self.GetIdeas(self.rootDir + "/common/ideas/")
        self.technology = self.GetTechnology(self.rootDir + "/common/technologies/")
        self.techSharingGroups = self.GetTechSharingGroups(self.rootDir + "/common/technology_sharing/")
        self.oppinionModifiers = self.GetOppinionModifiers(self.rootDir + "/common/opinion_modifiers/")
        self.scriptedEffects = self.GetScriptedEffects(self.rootDir + "/common/scripted_effects/")
        self.scriptedTriggers = self.GetScriptedTriggers(self.rootDir + "/common/scripted_triggers/")
        self.traits = self.GetTraits(self.rootDir + "/common/unit_leader/")
        self.nationalFocus = self.GetNationalFocus(self.rootDir + "/common/national_focus/")

    def GetTags(self, dir):
        tags = []
        for file in os.listdir(dir):
            with open(dir + file, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.readlines()
                for line in content:
                    if not line.startswith("#") or line.startswith(
                            ""):  # If the line doesn't start with a comment or blank
                        hasTag = re.match(r'^([A-Z]{3})', line, re.M | re.I)  # If it's a tag
                        if hasTag:
                            tags.append(hasTag.group(1))
        print(tags)
        return tags

    def GetIdeologies(self, dir):
        ideologies = []
        #ideologies.append(Ideology("test", ["1","2","3"]))

        for file in os.listdir(dir):
            with open(dir + file, 'r', encoding='utf-8', errors='ignore') as file:
                brace = 0
                content = file.readlines()
                isSubideology = False;

                for line in content:
                    if not line.startswith("#") or line.startswith(
                            ""):  # If the line doesn't start with a comment or is blank
                        if "{" in line or "}" in line:

                            if brace == 1:
                                match = re.match(r'^\s?([\w-]+)\s?=', line, re.M | re.I)
                                if match:
                                    ideologies.append(Ideology(match.group(1), []))

                            if isSubideology:
                                match2 = re.search(r'\s?([\w-]+)\s?=', line, re.M | re.I)
                                if match2:
                                    ideologies[len(ideologies)-1].Subideology.append(match2.group(1))

                            if "#" in line:
                                match = re.match(r'#.*[{}]+', line, re.M | re.I)
                                if not match:
                                    brace += line.count("{")
                                    brace -= line.count("}")
                            else:
                                brace += line.count("{")
                                brace -= line.count("}")

                            if brace == 3 and "types" in line:
                                isSubideology = True
                            if brace == 2:
                                isSubideology = False

        print(ideologies)
        return ideologies

    def GetIdeas (self, dir):
        variable = []
        Utility.GetData(dir, '\s+?([\w]+)\s?=', variable, 2)

        print(variable)
        return variable

    def GetTechnology (self, dir):
        variable = []
        Utility.GetData(dir, '\s+?([\w]+)\s?=', variable, 1)

        print(variable)
        return variable

    def GetTechSharingGroups(self, dir):
        variable = []

        for file in os.listdir(dir):
            with open(dir + file, 'r', encoding='utf-8', errors='ignore') as file:
                brace = 0
                content = file.readlines()

                for line in content:
                    if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or is blank


                        if brace == 1:
                            match = re.match(r'{}'.format('\s?id\s?=\s?([\w_]+)'), line, re.M | re.I)
                            if match:
                                variable.append(match.group(1))

                        if "{" in line or "}" in line:
                            if "#" in line:
                                match2 = re.match(r"\s?#.*[{}]+", line, re.M | re.I)
                                if not match2:
                                    brace += line.count("{")
                                    brace -= line.count("}")
                            else:
                                brace += line.count("{")
                                brace -= line.count("}")
        print(variable)
        return variable

    def GetOppinionModifiers (self, dir):
        variable = []
        Utility.GetData(dir, '\s?([-_\w]+)\s?=', variable, 1)

        print(variable)
        return variable

    def GetScriptedEffects (self, dir):
        variable = []
        Utility.GetData(dir, '^\s?([-_\w]+)\s?=', variable, 0)

        print(variable)
        return variable

    def GetScriptedTriggers (self, dir):
        variable = []
        Utility.GetData(dir, '^\s?([-_\w]+)\s?=', variable, 0)

        print(variable)
        return variable

    def GetTraits (self, dir):
        variable = []
        Utility.GetData(dir, '^\s?([-_\w]+)\s?=', variable, 1)

        toRemove = []
        for num, trait in enumerate(variable):
            if trait.isdigit():
                toRemove.append(trait)

        for num in toRemove:
            variable.remove(num)

        print(variable)
        return variable

    def GetNationalFocus (self, dir):
        variable = []
        Utility.GetData(dir, '\s?\bid\b\s?=\s?([\w_]+)', variable, 0)

        print(variable)
        return variable





class Utility:

    @staticmethod
    def ReturnMatch(self, text, expr):

        match = re.match(r'{}'.format(expr), text, re.M | re.I)
        if match:
            return match.group()

    @staticmethod
    def GetData(dir, expr, variable, braceCheck):

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
                                    variable.append(match.group(1))

                            if "#" in line:
                                match2 = re.match(r"\s?#.*[{}]+", line, re.M | re.I)
                                if not match2:
                                    brace += line.count("{")
                                    brace -= line.count("}")
                            else:
                                brace += line.count("{")
                                brace -= line.count("}")
        #print(variable)
        return variable

    @staticmethod
    def GetData2(self, dir, expr, variable, braceCheck, keyword):

        for file in os.listdir(dir):
            with open(dir + file, 'r', encoding='utf-8', errors='ignore') as file:
                brace = 0
                content = file.readlines()

                for line in content:
                    if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or is blank
                        if "{" in line or "}" in line:

                            if brace == braceCheck:
                                if keyword in line:
                                    match = re.match(r'{}'.format(expr), line, re.M | re.I)
                                    if match:
                                        variable.append(match.group())

                            if "#" in line:
                                match = re.match(r'#.*[{}]+', line, re.M | re.I)
                                if not match:
                                    brace += line.count("{")
                                    brace -= line.count("}")
                            else:
                                brace += line.count("{")
                                brace -= line.count("}")

@dataclass
class Ideology:
    Ideology: str
    Subideology: str



def main():

    thisMod = Mod(__file__)

    print('The script took {0} second!'.format(time.time() - startTime))








if __name__ == "__main__":
    sys.exit(main())
