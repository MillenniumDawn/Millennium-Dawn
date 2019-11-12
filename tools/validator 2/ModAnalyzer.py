import os, re

from pathlib import Path
from Utilities import Utility
from structs.Ideologies import Ideology
from structs.Country import Country
from structs.EquipmentVariant import EqpVariant

class Mod:

    def __init__(self, scriptDir):
        self.errors = []
        self.debugMode = False
        self.scriptDir = os.path.realpath(scriptDir)
        self.rootDir = os.path.realpath(Path(scriptDir).parents[2])

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
        self.countries, self.errors = self.GenerateCountries(self.rootDir + "/history/countries/")
        self.errors += self.getCountriesData()

        self.errors += self.validateEqpVariants()

        self.errors += self.validteOOBS()

        self.errors += self.check_event_for_logs(self.rootDir + "/events/")

        for error in self.errors:
            print(error)
        print("Total of: " + str(len(self.errors)) + " errors")


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
        if self.debugMode:
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
        if self.debugMode:
            print(ideologies)
        return ideologies

    def GetIdeas (self, dir):
        variable = []
        Utility.GetData(dir, '\s+?([\w]+)\s?=', variable, 2)

        if self.debugMode:
            print(variable)
        return variable

    def GetTechnology (self, dir):
        variable = []
        Utility.GetData(dir, '\s+?([\w]+)\s?=', variable, 1)

        if self.debugMode:
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
        if self.debugMode:
            print(variable)
        return variable

    def GetOppinionModifiers (self, dir):
        variable = []
        Utility.GetData(dir, '\s?([-_\w]+)\s?=', variable, 1)

        if self.debugMode:
            print(variable)
        return variable

    def GetScriptedEffects (self, dir):
        variable = []
        Utility.GetData(dir, '^\s?([-_\w]+)\s?=', variable, 0)

        if self.debugMode:
            print(variable)
        return variable

    def GetScriptedTriggers (self, dir):
        variable = []
        Utility.GetData(dir, '^\s?([-_\w]+)\s?=', variable, 0)

        if self.debugMode:
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

        if self.debugMode:
            print(variable)
        return variable

    def GetNationalFocus (self, dir):
        variable = []
        Utility.GetData(dir, '^[\s?]+id\s?=\s?([\w_]+)', variable, 2)

        if self.debugMode:
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
        if self.debugMode:
            print(pdxTriggers)
            print(pdxEffects)
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
        if self.debugMode:
            print(countryTriggers)
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

        if self.debugMode:
            print(stateTriggers)
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

        if self.debugMode:
            print(unkownTriggers)
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

        if self.debugMode:
            print(countryEffects)
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

        if self.debugMode:
            print(stateEffects)
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

        if self.debugMode:
            print(unkownEffects)
        return unkownEffects

    def GetFlag(self, dir, keyword):
        variable = []
        for root, dirs, files in os.walk(dir):
            for file in files:
                try:
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

                except:
                    print("Couldn't open file: " + str(file))

        Utility.RemoveDuplicates(variable)

        if self.debugMode:
            print(variable)
        return variable

    def check_event_for_logs(self, dir):
        errors = []

        for root, dirs, files in os.walk(dir):
            for file in files:
                lineNum = 0
                hasLog = 0
                optionFound = 0
                optionName = ""
                try:
                    if not os.path.isdir(dir + file):
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.readlines()
                            braces = 0
                            for line in content:
                                lineNum += 1
                                if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                                    if "option" in line and "=" in line:
                                        optionFound = 1
                                        optionLine = lineNum
                                        hasLog = 0
                                    if optionFound == 1:
                                        if "name" in line and "=" in line:
                                            hasName = re.search(r'name\s?=\s([a-zA-Z0-9-_.]+)', line, re.M | re.I)  # If it's a tag
                                            if hasName:
                                                optionName = hasName.group(1)
                                        if "{" in line:
                                            braces += line.count("{")

                                        if braces > 0 and hasLog == 0 and "log" in line:
                                            hasLog = 1
                                            optionFound = 0
                                            braces = 0
                                        if "}" in line:
                                            braces -= line.count("}")
                                        if braces == 0 and hasLog == 0:
                                            errors.append("ERROR: Event " + optionName + " doesn't have logging {0} Line number: {1}".format(
                                                dir, optionLine))
                                            optionFound = 0
                                            braces = 0
                                            hasLog = 0
                except:
                    print("Couldn't open file: " + str(file) )
        if self.debugMode:
            print(errors)
        return errors

    def GenerateCountries(self, dir):
        countries = []
        countryFiles = os.listdir(dir)
        errors = []

        for x in self.tags:
            countries.append(Country(x))
        for country in countries:
            for filename in countryFiles:
                if country.tag + " - " in filename:
                    country.countryFile = dir + filename
                    countryFiles.remove(filename)
                    #print(country.countryFile)
                    #print(len(countryFiles))


            #if country.countryFile == "":
                #print(f"{country.tag} doesn't have a history/countries file")
                #errors += str(f"{country.tag} doesn't have a history/countries file")

        return countries, errors

    def getCountriesData(self):
        errors = []
        for country in self.countries:
            if country.countryFile != "":
                with open(country.countryFile, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.readlines()
                    foundTech = 0
                    foundVariant = 0
                    openBrace = 0
                    startDate = 0

                    # input()
                    for line in content:
                        if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank
                            if "2000.1.1" in line:
                                startDate = 1
                            if "2017.1.1" in line:
                                startDate = 2
                            if "{" in line:
                                openBrace += 1


                            if foundTech == 1 and openBrace <= 1:
                                foundTech = 0
                            if foundVariant == 1 and openBrace <= 1:
                                foundVariant = 0

                            if startDate == 1:
                                if "set_technology" in line:
                                    foundTech = 1
                                if "create_equipment_variant" in line:
                                    foundVariant = 1

                                if "oob" in line and "set_naval_oob" not in line and "#oob" not in line:
                                    hasOOB = re.search(r'oob\s?=\s?\"([A-Za-z0-9_\-]+)\"', line,
                                                        re.M | re.I)  # If it's a tag
                                    if hasOOB:
                                        country.oob2000File = self.rootDir + "/history/units/" + hasOOB.group(1)  + ".txt"
                                        if country.tag not in country.oob2000File:
                                            errors.append((f"WARNING: Is {country.oob2000File} the correct OOB for {country.tag} seems a bit odd"))
                                if "set_naval_oob" in line and "#set_naval_oob" not in line:
                                    hasNavalOOB = re.search(r'set_naval_oob\s?=\s?\"([A-Za-z0-9_\-]+)\"', line,
                                                       re.M | re.I)  # If it's a tag
                                    if hasNavalOOB:
                                        country.oobNavy2000Files.append(self.rootDir + "/history/units/" + hasNavalOOB.group(1) + ".txt")
                                        for oobFileName in country.oobNavy2000Files:
                                            if country.tag not in oobFileName:
                                                errors.append((f"WARNING: Is {oobFileName} the correct OOB for {country.tag} seems a bit odd"))

                                if openBrace == 2:
                                    if foundTech == 1:
                                        country.AddTech(line, startDate)

                                if openBrace == 2 or openBrace == 3:
                                        if foundVariant == 1:
                                            country.AddVariant(line, startDate)

                            if startDate == 2:
                                if "set_technology" in line:
                                    foundTech = 1
                                if "create_equipment_variant" in line:
                                    foundVariant = 1

                                if "oob" in line and "set_naval_oob" not in line:
                                    hasOOB = re.search(r'oob\s?=\s?\"([A-Za-z0-9_\-]+)\"', line,
                                                       re.M | re.I)  # If it's a tag
                                    if hasOOB:
                                        country.oob2017File = self.rootDir + "/history/units/" + hasOOB.group(1) + ".txt"
                                        if country.tag not in country.oob2017File:
                                            errors.append((
                                                              f"WARNING: Is {country.oob2017File} the correct OOB for {country.tag} seems a bit odd"))

                                if "set_naval_oob" in line:
                                    hasNavalOOB = re.search(r'set_naval_oob\s?=\s?\"([A-Za-z0-9_\-]+)\"', line,
                                                       re.M | re.I)  # If it's a tag
                                    if hasNavalOOB:
                                        country.oobNavy2017Files.append(self.rootDir + "/history/units/" + hasNavalOOB.group(1) + ".txt")
                                        if country.tag not in country.oobNavy2017Files:
                                            for oobFileName in country.oobNavy2017Files:
                                                if country.tag not in oobFileName:
                                                    errors.append((
                                                                      f"WARNING: Is {oobFileName} the correct OOB for {country.tag} seems a bit odd"))

                                if openBrace == 2:
                                    if foundTech == 1:
                                        country.AddTech(line, startDate)

                                if openBrace == 2 or openBrace ==3:
                                    if foundVariant == 1:
                                        country.AddVariant(line, startDate)

                            if "}" in line:
                                openBrace -= 1

        return errors

    def validateEqpVariants(self):
        tempCountries = self.countries
        errors = []

        for country in self.countries:
            for variant in country.variants2000:
                startdate = 1
                error = variant.ValidateOnAdd(country, self.countries, startdate, self.debugMode)
                if error != "":
                    errors += error
            for variant in country.variants2017:
                startdate = 2
                error = variant.ValidateOnAdd(country, self.countries, startdate, self.debugMode)
                if error != "":
                    errors += error

        return errors

    def validteOOBS(self):
        errors = []
        for country in self.countries:
            oobs = []
            startdate = 0
            if country.oob2000File != "":
                oobs.append(country.oob2000File)
            for oob in country.oobNavy2000Files:
                oobs.append(oob)

            filecount = len(oobs) #counts how many 2000 oobs there are

            if country.oob2017File != "":
                oobs.append(country.oob2017File)
            for oob in country.oobNavy2017Files:
                oobs.append(oob)

            for x in range(0, (len(oobs))):
                if x < filecount:
                    startdate = 1
                else:
                    startdate = 2

                if os.path.exists(oobs[x]):
                    with open(oobs[x], 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.readlines()

                        openBrace = 0
                        braceWhenFound = 0

                        newShip = EqpVariant()
                        newEquipment = EqpVariant()

                        stockpileFound = False
                        productionFound = False
                        shipFound = False

                        # input()
                        for line in content:
                            if not line.startswith("#") or line.startswith(""):  # If the line doesn't start with a comment or blank

                                if "2000.1.1" in line:
                                    startDate = 1
                                if "2017.1.1" in line:
                                    startDate = 2
                                if "ship" in line and "#ship" not in line:
                                    shipFound = True
                                    braceWhenFound = openBrace
                                if "add_equipment_to_stockpile" in line and "#add_equipment_to_stockpile" not in line:
                                    stockpileFound = True
                                    braceWhenFound = openBrace
                                if "add_equipment_production" in line and "#add_equipment_production" not in line:
                                    productionFound = True
                                    braceWhenFound = openBrace
                                if "{" in line:
                                    openBrace += 1

                                if shipFound:
                                    if "equipment" in line:
                                        hasEquipment = re.search(r'equipment\s?=\s?{\s?([A-Za-z0-9_\-]+)\s?=', line,
                                                                 re.M | re.I)  # If it's a tag
                                        if hasEquipment:
                                            newShip.type = hasEquipment.group(1)
                                    if "version_name" in line:
                                        hasVersion = re.search(r'version_name\s?=\s?\"(.*)\"', line,
                                                               re.M | re.I)  # If it's a tag
                                        if hasVersion:
                                            newShip.versionName = hasVersion.group(1)
                                    if "creator" in line:
                                        hasCreator = re.search(r'creator\s?=\s?([A-Z]{3})', line,
                                                               re.M | re.I)  # If it's a tag
                                        if hasCreator:
                                            newShip.creator = hasCreator.group(1)
                                    if "owner" in line:
                                        hasOwner = re.search(r'owner\s?=\s?([A-Z]{3})', line,
                                                             re.M | re.I)  # If it's a tag
                                        if hasOwner:
                                            newShip.owner = hasOwner.group(1)

                                if stockpileFound:
                                    if "type" in line:
                                        hasEquipment = re.search(r'type\s?=\s?([A-Za-z0-9_\-]+)', line,
                                                                 re.M | re.I)  # If it's a tag
                                        if hasEquipment:
                                            newEquipment.type = hasEquipment.group(1)
                                    if "version_name" in line:
                                        hasVersion = re.search(r'version_name\s?=\s?\"(.*)\"', line,
                                                               re.M | re.I)  # If it's a tag
                                        if hasVersion:
                                            newEquipment.name = hasVersion.group(1)
                                    if "producer" in line:
                                        hasCreator = re.search(r'producer\s?=\s?([A-Z]{3})', line,
                                                               re.M | re.I)  # If it's a tag
                                        if hasCreator:
                                            newEquipment.creator = hasCreator.group(1)

                                if "}" in line:
                                    openBrace -= 1

                                if shipFound and openBrace <= braceWhenFound:
                                   if startdate == 1:
                                        country.ships2000.append(newShip)
                                   else:
                                       country.ships2017.append(newShip)

                                   errors += (newShip.Validate(self.countries, startdate, file.name, self.debugMode))
                                   shipFound = False
                                   newShip = EqpVariant()

                                if stockpileFound and openBrace <= braceWhenFound:
                                    if newEquipment.owner == "":
                                        newEquipment.owner = country.tag
                                    if newEquipment.creator == "":
                                        newEquipment.creator = country.tag
                                    errors += (newEquipment.Validate(self.countries, startdate, file.name, self.debugMode))
                                    stockpileFound = False
                                    newEquipment = EqpVariant()

                                if productionFound and openBrace <= braceWhenFound:


                                    productionFound = False
                                    newEquipment = EqpVariant()




                else:
                    if self.debugMode:
                        print(f"ERROR: {country.tag} has {oobs[x]} but it doesn't exist")
                    errors.append((f"ERROR: {country.tag} has {oobs[x]} but it doesn't exist"))

        return errors