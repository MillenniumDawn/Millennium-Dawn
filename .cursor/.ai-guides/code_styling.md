# Millennium Dawn Code Styling Guide

## Focus Trees

### Best Practices
- Use `relative_position_id` for focus alignment and tree positioning
- Implement logging in completion rewards: `log = "[GetDateText]: [Root.GetName]: Focus TAG_your_focus"`
- Avoid empty `mutually_exclusive` and `available` blocks
- Omit default values: `cancel_if_invalid = yes`, `continue_if_invalid = no`, `available_if_capitulated = no`
- Always include `ai_will_do` with historical game and game options checks
- Maintain consistent spacing (1 line between elements)
- Create balanced focus trees without clear military/economy/political branches
- Add search filters for focuses
- Remove unused/commented code
- Utilize scripted effects and tooltips
- Use variables instead of magic numbers
- Implement starting ideas that weaken nations, resolvable through focus trees/decisions
- Limit permanent effects to 5, use timed ideas for additional effects
- Balance focus trees for flavor, not overpowering nations

### Example Focus Tree Structure
```plaintext
focus_tree = {
    id = greece_focus

    country = {
        factor = 0
        modifier = {
            tag = GRE
            add = 100
        }
    }

    shared_focus = USoE001
    shared_focus = POTEF001

    continuous_focus_position = { x = 2350 y = 1200 }
}

focus = {
    id = SER_free_market_capitalism
    icon = blr_market_economy

    x = 5
    y = 3
    relative_position_id = SER_free_elections

    cost = 5
    prerequisite = { focus = SER_western_approach }
    search_filters = { FOCUS_FILTER_POLITICAL }

    available = {
        western_liberals_are_in_power = yes
    }

    completion_reward = {
        log = "[GetDateText]: [Root.GetName]: Focus SER_free_market_capitalism"
        add_ideas = SER_free_market_idea
    }

    ai_will_do = {
        base = 1
    }
}
```

## Decisions

### Best Practices
- Use `fire_only_once` only when necessary
- Include proper logging in effects
- Structure decisions with clear visibility and availability conditions
- Implement proper AI behavior

### Example Decision Structure
```plaintext
URA_world_opr = {
    allowed = { original_tag = URA }
    icon = GFX_decision_sovfed_button

    cost = 50
    days_remove = 400

    visible = {
        country_exists = OPR
        OPR = {
            OR = {
                has_autonomy_state = autonomy_republic_rf
                has_autonomy_state = autonomy_kray_rf
                has_autonomy_state = autonomy_oblast_rf
                has_autonomy_state = autonomy_okrug_rf
            }
        }
    }

    complete_effect = {
        log = "[GetDateText]: [Root.GetName]: Decision URA_world_opr"
        OPR = { country_event = { id = subject_rus.121 days = 1 } }
    }

    ai_will_do = {
        factor = 10
    }
}
```

## Events

### Best Practices
- Use `is_triggered_only` for triggered events
- Include proper logging
- Use `major = yes` sparingly for news events
- Structure events with clear options and effects

### Example Event Structure
```plaintext
country_event = {
    id = france_md.504
    title = france_md.504.t
    desc = france_md.504.d
    picture = GFX_france_mcdonalds_bombing
    is_triggered_only = yes

    option = {
        name = france_md.504.a
        log = "[GetDateText]: [This.GetName]: france_md.504.a executed"
        set_party_index_to_ruling_party = yes
        set_temp_variable = { party_popularity_increase = -0.01 }
        set_temp_variable = { temp_outlook_increase = -0.01 }
        add_relative_party_popularity = yes

        ai_chance = {
            base = 1
        }
    }
}
```

## Ideas

### Best Practices
- Include `allowed_civil_war` for civil war tags
- Use proper logging in `on_add`
- Structure modifiers clearly
- Implement balanced effects
- **Performance**: Remove unnecessary `allowed = { always = no }` statements as they add drag to performance - since `always = no` is the default behavior, these lines provide no functional benefit while consuming processing resources

### Example Idea Structure
```plaintext
BRA_idea_higher_minimun_wage_1 = {
    name = BRA_idea_higher_minimun_wage
    allowed_civil_war = { always = yes }
    on_add = { log = "[GetDateText]: [THIS.GetName]: add idea BRA_idea_higher_minimun_wage_1" }

    picture = gold

    modifier = {
        political_power_factor = 0.1
        stability_factor = 0.05
        consumer_goods_factor = 0.075
        population_tax_income_multiplier_modifier = 0.05
    }
}
```

## Code Formatting Rules

### Indentation
- Increase tabulation by 1 when entering a new scope `{`
- Decrease tabulation by 1 when leaving a scope `}`
- Use tabs, not spaces
- Maintain consistent indentation

### Brackets
- Place closing brackets on the same line as the starting word
- Avoid excessive whitespace
- Keep simple checks on one line when appropriate

### Subideology Localization Format
```plaintext
TAG.conservatism: "£PARTY_ICON (ABBRV) - NAME OF PARTY"
TAG.conservatism_icon: "£PARTY_ICON"
TAG.conservatism_desc: "(Dominant Ideology of the Party) - NAME OF PARTY (NAME OF LANGUAGES IN ALL NATIVE LANGUAGES FOR THE COUNTRY, ABBRV)\n\n(Description)"
```

Example:
```plaintext
MOR.conservatism: "£MOR_NRI (RNI) - National Rally of Independents"
MOR.conservatism_icon: "£MOR_NRI"
MOR.conservatism_desc: "(Classic Liberalism) - National Rally of Independents (Arabic: Altajamue Alwataniu Lil'ahrar, French: Rassemblement National des Indépendants, Standard Moroccan Tamazight: Agraw Anamur y Insimann, RNI)\n\nNominally a social-democratic party, the party often cooperates with other parties with liberal orientation and is heavily described as pro-business and liberal. Formed in 1978 by then-Prime Minister Ahmed Osman the party has consistently remained a major player in Moroccan politics. Furthermore, the party is a national observer of the Liberal International and is affiliated with the Africa Liberal Network and the European People's Party."
```