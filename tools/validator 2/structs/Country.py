from dataclasses import dataclass, field
from structs.EquipmentVariant import EqpVariant

import re

@dataclass
class Country:
    tag: str = field(default_factory=str)
    countryFile: str = field(default_factory=str)

    capital2000: str = field(default_factory=str)
    has2000Start: bool = field(default_factory=bool)
    oob2000File: str = field(default_factory=str)
    oobNavy2000Files: list = field(default_factory=list)
    convoys2000: int = field(default_factory=int)
    ideas2000: list = field(default_factory=list)
    opinion_modifier2000: list = field(default_factory=list)
    technology2000: list = field(default_factory=list)
    variants2000: list = field(default_factory=list)
    ships2000: list = field(default_factory=list)

    capital2017: str = field(default_factory=str)
    has2017Start: bool = field(default_factory=bool)
    oob2017File: str = field(default_factory=str)
    oobNavy2017Files: list = field(default_factory=list)
    convoys2017: int = field(default_factory=int)
    ideas2017: list = field(default_factory=list)
    opinion_modifier2017: list = field(default_factory=list)
    technology2017: list = field(default_factory=list)
    variants2017: list = field(default_factory=list)
    ships2017: list = field(default_factory=list)

    def AddTech(self, line, startDate):
        hasTech = re.search(r'[ \t]+([A-Za-z0-9_\-]+)\s?=\s?1', line, re.M | re.I)  # If it's a tag
        if hasTech:
            if startDate == 1:
                self.technology2000.append(hasTech.group(1))
            elif startDate == 2:
                self.technology2017.append(hasTech.group(1))
                #print(self.tag + " " + self.technology2017[-1])
                # input()



    def AddVariant(self, line, startDate):

            if "name" in line:
                variantName = re.search(r'name\s?=\s?\"(.*)\"', line, re.M | re.I)  # If it's a tag
                if variantName:

                    if startDate == 1:
                        self.variants2000.append(EqpVariant(variantName.group(1)))
                        self.variants2000[-1].creator = self.tag
                        #print(self.variants2000[-1] + " 2000")
                    elif startDate == 2:
                        self.variants2017.append(EqpVariant(variantName.group(1)))
                        self.variants2017[-1].owner = self.tag
                        #print(self.variants2017[-1] + " 2017")
                        #for variant in self.variants2017:
                            #print("var - " + variant.name)
                        #print(self.variants2017[-1].type)




            elif "type" in line:
                variantType = re.search(r'type\s?=\s?([A-Za-z0-9_\-]+)', line, re.M | re.I)  # If it's a tag
                if variantType:
                    if startDate == 1:
                        self.variants2000[-1].type = variantType.group(1)
                        # print(self.variants2000[-1] + " 2000")
                    elif startDate == 2:
                        self.variants2017[-1].type = variantType.group(1)

            #elif "=" in line and "obsolete" not in line:
                #check if that upgrade exists





