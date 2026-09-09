# Party Localisation Reference

How a country's political parties are named, described, and iconified in the MD politics
view. Read before adding or reworking any `TAG.<subideology>` key.

Three files are always involved:

- `localisation/english/MD_politics_view_parties_l_english.yml` — the name / icon / desc strings
- `common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt` — the per-tag
  hooks that select them
- `interface/MD_parties_icons.gfx` — the `GFX_<TAG>_<party>` sprites

**A loc key with no hook is dead.** Writing the `.yml` block is only half the job — the
politics view never reads `TAG.conservatism` directly, it calls `[conservatism_L]`, which
resolves through the scripted-localisation switch. This is the single most common mistake.

## The 24 subideologies

Defined in `common/ideologies/00_ideologies.txt`. The `^N` index is the country's
`party_pop_array` slot, set in `history/countries/<TAG>*.txt`; the index↔slot mapping is
documented at `MD_politics_view_parties_l_english.yml:38-61`.

| `^N` | Subideology                  | Ideology      | Generic label                 |
| ---- | ---------------------------- | ------------- | ----------------------------- |
| 0    | `Western_Autocracy`          | `democratic`  | Pro-Western Autocrats         |
| 1    | `conservatism`               | `democratic`  | Conservatives                 |
| 2    | `liberalism`                 | `democratic`  | Liberals                      |
| 3    | `socialism`                  | `democratic`  | Social Democrats              |
| 4    | `Communist-State`            | `communism`   | Communists                    |
| 5    | `anarchist_communism`        | `communism`   | Left-Wing Radicals            |
| 6    | `Conservative`               | `communism`   | Reactionaries                 |
| 7    | `Autocracy`                  | `communism`   | Autocrats                     |
| 8    | `Mod_Vilayat_e_Faqih`        | `communism`   | Moderate Shiite Revolutionary |
| 9    | `Vilayat_e_Faqih`            | `communism`   | Hardline Shiite Revolutionary |
| 10   | `Kingdom`                    | `fascism`     | Pro-Establishment Salafism    |
| 11   | `Caliphate`                  | `fascism`     | Salafi Jihadism               |
| 12   | `Neutral_Muslim_Brotherhood` | `neutrality`  | Moderate Islamists            |
| 13   | `Neutral_Autocracy`          | `neutrality`  | Non-Aligned Autocrats         |
| 14   | `Neutral_conservatism`       | `neutrality`  | Conservatives                 |
| 15   | `oligarchism`                | `neutrality`  | Oligarchs                     |
| 16   | `Neutral_Libertarian`        | `neutrality`  | Libertarians                  |
| 17   | `Neutral_green`              | `neutrality`  | Greens                        |
| 18   | `neutral_Social`             | `neutrality`  | Socialist Democrats           |
| 19   | `Neutral_Communism`          | `neutrality`  | Communists                    |
| 20   | `Nat_Populism`               | `nationalist` | Right Wing Populists          |
| 21   | `Nat_Fascism`                | `nationalist` | Fascists                      |
| 22   | `Nat_Autocracy`              | `nationalist` | Military Junta                |
| 23   | `Monarchist`                 | `nationalist` | Monarchists                   |

Case matters: `Communist-State` is hyphenated, `neutral_Social` and `oligarchism` are the
only two with a lowercase first letter.

## Key format

```
 TAG.subideology: "£PARTY_ICON (ABBRV) - Party Name"
 TAG.subideology_icon: "£PARTY_ICON"
 TAG.subideology_desc: "(Ideology Group) - Party Name (Native: Nativename, ABBRV)\n\nDescription."
```

Worked example (`MOR`, `MD_politics_view_parties_l_english.yml:7939`):

```
 MOR.conservatism: "£MOR_NRI (RNI) - National Rally of Independents"
 MOR.conservatism_icon: "£MOR_NRI"
 MOR.conservatism_desc: "(Classic Liberalism) - National Rally of Independents (Arabic: Altajamue Alwataniu Lil'ahrar, French: Rassemblement National des Indépendants, RNI)\n\nNominally a social-democratic party, the party often cooperates with other parties with liberal orientation…"
```

Rules:

- Every line carries a **leading space** before the key. The file is UTF-8 **with** BOM.
- All of a tag's keys sit in **one contiguous block**, placed alphabetically by tag among
  its neighbours, and ordered inside the block by `^N` index.
- `(Ideology Group)` in the desc is the party's real-world ideological label
  (`Liberal Conservatism`, `Democratic Socialism`, `Salafi Jihadism`), not the MD
  subideology token.
- Native names go in parentheses after the English name, one language per label
  (`Greek: …`, `Arabic: …`, `French: …`), abbreviation last.
- `\n\n` is a literal backslash-n pair in the `.yml`, not a real newline.
- Descriptions are encyclopedic and factual — founding year, founder, ideology, electoral
  record, splits, EP group. No editorialising, no purple prose.
- Reference-quality tags to copy from: `MOR` (`:7936`), `ITA` (`:6934`), `GEO` (`:6470`).

## Icons

A party gets an `_icon` key **only** when a tag-specific sprite exists — i.e. a
`spriteType` in `interface/MD_parties_icons.gfx` backed by a real `.dds` under
`gfx/texticons/parties_icons/<country>/`. Verify before writing the reference:

```bash
grep -n 'name = "GFX_TAG_' interface/MD_parties_icons.gfx
ls gfx/texticons/parties_icons/<country>/
```

With no tag sprite, use the generic one inline in the name key and **omit the `_icon` key
entirely** — the icon `defined_text` falls back to `generic.<slot>_icon` on its own
(`MOR.Caliphate` and `MOR.Vilayat_e_Faqih` are the precedent). Generic sprites are
`GFX_generic_<slot>_small`, with two irregulars:

- `Communist-State` → `£generic_Communist_State_small` (underscore, not the slot's hyphen)
- `Neutral_Muslim_Brotherhood` → `£muslim_brotherhood_small` (no `generic_` prefix)

Never invent a `GFX_` name; an undefined sprite renders nothing.

## The three hook blocks

`common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt` holds three
`defined_text` blocks per subideology:

| Block           | Selects     | Example name         |
| --------------- | ----------- | -------------------- |
| `<slot>_L`      | Party name  | `conservatism_L`     |
| `<slot>_L_desc` | Description | `Nat_Fascism_L_desc` |
| `<slot>_L_icon` | Sprite      | `Monarchist_L_icon`  |

Each is a switch whose lines are sorted **alphabetically by tag** and terminate in a
generic fallback:

```
	text = { trigger = { original_tag = GRE } localization_key = GRE.conservatism }
	…
	text = { localization_key = generic.conservatism }
```

Add one line per block per party. Insert alphabetically; a misplaced line still works but
makes the next edit harder to review.

Use `original_tag`, never `tag` — a civil-war split-off keeps its original tag and would
otherwise lose its parties.

## Date- and flag-gated variants

**First match wins**, so the more specific line goes first and the pair stays adjacent:

```
	text = { trigger = { original_tag = DEN date < 2016.12.12 } localization_key = DEN.Nat_Fascism }
	text = { trigger = { original_tag = DEN date > 2016.12.12 } localization_key = DEN.Nat_Fascism_2017 }
```

Other precedents: `EST.Nat_Fascism` / `EST.Nat_Fascism2` (flag-gated on
`EST_ekre_has_formed`), `ITA.Nat_Fascism` / `ITA.forza_nuova_loc_key` / `ITA.casapound_loc_key`
(`check_variable = { Nat_Fascism_leader = N }`).

Two traps:

- **Split the icon hook too.** A date-split name with an unconditional `_icon` hook shows
  the old party's logo next to the new party's name.
- **Watch the tag in copy-pasted gate lines.** A `GER`→`GRE` typo in exactly this position
  left Germany showing the generic "Fascists" post-2023 while Greece rendered the German
  party "Die Heimat" — silent, since both tags are valid.

## Choosing parties

Only use organisations that really existed in the 2000–2025 window. If a slot has no real
counterpart in that country, **leave it generic** rather than inventing one — a generic
label is honest, an invented party is not.

Non-party entities are acceptable where the slot has no electoral equivalent and MD
precedent exists: employers' confederations for `oligarchism` (`MOR.Autocracy` = CGEM),
`<Country> Armed Forces` for `Nat_Autocracy` (`ITA.Nat_Autocracy` = Forze Armate Italiane),
and the royal house for `Monarchist`. Say what the entity actually is in its description.

## Verification checklist

1. Every new loc key has a hook in `<slot>_L`, `<slot>_L_desc` and — if a tag sprite exists —
   `<slot>_L_icon`.
2. Total hooks match: `grep -c "localization_key = TAG\." common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt`
   equals names + descs + icons written.
3. No duplicate `original_tag = TAG` inside a single `defined_text` (the second is dead).
4. Every `£sprite` resolves: `grep -rn 'name = "GFX_<name>"' interface/`.
5. Keys alphabetical within the block, leading space on every line, BOM intact.
6. `history/countries/<TAG>*.txt` `party_pop_array^N` indices still line up with the slots
   they are commented as.
