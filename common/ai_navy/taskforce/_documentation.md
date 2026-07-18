# Taskforce composition

## Introduction

Script the ship composition for a specific taskforce and the missions it can perform. A taskforce may list more than one applicable mission; the goal system assigns it to whichever active objective fits best. Use only MD ship types (see `common/units/MD_naval_units.txt`) — vanilla hull types such as `light_cruiser`, `heavy_cruiser`, and the generic `submarine` do not exist in MD and will silently fail.

## Scripting

```
generic_taskforce_1 = {
	allowed = {
		original_tag = ENG
	}
	ai_will_do = {
		# AI weight modifier for this template
		# If <= 0, the AI will not use this template
		#
		# SCOPE = COUNTRY
		factor = 1
	}
	mission = { naval_patrol convoy_escort } # A list of applicable missions this taskforce can perform
	min_composition = { # The minimum composition before the goal system can form this taskforce
		frigate = {
			amount = 1
		}
	}

	optimal_composition = { # The target composition this taskforce will grow toward
		carrier = {
			amount = 1
		}
		cruiser = {
			amount = 2
		}
		heavy_frigate = {
			amount = 1
		}
		destroyer = {
			amount = 2
		}
		frigate = {
			amount = 3
		}
		attack_submarine = {
			amount = 2
		}
	}
}
```
