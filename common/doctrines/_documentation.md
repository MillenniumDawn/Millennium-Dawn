# Doctrines

## Important concepts:

- **Folder** - the category of doctrines, e.g. _land_, _air_ or _naval_
- **Grand Doctrine** - mutually exclusive root of the doctrine folder, unlocked with XP
- **Track** - a slot for a subdoctrine and its rewards
- **Milestone** - an additional reward for completing a track
- **Subdoctrine** - can be slotted as the root of a specific track, unlocked with XP
- **Mastery** - the progress made within a track
- **Reward** - a reward for making gaining mastery within a track, belongs to a subdoctrine

## Doctrine Effects

- set_grand_doctrine
- set_sub_doctrine
- add_mastery
- add_daily_mastery
- add_mastery_bonus

## Doctrine Triggers

- has_completed_subdoctrine
- has_doctrine
- has_completed_track
- has_subdoctrine_in_track
- has_mastery
- has_mastery_level

## Doctrine Modifiers

### Doctrine Cost modifiers

- _[folder_name]_\_doctrine_cost_factor

```
# Example:
land_doctrine_cost_factor = -0.15 # 15% cost reduction to grand doctrines and subdoctrines in the land folder
```

### Mastery Gain modifiers

Note: for these mastery gain modifiers, localization is automatically mapped, meaning you do not have to define unique localization keys for each generated modifier.

- _[folder_name]_\_track_mastery_gain_factor

```
# Example:
land_track_mastery_gain_factor = 0.15 # +15% mastery gain for all tracks in the land folder
```

- _[grand_doctrine_name]_\_mastery_gain_factor

```
# Example:
new_mobile_warfare_mastery_gain_factor = 0.15 # +15% mastery gain for all tracks which have Mobile Warfare as the grand doctrine
```

- _[subdoctrine_name]_\_mastery_gain_factor

```
# Example:
guerilla_war_mastery_gain_factor = 0.15 # +15% mastery gain for all tracks which have Guerilla Warfare as the subdoctrine
```

- _[track_name]_\_track_mastery_gain_factor

```
# Example:
infantry_track_mastery_gain_factor = 0.15 # +15% mastery gain for infantry tracks
```
