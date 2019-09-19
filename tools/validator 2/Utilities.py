import os, re



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
