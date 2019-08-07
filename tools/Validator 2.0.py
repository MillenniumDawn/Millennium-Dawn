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
        self.allTriggers, self.allEffects = self.FindPdxSyntax(self.rootDir + "/Modding resources/List of triggers and effects 1_6_1.txt")
        self.countryTriggers = self.GetCountryTriggers(self.allTriggers)
        self.stateTriggers = self.GetStateTriggers(self.allTriggers)
        self.unkownTriggers = self.GetUnkownTriggers(self.allTriggers)
        self.countryEffects = self.GetCountryEffects(self.allEffects)
        self.stateEffects = self.GetStateEffects(self.allEffects)
        self.unkownEffects = self.GetUnkownEffects(self.allEffects)
        self.globalFlags = self.GetFlag(self.rootDir + "/common/", "set_global_flag")
        self.countryFlags = self.GetFlag(self.rootDir + "/common/", "set_country_flag")

    def GetTags(self, dir):
        tags = []
        for root, dirs, files in os.walk(dir):
            for file in files:
                try:
                    if not os.path.isdir(dir + file):
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.readlines()
                            for line in content:
                                if not line.startswith("#") or line.startswith(
                                        ""):  # If the line doesn't start with a comment or blank
                                    hasTag = re.match(r'^([A-Z]{3})', line, re.M | re.I)  # If it's a tag
                                    if hasTag:
                                        tags.append(hasTag.group(1))
                except:
                    print("Couldn't open file: " + str(file))

        print(tags)
        return tags

    def GetIdeologies(self, dir):
        ideologies = []
        #ideologies.append(Ideology("test", ["1","2","3"]))

        for root, dirs, files in os.walk(dir):
            for file in files:
                try:
                    if not os.path.isdir(dir + file):
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as file:
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
                                            if not Utility.ReturnMatch(r"\s?#.*[{}]+", line):
                                                brace += line.count("{")
                                                brace -= line.count("}")
                                        else:
                                            brace += line.count("{")
                                            brace -= line.count("}")

                                        if brace == 3 and "types" in line:
                                            isSubideology = True
                                        if brace == 2:
                                            isSubideology = False
                except:
                    print("Couldn't open file: " + str(file))

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
                                if not Utility.ReturnMatch(r"\s?#.*[{}]+", line):
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
        Utility.GetData(dir, '^[\s?]+id\s?=\s?([\w_]+)', variable, 2)

        print(variable)
        return variable

    def FindPdxSyntax(self, dir):
        with open(dir, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.readlines()
            typeOfCode = 0  # 1 = trigger, 2 = effects
            pdxTriggers = []
            pdxEffects = []
            # 0 0 0 = trigger name
            # 0 1 x = scopes
            # 0 2 x = targets
            # 0 3 x = examples
            triggerNum = 0
            EffectrNum = 0

            for line in content:
                if "==" in line:  # check for triggers
                    if "TRIGGER DOCUMENTATION" in line:
                        typeOfCode = 1
                        # print(typeOfCode)
                    elif "EFFECT DOCUMENTATION" in line:
                        typeOfCode = 2

                if typeOfCode == 1:
                    if "Supported scopes:" in line:
                        if "state" in line:
                            pdxTriggers[triggerNum - 1].append(["state"])
                            # print("scope: " + pdxTriggers[triggerNum-1][1][0])
                        elif "country" in line:
                            pdxTriggers[triggerNum - 1].append(["country"])
                            # print("scope: " + pdxTriggers[triggerNum-1][1][0])
                        elif "Supported scopes: ???" == line:
                            pdxTriggers[triggerNum - 1].append(["N/A"])
                            # print("scope: " + pdxTriggers[triggerNum-1][1][0])
                        elif "Supported scopes:\n" == line:
                            pdxTriggers[triggerNum - 1].append(["N/A"])
                            # print("scope: " + pdxTriggers[triggerNum-1][1][0])

                    elif "Supported targets:" in line:
                        if "none" in line:
                            pdxTriggers[triggerNum - 1].append(["none"])
                            # print("scope: " + pdxTriggers[triggerNum-1][2][0])
                        elif "Supported targets:\n" == line:
                            pdxTriggers[triggerNum - 1].append(["N/A"])
                            # print("scope: " + pdxTriggers[triggerNum-1][2][0])

                    elif "" != line:
                        isTrigger = re.search(r'^([A-Z_?-?]+) -', line, re.M | re.I)  # If it's a tag
                        if isTrigger:
                            isTrigger = re.search(r'^([A-Z_?-?]+) -', line, re.M | re.I)  # If it's a tag
                            pdxTriggers.append([[isTrigger.group(1)]])
                            triggerNum += 1

                if typeOfCode == 2:
                    if "Supported scopes:" in line:
                        if "state" in line:
                            pdxEffects[EffectrNum - 1].append(["state"])
                            # print("scope: " + pdxTriggers[triggerNum-1][1][0])
                        elif "country" in line:
                            pdxEffects[EffectrNum - 1].append(["country"])
                            # print("scope: " + pdxTriggers[triggerNum-1][1][0])
                        elif "Supported scopes: ???" == line:
                            pdxEffects[EffectrNum - 1].append(["N/A"])
                            # print("scope: " + pdxTriggers[triggerNum-1][1][0])
                        elif "Supported scopes:\n" == line:
                            pdxEffects[EffectrNum - 1].append(["N/A"])
                            # print("scope: " + pdxTriggers[triggerNum-1][1][0])
                    elif "Supported targets:" in line:
                        if "none" in line:
                            pdxEffects[EffectrNum - 1].append(["none"])
                            # print("scope: " + pdxTriggers[triggerNum-1][2][0])
                        elif "country" in line:
                            pdxEffects[EffectrNum - 1].append(["country"])
                            # print("scope: " + pdxTriggers[triggerNum-1][2][0])
                        elif "Supported targets: none\n" == line:
                            pdxEffects[EffectrNum - 1].append(["N/A"])
                            # print("scope: " + pdxTriggers[triggerNum-1][2][0])
                            # print(content)
                            # input()

                    elif "" != line:
                        isEffect = re.search(r'^([A-Z_?-?]+) -', line, re.M | re.I)  # If it's a tag
                        if isEffect:
                            isEffect = re.search(r'^([A-Z_?-?]+) -', line, re.M | re.I)  # If it's a tag
                            pdxEffects.append([[isEffect.group(1)]])
                            EffectrNum += 1

        return pdxTriggers, pdxEffects

    def GetCountryTriggers(self, allTriggers):
        countryTriggers = []
        for x in allTriggers:
            # print("x = " + str(len(x)))
            for y in x:
                for z in y:
                    if z == "country":
                        countryTriggers.append(x)
        # for x in countryTriggers:
        #    # print("x = " + str(len(x)))
        #   for y in x:
        #       for z in y:
        #           print("x = " + str(x))
        #           print("y = " + str(y))
        #           print("z = " + str(z))

        return countryTriggers

    def GetStateTriggers(self, allTriggers):
        stateTriggers = []
        for x in allTriggers:
            # print("x = " + str(len(x)))
            for y in x:
                for z in y:
                    if z == "state":
                        stateTriggers.append(x)
        # for x in stateTriggers:
        #   # print("x = " + str(len(x)))
        #    for y in x:
        #        for z in y:
        #            print("x = " + str(x))
        #            print("y = " + str(y))
        #            print("z = " + str(z))

        return stateTriggers

    def GetUnkownTriggers(self, allTriggers):
        # print ("test")
        unkownTriggers = []
        for x in allTriggers:
            # print("x = " + str(x))
            for y in x:
                for z in y:
                    # print(z)
                    if z == "N/A":
                        unkownTriggers.append(x)
        # for x in unkownTriggers:
        # print("x = " + str(len(x)))
        #    for y in x:
        #        for z in y:
        #           print("x = " + str(x))
        #            print("y = " + str(y))
        #            print("z = " + str(z))

        return unkownTriggers

    def GetCountryEffects(self, allEffects):
        countryEffects = []
        for x in allEffects:
            # print("x = " + str(len(x)))
            for y in x:
                for z in y:
                    if z == "country":
                        countryEffects.append(x)
        # for x in countryEffects:
        #    # print("x = " + str(len(x)))
        #    for y in x:
        #       for z in y:
        #            print("x = " + str(x))
        #           print("y = " + str(y))
        #           print("z = " + str(z))

        return countryEffects

    def GetStateEffects(self, allEffects):
        stateEffects = []
        for x in allEffects:
            # print("x = " + str(len(x)))
            for y in x:
                for z in y:
                    if z == "state":
                        stateEffects.append(x)
        # for x in stateEffects:
        # print("x = " + str(len(x)))
        # for y in x:
        #   for z in y:
        #        print("x = " + str(x))
        #       print("y = " + str(y))
        #        print("z = " + str(z))

        return stateEffects

    def GetUnkownEffects(self, allEffects):
        unkownEffects = []
        for x in allEffects:
            # print("x = " + str(len(x)))
            for y in x:
                for z in y:
                    if z == "N/A":
                        unkownEffects.append(x)
        # for x in unkownEffects:
        # print("x = " + str(len(x)))
        # for y in x:
        #   for z in y:
        #        print("x = " + str(x))
        #       print("y = " + str(y))
        #        print("z = " + str(z))

        return unkownEffects

    def GetFlag(self, dir, keyword):
        variable = []
        for root, dirs, files in os.walk(dir):
            for file in files:
                #try:
                if not os.path.isdir(dir + file):
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.readlines()
                        inScope = False
                        for line in content:
                            temp = ""
                            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or is blank

                                if inScope and "flag" in line:
                                    if not Utility.ReturnMatch('\s?#.*[{}]+', line):
                                        temp = Utility.ReturnMatchGroup(line, 1, '.*\bflag\b\s?=\s?([-_\w\@]+)')

                                if keyword in line:
                                    inScope = False
                                    if "#" in line:
                                        if not Utility.ReturnMatch('\s?#.*[{}]+', line):
                                            temp = Utility.ReturnMatchGroup(line, 2, '.*' + keyword + '\s=\s?(\{\s?flag\s?=\s?)?([[-_\w\@]+)')
                                    else:
                                        temp = Utility.ReturnMatchGroup(line, 2, '.*' + keyword + '\s=\s?(\{\s?flag\s?=\s?)?([[-_\w\@]+)')
                                    if not temp:
                                        inScope = True

                                if temp:
                                    variable.append(temp)
                                    #print("line: " + line)
                                    #print("temp: " + variable[-1])
                                    #input()







                        #else:



                #except:
                    #print("Couldn't open file: " + str(file))

        Utility.RemoveDuplicates(variable)
        print(variable)
        return variable

class Utility:

    @staticmethod
    def ReturnMatch(self, text, expr):

        match = re.match(r'{}'.format(expr), text, re.M | re.I)
        if match:
            return match.group()

    def ReturnMatch(text, expr):

        match = re.match(r'{}'.format(expr), text, re.M | re.I)
        if match:
            return match.group()

    def ReturnMatchGroup(self, text, num, expr):

        match = re.match(r'{}'.format(expr), text, re.M | re.I)
        if match:
            return match.group(num)
    def ReturnMatchGroup(text, num, expr):

        match = re.match(r'{}'.format(expr), text, re.M | re.I)
        if match:
            return match.group(num)

    @staticmethod
    def GetData(dir, expr, variable, braceCheck):

        for root, dirs, files in os.walk(dir):
            for file in files:
                try:
                    if not os.path.isdir(dir + file):
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as file:
                            brace = 0
                            content = file.readlines()

                            for line in content:
                                if not line.startswith("#") or line.startswith(
                                        ""):  # If the line doesn't start with a comment or is blank

                                    if brace == braceCheck:
                                        match = re.match(r'{}'.format(expr), line, re.M | re.I)

                                        if match:
                                            variable.append(match.group(1))

                                    if "{" in line or "}" in line:
                                        if "#" in line:
                                            if not Utility.ReturnMatch('\s?#.*[{}]+', line):
                                                brace += line.count("{")
                                                brace -= line.count("}")

                                        else:
                                            brace += line.count("{")
                                            brace -= line.count("}")

                except:
                    print("Couldn't open file: " + str(file) )

        #print(variable)
        return variable

    @staticmethod
    def GetData2(self, dir, expr, variable, braceCheck, keyword):

        for root, dirs, files in os.walk(dir):
            for file in files:
                try:
                    if not os.path.isdir(dir + file):
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as file:
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
                except:
                    print("Couldn't open file: " + str(file) )

    @staticmethod
    def RemoveDuplicates(duplicate):
        final_list = []
        for num in duplicate:
            if num not in final_list:
                final_list.append(num)
        return final_list

@dataclass
class Ideology:
    Ideology: str
    Subideology: str



def main():

    thisMod = Mod(__file__)

    print('The script took {0} second!'.format(time.time() - startTime))








if __name__ == "__main__":
    sys.exit(main())
