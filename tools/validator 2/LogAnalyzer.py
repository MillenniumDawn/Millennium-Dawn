import os

class Logs:
    def __init__(self, logFolder):
        self.scriptDir = os.path.dirname(logFolder)
        self.rootDir = os.path.dirname(os.path.dirname(self.scriptDir))

        self.typeToIgnore = ['lexer.cpp', 'convoys.cpp', 'session.cpp', 'gameidler.cpp']
        self.highPriority = []
        self.mediumPriority = []
        self.lowPriority = []
        self.logTypes = {"map.cpp": self.Map, "technologytemplate.cpp": self.TechnologyTemplate, "pdx_entity.cpp": self.PdxEntity,
                         "effect.cpp": self.Effect, "effectimplementation.cpp": self.EffectImplementation, "containerwindow.cpp": self.ContainerWindow,
                         "gamestate.cpp": self.GameState, "graphics.cpp": self.Graphics, "effectbase.cpp": self.EffectBase,
                         "gfxairplanes.cpp": self.GfxAirplanes, "triggerimplementation.cpp": self.TriggerImplementation,
                         "texturehandler.cpp":self.TextureHandler}
        self.AnalyzeLogs()

        print("done")
        input()

    def AnalyzeLogs(self):
        files = os.listdir(self.scriptDir)
        if 'error.log' in files:
            file = os.path.join(self.scriptDir + '/error.log')
            with open(file, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.readlines()
                for x, line in enumerate(content):
                    if line.startswith('['):
                        ignore = False
                        for logType in self.typeToIgnore:
                            if logType in line:
                                ignore = True
                        if ignore == False:
                            found = False
                            for logType in self.logTypes:
                                if logType in line:
                                    for y in range (x + 1, len(content)):
                                        if not content[y].startswith('['):
                                            line = line.rstrip() + '' + content[y]
                                        else:
                                            break
                                    functionToCall = self.logTypes[logType]
                                    functionToCall(line)
                                    found = True
                                    break
                            if found == False:
                                print("Error: Couldn't catagorize this line, Please send this line to the developer: {0}".format(line))
                    #else:
                    #    print("need to append last log zzzz")
                     #   print(line)
                input()

    def Map(self, line):
        self.highPriority.append(line)

    def TechnologyTemplate(self, line):
        if 'has more than 1 XOR, this is not a big problem' in line or 'is primary mutual exclusive ( XOR ) with' in line:
            self.lowPriority.append(line)
        else:
            self.highPriority.append(line)

    def PdxEntity(self, line):
        self.lowPriority.append(line)

    def Effect(self, line):
        self.highPriority.append(line)

    def EffectImplementation(self, line):
        self.highPriority.append(line)

    def ContainerWindow(self, line):
        self.mediumPriority.append(line)

    def GameState(self, line):
        self.lowPriority.append(line)

    def Graphics(self, line):
        self.highPriority.append(line)

    def EffectBase(self, line):
        self.mediumPriority.append(line)

    def GfxAirplanes(self, line):
        self.mediumPriority.append(line)

    def TriggerImplementation(self, line):
        self.highPriority.append(line)

    def TextureHandler(self, line):
        self.highPriority.append(line)

    def CompareLogs(self, newHigh, newMediun, newLow):
        print()