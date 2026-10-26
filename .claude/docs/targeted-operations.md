# Targeted Operations

Targeted Operations is a persistent intelligence, authorization, operations, and
consequences system for registered people and organizations. Full Sandbox includes
genuine assassination operations against registered foreign civilian political
leaders. State-security organizations such as the IRGC are first-class subjects and
do not require a Counter-Terror organization slot.

This document is the canonical implementation contract. Development saves are not
supported across schema changes.

## Contents

- [Game modes and offensive ownership](#game-modes-and-offensive-ownership)
- [Registry and stable identity](#registry-and-stable-identity)
- [Physical truth and country beliefs](#physical-truth-and-country-beliefs)
- [Discovery, dossiers, and packages](#discovery-dossiers-and-packages)
- [Organizations and facility objectives](#organizations-and-facility-objectives)
- [Authorization contracts](#authorization-contracts)
- [Typed cases and lifecycle](#typed-cases-and-lifecycle)
- [Defensive systems and liaison](#defensive-systems-and-liaison)
- [Existing-content interfaces](#existing-content-interfaces)
- [Operations-center interface](#operations-center-interface)
- [Test tooling and evidence boundaries](#test-tooling-and-evidence-boundaries)
- [Native-engine acceptance matrix](#native-engine-acceptance-matrix)

## Game modes and offensive ownership

The `TOP_game_rule` game rule has three modes:

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
IDs 65 through 128, and 34 organization records. Zero is reserved. Organizations
remain in their own registry and never consume a person ID.

The four organization classes are:

- `militant_network`
- `state_security`
- `political_executive`
- `civilian_organization`

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

## Authorization contracts

Authorization is an immutable, player-only state machine. A visible dossier is not
authority, an approved mandate is not an operation in progress, and Full Sandbox does
not bypass intelligence, access, review, preparation, attribution, succession, or
strategic consequences.

### Eligibility boundary

The backend checks the game mode and subject class at every offensive entry point.
Limited Sandbox normally permits militants, requires war or a group or target mandate
for state-security subjects, and requires authored authority for political and civilian
subjects. Full Sandbox permits the normal pipeline for every registered foreign
subject. It does not permit generic domestic assassination. Domestic cases require a
civil war, coup, or explicit authored emergency route.

Relationships do not create immunity in Full Sandbox. Allies, faction partners,
guaranteed states, and friendly governments instead affect access, host posture,
exposure, and consequences.

`TOP_human_offense` is required by designation, review, approval, preparation, native
raid exposure, and timed launch. A GUI omission is never relied on as the AI boundary.

### Readiness and methods

Ordinary person and organization review requires all three current belief axes at 60,
a believed state and host, and lead age below 57 days. A serving political leader
requires all three axes at 80. The review copies those values into its proposal. Later
collection or decay cannot improve or weaken the proposal.

Methods are encoded as:

| ID  | Method               | Subject      | Access category                        | Result family                      |
| --- | -------------------- | ------------ | -------------------------------------- | ---------------------------------- |
| 1   | Remote strike        | Person       | Stand-off reach                        | Lethal native raid                 |
| 2   | Direct-action raid   | Person       | Direct-action staging                  | Native capture or lethal result    |
| 3   | Covert assassination | Person       | Clandestine access                     | Timed lethal result                |
| 4   | Rendition            | Person       | Clandestine access and custody route   | Timed capture                      |
| 5   | Partner operation    | Person       | Cooperative partner access             | Timed capture with partner custody |
| 6   | Facility sabotage    | Organization | Clandestine access                     | Damage and disruption              |
| 7   | Poison/Novichok      | Person       | Clandestine access plus authored gates | Timed lethal result                |

The Novichok route retains the authored Russian and decryption requirements. Method
overrides belong in the manifest only when an ordinary method is genuinely
nonsensical for that subject.

### Access and host posture

Access has two validations:

1. A plausible route is required to open review.
2. Exact access is rechecked at senior approval and at Begin Preparation or Begin
   Operation.

Loss of access after approval blocks launch but preserves the waiting mandate until
it expires. The system does not change targets or methods. Native raids retain final
authority over a suitable base, equipment, range, DLC, and engine preparation.

Host posture is frozen as one of:

- unconsulted;
- intelligence-only;
- tolerated;
- cooperative;
- refused.

Only cooperative posture permits a partner operation. Intelligence-only assistance
ends the proposal without consuming a mandate, returns the package to development,
adds 20 location and 5 to each other belief axis, and refreshes the location report.
Refusal returns the package, adds pressure, and may privately identify the actor. It
does not itself create public attribution or a strategic crisis.

Each host can hold one unresolved incoming request. Actor cancellation never rewrites
that request. A response must match actor, proposal sequence, subject kind, subject
ID, method, objective, state, and host before it can affect a proposal.

### Immutable proposal

`TOP_begin_review` and `TOP_begin_organization_review` record:

- subject kind and stable ID;
- country-owned proposal and case sequence;
- method and facility objective;
- identity or verification, location, and pattern or activity;
- lead age, believed state, and believed host;
- access category and host posture;
- doctrine and review rigor;
- capability, harm, exposure, and capture-feasibility inputs;
- a 42-day expiry.

One actor review dialog can be open at a time. Any number of developed packages and
approved waiting mandates can exist. Cancelling, rejecting, expiring, or invalidating
a proposal returns its unchanged package. It does not erase intelligence or charge
approval Political Power.

The review fails closed when status, serving role, operational eligibility, authority,
controller, capability, access, doctrine, case sequence, or lifecycle no longer
matches. The current GUI selection is not part of validation.

### Doctrine

Doctrine changes cost 100 Political Power and lock further changes for 365 days.
Restrictive and Standard are always available. Expanded requires an eligible
government family, war, or authored emergency. Delegated requires war, civil war, or
an authored override. Full Sandbox does not relax those institutional requirements.

| Doctrine    | Nonleader approval |  Mandate | Procedure                                               | Risk adjustment |
| ----------- | -----------------: | -------: | ------------------------------------------------------- | --------------: |
| Restrictive |              75 PP |  60 days | Cooperation or war is required                          |             -10 |
| Standard    |              50 PP |  91 days | Full normal review                                      |               0 |
| Expanded    |              40 PP | 120 days | Consultation is optional when independent access exists |              +5 |
| Delegated   |              25 PP | 182 days | Compressed nonleader review                             |             +10 |

Delegated nonleader cases skip staff and host consultation and enter senior review
directly. Organization facility cases count as nonleader cases. Political leaders
always follow the full procedure, regardless of doctrine.

A political-leader approval always costs 50 Political Power. Doctrine still supplies
mandate length, consultation constraints, and risk adjustment. Changing doctrine
invalidates an unfinished proposal whose procedure no longer matches. It never
changes a previously approved mandate.

### Review stages

Proposal stages are:

- **0, closed:** no active proposal;
- **1, staff review:** the immutable dossier is presented and checked;
- **2, host choice:** consultation, tolerated unilateral action, or the next review
  route is selected;
- **3, host response:** the matching host owns an unresolved request;
- **4, senior review:** cost, doctrine, access, capability, and frozen consequence
  inputs are shown and revalidated;
- **5, assassination confirmation:** a serving political leader's lethal case receives
  the dedicated final page.

The dedicated page is explicitly titled `Assassination`. Its final button is
`Authorize Assassination`, and the selected method remains visible underneath. It
shows the target's office, frozen intelligence, access route, host posture, succession
warning, attribution band, civilian-harm band, and strategic-escalation band. Capture
feasibility produces a prominent warning and modifies consequences. It does not veto
lethal authorization.

Every political target must have deterministic retirement and a valid authored or
generated successor fallback before lethal authorization is exposed. The generator
enforces that contract.

### Approval and operational capacity

Approval creates a phase-2 waiting mandate. It copies the immutable proposal into
person or organization case arrays and charges approval cost once. It does not occupy
the operation slot and does not create a native raid or timed mission.

Begin Preparation or Begin Operation:

- revalidates subject kind, ID, sequence, status, role, authority, state, host,
  access, method, objective, doctrine, and capability;
- requires the country's one operation slot to be free;
- reserves that slot with subject kind, ID, sequence, state, host, method, and
  objective;
- exposes the exact native raid or starts a 28-day timed operation.

BDA pending releases the operation slot. Waiting mandates remain intact while another
case executes. Access loss blocks launch without changing the case. Expiry closes an
unused waiting mandate and preserves the underlying dossier.

For native raids, TOP Stand Down releases the slot and closes the prepared case.
Engine-side map cancellation cannot be authoritative because HOI4 exposes no safe
cancellation callback. Reopening an identical still-valid mandate may reuse its
prepared native instance. Once a native tuple is retired, a late callback for it
cannot attach to a new operation.

### Resolution and consequence inputs

Authorization does not decide physical success. Resolution uses one intelligence roll
against all three frozen axes, followed by native or timed tactical resolution only
when the intelligence gates permit it.

The proposal freezes the inputs used to explain:

- operational success modifiers;
- attribution exposure;
- civilian-harm risk;
- capture feasibility;
- host cooperation;
- doctrine and review rigor;
- strategic escalation.

Exact inputs and adjustments can be shown. Final probability is shown as Low below
20, Moderate from 20 through 39, High from 40 through 59, and Extreme at 60 or more.
Ordinary civilian-harm risk is capped at 40. An authored strategic incident may
override that cap.

### Callback and event safety

Actor event slots remain reserved until their own option is consumed. Timeout closes
the proposal but retains enough identity to make a stale callback harmless. A host
response cannot approve a different or later proposal.

Native callbacks are person-only. The generated raid carries person and method, while
the callback validates actor, person, method, state, case sequence, and prepared
binding. The operation slot also records typed identity. Organization cases never use
native raid callbacks.

Oversight is not a second outcome system. Consequence triggers add a typed person or
organization key to `TOP_oversight_queue`. Only one country-level oversight subject
is dispatched at a time. Resolving it updates that case's shared consequence record,
clears the pointer, and dispatches the next queued case.

### Acceptance scenarios

- Open standard, enhanced, and leader packages at exactly their thresholds. Repeat
  with a 57-day lead and confirm it is stale.
- Reselect another dossier at every review stage. Confirm only the recorded subject,
  method, objective, state, host, and sequence can be approved.
- Run Restrictive with cooperation and war, Expanded with and without consultation,
  and Delegated against a nonleader, an organization, and a political leader.
- Verify Delegated skips directly to senior review for the first two but preserves the
  full leader path and assassination confirmation for the third.
- Accept intelligence-only help, tolerate unilateral action, cooperate, refuse, and
  leave a host request unanswered. Confirm package, pressure, and mandate behavior.
- Approve several waiting mandates, begin one, and verify every other launch is
  blocked without losing its mandate or package.
- Remove access after approval, restore it before expiry, and confirm the exact case
  resumes without retargeting.
- Cancel and renew a native raid, Stand Down through TOP, deliver a retired callback,
  and repeat under all supported DLC combinations.
- Save and reload during every proposal stage, host response, waiting mandate, native
  preparation, timed operation, and BDA.

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

## Typed cases and lifecycle

Person and organization cases have separate storage. A subject is always identified
by both kind and stable ID. Organization IDs are never placed in person arrays, and
native raid callbacks remain person-only.

### Dossiers and packages

Dossier knowledge is country-owned and persists independently of a case. A Cold
dossier can exist without a package. A package can be paused, collecting, ready, in
review, or waiting behind authority without changing physical truth.

`TOP_package_state` and `TOP_org_package_state` encode package lifecycle. The shared
`TOP_collecting_subjects` array uses a typed key: person IDs are stored directly and
organization IDs are stored with an offset of 1000. This supports three simultaneous
focused assignments across either kind without conflating their registries.

Creating a package charges 25 Political Power once. Pause and resume do not charge.
Abandonment clears package state and removes the collection key, but it does not clear
belief axes, believed location, reports, or dossier visibility.

### Person cases

`TOP_case_*` arrays are indexed by permanent person ID. They record:

- host and state;
- method and sequence;
- mandate expiry and mission due date;
- phase and consent;
- frozen identity, location, pattern, and lead age;
- access, host posture, doctrine, rigor, and capability;
- protection country, attribution, harm, result, and BDA;
- archive row and token;
- oversight and crisis state;
- visit binding for authored state-visit operations.

Person phases are:

- **0:** closed;
- **1:** immutable review case;
- **2:** approved waiting mandate;
- **3:** preparation or operation in progress;
- **4:** physical result recorded and BDA pending;
- **5:** report ready for closure and archive access.

`TOP_active_cases` may contain several people in the same host. There is no
one-person-per-country exclusion. `TOP_case_counter` assigns a monotonically
increasing sequence. Every review, preparation, operation, callback, archive write,
and close action rechecks the relevant sequence.

`TOP_close_case` accepts an explicit person and sequence and closes only that
generation. A current GUI selection cannot redirect it. Physical status and dossier
beliefs remain outside the case and are not erased by closure.

### Organization cases

`TOP_org_case_*` arrays are indexed by stable organization ID. They record host,
state, selected facility objective, sequence, mandate and operation timing, frozen
verification, location, activity, lead age, access, posture, doctrine, rigor,
capability, attribution, harm, result, archive binding, and oversight.

Organization phases mirror person phases where meaningful:

- **0:** closed;
- **1:** immutable facility review;
- **2:** approved waiting mandate;
- **3:** timed facility operation in progress;
- **4:** resolved result and attribution processing;
- **5:** report and archive ready.

Organizations do not have killed, captured, retired, custody, prosecution, or
succession phases. A facility result can damage a state and replace a timed disruption
but cannot modify any person's lifecycle.

### One operation slot

Approval does not reserve capacity. `TOP_operation_subject_kind`,
`TOP_operation_subject_id`, and `TOP_operation_sequence` are the authoritative
country operation binding. Kind zero is free, one is a person, and two is an
organization. The binding is created only by Begin Preparation or Begin Operation.

While the slot is occupied, other packages can collect, reviews can proceed, and
mandates can wait. Launch validation refuses a second operation without changing the
blocked case. The slot is released when a timed or native physical result enters BDA,
or when the player uses TOP Stand Down on a prepared native case.

Flat `TOP_authorized_*`, `TOP_pending_*`, and `TOP_proposal_*` values are display and
execution snapshots. They do not grant authority. Only the matching typed case arrays
and operation binding do.

### Movement and wrong-location behavior

Global movement changes physical truth only. It does not rewrite beliefs, proposals,
or prepared cases. At resolution, one intelligence roll is compared with all three
frozen axes and the recorded location is compared with physical truth.

A wrong-location or no-contact outcome:

- consumes the operational mandate;
- preserves the package and identity or verification knowledge;
- sets location or facility-location confidence to zero;
- reduces pattern or activity by 15;
- returns the package to development;
- records the attempted subject, method, state, host, and sequence;
- never retargets or changes method.

False-state reports remain in the believed host. If no alternate controlled state
exists, there is nothing false to plant and the real lead stands.

### Native callback constraint

The HOI4 raid callback exposes actor, target state, and the generated raid definition,
but it does not expose a safe arbitrary per-instance numeric token. Generated TOP
raids therefore carry a permanent person and method. Launch and callback validate the
country's person, method, state, sequence, phase, and operation binding.

Renewing an identical still-open waiting mandate can preserve its prepared native
instance. Native map cancellation is not treated as closure because no reliable
cancellation callback exists. TOP Stand Down is the authoritative release action.

Once a native case closes, its person, method, and state tuple enters
`TOP_retired_native_bindings`. A late callback for that tuple cannot be accepted by a
new case. The tuple key remains `person * 20000 + state * 2 + method` for person IDs,
states 1 through 9999, and native methods 1 and 2. Retired tuples are never discarded
to make a stale callback valid.

### Physical truth, BDA, and attribution

Resolution changes global person lifecycle or organization disruption exactly once.
Capture is immediately confirmed and creates global custody. Lethal person results
store physical truth immediately, release operation capacity, and schedule 14-day
BDA. BDA may change report wording or certainty based on frozen identity confidence.
It cannot call kill or capture again.

The initial exposure roll stores attribution from zero through three. A separate
14-day investigation may raise it by one tier at most. It can never lower attribution
or create a new physical result. Suppressive oversight modifies the investigation
chance on the same case record.

Visit and political-roster events, and any historical event bridged to TOP, consult
global truth before applying their fallbacks. They cannot kill, capture, retire,
reward, or replace the same identity twice.

### Archive

The country archive is a 128-row circular array. Every row stores typed identity,
objective, method, state, host, frozen intelligence, lead age, access, posture,
doctrine, rigor, physical result, BDA, attribution, harm, custodian or disposition,
date, and sequence.

The row is written from the case snapshot, not the current selection. BDA updates the
matching row through its archive token. Rollover reuses the oldest cursor row only
after removing its prior row reference. Person and organization cases both use the
same typed archive format.

### Oversight queue

Several cases can become oversight-eligible before the player answers the first
event. Each case sets its own pending value and appends a typed key to
`TOP_oversight_queue`. The country-level dispatcher only assigns
`TOP_oversight_subject_kind` and `TOP_oversight_subject_id` when no oversight event is
already active.

Resolving the event writes the selected response to the matching person or
organization case, clears that case's open value, clears the country pointer, and
immediately dispatches the next key. This prevents an operation finishing on the
same day from overwriting another event's subject.

### Acceptance beyond static tests

- Collect two people and one organization in the same host, fill all three slots,
  and save and reload.
- Approve several mandates and verify none occupies the operation slot until Begin
  Preparation or Begin Operation.
- Launch one case and confirm every other launch is blocked without package or
  mandate loss. Confirm BDA pending frees capacity.
- Change selection during review, preparation, operation, BDA, and archive browsing.
  Every callback and report must retain its recorded subject and sequence.
- Move the target after review. Exercise no contact, wrong state, escape, partial,
  capture, kill, and facility damage in separate saves.
- Cancel and renew a native raid through TOP, then deliver an old callback after a
  later case exists. The old tuple must not attach.
- Resolve two oversight-eligible operations close together. The second event must
  retain its own subject after the first response.
- Save and reload in each person and organization phase and at archive rollover.

Static tests do not establish native callback timing, DLC availability, rendering,
or save serialization. Record those as separate runtime evidence.

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

## Defensive systems and liaison

Defensive TOP systems remain available to eligible countries even when the country
cannot initiate an operation. AI countries may use these defensive, host, liaison,
custody, attribution, and crisis systems, but never cross into the offensive pipeline.

### National security policies

Protection and counterintelligence are independent 182-day national policies.

| Tier        | Political Power | Treasury, bn | Protection | Collection | Exposure |
| ----------- | --------------: | -----------: | ---------: | ---------: | -------: |
| Basic       |              25 |         0.25 |          5 |          3 |        5 |
| Reinforced  |              40 |         0.75 |         10 |          6 |       10 |
| Exceptional |              60 |         1.50 |         15 |          9 |       15 |

Protection subtracts percentage points from timed success. A native raid instead has
the tier's percentage chance to reduce a nonfailure result by one tier because the
callback exposes the engine result rather than its internal chance. Counterintelligence
subtracts from attacker collection and adds to exposure.

A purchase replaces that track's tier and expiry. It does not stack or bank unused
days. Both tracks charge once through the treasury effect after checking eligibility,
controlled territory, Political Power, and cash. Standing down clears both without a
refund. Expired values are ignored because every read requires expiry after the
current TOP clock.

`TOP_security_country_tick` may maintain AI defensive policies. It does not call any
offensive effect. A country with an authored protected official can buy defense even
when `TOP_country_eligible` is false.

### Central defensive resolver

`TOP_get_defensive_modifiers` is called in attacker scope with a recorded person in
`TOP_target`. It resets and returns:

- `TOP_defensive_collection_penalty`;
- `TOP_defensive_success_penalty`;
- `TOP_defensive_exposure_bonus`.

The roster's protection-country dispatcher supplies the defender. Presence in a
country does not itself grant official protection. Militants do not inherit a host's
VIP defense. Retired, detained, prosecuted, and dead people do not keep stale serving
protection.

The resolver centralizes national policy, individual VIP detail, person pressure,
organization-pressure spillover, and active organization disruption before clamping
each output. Authorization does not freeze later defensive spending. The operation
samples defense again when the attempt resolves.

### Individual VIP details

Eligible subjects are:

- serving political leaders;
- serving state-security officials;
- authored civilian public figures.

Militants and inactive former officeholders are ineligible. Capacity starts at two,
gains one slot from the existing passive-defense or early advanced-encryption
progression, gains another from later advanced cryptography or encryption, and is
capped at four.

Each assignment costs 25 Political Power and 0.25 billion treasury, lasts 91 days,
and applies:

- 3 points less attacker collection;
- 10 percentage points less operation success;
- 5 points more exposure.

The detail stacks with national policy only through the centralized resolver. Renewal
or reassignment replaces the remaining term without refund. Expired assignments free
capacity on the security tick.

### Person and organization pressure

Person and organization pressure are separate 0 through 100 values.

| Activity                         | Pressure gain |
| -------------------------------- | ------------: |
| Detected collection              |             5 |
| Detected review or host approach |            10 |
| Detected preparation             |            20 |
| Completed attempt                |            35 |
| 28 days left alone               |            -5 |

A person's effective pressure is direct person pressure plus 50 percent of affiliated
organization pressure, capped at 100. A direct person increase also adds 25 percent
of that increase to the organization.

Thresholds at 25, 50, and 75 apply automatic behavior and fire one defender event on
first entry into each tier. Falling below and later crossing a threshold does not spam
an already recorded notice.

Militants relocate more often as pressure rises. Officials and public figures tighten
protection and reduce travel. The highest tier blocks ordinary authored travel
opportunities. State-security organizations harden facilities and increase false
location risk.

### Detection, warning, and deception

Counterintelligence warnings reveal only an escalating actor assessment:

1. unknown foreign interest;
2. likely foreign service;
3. likely actor.

Warnings never reveal the exact person package, organization objective, method,
review stage, or scheduled date.

A likely actor permits private warnings, personnel expulsion, access cuts, or subject
hardening. That defensive actor assessment is not operation attribution and cannot
open a public strategic crisis by itself.

A defender can fund a deception response for 25 Political Power and 0.25 billion.
It lasts 91 days and adds 25 points to the chance that detected location collection
produces a wrong state in the correct host. If the host has no other controlled state,
the result becomes unresolved. Deception never writes or reveals physical truth.

### Liaison snapshots

Liaison sharing transfers a one-time country-owned snapshot. It never synchronizes
dossiers after delivery.

The snapshot contains:

- all three person or organization belief axes;
- believed state and host;
- lead age and report date;
- typed subject identity;
- source reliability.

It never transfers authorization, doctrine, methods, package ownership, operation
preparation, custody rights, or hidden source identities.

A request costs 25 Political Power and creates a 91-day subject-and-country-pair
cooldown. A valid relationship is a shared faction, subject relationship, cooperative
host relationship, intelligence partnership, or opinion of at least 50.

Reliability applies:

| Reliability | Supplied value used | Initial leak chance |
| ----------- | ------------------: | ------------------: |
| Trusted     |         100 percent |          10 percent |
| Mixed       |          75 percent |          25 percent |
| Suspect     |          50 percent |          40 percent |

The merge is non-destructive. An axis changes only when adjusted incoming knowledge
is higher. Believed location changes only when the incoming report is newer or
stronger. A deceptive source can provide a false state in the correct host. A leak
adds 10 pressure and gives the defender a vague warning.

AI countries may accept, partially share, refuse, or deceive. Receiving or sharing a
dossier never grants AI operational authority.

### Organization disruptions

Only one disruption type can be active for an organization. A later facility success
replaces the type and refreshes the 90-day expiry.

- Command/communications adds 5 collection gain against the organization and members.
- Training/logistics adds 10 percentage points to success against the organization
  and members.
- Funding/industrial reduces effective protection and relocation chance by 5.

The funding objective retains the one-time 3-point Counter-Terror threat reduction
when the organization has a current mapped CT slot. Missing `ct_id` is valid and does
not block the disruption or any other TOP organization behavior.

### Strategic-crisis support

A credibly attributed operation against a serving head of state or government can
notify the victim, attacker, physical host, faction partners, and victim guarantors.
Support consultations are one-time events for the current crisis token. Participants
may sanction the actor, reinforce the victim, share defensive intelligence, pressure
the actor, mediate, or abstain.

Support choices can change tension, opinion, Political Power, war support, or the
victim's defensive intelligence. They cannot directly declare war. Only the victim's
confirmed-attribution strategic-tripwire route can expose the one restricted war
choice, and that choice remains optional.

### Interface

Security remains a tab in the operations center and retains the existing
Counter-Terror entry point. It shows national policy, VIP assignments, capacity,
pressure, disruption, deception, warnings, and liaison actions for the selected
subject. Organization rows do not expose custody controls. Inactive former officials
do not expose VIP assignment.

The existing small sponsored-parody label has no external link or gameplay effect.
Its tooltip must continue to identify it as an in-game parody and disclaim actual
sponsorship, endorsement, or affiliation.

### Test and runtime acceptance

`python tools/analysis/targeted_operations_audit.py` checks national policy
independence, human-only offense, VIP capacity and cost, pressure increments and
spillover, threshold notices, deception, liaison cooldown and reliability, defensive
merge behavior, organization disruption replacement, and strategic-crisis support
dispatch.

Runtime acceptance must separately verify:

- each policy and VIP button's cost and tooltip;
- policy, detail, pressure, deception, and liaison persistence across save and reload;
- each pressure threshold for a militant, official, public figure, and state-security
  organization;
- anonymous, likely-service, and likely-actor warnings without secret detail leakage;
- a deceptive wrong-state report that remains in the correct host;
- trusted, mixed, suspect, refusing, and deceptive liaison partners;
- simultaneous national policy and VIP effects through one clamped resolver;
- faction-partner and guarantor crisis consultations without automatic war;
- layout at 1280 by 720, 1366 by 768, and 1920 by 1080.

Static fixtures do not establish rendering, native engine callbacks, or natural
campaign balance.

## Existing-content interfaces

Content integrations must call public effects instead of writing dossier arrays:

- `TOP_add_target_lead`
- `TOP_grant_target_mandate`
- `TOP_add_organization_lead`
- `TOP_grant_group_mandate`
- shared kill, capture, release, transfer, retirement, report, and archive effects

`TOP_add_target_lead` adds the supplied amount to identity, location, and pattern,
clamps each at 100, refreshes belief location and lead age, and reveals the affiliated
organization when applicable. The political roster and annual opportunities use these
adapters or their documented Off-mode fallback. Country event content that hands a
person or organization to TOP calls the same adapters.

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
