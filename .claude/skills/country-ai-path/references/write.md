# Write templates

Every artefact of a #3162 country pass, verbatim. Copy from here — **do not open another country's
focus tree to learn a shape**. Belarus, Brazil, Bulgaria and Comoros are naming references only.

Substitute `DEN` / `Denmark` / the path names. Tabs for indentation.

## 1. Game rule — `common/game_rules/00_game_rules.txt`

```
DEN_ai_behavior = {
	name = "DEN_AI_BEHAVIOR"
	group = "RULE_GROUP_AI_BEHAVIOR"
	option = {
		name = HISTORICAL
		text = "RULE_OPTION_DEN_HISTORICAL"
		desc = "RULE_OPTION_DEN_HISTORICAL_DESC"
	}
	option = {
		name = EUROPEAN_UNION
		text = "RULE_OPTION_DEN_EUROPEAN_UNION"
		desc = "RULE_OPTION_DEN_EUROPEAN_UNION_DESC"
	}
	option = {
		name = RANDOM_PATH
		text = "RULE_OPTION_MD_RANDOM_PATH"
		desc = "RULE_OPTION_MD_RANDOM_PATH_DESC"
	}
	default = {
		name = NO_PATH
		text = "RULE_OPTION_MD_NO_PATH"
		desc = "RULE_OPTION_MD_NO_PATH_DESC"
	}
}
```

`NO_PATH` is the `default = { }` block and stays last — a fresh game leaves the AI unscripted unless
the player picks a path. `HISTORICAL` is a plain `option` and comes first, with one `option` per
alt-history path between it and `RANDOM_PATH`. No `DEFAULT`. Option names are unprefixed
(`EUROPEAN_UNION`, not `DEN_EUROPEAN_UNION`) and never contain "random". Don't reorder the file —
the alphabetical pass is a separate cross-cutting item.

## 2. Localisation — `localisation/english/MD_game_rules_l_english.yml`

The historical option's displayed text is literally `"Historical"`. Its `_desc` carries the
country-specific history. Never an evocative title, never `"Default"`, `"Historic"` or
`"Historical AI"` — those are pre-standard spellings still in the file.

```
 #Denmark
 DEN_AI_BEHAVIOR: "@DEN Denmark"
 RULE_OPTION_DEN_HISTORICAL: "Historical"
 RULE_OPTION_DEN_HISTORICAL_DESC: "..."
 RULE_OPTION_DEN_EUROPEAN_UNION: "Into the Union"
 RULE_OPTION_DEN_EUROPEAN_UNION_DESC: "..."
```

Header key `@TAG <short country name>` — `@EST Estonia`, not `@EST Republic of Estonia`. Some
countries carry it in `localisation/english/replace/replaced_from_game_rules_l_english.yml` instead;
check both before adding a duplicate. Some existing keys are suffixed `_MD` (`CZE_AI_BEHAVIOR_MD`) —
match whatever the rule's `name =` points at.

Every `_desc` is **exactly two sentences**, present tense about the country, no hard dates, `§8…§!`
on party and movement names. First sentence: what the country does. Second: what that means for the
world or its neighbours. Reference blocks: `TUR` and `BHR` in the same file.

`RANDOM_PATH` / `NO_PATH` reuse the shared keys that already exist near the top of the file —
`RULE_OPTION_MD_RANDOM_PATH`, `RULE_OPTION_MD_NO_PATH` and their `_DESC`s. Never write per-country
copies.

## 3. Flag wiring — `common/on_actions/999_game_rules_on_actions.txt`

```
				if = {
					limit = {
						has_game_rule = {
							rule = DEN_ai_behavior
							option = RANDOM_PATH
						}
					}
					random_list = {
						30 = { set_global_flag = DEN_HISTORICAL_FOCUS_PATH }
						15 = { set_global_flag = DEN_EUROPEAN_UNION_FOCUS_PATH }
						15 = { set_global_flag = DEN_EUROSCEPTIC_FOCUS_PATH }
						10 = { set_global_flag = DEN_NATIONALIST_FOCUS_PATH }
					}
				}
				if = {
					limit = {
						has_game_rule = {
							rule = DEN_ai_behavior
							option = HISTORICAL
						}
					}
					set_global_flag = DEN_HISTORICAL_FOCUS_PATH
				}
```

One `if` per named option. `RANDOM_PATH` draws from a `random_list` that **includes the historical
bucket** and excludes `NO_PATH`; no bucket may be empty. `NO_PATH` gets no branch at all — it sets
nothing. Flags are global (`set_global_flag`), never country flags.

Optional AI sentiment grant, if the country has one — `if`/`else_if`, no bookkeeping flag:

```
				if = {
					limit = {
						is_ai = yes
						has_global_flag = DEN_SOCIALIST_FOCUS_PATH
					}
					add_timed_idea = { idea = DEN_ai_communist_sentiment days = 1095 }
				}
				else_if = {
					limit = {
						is_ai = yes
						OR = {
							has_global_flag = DEN_MONARCHIST_FOCUS_PATH
							has_global_flag = DEN_NATIONALIST_FOCUS_PATH
						}
					}
					add_timed_idea = { idea = DEN_ai_nationalist_sentiment days = 1095 }
				}
```

Everything downstream gates on `has_global_flag`, **never** `has_game_rule` — including events and
strategy plans, or a `RANDOM_PATH` roll enables the flags but not the plan. Known direct readers to
convert when they touch your country: `HOL_strategy_plans.txt`, `events/Solomon_Islands.txt`,
`events/Sao_Tome_e_Principe.txt`, `events/comoros.txt`, `events/05_japan.txt`, `events/Italy.txt`,
`history/countries/GER - Germany.txt`, `common/scripted_effects/00_yearly_effects.txt`. The report's
Wiring section lists any remaining reader for your tag.

## 4. Scripted triggers — `common/scripted_triggers/99_DEN_scripted_triggers.txt`

Every ownership group gets an **owner** trigger and a **not** trigger. AI-internal, so no loc key and
no `custom_trigger_tooltip`.

The **historical** group is special and must use this owner trigger — the flag alone is not enough,
because under `NO_PATH` with historical AI on no flag is set and the historical spine would be
zeroed along with everything else:

```
DEN_ai_historical_path = {
	OR = {
		is_historical_focus_on = yes
		has_global_flag = DEN_HISTORICAL_FOCUS_PATH
	}
}

DEN_ai_not_historical_path = {
	OR = {
		has_global_flag = DEN_EUROPEAN_UNION_FOCUS_PATH
		has_global_flag = DEN_EUROSCEPTIC_FOCUS_PATH
		has_global_flag = DEN_SOCIALIST_FOCUS_PATH
		has_global_flag = DEN_NATIONALIST_FOCUS_PATH
	}
}
```

An **alt path** group owns its flag directly, and its not trigger carries the historical killswitch:

```
DEN_ai_not_socialist_path = {
	NOT = { has_global_flag = DEN_SOCIALIST_FOCUS_PATH }
	OR = {
		is_historical_focus_on = yes
		DEN_ai_rival_of_socialist_path = yes
	}
}
```

**Alias** — only when several flags own one spine. Substitute it for the flag on both lines
(`NOT = { DEN_ai_western_path = yes }` in the not trigger):

```
DEN_ai_western_path = {
	OR = {
		has_global_flag = DEN_HISTORICAL_FOCUS_PATH
		has_global_flag = DEN_EUROPEAN_UNION_FOCUS_PATH
	}
}
```

**Rival** — the paths that are not this one. Only worth defining when a not trigger would otherwise
repeat a long flag list, or when several groups share the same rival set:

```
DEN_ai_rival_of_socialist_path = {
	OR = {
		DEN_ai_western_path = yes
		has_global_flag = DEN_EUROSCEPTIC_FOCUS_PATH
		has_global_flag = DEN_NATIONALIST_FOCUS_PATH
	}
}
```

Triggers may call each other, so the set stays small. Keep the depth shallow — three levels is
plenty.

**Precondition.** The collapsed shape is behaviour-identical to the old three-modifier form only
while at most one `TAG_*_FOCUS_PATH` flag is ever set and each not trigger excludes its own group's
flags. The report's Wiring section checks both; read it before writing the triggers.

## 5. Focus weights — `common/national_focus/05_denmark.txt`

The only shape — one boost, one killswitch. Historical group:

```
		ai_will_do = {
			base = 1
			modifier = { factor = 25 DEN_ai_historical_path = yes }
			modifier = { factor = 0 DEN_ai_not_historical_path = yes }
		}
```

Alt path group (owner is the flag, or an alias where a spine is shared):

```
		ai_will_do = {
			base = 1
			modifier = { factor = 25 has_global_flag = DEN_SOCIALIST_FOCUS_PATH }
			modifier = { factor = 0 DEN_ai_not_socialist_path = yes }
		}
```

Path modifiers are always **multiplicative** (`factor`), never `add` — an `add` loses to any
multiplicative historical modifier, which is the default state. Situational `add` nudges unrelated
to paths are fine and stay.

The two path modifiers go **last in the block**, after every other modifier. Order matters:
modifiers apply in sequence, so an `add` after a `factor = 0` resurrects a focus the killswitch was
meant to kill. Everything else in the block (bankruptcy, `can_staff`, `ai_is_threatened`, crisis
weighting) keeps its place and form — never fold a guard into a path trigger, or
`validate_focus_tree.py` stops recognising it.

Don't write these by hand. Author the mapping and run:

```bash
python tools/standardization/apply_ai_path_weights.py --tag DEN --map <file or ->
```

Mapping format — one `group` line per ownership group, an optional `boost` default, then one line
per focus. `owner=` names a scripted trigger, `owner_flag=` a global flag; a trailing number
overrides the default boost; `-` un-owns a focus (strips its path modifiers, keeps everything else):

```
group historical owner=DEN_ai_historical_path not=DEN_ai_not_historical_path
group socialist owner_flag=DEN_SOCIALIST_FOCUS_PATH not=DEN_ai_not_socialist_path
boost 25

DEN_join_the_euro      historical
DEN_red_bloc           socialist 150
DEN_army_reform        -
```

`--dry-run` lists every modifier the run would remove without writing. The tool refuses unknown or
duplicated focus ids, shared focus files, and any rewrite that would not be idempotent.

Leave the economy, army, airforce and equipment trunk path-neutral — only re-own focuses that
actually belong to a path.

## 6. AI-only popularity ramp — decisions

Needed when the chosen path's party cannot reach power on its own. Category in
`common/decisions/categories/99_DEN_decision_categories.txt`:

```
DEN_ai_path_category = {
	allowed = {
		is_ai = yes
		original_tag = DEN
	}

	icon = GFX_decisions_category_political
	priority = 100

	visible = {
		OR = {
			has_global_flag = DEN_MONARCHIST_FOCUS_PATH
			has_global_flag = DEN_NATIONALIST_FOCUS_PATH
		}
	}
}
```

The icon must be a **category** sprite (52x40, `GFX_decisions_category_*`), not a decision one.

A ramp pair per path, in `common/decisions/<Country>.txt`:

```
	DEN_rally_the_monarchists = {

		icon = generic_decision

		cost = 25

		days_re_enable = 30

		visible = { has_global_flag = DEN_MONARCHIST_FOCUS_PATH }

		available = {
			has_civil_war = no
			check_variable = { party_pop_array^23 < 0.55 }
		}

		complete_effect = {
			log = "[GetDateText]: [Root.GetName]: Decision DEN_rally_the_monarchists"
			set_temp_variable = { party_index = 23 }
			set_temp_variable = { party_popularity_increase = 0.04 }
			set_temp_variable = { temp_outlook_increase = 0.04 }
			change_relative_party_popularity = yes
		}

		ai_will_do = { base = 100 }
	}

	DEN_monarchists_take_the_country = {

		icon = generic_decision

		cost = 150

		days_re_enable = 180

		visible = { has_global_flag = DEN_MONARCHIST_FOCUS_PATH }

		available = {
			has_civil_war = no
			nationalist_monarchists_are_in_power = no
			check_variable = { party_pop_array^23 > 0.5 }
		}

		complete_effect = {
			log = "[GetDateText]: [Root.GetName]: Decision DEN_monarchists_take_the_country"
			set_temp_variable = { rul_party_temp = 23 }
			change_ruling_party_effect = yes
			hidden_effect = { update_party_name = yes }
		}

		ai_will_do = { base = 100 }
	}
```

The category is `is_ai = yes`, so **no localisation keys at all** — not for the category, not for a
decision name or desc — and bare `check_variable` in `available` with no
`custom_trigger_tooltip`. `validate_decisions.py` reports added keys as
`ai-only-decision-localisation`.

Read `change_relative_party_popularity` before picking numbers: passing `temp_outlook_increase`
skips the sibling-redistribution loop, so it is required when the target group starts at zero and
wrong when the target sits inside a group next to the incumbent.

## 7. AI strategy — war weighting

`declare_war` is target-keyed (`id = TAG`) and weights only **opening** a war. There is no
`dont_declare_war` token and no targetless form. A `declare_war` block gated on
`has_war_with = TARGET` is a no-op. The 306 `TAG_cancel_war_TARGET` blocks across
ITA/LIC/TUR/JAP/GER/HOL/ENG/SWE/CHI/BUL/CUB/IND/CAN/VEN/COL/ETH/GUY/KOR are that bug — never copy
one, never add one.

**Surrender brake, per target** (`common/ai_strategy/ALG.txt` is the model):

```
DEN_cancel_war_neighbours = {
	allowed = { original_tag = DEN }
	enable = {
		has_war = yes
		surrender_progress > 0.15
	}
	abort_when_not_enabled = yes

	ai_strategy = { type = declare_war id = "SWE" value = -4000 }
	ai_strategy = { type = declare_war id = "GER" value = -4000 }
}
```

**Pre-war readiness gate, per target.** Enable on `has_wargoal_against = X` +
`NOT = { has_war_with = X }` + a strength or size check, then `declare_war id = X` negative to hold
and positive to release. `MD_war_declaration_ai.txt`, `BOS_avoid_unready_war_with_cro` /
`BOS_prepare_war_with_cro` are the references. Cache anything containing `any_of_scopes` behind a
country flag and have `enable` read only the flag.

**Losing-war brake, targetless.** `avoid_starting_wars` gated on `has_war = yes` +
`enemies_strength_ratio`; `SOV_avoid_starting_wars`, `BLR_avoid_starting_wars` and `RAJ.txt:378` are
the references. `enemies_strength_ratio` rises as your enemies get stronger (MD's peace-deal
triggers read `> 1.7` as losing, `> 2.0` as massively outgunned), while
`strength_ratio = { tag = X ratio < 1 }` means you are weaker than X. `avoid_starting_wars` is
additive with `conquer`, not a standalone peacefulness dial — read the surrounding `conquer` values
before picking a sign or magnitude. A per-tag `avoid_starting_wars` stricter than the mod-wide
`MD_avoid_new_wars_when_outmatched` (`enemies_strength_ratio > 0.75`) is a strict subset and can
never fire.

**Never** add an `on_daily_<TAG>` pass that caches booleans into country flags for `enable` or
`ai_will_do` to read. Both are already evaluated lazily; a daily cache costs more and lags real
state by a day. Write the condition inline.
