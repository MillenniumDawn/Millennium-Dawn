# Targeted Operations: Country Cases

Each actor reserves one case per recorded target country. Other countries have independent
cases, collection assignments, mandates, timed missions, and assessments. The player may keep
several country cases open; AI admits at most three and processes one new proposal per staggered
CT tick. One actor review dialog and one incoming host-consent dialog remain separate limits.

## Persistent records

`TOP_case_*` arrays are indexed by permanent person ID. They record host, state, method, expiry,
consent, phase, due date, sequence, facility, review rigor, civilian assurance, and collection.
`TOP_active_cases` contains only reserved cases. A country's increasing `TOP_case_counter`
assigns a new sequence at designation. A review snapshots that sequence and rechecks it at
approval. Flat `TOP_authorized_*` and `TOP_pending_*` values are execution/display snapshots;
they do not grant authority and may change when the player selects another dossier.

Phases:

- **0:** Closed. No country slot or authority.
- **1:** Designated for collection, with a 182-day reservation.
- **2:** Native operation authorized for 91 days.
- **3:** Timed mission in progress, with a recorded 28-day due date and 91-day authority.
- **4:** Waiting for the already-resolved assessment. Expiry cannot free this country slot.
- **5:** Assessment ready. The player confirms it to close the case; AI acknowledges it on
  the pending-country tick. Confirmation never repeats a reward or rolls another outcome.

Designation checks the discovered person's authored role, credible host, existing country slot,
and exceptional political authority. Collection can continue independently for each case.
Starting collection costs 25 Political Power only when that assignment was inactive. Returning
from a review uses its recorded person and sequence rather than the current selection.

`TOP_close_case = { TARGET = ID SEQUENCE = SEQUENCE }` closes only a matching generation.
Player revocation can close phases 1–3. It cannot skip assessment in phases 4–5. Cancelling
the review dialog leaves its designated case available for collection. Host changes require
closing the old reservation and obtaining a new designation and host review.

## Native callback constraint

The documented raid outcome scope exposes actor, victim, target state, and target province,
but no per-instance numeric token. The person and method are authored into each raid definition.
Launch and callback both validate the actor's person/method/state case. Changing a dossier or
operating in another country cannot redirect that callback.

Renewing an identical **open** phase-2 mandate preserves its sequence and prepared native raid.
Native map cancellation leaves that mandate open. Changing method or state requires closing
the old case first; a timed mission cannot be restarted by renewing its mandate.

Once a native case closes, its person/method/state tuple enters
`TOP_retired_native_bindings`. That exact tuple cannot be authorized again. A different
actionable state or another method is required. This restriction prevents an arbitrarily late
callback from an older raid being accepted by a newly created identical mandate. It is an
engine compatibility constraint, not a claim about real operational practice.

The tuple key is `person * 20000 + state * 2 + method`; native states must be 1–9999 and
methods 1–2. Keys fit exactly in single-precision integers for this registry. The finite key
space is bounded by authored/generated people, game states, and the two native methods.
No historical tuple is discarded to make a stale callback valid again.

## Assessment and protection

The first successful resolver changes global lifecycle and records rewards once. A delayed
assessment reveals that recorded result. Other actors pursuing the same person wait for global
death confirmation before their cases can be confirmed. Custody produces an immediate recorded
assessment. Release does not restore authority to an already completed operation.

Protection and counterintelligence are sampled for the attempted operation before removal.
The exposure bonus remains available after a successful action retires the protected official.
Timed success subtracts the protection penalty; native results may drop one outcome tier using
that percentage chance. See [security policies](targeted-operations-security.md).

## Acceptance beyond the Python contract tests

- Prepare simultaneous cases in two countries; cancelling, expiring, or confirming one must
  preserve the other. Attempt two people in one country and check the designation explanation.
- Change dossier, facility selection, and state controller while review or preparation runs.
- Renew the identical native case and verify that preparation survives in the engine.
- Close a native case and attempt the same tuple again; it must be refused. Deliver the old
  callback after authorizing another state or method and verify it has no effect.
- Let two actors pursue one person. Keep the second case reserved until the first actor's
  recorded death assessment is confirmed globally. Confirm each actor's case separately.
- Save/reload in all five active phases and while the security popup is open. Verify that no
  operation depends on temporary UI scratch values or the current dossier.

Static script execution does not establish native raid delivery, graphical layout, DLC
availability, or natural campaign balance. Those checks require HOI4 runtime evidence.
