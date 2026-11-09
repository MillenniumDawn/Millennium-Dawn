"""Shared HOI4 script execution model for STALKER source tests."""

from collections import Counter

from script_model import ScopedScriptModel


class StalkerModel(ScopedScriptModel):
    """Execute STALKER source with scope, temp and stubbed-effect support."""

    def __init__(self, tags=("---", "USA", "YEM", "PER", "TAL", "AFG", "CHI")):
        self.effects, self.triggers = {}, {}
        self.countries, self.globals, self.temps = {}, {}, {}
        self.scope_stack, self.events = [], []
        self.global_flags, self.external = {}, Counter()
        self.stubs = set()
        self.goto(2005, 1)
        for ident, tag in enumerate(tags):
            self.country(ident, tag=tag)
            self.countries[ident].update(states=[], exists=ident != 0)
