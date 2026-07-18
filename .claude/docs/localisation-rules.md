# Localisation Rules

## Language & Encoding

- English is the only language to edit. All other language files are managed via Paratranz — **do not touch them**.
- All `.yml` files must be **UTF-8 with BOM**.
- First line must be `l_english:` with no leading whitespace.
- Use **1 space** of indentation per key (not tabs).

## File Naming

- **All country-specific localisation** (events, focuses, decisions, ideas, missions for one country) goes in the **single unified file** `MD_focus_TAG_l_english.yml`. Do **not** split per subsystem (e.g., `MD_TAG_rebellion_l_english.yml`, `MD_TAG_events_l_english.yml`). One country, one loc file.
- Only create a **separate** loc file for a standalone cross-country mechanic owned by no single country (e.g., `MD_NATO_events_l_english.yml`, `MD_tooltips_l_english.yml`).
- Check existing files in `localisation/english/` for the naming pattern before creating new ones.

## Key Formatting

- Keys use **no trailing version number**: `key: "value"`, not `key:0 "value"`.
- Key naming mirrors the script ID exactly (e.g., focus `SER_free_market_capitalism` → `SER_free_market_capitalism: "..."`, `SER_free_market_capitalism_desc: "..."`).
- Focus/decision/event keys: `ID`, `ID_desc` (tooltip body). Events also need `ID.t` (title), `ID.d` (description), and `ID.a`, `ID.b`, … (option names).
- Every new script object (focus, decision, event, idea, MIO, subideology) needs matching loc keys before it goes in.
- Undefined `[variable]` substitutions: every `[Foo.GetBar]` or `[my_var]` must correspond to a real scope getter or set variable. A missing or misspelled getter renders as an empty string or literal `[variable_name]` in-game.

## Writing Style

- **Grammar and correctness first.** Proofread for subject-verb agreement, punctuation, sentence completeness.
- **Be concise.** Remove filler and redundancy. Prefer shorter sentences.
- **No excessive hyphenation.** Only hyphenate compound modifiers before a noun (e.g., "pro-Western government"), not elsewhere.
- **No ellipsis abuse.** Do not use `...` in descriptions or tooltips.
- **No em dashes** (`—`) in player-facing strings. Use a period when the clause stands alone ("Their economy answers to us. Their borders remain intact."), a comma for a participial phrase ("...transfers weekly, appearing as a new expense..."), or a colon to introduce a list or requirement ("Requires war contribution: one battle won or three months at war."). Em dashes read as soft connectors and almost always replace one of those three.
- Capitalize proper nouns, party names, ideology group names, and in-game concepts (e.g., Political Power, Stability).
- No all-caps for emphasis; use in-game formatting codes if needed (e.g., `£icon`, `§Y...§!`).
- **No padding filler.** Every sentence should carry real information — founding facts, political orientation, mechanical implication, alignment. Sentences that restate the title or fill space with "the party has remained influential over the years" add nothing. Applies to subideology descs, focus descs, idea descs, event flavour, and option text alike.

## Subideology Localisation Format

Three keys required per country subideology entry:

```plaintext
TAG.ideology: "£PARTY_ICON (ABBRV) - Party Name"
TAG.ideology_icon: "£PARTY_ICON"
TAG.ideology_desc: "(Dominant Ideology) - Party Name (Language: Native Name, Language: Native Name, ABBRV)\n\nDescription paragraph."
```

Rules:

- **Short name** (`TAG.ideology`): icon + abbreviation in parentheses + dash + English party name.
- **Icon** (`TAG.ideology_icon`): icon reference only, no extra text.
- **Description** (`TAG.ideology_desc`): opens with the dominant ideology group in parentheses (e.g., `(Classic Liberalism)`), then the full English party name, then native-language names in parentheses as `Language: Native Name`, comma-separated, followed by the abbreviation. A `\n\n` separates the header line from the body. Body: 2–5 sentences covering founding, political orientation, notable history, and international alignments. Third person, past/present mix, encyclopedic tone. The "no padding filler" rule applies.

Example:

```plaintext
MOR.conservatism: "£MOR_NRI (RNI) - National Rally of Independents"
MOR.conservatism_icon: "£MOR_NRI"
MOR.conservatism_desc: "(Classic Liberalism) - National Rally of Independents (Arabic: Altajamue Alwataniu Lil'ahrar, French: Rassemblement National des Indépendants, Standard Moroccan Tamazight: Agraw Anamur y Insimann, RNI)\n\nFounded in 1978 by Prime Minister Ahmed Osman, the party has consistently remained a major player in Moroccan politics. Nominally social-democratic, it is widely regarded as pro-business and liberal, and cooperates closely with parties of a liberal orientation. It holds observer status in the Liberal International and is affiliated with the Africa Liberal Network and the European People's Party."
```

## Event Localisation

- `ID.t`: short, punchy title, no more than 6–8 words.
- `ID.d`: 1–3 sentences of flavour or context. No mechanical descriptions (those belong in option text or tooltips).
- `ID.a`, `ID.b`, …: option names read as a player decision or action, not a description (e.g., `"Provide funding"` not `"The government provides funding"`).

## Ideas & Focuses

- Name (`name: "..."`) title-cased, concise (3–6 words typical).
- Description explains what the idea represents in 1–3 sentences. Do not repeat modifier values verbatim; describe their political or economic meaning.

## YAML Validity

HOI4 loc files are checked by `check-yaml` in the pre-commit hook. The HOI4 format is not strict YAML, so several patterns cause parse failures:

- **Embedded double quotes**: `"He called it "important""` is invalid. Use `\"important\"` or rephrase to remove the inner quotes.
- **Mixed indentation**: all keys must be consistently indented (all with 1 leading space, or all without). Mixing makes YAML see two separate mappings. Remove stray spaces.
- **Colons in values**: a bare colon followed by a space inside a quoted string can confuse some parsers — wrap values in quotes (safe) and watch for unquoted values.

## Loc Key Collisions Between Game Objects

An idea's `name = X` redirects **both** the displayed name and the tooltip description: the game looks up `X` for the name and `X_desc` for the description. The idea's own ID is no longer used for loc.

Collision risk when an idea shares a name with a focus, decision, event, or other idea:

- A focus `id = ENG_british_commercial_spaceport` and idea `name = ENG_british_commercial_spaceport` both read the same `ENG_british_commercial_spaceport` / `_desc` keys.
- If both define those keys in the same `.yml`, YAML treats it as a duplicate and the later definition wins — the focus name silently changes to the idea's text (or vice versa).
- Even if only one side defines the keys, the other object displays whatever text is there, usually wrong.

**Rule:** Pick a `name = X` that no focus, decision, or other idea uses. Even when the display text intentionally matches a focus (e.g., the focus awards the idea and they share branding), use a distinct key — they may need to diverge later, and identical text in two keys is cheap.

Quick check before merging:

```bash
# Replace KEY with the value of your `name = ` field
grep -rn "id = KEY\b\|^\s*KEY:\s*\"" common/ localisation/english/
```

Hits in both `common/national_focus/` and `common/ideas/` for the same KEY = rename one side.

## Common Mistakes to Avoid

| Wrong                                                                   | Correct                                                                     |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `key:0 "value"`                                                         | `key: "value"`                                                              |
| `...` trailing sentences                                                | End with a full stop                                                        |
| `Pro-Western` mid-sentence as a standalone noun                         | `pro-Western` (adjective)                                                   |
| Repeating the same sentence across multiple ideology descs              | Unique body per entry                                                       |
| Empty or placeholder strings like `"TODO"`                              | Always provide a complete string                                            |
| `"text "quoted word" more text"`                                        | `"text \"quoted word\" more text"`                                          |
| Mixed indented/non-indented keys in same file                           | All keys at same indentation level                                          |
| Backtick `` ` `` as apostrophe: ``"we`ll"``                             | `"we'll"` — use the real apostrophe                                         |
| Cyrillic lookalike characters (e.g., `С`, `а`, `е`) in English text     | Latin equivalents — run a non-ASCII check                                   |
| Non-English text in `*_l_english.yml` (French, Russian, Spanish titles) | Full English translation                                                    |
| Duplicate keys in the same `.yml` file                                  | Remove the earlier duplicate; keep only one definition per key              |
| Wrong color-code prefix, e.g. `§RY` (stray extra character)             | `§R` then text immediately — no stray character between code and content    |
| Copy-pasted country-specific flavour text left unreplaced               | Update every reference to the original country's name, demonym, and culture |
| Lowercase scope keywords: `[From.GetName]`, `[Root.GetName]`            | Always uppercase: `[FROM.GetName]`, `[ROOT.GetName]`, `[THIS.GetName]`      |

## Recurring Typos

See [`.claude/docs/typo-watchlist.md`](.claude/docs/typo-watchlist.md) for the full list. Check it when reviewing localisation files.
