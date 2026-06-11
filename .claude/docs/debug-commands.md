# Quick Debug Commands

In-game console recipes for testing Millennium Dawn systems, with a focus on the
European Union / USoE subsystem. Paste these into the HOI4 console while running the
mod.

> All identifiers below are verified against the current codebase. When a recipe calls
> a scripted effect, the effect name is the exact one defined in `common/scripted_effects/`.

## Console basics

| Command | Effect |
| --- | --- |
| `` ` `` / `~` / `²` | Open the console (key depends on keyboard layout) |
| `debug` | Toggle the master debug overlay |
| `tdebug` | Toggle on-map tooltips (province IDs, state IDs, variable readouts) |
| `tag TAG` | Switch the country you control (e.g. `tag GER`) |
| `observe` / `tag ---` | Drop into observer mode |
| `event <id>` | Fire an event on the player (e.g. `event EUevent.3`) |
| `effect <script>` | Run arbitrary effect script in the **player country** scope |

### Running MD scripted effects

The `effect` console command executes any effect block in the player's scope. This is the
primary way to drive MD systems by hand:

```
effect add_ideas = EU_member
effect apply_USoE_technologies = yes
effect set_variable = { global.current_active_agenda_disp = 203 }
```

You can chain multiple statements in one `effect` call:

```
effect = { add_ideas = EU_member set_country_flag = EU_candidate }
```

## General cheats

| Command | Effect |
| --- | --- |
| `research all` | Unlock every technology for the player |
| `research_on_icon_click` | Click a tech to grant it instantly |
| `ic` / `instantconstruction` | Buildings finish instantly |
| `fow` | Toggle fog of war |
| `pp <n>` / `add_political_power <n>` | Add political power |
| `st <n>` / `add_stability <n>` | Add stability (decimal, e.g. `st 0.2`) |
| `allowtraits` | Remove trait assignment restrictions |
| `manpower <n>` | Add manpower |
| `xp <n>` | Add army/navy/air XP |

## Inspecting variables, flags, and arrays

HOI4 has no direct "print variable" console command. Three practical options:

1. **`tdebug` tooltips** — hover a country/state with debug tooltips on to read its
   variables and flags inline.
2. **Log dump** — write the value to the game log, then read
   `~/.local/share/Paradox Interactive/Hearts of Iron IV/logs/game.log`:

   ```
   effect log = "EU_passed_votes^0 = [?global.EU_passed_votes^0]"
   effect log = "active agenda = [?global.current_active_agenda_disp], active vote = [?global.current_active_vote_disp]"
   ```

3. **Scripted-loc readout** — most EU display values already surface through the EU GUI;
   open the relevant panel after changing state.

## EU / USoE debug recipes

### Become or drop EU membership

```
# Join: the EU_member idea's on_add pushes THIS into global.EU_member
effect add_ideas = EU_member

# Leave: on_remove pops THIS from global.EU_member and runs leaving_EU
effect remove_ideas = EU_member
```

### Mark a passed agenda without running a full vote

`global.EU_passed_votes` is the source of truth for "agenda EUxxx passed". Every
`focus_EUxxx_accepted` trigger reads it.

```
# Record that EU203 passed (opens every gate keyed on focus_EU203_accepted)
effect add_to_array = { global.EU_passed_votes = 203 }

# Undo
effect remove_from_array = { global.EU_passed_votes = 203 }
```

### Force a council (QMV) vote outcome

The QMV resolvers are `focus_EUxxx_QMV_result`. They branch on
`EU_voting_decision_result_trigger`; the YES branch calls
`cleanup_european_union_voting_yes` (which records the pass in `EU_passed_votes`).

```
# Set the active vote, then resolve it as passed
effect set_variable = { global.current_active_vote_disp = 203 }
effect focus_EU203_QMV_result = yes
```

### Form the United States of Europe (EU111)

The full formation runs through `focus_EU111_QMV_result` (annexes members, transfers
cores, applies pooled tech). As a member-state player:

```
effect focus_EU111_QMV_result = yes
```

The legacy event path (`EUevent.3`) does the same thing but is currently unreferenced;
fire it directly only for isolated testing:

```
event EUevent.3
```

### Test pooled technology transfer (`apply_USoE_technologies`)

`apply_USoE_technologies` pools every `global.EU_member`'s researched techs onto `EUU`
(the tech-bank tag), then applies the union to ROOT. **Precondition:** `EUU` must already
hold each member's tech, so load it first:

```
effect = {
    for_each_scope_loop = { array = global.EU_member  EUU = { inherit_technology = PREV } }
    apply_USoE_technologies = yes
}
```

`apply_USoE_technologies` builds `ROOT.eu_technologies`, applies each token via
`set_technology`, then clears the array — so nothing lingers in the save afterward.

### Recompute the EU Parliament

```
effect clear_EU_Parliament = yes      # wipe all PG flags + per-party globals
effect election_EU_Parliament = yes   # recompute MEP totals / majority
```

## Key EU state handles

| Handle | Kind | Meaning |
| --- | --- | --- |
| `global.EU_member` | country array | Current EU member states |
| `global.EU_potential` | country array | Candidate / potential members |
| `global.EU_passed_votes` | int array | Agenda IDs that have passed (source of truth) |
| `global.EU_council_votes` | int array | Agenda IDs currently in council voting |
| `global.current_active_agenda_disp` | int | Agenda being voted in the EP (0 = none) |
| `global.current_active_vote_disp` | int | Agenda in the council vote (0 = none) |
| `EU_member` | idea | Membership; `on_add`/`on_remove` maintain `global.EU_member` |
| `USoE` | country flag | Set on the formed United States of Europe |
| `USoE_member` | country flag | Set on each nation folded into the USoE |
| `EUU` | tag | Tech-bank country used to pool member technologies |
