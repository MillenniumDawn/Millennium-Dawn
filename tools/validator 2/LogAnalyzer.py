import os

class logs:
    def __init__(self, logFolder):
        self.scriptDir = os.path.realpath(logFolder)
        self.typeToIgnore = ['lexer.cpp', 'convoys.cpp', 'session.cpp']
        self.highPriority = []
        self.mediumPriority = []
        self.lowPriority = []

    def AnalyzeLogs(self):
        files = os.listdir(self.scriptDir)
        if 'error.log' in files:
            file = self.scriptDir + 'error.log'
            with open(file, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.readlines()
                for line in content:
                    if self.typeToIgnore in line:
                        print()

    def Map(self):
        print()

    def TechnologyTemplate(self):
        print()

    def PdxEntity(self):
        print()

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

