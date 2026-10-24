# Targeted Operations: Authorization

Authorization is an immutable, player-only state machine. A visible dossier is not
authority, an approved mandate is not an operation in progress, and Full Sandbox does
not bypass intelligence, access, review, preparation, attribution, succession, or
strategic consequences.

## Eligibility boundary

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

## Readiness and methods

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

## Access and host posture

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

## Immutable proposal

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

## Doctrine

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

## Review stages

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

## Approval and operational capacity

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

## Resolution and consequence inputs

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

## Callback and event safety

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

## Acceptance scenarios

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
