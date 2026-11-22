# Counter-Terrorism Arrays and Scheduling

The implementation is in `common/scripted_effects/00_ct_effects.txt`. Its weekly
dispatcher is in `common/on_actions/MD_on_actions.txt`.

## Organization ids and slots

- `global.active_terror_orgs` stores stable organization ids. Its array positions are
  mutable slots.
- Threat, visibility, cooldown, HQ state, HQ controller, reach, region, and announcement
  flags all use those slots. Each country's four intel arrays must have the same length
  and slot order.
- Deleting a slot shifts every surviving organization's global data and every country's
  intel together.
- Infiltration flags and prepared raid targets use organization ids, because they
  outlive a slot's position. Raid resolution looks up the id's current slot. A destroyed
  target receives no effects.
- The player's selected slot shifts with surviving organizations and resets to the first
  slot when its organization is removed.
- Attacked, infiltrated, and failed-infiltration state live in per-country arrays indexed
  by organization id (`ct_attacked_by_org_arr`, `ct_infiltrated_org_arr`,
  `ct_failed_infil_org_arr`, fixed size 10). Creation and removal touch no per-country
  state except clearing the removed id. Ids recycle through the inactive pool.
- Attacked and failed-infiltration entries count down one per staggered pass.
  Infiltrated is permanent until the organization is removed.
- Global setup creates the organization arrays before country intel initialization. A
  new country sizes its intel arrays from the current organization count, including
  zero.
- Creation appends a complete record with a controlled HQ in the Middle East country
  pool. An empty inactive pool or no eligible HQ makes it a no-op. Creation has no
  production caller. Successful elimination raids call removal.

## Country coverage and cadence

- The four `global.ct_*_week` arrays together hold every enrolled country exactly once.
  Membership in them is the initialization check. An empty intel array cannot serve,
  since it is also what remains after the last organization dies.
- Released and civil-war countries use the same idempotent enrollment path.
- Annexed countries stay enrolled, so a restored country does not attach old
  intelligence to the wrong organization. Weekly processing skips non-existing
  countries.
- Each weekly dispatch processes one bucket, so each country runs once per four weeks,
  in this order: national CT, conditional power ranking, AI cyber, AI CT.
- The organization count is copied once before bucket processing. These effects do not
  add or remove organizations during the pass.

## International escalation

`MD_terror.21` is a country event with stability, policing-budget, and party-popularity
effects. Human and AI countries, including non-UN countries, each need their own
resolution. Keep the worldwide dispatch and its 1 to 8 day delay. A player-only
notification, a UN array, or a single news event would change those outcomes. Regional
escalation stays region-scoped.
