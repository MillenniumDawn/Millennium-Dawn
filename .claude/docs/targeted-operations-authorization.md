# Targeted Operations: Authorization

This is a strategic game abstraction inspired by dated public policy documents. It does not
reproduce targeting techniques or claim that one historical United States policy applies to
every country, every conflict, or the current real world.

## Historical sources

- White House, 23 May 2013, [policy standards and procedures fact sheet][ppg]: describes
  capture preference, confidence about the target and civilian protection, consideration of
  other governments and alternatives, sovereignty, and senior interagency and legal review
  for operations outside the United States and areas of active hostilities. The game borrows
  those strategic review subjects, without treating an intelligence score as a legal finding.
- Department of Defense, 25 August 2022, [civilian harm action plan fact sheet][chmr]: describes
  institutional learning, reporting, assessment, and response. This supports separating
  authorization from the later recorded assessment of an operation.

Sources consulted 7 September 2026. These are historical references, not current-policy claims.

[ppg]: https://obamawhitehouse.archives.gov/the-press-office/2013/05/23/fact-sheet-us-policy-standards-and-procedures-use-force-counterterrorism/
[chmr]: https://www.defense.gov/News/Releases/Release/Article/3140007/civilian-harm-mitigation-and-response-action-plan-fact-sheet/

## Game contract

- `TOP_begin_review = { METHOD = N }` records the selected person, method, actionable state,
  controller, and an increasing country-owned proposal sequence. Methods are drone strike
  (1), capture raid (2), covert lethal action (3), rendition (4), partner detention (5), and
  sabotage (6). GUI selection changes never rewrite these fields.
- Stages are staff review (1), sovereignty choice (2), host response (3), and senior review
  (4). Stage zero is closed. The proposal expires after 42 game-clock days; the weekly pending
  actor pass also cancels it if intelligence, authority, capabilities, or state control fails.
- Standard review requires confidence and civilian assurance of at least 60. Enhanced review
  requires at least 80 in both and rejects lethal proposals with a feasible detention route,
  except the explicit authored domestic-civil-war emergency override. That override is a fictional
  campaign policy with its own crisis conditions and consequences, not a real legal exception.
  Western conservative, liberal, and social democratic governments use enhanced review;
  political targets always do. These are game balance choices, not national legal categories.
- Civilian assurance is an abstract staff assessment: nomination confidence minus one quarter
  of lead age, clamped to 0–100. Domestic jurisdiction, a friendly faction partner, or host
  opinion above 49 supplies a feasible detention alternative. These coarse diplomatic proxies
  are game rules, not a representation of real operational feasibility or civilian presence.
- Host consent is scoped to the immutable case. Refusal or an occupied host request slot does
  not authorize a partner operation. Other methods can reach a separate unilateral approval
  choice. A country-wide consent flag cannot replace the recorded case consent.
- `TOP_review_valid` checks the snapshot without requiring a particular UI selection.
  `TOP_review_can_approve` additionally requires the senior stage and staff criteria.
  `TOP_approve_review` calls `TOP_commit_reviewed_authorization` with the proposal intact.
  Core copies its snapshot into the matching per-person country case, charges 50 Political Power
  once, and handles the 91-day mandate or timed mission. Approval rechecks the reserved host slot
  and designation sequence. Other countries can have independent cases and operations. The event itself supplies no target-removal effect.
- SF technology is required for capture raids and rendition; covert lethal action requires
  decryption. Methods 3–6 require a foreign host, except method 3 under the explicit domestic
  civilian-emergency override. Native drone equipment and launch capability
  remain part of the native raid contract.
- Sabotage snapshots `TOP_selected_facility` as `TOP_proposal_facility`, clamped to 1–3:
  civilian industry, infrastructure, or resources. Review and final approval set
  `TOP_facility_state` and `TOP_facility_kind` for the core `TOP_facility_available` trigger.
  Changing the GUI facility selection never changes an already submitted proposal.

## Callback safety

Actor event slots remain reserved until their own option is consumed. Cancellation and timeout
close the proposal but retain an open-window tombstone. Closing the stale window releases it;
until then a new nomination is unavailable. The first option in each actor event closes or
defers the case, so unattended player dialogs do not implicitly approve an operation.

Each host has one request window backed by immutable actor, sequence, person, method, and state
fields. Only consuming that window releases the slot. Its reply must match all five fields and
an unexpired actor proposal waiting for consent. Actor cancellation does not overwrite the host
record. An old reply therefore cannot approve a later nomination, including an identical case.

A host with an unresolved window returns unavailable to other requests. Those actors can defer
or seek unilateral authorization. This avoids relying on undocumented event-local numeric
variables or replacing a record while an old popup still references it. Engine event delivery,
automatic dismissal, annexation, and save/reload need runtime acceptance; a dropped actor window
can keep its nomination slot reserved until the corresponding event is acknowledged.

## Acceptance scenarios

- Senior refusal, host refusal, busy host, cancellation, and timeout spend no Political Power.
  Returning the case to active collection pays its normal 25 Political Power collection cost.
- Reselect another dossier at every stage; approve only the recorded person and state.
- Cancel while awaiting consent, start another nomination, and answer the old host request.
  It cannot change the newer proposal; host slots are released only by their own response.
- Cancel or expire an open actor dialog. Its stale options cannot commit; acknowledgement
  restores nomination access. Save/reload both actor and host windows before responding.
- Change host controller, lead state, capability, target status, or political authority before
  approval. The case fails closed. Enhanced review rejects an available detention alternative.
- Approve each method with valid capabilities; partner action requires affirmative host
  consent. Confirm native raid launch remains separate and the final mandate records consent.

## Opportunities for 2024–2026

These are fictional intelligence opportunities shaped by contemporary strategic themes. They
do not inject historical attacks, force leadership changes, or establish real-world identities,
locations, survival, or deaths. Three annual effects advance `global.TOP_modern_year`:
`TOP_modern_opportunities_2024`, `TOP_modern_opportunities_2025`, and
`TOP_modern_opportunities_2026`. Each is idempotent and cannot move the marker backwards.
The opportunity window expires after 365 game-clock days, preventing a newly eligible country
in a later campaign year from receiving an obsolete 2026 report.

The existing staggered country pass calls `TOP_modern_country_opportunity` once when
`TOP_last_modern_year` trails the marker. It scans only that country's existing dossiers and
selects one known, living, active, nonpolitical person affiliated with groups 1–7. The score is
current dossier confidence plus the existing CT organization's threat level, with a 30-point
theme bonus: Islamic State in 2024; African networks in 2025; Al-Qaeda central or TTP in 2026.
If no person qualifies, that year's review produces no opportunity and no popup.

Delivery calls the shared lead effect for 25 intelligence points before creating any report.
Separate `TOP_modern_2024_target`, `TOP_modern_2025_target`, and `TOP_modern_2026_target`
snapshots keep reports independent. Notifications are pure flavor and are omitted for AI.
Their text names only an already-known person; exact states remain subject to the dossier's
confidence gate. No political mandate or operation authorization is granted.

Historical context, verified against primary UN reporting:

- [S/2024/556][un2024], 22 July 2024: regional and external threats, dispersed Islamic State
  activity, and continued counterterrorism pressure. This supports a broad network review.
- [S/2025/71/Rev.1][un2025], 6 February 2025: resilient, decentralized networks and increased
  attention to regional affiliates in Africa. No leadership identity claim is imported.
- [S/2026/44][un2026], 4 February 2026: persistent threats across regions, Al-Qaeda affiliate
  connections, and concerns about TTP. This informs the South Asian network emphasis.
- [S/2026/651][un2026latest], 10 August 2026, information cutoff 9 June 2026: the independent
  source-manifest review verified broad themes of Sahel/South Asian pressure, regional affiliate
  emphasis, disruption of Islamic State coordination, and TTP restructuring. These are
  consistent with the authored 2026 opportunity; they do not prescribe its outcome.

[un2024]: https://docs.un.org/S/2024/556
[un2025]: https://docs.un.org/S/2025/71/Rev.1
[un2026]: https://docs.un.org/S/2026/44
[un2026latest]: https://docs.un.org/S/2026/651
