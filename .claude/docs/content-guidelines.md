# Content Guidelines

On-demand quality checklist for new Millennium Dawn content. Condensed from `docs/src/content/resources/content-review-guide.md` and `docs/src/content/resources/new-general-guidelines.md`.

## Economic

- All buildings in effects need monetary cost — use scripted effects, not raw `add_building_construction`
- Building slots are included in the scripted effect cost; adjust if intentionally omitting
- Trade opinion alone is shallow — always pair with a supplementary effect
- Budget law changes alone are filler — add supporting effects
- Tree must meet or exceed the generic tree baseline (114 focuses)
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
