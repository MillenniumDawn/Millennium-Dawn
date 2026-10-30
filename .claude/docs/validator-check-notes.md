# Validator Check Notes

What each validator enforces where the reason is not obvious from its code: engine
behavior, exemptions, and known gaps. Search for the script or category name. Do not
read this file whole. Wiring and strictness are in `validator_batches.py`, and open
backlogs live in GitHub issues, not here. Pipeline rules:
[Validation Pipeline](validation-pipeline.md).

## Encoding and loc format

- `fix_loc_yaml.py` fixes on commit. `validate_localisation.py` reuses its checks and
  reports YAML errors in the localisation results, including for contributors without
  hooks. `validate_localization_encoding.py`,
  `validate_mod_encoding.py`, and `validate_txt_encoding.py` run in CI for the same reason.
- `validate_txt_encoding.py` scans shipped `.txt` roots only. Script `.txt` must not
  carry a BOM.
- `validate_defines.py` reads the live install on commit and `vanilla_defines.txt` in CI.

## validate_ai_path_rules.py

- `ai-path-rule-missing`, `ai-path-rule-incomplete` (WARNING): a focus tree whose
  `country` block names exactly one tag that owns a state at start needs a
  `TAG_ai_behavior` rule with a `HISTORICAL` option and a `default` block.
- Out of scope: shared trees, and tags that only spawn later.

## validate_ai_weight_order.py

- Checks event `ai_chance`, decision/GUI `ai_will_do`, and diplomatic `ai_desire`
  through the same scanner. The existing common/events CI batch covers all three.
- `ai-weight-zero-then-add` (WARNING): modifiers run in order, so a positive `add`
  can restore a zeroed weight. Opposite boolean guards in the same scope cannot
  both apply. Other relationships, including numeric bounds and flag values,
  remain unknown and need review.

## validate_building_guards.py

- `damage_building` or `remove_building` against a building the state lacks spams
  `error.log`. The guard must name the same building as the effect's `type`.
- Accepted guards: a count comparison in an enclosing `limit` (also on `random_owned_state`
  and similar, and through `meta_effect` wrappers), `non_damaged_building_level`,
  `any_province_building_level`, `has_building`, `num_of_buildings`, a `random_list`
  bucket zeroed by `modifier = { factor = 0  X < N }`, or an `any_core_state`-style
  pre-selection.
- Not guards: a `limit` on something else (an idea, a flag), and `trigger`, `available`,
  `visible`, `allowed`. `effect_tooltip` subtrees are skipped.

## validate_characters.py

- `trait-role-mismatch` (ERROR): a unit leader trait from the wrong branch (`land`,
  `navy`, `operative`) loads silently and never applies. Only the branch is compared.
  Corps commander traits on field marshals are not a finding, since vanilla does it.
- `undefined-unit-leader-trait` (WARNING). `common/unit_leader` is `replace_path`'d, so
  the mod's files are the whole trait universe.
- Advisor slots: each slot owns a pool file in `common/country_leader/`
  (`01_high_command_traits.txt`, `01_army_chief_traits.txt`, `01_navy_chief_traits.txt`,
  `01_air_chief_traits.txt`). A trait belongs to the pool of its file, not its name
  prefix. New pool: add the file and one `SLOT_POOL_FILES` entry.
- `advisor-trait-slot-mismatch`, `undefined-advisor-trait`, `unit-leader-trait-on-advisor`,
  `advisor-trait-on-unit-leader`, `advisor-pool-file-missing` are ERROR. Chiefs scale
  5/10/15% and high command 4/8/12%, so a crossed assignment is a sprite and tier defect.
- `TAG_`-prefixed traits are exempt from the slot check. Traits outside the four pool
  files are unclassified. `country_leader` blocks are not scanned.

## validate_country_names.py

- `country-names-missing` (ERROR): every tag defined before `dynamic_tags = yes` needs a
  top-level block in `common/names/`, or the game logs an error and uses `default`
  names. Aliases are not checked.

## validate_decisions.py

- `missing-decision-log` (ERROR): a `complete_effect` with effects but no `log =`.
- `undefined-unlock-tooltip-target` (ERROR): `unlock_decision_tooltip` and
  `unlock_decision_category_tooltip` name a definition the engine looks up at render. A
  stale name leaves the tooltip empty while the unlock still happens. The category form
  takes the bare token only.
- `validate_formable_commitment_sync` (ERROR): contract in `formable-reference.md`.
- `decision-cosmetic-targeting` (WARNING): a single explicit country target is a
  candidate for a normal decision with a custom icon. Multiple explicit country
  targets without unquoted `FROM` use need review for target-dependent behavior.
  State/map targeting, script-only `allowed = { always = no }`, target arrays, and
  dynamic country variants are skipped. For multiple targets, an enabled
  `war_with_target_on_*` hint also counts as target use. Comments and quoted text
  such as logs do not count as script use. This is advisory: localisation and called
  scripts may consume `FROM`, and a single-target decision may depend on it too.
  Verify those dependencies and visibility before removing targeting. The check
  neither follows those references nor rewrites decisions or creates icons.
- `validate_random_seed` (ERROR): covers `random_list` and bare `random`. Exempts
  `fire_only_once = yes`. Only an absent `fixed_random_seed` is a finding.
- `missing-decision-localisation` (WARNING): a name key, `name`/`desc` override, or
  `custom_cost_text` that resolves to nothing. `<id>_desc` is not required.
- `ai-only-decision-localisation` (WARNING): a key that exists for an AI-only decision or
  category. AI-only means an unconditional depth-0 `is_ai = yes` in `visible`,
  `available`, or `allowed`, or a category gated that way. `is_ai = yes` nested in `OR`,
  `if`, or a tag scope is conditional. `custom_cost_text` and categories named by
  `unlock_decision_category_tooltip` are exempt.
- `missing-decision-icon` (WARNING, opt-in `--missing-icons`, not in CI): a decision
  `icon = X` passes if `X`, `GFX_decision_X`, or `GFX_X` exists. A category `icon = X`
  takes `GFX_decision_category_` instead. A category `picture` is the full sprite name.
  Needs a live install to avoid vanilla noise. The flag also drives the focus-tree check.
- `unannounced-decision-category` (WARNING, opt-in `--unannounced-categories`, passed in
  CI): a category whose `visible` waits on a flag, focus, idea, or variable, with no
  `unlock_decision_category_tooltip` naming it and no `unlock_decision_tooltip` naming
  one of its decisions. History mentions do not exempt a category.
  `unannounced_category_exempt` in the config records each exception and its reason:
  startup gates, shared state with no single owning-country unlock effect, and balance
  of power categories that have no name key to render.
- `decision-id-case`, `decision-prefix-owner` (WARNING, opt-in `--naming-style`, not in
  CI): the case rule in the stylization guide, and a prefix-owner rule still under
  review. Existing ids are never renamed, so
  the flag stays off until the backlog is reviewed (#6239). The owner is the decision's
  flat `allowed` pin, else its category's. Prefixes that are not country tags are
  skipped. Shared systems often prefix with the subject country (`CHI_jap_*`,
  `SIL_bund_*`), so review the owner rule before enforcing it.
- `decision-icon-slot-mismatch` (ERROR): the decision UI draws icons at native texture
  size, so art for one slot renders wrong in another. Bands by longest edge: decision icon
  up to 36, category icon 48 to 79, picture 80 and up. Sizes in the gaps are not reported.
  `slot_exempt_sprites` in the config are accepted anywhere.
  `tools/assets/resize_decision_icons.py --dry-run` shows the fix: it resizes in place
  when nothing else uses the texture, else writes a resized sibling and repoints. It
  skips vanilla art.
- `decision-icon-unmeasured` (WARNING): an icon whose texture is not on disk, so its
  slot size is unchecked. In CI this means the art lives outside the shipped trees
  (see `validation-pipeline.md`); confirm the size locally.
- `category-desc-image-overlap` (WARNING): a category `<id>_desc` that opens with a
  `£icon` draws the art at native size and can cover the header. Minimum leading `\n`:
  `ceil((height / 2 - 22) / 16)`. Not confirmed pixel for pixel in game.
- `decision-ai-will-do-ignores-cost` (ERROR): the decision twin of
  `event-ai-chance-ignores-cost`, with the same known gaps. A finding behind a treasury
  `custom_cost_trigger` carries a "verify" note, because the engine already stops a
  country that cannot pay. A decision that must stay unguarded, such as a deadline the
  AI cannot miss, needs a reason in `ai_cost_exempt`. An exemption skips the whole
  decision, not one cost, so re-check its reason when the decision gains a new cost.
- `decision-unneeded-treasury-guard` (WARNING): the decision twin of
  `event-unneeded-treasury-guard`, read over the whole decision, with the same gaps.
  `cost` and `ai_hint_pp_cost` are political power prices, a treasury custom cost is
  money, and a money modifier in the `modifier` block commits money.
- AI reach: this check and the AI factor check skip a decision the AI cannot see. That
  is an unconditional `is_ai = no` or `always = no` in the decision's `visible` or
  `available`, or in its category's own `visible`, `available`, or `allowed`. The match
  may sit inside `hidden_trigger` or a tooltip wrapper, as in
  `hidden_trigger = { always = no }`. Under a tag scope, `OR`, `NOT`, `AND`, or `if` it
  is conditional, so the decision stays reachable.
- `decision-custom-cost-not-charged` (WARNING): a `custom_cost_trigger` that checks
  treasury, political power, command power, manpower, or equipment needs a matching
  charge in `complete_effect`. A charge found only in `remove_effect` is reported as
  late; timeout and cancellation payments do not satisfy the check either. All five
  resource kinds follow scripted effects in the choosing country's scope, including
  nested math and equipment transfers. Previews, quoted text, foreign-country writes,
  literal `always = no` branches, and zero-chance random blocks do not count as payment.
  Amounts, equipment types, and dynamic branch coverage are not compared. Other custom
  resource variables and scripted cost triggers still need manual review.
- `decision-days-remove-without-effect` (WARNING): a `days_remove` timer that nothing
  reads. A `remove_effect`, a top-level `modifier` or `targeted_modifier`, or a
  `has_decision` naming the decision anywhere in shipped script exempts it. Repeatable
  decisions that use the timer as a cooldown are reported too; `days_re_enable` is the
  cooldown. Missions are skipped, though some set `days_remove`. Known gap: a
  `has_decision` in the decision's own block also exempts it.
- `decision-money-charged-late` (ERROR): money a non-mission `remove_effect` charges,
  by the cost rules of `decision-ai-will-do-ignores-cost`, directly or through the
  scripted effects it calls. Building payments are not followed, since they are paid on
  delivery: an effect that holds `add_building_construction`, `add_offsite_building`, or
  `skip_payment`, or calls one that does. A treasury custom cost that
  `decision-custom-cost-not-charged` already reports as late is not repeated. An
  outcome rather than a price, such as an annexation inheriting debt or a charge per
  subject converted at the end, needs a reason in `late_charge_exempt`, which also
  skips the whole decision. `timeout_effect` and `cancel_effect` are not read. Known
  gap: a building built in the decision itself and paid through a separate effect still
  counts (Syria's cotton investment is exempt for this).
- `decision-treasury-gate-below-charge` (WARNING): the highest literal `treasury > N` in
  `available` and `custom_cost_trigger` against the literal `treasury_change` charges at
  the top level of `complete_effect`. A scripted trigger's minimum comes from its body,
  not its name. Only `hidden_trigger` and the
  tooltip wrappers are looked through. A gate within 0.1 of the charge, such as `> 1.4`
  for 1.5, is how the mod writes `>=` and passes. Known gaps: the long `var = treasury`
  form, `NOT = { treasury < N }`, a gate inside `OR` or `AND`, and a charge inside an
  `if` or built from a variable.
- `decision-trigger-reads-temp-variable` (WARNING): `custom_cost_trigger`, `available`,
  or `visible` reads a name in a `check_variable` that the decision's effects set only
  with `*_temp_variable`. A name the trigger sets, or that any scripted trigger sets as
  a temp variable, is exempt, since MD triggers such as `calculate_ai_interest` can set
  one. Known gaps: a name set persistently elsewhere in the mod still counts as temp,
  and a value read inside a math block is not seen.
- `decision-duplicate-log` (WARNING): more than one `log` at an effect block's own level,
  reported by the same pass as `decision-log-not-first`.
- Decision staffing guards are not checked. A money guard does not prove that
  the target state can staff a building; scripted building chains need a separate
  target-state analysis.

## validate_dynamic_modifier_guards.py

- `remove_dynamic_modifier` on a scope not carrying the modifier logs an error and does
  nothing. The removal must sit under a `limit` holding `has_dynamic_modifier` for the
  same modifier, at any depth, same-scope or re-entering the target scope.
- A flag, idea, or variable proxy is still a finding. `trigger`, `available`, `visible`,
  and `allowed` are not guards. `has_dynamic_modifier`'s `scope =` is ignored.

## validate_equipment_variants.py

- `equipment-variant-unavailable` (ERROR): an effect sequence creates a named variant
  without an assured enabling technology, then uses it in `add_equipment_production`,
  `create_ship`, or `add_equipment_to_stockpile`. Technologies resolve through
  `enable_equipments`, not by matching ids.
- It follows effect order, direct technology guards, conditional grants, and
  `allow_without_tech = yes`. Country history through the earliest bookmark supplies
  starting technologies only for proven recipients. Tooltip effects and foreign scopes
  cannot supply an unlock. Starting-history DLC branches support both nested and
  sibling `else`/`else_if` forms.
- Scripted-effect calls share the caller's country, guards, technologies, and pending
  variants, including nested calls across files. Definitions are checked through their
  callers, not as separate executions. Recursive calls stop at an active effect.
  Changes to effect definitions rescan callers, and findings identify the creation and
  consumption files.
- It does not follow unrelated event or focus chains, substitute scripted-effect
  parameters, or resolve dynamic names, so findings need review.

## validate_history.py

- `history-influence-order` (WARNING): country history writes to `influence_array`
  or `influence_array_val` need preceding `init_influence` and following
  `sort_influence` (or its `recalculate_influence` wrapper). A later initialization
  clears earlier writes; a sort before a later write is premature.
- Checks track explicit country scopes, ROOT/THIS, hidden effects, and conditional
  paths. Dated setups remain independent. Comments, tooltip blocks, unrelated
  arrays, and countries without foreign influence writes do not require setup.
  Arbitrary scripted effects and dynamic country scopes are not expanded.
- Warning-only while the audited content backlog in #5825 remains. The existing
  history CI batch selects this check for country-history changes.

## validate_events.py

- `date-gated-not-scheduled` (ERROR): MD fires historical events from
  `common/scripted_effects/00_yearly_effects.txt`, and the event's own `date >` is only
  a guard. An event with the guard and no schedule is dead content. Exempt: events
  reachable from a scheduled ancestor, fires from focuses or decisions, `random_events`
  pools, and chance-rolled `random` polls. A `date <` bound alone is an expiry guard.
- `scheduled-event-date-bound` (ERROR): a `date` comparison in an event's own
  trigger is redundant when only the yearly effects fire it. The yearly slot fixes
  the schedule; a `date <` bound can silently drop a fire when `random_days`
  spills past it. Events with another fire path (focus, decision, chain, or
  on_action `random_events` pool) may need the guard and are exempt.
- `event-fire-type-mismatch`, `malformed-event-fire` (ERROR).
- `event-option-log-without-effect` (ERROR): an option with a log but no effects is
  dead code. Tooltips count as effects. `fix_event_option_logs.py` removes dead logs.
- `event-option-log-id` (ERROR): log the option's own id, not a neighboring option's.
  Version strings and dotted scopes are not event ids. Exemptions live in
  `validation_config.json` `option_log_id_exempt`.
- `event-ai-chance-ignores-cost` (WARNING): authoring rules and cost kinds are in
  `event-reference.md`, "Cost-aware AI weights". A literal country scope is the
  receiver when a conjunctive event trigger requires `tag = TAG`, even with other
  conditions. `original_tag`, foreign-scope tags, and tags mentioned only inside
  `OR` or `NOT` do not prove the receiver.
  - Display-only `effect_tooltip` costs and temp writes do not execute.
  - Skipped: an option at `base = 0` with no `add` while another option can win, and
    a cost kind every option always pays, or every option pays only sometimes. A kind
    some options always pay and others only sometimes pay is not shared. An
    `if`/`else` chain or `random_list` whose every arm charges counts as always, and
    so does a charge behind the `MD_skip_treasury_cost` flag or an unset
    `skip_payment`. Tax rate is never shared, since options can move it apart.
  - Known gaps: a shared cost of different sizes is skipped too, so the dearer
    option goes unreported. So is a kind every option pays only sometimes, at
    different odds. Charges that depend on a variable set in each arm stay
    conditional. Costs behind conditions that can never hold still count. Stored negative values built from math or arrays, unsubstituted
    `[TOKEN]` values, custom cost-guard triggers, delayed event-chain costs,
    nonconjunctive recipient gates, caller-derived recipients, and single-option
    events. Review these manually.
- `event-unneeded-treasury-guard` (WARNING, opt-in with `--check-ai-chance-costs`): an
  `ai_chance` modifier that lowers the weight on bankruptcy or a high deficit, on an
  option with no money cost. Costs come from the whole option, nested scopes included,
  so a charge back to ROOT from a state scope counts, and so does one to another
  country. A political power cost justifies the bankruptcy check only. A war, a
  spending law change, or a money modifier the script names commits money and
  justifies both, directly or through a scripted effect (`MONEY_COMMITMENT_RE`).
  A free build costs nothing here, even for a building with upkeep, matching the
  `skip_payment` rule. Known gaps: reply-chain and delayed own-event costs, and money
  modifiers on an idea the option adds.
- `event-corruption-pp-cost` (WARNING, opt-in with
  `--check-corruption-pp-costs`): event options with a literal negative
  `add_political_power` and `decrease_corruption` in the choosing country, without a
  recognized local guard. Each decrease refunds 150 PP at level 1, so only a charge
  above 150 PP per decrease is reported. Event/option triggers and nested `if`
  limits can supply a lower corruption-level bound; fewer decreases must run than
  that bound. A direct
  level-1 exclusion supplies a bound of 2, so repeated decreases still need review.
  Entry bounds are discarded when event `immediate` effects can change corruption.
  Option bounds are discarded when a literal corruption-idea change precedes a
  decrease in that option. Nested `if` bounds expire after a corruption-idea change
  before a later decrease; a guard evaluated after an earlier change can establish a
  fresh bound. Every relevant operation must be guarded before nested limits suppress
  an option. Numeric state scopes are excluded; only explicit `ROOT` effects are
  followed back to the choosing country. Numeric weights directly under `random_list`
  remain in the choosing country's scope. Run:

  ```sh
  python3 tools/validation/validate_events.py --path . --check-corruption-pp-costs \
    --workers 1 --no-color --no-cache --output /tmp/event-corruption-audit.txt
  ```

  This runs all event checks; review the `event-corruption-pp-cost` diagnostics.
  Findings are review candidates, not proven content bugs. Dynamic PP costs,
  scripted-effect bodies, caller conditions, surrounding conditions in foreign scopes,
  and indirect corruption mutations are not followed. Mutually exclusive branches are
  aggregated. These gaps keep the check opt-in. No decisions are checked.

- Other gaps from #5738 are not checked:
  - Double building charges need both payments resolved to the same country and
    reachable path. Adjacent costs alone do not prove a double charge.
  - News-option coverage needs the reachable recipient set and satisfiable option
    triggers. A repeated tag mention alone does not prove overlap or omission.
  - Receiver identity inferred from event callers needs all call paths, including
    scripted effects and scope changes. `korea.60` through `korea.63` have no literal
    receiver tag gate, so the cost check cannot prove their receivers.
  - Flag-loop reachability needs all flag setters and executable caller guards.
    References alone cannot prove that a cycle is unreachable.
- Event pictures: both event windows draw `event_picture` at native size.
  `event-picture-format-mismatch` (ERROR) classifies by aspect ratio, not name: country
  art up to 1.45, news art from 2.0. The band between is not reported. For a sprite
  shared by both windows, split it into a `news_`-prefixed and an unprefixed pair
  instead of editing call sites.
- `hidden-event-picture`, `news-event-picture-omitted`,
  `placeholder-event-picture` (ERROR). Only pictures at depth 0 of the event body count,
  so leader portraits inside `immediate` do not.

## validate_factions.py

- `faction-goal-cache-scope` (ERROR): a goal file reads a `*_cache` variable with
  `check_variable` or `has_variable` under `scope:faction`. The cache effects write on
  the faction leader, so the read finds nothing and the goal never shows or completes.
  Only the nearest scope-changing block counts, so `faction_leader` inside
  `scope:faction` is fine. A name with a scope prefix (`ROOT.x_cache`) is skipped.

## validate_file_paths.py

- Windows resolves paths case-insensitively and Linux does not. A mod path that differs
  from a vanilla path only in case replaces it on Windows and loads beside it on Linux,
  so the platforms hash different file sets and cannot play multiplayer together.
- The checksummed set is `common/**/{*.txt,*.lua}`, `events/**/*.txt`,
  `history/**/*.txt`, and `map/**/{*.txt,*.map,*.bmp,*.csv}`. Collisions inside a
  `replace_path`'d directory are WARNING. `replace_path` is not recursive.
- It reads path names from the git index against `vanilla_paths.txt`. The in-mod case
  check overlaps the `check-case-conflict` hook on purpose.
- `source-art-format` (ERROR): under `gfx/`, `.psd`, `.xcf`, and `.tif` cannot load, and
  `.png` and `.jpg` load uncompressed without mipmaps. Convert with
  `tools/assets/md_art_convert.py`. `map/` is out of scope.

## validate_focus_tree.py

- `relative-position-forward-ref`, `relative-position-missing-target` (ERROR): the engine
  resolves focus positions in file order. Targets in another file are not checked.
- Focus geometry (WARNING): see the
  [coordinate policy](../../tools/validation/README.md#focus-coordinate-warnings).
- `focus-allow-branch-leak` (WARNING): a focus with its own `allow_branch` under an
  ancestor whose `allow_branch` can hide the branch, without repeating its conditions.
  A condition the ancestor checks only under the `obsolete_focus_branches_visibility`
  HIDE rule is also met when the child checks it without that rule.
- `unneeded-treasury-guard` (WARNING): the focus twin of
  `event-unneeded-treasury-guard`, over the completion rewards. The focus `cost` is
  completion time, never a price. A literal political power loss justifies the
  bankruptcy check. A literal `debt_change` cut is free, and a tax rate effect counts
  as a cost. A building effect after `skip_payment = 1` in the same or an enclosing
  block costs nothing. A charge another nation's event sends back to the sender,
  directly or through a reply event, counts. Known gaps: partner-event branches gated
  on the receiver's tag are not told apart, a partner-event charge never raises
  `missing-bankruptcy-guard`, and costs that come from an idea's modifiers, such as
  `personnel_cost_multiplier_modifier`, are not seen, so their guards read as unneeded.

## validate_ai_path_rules.py

- `common/national_focus/eritrea_puppet.txt` contains Ethiopia's Eritrean federation-
  puppet content. Its owner factor is 0 plus 1 for ERI, below `generic_focus`'s day-one
  factor of 2, so it does not need an ERI day-one AI path rule.

## validate_gfx_references.py

- The unused-sprite check is opt-in behind `--report-unused`. `MD_GFX_HIDE_UNUSED=1`
  hides the orphan list and keeps the case and duplicate findings.
- Sprite names the engine builds from mod data are resolved into the reference set, so a
  sprite still reports once its backing declaration is deleted: `GFX_<FOCUS_FILTER_X>`,
  `GFX_EMI_<module>`, `GFX_SMI_<module>`,
  `GFX_unit_<subunit|category>_icon_{small,medium}[_white|_black]`,
  `GFX_<TAG|graphical_culture>_ace_<m|f>_<n>`, bare decision icons as
  `GFX_decision_<icon>` and `GFX_decision_category_<icon>`, and anything a `[...]`
  template in scripted loc or a scripted-GUI `image` can build. A template with under four
  literal characters after `GFX_` is rejected, except `GFX_[?x.GetTokenKey]`, which
  resolves `GFX_<token>` for every synchronized dynamic token. Known gap: a sprite that
  shares a token's name never reports, whichever variable holds the token.
- True exemptions: equipment, tech, and designer icons, and any name vanilla also defines.
- `sprite-ref-case` (ERROR): an English `£name` that matches a sprite only
  case-insensitively, so the icon is missing on Linux. `undefined-loc-sprite` (ERROR): an
  English `£name` that matches no sprite at all. A `£` before a digit is the pound sign.
  `unused-sprite-case` (WARNING): a sprite whose only reference is miscased.
- `duplicate-sprite`, `case-variant-sprite` (ERROR): the message says whether the blocks
  share a texture. Unquoted `texturefile` values are read the same as quoted ones.
- `raw-icon-path` (ERROR): `icon =` inside `create_equipment_variant`, or an entry in a
  `graphic_db` `icons = { }` block, that is a texture path instead of a `GFX_` sprite.
  Quoted and unquoted, slash or backslash. Comments and focus-tree `icon =` are ignored.
  `_documentation.info` is not scanned. Raw plane paths crash the macOS air battle window.
- `undefined-font` (ERROR): a `.gui` font naming no `bitmapfont` renders in the default
  face. Vanilla names come from an install or `vanilla_fonts.txt`.
- Sprite names in generator-managed `.gfx` files come from the texture filename. Rename
  the texture and update `texturefile`, not the entry.

## validate_ideas.py

- Missing-icon audit (WARNING, always on): the sprite is undefined, exists only under a
  different case, or resolves to placeholder art (`_PLACEHOLDER_TEXTURES`). A mod
  placeholder that shadows a vanilla sprite name still reports.
- `missing-idea-localisation` (ERROR, behind `--missing-name-loc`): an idea whose name
  key has no English loc shows its raw id in every tooltip that grants it. The key is the
  `name = X` override when set, otherwise the idea id. Hidden categories and character
  `idea_token` entries are exempt. The CI core batch and the nightly run pass the flag.
  The commit hook does not, so there is no local signal. `--missing-loc` adds missing
  `_desc` keys as WARNING findings and runs nowhere by default.
- `loc-key-collision` (WARNING): an idea's `name = X` override resolves its name to `X`
  and its description to `X_desc`. When `X` is also a focus or decision id and resolves
  in English loc, one string silently overrides the other. Intentional sharing is allowed.
- `idea-quality` (WARNING): an idea `equipment_bonus` without `instant = yes` applies only
  to variants created afterwards. Exempt name prefixes go in
  `equipment_bonus_instant_exempt`.
- `idea-quality` (WARNING): `weekly_war_support` and `weekly_stability` in a top-level
  `modifier` on a `country` idea need a permanent grant to tick as intended. The check
  reads static `add_idea(s)` and `add_timed_idea` call sites across `common/`, `events/`,
  and `history/`; display-only `effect_tooltip` references are ignored. Timed-only ideas
  are skipped, while mixed grants are reported. A definition with no statically resolved
  grant is advisory because dynamic references and grants from outside those trees
  cannot establish permanence.
- `bonus-type-archetype-stack` (ERROR, also in `validate_mios.py`): a nested
  `equipment_bonus` naming a type category (`carrier`) and a child archetype of that type
  with the same modifier stacks twice. Helicopter operators are `type = carrier`.
  Distinct stats on the child are allowed.

## validate_localisation.py and validate_scripted_localisation.py

- `loc-yaml-*` (ERROR): tabs, curly quotes, version-number keys, missing colon spacing,
  excess indentation, missing closing quotes, and unescaped inner quotes. These check
  raw English lines, including comments and files exempt from other content checks.
  Findings use repository-relative paths for PR file matching, links, and annotations.
- `loc-em-dash`, `loc-backtick-apostrophe` (WARNING), and `loc-unbalanced-quote` (ERROR)
  scan only the quoted values in `localisation/english/`. Inch marks and quotes spanning
  paragraphs are expected false positives of the quote check.
- `loc-spaced-en-dash` (WARNING): a spaced en dash ( – ) used in place of an em dash. A
  dash between two numbers is a range and is skipped. Official names go in
  `spaced_en_dash_exemptions` (by loc key) or `spaced_en_dash_exempt_files` (by file) in
  `validation_config.json`.
- `loc-typo-watchlist` (ERROR): `typo-watchlist.md` entries in prose, excluding keys and
  runtime references. `it's` and `civilisation` are excluded as context-dependent.
- Prose warnings (repeated word, tripled letter, exact placeholder, dangling
  description): see `localisation-rules.md`.
- `loc-getter-spelling` (WARNING): a `[SCOPE.Member]` whose member is not a defined
  scripted loc is checked against `loc_objects_documentation.md`. Built-in getters match
  case-insensitively in game, so a case variant is a style finding. An unknown getter
  renders empty and logs nothing.

## validate_math_expressions.py

- `math-sibling-operator`, `math-from-read` (ERROR). The traps are in
  `hoi4-data-structures.md`. Plain `set_temp_variable = { x = FROM.y }` copies are valid.
- `clamp-min-above-max` (ERROR, opt-in `--clamp-bounds`, passed in CI): a `clamp`,
  `clamp_variable`, or `clamp_temp_variable` whose literal `min` is above its literal
  `max`. A bound that is a variable, an `@constant`, or an expression block is not
  judged, so a swapped pair with one of those still passes.

## validate_mesh_textures.py

- Commit-stage only, since the CI workspace ships no models. `mesh-texture-empty`,
  `mesh-texture-missing` (ERROR). Lookup rules: `entity-system.md`. The missing-name
  check needs a HoI4 install and logs a skip without one.

## validate_mio_icons.py

- The engine draws an equipment group as `GFX_<group>` and an archetype or type category
  under `equipment_type` as `GFX_military_industrial_organization_<token>`. A missing
  group sprite logs an error on every MIO refresh.
- `mio-equipment-group-icon` fires once at the group definition, `mio-equipment-type-icon`
  on each org block naming a non-group token. Both ERROR. `limit_to_equipment_type`
  carries no icon.

## validate_mios.py

- Gates: org-id format, `allowed = { original_tag = TAG }`, non-empty `on_complete`,
  initial-trait naming, and trait-grid x above 9. Negative x is the standard
  first column. `generic_` orgs and `generic_` initial traits are exempt.
- Trait geometry (ERROR): `trait-geometry-parent-row` (child on or above its parent's
  row), `trait-geometry-mutex-row` (mutually exclusive traits on different rows),
  `trait-geometry-mutex-parents` (a `parent` or `all_parents` list naming two mutually
  exclusive traits locks the child out, `any_parent` is the fix). Unresolvable anchors
  and cycles report nothing.
- Localisation (ERROR): `header-text-not-tokenized` (a literal quoted `tree_header_text`
  is printed verbatim and cannot be translated), `header-text-loc-missing`,
  `trait-loc-missing`. Key resolution mirrors the engine: `TAG_<key>` wins, else the
  bare key.
- Dead `equipment_bonus` (ERROR): a bonus is a percentage of the equipment's base stat,
  so a stat the target never declares, or declares as 0, does nothing.
  `mio-bonus-no-base-stat`: nothing in scope declares it. `mio-bonus-partial-base-stat`:
  only part of the scope does. The partial check skips `initial_trait`, which cannot be
  split. `mio-equipment-type-unknown` (WARNING) suppresses the bonus check for its block.
  - Scope in `organizations/`: the trait's `limit_to_equipment_type`, else the org's
    `equipment_type`, else that of the org named by `include`.
  - Scope in `policies/` and company traits: each named block is its own scope. A
    policy's `same_as_mio` block reaches the attached MIO's departments, so it gets no
    check. Outside `policies/` it is an unknown type.
  - `NON_STAT_BONUS_KEYS` excludes the per-archetype production keys.
    `zero_base_exempt_stats` in the config is empty on purpose: confirm in game before
    adding a stat. The naval `*_factor` keys stay out of it. Vanilla declares their base
    on hulls and modules, and MD declares none, so they are dead here.
  - The stat index (`equipment_stats.py`) counts a stat only with a non-zero value, and
    scopes modules to the slots a hull accepts.
- Naval production bonus: ships are built in dockyards, which have no production
  efficiency, so `production_efficiency_gain_factor`, `production_efficiency_cap_factor`,
  and `production_conversion_speed_factor` do nothing on a ship.
  `mio-production-bonus-naval` (ERROR): everything the trait reaches is naval.
  `mio-production-bonus-partial-naval` (WARNING): mixed scope, a coverage note.
  `policies/` is out of scope because `same_as_mio` is not statically resolvable.
- `mio-design-team-type-uncovered` (WARNING): a `create_equipment_variant` names
  `design_team = mio:<org>` whose `equipment_type` does not cover the variant's
  archetype after `mio_cat_*` expansion, so the engine ignores the designer. A type
  the equipment index cannot resolve (a vanilla designer airframe) is skipped. A
  staged org edit does not rescan unstaged references; the full CI run does.
- A staged change in `policies/`, `common/country_leader/`, `common/units/equipment/`,
  `common/equipment_groups/`, or English loc rescans every org.

## validate_modifiers.py

- No pre-commit hook, so `common/dynamic_modifiers/` edits get no local signal.
- `redundant-enable-gate` (ERROR): a top-level `always = yes`, `original_tag`, or `tag` in
  a dynamic modifier's own `enable`. See `common/dynamic_modifiers/README.md`.
  `tools/standardization/strip_dynmod_tag_gates.py` clears them in bulk.
- `dynamic-modifier-name-loc` (ERROR): a dynamic modifier needs a bare-name English key.
- `dynamic-modifier-enable-block` (WARNING): the whole `enable` block is re-evaluated per
  tick per holder. The state usually belongs in the effect that adds or removes the
  modifier. `unknown-modifier` (WARNING) has known false positives.

## validate_on_actions.py

- `deterministic-date-poll` (ERROR): `date >` polling from `on_daily`, `on_weekly`, or
  `on_monthly`. Historical events belong in `00_yearly_effects.txt`. Chance-rolled polls
  are exempt.

## validate_oob_units.py and validate_ai_equipment.py

- Every `create_equipment_variant` is slot-checked through `equipment_module_slots.py`
  (ERROR): unknown hulls, slots, and modules, slot categories, required slots, hull
  `module_count_limit`, `forbid_equipment_type`.
  `validate_ai_equipment.py` applies the same rules to `target_variant` designs.
- `parent_version` is not resolved. A clean run on a `parent_version > 0` design is not
  proof the runtime design is legal.
- Explicit variant definitions are cached per source file by content and indexed by
  producer, equipment type, and name. English default model names stay separate.
  Staged edits widen reference checks only when the resulting identities or
  producer/DLC/date context change. Equipment and English name edits still widen them.
- `duplicate-equipment-variant` (WARNING): repeated explicit creation of the same
  producer, equipment type, and name in potentially overlapping contexts. The finding
  cites both sites. Different producers or types, mutually exclusive DLC/if branches,
  event options, random outcomes, and tooltip-only effects do not count. Unresolved
  producers and dynamic names or types are not checked. Separate events can overlap,
  but the check does not prove both execute, so this is advisory.
- `validate_ai_equipment.py` runs without `--strict` locally and with it in CI.
- `create_unit` is checked for state scope, `owner`, block keys, a single-line division
  string that parses, zero or near-zero factors, and template order.
- `missing-equipment-factor` (WARNING, opt-in `--missing-equipment-factor`).
- `out-of-bounds-division` (WARNING): the parser rejects German and Danish letters
  (`äöüßæøå`) in the division string, even inside quotes. Other accents render.
- `missing-template-ensure` (WARNING): a `create_unit` naming a template that
  `delete_unit_template_and_units` removes anywhere needs the template created earlier
  or a `has_template` guard. A scripted effect that creates or guards it also counts.
- `airborne-template-not-parachutable` (WARNING): a `division_template` whose name
  matches para, airborne, VDV, or desant lists a sub-unit without
  `can_be_parachuted = yes`, which stops the whole division from paradropping.
  Deliberate air-assault templates are listed in `air_assault_templates` in the
  config as `<file>:<template name>`. Staged mode checks only staged template files, so a `common/units/`
  flag change surfaces on the full CI run.
- `template-slot` (ERROR): a `division_template` skips a row or column, puts two units
  on one slot, places a unit off the designer grid, or has a unit with no readable
  `x`/`y`. The designer hides the unit and locks the template for editing.
  `regimental_support` may skip columns, but each of its columns needs the same
  `regiments` column, and each row needs the battalions
  `REGIMENTAL_SUPPORT_REQUIRED_BATTALIONS` sets for it.
- `template-locked-row` (WARNING): a `regiments` unit sits on a row past
  `MIN_DIVISION_BRIGADE_HEIGHT`. Those rows stay locked until the country has
  `additional_brigade_column_size`. One finding per template. A tag's starting
  subdoctrines (`set_sub_doctrine` at the top level of its `history/countries` file)
  open rows for its `history/units/TAG_*` files and for templates scoped to it. So do
  their mastery rewards, once top-level `add_mastery` blocks with a literal `amount`
  and only a `sub_doctrine` filter reach the reward. Reward thresholds add up in
  order. Dated history and ideas are not counted. Tracked in #5451.
- Both read the grid from `NDefines.NMilitary` in `common/defines/*.lua`, falling back
  to the vanilla values in `_VANILLA_TEMPLATE_DEFINES`. Not checked: Army HQ template
  sizes and `allowed_battalion_groups`. Staged mode checks only staged template files,
  so a define or doctrine change surfaces on the full CI run.
- `template-misplaced-support` (WARNING): a `support` block lists a sub-unit with
  `divisional = no`, or a `regimental_support` block lists one with `regimental = no`.
  The game drops that unit from the template. Ships as WARNING for its backlog of
  1,286 `divisional = no` units in `support`. A `common/units/` flag change surfaces
  on the full CI run only.
- `airbase-over-capacity` (WARNING): the planes `history/units` `air_wings` place in a
  state exceed its undated `air_base` level times `NBuildings.AIRBASE_CAPACITY_MULT`
  (vanilla 200, one slot per plane). Totals add every country's OOB, so each file
  sharing an overfull base gets its own finding. Every file with `air_wings` counts as
  a starting placement; today all are `set_air_oob` targets. Staged mode reports only
  staged OOB files, so a state or define change surfaces on the full CI run. WARNING
  until the starting backlog clears.

## validate_party_loc.py

- Format categories are WARNING and tracked per nation in #3895. `party-loc-unknown-tag`
  is ERROR.
- The default run scopes format checks to the tags the branch touched. `--all` sweeps
  everything, `--tag TAG` audits one nation. Missing slots are never reported.
- Full `run_all_validators.py` runs, including main's baseline, pass `--all`, so a PR's
  scoped findings in a touched tag match main's results instead of reading NEW.

## validate_scientist_traits.py

- A trait's medal resolves to `icon = X`, else `GFX_<token>`. The sprite index is
  MD-only, because MD replaces `interface/unitleaderwindow.gfx` and vanilla's
  `GFX_scientist_trait_*` names are dead in game.
- `shadowed-scientist-trait-icon` (vanilla ships the art, re-declare the `spriteType`),
  `missing-scientist-trait-icon`, `stale-scientist-trait-icon-todo`. All WARNING.

## validate_simplifications.py

- `simplification` (WARNING): a repeated clause in `OR` is dead weight or a
  copy-paste where one copy was meant to differ.

## validate_scripted_params.py

- Contracts come from the `# Parameters:` block above a scripted effect, plus the
  `HARDCODED_CONTRACTS` table in the validator. Declare a parameter in the block to
  have its required temp variables checked. Effects without a contract still get the
  unsupported-argument checks below.
- `content/tool_data_drift_test.py` pins the four money and party popularity blocks. A
  blank line inside a block, or a renamed header, silently drops the contract.
- `unsupported-effect-arguments` (WARNING): a known scripted effect called with a
  block such as `HLS_holy_wargoal = { TARGET = FRA }` instead of `= yes`.
- `unsupported-effect-placeholder` (WARNING): an unquoted `$NAME$` in a scripted
  effect definition. Use scopes, temp variables, or `meta_effect` instead. Definitions,
  comments, quoted strings, native effect blocks, and scripted trigger parameters are
  not flagged. Both unsupported-syntax checks stay advisory pending backlog triage.
- `call-shares-line` (ERROR): a contracted call sharing its line with another statement.
  Single-call wrappers and trailing comments are accepted. `--audit-shared-lines` adds
  uncontracted mixed lines as WARNING.
- `missing-required-param` (ERROR): a call with a required parameter not set first.
  `set_temp_variable`, its `var = NAME` long form, `set_temp_variable_to_random`,
  `add_to_temp_variable`, and `subtract_from_temp_variable` all count as setting it.
- `orphan-param-setter` (ERROR): a `set_temp_variable`, `add_to_temp_variable`, or
  `subtract_from_temp_variable` of a declared parameter, required or optional, that
  nothing uses afterwards in the same effect block, or that is overwritten at the same
  depth before its first use. The `var = NAME` long form counts.
  - A use is a call to any scripted effect or trigger that reads the parameter before
    writing it, contracted or not, or a direct read. `multiply_temp_variable` and the
    other statements that only change it are not uses. A write nested in a branch of
    the callee is ignored, since it may not run.
  - `move_party_popularity` writes `party_popularity_increase` itself, so it does not
    consume a caller's value.
  - Not reported: a reset to `0`, a setter in a scripted effect's own body, and a
    setter outside the blocks in `EFFECT_BLOCK_KEYWORDS`, `effect_tooltip`, and
    scripted GUI `*_click`.
  - A setter inside `effect_tooltip` must be used inside it. A runtime setter that only
    feeds a later `effect_tooltip` preview is accepted.
  - Known gap: a use in a sibling `if` or `else` arm counts.
- A staged change under `common/scripted_effects/`, `common/scripted_triggers/`,
  `common/country_tags/`, or `common/country_tag_aliases/` rescans every caller.
- See the [layout policy](../../tools/validation/README.md#scripted-effect-call-layout).

## validate_style.py and check_common_mistakes.py

- The style check is diff-scoped in the core job. Common mistakes run full-repo in the
  core batch through `validate_common_mistakes.py` and report ERROR, with
  `shadowed-branch` as its own category. It scans `common`, `events`, `history`, and
  `music`.
- Shadowed branches: the parser blanks quoted strings, so a limit with a quoted value
  never matches another. Only strict `>` and `<` bounds are ordered. Leader files are
  skipped, since the rotation check already reports their duplicate branches.
- `shared_focus_prefixes` in the config exempts `EH_` focus ids.
- The decision log id check also reads a log with no `Decision` word, when the string is
  only the standard prefix, filler words, and one id. Longer text is skipped, so a log
  such as `... <other_decision> setup finished` is a known gap. `Mission` works like
  `Decision`, and an id that runs into `[?...]` is built at runtime and skipped.
- An effect block whose only content is a `log` line is dead: delete the block. The
  standardizers and `tools/logging_tool.py` never inject a log into an empty block.
- Name checks resolve against mod data: equipment `type =` (with `duplicate_archetypes`
  clones expanded across numbered variants), `equipment_bonus` types,
  `has_active_mission` and `has_active_decision`, `add_opinion_modifier`, and
  `add_relation_modifier`.
- Structural checks: a `limit` directly under `else`, `province = { province = <id> }`,
  and a `#` comment swallowed into a `log` string.
- `indent-depth` (WARNING): a line whose leading tabs differ from its brace depth, one
  finding per run of lines off by the same amount. It uses the `reindent_by_brace_depth`
  rule, so `tools/linting/fix_styling.py --fix-indent <files>` or a standardizer run
  clears it. The scan strips comments, so comment-only lines are not checked. Four
  leading spaces stay the `indent-brackets` ERROR. Ships as WARNING for its backlog,
  tracked in #6248.

## validate_variables.py

- `clamp-range-conflict` (WARNING): a `check_variable` against a value outside a literal
  `clamp_variable` range, or a sub-1 value against a variable clamped to a wide integer
  range. Variables written only by `set_temp_variable` are excluded.
- `unregistered-dynamic-token` (ERROR): every `token:X` literal and every `@X` target of a
  token game variable must be in `common/synchronized_dynamic_tokens/MD_tokens.txt`, or
  the engine logs an OOS warning per use. `@` after any other name is a scope.
  Runtime-built names are ignored. New tokens go in `MD_tokens.txt`, not
  `_ENGINE_KNOWN_TOKENS`.
- `redundant-focus-flag` (WARNING): a country flag set once, unconditionally, in a focus
  `completion_reward`, never cleared, and read only by short-form `has_country_flag`.
  `has_completed_focus` replaces it. Not reported: a second setter, a conditional or
  foreign-scope set, any `clr_country_flag` or `modify_country_flag`, a timed or valued
  form, a focus with `bypass`, joint rewards, and a set in a file that loads a focus
  tree or defines one that `load_focus_tree` loads. `keep_completed = yes` only keeps
  focuses the new tree also has, so the flag outlives a swapped-out focus.
- `available`-block checks (ERROR), each protecting a requirement line the player reads:
  - `untooltipped-available-check`: a bare `check_variable` renders no line.
  - `unlocalised-available-flag`: `has_country_flag` and `has_global_flag` render from a
    loc key named after the flag. Also covers `cancel_trigger`, `bypass`, and flags
    inside called scripted triggers.
  - `unlocalised-negated-trigger-tooltip`: a tooltip under an odd number of `NOT` blocks
    looks up `not_tooltip`, or `KEY_NOT` when none is set. `= no` counts as a negation.
  - `untooltipped-available-scripted-trigger`: a bare call to a scripted trigger whose
    body checks `has_global_flag` renders nothing.
  - Exempt: `custom_trigger_tooltip`, `custom_override_tooltip`, and `hidden_trigger`
    wrappers at any depth, `check_variable`'s inline `tooltip`, `visible` blocks, names
    containing `@`, AI-only decisions, and `if` branches whose `limit` holds an
    unconditional `is_ai = yes`.
- `variable-tooltip-missing-loc` (ERROR): `tooltip = KEY` in a variable effect with no
  English entry. `dynamic-modifier-tooltip-missing` (ERROR): an add or subtract on a
  variable backing a dynamic modifier with no `tooltip`, in blocks the engine renders.
  `hidden_effect` suppresses both.

## Other tools

- `validate_standardization.py` is manual. It runs the standardizers in memory and
  reports files they would rewrite. Pass `--all --no-color` for a full pass.
- `validate_unused_textures.py` is a manual-stage hook. CI cannot run it.
- `validate_set_variables.py` and `validate_scripted_localisation.py` are CI-only and
  strict. Run them directly for a local check.
- `sprite_index.py` indexes mod `.gfx` plus a live install. It reads `vanilla_sprites.txt`
  only for sizes (`build_sprite_size_index`) and for `validate_ideas.py`. Event pictures
  use `include_vanilla=False`, since MD must not rely on vanilla event pictures.
