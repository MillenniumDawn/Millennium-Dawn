# Localisation Rules

## Language & Encoding

- English is the only language to edit. All other language files are managed via Paratranz — **do not touch them**.
- All `.yml` files must be **UTF-8 with BOM** encoding.
- File header must be `l_english:` on the first line with no leading whitespace.
- Use **1 space** of indentation for each key (not tabs).

## Key Formatting

- Keys use **no trailing version number**: write `key: "value"`, not `key:0 "value"`.
- Key naming mirrors the associated script ID exactly (e.g., focus `SER_free_market_capitalism` → `SER_free_market_capitalism: "..."`, `SER_free_market_capitalism_desc: "..."`).
- Focus/decision/event keys follow the pattern: `ID`, `ID_desc` (tooltip body). Events also need `ID.t` (title), `ID.d` (description), and `ID.a`, `ID.b`, … (option names).
- Every new script object (focus, decision, event, idea, MIO, subideology) needs matching loc keys before it goes in.
- Undefined `[variable]` substitutions in loc strings — every `[Foo.GetBar]` or `[my_var]` must correspond to a real scope getter or set variable. A missing or misspelled getter renders as an empty string or literal `[variable_name]` in-game.

## Writing Style

- **Grammar and correctness first.** Proofread for subject-verb agreement, punctuation, and sentence completeness.
- **Be concise.** Remove filler words and redundant phrasing. Prefer shorter sentences.
- **No excessive hyphenation.** Only hyphenate compound modifiers before a noun (e.g., "pro-Western government"), not elsewhere.
- **No ellipsis abuse.** Do not use `...` in descriptions or tooltips.
- Capitalize proper nouns, party names, ideology group names, and in-game concepts (e.g., Political Power, Stability).
- Do not use all-caps for emphasis; use in-game formatting codes instead if needed (e.g., `£icon`, `§Y...§!`).

## Subideology Localisation Format

Three keys are required for every country subideology entry:

```plaintext
TAG.ideology: "£PARTY_ICON (ABBRV) - Party Name"
TAG.ideology_icon: "£PARTY_ICON"
TAG.ideology_desc: "(Dominant Ideology) - Party Name (Language: Native Name, Language: Native Name, ABBRV)\n\nDescription paragraph."
```

Rules:

- **Short name** (`TAG.ideology`): icon + abbreviation in parentheses + dash + English party name.
- **Icon** (`TAG.ideology_icon`): icon reference only, no extra text.
- **Description** (`TAG.ideology_desc`):
  - Opens with the dominant ideology group in parentheses (e.g., `(Classic Liberalism)`), then the full English party name, then native-language names in parentheses listed as `Language: Native Name`, comma-separated, followed by the abbreviation.
  - A `\n\n` separates the header line from the body paragraph.
  - Body paragraph: 2–5 sentences covering founding, political orientation, notable history, and international alignments. Written in third person, past/present mix, encyclopedic tone.
  - Do not pad with vague filler sentences.

Example:

```plaintext
MOR.conservatism: "£MOR_NRI (RNI) - National Rally of Independents"
MOR.conservatism_icon: "£MOR_NRI"
MOR.conservatism_desc: "(Classic Liberalism) - National Rally of Independents (Arabic: Altajamue Alwataniu Lil'ahrar, French: Rassemblement National des Indépendants, Standard Moroccan Tamazight: Agraw Anamur y Insimann, RNI)\n\nFounded in 1978 by Prime Minister Ahmed Osman, the party has consistently remained a major player in Moroccan politics. Nominally social-democratic, it is widely regarded as pro-business and liberal, and cooperates closely with parties of a liberal orientation. It holds observer status in the Liberal International and is affiliated with the Africa Liberal Network and the European People's Party."
```

## Event Localisation

- `ID.t`: Short, punchy title — no more than 6–8 words.
- `ID.d`: 1–3 sentences of flavour or context. No mechanical descriptions (those belong in option text or tooltips).
- `ID.a`, `ID.b`, …: Option names should read as a player decision or action, not a description (e.g., `"Provide funding"` not `"The government provides funding"`).

## Ideas & Focuses

- Name (`name: "..."`) should be title-cased, concise (3–6 words typical).
- Description should explain what the idea represents in 1–3 sentences. Do not repeat modifier values verbatim; describe their political or economic meaning.

## YAML Validity

HOI4 localisation files are checked by `check-yaml` in the pre-commit hook. The HOI4 format is not strict YAML, so several patterns cause parse failures:

- **Embedded double quotes**: `"He called it "important""` is invalid. Use `\"important\"` for emphasis, or rephrase to remove the inner quotes entirely.
- **Mixed indentation**: All keys in a file must be consistently indented (all with 1 leading space, or all without). Mixing indented and non-indented keys in the same file causes YAML to see two separate mappings. Remove stray spaces to make indentation uniform.
- **Colons in values**: A bare colon followed by a space inside a quoted string can confuse some parsers — wrap the value in quotes as usual and this is safe, but watch for unquoted values.

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

## Recurring Typo Watchlist

These typos appear frequently across country files — check for them when reviewing:

| Typo                                                        | Correct                   |
| ----------------------------------------------------------- | ------------------------- |
| `Estabilish` / `estabilish`                                 | `Establish` / `establish` |
| `innvoations`                                               | `innovations`             |
| `irreperable` / `irrepairable`                              | `irreparable`             |
| `unenmployed`                                               | `unemployed`              |
| `existance`                                                 | `existence`               |
| `effectivness`                                              | `effectiveness`           |
| `disproportinate`                                           | `disproportionate`        |
| `tarditions`                                                | `traditions`              |
| `contrats` (used as contrast)                               | `by contrast`             |
| `Airforce`                                                  | `Air Force`               |
| `miltiary`                                                  | `military`                |
| `coaltion`                                                  | `coalition`               |
| `tumultous`                                                 | `tumultuous`              |
| `recgonized`                                                | `recognized`              |
| `Propgramme`                                                | `Programme`               |
| `poeple`                                                    | `people`                  |
| `it's` (possessive)                                         | `its`                     |
| `Unloyal`                                                   | `Disloyal`                |
| `Isreal`                                                    | `Israel`                  |
| `unrepairable`                                              | `irreparable`             |
| `bocme`                                                     | `become`                  |
| `hovewer`                                                   | `however`                 |
| `acomplish`                                                 | `accomplish`              |
| `Endevours`                                                 | `Endeavours`              |
| `Quiantified`                                               | `Quantified`              |
| `convering`                                                 | `converting`              |
| `encomapassing`                                             | `encompassing`            |
| `fundamnetals`                                              | `fundamentals`            |
| `civillian`                                                 | `civilian`                |
| `civillisation` / `civilisation` (American English context) | `civilization`            |
| `suprised`                                                  | `surprised`               |
| `alledged`                                                  | `alleged`                 |
| `succesful` / `succesfull`                                  | `successful`              |
| `huminliating`                                              | `humiliating`             |
| `reffered`                                                  | `referred`                |
| `stronly`                                                   | `strongly`                |
| `togeather`                                                 | `together`                |
| `disasterous`                                               | `disastrous`              |
| `religous`                                                  | `religious`               |
| `suzerainity`                                               | `suzerainty`              |
