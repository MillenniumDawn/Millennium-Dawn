# Targeted Operations: Typed Cases and Lifecycle

Person and organization cases have separate storage. A subject is always identified
by both kind and stable ID. Organization IDs are never placed in person arrays, and
native raid callbacks remain person-only.

## Dossiers and packages

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

## Person cases

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

## Organization cases

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

## One operation slot

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

## Movement and wrong-location behavior

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

## Native callback constraint

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

## Physical truth, BDA, and attribution

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

## Archive

The country archive is a 128-row circular array. Every row stores typed identity,
objective, method, state, host, frozen intelligence, lead age, access, posture,
doctrine, rigor, physical result, BDA, attribution, harm, custodian or disposition,
date, and sequence.

The row is written from the case snapshot, not the current selection. BDA updates the
matching row through its archive token. Rollover reuses the oldest cursor row only
after removing its prior row reference. Person and organization cases both use the
same typed archive format.

## Oversight queue

Several cases can become oversight-eligible before the player answers the first
event. Each case sets its own pending value and appends a typed key to
`TOP_oversight_queue`. The country-level dispatcher only assigns
`TOP_oversight_subject_kind` and `TOP_oversight_subject_id` when no oversight event is
already active.

Resolving the event writes the selected response to the matching person or
organization case, clears that case's open value, clears the country pointer, and
immediately dispatches the next key. This prevents an operation finishing on the
same day from overwriting another event's subject.

## Acceptance beyond static tests

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
