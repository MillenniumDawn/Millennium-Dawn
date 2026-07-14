# Content Guidelines

On-demand quality checklist for new Millennium Dawn content. Condensed from `docs/src/content/resources/content-review-guide.md` and `docs/src/content/resources/new-general-guidelines.md`.

## Economic

- All buildings in effects need monetary cost — use scripted effects, not raw `add_building_construction`
- Building slots are included in the scripted effect cost; adjust if intentionally omitting
- Trade opinion alone is shallow — always pair with a supplementary effect
- Budget law changes alone are filler — add supporting effects
- Country trees must meet or exceed the generic-tree focus count (currently ~114); a thinner tree feels worse than the generic fallback. Count what the generic tree provides before merging a new country.
- Starting factories are set to match IRL GDP PPP and must not be changed

## Political

- Parties founded after Jan 1, 2000 must be hidden until created through events/triggers
- At least 2 traits per leader, at least 1 with an effect/modifier
- Content must be politically neutral and objective
- All parties need descriptions and icons
- Cross-nation permanent effects should come from events (give target player agency)
- No free cores — require 80% compliance or an integration mechanic
- Aim for 10-15 flavour events per country

## Visual

- Every focus needs an icon and `search_filters`
- Decision `icon =` accepts the bare sprite stem; the engine auto-prepends `GFX_decision_` (so `icon = generic_political_discourse` == `icon = GFX_decision_generic_political_discourse`). Don't add the prefix to a working bare icon. See `decision-reference.md` → Icon Field.
- Use tooltips for event outcomes triggered from focuses
- Max 1 meme GFX per content set
- No unlocalised strings; focus descriptions must not be blank or reuse the focus name
- Starting national spirits must have descriptions (if negative/removable, explain how)

## AI

- Create game rules for AI customisation
- Add AI logic to focus trees to prevent self-destructive choices
- Do not use `add_ai_strategy` in effects (harmful to AI performance)
- All events targeting another nation need AI weighting based on opinion/influence
- AI must be able to interact with any custom GUIs

## Code

- All effects must be logged
- All focuses must have `ai_will_do`
- No empty trigger blocks (`allowed`, `available`, `cancel`, `bypass`)
- Use `relative_position_id` in all focus trees
- Tags must be capitalised in script IDs (e.g., `SPR_focus_name_here`)
- High-cost focuses must have a `factor = 0` modifier in `ai_will_do` when `has_active_mission = bankruptcy_incoming_collapse`. "High-cost" thresholds: `cost ≥ 8` for any focus, or `cost ≥ 5` if the focus has military / economy / research `search_filters`. **Why:** focuses at or above these costs commit enough treasury that an AI in active collapse digs deeper into debt; the lower threshold for econ/mil/research reflects that those focuses typically chain large monetary effects. The guard skips the AI without locking the player out.

## Balance & Tradeoffs

- No parallel path, idea, or event option should be objectively weaker than its alternative in every dimension.
- Every choice must have a distinct advantage and a distinct drawback.
- If an option is strictly dominated, buff the weaker path or remove it.
- Currency and alliance transitions should never feel like a downgrade to the player.

### Worked example: a lateral choice done well

A real pair from the codebase: the CFA franc continuation idea (`cfa_franc_2`) offers peak political power (+0.25) and construction speed (+0.25) at the cost of a heavy tax penalty (−0.10). The ECO transition idea (`the_eco`) trades some peak performance for stability (+0.05), lower consumer goods (−0.03), and a positive tax modifier (+0.05). Neither is strictly better; each supports a different playstyle. **Use this as the test:** if a player could pick the same option every campaign without trade-off, the pair is not yet a real choice.

## Variety & Anti-Formulaic Content

Reward _shape_ diversity, distinct from balance — a tree can be balanced and still formulaic (every focus a same-shaped stat bump). This is the dimension the balance checks miss. Cross-check a new or modernized tree against a reference tree known for variety (Iran `05_iran.txt`, Spain `05_spain.txt`) rather than judging it alone. Full checklist + Iran/Spain/Balkan worked comparison: `docs/src/content/resources/content-review-guide.md` → Variety Guidelines.

- A variable / dynamic-modifier bump is fine at any frequency **as seasoning** on a substantive reward — formulaic only when it _is_ the whole `completion_reward`. Flag focuses whose reward is only `log` + `custom_effect_tooltip` + `add_to_variable`(s); if >~20% of the tree is bump-only, it's too thin. (Iran layers an economy bump into 61% of focuses and never feels formulaic; Spain uses the shape 0 times.)
- No `completion_reward` or `ai_will_do` block should repeat verbatim more than ~3 times — the same `variable = number` line 10+ times with only the name changed is copy-paste, not design.
- Every `mutually_exclusive` fork must differ in reward **kind**, not just magnitude. Sibling A +0.02 / sibling B +0.01 of the same variable is a fake choice; real forks trade a building for a resource, an idea swap for an event.
- At least 4 distinct reward categories across the tree — dynamic modifier, timed idea + `swap_ideas`, treasury/expenditure, building/resource spawn, interest-group opinion, event-with-choice, country flag / bespoke mechanic, decision-category unlock, army/tech unlock. Only 2-3 = formulaic regardless of size.
- At least one bespoke mechanic / idea family the tree alone owns (its national identity). "Increment the shared economy modifier" is not an identity.
- Capstone / terminal focuses deliver a **new** reward kind (unlock a decision category, release a subject, fire a defining event), not a bigger number of a variable the branch already used.
- Political forks differ mechanically (own ideas / mechanics / events), not just which popularity ticks up. `generic`-named political focus IDs are a red flag for the shared minor-nation scaffold.
- Event tie-in density ~1 per 8 focuses for narrative trees; exempt deliberately-lean utility trees (recognition, independence).

## Miscellaneous

- Do not add nations to the bookmarks screen — bookmarks are added post-merge by leads
- Changelog entry required before submitting for review — add to `Changelog.txt`
- Cosmetic tags must be dropped when no longer applicable (e.g., an empire tag lost on regime change)
- New tags (new countries) require all of: OOB, name lists, political structuring, starting laws, starting leader
- For name list authoring conventions (division groups, ship hull names, ship class names, naval prefixes), see `docs/src/content/resources/unit-name-lists.md` and `.claude/docs/namelist-reference.md`

## Generals & Admirals

- General count: `ROUND(units / 15) + 1 + IsMajor + IsInFaction + IsNATO`
- Field Marshal count: `ROUND(generals / 3)`
- Admiral count: `ROUND(ships / 15)`
- Skill levels by region:
  - 1-2: Civil war factions
  - 2-3: Africa
  - 3-4: Middle East and Asia
  - 4-5: Eastern Europe, South America
  - 5-6: Western countries
- Skill points = `(level - 1) * 3 + 4`
- Portrait sizes: large 156x210, small 38x51
- Always include Army/Navy/Air Chiefs (Air Chief required even without an air force)

For the full review guide, see `docs/src/content/resources/content-review-guide.md`.
For general/admiral creation details, see `docs/src/content/resources/new-general-guidelines.md`.
