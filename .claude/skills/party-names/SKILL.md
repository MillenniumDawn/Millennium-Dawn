---
name: party-names
description: 'Fill or rework a country''s political party localisation in the MD politics view — the 24 subideology name/icon/description keys plus their scripted-localisation hooks. Use when asked for party names, subideology localisation, or "political parties for TAG", e.g. "/party-names GRE".'
---

Fill in a country's political parties across all 24 subideology slots: the localisation
keys, the descriptions, and the scripted-localisation hooks that make them render.

Requested arguments: $ARGUMENTS (a 3-letter TAG; ask if none given).

Read `.claude/docs/party-loc-reference.md` first — it holds the slot table, the key format,
the icon rules, the hook mechanics, and the verification checklist. This skill is the
procedure; that doc is the reference.

**Hard limit: at most 5 TAGs per PR.** When asked for more, split the work into separate
branches/PRs of 5 TAGs or fewer and say so up front. Never append a sixth TAG to an existing
party-loc branch.

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

   Run `python tools/validation/validate_party_loc.py --tag <TAG>` until it is clean, then
   work the rest of the reference doc's verification checklist. Confirm the branch touches
   the party blocks of at most 5 TAGs before pushing. Finally, in game, open the politics
   view at the start date and at any date the gates split on.
