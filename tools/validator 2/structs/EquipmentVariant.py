from dataclasses import dataclass, field

@dataclass
class EqpVariant:
    versionName: str = field(default_factory=str)
    type: str = field(default_factory=str)
    upgrades: list = field(default_factory=list)
    obsolete: str = field(default_factory=bool)
    creator: str = field(default_factory=str)
    owner: str = field(default_factory=str)

    def ValidateOnAdd(self, thisCountry, countries, startdate, debugMode):
        errors = []

        if startdate ==1:
            for otherCountry in countries:
                for variant in otherCountry.variants2000:
                    if thisCountry.tag != otherCountry.tag:
                        if self.versionName == variant.versionName:
                            if debugMode:
                                print((f"ERROR Duplicate Variant. Is this intentional? {thisCountry.tag}:  {self.versionName} and {otherCountry.tag}: {variant.versionName}"))
                            errors.append((f"ERROR Duplicate Variant. Is this intentional? {thisCountry.tag}:  {self.versionName} and {otherCountry.tag}: {variant.versionName}"))

            if (self.type not in thisCountry.technology2000):
                if debugMode:
                    print((f"ERROR {thisCountry.tag} has variant {self.versionName} - {self.type} but doesn't have the tech for it"))
                errors.append((f"ERROR {thisCountry.tag} has variant {self.versionName} - {self.type} but doesn't have the tech for it"))
        else:
            for otherCountry in countries:
                for variant in otherCountry.variants2017:
                    if thisCountry.tag != otherCountry.tag:
                        if self.versionName == variant.versionName:
                            if debugMode:
                                print(f"ERROR Duplicate Variant. Is this intentional? {thisCountry.tag}:  {self.versionName} and {otherCountry.tag}: {variant.versionName}")
                            errors.append(f"ERROR Duplicate Variant. Is this intentional? {thisCountry.tag}:  {self.versionName} and {otherCountry.tag}: {variant.versionName}")

            if (self.type not in thisCountry.technology2017 and self.type not in thisCountry.technology2000):
                if debugMode:
                    print((f"ERROR {thisCountry.tag} has variant {self.versionName} - {self.type} but doesn't have the tech for it"))
                errors.append((f"ERROR {thisCountry.tag} has variant {self.versionName} - {self.type} but doesn't have the tech for it"))

        return errors


    def Validate(self, countries, startdate, filename, debugMode):
        errors = []
        tag = ""
        variantFound = False
        if self.creator == "":
            tag = self.owner
        else:
            tag = self.creator

            for country in countries:
                if country.tag == tag:
                    if self.versionName != "":
                        for variant in country.variants2000:
                            if self.versionName == variant.versionName:
                                variantFound = True
                        if startdate != 1 and not variantFound:
                            for variant in country.variants2017:
                                if self.versionName == variant.versionName:
                                    variantFound = True

                        if not variantFound:
                            if startdate ==1:
                                if debugMode:
                                    print((f"ERROR: {filename} {self.owner} has {self.type} {self.versionName} from"f" {tag} but {tag} doesn't have this  variant in the 2000 start date"))
                                errors.append((f"ERROR: {filename} {self.owner} has {self.type} {self.versionName} from"f" {tag} but {tag} doesn't have this  variant in the 2000 start date"))
                            else:
                                if debugMode:
                                    print(( f"ERROR: {filename} {self.owner} has {self.type} {self.versionName} from {tag} but{tag} doesn't have this  variant in the 2000 or 2017 start date"))
                                errors.append((f"ERROR: {filename} {self.owner} has {self.type} {self.versionName} from {tag} but{tag} doesn't have this  variant in the 2000 or 2017 start date"))

                    if startdate ==1:
                        if self.type not in country.technology2000:
                            if debugMode:
                                print((
                                          f"ERROR {filename} {self.owner} has {self.type} {self.versionName} from {tag} but {tag} doesn't have tech {self.type} in the 2000 start date"))
                            errors.append((f"ERROR {filename} {self.owner} has {self.type} {self.versionName} from {tag} but {tag} doesn't have tech {self.type} in the 2000 start date"))

                    else:
                        if self.type == "Strike_fi22ghter22":
                            print("ROFL")
                            input()
                        if self.type not in country.technology2017 and self.type not in country.technology2000:
                            if debugMode:
                                print((f"ERROR {filename} {self.owner} has {self.type} {self.versionName} from {tag} but {tag} doesn't have tech {self.type} in the 2000 or 2017 start date"))
                            errors.append((f"ERROR {filename} {self.owner} has {self.type} {self.versionName} from {tag} but {tag} doesn't have tech {self.type} in the 2000 or 2017 start date"))
                    #break
        return errors



