# Refactor Breaking-Change Checklist

Systematic steps to verify a large-scale rename, refactor, or subsystem rewrite doesn't silently break the game.

Run these checks **after** automated review and **before** declaring the PR ready.

---

## 1. Prefix / Name Rename Verification

When renaming a prefix (e.g., `AC_` -> `investments_`), verify no stale references remain anywhere in the repo.

```bash
# Flags
grep -rn "old_flag_name" common/ events/

# Variables
grep -rn "old_variable_name" common/ events/

# Event IDs
grep -rn "old_namespace\." common/ events/

# Decision IDs
grep -rn "old_decision_id" common/ events/

# Scripted loc names
grep -rn "old_scripted_loc_name" common/ localisation/

# GUI window names
grep -rn "old_window_name" interface/ common/scripted_guis/

# GFX sprite names
grep -rn "GFX_old_prefix" interface/ gfx/

# Opinion modifiers
grep -rn "old_opinion_modifier" common/ localisation/
```

**Tip:** Search the **entire repo**, not just changed files. Other subsystems, `on_actions`, and country-specific overrides may reference the old names.

---

## 2. Array Index Semantic Verification

When a function uses array subscripts (`^idx`), trace every caller to confirm `idx` holds the expected value.

### Common Index Confusions

| Variable       | Typical Meaning       | What It Is NOT        |
| -------------- | --------------------- | --------------------- |
| `project`      | Slot index (0..14)    | Building type (1..14) |
| `project_type` | Building type (1..14) | Slot index            |
| `i` / `v`      | Loop position / value | Depends on context    |

### Checklist

- [ ] For every function that reads `foo^bar`, find every place `bar` is set.
- [ ] Confirm `bar` is set **before** the function is called.
- [ ] If `bar` is an argument-like variable, verify no caller passes the wrong index type.
- [ ] If the function writes to `foo^bar`, confirm `bar` is a valid slot index at write time.

**Example bug:** `project_build_amount^project_type` reads the build amount at the **building type** index, not the **slot** index. Fixed by using `project_build_amount^project`.

---

## 3. Global Variable -> Array Migration

When replacing individual globals with an array, check:

- [ ] Every old global reference in **scripted effects** is updated to the array lookup.
- [ ] Every old global reference in **scripted triggers** is updated.
- [ ] Every old global reference in **scripted localisation** is updated.
- [ ] **Localisation strings** using `[?global.old_name]` are updated. These fail silently to 0.
- [ ] Any **other mods or submods** that depend on this mod are checked (if applicable).

---

## 4. Function Precondition Verification

When a function's requirements change, verify all callers meet the new preconditions.

| Change                                | What to Check                                           |
| ------------------------------------- | ------------------------------------------------------- |
| Requires variable X to be set first   | Every caller sets X before calling                      |
| Requires temp variable Y              | Every caller sets Y in the right scope                  |
| Assumes array Z is initialized        | `resize_array` or `set_variable` runs before first call |
| Expects `project > -1` for slot logic | Callers with `project = -1` don't enter the slot branch |

---

## 5. Event Namespace and Option Consistency

- [ ] `add_namespace = foo` at the top of the file matches every `country_event = { id = foo.N }`.
- [ ] Every event option's `log =` string matches its `name =` key suffix (`.a`, `.b`, etc.).
- [ ] Every option name key (`foo.N.a`, `foo.N.b`) has a matching loc entry.
- [ ] Event title key is `foo.N.t`, description is `foo.N.d`.

---

## 6. Decision Namespace Consistency

- [ ] Every decision ID in `common/decisions/*.txt` has a matching loc entry.
- [ ] Decision category names in `common/decisions/categories/*.txt` match the category referenced in decisions.
- [ ] `highlight_states_trigger` uses `THIS` or `ROOT` correctly for state scope.
- [ ] `days_remove` / `days_mission_timeout` references a variable that exists at activation time.

---

## 7. GUI and GFX Cross-Reference

- [ ] Every `window_name` in `scripted_gui` has a matching `containerWindowType` in `.gui` files.
- [ ] Every button `name` in `scripted_gui` `effects` matches a `buttonType` / `iconType` in `.gui`.
- [ ] Every `spriteType` referenced in `.gui` has a matching `name` in `.gfx` files.
- [ ] Every `.gfx` `texturefile` path points to an existing `.dds` file.

---

## 8. Decision `visible` Block Performance

- [ ] `visible = { always = no }` is fine for scripted-effect-only decisions.
- [ ] Any non-trivial `visible` block is checked for `every_country` / `any_country` without a narrow array.
- [ ] Complex `visible` blocks should be replaced with a cached flag set in `on_actions`.

---

## 9. `ai_will_do` Syntax

- [ ] `ai_will_do = { base = N }` is used, not `factor = N` at root level.
- [ ] `ai_chance` inside event options also uses `base = N`.

---

## 10. Scope Safety

- [ ] `CONTROLLER` is only used inside a **state scope**.
- [ ] `var:X = { ... }` checks `exists = yes` when X might be 0 or -1 (uninitialized).
- [ ] Division operations guard the denominator with `clamp_temp_variable` or a zero-check.

---

## 11. Country Tag Removal / Consolidation

When removing a country tag entirely (not just renaming), check every layer:

### Files to update

- [ ] `common/country_tags/00_countries.txt` — remove the tag definition
- [ ] `common/countries/TAG - Name.txt` — delete the country file
- [ ] `history/countries/TAG - Name.txt` — delete the history file
- [ ] `common/countries/colors.txt` — remove the color entry (or move to `cosmetic.txt` if keeping as alias)
- [ ] `history/states/*.txt` — remove `add_core_of = TAG` and owner/controller references
- [ ] `common/scripted_localisation/*_FR_loc.txt` — remove from French article trigger tag lists

### If converting to a cosmetic tag alias

- [ ] Add entry to `common/country_tag_aliases/tag_aliases.txt` with `original_tag` and flag condition
- [ ] Move color definition from `colors.txt` to `common/countries/cosmetic.txt` — `colors.txt` only accepts real country tags
- [ ] Verify `set_cosmetic_tag = TAG` calls in events reference the alias correctly

### Find-and-replace pitfalls

- [ ] **Never** search-and-replace `tag = TAG ` in dense tag lists on `original_tag` lines — removing `tag = KAS ` from inside `original_tag = KAS original_tag = KAZ` leaves `original_original_tag = KAZ`. Process `tag =` and `original_tag =` lines separately.
- [ ] After bulk replacement, grep for `original_original_` to catch doubled prefixes.

### Cross-references to verify

```bash
# Find ALL remaining references to the removed tag
grep -rn "TAG" common/ events/ history/ localisation/ interface/ --include="*.txt" --include="*.yml" | grep -v "tag_aliases\|cosmetic\|colors"
```
