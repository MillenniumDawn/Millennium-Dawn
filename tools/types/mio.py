class Trait:
    def __init__(self, token: str, name: str, applies_to: list[str], bonuses: dict[str, float], parent: 'Trait' = None, mutually_exclusive: list['Trait'] = None):
        self.token = token
        self.name = name
        self.applies_to = applies_to
        self.bonuses = bonuses
        self.parent = parent
        self.mutually_exclusive = mutually_exclusive if mutually_exclusive is not None else []

class MIO:
    def __init__(self, name: str, countries: list[str], equipment_types: list[str], research_categories: list[str]):
        self.name = name
        self.countries = countries
        self.equipment_types = equipment_types
        self.research_categories = research_categories
        self.traits = []