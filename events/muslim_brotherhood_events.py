def setup_muslim_brotherhood_relations():
    # Define a single function to manage all opinion modifiers for the Muslim Brotherhood
    opinion_modifiers = {
        'country1': 15,
        'country2': -10,
        'country3': 5,
    }
    for country, modifier in opinion_modifiers.items():
        set_opinion_modifier('Muslim Brotherhood', country, modifier)

def set_opinion_modifier(group_name, country, modifier):
    # This function sets a specific opinion modifier for a country
    print(f"Setting opinion modifier for {country} towards {group_name} to {modifier}")