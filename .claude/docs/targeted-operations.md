# Targeted Operations

Targeted Operations is a persistent intelligence, authorization, operations, and
consequences system for registered people and organizations. Full Sandbox includes
genuine assassination operations against registered foreign civilian political
leaders. State-security organizations such as the IRGC are first-class subjects and
do not require a Counter-Terror organization slot.

This document is the canonical implementation contract. Development saves are not
supported across schema changes.

## Game modes and offensive ownership

The `RULE_TARGETED_OPERATIONS` game rule has three modes:

| Mode            | Dossier visibility                                                                                                                       | Operational authority                                                                                                                                            |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Limited Sandbox | Active registered public leaders, officials, and organizations can appear as Cold dossiers. Other subjects follow their discovery rules. | Militants are normally eligible. State-security subjects need war or an authored mandate. Political and civilian subjects need an authored mandate.              |
| Full Sandbox    | Every active registered foreign subject can be visible or discovered under its normal knowledge rules.                                   | Every registered foreign person and organization can use the normal method-specific pipeline. Serving foreign political leaders are valid assassination targets. |
| Off             | The TOP interface and offensive workflow are unavailable.                                                                                | OEF, Iraq, ISIS, Soleimani, and other legacy systems use their non-TOP fallbacks.                                                                                |

The authoritative triggers are `TOP_enabled`, `TOP_limited_sandbox`,
`TOP_full_sandbox`, `TOP_person_operational_eligible`,
`TOP_organization_operational_eligible`, and
`TOP_facility_operational_eligible`. GUI visibility is not authority.

All offensive entry points also require `TOP_human_offense`. AI countries cannot
designate packages, select a focus, open a review, approve a mandate, reserve the
operation slot, prepare an operation, or launch one. AI countries may still defend
subjects, answer host and liaison requests, use deception, hold custody, investigate
attribution, respond to crises, and make restricted strategic-crisis choices.

## Registry and stable identity

`tools/data/targeted_operations.json` is the authoring source. Run:

```text
python tools/generators/generate_targeted_operations.py
python tools/generators/generate_targeted_operations.py --check
```

Person and organization IDs are permanent and must never be recycled. The current
manifest has person capacity 161, permanent IDs through 160, generated successor
IDs 65 through 128, and 37 organization records. Zero is reserved. Organizations
remain in their own registry and never consume a person ID.

The four organization classes are:

- `militant_network`
- `state_security`
- `political_executive`
- `civilian_organization`

A group may also set `activation_condition`, a scripted trigger added to its monthly
activation check, and the `fixed_state` location policy with a `state` ID, which places it
in that state instead of a random state of its host. The STALKER organizations use both.

`ct_id` is an optional intelligence source. It is not an activation, discovery,
display, collection, or authority prerequisite. IRGC/Quds Force, IRGC high command,
Ground Forces, Aerospace Force, and Navy are public `state_security` organizations
from their authored activation dates even when no Counter-Terror slot exists.

The generator validates stable IDs, organization classes, objective combinations,
role ownership, retirement effects, and successor bindings. Generated output owns
registry initialization, role wrappers, name dispatch, retirement and succession
dispatch, and person-only native raid definitions.

## Physical truth and country beliefs

Global person state is physical truth. It records lifecycle, actual host and state,
affiliation, serving role, custody, detention state, protection country, lifetime
attempts, removal credit, pressure, and historical fallback eligibility. A person
can be active, captured, killed, retired, or prosecuted. Death, capture, retirement,
and prosecution cannot be undone by a later role-activation check.

Each country owns its beliefs about a person:

| Axis            | Meaning                                                                        | Routine decay   |
| --------------- | ------------------------------------------------------------------------------ | --------------- |
| Identity        | Confidence that the named person and registered role are correctly identified. | None            |
| Location        | Confidence in the believed state and host.                                     | 5 every 28 days |
| Pattern of life | Confidence in routine, protection, operational window, and civilian exposure.  | 3 every 28 days |

Each country also owns the believed state and host, lead age, package state,
collection focus, reports, and immutable review and operation snapshots. The old
scalar `TOP_confidence` is compatibility and display state only. It is not the
authority or resolution source of truth.

Global organization truth records activation, class, actual host and operating
state, pressure, disruption type and expiry, and an optional Counter-Terror mapping.
Country beliefs use verification, facility location, and activity window axes plus
believed state and host, lead age, package state, collection focus, mandates, and
liaison metadata. Organizations can be disrupted but cannot be killed or captured.

## Discovery, dossiers, and packages

Newly discovered nonpublic people and militant organizations start at `15 / 15 / 0`.
Serving public political leaders, public state-security officials, and public
organizations start at `100 / 0 / 0`. Public identity does not imply an actionable
location or operating pattern.

A lead becomes stale at 57 days. Only location-focused collection refreshes lead
age. Standard readiness requires all three axes at least 60, a believed state and
host, and a fresh lead. Enhanced readiness requires all three axes at least 80 with
the same location and freshness requirements. Serving political leaders always
require an enhanced package. Readiness is derived and is not stored as a second flag.

A human country has:

- unlimited discovered Cold dossiers;
- unlimited paused or ready packages;
- three simultaneous focused collection assignments;
- one preparation or execution slot.

Creating a package costs 25 Political Power once. Pausing frees its collection slot
without losing knowledge. Resuming the same package is free. Abandoning clears its
package state but preserves the Cold dossier and all accumulated belief values.
Several people and organizations in the same host may have packages at once.

Each collecting package focuses on identity or verification, location, or pattern
or activity. A collection pulse applies the full clamped gain, initially 2 through
25, to the selected axis and 25 percent to each other axis. Counter-Terror knowledge,
infiltration, agencies, decryption, liaison, access, disruption, pressure, national
security policy, and VIP protection modify collection through shared resolvers.
La Resistance is not required for the baseline path.

Normal movement can change global truth without changing an attacker's belief. A
prepared proposal does not follow a moving target. A deceptive or false location
stays within the believed host and chooses another controlled state. If that host has
no alternate state, the report becomes unresolved instead of inventing an impossible
state.

## Organizations and facility objectives

Organization dossiers appear beside people and expose class, public identity,
belief axes, believed host and state, pressure, disruption, members, objectives,
collection state, authority blockers, liaison actions, and archive history. Registered
IRGC commanders appear independently as public Cold person dossiers with identity
100 and location and pattern zero.

Default facility objectives are:

| Class                 | Objectives                                                     |
| --------------------- | -------------------------------------------------------------- |
| Militant network      | Command/communications, training/logistics, funding/industrial |
| State security        | Command/communications, training/logistics, funding/industrial |
| Political executive   | Command/communications, funding/industrial                     |
| Civilian organization | Command/communications, funding/industrial                     |

An organization can override those defaults in the manifest. The chosen objective is
frozen when review begins. Facility packages use the organization's three belief
axes and the same collection slots as people. There is no persistent named-facility
registry.

A successful facility operation damages the recorded state and replaces the
organization's one active 90-day disruption:

| Objective              | Map result                                                                           | TOP result                                                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Command/communications | Damage one infrastructure level.                                                     | Add 5 collection gain against the organization and affiliated people.                                                          |
| Training/logistics     | Damage one military factory, or infrastructure if none exists.                       | Add 10 percentage points to success against the organization and its members.                                                  |
| Funding/industrial     | Damage one civilian factory, or apply 60 days of resource disruption if none exists. | Reduce effective protection and relocation by 5; apply the one-time Counter-Terror threat reduction when a mapped slot exists. |

The new disruption replaces the old type and refreshes its expiry. Effects do not
stack. Facility sabotage never changes a person's lifecycle.

## Review, authorization, and execution

The method, access category, and result family are:

| Method               | Subject      | Access                                                        | Result                          |
| -------------------- | ------------ | ------------------------------------------------------------- | ------------------------------- |
| Remote strike        | Person       | Stand-off reach                                               | Lethal                          |
| Direct-action raid   | Person       | Direct-action staging                                         | Capture or lethal native result |
| Covert assassination | Person       | Clandestine access                                            | Lethal                          |
| Rendition            | Person       | Clandestine access and custody route                          | Capture                         |
| Partner operation    | Person       | Cooperative partner access                                    | Capture with partner custody    |
| Facility sabotage    | Organization | Clandestine access                                            | Damage and disruption           |
| Poison/Novichok      | Person       | Clandestine access plus authored Russian and decryption gates | Lethal                          |

A plausible route is required to open review. Exact access is revalidated at senior
approval and at preparation. Native raids retain final authority over equipment,
basing, range, DLC, and launch feasibility.

Review snapshots subject kind and ID, sequence, method, objective, all three belief
axes, lead age, believed state and host, access, host posture, doctrine, capability,
review rigor, harm inputs, and exposure inputs. Proposals expire after 42 days.
Selection, collection, decay, or movement cannot rewrite the snapshot. Lifecycle,
authority, controller, capability, access, role, and doctrine changes fail closed.

Host posture is unconsulted, intelligence-only, tolerated, cooperative, or refused.
Only cooperative posture permits a partner operation. Intelligence-only help closes
the proposal without consuming a mandate and adds 20 location plus 5 to each other
axis. Refusal returns the package, increases pressure, and can identify the actor
privately without creating public attribution.

Restrictive, Standard, Expanded, and Delegated doctrine set approval cost, mandate
length, consultation procedure, and risk adjustment. Delegated doctrine bypasses
staff and host consultation for nonleaders and enters senior review directly.
Political leaders always retain the full review path. A serving political leader's
lethal case then opens a dedicated page titled `Assassination` with the final action
`Authorize Assassination`. Capture feasibility is a warning and consequence input,
not a veto.

Approval creates a waiting mandate. It does not reserve operational capacity. The
explicit Begin Preparation or Begin Operation action revalidates the immutable case,
reserves the one operation slot, and either exposes the native raid or starts a
28-day timed mission. BDA pending releases the slot. TOP Stand Down closes a prepared
native case and releases capacity. An identical still-valid mandate can reuse its
prepared native instance. Retired native tuples prevent a late callback from binding
to a later case.

See [authorization](targeted-operations-authorization.md) and
[case storage](targeted-operations-cases.md) for the detailed contracts.

## Resolution, reports, and archive

Each operation draws one 1 through 100 intelligence roll and compares it with all
three frozen axes. Identity failure prevents positive identification. Location
failure or movement produces no contact or wrong location. Pattern or activity
failure produces a compromised window, escape, partial result, or elevated harm.
Passing all three allows tactical resolution. Native raids then use their engine
result. Timed methods use the shared tiered resolver.

Physical results are aborted, no contact, escaped, failed, partial, captured, killed,
or facility damaged. Physical truth resolves exactly once. Capture is immediately
confirmed. Lethal operations enter a 14-day BDA period, but BDA only changes report
certainty and never rerolls death or survival.

Attribution has four levels: unattributed, suspected, credible, and confirmed/public.
The immediate exposure roll sets the initial tier. The 14-day investigation may add
at most one tier and can never reduce it. Civilian harm is none, limited, severe, or
durable. Ordinary harm risk is capped at 40 before its qualitative band is shown.
Civilian harm magnifies consequences only after attribution exists.

The archive is a 128-row typed circular record. It stores subject kind and stable ID,
method, facility objective, state, host, frozen intelligence, lead age, access, host
posture, doctrine, rigor, physical result, BDA, attribution, harm, custody or
disposition, date, and sequence. Changing selection cannot rewrite an archive row.

## Leader removal, custody, crises, and oversight

Killing or capturing a serving registered leader changes physical truth immediately,
retires the exact authored identity, selects an authored successor before a generated
fallback, and invokes the country-specific leadership hook. Succession does not wait
for the attacker's BDA report. A vacancy is allowed only after valid successors are
exhausted.

Every serving head-of-state or head-of-government kill or capture is crisis-eligible.
Credible attribution opens a strategic crisis. Confirmed/public attribution unlocks
the strongest choices. War-risk choices appear only for a major power, nuclear state,
alliance member, or authored tripwire. War is never automatic. The victim, attacker,
host, faction partners, and guarantors receive contextual choices. Leader capture
uses the capture and custody context rather than pretending it was an assassination.

Capture creates immediate global custody. One lifetime exploitation action can:

- add 20 balanced intelligence to up to two active affiliated people with the lowest
  current knowledge;
- add 25 to all three organization axes and refresh its believed location; or
- refresh command/communications disruption for 90 days without map damage.

The custodian may detain, prosecute, transfer, negotiate an authored exchange, or
release. There is no generic prisoner-execution action. Prosecution permanently
removes the person from ordinary operations. Release clears actionable location and
raises person and organization pressure.

Credibly attributed political operations, severe or durable harm, leader capture,
and compromised actor-identifying operations open oversight. Democratic governments
choose disclose, contain, or suppress. Security states choose internal review,
scapegoat, or purge. Suppression can increase the later attribution investigation.
Oversight decisions modify the shared case consequence record. A typed queue
serializes simultaneous oversight events so one case cannot overwrite another.

## Protection, pressure, deception, and liaison

National protection and counterintelligence policies remain independent 182-day
defensive systems. Eligible defenders can use them even when they cannot initiate
TOP. Individual VIP details cover serving political leaders, state-security officials,
and authored civilian public figures. Capacity starts at two, gains one slot from
each of two encryption progressions, and is capped at four. Each 91-day detail costs
25 Political Power and 0.25 billion treasury and applies collection, success, and
exposure modifiers through the centralized defensive resolver.

Person and organization pressure are separate 0 through 100 values. Detected
collection adds 5, detected review or host approach adds 10, detected preparation
adds 20, and a completed attempt adds 35. Pressure decays by 5 every 28 days when
left alone. A member uses direct pressure plus half organization pressure, capped at 100. Person activity also passes one quarter of its increase to the organization.

Thresholds at 25, 50, and 75 change movement, protection, travel, hardening, and false
location behavior and fire only once per threshold entry. Warnings progress from
unknown interest to likely foreign service to likely actor without exposing a package,
objective, method, or date. A 91-day deception response costs 25 Political Power and
0.25 billion and adds 25 points to false-state chance after detected location work.

Liaison sharing sends one dossier snapshot, never live synchronization. It transfers
belief axes, believed state and host, lead age, report date, subject identity, and
source reliability. It does not transfer authority, doctrine, package ownership,
method, preparation, custody, or source identities. Trusted, mixed, and suspect
sources apply 100, 75, and 50 percent of supplied values. Merges only improve an axis,
and a location report replaces local belief only when newer or stronger. AI partners
may accept, partially share, refuse, or deceive, but sharing never authorizes AI
offense.

See [defensive systems](targeted-operations-security.md) for details.

## Existing-content interfaces

Content integrations must call public effects instead of writing dossier arrays:

- `TOP_add_target_lead`
- `TOP_grant_target_mandate`
- `TOP_add_organization_lead`
- `TOP_grant_group_mandate`
- shared kill, capture, release, transfer, retirement, report, and archive effects

`TOP_add_target_lead` adds the supplied amount to identity, location, and pattern,
clamps each at 100, refreshes belief location and lead age, and reveals the affiliated
organization when applicable. OEF, Iraq, ISIS, Soleimani, political-roster, and
annual-opportunity content uses these adapters or its documented Off-mode fallback.

STALKER Zone crises reach TOP through `STALKER_check_top_zone_crisis`, which reads a
state ID in `STALKER_top_state` and sets `STALKER_top_zone_crisis`. A Zone is in crisis
during an emission, below 30 containment, or above 79 activity. Proposal risks take -15
exposure and +10 harm before their caps. Resolution adds 10 to the intelligence roll,
clamped at 100, and 10 to the tactical or facility chance. Harnesses stub the hook to 0.

After a person is captured or killed, or a facility is damaged, in an active Zone, STALKER_apply_top_zone_disturbance adds 10 activity and removes 10 containment, then clamps the state values and refreshes the controller Zone Administration modifier. No-contact, wrong-location, failed-sabotage, inactive-state, and scenario-off results leave the Zone unchanged. The consequence runs only on the one-time physical result path, so delayed attribution updates cannot apply it again and TOP frozen case snapshot remains intact.
Organizations 35 to 37 are the Monolith, the Zone artifact smugglers, and SIRCAA. They sit in
the original Zone's anchor state (698) and activate only while that Zone is active; SIRCAA also
waits for the Ward. A damaged facility then calls STALKER_apply_top_organization_sabotage:
the Monolith loses 15 influence, the smugglers cost the bandits 10 and add 5 containment, and
SIRCAA's Ward loses 10.
The Package tab appends `[STALKER_top_package_zone_crisis]`, which names the crisis
when the selected subject's believed lead state holds one.

## Operations-center interface

The existing Counter-Terror screen retains an explicit Dossiers entry. The operations
center is a 1040 by 700 two-pane window sized to fit 1280 by 720 while remaining usable
at 1366 by 768 and 1920 by 1080. The left side is a persistent combined list. The
right side shows the selected subject.

Filters are Active, Cold, All, People, and Organizations. Tabs are Dossier, Package,
Authority, Custody, Archive, and Security. Organization rows identify class and expose
members and facilities. Person rows identify office and affiliation. Custody controls
are unavailable for organizations, and facility controls are unavailable for people.

Blockers are presented in this order: inactive subject, undeveloped package, full
collection capacity, low axis, stale lead, unavailable authority, missing access,
open review, pending host response, expired mandate, occupied operation slot, and
missing capability or equipment. Exact facts and modifiers are shown. Final harm,
attribution, and escalation chances are shown only as qualitative bands.

## Test tooling and evidence boundaries

The focused audit entry point is:

```text
python tools/analysis/targeted_operations_audit.py
```

It runs the registry generator in `--check` mode and every
`tools/tests/targeted_operations*_test.py` module with a repository-local pytest
temporary directory. Use it during iteration and in bug reports. Because the
generator and Python tooling change in this redesign, also run the complete suite
before merge:

```text
python -m pytest --basetemp .pytest_cache/full
```

Run pre-commit only for changed paths. Do not use `pre-commit run --all-files`, and
do not substitute the repository's full content-validation pipeline for PR CI.

Evidence must be reported separately:

1. Generator and static contract tests.
2. PR CI and content validation for the exact head SHA.
3. Console-assisted native-engine checks.
4. Visual screenshots at supported resolutions.
5. Natural-campaign behavior and balance.

A clean generator or Python suite does not prove native raid callbacks, equipment and
DLC launch gates, GUI rendering, save/reload, or campaign balance.

## Native-engine acceptance matrix

Use disposable fresh campaigns and record the checkout SHA, game version, mod
descriptor, DLC set, save, and whether setup was natural or console-assisted.

- Modes: Off hides TOP but preserves legacy fallbacks; Limited shows public leader
  and IRGC dossiers with restricted authority; Full completes a registered foreign
  civilian-leader assassination through the full pipeline.
- IRGC: open commander and organization packages together, execute all three facility
  objectives, verify map damage, 90-day replacement disruption, archive data, and no
  person lifecycle change.
- Concurrency: collect two people and one organization in one host, approve several
  waiting mandates, reserve the single execution slot, and verify BDA releases it.
- Leader operations: exercise kill, capture, no contact, and escape in separate saves;
  verify explicit assassination wording, enhanced thresholds, succession, distinct
  capture crisis, attribution gates, and no historical resurrection.
- Native raids: prepare, launch, Stand Down, renew, and deliver callbacks under all
  supported DLC combinations; verify old callbacks cannot bind to later cases.
- Defense: cross all pressure thresholds, assign and renew VIP details, fund deception,
  and verify a wrong state never reveals physical truth.
- Liaison: test trusted, mixed, suspect, refusing, and deceptive sources and a partner
  capture whose physical partner initially holds custody.
- Custody and crises: exercise each exploitation and disposition; confirm exploitation
  cannot repeat, ordinary operations cannot jump directly to war, and strategic war
  remains a confirmed-attribution choice.
- Persistence and layout: save and reload during collection, review, host response,
  waiting mandate, native preparation, timed mission, BDA, exploitation, doctrine
  cooldown, VIP detail, and crisis; inspect every filter and tab with long names at
  1280 by 720, 1366 by 768, and 1920 by 1080.
