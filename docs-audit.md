# Docs Content Audit — Action Tracker

Generated 2026-06-15 against `main` @ `f91be9d36c`. Working note from a doc-site audit. Items split into two groups: **Flagged** (need a maintainer call before acting) and **Reference** (already checked or back-burner).

The audit also surfaced a set of small, factual fixes (typos, wrong filenames, wrong scripted-effect cost claims, GitHub-emoji shortcodes, etc.) that the user has parked for a separate pass; see "Reference — parked fixes" below. Run any time the docs site is touched.

## Flagged — needs a maintainer decision

### F1. Changelog-guide "Event Reference" link

- **Where:** `docs/src/content/resources/changelog-guide.md:108`
- **Evidence:** the line reads `[Event Reference](/dev-resources/new-general-guidelines/) — event conventions`. The link target is the _New General Guidelines_ page, not an event reference. No `event-reference` page exists on the public site. The actual event reference is `.claude/docs/event-reference.md` (private to the repo, not published).
- **Question:** what's the intent?
  - (a) **Fix the label** to "New General Guidelines" (cheapest, current target).
  - (b) **Create** a new public `event-reference.md` page that mirrors `.claude/docs/event-reference.md`.
  - (c) **Drop** the line entirely.
- **Default if no answer:** (a). It costs one line edit and matches what the link already does.
- **Owner:** docs maintainer.

### F2. `united-states.md` country guide — fabricated content

- **Where:** `docs/src/content/countries/united-states.md:1-65`
- **Evidence:** the page lists 10 "unique national spirits" with names that don't exist in the codebase. Actual US start-of-game `add_ideas` in `history/countries/USA - USA.txt:2794-2860` use a different set (`land_of_the_free`, `political_establishment`, `congress_authority`, `american_militarism`, `us_war_on_drugs`, `us_mass_media_problems`, `heavy_additional_consumption_spirit`, `petro_dollar`, `heavily_regulated_immigration`, `nuclear_power_off`, `full_first_use`, plus the standard mod-flavour ideas). The popularity numbers in the page also don't match the per-subideology `party_pop_array`.
- **Question:** is the page meant to list _only the US-signature_ spirits (in which case the names are wrong) or _all_ ideas at game start (in which case the list is too short)? Either way, the existing text is not in a state to ship.
- **Default if no answer:** **do not regenerate by AI.** A correct rewrite needs gameplay judgement (compare the 268-line `italy.md` for the target shape) and an actual US-content maintainer.
- **Owner:** US content team.
- **Related:** ~25 of 68 country docs are WIP stubs (see F5 below); US is the highest-traffic non-WIP that's still wrong.

### F3. Dev diary #52 — placeholder in the build

- **Where:** `docs/src/content/devDiaries/052-special-projects-performances-raids-missiles.mdx:1-13`
- **Evidence:** `frontmatter author: Template`, body says "Use this section for...". The page renders in `dist/` and shows up in the dev-diaries archive. There is no clean glob-exclude convention in `docs/src/content.config.ts` (collections glob `**/*.md` and `**/*.{md,mdx}` without exclude support).
- **Question:** keep as a contributor template or remove entirely?
  - (a) **Move** to `docs/templates/dev-diary-template.mdx` (outside `src/content/`, so out of the build but still discoverable).
  - (b) **Delete** the file.
- **Default if no answer:** (a). Move is reversible; delete is not.
- **Owner:** docs maintainer.

### F4. AI guard convention — cross-doc inconsistency

- **Where:**
  - `AGENTS.md:54` — high-cost focus guard lives in `available` as `NOT = { has_active_mission = bankruptcy_incoming_collapse }`.
  - `.claude/agents/focus-tree-builder.md:58-63` and `.claude/docs/*` — same guard lives in `ai_will_do` as `modifier = { factor = 0 has_active_mission = bankruptcy_incoming_collapse }`.
  - `docs/src/content/resources/content-review-guide.md:159-160` and `docs/src/content/resources/search-filters.md:67, 161, 172` — follow the `.claude/` / agent version (in `ai_will_do`).
- **Evidence:** the AI guard for high-cost focuses is described two different ways across the repo's own docs. The two placements behave differently: in `available` it locks the player out of the focus; in `ai_will_do factor = 0` it only stops the AI.
- **Question:** which is canonical?
  - (a) **Player lockout** — `NOT = { has_active_mission = bankruptcy_incoming_collapse }` in `available`. Stricter; protects AI from making bad decisions but also stops the player. Matches `AGENTS.md`.
  - (b) **AI-only guard** — `modifier = { factor = 0 has_active_mission = bankruptcy_incoming_collapse }` in `ai_will_do`. Looser; only stops the AI. Matches `.claude/`, the focus-tree-builder agent, and the public docs site.
- **Default if no answer:** (b). The agent, the in-repo `.claude/`, and the public docs all agree on it, and the in-repo focus tree examples that I sampled use this pattern. Picking (a) would mean rewriting a lot of content and potentially changing in-game behaviour. But this is a policy call: the user can override.
- **Owner:** maintainer (project-policy decision, not a docs call).

### F5. WIP country docs — UX call

- **Where:** `docs/src/content/countries/*.md` — 25 of 68 country docs are WIP stubs (Bosnia, Bulgaria, Cuba, Czechia, Egypt, Estonia, Fiji, Gagauzia, India, Indonesia, Iraq, Kazakhstan, Kosovo, Kyrgyzstan, Libya, Netherlands, San Marino, Serbia, Singapore, South Ossetia, Tajikistan, Transnistria, Turkey, Uzbekistan, Venezuela, plus Artsakh, Belarus, Abkhazia, Gulf Tree, Hezbollah).
- **Evidence:** infobox `Content: WIP` is set, body is `WIP\n\n## Overview\n\nWIP`. The `/countries/` grid card on `docs/src/pages/countries/index.astro` doesn't surface the WIP status — players click through to a 30-line page that says nothing.
- **Question:** how should the public grid handle stubs?
  - (a) **Hide WIP entries from the grid** entirely. Players don't see countries with no content.
  - (b) **Render the WIP badge** on the grid card so the player knows before clicking. (The badge is already in the infobox; the grid just doesn't display it.)
  - (c) **Status quo.** Continue to ship empty pages.
- **Default if no answer:** (b). Lowest-cost, keeps discoverability, honest about content state. Implementation: thread `infobox[].stats[].value === "WIP"` through to the grid card and visually mute it.
- **Owner:** docs maintainer + country content team (long term, write the missing pages).

### F6. Em-dash and AI-tell sweep — editorial policy

- **Where:** ~30 prose files under `docs/src/content/` (full list in "Reference — AI-voice audit" below).
- **Evidence:** 100+ em-dashes; 5 `on top of` constructions; specific banned words (`robust`, `on top of`, `seamless`, etc.); 8+ American-spelling misses in general prose (`customise`, `armour`, `flavour`). Dev-diaries (#52, #53, #54, #55, #56, #57) are human-authored and exempt.
- **Question:** enforce the policy the changelog-guide already states ("Does it contain no em dashes?") across all contributor-written docs, or leave it as a changelog-only rule?
  - (a) **Enforce** via the linter / pre-commit (a `markdownlint` rule or `markdownlint-cli2` custom rule). Catches regressions; one-time cost to bring existing files in line.
  - (b) **Document only** in `CONTRIBUTING.md` and the dev-diary template. Manual enforcement; no automated gate.
- **Default if no answer:** (a) for em-dashes (the existing rule is already a one-liner to add to `.markdownlint-cli2.jsonc`); (b) for the broader AI-tell list (customise/armour/flavour), which is a stylistic judgement and hard to lint.
- **Owner:** docs maintainer.

## Reference — verified clean

Spot-checks against the live repo at HEAD came back clean. No action needed.

- `docs/src/content/resources/code-resource.md:544-552` — Party Popularity examples match the new `add_relative_party_popularity` default-to-ruling-party behaviour (post #1876 / #1878).
- `docs/src/content/resources/code-stylization-guide.md:187` — same; example is correct under the new default.
- `docs/src/content/countries/italy.md` — spot-checked against `history/countries/ITA - Italy.txt` and `common/national_focus/05_italy.txt`. Spirit count (19), popularity numbers (34.5% / 18.9% / 15.8%), focus IDs (`ITA_what_we_are`, `ITA_diplomatic_focus`, `ITA_strenghten_ties_with_west`, `ITA_abandon_the_west`), `italy_md.69` threshold (`stability_protests_counter < -15`), and `ITA_nuclear_power_banned` all check out.
- `docs/src/content/resources/add-eu-nation.md` — claims about `EU_is_potential` (`common/scripted_triggers/99_EU_scripted_triggers.txt:651`) and `on_startup_euu_action` array (`common/scripted_effects/99_eu_scripted_effects.txt:745, 896+`) are accurate.
- `docs/src/content/**` — no remaining `set_party_index_to_ruling_party` references. Verified with `grep -rn "set_party_index_to_ruling_party" docs/src/content/` (zero matches).
- 47 image references across `docs/src/content/**` all resolve to existing files under `docs/src/assets/images/`.
- `astro check` — 0 errors, 0 warnings, 0 hints across 150 files.
- `docs/.../lint:md` — 0 errors across 144 files.
- `docs/.../check_docs_hygiene.py` — passed.
- `docs/.../check_flag_images.py` — passed.

## Reference — parked fixes

Concrete bugs and small fixes the user has parked for a separate pass. Each is a one-line-to-30-line edit, all mechanical.

| File                                                                                                                       | Fix                                                                                                                                                                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/src/content/resources/add-eu-nation.md:5`                                                                            | Drop duplicate body H1. CI (`check_content_html.py`) is currently red on this.                                                                                                                                                                     |
| `docs/src/content/resources/code-stylization-guide.md:155-158`                                                             | `ai_will_do = { factor = 10 }` → `base = 10`. Project rule is `base = N` (per `AGENTS.md` and `.claude/agents/focus-tree-builder.md`).                                                                                                             |
| `docs/src/content/resources/code-resource.md:386-388`                                                                      | Drop the wrong "$6.50 without a building slot" claim. The scripted effect (`common/scripted_effects/00_scripted_effects.txt:223-237`) always charges $7.50 with the slot included.                                                                 |
| `docs/src/content/resources/error-debug-codes.md:21-26, 95`                                                                | Source filenames `00_money_scripted_guis.txt` don't exist. Real file is `00_MD_economyview_scripted_guis.txt` (e.g. lines 81, 96, 168, 827 contain the codes the doc lists). Drop the generic Common Errors table — it has no HOI4-specific value. |
| `docs/src/content/tutorials/troubleshooting-guide.md:17`                                                                   | "more stable then DX11" → "than".                                                                                                                                                                                                                  |
| `docs/src/content/tutorials/troubleshooting-guide.md:45`                                                                   | Replace GitHub-specific `:repeat:` / `:white_check_mark:` / `:x:` with literal emoji.                                                                                                                                                              |
| `docs/src/content/resources/ai-modding-guide.md:319`                                                                       | Drop off-topic external links (Ollama, HOI4 wiki) from "Related Resources".                                                                                                                                                                        |
| `docs/src/content/changelogSections/v1-12-0-every-tank-an-upgrade-hotfixes.md:4`                                           | Bump `order: 13` → `14` for stable sort.                                                                                                                                                                                                           |
| `docs/src/content/tutorials/formable-nations.md:6`                                                                         | Drop "robust" (banned word).                                                                                                                                                                                                                       |
| `docs/src/content/resources/search-filters.md:172`, `resources/git-workflow.md:158`, `tutorials/economy-guide.md:467, 930` | Replace "on top of" with neutral phrasing.                                                                                                                                                                                                         |
| `docs/src/content/tutorials/military-tutorial.md:1-6`                                                                      | Body is just `WIP`. Linked from `space-systems-guide.md:391`. Either stub the page or remove the link.                                                                                                                                             |
| `docs/src/content/countries/countries.md:51`                                                                               | Decide whether the inline "Unique Focus Trees" table is canonical or a derivative of per-country `unique_focus_tree` frontmatter. If the latter, drop the table and the markdownlint-disable comment.                                              |
| `docs/src/content/resources/developer-setup.md`                                                                            | Heavy overlap with `CONTRIBUTING.md` and `resources/contributing.md` (Fork Workflow, Setup, Pre-commit, Tooling, VS Code). Pick one canonical; the other two should defer.                                                                         |
| `docs/src/content/resources/new-general-guidelines.md:113`                                                                 | Line "ai_will_do_factor = add to all entries, can just use factor = 1 in all" is leftover HOI4 advisor style, not focus/decision. Either drop or label it "advisor-specific".                                                                      |
| `docs/src/content/resources/ai-modding-guide.md:130-148`                                                                   | Two near-identical JSON config examples (Continue and Cline). Collapse to one with a pointer.                                                                                                                                                      |
| `docs/src/content/changelogSections/v1-{8,9,10,11,12}-*.md`                                                                | File name says "v1-N-0-..." but content rolls up the whole minor (e.g. v1-10-0-... covers v1.10.0 through v1.10.5). Rename or split per patch.                                                                                                     |
| `docs/src/content/tutorials/international-systems.md`                                                                      | 697 lines covering 7 systems; clean split: pull Cyberwarfare and PMCs into their own pages.                                                                                                                                                        |
| `docs/src/content/resources/code-resource.md`                                                                              | 837 lines; modifiers catalog (lines ~71-340) and scripted-effects how-to (lines ~340-820) could split, but cross-references are dense.                                                                                                             |
| Internal links missing trailing slash                                                                                      | Most `/dev-resources/*`, `/player-tutorials/*`, etc. links lack the trailing slash. Astro `dist/` emits both forms, so they resolve, but the inconsistency is brittle. Standardise on trailing-slash.                                              |

## Reference — AI-voice audit

Em-dash count per prose file (top offenders, descending). Dev-diaries are human-authored and exempt.

- `docs/src/content/tutorials/investments-guide.md` — 24
- `docs/src/content/tutorials/economy-guide.md` — 24
- `docs/src/content/resources/git-workflow.md` — 15
- `docs/src/content/resources/changelog-guide.md` — 15
- `docs/src/content/tutorials/internal-factions.md` — 14
- `docs/src/content/resources/developer-setup.md` — 14
- `docs/src/content/resources/ai-modding-guide.md` — 11
- `docs/src/content/resources/code-stylization-guide.md` — lines 3, 18, 22, 39, 129, 145, 190, 315-318
- `docs/src/content/resources/code-resource.md` — line 3, 730, 750, etc.

Specific banned-word hits (per the user's voice rules in `AGENTS.md`):

- `docs/src/content/tutorials/formable-nations.md:6` — "**robust** formable nations system".
- `docs/src/content/resources/search-filters.md:172` — "on top of" construction.
- `docs/src/content/resources/git-workflow.md:158` — "on top of".
- `docs/src/content/tutorials/economy-guide.md:467, 930` — "on top of" (twice).
- `docs/src/content/resources/content-review-guide.md:142` — "customise" (British). Should be "customize" in general prose.
- `docs/src/content/resources/unit-name-lists.md:49-54, 95, 229, 248-250` — `armour` / `Armoured`. In-game proper nouns (`change_labour_unions_opinion`, "Labour Unions") stay as-is.
- `docs/src/content/resources/unit-name-lists.md:6, 95, 229` and `resources/content-review-guide.md:79, 96-97, 128, 142` — `flavour`. Lean American: `flavor`.

## Reference — duplication map

- `CONTRIBUTING.md` ↔ `docs/src/content/resources/developer-setup.md` ↔ `docs/src/content/resources/contributing.md` — three sources of truth for the contributor workflow. Pick one canonical, defer the others.
- `docs/src/content/countries/countries.md:51` table ↔ per-country `unique_focus_tree` frontmatter — two sources of truth for "who has a unique tree". The grid renders from per-country frontmatter; the table is a static list.
- `docs/src/content/pages/countries.md:5` table ↔ `docs/src/pages/countries/index.astro:11-` grid cards — same point, different render path.
- `docs/src/content/changelogSections/v1-12-0-every-tank-an-upgrade.md` ↔ `v1-12-0-every-tank-an-upgrade-hotfixes.md` — both `order: 13`, both contain overlapping v1.12.0 entries. The hotfixes page is `hidden: true` (not in the index), so the overlap is only visible via cross-links.

## Completed

- **F1**: changelog-guide "Event Reference" link label fixed. Commit `a5ea72179b`.
- **F3**: Dev diary #52 moved to `docs/templates/dev-diary-template.mdx`, removed from archive. Commit `7e7a428b79`.
- **F5**: WIP badge rendered on country grid card for 34 stubs. Commit `51f656ff63`.
- **F6**: Em-dash lint rule added (MD9999), 121 mechanical violations fixed. The rule is now blocking (the no-op `severity: warning` was removed) and code-aware (skips fenced and inline code); `bun run lint:md` reports 0 violations. Commits `20cedb32fa`, `5778317b43`, `4523839ebd`.
- **Bug Bot ToS**: new page, footer nav, cross-links. Commit `cbdacee2d7`.
- **`.claude/docs/`**: aligned with PRs #1876/#1878. Commit `06f19454cb`.
- **Parked fixes**: 13 mechanical fixes (duplicate H1, factor/base, building cost, error filenames, typos, emoji shortcodes, external links, sort order, banned word, "on top of", advisor line, military stub). Commit `897ad3cf64`.
- **Contributor docs unification**: `developer-setup.md` = main SoT, `contributing.md` = docs/bun guide, `CONTRIBUTING.md` = slim pointer. Commit `20cedb32fa`.
- **Trailing-slash sweep**: 28 files, all internal links standardised. Commit `2b317d1ba3`.
- **ai-modding-guide JSON collapse**: two near-identical VS Code config examples merged. Commit `2b317d1ba3`.
- **Changelog renames**: `v1-10-0-...` → `v1-10-...`, `v1-11-0-...` → `v1-11-...`, `v1-12-0-...` → `v1-12-...`. Redirect pages for old URLs. Commit `8dae0ef95f`.
- **Page splits**: international-systems (485 → ~300 lines, Cyberwarfare and PMCs extracted); code-resource (837 → ~344 lines, scripted-effects reference extracted). Commit `8dae0ef95f`.
- **Unified check script**: consolidated into `tools/docs_checks/` (shared `common.py`, single `check_docs.py` entry); all docs checks now share one package. package.json, `docs-quality.yml`, and pre-commit point there.
- **Link-corruption fix**: the trailing-slash sweep (`2b317d1ba3`) replaced the closing `)` of 95 internal links with `/`, breaking them. All 95 repaired. New `check_link_syntax.py` (CI + pre-commit) guards against it recurring.

## Remaining

- **F2**: `united-states.md` — 10 wrong spirit names, needs US content maintainer.
- **F4**: AI guard `factor = 0` vs `NOT = { ... }` convention divergence. Needs project policy call.
- **Country em-dashes**: countries and dev-diaries are exempt from MD9999. Track separately.
