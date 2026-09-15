---
name: party-names
description: 'Fill or rework a country''s political party localisation in the MD politics view — the 24 subideology name/icon/description keys plus their scripted-localisation hooks. Use when asked for party names, subideology localisation, or "political parties for TAG", e.g. "/party-names GRE".'
---

Fill in a country's political parties across all 24 subideology slots: the localisation
keys, the descriptions, and the scripted-localisation hooks that make them render.

Requested arguments: $ARGUMENTS (one or more 3-letter TAGs; see Defaults when none given).

Read `.claude/docs/party-loc-reference.md` first — it holds the slot table, the key format,
the icon rules, the hook mechanics, and the verification checklist. This skill is the
procedure; that doc is the reference.

**Hard limit: at most 5 TAGs per PR.** When asked for more, split the work into separate
branches/PRs of 5 TAGs or fewer and say so up front. Never append a sixth TAG to an existing
party-loc branch.

## Defaults

These are settled; do not ask about them again.

- **No TAG given:** run `gh issue view 3895 --json body -q .body`, take the first `- [ ]`
  tag, and work that one tag only.
- **Branch:** always a fresh `3895-party-loc-batch-N` off `origin/main`, where N is one
  more than the highest existing local or remote `3895-party-loc-batch-*`. Never reuse or
  extend an old batch branch.
- **Research, then re-verify:** one research agent per tag, then a separate fresh agent
  re-verifies every party, slot fit and gate date against sources. Only after that is the
  mapping presented for confirmation (step 3).
- **Style standard:** the `ENG` block for shape (header, `\n\n`, two paragraphs) and the
  `HOL` block for prose register. Present tense; what the party stands for, how it governs
  or campaigns, its foreign-policy posture where relevant, and where its leverage lies. No
  leader parades, chronologies or founding narratives. Target 90–120 words per `_desc`
  including the header.
- **Dates:** no dates before 2000 at all, not even founding years. Post-2000 events may
  carry a year but never a day-level date; no election results, percentages, seat counts,
  or "entered/left parliament" outcomes; no speculation about future outcomes.
- **Gating:** only on verified identity changes (rename, merger, ban, dissolution), never
  on a founding alone.
- **Icons:** a generic sprite means no `_icon` key and no `_icon` hook. Ignore reviewers
  that flag "missing icon keys" for generic sprites.
- **Slot 23:** show the monarchist party while out of power and the royal house when
  `check_variable = { ruling_party = 23 }` (AUS Habsburg precedent).
- **Moving a party between slots:** first grep the country's focus tree, events and
  `*_political_leaders.txt` for `ruling_party = N` and `*_are_in_power` gates, and move the
  leader block with the party.
- **After writing:** a second style recheck against ENG/HOL plus a grep of the block for
  any `19xx` year, then the validator.
- **PR:** title "Standardize party localisation for TAG[, TAG]", no changelog entry, and tick
  the tag's box in #3895 when the PR is opened.

## Steps

1. **Inventory what exists**

   ```bash
   grep -n "^ TAG\." localisation/english/MD_politics_view_parties_l_english.yml
   grep -n "localization_key = TAG\." common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt
   grep -n 'name = "GFX_TAG_' interface/MD_parties_icons.gfx
   grep -n "party_pop_array" "history/countries/TAG - *.txt"
   ```

   Report which of the 24 slots are filled, which names are still bare `£ICON Name` rather
   than the `£ICON (ABBRV) - Name` standard, which `_desc` values are empty, and — the one
   that bites — which existing keys have **no hook** and are therefore already dead.

2. **Research the parties**

   Research the country's real political parties for 2000–2025 and map them to slots. For
   each: official native name and transliteration, abbreviation, founding year (and
   dissolution if defunct), founder or defining leader, precise ideology, and two or three
   concrete facts — best electoral result, splits, coalitions, EP group.

   Leave a slot generic when the country has no real counterpart. Do not invent parties.
   Non-party entities are allowed only where the reference doc says so.

   Use only verifiable sources: Wikipedia (and the references it cites), the party's own
   website, the national electoral commission / parliament / government register, and
   reputable news archives. Every name, abbreviation, founding year, and fact in a `_desc`
   must be traceable to one of these. If a claim cannot be verified, drop it — leave the
   slot generic rather than guess.

   Where a country's party of a given slot changed identity mid-period (a ban, a rename, a
   successor), plan a date- or flag-gated variant pair instead of picking one.

   Then hand the full candidate list to a fresh agent to re-verify from scratch (see
   Defaults). Drop or downgrade anything it cannot confirm.

3. **Confirm the mapping before writing.**

   Present the slot→party table and the slots you intend to leave generic. This is where
   judgement calls get settled; do not write 50 keys on an unconfirmed mapping.

4. **Check the sprites**

   For each mapped party decide tag sprite vs generic, per the reference doc's icon rules.
   Verify each `£name` resolves in `interface/` before writing it.

5. **Write the loc block**

   Replace or extend the tag's contiguous block in
   `localisation/english/MD_politics_view_parties_l_english.yml`, keeping it in tag-alphabetical
   position and ordering keys by `^N` index. Leading space on every line; the file keeps its
   UTF-8 BOM.

6. **Wire the hooks**

   Add a line to `<slot>_L` and `<slot>_L_desc` for every filled slot, and to `<slot>_L_icon`
   only where a tag sprite exists, in
   `common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt`. Insert
   alphabetically by tag. Gated variants go in adjacent pairs, most specific first, and a
   date-split name needs its icon hook split to match.

7. **Verify**

   Run the post-write style recheck from Defaults, then
   `python tools/validation/validate_party_loc.py --tag <TAG>` until it is clean, then work
   the rest of the reference doc's verification checklist. Confirm the branch touches the
   party blocks of at most 5 TAGs before pushing. Open the PR and tick the tag's box in
   #3895. Finally, in game, open the politics view at the start date and at any date the
   gates split on.
