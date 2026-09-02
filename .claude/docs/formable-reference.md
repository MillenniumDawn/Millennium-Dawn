# Formable Nations Reference

Every path by which a country adopts a union identity — the 23 decision formables, the six special formables that commit through `commit_special_formable`, and every other focus/decision/event union or cosmetic identity — plus the AI commitment ratchet that stops the AI flicking between them. Read before editing `common/decisions/formable_nation_decisions.txt`, `common/decisions/categories/formable_nations.txt`, `common/decisions/MD_EFS_decisions.txt`, the EU111/EU112 vote effects, the UAR, Yugoslavia, African Union or Event Horizon formation sites, or any `set_cosmetic_tag` that represents a union.

## 1. Scope & vocabulary

Decision paths are under `common/decisions/`.

| Term                          | Meaning                                                          |
| ----------------------------- | ---------------------------------------------------------------- |
| Decision formable             | One of 23 categories in `formable_nation_decisions.txt` (§2)     |
| Special formable              | Union outside that file — six identities, ids 101-106 (§4)       |
| Cosmetic identity             | Any other `set_cosmetic_tag` union/empire; catalog in §5         |
| `is_<TAG>`                    | Started formable `<TAG>` (Spain: completed). Never cleared.      |
| `<TAG>_exists`                | Global: `<TAG>` started; hides its category. Never cleared.      |
| `reshaping_national_identity` | Idea (`MD_formable_ideas.txt:5`, `stability_factor = -0.15` :16) |
| Cosmetic `<TAG>`              | From `<TAG>_update_flag`: the flag/name the player sees          |
| `formable_committed_id/_size` | Ratchet country variables (§3). Unset reads 0 — never seed       |
| `formed_country_formable`     | Permanent latch once an identity locks in (#3440; §2)            |
| `special_formable_id`         | Temp variable read by `commit_special_formable` (§4)             |

Details:

- Ratchet commits: a decision formable commits a real id (1-23) and its state count; a special formable commits through `commit_special_formable` with a reserved id (>= 100) and the sentinel size 1000.
- `reshaping_national_identity`: added by `integrate_start`, removed by `update_flag` and by `commit_special_formable`; its `on_add` latches (§2). Lifecycle idea shown to the player; -15 % stability.
- The six special formables: USoE, EFS membership, UAR, Yugoslavia, United States of Africa, Event Horizon blocs.
- Full variable names: `formable_committed_id`, `formable_committed_size`.

- `common/decisions/formable_nation_decisions.txt` — 23 categories × 4 decision shapes (§2) = 183 decisions, every one ratchet-gated
- `common/decisions/categories/formable_nations.txt` — 23 `form_<TAG>_category`; `EFS_flag_category` :128-140; `USoE_Flag_Reset_Flag_category` :142-154
- `common/scripted_effects/00_formable_effects.txt` — `commit_special_formable` :56-66; `mark_formed_country_formable` :48-50; purchase timers :7-44
- `common/ideas/MD_formable_ideas.txt` — `reshaping_national_identity`
- `common/decisions/MD_EFS_decisions.txt` — `EFS_update_flag` (special 102)
- `common/scripted_effects/99_EU_voting_scripted_effects.txt` — `focus_EU111_QMV_result` (special 101), `focus_EU112_QMV_result`
- `common/decisions/UnitedArabRepublic.txt`, `common/on_actions/99_UAR_on_action.txt` — UAR (special 103)
- `common/scripted_effects/99_yugoslavia_scripted_effects.txt` — `form_yugoslavia_effect` (special 104)
- `common/national_focus/06_AfricanUnion_shared.txt` — United States of Africa (special 105)
- `events/Event Horizon.txt` — Event Horizon blocs (special 106)
- `tools/validation/validate_decisions.py` — `validate_formable_commitment_sync`; `_SPECIAL_FORMABLE_IDS` :480-487 (special-id source of truth)
- `tools/tests/validation/validate_decisions_formable_commitment_test.py` — Regression tests for both rule sets

Details:

- Decision shapes: `integrate_start` / `integrate_<SUB>` / `update_flag` / `buy_core_state` (§2).
- `00_formable_effects.txt:7-44`: `formable_purchase_deliver_offer` / `formable_purchase_cancel_offer` (the `buy_core_state` timers).

## 2. Decision-category system

### Category visibility

Every `form_<TAG>_category` in `categories/formable_nations.txt` (e.g. `form_SOU_category` :158-186) has the same `visible`:

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

Hidden for everyone under the game rule. Unlatched: hidden once anyone else starts `<TAG>` (`<TAG>_exists` is never cleared — no `clr_global_flag = *_exists` in the repo — so a formed nation that is later annexed leaves its category hidden for any re-emerged constituent, §8h). Latched: only the categories of formables the country itself started (`is_<TAG>`) stay visible. `european_federation` does **not** hide these categories — its only read in the file is `EFS_flag_category` (:136).

### Formed-country latch

`formed_country_formable` is a permanent country flag set by `mark_formed_country_formable` (`00_formable_effects.txt:48-50`; #3440, issue #3432 — Hohenzollern Germany flipping German Empire ↔ GDR every few seconds). Writers: `reshaping_national_identity` `on_add` (`MD_formable_ideas.txt:9-13`) — every decision-formable start latches; `commit_special_formable` (§4) — every special formable latches; both UAR announces (:44, :104), `LBA_strive_for_uar` (:11797), `SPR_solidify_the_iberian_union` (`05_spain.txt:3417`); and ~80 national-identity sites across the German empires, Iranic/Tajik unions, Vanguard, Iraq, US junta and similar cosmetic-identity decisions and events. Readers (all `visible`): the 23 formable categories (above), `different_country_flags_category` (`different_country_flags.txt:25`), both UAR announces (`UnitedArabRepublic.txt:7`, :68). Never cleared, even when the identity that set it is later abandoned or revoked (§8m).

Latch vs ratchet: the latch is a one-way **visibility** cut for players and AI alike; the ratchet (§3) is an AI-only ranked commitment. Once latched, only already-started formables' categories are visible, so the ratchet's strictly-larger upgrade and the CANZUK fallback exemptions are reachable only from pre-latch states (old saves, multi-`is_<TAG>` countries). Inside a still-visible category the ratchet is what stops `update_flag` flicking and enforces special identities — the latch does neither.

### Per-formable decision set

Names are `<TAG>_<shape>`; effect details below.

| Decision          | Shape                                                | Ratchet              |
| ----------------- | ---------------------------------------------------- | -------------------- |
| `integrate_start` | `visible = { NOT is_<TAG> }`; ~80 % owned; below     | gate + commit        |
| `integrate_<SUB>` | timed (`days_remove`); `remove_effect` cores/annexes | gate (IBR/ANZ below) |
| `update_flag`     | `cost = 0`; `base = 10000`; visibility below         | gate + commit        |
| `buy_core_state`  | state-targeted purchase; timers below                | gate only            |

Details:

- `integrate_start` `complete_effect`: `set_country_flag = is_<TAG>`, `set_global_flag = <TAG>_exists`, `add_ideas = reshaping_national_identity`.
- `update_flag` (`ai_will_do base = 10000`): `available` = every listed state `is_core_of = ROOT`; `complete_effect`: `set_cosmetic_tag = <TAG>`, `remove_ideas = reshaping_national_identity`.
- `buy_core_state` timer: `formable_purchase_deliver_offer` / `formable_purchase_cancel_offer` (`00_formable_effects.txt:7-44`), events `formable_buy.*`.
- `integrate_start` `available`: owns or puppet-owns ~80 % of the state list.
- `update_flag` `visible`: `is_<TAG>` + NOT `has_cosmetic_tag <TAG>`.
- Ratchet anchors (BLT): `integrate_start` gate :7-18, commit :72-75; `update_flag` gate :295-306, commit :353-356; IBR/ANZ subs carry guarded commits (§3).

The `update_flag` state list is the formable's **size** (§3).

**IBR / ANZ** have no `integrate_start` and no `buy_core_state`. `IBR_integrate_SPR` (:2354) / `IBR_integrate_POR` (:2493) and `ANZ_integrate_AST` (:2689) / `ANZ_integrate_NZL` (:2812) set `is_<TAG>` + `<TAG>_exists` + `reshaping_national_identity` in their `remove_effect` (`is_<TAG>` + `<TAG>_exists` at IBR :2469-2470, :2570-2571; ANZ :2788-2789, :2887-2888) and carry a guarded commit (§3).

**Spain's focus entry into IBR** (`common/national_focus/05_spain.txt`, `SPR_the_old_ways` branch, `nationalist_monarchists_are_in_power`):

- `SPR_declare_the_iberian_union` (:3041): `set_global_flag = IBR_exists` unless `is_IBR` (:3061-3062), fires `spain.60` → `set_cosmetic_tag = IBR` (`events/Spain.txt:3540`, :3553). Its `ai_will_do` (:3067-3078) carries the standard decision-shape ratchet gate for id 5 / size 24, so an AI Spain committed to anything larger — in particular a special identity such as EFS — never takes it.
- `SPR_demand_andorra` (:3150, `spain.65` annexes ADO); `SPR_seize_the_portuguese_throne` (:3195, `spain.62` annexes POR).
- `SPR_solidify_the_iberian_union` (:3347): cores POR/ADO, `set_country_flag = is_IBR` (:3416), latch (:3417), guarded commit 5/24 (:3418-3431).
- No `reshaping_national_identity`; not gated by the formable game rule. Afterwards `form_IBR_category` is visible for Spain (`is_IBR`) and `IBR_update_flag` stays hidden because the cosmetic is already `IBR`. IBR remains a **decision** commitment (id 5), not a sentinel.

### External readers of formable state

Prefixes omitted: `common/national_focus/`, `common/decisions/categories/`.

| Reader                | Where — reads                                                          |
| --------------------- | ---------------------------------------------------------------------- |
| Achievements          | `common/achievements/MD_achievements.txt:548-941` — `is_<TAG>` (22)    |
| EFS branding          | `MD_EFS_decisions.txt` :48, :74, :94, … — `is_IBR/SCA/BLT` → `EFS_*`   |
| UAR category          | `UnitedArabRepublic_categories.txt:10` — hidden when `is_MAGHREB`      |
| Benelux focus         | `03_benelux_shared.txt:776` — `BNL_treaty_of_union` bypass on `is_HBL` |
| Flag-change decisions | `different_country_flags.txt:25` — hidden once latched (#3440)         |
| MAGHREB start         | `formable_nation_decisions.txt:10866-10867` — `NOT is_*_uar` (below)   |
| Spain                 | `05_spain.txt:3061-3062`, :3416 — sets `IBR_exists`, `is_IBR`          |

Details:

- Flag-change: #3440 replaced the old `is_BLT/FCA/GCL/SCA/IBR/UAS` list with the latch.
- MAGHREB start: `NOT is_neo_baathist_uar` / `NOT is_baathist_uar` — the sole decision-formable gate on a special identity.

Nothing else reads `<TAG>_exists`, `reshaping_national_identity` or `formable_committed_*` (outside the ratchet sites, `commit_special_formable`, the UAR revocations and the validator).

### Game rule

`GAME_RULE_disable_formable_nations` (set at `common/on_actions/999_game_rules_on_actions.txt:415-424` from `rule_disable_formable_nations`, `common/game_rules/00_game_rules.txt:353`) is read **only** by the 23 categories. Every mechanism in §4 and §5 stays formable under the rule (§7).

## 3. Commitment ratchet

`formable_committed_id` (unique ordinal) and `formable_committed_size` (that formable's `update_flag` state count) are country variables. The AI only ever moves to a **strictly larger** formable and finishes the one it committed to; without this a country holding territory for two formables alternated their zero-cost `update_flag`s forever. Since #3440, a second formable's category is only visible pre-latch (§2), so the upgrade path exists for old saves and multi-`is_<TAG>` states. Player freedom is untouched — the ratchet lives only in `ai_will_do`. Unset variables read 0; never seed them. Landed in `9026c008f3` (#3115).

Gate — on every one of the 183 decisions (`BLT_integrate_start` :7-18):

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

Commit — in every `integrate_start` and `update_flag` `complete_effect` (:72-75, :353-356):

```
	hidden_effect = {
		set_variable = { formable_committed_id = <ID> }
		set_variable = { formable_committed_size = <SIZE> }
	}
```

Guarded commit — a delayed or ungated site must not downgrade a larger commitment made meanwhile. Sites: the IBR/ANZ integrate `remove_effect`s (`compare = less_than` at :2483, :2584, :2802, :2901) and `SPR_solidify_the_iberian_union` (`05_spain.txt:3417-3430`):

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

### Id / size table

size = `<TAG>_update_flag` state-list count; the validator recomputes it (§9). Ids 100+ are reserved for special formables (§4).

| id  | TAG | size | id  | TAG     | size | id      | TAG          | size |
| --- | --- | ---- | --- | ------- | ---- | ------- | ------------ | ---- |
| 1   | BLT | 12   | 9   | USNA    | 83   | 17      | NORDEM       | 45   |
| 2   | FCA | 14   | 10  | UTS     | 14   | 18      | MAGHREB      | 46   |
| 3   | GCL | 18   | 11  | MAPHI   | 42   | 19      | WESTFED      | 9    |
| 4   | SCA | 27   | 12  | INDOCHI | 14   | 20      | AUSHUN       | 33   |
| 5   | IBR | 24   | 13  | ANDES   | 16   | 21      | PBL          | 41   |
| 6   | ANZ | 16   | 14  | ANTCONF | 9    | 22      | UAS          | 15   |
| 7   | SOU | 74   | 15  | CANZUK  | 53   | 23      | AVG          | 21   |
| 8   | HBL | 10   | 16  | RDLP    | 21   | 101-106 | special (§4) | 1000 |

### CANZUK exemption

CANZUK's `update_flag` is hidden for an EU member or once any European federation exists (§6), so a CANZUK commitment can strand. Two mitigations:

- `CANZUK_integrate_start` has a second AI modifier (:8680-8687): `factor = 0` when `has_global_flag = european_federation` OR `has_idea = EU_member` — never commit to a formable whose `update_flag` the EU guard blocks.
- Every ANZ, NORDEM and AVG decision (CANZUK's fallback formables, sharing AST/NZL and ENG) extends its gate so a CANZUK commitment held under the EU guard does not block them:

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

Sites (anchor = the `formable_committed_id = 15` line): ANZ :2706, :2829, :2927; NORDEM :10055, :10195, :10287, :10363, :10458, :10612, :10770; AVG :15056, :15163, :15250, :15317, :15423, :15533. The exemption tests id 15 only, so a sentinel id never matches it. Post-#3440 the fallback also needs its category visible — a latched ENG sees `form_NORDEM_category` only with `is_NORDEM` already set — so the exemptions matter for pre-latch states only (§2).

### Adding a formable

Full checklist in §9. In short: next free id below 100, size = the `update_flag` state count, gate on every decision, commit in `integrate_start` and `update_flag`, guarded commit on any delayed or ungated site, category with the standard `visible`, then run `validate_decisions.py`.

## 4. Special formables

A special formable is an identity the AI must keep even though the country still qualifies for, or is mid-way through, a decision formable. It commits with the sentinel size 1000, which outranks every decision size (largest: USNA 83), so all 183 decision gates evaluate `factor = 0`.

### Contract

`commit_special_formable` (`common/scripted_effects/00_formable_effects.txt:56-66`):

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

Call pattern — the setter must be **immediately** followed by the call (the validator enforces the pair, §9):

```
	set_cosmetic_tag = <SPECIAL_COSMETIC>
	set_temp_variable = { special_formable_id = <ID> }
	commit_special_formable = yes
```

Rules:

- Also latches (first line; #3440): a special formable hides flag-change decisions and unstarted formable categories for players too (§2).
- The write is unconditional: a special identity overrides any decision commitment, including a completed one (an EFS Sweden that already formed SCA is `EFS_SCA`; the sentinel keeps it there). No `less_than` guard.
- 1000 is written only inside the effect; ids >= 100 only through `special_formable_id`. Inline literals are validator errors.
- `special_formable_id` is a temp variable; the setter sits outside `hidden_effect` and produces no tooltip. The only player-visible effect is the `remove_ideas` when the idea is held (this is the one player-facing change the sentinel shipped: adopting a special identity now ends reshaping early).
- Never inside `effect_tooltip` — the validator strips those bodies, so a call there is not a call site.
- A player who later clicks a decision `update_flag` replaces the sentinel with that decision's unconditional commit — accepted (the player overrode the identity).
- The ratchet never gates a special formable, and nothing in the EU voting/GUI/focus files reads ratchet state (§8k).

### Sentinel table

Mirrors `_SPECIAL_FORMABLE_IDS` (`tools/validation/validate_decisions.py:480-487`), the source of truth; nothing checks this table against the dict.

| Special                             | Write site(s)                                        |
| ----------------------------------- | ---------------------------------------------------- |
| 101 United States of Europe (EU111) | `99_EU_voting_scripted_effects.txt:451-452`          |
| 102 European Federation member      | `MD_EFS_decisions.txt:281-282`                       |
| 103 United Arab Republic            | `UnitedArabRepublic.txt:46-47`, :106-107; more below |
| 104 Yugoslavia restored             | `99_yugoslavia_scripted_effects.txt:169-170`         |
| 105 United States of Africa         | `06_AfricanUnion_shared.txt:2674-2675`               |
| 106 Event Horizon bloc (all eleven) | `events/Event Horizon.txt` :368 … :1578              |

Details:

- Context per id in §4.1-4.6 (101: `focus_EU111_QMV_result` ROOT block, cosmetic :450; 102: `EFS_update_flag`, after the tag chain, before `EFS_flag_change` :283; 104: `form_yugoslavia_effect`; 105: `AFRICAN_UNION_shared_focus_unite_africa`).
- 103 also: `05_egypt.txt:4416-4417`, :4429-4430; `05_libya.txt:11799-11800`.
- 106 sites: :368, :491, :609, :730, :853, :974, :1094, :1215, :1337, :1456, :1578.
- Revocation: none except 103 — `clear_variable` of both vars at the falls-apart timeouts (:773-774, :825-826) and `99_UAR_on_action.txt` on_puppet (:69-70, :83-84); gaps §4.3. 102: `european_federation` and the EFS cosmetic are never dropped, not even by `leaving_EU`.

Details:

- 103 write sites also: `05_libya.txt:11798-11799`.
- 103 revocation: `clear_variable` of both vars at `UAR_neo_baathist_uar_falls_apart` :769-770, `UAR_baathist_uar_falls_apart` :821-822, `99_UAR_on_action.txt` on_puppet :69-70, :83-84 (§4.3 for the gaps).

### 4.1 United States of Europe (EU111, id 101)

Two distinct EU end-states exist: EU111 annexes the members into one country; EU112 (§4.2) leaves them sovereign.

Chain: agendas 110/111/112 are seeded into `global.EU_potential_votes` (`99_eu_scripted_effects.txt:736-738`) → proposal gates in `common/scripted_guis/01_european_union_guis.txt` (112 :4971 needs 110 passed and not 111; 110 :4982; 111 :5000 needs 110 passed and not 112; PP > 300) → a European Parliament pass appends to `global.EU_council_votes` (`99_EU_voting_scripted_effects.txt:1082`) → Council QMV mission `EU_voting_mission_focus_EUXXX_QMV_result` (`common/decisions/EU_voting_decisions.txt:391`, 14 days :397) on every member; the holder of `EU_commission_president` (else a caretaker) runs `apply_EU_QMV_result` (:405, :413) → `apply_EU_QMV_result` (`99_EU_voting_scripted_effects.txt:316-330`): **EU111 applies regardless of the result trigger**; every other agenda needs `EU_voting_decision_result_trigger` (`99_EU_voting_scripted_triggers.txt:16-17`, yes-population ratio > 0.65). AI members vote through party weights `EU_vote_w1..w6^111` (:207), read by `EU_update_AI_focus_voting_modifier` (:255); the weights read `ruling_party` and `europeanism` only.

`focus_EU111_QMV_result` (:386-473): rejecters lose `EU_member` (:389); `global.EU_passed_votes` += 111 (:394); members are snapshotted (:401-404) and each gets `USoE_member` + `USoE` (:410-411), cores to ROOT (:430) and is annexed (:439); ROOT — the Commission president — gets `set_cosmetic_tag = USoE` (:450), the sentinel (:451-452), `USoE` (:454) and `multi_ethnic_state_idea` (:471). ROOT keeps `EU_member` until focus `USoE001` (`01_EU_USoE_shared.txt:3`, `remove_ideas = EU_member` :301; the `usoe_formed` global at :309 is commented out — no global "formed" flag exists).

Follow-ups: `USoE_integrate_new_members` (`common/decisions/EU_USoE_decisions.txt:125`, cost 1500, `base = 0` :184); `USoE_reset_flag` / `USoE_AI_reset_flag` (`common/decisions/MD_USoE_decisions.txt:5`, :17; category `USoE_Flag_Reset_Flag_category`, `categories/formable_nations.txt:142-154`, visible `has_country_flag = USoE`); dynastic variants `set_USoE_flag_of_the_house` (`99_eu_scripted_effects.txt:563`: `USoE_SAV/WIT/BOR_ANJ/BOR/HAN/GLU/WIN/ORA/HAB/NAP/HOH`) and `USoE_com/air/army/navy/green` in the USoE tree (`01_EU_USoE_shared.txt:1739`).

AI-reachable: yes; the only AI kill switch is `rule_enable_ai_european_union_end_game_paths = no` (§7). Ratchet: the sentinel lands on ROOT only — annexed members cease to exist. Formation clears no `is_<TAG>` / `<TAG>_exists`; a ROOT holding `is_<TAG>` keeps `form_<TAG>_category` visible (player-clickable, §8c) but the AI is blocked from `<TAG>_update_flag`. `USoE_AI_reset_flag` only resets from `USoE_*` variants, never from a decision cosmetic.

### 4.2 European Federation (EU112, id 102) — EFS branding

`focus_EU112_QMV_result` (`99_EU_voting_scripted_effects.txt:847-848`) does one thing: `set_global_flag = european_federation`. The flag is never cleared. Needs the result trigger (§4.1); AI weights `^112` at :208.

Branding: `EFS_flag_category` (`categories/formable_nations.txt:128-140`, visible `european_federation` + `has_idea = EU_member` + NOT `GAME_RULE_eu_disabled`) → `EFS_update_flag` (`MD_EFS_decisions.txt:6`): `cost = 0` (:8), `base = 10000` (:9), `visible = { NOT EFS_flag_change }` (:10). A `tag =` chain sets `EFS_<TAG>`, with the decision-formable branches `is_IBR` → `EFS_IBR` (CAT/POR/SPR :48-49, :214-215, :248-249), `is_SCA` → `EFS_SCA` (DEN/FIN/ICE/NRY/SWE :74-75, :104-105, :142-143, :200-201, :258-259), `is_BLT` → `EFS_BLT` (EST/LAT/LIT :94-95, :164-165, :174-175), else `EFS_WAS` (:278); then the sentinel (:281-282) and `set_country_flag = EFS_flag_change` (:283). `EFS_flag_change` is **one-shot**: written only there, read only at :10, never cleared. The decision fires for founding members and every later joiner (the day a country holds both the flag and `EU_member`), which is why the sentinel lives here and not in the vote result. No `EFS_HBL/AUSHUN/NORDEM/AVG` variants exist (§8d).

Also unlocked by the flag: the POTEF tree (`02_EU_POTEF_shared.txt:14`), `EU_POTEF_decisions.txt:314/444/476/491`, weekly elections (`MD_on_actions.txt:827`), GUI office buttons (`01_european_union_guis.txt:368-386`, :512-516); `different_country_flags_category` hides for EU members (`categories/different_country_flags.txt:20-23`).

Ratchet: sentinel 102 overrides any decision commitment, completed or not (§8e), which also AI-blocks that formable's `buy_core_state`. The `is_IBR/is_SCA/is_BLT` branches read flags only. `leaving_EU` (`99_eu_scripted_effects.txt:331`) never drops the EFS cosmetic, so a leaver keeping the sentinel matches the identity it keeps.

### 4.3 United Arab Republic (id 103)

Category `form_UAR_category` (`categories/UnitedArabRepublic_categories.txt:2-12`): `allowed = { is_arabic_nation = yes }`; `visible` = NOT `is_MAGHREB` (§8f), NOT `GAME_RULE_disable_formable_nations` (#3440, §7). Decisions in `common/decisions/UnitedArabRepublic.txt`:

| Step        | Decisions                                                 | Effect           |
| ----------- | --------------------------------------------------------- | ---------------- |
| Announce    | `UAR_announce_neo_baathist_uar` :2 / `…_baathist_uar` :63 | below            |
| Invite      | `UAR_invite_country_neo_baathist_uar` :123 / :289         | subjects (below) |
| Leave       | `UAR_country_leaves_neo_baathist_uar` :455 / :604         | subject exits    |
| Falls apart | `UAR_neo_baathist_uar_falls_apart` :753 / `…` :805        | below            |
| Unite       | `UAR_unite_neo_baathist_uar` :917 / :1012                 | below            |
| Integrate   | `UAR_integrate_MAU` :1115 … `UAR_integrate_YEM` :2135     | cores            |

Details:

- Announce: `UAR_announce_neo_baathist_uar` (`emerging_autocracy`) / `UAR_announce_baathist_uar` (`nationalist_fascist`) set global `neo_baathist_uar_formed` / `baathist_uar_formed` (:42 / :102), country `formed_*` (:43 / :103), latch (:44 / :104), `set_cosmetic_tag = UAR_communism` / `UAR_nationalist` (:45 / :105), **sentinel** (:46-47 / :106-107). Both announces are hidden once latched (:7, :68).
- Falls apart: `timeout_effect` :770 / :822 drops the cosmetic, clears the ratchet vars (:773-774 / :825-826), `formed_*` and the global.
- Unite: sets global `*_uar_united` / country `united_*`; **clears `formed_*`** (:939 / :1034); needs `uar_has_required_gdp_share` (:931 / :1026; 40 % of Arab GDP); cores + annexes Arab subjects, wargoal on the rival UAR.
- Full second names of each pair: `UAR_announce_baathist_uar`, `UAR_invite_country_baathist_uar`, `UAR_country_leaves_baathist_uar`, `UAR_baathist_uar_falls_apart`, `UAR_unite_baathist_uar`.
- Announce cost 200; Announce/Unite `base = 100`. Invite: subjects via `autonomy_uar_regional_command` / `autonomy_uar_state`. Falls apart fires when the ruling ideology drifts.

Focus sites that form the UAR without the decision (both wired): `EGY_pan_arab_effort` (`05_egypt.txt:4385`) — neo-Ba'athist branch (cosmetic :4415, sentinel :4416-4417), Ba'athist branch (:4428, :4429-4430); the third branch (:4437-4441) is an `effect_tooltip` that never runs and carries no call. `LBA_strive_for_uar` (`05_libya.txt:11764`, :11795-11800) — Libya is a MAGHREB constituent, so without this site an AI Libya mid-MAGHREB would have `MAGHREB_update_flag` overwrite `UAR_communism`.

Pre-announce cosmetic sites, deliberately **not** sentinel sites: `EGY_negot_iraq` :4159 (cosmetic :4196), `EGY_friend_syria` :4214 (:4251), `EGY_negot_yemen` :4272 (:4309), `EGY_befr_libya` :4327 (:4364), `SYR_the_arab_union` (`05_syria.txt`, latch :13914), event `egypt.144` (`events/Egypt.txt`, :3209 / :3218). Since #3440 they latch (`mark_formed_country_formable`; their old `is_UAR` flag was dropped) but set no `formed_*` flag, so the UAR resets never apply to them; the announce or focus site that follows writes the sentinel. EGY/SYR are not decision-formable constituents, so there is no ratchet impact.

Revocation: `common/on_actions/99_UAR_on_action.txt` — `on_annex` (:29-56) resets FROM's cosmetic and flags (FROM ceases to exist; nothing to clear); `on_puppet` (:59-90) resets ROOT and clears both ratchet vars (:69-70, :83-84). Both key on `formed_*`, and `UAR_unite_*` clears `formed_*`, so a united-then-puppeted UAR keeps cosmetic and sentinel (pre-existing).

Ratchet: `MAGHREB_integrate_start` is hidden for a UAR (`NOT is_neo_baathist_uar` / `NOT is_baathist_uar`, `formable_nation_decisions.txt:10866-10867`) — the only decision-formable gate on a special identity (§6).

### 4.4 Yugoslavia restored (id 104)

`form_yugoslavia_effect` (`99_yugoslavia_scripted_effects.txt:166`): `set_cosmetic_tag = yugoslavia_restored` (:167), `add_ideas = formed_yugoslavia` (:168; `common/ideas/00_yugoslavia_ideas.txt:3`), sentinel (:169-170), `GLOBAL_yugoslavia_restored` (:178), invites successors through `yugoslavia.1` (:203; `events/yugoslavia_events.txt:6`) — an accepting successor is cored and annexed. The single site covers every caller: `yugo_form_federation` (`common/decisions/Yugoslavia.txt:82`; `is_yugo_dominant_trigger` + `yugoslav_consensus_trigger` :88-89; `base = 2` with +50 / +20 modifiers :101-107), `SER_restore_yugoslavia` (`05_serbia.txt:981`, call :1004), `KOS_restore_yugoslavia` (`05_kosovo.txt:2404`, :2428), `MNT_restore_yugoslavia` (`05_montenegro.txt:2377`, :2400). The gate is `has_idea = formed_yugoslavia`, not a flag. AI-reachable. Overlap: SLV/CRO/BOS are AUSHUN constituents. No revocation.

### 4.5 United States of Africa (id 105)

`AFRICAN_UNION_shared_focus_unite_africa` (`06_AfricanUnion_shared.txt:2619`; requires `African_Union_formed`, set `events/AfricanUnion.txt:39`): `African_Union_united` global (:2670), `set_cosmetic_tag = AFRICAN_UNION` (:2673), sentinel (:2674-2675), `is_united_states_of_africa` (:2688; achievement reader `MD_achievements.txt:334`; tag alias `UAF`, `common/country_tag_aliases/tag_aliases.txt:122`), members offered `AfricanUnion.3` / `AfricanUnion.2` (:2706, :2718) — accepters are cored and annexed or puppeted. Overlap: UAS (GAH/GUI/MAL) and MAGHREB constituents. No revocation.

### 4.6 Event Horizon blocs (id 106)

Scenario gate `EH_scenario_enabled` (`common/scripted_triggers/99_EH_scripted_triggers.txt:114`, `rule_event_horizon_scenario` not at default). Chain: `EH_convergence_event_chain_effect` (`99_EH_scripted_effects.txt:278`) → `EH_event.401` (:291; `events/Event Horizon.txt:292`) to a random North American country; each odd event (401, 403, … 421) picks a country of its region and fires the even formation event, which chains the next region. Every formation option: `drop_cosmetic_tag`, `set_cosmetic_tag = EH_*`, sentinel, kill the leader, `set_politics` neutrality, `load_focus_tree = event_horizon_generic_focus`, annex every AI country matching the region trigger, core all owned states, `EH_chimera_declares_war`. Forced (no `ai_will_do`), AI- and player-reachable. One id for all blocs.

| Event                | Bloc                       | cosmetic / sentinel |
| -------------------- | -------------------------- | ------------------- |
| `EH_event.402` :356  | `EH_USN` (North America)   | :367 / :368-369     |
| `EH_event.404` :479  | `EH_RCA` (Central America) | :490 / :491-492     |
| `EH_event.406` :598  | `EH_USM` (South America)   | :608 / :609-610     |
| `EH_event.408` :718  | `EH_EUF` (Europe + TUR)    | :729 / :730-731     |
| `EH_event.410` :841  | `EH_AFD`                   | :852 / :853-854     |
| `EH_event.412` :962  | `EH_CRU`                   | :973 / :974-975     |
| `EH_event.414` :1082 | `EH_ERF`                   | :1093 / :1094-1095  |
| `EH_event.416` :1203 | `EH_CHN`                   | :1214 / :1215-1216  |
| `EH_event.418` :1325 | `EH_ASE`                   | :1336 / :1337-1338  |
| `EH_event.420` :1444 | `EH_EAC`                   | :1455 / :1456-1457  |
| `EH_event.422` :1566 | `EH_ODU`                   | :1577 / :1578-1579  |

`is_european_federation_country` (`99_EH_scripted_triggers.txt:182`) is a continent test (Europe + TUR minus SOV/SOO/ABK/CHE/GEO/UKR/BLR), not a read of the `european_federation` flag. `different_country_flags_category` hides when `EH_scenario_enabled` (`categories/different_country_flags.txt:65`). The bloc ROOT (USA → USNA, BRA → SOU, …) stays a decision-formable constituent — hence the sentinel. Nothing in the EU scripts reads the scenario, so the EU keeps running (§8g). No revocation.

### 4.7 Not wired (documented only)

National-tree steps and sub-steps of a decision formable carry **no** sentinel: Estonia annexing LIT/LAT (`EST_dreams_of_union`) before BLT; the UK annexing CAN/AST/NZL before CANZUK; Commonwealth Federation; Dietsland; Pan-Turkic / Ottoman; Franco-German; Litbel; GCC; Iranic Confederation; TAJ Central Asia; Union State; Czechoslovakia; Korea; Karabakh; Cyprus; Vanguard; every cosmetic-only empire; the `EGY_negot_*` / `SYR_the_arab_union` pre-announce UAR sites; POTEF-tree annexations; `EST_european_federation` flavour. Spain → IBR is a **decision** commitment (id 5), not a sentinel. All rows in §5.

Rule for authors: add the two-line call only when the tree's identity must survive a later decision formable. A sub-step of a decision formable must **not** commit — it would block the formable it leads to.

## 5. Catalog of every union / identity mechanism

Kinds: `decision` (23 decision formables), `special` (§4), `decision-union` (decision outside the formables file), `focus-union` (annex/core + new identity from a focus), `event-union`, `cosmetic` (no annex/cores in the block). Ratchet field: `decision N/S` = commits id N size S; `sentinel N` = special commit; `none` = neither reads nor writes ratchet state; `sub-step` = leads into a decision formable, must not commit.

Paths: `common/` files may appear by basename alone — focus trees live in `common/national_focus/`, decisions in `common/decisions/`, categories in `common/decisions/categories/`, the rest per §1; `events/` files keep their prefix. Overflow references sit in the "Further anchors" list below the table.

- **23 decision formables** (decision; AI: yes (`base = 10` / 10000)) — `formable_nation_decisions.txt` (§2). Writes: `is_<TAG>`, `<TAG>_exists`, `reshaping_national_identity`, cosmetic `<TAG>`. Ratchet: decision 1-23.
- **Spain → Iberian Union** (focus-union; AI: `base = 1`, ratchet-gated) — `05_spain.txt:3041` (`SPR_declare_the_iberian_union`) … :3347 (`SPR_solidify_the_iberian_union`) §2. Writes: `IBR_exists`, `is_IBR`, cosmetic `IBR`, cores/annex POR+ADO. Ratchet: decision 5/24 (guarded).
- **United States of Europe (EU111)** (special; AI: yes (vote weights :207)) — `99_EU_voting_scripted_effects.txt:386` (§4.1). Writes: cosmetic `USoE`; flags `USoE`, `USoE_member`; `multi_ethnic_state_idea`; annexes members. Ratchet: sentinel 101.
- **European Federation (EU112) + EFS branding** (special; AI: yes (:208; base 10000)) — `99_EU_voting_scripted_effects.txt:847`; `MD_EFS_decisions.txt:6` (§4.2). Writes: global `european_federation`; cosmetic `EFS_<TAG>` / `EFS_IBR/SCA/BLT/WAS`; `EFS_flag_change`. Ratchet: sentinel 102.
- **`USoE_integrate_new_members`** (decision-union; AI: no (`base = 0` :184)) — `EU_USoE_decisions.txt:125`. Writes: cores + `USoE_member` for later joiners. Ratchet: none.
- **`USoE_reset_flag` / `USoE_AI_reset_flag`** (cosmetic; AI: AI variant only) — `MD_USoE_decisions.txt:5`, :17 (category `categories/formable_nations.txt:142-154`). Writes: cosmetic back to `USoE` (AI: from `USoE_*` variants only). Ratchet: none.
- **USoE dynastic / ideological variants** (cosmetic; AI: yes) — `set_USoE_flag_of_the_house` `99_eu_scripted_effects.txt:563`; `01_EU_USoE_shared.txt:1739`. Writes: cosmetic `USoE_SAV/WIT/BOR_ANJ/BOR/HAN/GLU/WIN/ORA/HAB/NAP/HOH`, `USoE_com/air/army/navy/green`. Ratchet: none (sentinel already held).
- **`EU_USoE_westernize_decision`** (expansion; AI: yes) — `EU_USoE_decisions.txt:33`. Writes: annex wargoals from the USoE. Ratchet: none.
- **POTEF-tree annexations** (focus-union; AI: yes) — `02_EU_POTEF_shared.txt:4555-4563` (LBA annexes GNA/GNC/HOR), :4798 (CYP annexes NCY). Writes: annex only, no cosmetic. Ratchet: none.
- **Estonia "European Federation" (flavour)** (cosmetic; AI: `base = 1`) — `05_estonia.txt:5134` (`EST_european_federation`), cosmetic :5152. Writes: cosmetic `EST_euro_federation`; cores of neighbours' states; `nationalist_fascist` gate. Ratchet: none (loc-name clash only).
- **Event Horizon blocs (11)** (special; AI: forced (event chain)) — `events/Event Horizon.txt:356` … :1566 (§4.6). Writes: cosmetic `EH_*`; annexes region; scenario flags. Ratchet: sentinel 106.
- **United Arab Republic** (special; AI: yes (`base = 100`)) — `UnitedArabRepublic.txt:2`, :63; `05_egypt.txt:4385`; `05_libya.txt:11764` (§4.3). Writes: cosmetic `UAR_communism` / `UAR_nationalist`; globals `*_uar_formed`; flags `formed_*`. Ratchet: sentinel 103; MAGHREB cross-gate :10866-10867.
- **UAR pre-announce cosmetic sites** (cosmetic; AI: yes) — `05_egypt.txt:4159`, :4214, :4272, :4327; `05_syria.txt`; `egypt.144` (§4.3). Writes: cosmetic `UAR_communism`; latch (`is_UAR` dropped, #3440). Ratchet: none — not sentinel sites (§4.3).
- **UAR invite / leave / unite / integrate** (decision-union; AI: yes (`base = 100`)) — `UnitedArabRepublic.txt:123`, :289, :455, :604, :917, :1012, :1115-2135. Writes: subjects; globals `*_uar_united`; cores. Ratchet: none beyond §4.3.
- **Union State (Russia ⇄ BLR/SER/UKR/ARM)** (decision-union; AI: belarus `base = 0` ×355 if BLR is AI; armenia `base = 1`) — `Union State.txt:651` (`USR_russia_reunite_with_belarus`), :914 (`USR_belarus_annex_russia`). Writes: cosmetic `BLR_UNS_Communism` (:680, :984, :1436) / `BLR_UNS_great` (:689); cores + annex. Ratchet: none.
- **Union State focuses** (focus-union; AI: `base = 355` / 100) — `05_russia.txt:8467` (`SOV_strengthen_union_state`); `05_ukraine.txt:17611` (below). Writes: cores BLR → SOV; UKR annexes SOV. Ratchet: none.
- **Iranic Confederation** (decision-union; AI: yes (`base = 10`)) — `common/decisions/Tajikistan.txt:732`, :765, :791, :814 (`IRN_announce_*`). Writes: cosmetic `IRN_confederation_early` :756 / `PER_iranic_federation` :825; latch :826; flags below. Ratchet: none.
- **Iranian civil-war latch sites** (latch; AI: yes) — `events/Iran.txt:17586`, :17955, :18426; `Tajikistan.txt:2365`. Writes: latch (their old `is_IRAN` flag was dropped by #3440). Ratchet: none — not a formable marker.
- **Socialist Commonwealth of Central Asia** (decision-union; AI: `base = 10`) — `Tajikistan.txt:1974` (`TAJ_workers_council_of_central_asia`). Writes: cosmetic `SCA_soviet_onion` :2059; latch :2060; cores KAZ/UZB/KYR/TAJ/TRK. Ratchet: none — reuses the `SCA` prefix, never touches `is_SCA`.
- **Union of Central Asian States** (cosmetic; AI: `base = 1`) — `05_tajikistan.txt:8225` (`TAJ_central_asian_state`, cosmetic :8244); integrations below. Writes: hidden cosmetic `TAJ_formable`; province renames. Ratchet: none — cosmetic-only despite the name.
- **Yugoslavia restored** (special; AI: yes (`base = 2`)) — `99_yugoslavia_scripted_effects.txt:166`; `Yugoslavia.txt:82`; focus callers below (§4.4). Writes: cosmetic `yugoslavia_restored`; idea `formed_yugoslavia`; `GLOBAL_yugoslavia_restored`. Ratchet: sentinel 104.
- **Czechoslovakia** (decision-union; AI: yes (`base = 100`)) — `Czech_Republic.txt:6187` (`CZE_SLO_border_removal_2`, cosmetic :6246); focus + events below. Writes: cosmetic `CZE_SLO_czechoslovakia`; flag `CZE_SLO_new_dawn_of_czechoslovakia_flag`; annex CZE ⇄ SLO. Ratchet: none.
- **Czechoslovakia (Russian sphere)** (event-union; AI: yes) — `events/Russia.txt:7427` (`sov_warsaw_pact.7`). Writes: CZE annexes SLO; cosmetic `CZR_union` (:7446). Ratchet: none.
- **Serbia-Montenegro** (cosmetic; AI: `base = 0`) — `common/decisions/Serbia.txt:381` (`SER_rename_nation`). Writes: cosmetic `SER_MNT` (:400) / back to `SER`. Ratchet: none.
- **Antillean Confederation** (cosmetic; AI: yes) — `common/decisions/Cuba.txt:1124` (`CUB_form_confederation`). Writes: cosmetic `CUB_confederation` (:1141); needs HAI/DOM/COL/JAM/PTR subjects. Ratchet: none.
- **Liechtenstein HRE** (decision-union; AI: `base = 3`) — `common/decisions/Liechtenstein.txt:123` (`LIC_form_HRE`). Writes: cosmetic `LIC_AUTH_SS` (:178); cores. Ratchet: none.
- **Kurdistan declaration** (decision-union; AI: yes) — `common/decisions/Kurdistan.txt:133` (`KUR_declare_kurdistan`). Writes: cosmetic `KUR_neutrality` (:157; hides `different_country_flags` :35); 8 cores. Ratchet: none.
- **Ottoman State / Turkic confederation** (decision-union; AI: yes) — `common/decisions/Turkey.txt` (`TUR_empower_sultan`, cosmetic :772); `turkey.txt:16781` (below). Writes: cosmetic `TUR_NEW_TURKIC_STATE`; flag `TUR_osmani` :16817; latch. Ratchet: none.
- **Pan-Turkic** (focus-union; AI: yes) — `turkey.txt:16736` (`TUR_pan_turkey`). Writes: cosmetic `TUR_PAN_TURKIC` :16760; latch :16762. Ratchet: none.
- **Ethiopia-Eritrea federation** (decision-union; AI: yes) — `common/decisions/Ethiopia.txt:375` (`ETH_federalise_ERI_flip`, cosmetic :406); event below. Writes: cosmetic `ETH_federation_ct` / `ERI_ETH`. Ratchet: none.
- **Nagorno-Karabakh** (decision-union; AI: yes) — `common/decisions/karabakh.txt:518` (`NKR_armenia_annex_nkr`); category `karabakh_categories.txt:1`. Writes: ARM annexes NKR; flag `karabakh_regulated_flag` (:548, :565); no cosmetic. Ratchet: none.
- **Korea reunification** (focus-union; AI: yes) — `03_joint_korea_confederation.txt:510`, :535, :612 (`KOR_confederation` :560); more below. Writes: flag `korea_peninsula_reunited`; no cosmetic. Ratchet: none.
- **Cyprus** (decision-union; AI: yes) — `Greece.txt:177` (`GRE_unify_cyprus`); `05_GRE_decisions.txt:755` (`TUR_unify_cyprus`); more below. Writes: states 145/146 transfer; cosmetic on NCY. Ratchet: none.
- **Vanguard bloc** (cosmetic; AI: yes) — `events/Turkey.txt:3101-3439` (12 latch sites); more below. Writes: cosmetic `TUR/PER/IRQ/SYR_VANGUARD`; latch (`is_VANGUARD` dropped, #3440). Ratchet: none.
- **Franco-German "European Socialist Republic"** (focus-union; AI: `base = 1`) — `05_germany.txt:19235` (`GER_german_franco_union`; event `germany.223`). Writes: cosmetic `GER_franco_german_union` :19279; latch :19280; annex FRA. Ratchet: none.
- **German empires / mandates** (cosmetic; AI: yes) — `05_germany.txt:20371` (`GER_our_long_lost_glory`, cosmetic :20396); more below. Writes: cosmetics `GER_fourth_reich` / `GER_german_empire` / `GER_holy_german_empire`; latch. Ratchet: none.
- **United Islamic Republics** (focus-union; AI: yes (`base = 10` decisions)) — `05_iran.txt:13668` (`PER_a_new_dawn`, cosmetic :13804), :16230 (`PER_reunification` → below). Writes: cosmetic `UNITED_ISLAMIC_REPUBLICS`; cores + annex subjects. Ratchet: none.
- **Turkey-Syria union** (focus-union; AI: yes) — `turkey.txt:16786` (`TUR_turkey_syria_union`); `events/Turkey.txt:4393`. Writes: cosmetic `TUR_TURKEY_SYRIA_UNION`; annex SYR. Ratchet: none.
- **Polish-Lithuanian Commonwealth / Visegrad** (focus-union; AI: `base = 50`) — `05_poland.txt:26299` (`POL_make_two_nations_one_again`, cosmetic :26349); Visegrad below. Writes: cosmetic `POL_LIT` / `POL_QUAD` / `POL_LIT_QUAD`; annex LIT; subjects. Ratchet: none.
- **Baltic union under Estonia** (focus-union; AI: yes) — `05_estonia.txt:3340` (`EST_dreams_of_union`). Writes: annex LIT/LAT; no cosmetic. Ratchet: sub-step of BLT (id 1).
- **Commonwealth Federation** (focus-union; AI: `base = 1`) — `05_united_kingdom.txt:20317` (`ENG_declare_the_commonwealth`, cosmetic :20374); Ireland below. Writes: cosmetic `ENG_commonwealth_federation`; annex 3 subjects; cores. Ratchet: sub-step of CANZUK (id 15).
- **Gulf super-state** (focus-union; AI: `base = 1`) — `gulf_shared.txt:1551` (`GCC_gulf_super_state`, cosmetic :1618); `05_saudi_arabia.txt:1544` (below). Writes: cosmetic `GCC`; cores + annex; two `*_completed` globals (below). Ratchet: none (not wired).
- **United States of Africa** (special; AI: yes) — `06_AfricanUnion_shared.txt:2619` (§4.5). Writes: cosmetic `AFRICAN_UNION`; `African_Union_united`; `is_united_states_of_africa`; cores + annex/puppet. Ratchet: sentinel 105.
- **Alpine Federation** (focus-union; AI: `base = 2`) — `05_switzerland.txt:6526` (`SWI_proclaim_the_alp_federation`, cosmetic :6547). Writes: cosmetic `SWI_alpine_federation`; cores. Ratchet: none.
- **Dietsland / Dutch Fourth Reich** (focus-union; AI: yes) — `05_netherlands.txt:35329` (`HOL_glorify_dietsland`, cosmetic :35351), :36985 (`HOL_fourth_reich`). Writes: cosmetic `HOL_dietsland` / `HOL_fourth_reich`; cores 50/51; annexes. Ratchet: none (HBL constituent, not wired).
- **Litbel** (focus-union; AI: `base = 150`) — `05_belarus.txt:13505` (`BLR_the_litbel`, cosmetic :13545), :13594 (`BLR_litbel_annex_lat`). Writes: cosmetic `BLR_Litbel`; annex LIT/LAT. Ratchet: none (not wired).
- **Islamic Republic of Lebanon** (focus-union; AI: `base = 0`) — `05_Hezbollah.txt:3973` (`HEZ_Shias_Lebanon`). Writes: annex LEB. Ratchet: none.
- **Union of Slavic Republics** (focus-union; AI: yes) — `05_ukraine.txt:18139` (cosmetic `UKR_SlavicUSSR`; 8 subjects). Writes: cosmetic; subjects. Ratchet: none.
- **Union of Democratic States** (event-union; AI: yes) — `events/Ukraine.txt:6293` (`ukraine_kommi.8`). Writes: annex PMR/HUN/BLR/MLV. Ratchet: none.
- **West-Balkan Federation** (event-union; AI: yes) — `events/Serbia.txt:4141` (`kosovo.8`; cosmetic :4150, latch :4152). Writes: cosmetic `KOS_AUTH`; latch (`is_KOS` dropped, #3440); annex ALB. Ratchet: none.
- **Greater Serbia** (focus-union; AI: yes) — `05_serbia.txt:4137` (`SER_integrate_bosnia`). Writes: annex RSK. Ratchet: none.
- **Bosnian Federal Republic** (event-union; AI: yes) — `events/bosnia_events.txt:1272` (`BOS_political.2`, cosmetic :1283), :1294 (`.3`, `bos_fed2` :1312). Writes: cosmetic `bos_fed` / `rsk_fed` / `hzg_fed` → `bos_fed2`; annex. Ratchet: none.
- **China SAR integrations / Mongolia** (focus-union; AI: yes) — `05_china.txt:23672` (`CHI_SAR_integrate_HKG`) … :28613 (`_OMG`); Mongolia below. Writes: cores / annex; no cosmetic. Ratchet: none (the dead `is_CHINA` reader was removed by #3440).
- **Benelux union** (focus-union; AI: yes) — `03_benelux_shared.txt:752` (`BNL_treaty_of_union`). Writes: puppets BEL/LUX; no cosmetic; bypass `is_HBL` (:776). Ratchet: reads `is_HBL`.
- **Italian integrations** (decision-union; AI: yes) — `common/decisions/Italy.txt:2` (`integration_britannia` …). Writes: cores. Ratchet: none.
- **Country-flag decisions (GER/USA)** (cosmetic; AI: yes) — `common/decisions/Country Flag Decisions.txt:905` (`USA_51`), :908 (`USA_52`), :986 (`GER_empire`). Writes: cosmetic. Ratchet: none.

Further anchors:

- Spain → Iberian Union: `05_spain.txt:3150`, :3195; `events/Spain.txt:3540` (`spain.60`).
- UAR pre-announce cosmetic sites: `events/Egypt.txt:3146` (`egypt.144`).
- Union State: `common/decisions/Union State.txt:1406` (serbia), :2019 (ukraine), :2645 (armenia); category `union_state_decision_categories.txt:1`.
- Union State focuses: `05_ukraine.txt:17611` (`UKR_propose_full_union_state`).
- Iranic Confederation: category `99_TAJ_decision_categories.txt:107`; unlock `05_tajikistan.txt:680`, `05_iran.txt:21180`; event `iranic_confederation.7` `events/Tajikistan.txt:5006`; writes flags `iranic_confederation_member`, `disable_different_country_flag` (:757).
- Socialist Commonwealth of Central Asia: category `TAJ_soviet_onion` `99_TAJ_decision_categories.txt:129`; unlock `05_tajikistan.txt:4164`; the UZB islamist split-off latches at `05_tajikistan.txt:2615`.
- Union of Central Asian States: `TAJ_kyrgzy_integration` :7859, `TAJ_uzbek_integration` :7928 (`05_tajikistan.txt`).
- Yugoslavia restored focus callers: `05_serbia.txt:981`; `05_kosovo.txt:2404`; `05_montenegro.txt:2377`.
- Czechoslovakia: `06_czehcoslavakia_shared.txt:1930` (`CZE_SLO_new_dawn_of_czechoslovakia`, annex :1980/:1988); `events/Czech Republic.txt:6121` (`CZE_SLO_event.6`, cosmetic :6147), :6432 (`.12`).
- Ottoman State / Turkic confederation: `turkey.txt:16781` (`TUR_osman_alliance`, `TUR_osmani` :16817); categories `99_TUR_decision_categories.txt:18`, :28.
- Ethiopia-Eritrea federation: `events/Ethiopia.txt` `ethiopia.24` (cosmetic :783).
- Korea reunification: `05_north_korea.txt:9461` (`NKO_united_again`, :9509); `05_south_korea.txt:2431` (`KOR_juche_in_the_south`, :2461); `events/Korea.txt:1327` (`korea.27`), :1674 (`.35`), :1995 (`.42`); `99_KOR_on_actions.txt:37`, :49; categories `00_korea_category.txt:1`, :14, :48.
- Cyprus: `TUR_unify_cyprus` sets the NCY cosmetic `CYP_TURK_UNIFIED` and latches (`05_GRE_decisions.txt:788`); `05_greece.txt:11133` (`GRE_cyprus_reunification`).
- Vanguard bloc: `05_GRE_decisions.txt:788`; cosmetics `events/Turkey.txt:3101-3371`.
- Franco-German "European Socialist Republic": `is_GERMAN` was dropped by #3440; the site latches instead (:19280).
- German empires / mandates: `05_germany.txt:21856` (`GER_restore_the_empire` → `germany.218`, latch `events/Germany.txt:4328`, :4338), SWI/AUS/BEL mandates.
- United Islamic Republics: `PER_reunification` (`05_iran.txt:16230`) → `common/decisions/Iran.txt:3466` (`PER_integrate_*`).
- Polish-Lithuanian Commonwealth / Visegrad: `05_poland.txt:21362` (`POL_quadruple_alliance`, :21409).
- Commonwealth Federation: `05_ENG_decisions.txt:1523` (`ENG_integrate_ireland`).
- Gulf super-state: `05_saudi_arabia.txt:1544` (`SAU_unif_khaleeji_union`, :1599); globals `GCC_gulf_super_state_completed` / `SAU_unif_khaleeji_union_completed`.
- China SAR integrations / Mongolia: `05_china.txt:28936` (`CHI_MON_reunification_offer`).

Cosmetic-only identities (no annex or cores in the block; flavour / easter egg; none read or write ratchet state):

- `SWE_Swedish_empire` — `05_sweden.txt:16663`, :16674
- `ITA_RomanEmpire` / `ITA_RomanEmpire2` — `05_italy.txt:3510`, :3522
- `SOV_hyper_empire` (hides `different_country_flags` :46) — `05_russia.txt:7994`
- `SOV_soviet_empire`, `SOV_USA` — `05_russia.txt:13010`, :18074
- `SOV_romanov_empire` — `events/Russia.txt:5757`
- `RAJ_AUTH_SS`, `RAJ_Empireofsun` — `05_india.txt:13942`, :14924
- `ARM_armen_empire_nationalist` — `05_armenia.txt:7932`
- `ARM_United_States` — `events/Armenia.txt:7313`
- `GRN_Frozen_Federation`, `GRN_Kingdom_Of_Greenland` — `05_greenland.txt:21424`, :9034
- `LBA_LIBYAN_FEDERATION` — `05_libya.txt:3650`
- `BRM_Burma_federation`, `BRM_Myanmar_federation` — `05_myanmar.txt:1592`, :1777, :1781
- `CAS_pan_pacific_union` — `05_cascadia.txt:14296`
- `USB_MidAtlantic_Union`, `USB_UFSR` — `05_free_states_of_america.txt:4293`, :1865
- `LKT_Continental_Confederation` — `05_republic_of_lakota.txt:12681`
- `CSA_southern_union`, `CSA_united_southern_states` — `events/Southern Republic of America.txt:2019`, :2041
- `FRA_empire`, `FRA_Occident_Empire`, `FRA_Kingdom_Jerusalem` (37 cores) — `events/France.txt:7518`, :9380, :9738
- `JAP_EMPIRE`, `JAP_EMPIRE_NAVAL` — `events/05_japan.txt:382`, :392
- `BUL_empire`, `BUL_empire2` — `events/05_bulgaria.txt:341`, :335
- `SYR_Federal_State` — `05_syria.txt:7772`
- `BLR_GLI` — `05_belarus.txt:5086`
- `SAU_republic_of_arabia` — `05_saudi_arabia.txt:9850`, :10094
- `BHR_REP`, `KUW_REP`, … — `gulf.txt:3455-3475`
- `KHM_Russia_nationalist` / `_democratic` — `Khanti-mansi.txt:2484`, :2491

The remaining ~350 `set_cosmetic_tag` hits are ideology or civil-war variants (`*_AUTH_*`, `*_REB_*`, `GOV_*` Russian governorates, `IRQ_*` insurgents, `Nazbols_*`, …) — not identities.

### Dead / ambiguous references

- `is_CHINA` and the other per-identity flags (`is_UAR`, `is_GERMAN`, `is_VANGUARD`, `is_KOS`, `is_IRAN`, `is_TAJIKISTAN`) were dropped by #3440 — `formed_country_formable` replaced them everywhere.
- `SOV_reunification_mission` (`common/decisions/Russia.txt:4816`) has `allowed` and `available = { always = no }` (:4817-4818) — dead.
- `EST_euro_federation` localises as "European Federation", the EU112 name; mechanically unrelated to `european_federation`.
- `SCA_soviet_onion` (`Tajikistan.txt:2059`) reuses the `SCA` prefix but never touches `is_SCA` / `SCA_exists`.
- `TAJ_formable` (`05_tajikistan.txt:8244`) is named like a formable and is cosmetic-only.
- `is_european_federation_country` (`99_EH_scripted_triggers.txt:182`) is a continent trigger; it does not read the `european_federation` flag.
- `usoe_formed` (`01_EU_USoE_shared.txt:309`) is commented out — there is no global "USoE formed" flag; use `has_country_flag = USoE` on the country.

## 6. Cross-guard matrix

All lines in `common/decisions/formable_nation_decisions.txt` unless noted. "EU guard" = the `visible` condition that hides an `update_flag`; `european_federation` is a **global** flag, so those guards fire worldwide (§8a).

- **BLT** — `update_flag` EU guard: `NOT european_federation` (:310) + `NOT EU_member` (:311); `integrate_start` AI EU block: none (:5-21 — the Baltic trap, §8b); CANZUK exemption: none; special cross-gate: none.
- **CANZUK** — `update_flag` EU guard: `NOT OR { european_federation :9209, EU_member :9210, has_cosmetic_tag CANZUK :9211 }`; `integrate_start` AI EU block: `factor = 0` on `european_federation` OR `EU_member` (:8680-8687); CANZUK exemption: source of the exemption; special cross-gate: none.
- **MAGHREB** — `update_flag` EU guard: `NOT OR { european_federation :11537, EU_member :11538, has_cosmetic_tag MAGHREB :11539 }`; `integrate_start` AI EU block: none; CANZUK exemption: none; special cross-gate: `integrate_start` visible `NOT is_neo_baathist_uar` / `NOT is_baathist_uar` (:10866-10867); below.
- **ANZ** — `update_flag` EU guard: none (:2936-2939); `integrate_start` AI EU block: no `integrate_start`; CANZUK exemption: all 3 decisions (:2706, :2829, :2927); special cross-gate: none.
- **NORDEM** — `update_flag` EU guard: none (:10621-10624); `integrate_start` AI EU block: none; CANZUK exemption: all 7 decisions (:10055 … :10770); special cross-gate: none.
- **AVG** — `update_flag` EU guard: none (:15432-15435); `integrate_start` AI EU block: none; CANZUK exemption: all 6 decisions (:15056 … :15533); special cross-gate: none.
- **SCA, IBR, HBL, AUSHUN** — `update_flag` EU guard: none (:2171-2174, :2610-2613, :4799-4803, :13694-13697); EFS players can still click them (§8c); `integrate_start` AI EU block: none / no `integrate_start` (IBR); CANZUK exemption: none; special cross-gate: none.
- **FCA, GCL, SOU, USNA, UTS, MAPHI, INDOCHI, ANDES, ANTCONF, RDLP, WESTFED, PBL, UAS** — `update_flag` EU guard: none; `integrate_start` AI EU block: none; CANZUK exemption: none; special cross-gate: none.
- **`EFS_update_flag` (`MD_EFS_decisions.txt:6`)** — `update_flag` EU guard: `visible = { NOT EFS_flag_change }` only; `integrate_start` AI EU block: no ratchet gate, no exemption — writes sentinel 102; CANZUK exemption: none; special cross-gate: reads `is_IBR/is_SCA/is_BLT`.

Details:

- MAGHREB ↔ UAR: `form_UAR_category` hidden when `is_MAGHREB` (`UnitedArabRepublic_categories.txt:10`).

The `european_federation` reads at :2708, :2831, :2929, :10057 … :15535 are the exemption blocks (§3), not guards. All 23 categories additionally apply the latch if/else (§2): once latched, only started formables' categories are visible at all.

## 7. Game-rule coverage

Rules live in `common/game_rules/00_game_rules.txt`.

| Rule                                                  | Runtime state                        |
| ----------------------------------------------------- | ------------------------------------ |
| `rule_disable_formable_nations` (:353)                | `GAME_RULE_disable_formable_nations` |
| `rule_disable_eu` (:386)                              | `GAME_RULE_eu_disabled`              |
| `rule_enable_ai_european_union_end_game_paths` (:456) | read directly via `has_game_rule`    |
| `rule_event_horizon_scenario` (:3872)                 | `EH_scenario_enabled`                |

Details:

- Flag sources: `999_game_rules_on_actions.txt:415-424`; `99_eu_scripted_effects.txt:604-620`; `99_EH_scripted_triggers.txt:114`.
- `rule_disable_formable_nations`: read by the 23 `form_<TAG>_category` blocks and, since #3440, `form_UAR_category` (`UnitedArabRepublic_categories.txt:10`) — hides them all; sentinel writes stay inert but harmless. EU111/EU112, Yugoslavia, United States of Africa, Event Horizon, Spain's IBR focus and every other §5 mechanism stay formable.
- `rule_disable_eu`: read by the EU setup (`99_eu_scripted_effects.txt:134`, :164, :189, :681) — no EU, so EU111/EU112 are unreachable and `EFS_flag_category` never appears.
- `rule_enable_ai_european_union_end_game_paths`: GUI AI weights (`01_european_union_guis.txt:4548-4552`, :5190-5194); `option = no` → `factor = 0` on the AI proposing agendas 110/111/112 — the **only** AI kill switch for USoE/EFS; players unaffected (§8j).
- `rule_event_horizon_scenario`: read by `EH_convergence_event_chain_effect` and `categories/different_country_flags.txt:49` — enables the Event Horizon chain and hides flag-change decisions. The EU system does not read it.

## 8. Known traps / accepted behaviour

All pre-existing or accepted; none changed by the sentinel or latch work unless stated.

- **(a) `european_federation` leaks onto non-EU formables.** The global flag hides `MAGHREB_update_flag` (:11537) and `CANZUK_update_flag` (:9209) worldwide and AI-blocks `CANZUK_integrate_start` (:8680-8687) once any European federation exists. An AI Morocco/Canada committed mid-formable is stranded with `reshaping_national_identity` (-15 % stability) and no remover; MAGHREB has no EU-member constituent, so the guard is either a deliberate "no new Maghreb once Europe federates" rule or a copy-paste — author intent unverified. Pre-existing content decision; deferred. Post-#3440 a latched CANZUK-committed AI also has the NORDEM/AVG/ANZ categories hidden, so the §3 exemptions only help pre-latch saves.
- **(b) Baltic trap.** `BLT_integrate_start` (:5-21) has no EU gate while `BLT_update_flag` is hidden for `EU_member` (:311). EST/LAT/LIT are EU members from 2004, so an AI that starts BLT carries the permanent -15 % stability idea; the only remover is the hidden decision (:352). Fix options: drop the `EU_member` line, or add an EU AI block to `BLT_integrate_start` mirroring CANZUK's.
- **(c) Player-side EFS/USoE clobber.** `SCA/IBR/HBL/NORDEM/AUSHUN/AVG_update_flag` have no EU guard (:2171-2174, :2610-2613, :4799-4803, :10621-10624, :13694-13697, :15432-15435). After `EFS_update_flag` sets `EFS_SCA`, `SCA_update_flag` becomes visible again (`NOT has_cosmetic_tag = SCA`); a **player** may click it and permanently lose EFS branding (`EFS_flag_change` is one-shot, `MD_EFS_decisions.txt:10`, :283). Same for a player USoE ROOT holding `is_<TAG>`; `USoE_AI_reset_flag` (`MD_USoE_decisions.txt:17`) only resets from `USoE_*` variants. The AI no longer does this thanks to the sentinel. Do not fix by copying BLT's `EU_member` guard — that is trap (b) for every EU-member player.
- **(d) EFS variants exist only for IBR/SCA/BLT.** A completed HBL/AUSHUN/NORDEM/AVG member gets a plain `EFS_<TAG>` ("EFS Netherlands", not "EFS Benelux") from `EFS_update_flag`'s `else` branches and — post-sentinel — stays on it. Adding `is_HBL/is_AUSHUN/is_NORDEM/is_AVG` branches plus sprites is a follow-up.
- **(e) Member mid-formable when EU112 passes.** `EFS_update_flag` writes sentinel 102 for every member the day after the vote, including a leader mid-integration (Sweden with `is_SCA` but DEN/NOR/FIN not yet integrated). Intended: special beats decision. Consequences: a running `days_remove` integrate still resolves (ai_will_do only affects selection); every remaining integrate, `update_flag` and `buy_core_state` for that formable is AI-blocked forever; `is_SCA` alone brands it `EFS_SCA` (`MD_EFS_decisions.txt:74-75` etc.), so a half-Scandinavia shows as "EFS Scandinavia"; `SCA_exists` stays set so no other Nordic AI can start it; cores already granted stay. Player unaffected.
- **(f) UAR unreachable mid-MAGHREB.** `form_UAR_category` is hidden when `is_MAGHREB` (`UnitedArabRepublic_categories.txt:10`) and `MAGHREB_integrate_start` is hidden for a UAR (:10866-10867). Since #3440 both announces are also hidden for any latched country (:7, :68) — and starting MAGHREB latches. The only remaining route is `LBA_strive_for_uar` (`05_libya.txt:11764`), which writes latch and sentinel.
- **(g) Event Horizon bloc that later passes EU112.** Nothing in the EU scripts reads `EH_scenario_enabled`, so an `EH_EUF` ROOT that is still `EU_member` can pass EU112 (a lone member clears the 0.65 ratio) and `EFS_update_flag` (base 10000) re-brands it `EFS_<TAG>`, sentinel 106 → 102. Ratchet-consistent; accepted.
- **(h) `<TAG>_exists` is never cleared.** No `clr_global_flag = *_exists` exists. A formed SCA/IBR/BLT annexed into the USoE or an EH bloc leaves `form_<TAG>_category` hidden for any re-emerged constituent (civil-war split-offs and re-emerged countries start with unset variables and are otherwise free).
- **(i) Old saves.** A save where the special formable already formed never receives the sentinel (`EFS_update_flag` already consumed, EU111/UAR/Yugoslavia/AU/EH sites already fired). Dev builds may invalidate saves; no migration.
- **(j) AI never federates.** The only AI kill switch for EU110/111/112 is `rule_enable_ai_european_union_end_game_paths = no` (`01_european_union_guis.txt:4548-4552`, :5190-5194). Check it first. Nothing in EU voting reads stability, ratchet state, `reshaping_national_identity` or cosmetics — the sole stability read in the voting system is the EU202 Banking Union bonus (`99_EU_voting_scripted_effects.txt:272-277`) and it makes a low-stability member _more_ likely to vote yes.
- **(k) The ratchet never gates a special formable.** Zero readers of `formable_committed_*`, `reshaping_national_identity`, `is_<TAG>` or `has_cosmetic_tag` in `99_EU_voting_scripted_effects.txt`, `99_EU_voting_scripted_triggers.txt`, `99_eu_scripted_effects.txt`, `99_EU_scripted_triggers.txt`, `01_european_union_guis.txt`, `EU_voting_decisions.txt`, `EU_POTEF_decisions.txt`, `01_EU_USoE_shared.txt`, `02_EU_POTEF_shared.txt`; repo-wide `formable_committed_` readers are the formables file, `05_spain.txt`, `commit_special_formable`, the UAR revocations and the validator. A country stuck with `reshaping_national_identity` cannot fail any EU trigger it previously passed.
- **(m) The latch is permanent and pre-emptive.** `reshaping_national_identity` `on_add` latches at `integrate_start`, so a country that starts and later abandons a formable never sees another formable category or a flag-change decision again (player and AI). Stricter than the ratchet's strictly-larger rule and supersedes it after the first start; revocations (UAR falls-apart, `on_puppet`) clear the sentinel but never the latch. Accepted — #3440's design.
- **(l) No generic sentinel revocation.** Only the UAR clears the sentinel (falls-apart timeouts, `on_puppet`). Any other path that drops a special cosmetic (an ideology event's `drop_cosmetic_tag`) leaves `formable_committed_size = 1000` on the country, AI-blocking all 23 decision formables. Accepted: the sentinel follows the identity's own revocation sites, and only the UAR has any (`leaving_EU` is not one — it never drops the EFS cosmetic, so an EFS leaver keeps identity and sentinel by design). A new special formable with a dissolution path must clear both variables there.

## 9. Maintenance rules

### New decision formable

1. Category in `categories/formable_nations.txt` with the standard latch-aware `visible` (§2); nation gate in `allowed`.
2. Decisions in `formable_nation_decisions.txt`: `<TAG>_integrate_start`, `<TAG>_integrate_<SUB>` per constituent, `<TAG>_update_flag`, `<TAG>_buy_core_state`. `integrate_start` sets `is_<TAG>`, `<TAG>_exists`, adds `reshaping_national_identity`; `update_flag` sets the cosmetic and removes the idea.
3. Pick the next free id **below 100** (currently 24). Size = the `update_flag` state-list count.
4. Gate on **every** decision; commit in `integrate_start` and `update_flag`; guarded (`less_than`) commit on any delayed or ungated site (a `remove_effect`, a focus).
5. Never use `commit_special_formable` or a literal >= 100 in the formables file.
6. Editing an `update_flag` state list means updating that formable's size literal at **every** gate and commit site (and the Spain focus for IBR); the validator diffs them.
7. If the `update_flag` must be hidden by an EU guard, also AI-block `integrate_start` under the same condition (CANZUK pattern) and extend the exemption to any fallback formable — otherwise you create trap (b).
8. Flag-change decisions and other formable categories hide automatically once `integrate_start` runs (the `reshaping_national_identity` `on_add` latch, §2); add achievements if wanted.
9. Run `python tools/validation/validate_decisions.py` (CI runs it) and `python -m pytest`.

### New special formable

1. Take the next free id >= 100 (currently 107). Add it to `_SPECIAL_FORMABLE_IDS` in `tools/validation/validate_decisions.py` (:480-487) with a short name.
2. At every site that adopts the identity — after the `set_cosmetic_tag`, outside any `effect_tooltip`, in one of the scanned directories — add exactly (the effect also latches, §2):
   `set_temp_variable = { special_formable_id = <ID> }` followed immediately by `commit_special_formable = yes`.
3. One id per identity, however many cosmetics or sites it has (Event Horizon: one id for eleven blocs).
4. If the identity can be dissolved, `clear_variable = formable_committed_id` and `clear_variable = formable_committed_size` at each dissolution site (UAR pattern). The latch stays (§8m).
5. Add the row to the sentinel table in §4 and a subsection if the chain is non-trivial. The table is a mirror; the dict is the truth.
6. Add a test in `tools/tests/validation/validate_decisions_formable_commitment_test.py` if the site shape is new; run `python -m pytest`.
7. Never write `1000`, `formable_committed_size` or an id >= 100 inline anywhere outside `commit_special_formable`. Never add a `less_than` guard to a special commit — it must override.
8. Do not add a sentinel to a sub-step of a decision formable (§4.7).

### Validator (`validate_formable_commitment_sync`, CI-gating)

Scans `common/decisions`, `common/national_focus`, `common/scripted_effects`, `common/on_actions`, `events` (`_COMMIT_SCAN_DIRS`, `validate_decisions.py:501-507`) for texts containing `formable_committed_`, `special_formable_id` or `commit_special_formable`; a call site outside those directories is invisible to the "no call site" check, so keep calls inside them. `effect_tooltip` bodies are stripped before matching.

- `<decision> - not a formable decision shape` — formables-file token ≠ `<TAG>_(integrate_start\|integrate_<SUB>\|update_flag\|buy_core_state)`
- `<TAG>: no update_flag available block - cannot derive size` — `update_flag` missing or has no `available`
- `<decision> - missing commitment gate (no formable_committed_size literal)` — a decision without the §3 gate
- `<decision> - size literal N != <TAG> update_flag state count M` — state list edited without updating the literal (or vice versa)
- `<TAG>: conflicting commit ids [...]` / `<TAG>: no commit write (...)` — commit sites disagree, or none exist
- `<TAG>: commit id N is in the reserved special range (>= 100)` — decision formable used a special id
- `<TAG>: commit id N collides with <OTHER>` — id reused
- `<decision> - gate id G != <TAG> commit id F` — gate copied from another formable
- `<decision> - references unknown formable id R` — an exemption or guard names an id nobody commits
- `<path>: commit references unknown formable id I` — a focus or effect commit (Spain) drifted (id)
- `commit size S != update_flag state count M for id I` — a focus or effect commit (Spain) drifted (size)
- `<path>: guard size V matches no formable state count` — a `less_than` / `>=` guard value drifted
- `<decision>: decision formables commit by id/size, not commit_special_formable` — sentinel call inside the formables file
- `special sentinel size 1000 does not exceed the largest formable state count N` — a formable grew past 1000 states — raise `_SPECIAL_COMMIT_SIZE` and the effect together
- `<path>: commit_special_formable must set formable_committed_id = …` (full text below) — the effect definition drifted
- `<path>: sentinel size literal N outside commit_special_formable` — `formable_committed_size = 1000` (or any >= 100) written inline
- `<path>: special formable id N written inline - use commit_special_formable` — `formable_committed_id = <special>` written inline
- `<path>: N special_formable_id setter(s) not immediately followed by commit_special_formable = yes` — orphan setter
- `<path>: N commit_special_formable call(s) without a preceding special_formable_id setter` — call without setter
- `<path>: unknown special formable id N (add it to _SPECIAL_FORMABLE_IDS)` — setter uses an id not in the table
- `00_formable_effects.txt: expected exactly one commit_special_formable definition, found N` — effect missing, duplicated, or moved out of that file
- `special formable id N (name) has no call site - remove it from _SPECIAL_FORMABLE_IDS` — table id with no live call (tooltip-only calls do not count)

Details:

- Full row text: `<path>: commit_special_formable must set formable_committed_id = special_formable_id and formable_committed_size = 1000`.

Tests: `tools/tests/validation/validate_decisions_formable_commitment_test.py` — decision rows (`test_consistent_formable_clean` … `test_focus_commit_consistent_clean`, :62-140) and special rows (`test_special_commit_clean`, `test_special_unknown_id_flagged`, `test_special_orphan_setter_flagged`, `test_special_call_without_setter_flagged`, `test_special_definition_drift_flagged`, `test_special_definition_missing_flagged`, `test_unused_special_id_flagged`, `test_special_size_must_exceed_largest_formable`, `test_sentinel_literal_outside_effect_flagged`, `test_effect_tooltip_call_is_not_a_call_site`, `test_special_call_in_formables_file_flagged`, `test_decision_commit_id_in_special_range_flagged`, :164+). The suite must stay green; CI runs `python -m pytest` on any `tools/` change.
