# Refactor Checklist

For a rename, migration, or subsystem rewrite. Run after automated review and before
calling the PR ready.

## Renames

Search the whole repo for the old name, not only the changed files. Other subsystems,
on_actions, and country overrides may reference it. Cover every kind of reference:

- Flags, variables, event ids (`old_namespace.`), and decision ids in `common/` and
  `events/`.
- Scripted loc names and opinion modifiers in `common/` and `localisation/`.
- GUI window names in `interface/` and `common/scripted_guis/`.
- `GFX_` sprite names in `interface/` and `gfx/`.

## Array indices

For every `foo^bar` read, find where `bar` is set, confirm it is set before the call,
and confirm it holds the kind of index the reader expects. Slot and type indices:
`scripting-edge-cases.md`.

## Globals to an array

- [ ] Every old global is updated in scripted effects, triggers, and scripted loc.
- [ ] Loc strings using `[?global.old_name]` are updated. They fail silently to 0.

## Changed preconditions

When an effect's requirements change, check every caller:

- A variable or temp variable it now needs is set first, in the right scope.
- An array it assumes is initialized before the first call.
- Callers passing a sentinel such as `project = -1` do not enter the slot branch.

## Events and decisions

- [ ] `add_namespace` matches every event id in the file.
- [ ] Each option's `log` matches its own name suffix.
- [ ] Every title, description, and option key has a loc entry.
- [ ] Every decision id has a loc entry, and its category exists.
- [ ] `days_remove` and `days_mission_timeout` reference a variable that exists at
      activation.
- [ ] `highlight_states_trigger` uses `THIS` or `ROOT` correctly for state scope.

## GUI and GFX

- [ ] Every scripted GUI `window_name` has a matching `containerWindowType`.
- [ ] Every button named in `effects` matches a `buttonType` or `iconType`.
- [ ] Every sprite referenced in `.gui` is defined in a `.gfx`, and its `texturefile`
      exists.

## Scope safety

- [ ] `CONTROLLER` is used only in state scope.
- [ ] `var:X = { ... }` is guarded when X may be unset.
- [ ] Divisions guard the denominator.
- [ ] No non-trivial decision `visible` block walks `every_country` or `any_country`.

## Removing a country tag

- [ ] `common/country_tags/00_countries.txt`: the tag definition.
- [ ] `common/countries/TAG - Name.txt` and `history/countries/TAG - Name.txt`.
- [ ] `common/countries/colors.txt`: the color entry.
- [ ] `history/states/*.txt`: `add_core_of`, owner, and controller references.
- [ ] `common/scripted_localisation/*_FR_loc.txt`: French article tag lists.

Converting it to a cosmetic alias:

- [ ] Add it to `common/country_tag_aliases/tag_aliases.txt` with `original_tag` and
      the flag condition.
- [ ] Move its color to `common/countries/cosmetic.txt`. `colors.txt` accepts only real
      tags.
- [ ] Check every `set_cosmetic_tag = TAG` call.

Never search-and-replace `tag = TAG ` across lines that also hold `original_tag`.
Removing `tag = KAS ` from `original_tag = KAS original_tag = KAZ` leaves
`original_original_tag = KAZ`. Handle the two separately, then grep for
`original_original_`.
