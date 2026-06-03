Run the full Millennium Dawn content review checklist against a file or the current branch diff.

**Syntax:** `/content-review [file_path]`

- With `file_path`: review that specific file against all content guidelines.
- Without argument: review all changed files on the current branch against `main`.

The authoritative checklist lives in `docs/src/content/resources/content-review-guide.md` and `docs/src/content/resources/new-general-guidelines.md`. Read both before starting if not yet read this session. The condensed `.claude/docs/content-guidelines.md` is a quick summary but not exhaustive; always defer to the full docs.

## Execution

### 1. Gather context

**File mode** (path provided):

- Read the file and identify its type (focus tree, events, characters/generals, OOB, decisions, etc.).
- Read `docs/src/content/resources/content-review-guide.md`, `docs/src/content/resources/new-general-guidelines.md`, and `.claude/docs/content-guidelines.md`.

**Branch mode** (no argument):

- Run `git diff origin/main...HEAD` and `git log origin/main..HEAD --oneline`.
- Identify the changed files and their types.
- Read `docs/src/content/resources/content-review-guide.md`, `docs/src/content/resources/new-general-guidelines.md`, and `.claude/docs/content-guidelines.md`.

### 2. Apply the checklist

For each file in scope, check the categories below. Skip categories that don't apply to the file type (no admiral counts in a decisions file, no building costs in a character file).

#### Economic

- Buildings added without a monetary cost — use the scripted effects from the Code Resource, not raw `add_building_construction`
- Building slot included in the scripted effect but intentionally omitted — check whether the building cost was reduced to compensate
- Trade opinion effects with no supplementary effect — trade opinion alone is a shallow filler effect
- Budget law changes with no supporting effects — budget changes alone are filler; something unique must accompany them
- Full focus tree provides fewer economic benefits than the generic tree baseline (114 focuses)
- Starting factory counts changed — these are fixed to IRL GDP PPP and must not be altered

#### Political

- Parties founded after January 1, 2000 visible at game start without a trigger or event gating their creation
- Leaders with fewer than 2 traits, or all traits lacking any effect or modifier
- Content that is politically biased or takes a non-neutral stance
- Political parties missing descriptions or icons
- Focus tree paths that are linear with no meaningful player choices (railroaded)
- Permanent cross-nation effects applied directly in a focus or decision rather than through an event (target player must have agency)
- Cores added without a mechanic — no free cores; require 80% compliance or an integration system
- Full country content set has fewer than 10 flavour events

#### Visual

- Focuses missing icons
- Focuses missing `search_filters`
- Focuses that fire events without tooltips showing potential outcomes
- More than one meme GFX (wojak, trollface, etc.) in the content set
- Unlocalised strings; focus descriptions blank or reusing the focus name verbatim
- Starting national spirits without descriptions; removable spirits that don't explain how to remove them
- Custom focus icons used on most or all focuses — reserve for major focuses (key decisions, party choices, etc.)

#### Military (character/OOB files)

Count formulas, skill levels by region, and skill point calculations are in `.claude/docs/content-guidelines.md` under "Generals & Admirals". Read that section first. Check:

- General, Field Marshal, and Admiral counts outside the formula range (exceptions allowed for famous commanders)
- Skill levels outside the expected region range without justification
- Total skill points not matching `(level - 1) * 3 + 4`
- Air Chief missing (required even if the country has no air force)
- Portrait sizes wrong: large must be 156×210 px, small must be 38×51 px
- Advisor entries missing `original_tag` in `allowed` (must not use `tag` — breaks during civil wars)

#### AI

- `add_ai_strategy` used inside effects — harmful to AI performance; consult the AI team
- Events targeting another nation with no AI weighting on the acceptance/rejection chance (e.g., acceptance should scale with opinion, not be random or fixed)
- Custom GUIs or mechanics with no AI interaction or game rules for AI customisation
- Focuses missing `ai_will_do` — every focus must have one
- No game rules created for AI customisation in a full country content set

#### Code

- Effects without a log entry — all effects must be logged for debugging
- Empty trigger blocks (`allowed`, `available`, `cancel`, `bypass`) — delete them; they are bloat
- Focus tree not using `relative_position_id` — required for all focus trees
- Tag references not capitalised in script IDs (e.g., `spr_focus` instead of `SPR_focus`)

#### Miscellaneous

- Nation added to the bookmarks screen — do not; bookmarks are added post-merge by leads
- Cosmetic tags not dropped when no longer applicable (e.g., a nation gains an empire tag but never drops it on regime change)
- New tags (new countries) missing any of: OOB, name lists, political structuring, starting laws, starting leader
- No changelog entry added for the content — developers must document their additions in `Changelog.txt`

### 3. Output

For each file reviewed, report:

1. **File**: path and file type.
2. **Issues**: numbered list with category labels (`[Economic]`, `[Political]`, `[Visual]`, `[Military]`, `[AI]`, `[Code]`, `[Misc]`) and line numbers where applicable.
3. Mark anything that must be fixed before merge as **[blocker]**.

End with a total issue count per category, or "No content issues found."
