import os

class Logs:
    def __init__(self, logFolder):
        self.scriptDir = os.path.dirname(logFolder)
        self.rootDir = os.path.dirname(os.path.dirname(self.scriptDir))

        self.typeToIgnore = ['lexer.cpp', 'convoys.cpp', 'session.cpp']
        self.highPriority = []
        self.mediumPriority = []
        self.lowPriority = []
        self.logTypes = {"map.cpp": self.Map, "technologytemplate.cpp": self.TechnologyTemplate, "pdx_entity.cpp": self.PdxEntity,
                         "effect.cpp": self.Effect, "effectimplementation.cpp": self.EffectImplementation, "containerwindow.cpp": self.ContainerWindow,
                         "gamestate.cpp": self.GameState, "graphics.cpp": self.Graphics, "effectbase.cpp": self.EffectBase,
                         "session.cpp": self.Session, "gfxairplanes.cpp": self.GfxAirplanes,
                         "triggerimplementation.cpp": self.TriggerImplementation }
        self.AnalyzeLogs()

        print("done")
        input()

    def AnalyzeLogs(self):
        files = os.listdir(self.scriptDir)
        if 'error.log' in files:
            file = os.path.join(self.scriptDir + '/error.log')
            with open(file, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.readlines()
                for line in content:
                    if line.startswith('['):
                        ignore = False
                        for logType in self.typeToIgnore:
                            if logType in line:
                                ignore = True
                        if ignore == False:
                            found = False
                            for logType in self.logTypes:
                                if logType in line:
                                    functionToCall = self.logTypes[logType]
                                    functionToCall(line)
                                    found = True
                                    break
                            if found == False:
                                print("Error - Please send this line to the developer: {0}".format(line))
                    else:
                        print("need to append last log zzzz")
                input()

    def Map(self, line):
        print("MAP")

    def TechnologyTemplate(self, line):
        print("TECH TEMPLATE")

    def PdxEntity(self, line):
        print("PDX ENTITY")

    def Effect(self, line):
        print("EFFECT")

    def EffectImplementation(self, line):
        print("EFFECT IMPLEMENTATION")

    def ContainerWindow(self, line):
        print("CONTAINER WINDOW")

    def GameState(self, line):
        print("GAME STATE")

    def Graphics(self, line):
        print("GRAPHICS")

    def EffectBase(self, line):
        print("EFFECT BASE")

    def Session(self, line):
        print("SESSION")

    def GfxAirplanes(self, line):
        print("GFX Airplanes")

    def TriggerImplementation(self, line):
        print("TRIGGER IMPLEMENTATION")

