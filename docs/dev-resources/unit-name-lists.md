---
layout: default
title: "Unit Name Lists Guidelines"
description: "Guidelines for creating unit name lists for Millennium Dawn"
---

# Unit Name Lists Guidelines

This is a requirement for all new content for the developers. Name lists define what new trained units, ships and airwings will be called. Name lists are fairly easy to complete and only take a small amount of effort for us to complete. It adds good flavour while also being a relatively minor addition.

When creating name lists, the name of the namelist should be in English while the names of the units should be in the native language.

## Division Requirements

File Path: common/units/names_divisions

This is the location for storing division name lists. The lists for a single country are stored in the country's own file. Name lists that are shared between countries can be in a common file. Once name lists have been created, they also need to be assigned to units. The below picture should provide all the necessary information. Explanation for the different elements is described below the picture.
![unit_namelist](uploads/c38eaab4cff489578c4f7949665ed4c6/unit_namelist.png)

The top left section is something you will find in the division name list file (in this case FIN_names_divisions.txt). This is a single entry, and a single file can have multiple entries. This is how an entry is built:
1) The token for the name list. This must be unique for each name list and it something the game uses to recognise the name list
2) The name of the name list. This is what the player sees in the drop-down menu when designing a template. This describes the overall "theme" of the name list. This should be in English so the player knows what the name list is intended for.
3) for_countries defines which countries the name list is available for. Multiple tags can be defined here. For an example, check the Syrian name lists.
4) can_use works as a trigger similar to "visible" in decisions. This defines when the name list will be visible in the drop-down menu. This only needs to be defined in special cases. **Do not have an empty can_use = { } in the list as this has an extra performance impact!**. If it is not needed, remove the line.
5) division_types defines which type of units the AI will assign this name list to. So if the unit is predominantly motorised infantry, it would use this name list. This has no impact on the player. Only use front-line type units (militia, types of infantry, armour, air cavalry, paratroopers and marines).
6) link_numbering_with can be used to link two name lists together. This will make the two lists share numbering. In the example, Jäger Brigades and Armoured Jäger Brigades are linked. This prevents duplicates between two unis, so for example you can't have two units with the "Lapin Jääkäriprikaati" name. Another advantage is using continuous numbering. For Japan for example, Army Divisions and Armoured Divisions are linked. This means you can never have 15. Army Division and 15. Armoured Division at the same time, but the 15. number will be assigned to whichever unit type is trained first.
7) fallback_name defines the base name for the unit. This is the name a unit will use if no unique names are left. Here, %d means the number of the unit. So if the country deploys the 16th unit using this name list, it will be called "16. Jääkäriprikaati". You can also use %s to get the number as a Roman numeral (XVI for example).
8) "ordered" defines unique names for this name list that differ from the the fallback_name. These aren't necessary if the fallback_name works for all units.

Once a name list is created, it needs to be tied to the starting templates and assigned to units. In order to do this, you must find the country's unit files in history/units/. The name list is assigned to a template by adding "division_names_group = namelist_token" inside the template definition. Then within the unit definition itself, division_name = { } needs to be added. This  tells the game which name to pick from the unit name list that is linked to the unit's template. The name_order value doesn't need to correspond to a unique name inside the "ordered" list in the name list. In this case the game will just use the fallback_name to name the unit. So using "name_order = 20" for example would simply name the unit to "20. Jääkäriprikaati"

When creating the name lists, several points should be followed:
- Starting units must have their historical real life names. A good place to start creating the name lists is by creating appropriate name lists for the starting units first.
- Some countries won't have historical real life names for their units (especially minors). In this scenario, research needs to be done to see whether or not this data is available.
- Each front line unit type must be included in at least one division_types entry. This ensures that all all units the AI produces will have valid names.
- Name lists should follow real life naming patterns for military formations. So no "Light Infantry Brigades" just because there is a unit type called light infantry. Especially for countries that don't have very varied starting units, this will require a bit of research. So the local naming tradition should be taken into account. For example for English speaking countries, "Mechanised Infantry Brigade" works for both mechanised and armoured infantry. But in a French speaking country, this would only refer to armoured infantry (as mechanised infantry would be called "Motorised Infantry Brigade").
- Whether the units should be called brigades or divisions depends on the size of the starting units.
- For good examples of unit name lists look at Finland, Syria or Japan.

## Ship Requirements

File Path: common/units/names_ships

## Plane Requirements

File Path: common/units/names

If there are questions or you are not sure what to do, please contact Kalkalash
