# Counter-Terrorism Arrays and Scheduling

The CT implementation is in `common/scripted_effects/00_ct_effects.txt`. Its weekly dispatcher is
in `common/on_actions/MD_on_actions.txt`.

## Organization identity and slots

`global.active_terror_orgs` stores stable organization IDs. Its array positions are mutable slots.
Threat, visibility, cooldown, HQ state, HQ controller, reach, region, and announcement flags all
use those same slots. Each country's four intel arrays must have the same length and slot order.
Deleting a slot shifts every surviving organization's global data and country intel together.

Infiltration flags and prepared raid targets use organization IDs because they outlive a slot's
position. Raid resolution finds the ID's current slot; a destroyed or missing target receives no
organization effects. The player's selected slot shifts with surviving organizations and resets
to the first slot when its organization is removed. Organization controls require a valid slot.

Attacked, infiltrated, and failed-infil state live in per-country arrays indexed by organization
id (`ct_attacked_by_org_arr`, `ct_infiltrated_org_arr`, `ct_failed_infil_org_arr`, fixed size 10).
Id indexing survives slot shifts, so org creation and removal touch no per-country state except
clearing the removed id (ids recycle through the inactive pool). Attacked and failed-infil entries
count down one per staggered pass (13 passes cover the old 365-day flag window); infiltrated is
permanent until its org is removed. No CT scoring, gate, or button uses `meta_trigger`/`meta_effect`.

Global setup creates the organization arrays before country intel initialization. New countries
size their intel arrays from the current organization count, including when that count is zero.
Creation appends a complete organization record with a controlled HQ in the existing Middle East
country pool. An empty inactive pool or no eligible HQ makes creation a no-op. Creation currently
has no production caller; successful elimination raids call removal.

## Country coverage and cadence

The four `global.ct_*_week` arrays together contain every country enrolled in CT, exactly once.
Membership is the initialization check; an empty intel array cannot serve that purpose after the
last organization dies. Released and civil-war countries use the same idempotent enrollment path.

Annexed countries remain enrolled. Lifecycle updates include their intel so restoration cannot
attach old intelligence to the wrong organization. Weekly processing skips non-existing countries.
Countries that have never existed receive correctly sized arrays when they first enroll.

Each weekly dispatch processes one bucket. Each existing enrolled country therefore runs once
per four weekly ticks, in the order: national CT, conditional power ranking, AI cyber, AI CT.
The organization count is copied once before bucket processing; these effects do not add or
remove organizations during that pass. The separate monthly global CT pulse is unchanged.

## International escalation recipients

`MD_terror.21` is a country event with stability, policing-budget, and party-popularity effects.
Both human and AI countries, including non-UN countries, require their own resolution and options.
Keep the existing worldwide dispatch and its 1–8 day delay. A player-only notification, UN array,
or single news event would change those outcomes. Regional escalation remains region-scoped.

## Work demonstrated by script inspection

- Startup previously allocated seven intel slots for six organizations. Correct sizing removes
  one full intel calculation per eligible country per four-week cycle: seven iterations become six.
- For a bucket with A AI countries, the weekly dispatch changes A global organization-size reads
  to one cached read. Per-country numeric comparisons remain; this is not a measured timing gain.
- Lifecycle updates require four intel-array operations for each enrolled country. Iterating the
  four existing buckets covers the readers without a new global country scan or registry.
- International escalation still queues one gameplay event per existing country. Those events
  are required by the current design; reducing their number needs a separate gameplay decision.

These are script-operation counts, not HOI4 wall-clock profiling. Engine-level checks should cover
startup, four weekly ticks, annexation and restoration, civil-war enrollment, creation after zero
organizations, middle-slot elimination, prepared raids after elimination, and escalation choices.
