---
name: party-names
description: 'Fill or rework a country''s political party localisation in the MD politics view: the 24 subideology name, icon, and description keys plus their scripted-localisation hooks. Use when asked for party names, subideology localisation, or "political parties for TAG", e.g. "/party-names GRE".'
---

Fill a country's parties across the 24 subideology slots: loc keys, descriptions, and
the hooks that make them render.

Requested arguments: $ARGUMENTS (one or more TAGs).

Read `.claude/docs/party-loc-reference.md` first. It holds the slot table, key format,
icon rules, hook mechanics, and verification checklist. This skill is the procedure.

At most 5 TAGs per PR. Split larger requests into separate branches and say so up
front.

## Defaults

Settled. Do not ask about them.

- No TAG given: run `gh issue view 3895 --json body -q .body`, take the first `- [ ]`
  tag, and work that tag only.
- Branch: `git fetch origin main`, then
  `git switch -c 3895-party-loc-batch-N origin/main`, with N one above the highest
  existing local or remote batch branch. Never reuse an old batch branch.
- Research, then re-verify: one research agent per tag, then a fresh agent re-verifies
  every party, slot fit, and gate date against sources. Only then present the mapping.
- Style: the `ENG` block for shape (header, `\n\n`, two paragraphs) and the `HOL` block
  for register. Present tense. What the party stands for, how it governs or campaigns,
  its foreign-policy posture, and where its leverage lies. No leader parades,
  chronologies, or founding narratives. 90 to 120 words per `_desc` including the header.
- Identity only: each `_desc` describes the party under its own gate. Never say what it
  later becomes. "Renamed in 2015 from X" in the post-2015 variant is fine.
- Dates: none before 2000, not even founding years. Post-2000 events may carry a year,
  never a day. No election results, percentages, seat counts, or speculation.
- Gating: only on a verified identity change (rename, merger, ban, dissolution, split),
  never on a founding alone, and always a country flag set by a flavor event.
- Icons: a generic sprite means no `_icon` key and no `_icon` hook.
- Slot 23: the monarchist party while out of power, and the royal house when
  `check_variable = { ruling_party = 23 }`.
- Moving a party between slots: first grep the focus tree, events, and
  `*_political_leaders.txt` for `ruling_party = N` and `*_are_in_power` gates, and move
  the leader block with the party.
- PR title: "Standardize party localisation for TAG[, TAG]". Tick the tag's box in
  #3895 when the PR opens.
- Changelog: one shared line under Content,
  ` - Standardized and historical party names for the countries: TAG, TAG`. Append the
  tag to it.

## Steps

1. Inventory what exists:

   ```bash
   grep -n "^ TAG\." localisation/english/MD_politics_view_parties_l_english.yml
   grep -n "localization_key = TAG\." common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt
   grep -n 'name = "GFX_TAG_' interface/MD_parties_icons.gfx
   grep -n "party_pop_array" "history/countries/TAG - *.txt"
   ```

   Report which slots are filled, which names lack the `£ICON (ABBRV) - Name` form,
   which `_desc` values are empty, and which keys have no hook and are already dead.

2. Research the country's real parties for 2000 to 2025 and map them to slots: native
   name and transliteration, abbreviation, ideology, and two or three concrete facts.
   Use verifiable sources only: Wikipedia and its references, the party's site, the
   electoral commission or parliament, and reputable news archives. Drop any claim you
   cannot verify, and leave a slot generic when there is no real counterpart. Plan a
   flag-gated variant pair for each mid-period identity change. Then have a fresh agent
   re-verify the list.

3. Confirm the slot mapping, and the slots left generic, before writing.

4. Check sprites: tag sprite or generic for each party. Verify each `£name` resolves in
   `interface/`.

5. Write the loc block in `MD_politics_view_parties_l_english.yml`, in tag-alphabetical
   position, ordered by `^N`, with the leading space and the BOM intact.

6. Wire the hooks: one line in `<slot>_L` and `<slot>_L_desc` per filled slot, and in
   `<slot>_L_icon` only where a tag sprite exists. Insert alphabetically by tag.

   For each verified identity change, write one event in the tag's events file at the
   next free id (`Botswana_events.8` is the reference):
   - `is_triggered_only = yes`, `fire_only_once = yes`,
     `trigger = { original_tag = TAG }`, no `picture`.
   - One option: `set_country_flag = TAG_<party>_<change>` and
     `update_party_name = yes`. Move popularity only when a merger empties a slot.
   - Schedule it in `trigger_year_YYYY_events` in `00_yearly_effects.txt` with `days` on
     the real date. Add `random_days` when only the month is known.
   - Loc in `MD_focus_TAG_l_english.yml`: two or three factual sentences, same date
     rules as the descriptions.
   - All three hooks gate on the flag: the flag line first, the `NOT` line second.

7. Verify: recheck style against ENG and HOL, grep the block for any `19xx` year, run
   `python tools/validation/validate_party_loc.py --tag <TAG>` until clean, and work the
   reference doc's checklist. Confirm the branch touches at most 5 TAGs. In game, open
   the politics view at the start date, then fire each new event and check the name,
   description, and icon swap.
