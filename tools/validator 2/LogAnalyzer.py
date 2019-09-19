import os

class Logs:
    def __init__(self, logFolder):
        self.scriptDir = os.path.dirname(logFolder)
        self.rootDir = os.path.dirname(os.path.dirname(self.scriptDir))

        self.typeToIgnore = ['lexer.cpp', 'convoys.cpp', 'session.cpp']
        self.highPriority = []
        self.mediumPriority = []
        self.lowPriority = []
        self.logTypes = {"pdx_entity": self.PdxEntity}
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
                    ignore = False
                    for logType in self.typeToIgnore:
                        if logType in line:
                            ignore = True
                    if ignore == False:
                        for logType in self.logTypes:
                            if logType in line:
                                functionToCall = self.logTypes[logType]
                                functionToCall()
                        input()

    def Map(self):
        print()

    def TechnologyTemplate(self):
        print()

    def PdxEntity(self):
        print("PDX ENTITY")

    def Effect(self):
        print()

    def EffectImplementation(self):
        print()

    def ContainerWindow(self):
        print()

    def GameState(self):
        print()

    def Graphics(self):
        print()

    def EffectBase(self):
        print()

    def Session(self):
        print()

    def GfxAirplanes(self):
        print()

    def TriggerImplementation(self):
        print()

