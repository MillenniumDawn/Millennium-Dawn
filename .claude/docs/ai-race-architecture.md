# AI Race Architecture

The player-facing name is the AI Race.

Status: upstream core port of the OEM four-stage race and strategic computer planning.
The investment-owner offer guard and the corporate adapters for OEM-only systems follow
in a later port. Natural campaign balance and UI acceptance remain separate from source
and regression-test evidence.

## Ownership and scope

The race owns `ai_race_*` variables, `AI_RACE_*` country flags, its registries, declarative AI
preferences, and operating dynamic modifier. USA and China use national baselines from
technology, microchips, research slots, and their starting policies. Other countries use
technology, research slots, industry, Network Infrastructure, energy, and material supply.
Buildings, queues, research projects, trade, investment offers, and sovereign debt remain owned
by their existing systems.

If Corporate History later joins upstream, its modes remain independent of the AI
Race. National corporate state is never repaired, granted, or cleared by the race.
Existing AI technologies, including the later AGI technology, retain their dates
and effects.

Competing laboratories, model releases, crises, and broader policy systems are outside this
implementation.

## Stages and centralized values

`common/scripted_effects/01_ai_race_capacity_effects.txt` owns the stage requirement table.
Costs are billions of dollars. Work is completed monthly work after entry, not calendar catch-up.

| Stage          | Entry from | AI tech | Work months | Upfront |
| -------------- | ---------- | ------- | ----------- | ------- |
| Research       | Jan 2016   | 7       | 36          | 50      |
| Implementation | Jan 2019   | 7       | 60          | 150     |
| Expansion      | Jan 2024   | 8       | 12          | 400     |
| Frontier AI    | Jan 2025   | 8       | Terminal    | 1,000   |

| Requirement       | Research | Implementation | Expansion | Frontier |
| ----------------- | -------- | -------------- | --------- | -------- |
| Civilian levels   | 20       | 40             | 80        | 150      |
| Network levels    | 10       | 20             | 40        | 80       |
| Base power demand | 2        | 8              | 25        | 60       |
| Microchips        | 5        | 20             | 60        | 150      |
| Composites        | 2        | 8              | 25        | 60       |
| Oil               | 2        | 5              | 10        | 20       |

Demand is the cumulative requirement of the current stage; advancing replaces the old demand.
The dashboard scales base power with the multiplier sampled by MD's energy owner and displays GW.

Entry checks the date, technology, completed previous-stage work, quoted terms, treasury, and
bankruptcy risk. Instant construction is treated like ordinary construction: actual capacity
counts, regardless of how it was built.

The entry month earns no work. An uninterrupted January 2016 entrant can buy Implementation in
January 2019, Expansion in January 2024, and Frontier AI in January 2025. Later starts begin with
no funded stage. Purchased stages continue accumulating work during capacity shortages.

## Enrollment, scheduling, and rankings

- `global.countries` is scanned from 2016 on the first discovery pass and each January.
- A human can enroll between passes through the dashboard refresh or an eligible stage review.
- Completing AI technology 7 initializes an eligible human country and announces the category
  immediately. The 2016 date gate and race modes still apply; repeat initialization is silent.
- `global.ai_race_all_initialized` records every initialized country independently of eligibility.
- Active arrays are rebuilt from existing, non-collapsed registry members. Temporary eligibility
  loss never erases paid stages or obligations.
- Annexed countries retain dormant history. Existing countries with obligations remain subject
  to normal weekly billing, even when inactive in the leaderboard.
- A global month token prevents replay of the monthly dispatcher; each country also records its
  last progress month and stage-entry month.
- Quarterly aggregation retains its separate replay guard and epoch.
- Ranking compares stage, completed stage work, effective capability, then ascending country ID.
  `global.ai_race_ranked_participants` drives the public rival list.
- Maximum effective capability is recorded independently of the stage-first leaderboard leader.
- `global.ai_race_first_finisher_id` records the historical first terminal finisher. A later change
  in rank or operating capacity cannot transfer that identity.

Monthly autonomous candidates are ordered by pre-purchase effective capability and country ID
after every participant has received that month's work. The successful terminal transaction
claims leadership; an unsuccessful candidate cannot reserve it.

## Physical capacity

The minimum of six individually clamped ratios determines operating effectiveness:

1. Undamaged civilian factory levels in controlled states.
2. Undamaged Network Infrastructure levels in controlled states.
3. Sustained national power headroom.
4. Net microchip supply.
5. Net composite supply.
6. Net oil supply.

Material supply reads the engine's net `resource@` values, including delivered imports and the
effects of trade disruption. Construction queues and damaged levels contribute no readiness.

Power reads `energy_balance`, which MD computes before battery withdrawal and fossil curtailment.
That balance includes available fossil generation when fuel exists and delivered power imports.
Battery withdrawal and curtailed fossil capacity must not be added again.

The race modifier applies base electricity demand and resource costs. In the same modifier,
four applied-demand markers identify the race portion actually applied by the engine.
The energy owner samples its applied power marker and display multiplier during consumption,
then publishes supporting capacity after the corresponding balance calculation. Only that
sampled race load is added back; a newly requested stage cannot create apparent spare power.

For resources, a new load must match the applied markers and pass a full daily settling interval
before its load can be added back. During settling, live net supply uses zero add-back and new
commitments are blocked. Stable quotes refresh current net supply instead of trusting old imports.
This can temporarily understate operating benefits while the engine settles a new modifier.

Repository documentation does not establish atomic cache refresh of `resource@` and `modifier@`.
Marker agreement and the settling interval are conservative safeguards; the actual engine
boundary requires a dedicated natural-runtime check. No forced dynamic-modifier update is used.

## Funding and weekly accounting

Normal funding requires all six readiness ratios to equal one and sufficient upfront treasury.
Emergency AI Financing permits physical shortfalls but cannot bypass dates, technology, prior
work, upfront funds, or bankruptcy checks.

```text
greatest_shortfall = 1 - minimum_readiness
additional_principal = approval_GDP * (0.45 + 0.40 * greatest_shortfall)
weekly_installment = additional_principal / 520
```

The fixed additional principal is 45% to 85% of approval-time GDP. It is additional to the upfront
investment. There is no GDP destruction, treasury grant, or modeled IMF transfer.

Each stage has one immutable original principal and weekly installment, plus remaining principal
and installments. Concurrent packages add together. On installment 520, the exact remaining
principal is due, including rounding residue. Even a rounded zero interim installment advances
its term after the corresponding zero charge enters weekly accounting.

The first package cannot bill before seven days after approval. Later packages use the country's
existing weekly cadence. A next-bill day prevents repeated weekly callbacks from collecting twice.

Accounting entrypoints in `02_ai_race_finance_effects.txt`:

- `ai_race_refresh_finance_totals`: pure outstanding and installment projections.
- `ai_race_refresh_finance_expense`: adds the fixed obligation after MD's inflation adjustment.
- `ai_race_prepare_weekly_bill`: freezes the per-stage due amounts and corrects only the race
  component of the treasury rate when the callback is repeated or a package changed.
- `ai_race_commit_weekly_bill`: advances ledgers only after the actual treasury accrual.
- `ai_race_clear_finance_state`: removes race obligations without reversing existing sovereign debt.

The additional-expense component and the component represented in `treasury_rate` are sampled
separately at their owner refreshes. The ledger commit sits inside the enabled economy branch,
after treasury accrual and before MD's automatic borrowing. No preview, repair, economy refresh,
or reload calls that commit path.

GDP changes, inflation, capacity recovery, and bankruptcy do not reprice existing obligations.
MD's ordinary negative-budget borrowing remains authoritative.

## Rewards and autonomous policy

Funded stages provide cumulative 1%, 2%, 3%, and 4% bonuses to research speed, production
efficiency growth, and office income. The first Frontier AI finisher adds one percentage point
to each. Every bonus is multiplied by current operating effectiveness; demand is never reduced
by shortages.

Computer-controlled countries use the same quoted transaction as humans. They prefer normal
funding. Emergency financing additionally requires every readiness ratio to be at least 75%,
debt below 60% of GDP, a nonnegative projected weekly budget after the new installment, and
treasury remaining after upfront investment sufficient for a year of expenses.

## Strategic computer planning

`04_ai_race_ai_effects.txt` owns the controller and `MD_ai_race_ai.txt` owns declarative
AI strategies. Policy state uses `ai_race_ai_*`. Preparation has its own
`global.ai_race_ai_countries` registry and never initializes a public stage or grants technology.

Discovery begins in January 2013 and repeats annually. A prospective country must be computer
controlled, exist with an enabled economy and positive GDP, have a research slot, and control at
least ten undamaged civilian factory levels. There is no country whitelist. Enrolled countries
remain managed after capacity loss, and the registry retains dormant members for later return.

The guarded monthly dispatcher updates plans after stage work and before autonomous purchases.
The controller first restores deficient paid-stage capacity. Otherwise, it prepares for the next
stage when the later of its calendar gate and remaining-work completion is within 36 months.
Frontier finishers continue maintaining their operating capacity. Preparation does not alter
stage-entry dates, completed work, financing eligibility, or first-finisher ordering.

War, bankruptcy risk, collapse, a disabled economy, high deficit, or MD's major economic problems
condition suspend expansion preferences, protected expansion savings, and stage purchases. Live
guards also disable these preferences on human takeover. Affordable operating supply recovery
uses existing energy systems and their normal affordability checks.

Initial preference values:

| Preference                    | Initial value                         |
| ----------------------------- | ------------------------------------- |
| First missing AI prerequisite | +100% research weight                 |
| One supporting technology     | +100% research weight                 |
| Needed production project     | 2x existing project preference        |
| Preparation building pressure | +25, except civilian factory targets  |
| Recovery building pressure    | +50, except civilian factory targets  |
| Activated power/material goal | Continue to 110% of stage requirement |
| Savings activation            | Every target readiness ratio >=75%    |

Research preferences follow the existing AI, computing, microchip, composite, and energy chains.
Additional ahead-of-time preference begins no more than one year before a technology's date;
ordinary availability, economic gates, and research penalties still apply. Production unlocks
use normal special projects, facilities, breakthrough points, resource costs, and rewards. The
planner prioritizes a required facility when none exists; it never reproduces a project reward.

Construction adds pressure for the greatest actionable proportional shortage. Native civilian
and network `building_target` strategies use the literal values in the centralized stage table;
regressions keep these targets aligned. Construction compares total levels, while readiness uses
undamaged levels. Sufficient but damaged buildings wait for ordinary repairs. Native queues and
construction choices remain authoritative. Civilian factories use only their fixed targets:
targetless `build_building` for that building requests military-factory conversion, so the planner
does not apply the extra 25/50 pressure through that strategy type.

Plants require available state capacity, workers, operating electricity, and delivered feedstocks.
Microchip plants need tungsten and chromium; composite plants need rubber, chromium, and oil.
Delivered output imports satisfy the target and can stop construction pressure. A blocked plant
can create a supporting power construction goal without changing purchase requirements. Power
and material priorities already activated persist to 110%, preventing repeated small shortages;
purchase readiness and emergency financing continue using the original six requirements.

Fossil generation requires fuel support; nuclear construction requires reactor-material support.
The planner can prefer renewables when available. Existing fuel purchases, reactor-material
diplomacy, and deficit-based electricity sharing retain their prices, suppliers, political-power
costs, cooldowns, and acceptance rules. Refineries may support native fuel and rubber needs but
never count as oil-resource supply. A refinery can serve the selected composite shortage when
rubber blocks an otherwise feasible plant or project, or an operating fossil fleet's low fuel
when no new power source is actionable. Native technology, staffing, slots, electricity, and
affordability gates still apply. No proactive import contract is created. A country can wait for
ordinary trade when remaining requirements cannot be supplied domestically.

## Savings and outgoing investments

Once every target ratio reaches 75% and expansion is permitted, the protected treasury target is
the next upfront investment plus 52 weeks of expenses. Existing financing is already included in
those expenses. A prospective installment is added only when the race's emergency policy permits
it, including its debt and projected-budget checks.

After weekly economy calculation and treasury accounting, a pure refresh updates the monetary
target before automatic stockpile debt repayment. Both gradual and full debt payoff preserve the
active race target; cash above that reserve remains available for repayment. Mandatory
expenses, scheduled installments, ordinary borrowing, and separate weekly-surplus debt repayment
retain their existing behavior. Live expansion guards release protection during war or crisis.

A race purchase waits while upstream's seven-day `investments_ai_pending` flag marks an
outgoing offer in flight. Outgoing investments subtract the reserve only while the live
`ai_race_ai_expansion_permitted` guard passes. The AI checks spendable treasury before
scoring targets and checks the calculated cost before sending an offer. Acceptance rechecks
the saved offer cost against spendable treasury. An investor-side funding failure never
blacklists the target; an accepted offer that can no longer be funded notifies the investor
that it lapsed. A frozen, generation-bound offer record remains part of the investment-owner port.

## Decisions and notifications

One Decisions dashboard shows national progress, current physical requirements, benefits, rank,
next investment, and financing. The public leaderboard lives in its own International Systems
tab, The AI Race (`01_international_ai_race_gui.txt`, `MD_international_ai_race.gui`): every
ranked participant's stage and capability, the first Frontier AI finisher, and a status line for
Off, before 2016, no participants, and Outcomes Only. It refreshes on `global.ai_race_view_dirty`, and
opening it calls `ai_race_bump_view` only while the race is enabled, so Off creates no state.
Foreign financial ledgers are never rendered. Country-scope dynamic rows avoid per-country
localisation or interface definitions.

Four free stage reviews open confirmation events. Defer is the first option and the timeout
default. Quotes expire after seven days; a nine-day pending-review flag prevents duplicate
dialogs without permanently locking progression.

Confirmation rechecks the stage, prerequisites, treasury, and all six quoted readiness ratios.
Emergency financing also rechecks GDP and financing terms; a direct payment does not depend on them. Changed terms charge nothing and require a fresh review. The event option
delegates all gameplay to the authoritative transaction.

The first terminal transaction sends one global announcement. Human terminal finishers receive a
national completion report. Notification options have no gameplay payload.

All shared English strings remain in `MD_ai_race_l_english.yml`. The UI uses Emergency AI
Financing, Outstanding AI Financing, and Capacity Shortfall. Explicit Ready/Shortfall labels
prevent rounded percentage displays from promising eligibility.

## Modes and cleanup

| Race mode     | Behavior                                                        |
| ------------- | --------------------------------------------------------------- |
| Full          | Progression, demand, financing, bonuses, and strategic planning |
| Outcomes Only | Capability assessments and rankings                             |
| Off           | No active race mechanics; cleanup visits the lifetime registry  |

Outcomes Only clears funded progression, demands, financing, terminal rewards, and planning while
retaining the assessment registry and any historical first-finisher identity. Off clears every
initialized country, including dormant countries, then clears global race state. Both modes clear
preparation-only countries, their preferences, and protected savings. Neither path reverses
buildings, native queues, trade, investment commitments, or sovereign debt already incurred by MD.
Any future Corporate History mode must remain independent of the race mode.

## Acceptance evidence

Executable state regressions cover actual progression/transaction scripts with bounded owner
stubs. Separate accounting and capacity models test conservation, timing, shocks, and cleanup,
with structural checks binding them to the shipped owner hooks. These are source-level evidence.
Strategic regressions execute the planner, construction and research predicates, and savings
hooks against explicit native-state fixtures. They do not simulate native AI
research scoring, construction scheduling, diplomacy, or campaign economics.

Natural HOI4 acceptance is still required:

- Observe USA, China, and a generic country from 2013 preparing through ordinary research,
  special projects, construction, and trade. Do not prescribe a winner or a January 2025 finish.
- Observe saving toward a stage, repayment of cash above the reserve, wartime/crisis release,
  affordable operating recovery, and resumed preparation after supply restoration.
- Start a January 2016 capable generic country and inspect the dashboard before and after funding.
- Exercise normal, emergency, insufficient-funds, changed-quote, Defer, and seven-day expiry paths.
- Verify exact boundary values and Ready/Shortfall labels, including near-100% rounded ratios.
- Observe weekly treasury billing and the four independent ledgers over overlapping obligations.
- Lose imports, damage civilian/network capacity, exhaust fuel, and test battery-only coverage.
- Test surplus fossil generation curtailed by full storage and delivered electricity imports.
- Purchase immediately before/after a resource refresh; verify no false spare capacity.
- Restore capacity and confirm benefits recover while the original repayment term continues.
- Save/reload around entry, monthly progress, weekly accrual, and pending confirmations.
- Produce simultaneous terminal candidates; verify one global first announcement and later
  human completion reports with historical leadership retained after capacity loss.
- Exercise all three race modes, inactivity, annexation, return, and complete cleanup.

Static checks, model tests, and console fixtures do not establish natural campaign balance.
