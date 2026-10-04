# Formable Nations Reference

How a country adopts a union identity, and the AI ratchet that stops it flicking between
identities. Read before editing `common/decisions/formable_nation_decisions.txt`, its
categories file, `MD_EFS_decisions.txt`, the EU111/EU112 vote effects, the UAR,
Yugoslavia, African Union, or Event Horizon formation sites, or any `set_cosmetic_tag`
that represents a union.

## Vocabulary

| Term                          | Meaning                                                     |
| ----------------------------- | ----------------------------------------------------------- |
| Decision formable             | One of the 23 categories in `formable_nation_decisions.txt` |
| Special formable              | A union that commits through `commit_special_formable`      |
| `is_<TAG>`                    | Country flag: started formable `<TAG>`. Never cleared       |
| `<TAG>_exists`                | Global flag: someone started `<TAG>`. Never cleared         |
| `reshaping_national_identity` | Idea held while forming, -15% stability                     |
| `formed_country_formable`     | Permanent country flag, the latch                           |
| `formable_committed_id/_size` | Ratchet country variables. Unset reads 0, never seed them   |
| `special_formable_id`         | Temp variable read by `commit_special_formable`             |

Files:

- `common/decisions/formable_nation_decisions.txt` and
  `common/decisions/categories/formable_nations.txt`: the decision formables.
- `common/scripted_effects/00_formable_effects.txt`: `commit_special_formable`,
  `mark_formed_country_formable`, and the purchase timers.
- `common/ideas/MD_formable_ideas.txt`: `reshaping_national_identity`.
- `tools/validation/validate_decisions.py`: `validate_formable_commitment_sync` and
  `_SPECIAL_FORMABLE_IDS`, the source of truth for special ids.

## Decision formables

### Category visibility

Every `form_<TAG>_category` has the same `visible`:

```
	visible = {
		NOT = { has_global_flag = GAME_RULE_disable_formable_nations }
		if = {
			limit = { has_country_flag = formed_country_formable }
			has_country_flag = is_<TAG>
		}
		else = {
			NOT = { has_global_flag = <TAG>_exists }
		}
	}
```

- Unlatched: hidden once anyone else starts `<TAG>`. `<TAG>_exists` is never cleared, so
  a re-emerged constituent never sees the category again.
- Latched: only the categories of formables the country itself started stay visible.

### Latch

`mark_formed_country_formable` sets `formed_country_formable`. It is never cleared, even
when the identity is abandoned or revoked.

- Writers: the `on_add` of `reshaping_national_identity` (every decision-formable start),
  `commit_special_formable`, both UAR announces, and the national-identity cosmetic
  sites (German empires, Iranic and Tajik unions, Vanguard, and similar).
- Readers, all `visible`: the 23 formable categories, `different_country_flags_category`,
  and both UAR announces.

The latch is a one-way visibility cut for players and AI. The ratchet is an AI-only
ranked commitment. Once latched, the ratchet's upgrade path and the CANZUK exemptions
are reachable only from pre-latch states.

### Decision set

- `<TAG>_integrate_start`: visible while `NOT is_<TAG>`, available at about 80% of the
  state list owned or puppet-owned. Sets `is_<TAG>` and `<TAG>_exists` and adds the idea.
  Gate and commit.
- `<TAG>_integrate_<SUB>`: timed. Its `remove_effect` cores or annexes. Gate.
- `<TAG>_update_flag`: cost 0, `base = 10000`. Visible with `is_<TAG>` and without the
  cosmetic. Available when every listed state is a core. Sets the cosmetic and removes
  the idea. Gate and commit. Its state list is the formable's size.
- `<TAG>_buy_core_state`: state-targeted purchase through
  `formable_purchase_deliver_offer` and `formable_purchase_cancel_offer`. Gate only.

IBR and ANZ have no `integrate_start` or `buy_core_state`. Their integrate decisions set
the flags and the idea in `remove_effect` and carry a guarded commit.

Spain also enters IBR by focus. `SPR_declare_the_iberian_union` sets `IBR_exists` and the
cosmetic and carries the ratchet gate in `ai_will_do`. `SPR_solidify_the_iberian_union`
sets `is_IBR`, latches, and makes a guarded commit. Neither adds the idea nor reads the
formable game rule. IBR stays a decision commitment, not a sentinel.

### External readers

Achievements read `is_<TAG>`. EFS branding reads `is_IBR`, `is_SCA`, and `is_BLT`. The
UAR category hides on `is_MAGHREB`. `BNL_treaty_of_union` bypasses on `is_HBL`. Nothing
else reads `<TAG>_exists`, `reshaping_national_identity`, or `formable_committed_*`.

## Commitment ratchet

The AI only moves to a strictly larger formable and finishes the one it committed to.
Without this, a country holding territory for two formables alternated their zero-cost
`update_flag` decisions forever. The ratchet lives only in `ai_will_do`, so players are
unaffected.

Gate, on every decision in the formables file:

```
	ai_will_do = {
		base = 10
		modifier = {
			factor = 0
			NOT = { check_variable = { formable_committed_id = <ID> } }
			check_variable = {
				var = formable_committed_size
				value = <SIZE>
				compare = greater_than_or_equals
			}
		}
	}
```

Commit, in every `integrate_start` and `update_flag` `complete_effect`:

```
	hidden_effect = {
		set_variable = { formable_committed_id = <ID> }
		set_variable = { formable_committed_size = <SIZE> }
	}
```

Guarded commit, for a delayed or ungated site (a `remove_effect`, a focus) that must not
downgrade a larger commitment made meanwhile:

```
	hidden_effect = {
		if = {
			limit = {
				check_variable = {
					var = formable_committed_size
					value = <SIZE>
					compare = less_than
				}
			}
			set_variable = { formable_committed_id = <ID> }
			set_variable = { formable_committed_size = <SIZE> }
		}
	}
```

`<ID>` is a unique ordinal below 100. `<SIZE>` is the `update_flag` state-list count. The
validator recomputes both.

### CANZUK exemption

`CANZUK_update_flag` is hidden for an EU member or once any European federation exists,
so a CANZUK commitment can strand.

- `CANZUK_integrate_start` has a second AI modifier: `factor = 0` when
  `has_global_flag = european_federation` or `has_idea = EU_member`.
- Every ANZ, NORDEM, and AVG decision (CANZUK's fallback formables) extends its gate so a
  stranded CANZUK commitment does not block them:

```
			NOT = {
				AND = {
					check_variable = { formable_committed_id = 15 }
					OR = {
						has_global_flag = european_federation
						has_idea = EU_member
					}
				}
			}
```

## Special formables

A special formable is an identity the AI must keep even though the country still
qualifies for a decision formable. It commits with the sentinel size 1000, which outranks
every decision size, so every decision gate evaluates `factor = 0`.

```
commit_special_formable = {
	mark_formed_country_formable = yes
	if = {
		limit = { has_idea = reshaping_national_identity }
		remove_ideas = reshaping_national_identity
	}
	hidden_effect = {
		set_variable = { formable_committed_id = special_formable_id }
		set_variable = { formable_committed_size = 1000 }
	}
}
```

Call pattern. The setter must be immediately followed by the call:

```
	set_cosmetic_tag = <SPECIAL_COSMETIC>
	set_temp_variable = { special_formable_id = <ID> }
	commit_special_formable = yes
```

- The write is unconditional. A special identity overrides any decision commitment,
  including a completed one. Never add a `less_than` guard.
- Write 1000 only inside the effect, and ids of 100 and up only through
  `special_formable_id`. Inline literals are validator errors.
- Never call it inside `effect_tooltip`. The validator strips those bodies.
- A player who later clicks a decision `update_flag` replaces the sentinel. Accepted.
- Do not add a sentinel to a sub-step of a decision formable (Estonia annexing LIT and
  LAT before BLT, the UK annexing CAN, AST, and NZL before CANZUK). It would block the
  formable it leads to. Add the call only when the identity must survive a later
  decision formable.

### The six identities

- 101 United States of Europe (EU111): `focus_EU111_QMV_result` annexes the members into
  the Commission president's country. EU111 applies regardless of the result trigger.
  The sentinel lands on ROOT only. ROOT keeps `EU_member` until focus `USoE001`. There
  is no global "USoE formed" flag: use `has_country_flag = USoE`.
- 102 European Federation member (EU112): `focus_EU112_QMV_result` only sets the global
  `european_federation`, which is never cleared. The sentinel lives in `EFS_update_flag`
  because that decision fires for founders and every later joiner. `EFS_flag_change` is
  one-shot. Branches `is_IBR`, `is_SCA`, and `is_BLT` set `EFS_IBR`, `EFS_SCA`, and
  `EFS_BLT`. `leaving_EU` never drops the EFS cosmetic or the sentinel.
- 103 United Arab Republic: both announces in `UnitedArabRepublic.txt`, plus
  `EGY_pan_arab_effort` and `LBA_strive_for_uar`. The `EGY_negot_*`,
  `SYR_the_arab_union`, and `egypt.144` pre-announce sites latch but are not sentinel
  sites. The only identity with revocation: the falls-apart timeouts and `on_puppet`
  clear both ratchet variables. They key on `formed_*`, which `UAR_unite_*` clears, so a
  united-then-puppeted UAR keeps cosmetic and sentinel.
- 104 Yugoslavia restored: `form_yugoslavia_effect` is the single site for the decision
  and the SER, KOS, and MNT focuses. The gate is `has_idea = formed_yugoslavia`.
- 105 United States of Africa: `AFRICAN_UNION_shared_focus_unite_africa`.
- 106 Event Horizon blocs: one id for all eleven formation events. Nothing in the EU
  scripts reads the scenario, so an `EH_EUF` bloc can still pass EU112.

## Cross-guards

`european_federation` is a global flag, so guards on it fire worldwide.

- BLT: `update_flag` is hidden for `european_federation` or `EU_member`.
  `integrate_start` has no EU block (the Baltic trap below).
- CANZUK and MAGHREB: `update_flag` is hidden for `european_federation`, `EU_member`, or
  the cosmetic already held. Only CANZUK AI-blocks `integrate_start` to match.
- MAGHREB and UAR exclude each other: `MAGHREB_integrate_start` is hidden for a UAR, and
  `form_UAR_category` is hidden on `is_MAGHREB`.
- ANZ, NORDEM, AVG: no EU guard. They carry the CANZUK exemption.
- All other formables have no EU guard. `EFS_update_flag` has no ratchet gate.

## Game rules

| Rule                                           | Effect                                         |
| ---------------------------------------------- | ---------------------------------------------- |
| `rule_disable_formable_nations`                | Hides the 23 categories and the UAR category   |
| `rule_disable_eu`                              | No EU, so EU111 and EU112 are unreachable      |
| `rule_enable_ai_european_union_end_game_paths` | `no` stops the AI proposing agendas 110 to 112 |
| `rule_event_horizon_scenario`                  | Enables the Event Horizon chain                |

The formable rule hides categories only. Every special formable and focus union stays
formable under it. The end-game-paths rule is the only AI kill switch for USoE and EFS.
Check it first when the AI never federates.

## Known traps and accepted behavior

- Baltic trap: `BLT_integrate_start` has no EU gate while `BLT_update_flag` is hidden for
  `EU_member`. An AI that starts BLT as an EU member keeps the -15% stability idea.
- `european_federation` hides `MAGHREB_update_flag` and `CANZUK_update_flag` worldwide,
  which can strand an AI mid-formable.
- Player-side clobber: `SCA`, `IBR`, `HBL`, `NORDEM`, `AUSHUN`, and `AVG` `update_flag`
  have no EU guard, so a player can click one after EFS branding and lose it for good.
  Do not fix this by copying BLT's `EU_member` guard. That recreates the Baltic trap.
- EFS variants exist only for IBR, SCA, and BLT. Other completed formables get a plain
  `EFS_<TAG>`.
- A member mid-formable when EU112 passes gets sentinel 102 and is AI-blocked from the
  rest of that formable. Intended: special beats decision.
- No generic sentinel revocation. A path that drops a special cosmetic leaves size 1000
  on the country and AI-blocks all decision formables. A new special formable with a
  dissolution path must clear both variables there.
- The latch is permanent and pre-emptive. A country that starts and abandons a formable
  never sees another formable category or flag-change decision.
- The ratchet never gates a special formable. Nothing in the EU voting, GUI, or focus
  files reads ratchet state.
- Naming traps: `EST_euro_federation` localises as "European Federation" but is
  unrelated to the flag. `SCA_soviet_onion` reuses the `SCA` prefix without touching
  `is_SCA`. `TAJ_formable` is cosmetic-only. `is_european_federation_country` is a
  continent trigger.

## Maintenance

New decision formable:

1. Add the category with the standard latch-aware `visible`.
2. Add the four decision shapes. `integrate_start` sets `is_<TAG>` and `<TAG>_exists`
   and adds the idea. `update_flag` sets the cosmetic and removes the idea.
3. Take the next free id below 100. Size is the `update_flag` state-list count.
4. Gate every decision. Commit in `integrate_start` and `update_flag`. Use a guarded
   commit on any delayed or ungated site.
5. Editing an `update_flag` state list means updating the size literal at every gate
   and commit site, including the Spain focus for IBR.
6. If an EU guard hides the `update_flag`, AI-block `integrate_start` under the same
   condition and extend the exemption to any fallback formable.

New special formable:

1. Take the next free id of 100 or more and add it to `_SPECIAL_FORMABLE_IDS`.
2. At every site that adopts the identity, after the `set_cosmetic_tag` and outside any
   `effect_tooltip`, add the setter and the call. One id per identity.
3. If the identity can dissolve, `clear_variable` both ratchet variables at each
   dissolution site. The latch stays.
4. Add a test in `tools/tests/validation/validate_decisions_formable_commitment_test.py`
   if the site shape is new.

Then run `python tools/validation/validate_decisions.py` and `python -m pytest`. The
validator scans `common/decisions`, `common/national_focus`, `common/scripted_effects`,
`common/on_actions`, and `events`. A call site outside those directories is invisible to
it.
