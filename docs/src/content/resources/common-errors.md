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
