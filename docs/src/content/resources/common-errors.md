---
title: Common Hearts of Iron IV Errors
description: List of common Hearts of Iron IV errors and how to fix them.
---

This guide is intended for developers to find and fix common errors and crashes they may encounter during development.

---

## Crash: Special Project with ai_will_do base = 0

**Symptom:** The game crashes when a special project becomes available and the AI gains a breakthrough point for it.

**Cause:** Setting `ai_will_do = { base = 0 }` on a special project causes a crash. Unlike focuses and decisions where `base = 0` is valid, the special projects system does not handle a zero base value correctly.

**Note:** Using `factor = 0` inside a `modifier` block within `ai_will_do` is fine — the crash only occurs when the root-level `base` itself is 0.

**Fix:** Use a very small positive value instead:

```hoi4
ai_will_do = {
	base = 0.001
	# use modifier blocks to zero it out conditionally
	modifier = {
		factor = 0
		# condition here
	}
}
```

---

## Save Corruption: give_military_access to Self

**Symptom:** The save file becomes corrupted and the game crashes when loading. This can also cause an OOS (out of sync) in multiplayer.

**Cause:** If a script path allows a country to call `give_military_access` on itself (e.g., through an event, decision, or focus where the target is not properly guarded), the game enters a broken state. The save file is written with invalid military access data and cannot be loaded again.

**How it happens:** This usually occurs when a generic or scoped effect fires `give_military_access` using a variable or `FROM`/`ROOT` target without checking that the target is not the same country. For example:

```hoi4
# WRONG — if ROOT and FROM are the same country, this corrupts the save
give_military_access = FROM
```

**Fix:** Always guard `give_military_access` with a check that the target is not the current country:

```hoi4
if = {
	limit = {
		NOT = { tag = FROM }
	}
	give_military_access = FROM
}
```

**Recovery:** If a save is already corrupted, there is no reliable way to fix it. The save must be reverted to an earlier autosave from before the self-access was granted.

---

## Crash on Load: Infinite Event Loops

**Symptom:** The game freezes or crashes when loading a save, or shortly after unpausing. The error log may show the same event ID firing thousands of times.

**Cause:** An event fires itself (directly or through a chain) without a condition that eventually stops the loop. When the game loads and processes queued events, it enters an infinite loop and runs out of memory or hangs.

**Common patterns that cause this:**

1. **Event fires itself directly:**

```hoi4
# WRONG — option fires the same event, infinite loop
country_event = { id = my_event.1 }
option = {
	name = my_event.1.a
	country_event = { id = my_event.1 }
}
```

2. **Two events fire each other:**

```hoi4
# Event A fires Event B, Event B fires Event A — infinite ping-pong
```

3. **on_action or MTTH event with no exit condition:**
   An `on_daily` or `on_weekly` event that triggers another event that triggers the first, with no flag or condition to break the cycle.

**Fix:** Make sure every event chain has a clear termination condition. Use country flags to prevent re-entry:

```hoi4
option = {
	name = my_event.1.a
	set_country_flag = my_event_handled
	# effects here
}

# In the trigger that fires the event:
trigger = {
	NOT = { has_country_flag = my_event_handled }
}
```

**Recovery:** If a save is stuck in an infinite loop, you may be able to fix it by opening the save file in a text editor, searching for the queued event entries, and deleting them. Revert to an earlier autosave if that is not feasible.

---

## Crash on Load: Focus Icons with Mipmaps

**Symptom:** The game crashes when loading, often with no clear error message or with a graphics-related crash in the log. The crash happens consistently on the same save or when a specific country's focus tree is loaded.

**Cause:** Focus icon `.dds` files were saved with mipmaps enabled. HOI4 expects focus icons (and most small UI icons) to be single-layer DDS files without mipmaps. When the engine tries to load a mipmapped icon at the wrong resolution, it crashes.

**How to check:** Open the suspect `.dds` file in a DDS viewer (e.g., the Windows Texture Viewer, GIMP with the DDS plugin, or paint.net). If the file has more than one mip level, that is the problem.

**Fix:** Re-export the DDS file without mipmaps:

- **paint.net:** Save as DDS, uncheck "Generate Mip Maps"
- **GIMP (with DDS plugin):** Export as DDS, set "Mipmaps" to "None"
- **nvtt_export / texconv:** Use the `-m 1` flag to generate only a single mip level
- **tools/assets/batchdds-2.py:** The repo's built-in converter already exports without mipmaps by default

Focus icons should be saved as **DXT5 (BC3)** format, **without mipmaps**, at **70x70** pixels. See the [Art Standards](/dev-resources/art-standards/) for the full list of formats by asset type.

---

## Failed to Generate a Name for a Character

This error is commonly caused by not having a list of names defined in `common/names/00_names.txt`.

```plaintext
[17:57:08][2005.03.10.01][character_manager.cpp:257]: Failed to generate a name for a character of origins Florida and for country Florida
```

Example Fix:

Add a line like this or similar into the name lists file in `common/names/00_names.txt`.
We suggest giving at least 10 to 15 names otherwise you are going to end up with a bunch of characters of the same name.

```hoi4
FLA = {
	male = {
		names = {
			Noah
		}
	}
	female = {
		names = {
			Emma
		}
	}
	surnames = {
		Smith
	}
	callsigns = { }
}

```
