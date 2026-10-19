# Party Localisation Reference

Read before adding or reworking any `TAG.<subideology>` key. Three files are involved:

- `localisation/english/MD_politics_view_parties_l_english.yml`: name, icon, and
  description strings.
- `common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt`: the
  per-tag hooks that select them.
- `interface/MD_parties_icons.gfx`: the `GFX_<TAG>_<party>` sprites.

A loc key with no hook is dead. The politics view calls `[conservatism_L]`, which
resolves through the scripted-localisation switch. It never reads `TAG.conservatism`
directly.

## The 24 subideologies

Defined in `common/ideologies/00_ideologies.txt`. `^N` is the country's `party_pop_array`
slot, set in `history/countries/<TAG>*.txt`.

| `^N` | Subideology                  | Ideology      | Generic label                 |
| ---- | ---------------------------- | ------------- | ----------------------------- |
| 0    | `Western_Autocracy`          | `democratic`  | Pro-Western Autocrats         |
| 1    | `conservatism`               | `democratic`  | Conservatives                 |
| 2    | `liberalism`                 | `democratic`  | Liberals                      |
| 3    | `socialism`                  | `democratic`  | Social Democrats              |
| 4    | `communist_state`            | `communism`   | Communists                    |
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

Case matters. `neutral_Social` and `oligarchism` are the only two with a lowercase first
letter.

## Key format

```
 MOR.conservatism: "£MOR_NRI (RNI) - National Rally of Independents"
 MOR.conservatism_icon: "£MOR_NRI"
 MOR.conservatism_desc: "(Classic Liberalism) - National Rally of Independents (Arabic: Altajamue Alwataniu Lil'ahrar, French: Rassemblement National des Indépendants, RNI)\n\nDescription."
```

- Every line has a leading space before the key.
- A tag's keys sit in one contiguous block, placed alphabetically by tag and ordered
  inside the block by `^N`.
- `(Ideology Group)` is the party's real-world label (`Liberal Conservatism`,
  `Salafi Jihadism`), not the MD subideology token.
- Native names follow the English name, one language per label, abbreviation last.
- `\n\n` is a literal backslash-n pair in the `.yml`.
- Descriptions are factual and present tense, and describe the party as it is under its
  own gate. No forward references to a later rename, merger, or split.
- Tags to copy from: `MOR`, `ITA`, `GEO`.

## Icons

A party gets an `_icon` key only when a tag sprite exists: a `spriteType` in
`interface/MD_parties_icons.gfx` backed by a `.dds` under
`gfx/texticons/parties_icons/<country>/`. Never invent a `GFX_` name.

With no tag sprite, use the generic one inline in the name key and omit the `_icon`
key. The icon hook falls back to `generic.<slot>_icon`. Generic sprites are
`GFX_generic_<slot>_small`, with two irregulars:

- `communist_state` uses `£generic_Communist_State_small`.
- `Neutral_Muslim_Brotherhood` uses `£muslim_brotherhood_small`.

## Hooks

Each subideology has three `defined_text` blocks: `<slot>_L` (name), `<slot>_L_desc`,
and `<slot>_L_icon`. Each is a switch sorted alphabetically by tag that ends in a
generic fallback:

```
 text = { trigger = { original_tag = GRE } localization_key = GRE.conservatism }
 text = { localization_key = generic.conservatism }
```

Add one line per block per party. Use `original_tag`, never `tag`, so a civil-war
split-off keeps its parties.

## Flag-gated variants

A mid-period identity change (rename, merger, dissolution, split) is a flag set by a
flavor event, not a bare `date >` in the hook. First match wins, so the flag line goes
first:

```
 text = { trigger = { original_tag = BOT has_country_flag = BOT_business_botswana_formed } localization_key = BOT.oligarchism_2015 }
 text = { trigger = { original_tag = BOT NOT = { has_country_flag = BOT_business_botswana_formed } } localization_key = BOT.oligarchism }
```

The event (`Botswana_events.8` is the reference) is `is_triggered_only` and
`fire_only_once`, checks `original_tag`, has no picture, and its one option sets the
flag and runs `update_party_name = yes`. Schedule it on the real date in
`common/scripted_effects/00_yearly_effects.txt`.

- Split the icon hook too, or the old logo shows beside the new name.
- Check the tag in copied gate lines. A `GER` for `GRE` typo is silent, since both tags
  are valid.
- Older bare date gates exist. Do not add new ones.

## Choosing parties

Use only organisations that existed in the 2000 to 2025 window. If a slot has no real
counterpart, leave it generic.

Non-party entities are acceptable where MD precedent exists: employers' confederations
for `oligarchism`, `<Country> Armed Forces` for `Nat_Autocracy`, and the royal house for
`Monarchist`. Say what the entity is in its description.

## Verification

```bash
python tools/validation/validate_party_loc.py --tag TAG
```

It covers the name and description formats, key and hook pairing, icon agreement,
miscased subideologies, and duplicate gates. It never reports a missing slot. Check by
hand:

1. Every `£sprite` resolves in `interface/`.
2. Keys are alphabetical within the block, with the leading space and BOM intact.
3. `party_pop_array^N` indices in `history/countries/<TAG>*.txt` match their slots.
4. In game: the politics view at the start date, then after `event <id>` for each new
   identity-change event.
