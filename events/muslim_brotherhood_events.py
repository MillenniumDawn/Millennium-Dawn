# This file will handle relations more efficiently
from common import opinion_modifiers

def update_muslim_brotherhood_relations(countries):
    for country in countries:
        # Assume `base_opinion` is a predefined function
        country.opinion_modifiers.append(opinion_modifiers.muslim_brotherhood)

def on_game_start():
    countries = get_all_countries()
    update_muslim_brotherhood_relations(countries)