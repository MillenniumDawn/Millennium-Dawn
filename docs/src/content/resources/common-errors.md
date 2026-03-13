---
title: Common Hearts of Iron IV Errors
description: List of common Hearts of Iron IV errors and how to fix them.
---

This guide is intended for developers to find and fix any errors they may see in the error log.

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
