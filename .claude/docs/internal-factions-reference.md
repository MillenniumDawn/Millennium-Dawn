# Internal Factions v3 Reference

Source of truth for epic #4260, the Internal Factions v3 rebuild. The registry
lives in `setup_global_arrays` in `common/scripted_effects/00_startup_effects.txt`.
This doc replaces, over steps 1-11, the old system built from these files:
`common/ideas/AA_law_internal_factions.txt`,
`common/scripted_effects/00_internal_faction_effects.txt`,
`common/scripted_triggers/00_internal_factions_trigger.txt`,
`common/dynamic_modifiers/05_internal_factions_modifiers.txt`,
`common/decisions/00_internal_factions.txt`, `events/Internal Faction Events.txt`,
and loc `localisation/english/MD_internal_factions_l_english.yml`.
Every v3 identifier (arrays, effects, triggers, GUI names, loc keys, registry
vars, file constants, temp vars) carries the `internal_faction_` prefix.

## Decisions closed here

Open questions 1-4 and 8 from the epic are closed as of this step.

| #   | decision                                                                             |
| --- | ------------------------------------------------------------------------------------ |
| 1   | The `change_<f>_opinion` wrappers stay permanently, even after step 11.              |
| 2   | Every faction gets exactly 3 privileges plus 1 crackdown, uniform stride.            |
| 3   | Multiple privileges stack: +10 opinion, +10 influence target each, cap +20/+20.      |
| 4   | The 23 per-faction dynamic modifier blocks stay; bonuses and policy vars share them. |
| 8   | `autocrats_opinion_change` is dropped in step 11.                                    |

## Global registry (table A)

Ids are 1-based; index 0 is reserved and never read. Category: 1 economic,
2 military-industrial, 3 mass, 4 religious, 5 nation-specific. The
availability column reuses the `allowed`/`available` blocks already in
`AA_law_internal_factions.txt`; the line numbers below point at that old file.

| id  | token                        | cat | inf | availability (old idea, line)                       |
| --- | ---------------------------- | --- | --- | --------------------------------------------------- |
| 1   | small_medium_business_owners | 1   | 30  | not KOR, NKO (L23)                                  |
| 2   | international_bankers        | 1   | 30  | not USA (L55)                                       |
| 3   | fossil_fuel_industry         | 1   | 25  | generic (L89)                                       |
| 4   | industrial_conglomerates     | 1   | 35  | not oligarch-state tag list (L112)                  |
| 5   | oligarchs                    | 1   | 40  | oligarch party ruling/coalition, or tag list (L163) |
| 6   | maritime_industry            | 2   | 20  | any owned coastal state (L248)                      |
| 7   | the_military                 | 2   | 40  | not `has_idea = no_military` (L301)                 |
| 8   | defense_industry             | 2   | 30  | generic (L276)                                      |
| 9   | intelligence_community       | 2   | 30  | not PAK (L327)                                      |
| 10  | labour_unions                | 3   | 30  | not nationalist/fascism government (L361)           |
| 11  | landowners                   | 3   | 25  | generic (L387)                                      |
| 12  | farmers                      | 3   | 25  | generic, hidden for LBA (L412)                      |
| 13  | communist_cadres             | 3   | 40  | communist ruling group (L442)                       |
| 14  | the_priesthood               | 4   | 25  | buddhism/hindu/shinto/cheondo idea (L477)           |
| 15  | the_ulema                    | 4   | 30  | sunni/ibadi/sufi_islam/shia, NIG special (L514)     |
| 16  | the_clergy                   | 4   | 25  | christian idea family, NIG special (L551)           |
| 17  | wahabi_ulema                 | 4   | 35  | AQY ISI SAU QAT UAE NUS SHB + sunni family (L594)   |
| 18  | the_donju                    | 5   | 25  | NKO (L646)                                          |
| 19  | saudi_royal_family           | 5   | 40  | SAU QAT BHR OMA KUW (L675)                          |
| 20  | iranian_quds_force           | 5   | 35  | tag list + communism/neutral/nationalist gov (L707) |
| 21  | foreign_jihadis              | 5   | 20  | fascism government (L763)                           |
| 22  | wall_street                  | 5   | 40  | USA (L797)                                          |
| 23  | chaebols                     | 5   | 40  | KOR (L831)                                          |

Religious factions 14-17 stay mutually exclusive: one religious slot per
country, as the old idea blocks already encode.

## Party affinity (table B)

Policy groups come from `global.ip_party_policy_group`
(`00_startup_effects.txt:75-104`): 1 communist, 2 socialist, 3 green,
4 conservative, 5 religious conservative, 6 liberal, 7 autocrat, 8 oligarch,
9 fascist, 10 monarchist, 11 emerging fundamentalist, 12 salafist. Lookup:
`global.internal_faction_affinity^(id * 13 + global.ip_party_policy_group^ruling_party)`.

| id  | faction            | backs (+1)  | opposes (-1)          |
| --- | ------------------ | ----------- | --------------------- |
| 1   | SMBO               | 6, 4        | 1, 8                  |
| 2   | bankers            | 6, 4        | 1, 2, 9               |
| 3   | fossil fuel        | 4, 7, 8     | 3, 1                  |
| 4   | conglomerates      | 4, 6, 7     | 1, 3                  |
| 5   | oligarchs          | 8, 7        | 6, 1                  |
| 6   | maritime           | 6, 4        | 1                     |
| 7   | military           | 7, 9, 10, 4 | 1, 3, 2               |
| 8   | defense industry   | 4, 7, 9     | 3, 2                  |
| 9   | intelligence       | 7, 4, 9     | 6, 3                  |
| 10  | unions             | 2, 3, 1     | 9, 8, 6               |
| 11  | landowners         | 4, 10, 8    | 1, 2                  |
| 12  | farmers            | 4, 5, 2     | 8                     |
| 13  | cadres             | 1           | 6, 9, 8               |
| 14  | priesthood         | 5, 4, 10    | 1, 3                  |
| 15  | ulema              | 5, 11       | 1, 6                  |
| 16  | clergy             | 5, 4, 10    | 1, 3                  |
| 17  | wahabi ulema       | 12, 11, 10  | 6, 1, 2               |
| 18  | donju              | 1, 7        | 6                     |
| 19  | saudi royal family | 10, 5       | 6, 2, 12              |
| 20  | quds force         | 11, 1       | 6                     |
| 21  | jihadis            | 12          | 1-10 (all but 11, 12) |
| 22  | wall street        | 6, 4        | 1, 2, 9               |
| 23  | chaebols           | 4, 6, 7     | 1, 3                  |

Coalition partners count at half weight of the average partner affinity
(open question 6, already decided in the epic).

## Law preferences (table C)

Value +1 wants the law high, -1 wants it low; max 3 non-zero cells per
faction. Sources: `military_law` 1-10, `police_law` 1-5, `education_law` 1-5,
`social_law` 1-6 (`00_law_attitudes.txt:5-205`); `corporate_tax_rate` and
`population_tax_rate` 0-50, default 20 (`00_money_system.txt:6244`). Law term
(step 2): `pref * (law - centre) * scale`, centre 5 / scale 1 for military,
centre 3 / scale 2 for police, education, and social; taxes use
`pref * (rate - 25) * 0.2`; the sum clamps to -10..+10.

| id              | mil | pol | edu | soc | corp tax | pop tax |
| --------------- | --- | --- | --- | --- | -------- | ------- |
| 1 SMBO          |     |     | +1  |     | -1       | -1      |
| 2 bankers       |     |     | +1  | -1  | -1       |         |
| 3 fossil        |     |     |     | -1  | -1       |         |
| 4 conglomerates |     |     | +1  | -1  | -1       |         |
| 5 oligarchs     |     | -1  |     | -1  | -1       |         |
| 6 maritime      | +1  |     |     |     | -1       |         |
| 7 military      | +1  | +1  |     | -1  |          |         |
| 8 defense       | +1  |     |     |     | -1       |         |
| 9 intelligence  | +1  | +1  |     |     |          |         |
| 10 unions       |     |     |     | +1  | +1       | -1      |
| 11 landowners   |     | +1  |     | -1  | -1       |         |
| 12 farmers      | -1  |     |     | +1  |          | -1      |
| 13 cadres       | +1  | +1  |     | +1  |          |         |
| 14 priesthood   |     |     | -1  | +1  |          |         |
| 15 ulema        |     | +1  | -1  | +1  |          |         |
| 16 clergy       |     |     | -1  | +1  |          |         |
| 17 wahabi       | +1  | +1  | -1  |     |          |         |
| 18 donju        |     | -1  | +1  |     | -1       |         |
| 19 saudi royal  | +1  | +1  |     |     |          | -1      |
| 20 quds         | +1  | +1  | -1  |     |          |         |
| 21 jihadis      | +1  | -1  | -1  |     |          |         |
| 22 wall street  |     |     | +1  | -1  | -1       |         |
| 23 chaebols     |     |     | +1  | -1  | -1       |         |

## Sector drivers

Step 2 influence formula: `inf_target = base + sector (0-30) + 10 per active
privilege (cap 20) - 20 if cracked down + 10 if a backed group rules`,
clamped to 5..100. Sector is `clamp(driver * K, 0, 30)`; K values are
provisional and get tuned in step 9. Shares are the existing GDP-share vars
set in `00_money_system.txt:6040+` (`civil_fac_percent`, `office_fac_percent`,
`naval_factory_total_percent`, `military_factory_total_percent`,
`agriculture_district_fac_percent`, `agriculture_percent`), `debt_ratio`
(`:2584`), and `oil_exports / gdp_total`. K constants: `@internal_faction_k_building_share`
100, `@internal_faction_k_heavy_share` 300, `@internal_faction_k_debt` 10, `@internal_faction_k_unions` 15,
`@internal_faction_k_party_pop` 30, `@internal_faction_k_religious_pop` 20.

- 1, 4, 18, 23: `civil_fac_percent` x `@internal_faction_k_building_share`
- 2, 22: `office_fac_percent` x `@internal_faction_k_building_share` + `debt_ratio` x
  `@internal_faction_k_debt`
- 3: `oil_exports` / `gdp_total` x `@internal_faction_k_heavy_share`
- 5: oligarchs, `civil_fac_percent` x `@internal_faction_k_building_share` x 0.6, +10 under
  `corruption_level_04` and above
- 6: `naval_factory_total_percent` x `@internal_faction_k_heavy_share`
- 7: `military_law` x 2, plus 10 if `has_war = yes`
- 8: `military_factory_total_percent` x `@internal_faction_k_heavy_share`
- 9: `police_law` x 5
- 10: (`civil_fac_percent` + `military_factory_total_percent`) x
  `social_law` x `@internal_faction_k_unions`
- 11, 12: (`agriculture_district_fac_percent` + `agriculture_percent`) x
  `@internal_faction_k_building_share`
- 13: communist, (`party_pop_array^4` + `party_pop_array^19`) x
  `@internal_faction_k_party_pop` (party indices 4 and 19 are the communist parties)
- 14-17: religious, 10 + (5 - `education_law`) x 3 + (`party_pop_array^8` +
  `^9` + `^11` + `^12`) x `@internal_faction_k_religious_pop` (party indices 8, 9, 11, 12
  are the religious parties)
- 19: fixed 20
- 20: `military_law` x 2
- 21: 10 if `has_war = yes`, else 0

## Policies (table D)

Policy id `p = (id - 1) * 4 + k`: k 1-3 is a privilege, k 4 is the crackdown.
`global.internal_faction_policy_faction^p` and `global.internal_faction_policy_kind^p` (1 privilege,
2 crackdown) hold the reverse map. Loc keys are `internal_faction_policy_<slug>` and
`_desc` (step 5). Effects are vars written into the faction's dynamic
modifier block (step 4); the values below are the full effect at 100%
strength. Costs follow epic 1.6. `(md)` marks a key defined in
`common/modifier_definitions/`; everything else is vanilla.

**1 SMBO**

- `smbo_startup_grants` P: production_speed_industrial_complex_factor +0.05,
  civilian_industry_tax_modifier (md) -0.05
- `smbo_deregulation` P: civilian_factories_productivity (md) +0.05,
  corporate_tax_income_multiplier_modifier (md) -0.03
- `smbo_procurement_quota` P: production_speed_internet_station_factor +0.10,
  consumer_goods_factor +0.02
- `smbo_licensing_crackdown` C: civilian_industry_tax_modifier (md) +0.08,
  civilian_factories_productivity (md) -0.05

**2 international bankers**

- `bankers_deregulation` P: interest_rate_multiplier_modifier (md) -0.5,
  econ_cycle_upg_cost_multiplier_modifier (md) -0.05
- `bankers_bailout_guarantee` P: econ_cycle_upg_cost_multiplier_modifier
  (md) -0.10, corporate_tax_income_multiplier_modifier (md) -0.03
- `bankers_capital_freedom` P: investment_cost_modifier (md) -0.10,
  receiving_investment_cost_modifier (md) -0.05
- `bankers_capital_controls` C: tax_gain_multiplier_modifier (md) +0.04,
  trade_opinion_factor -0.10

**3 fossil fuel industry**

- `fossil_drilling_permits` P: oil_export_multiplier_modifier (md) +0.10,
  local_resources_oil_factor +0.05
- `fossil_fuel_subsidy` P: base_fuel_gain_factor +0.10,
  fossil_pp_fuel_consumption_modifier (md) -0.05
- `fossil_export_terminals` P: resource_export_multiplier_modifier (md) +0.05,
  production_speed_fuel_silo_factor +0.10
- `fossil_windfall_tax` C: corporate_tax_income_multiplier_modifier (md)
  +0.05, oil_export_multiplier_modifier (md) -0.10

**4 industrial conglomerates**

- `conglomerates_industrial_policy` P: industrial_capacity_factory +0.03,
  civilian_industry_tax_modifier (md) -0.05
- `conglomerates_export_credits` P: resource_export_multiplier_modifier
  (md) +0.05, international_market_income_modifier (md) +0.05
- `conglomerates_infrastructure_contracts` P:
  production_speed_infrastructure_factor +0.10,
  infrastructure_cost_multiplier_modifier (md) +0.05
- `conglomerates_antitrust` C: civilian_industry_tax_modifier (md) +0.08,
  industrial_capacity_factory -0.05

**5 oligarchs**

- `oligarchs_privatisation_deals` P:
  production_speed_industrial_complex_factor +0.05, corruption_cost_factor +0.10
- `oligarchs_resource_concessions` P: local_resources_factor +0.05,
  resource_export_multiplier_modifier (md) +0.05
- `oligarchs_media_holdings` P: political_power_factor +0.05,
  drift_defence_factor +0.10
- `oligarchs_asset_seizure` C: tax_gain_multiplier_modifier (md) +0.04,
  trade_opinion_factor -0.05

**6 maritime industry**

- `maritime_shipbuilding_subsidy` P: production_speed_dockyard_factor +0.10,
  dockyard_income_tax_modifier (md) -0.05
- `maritime_cabotage_law` P: industrial_capacity_dockyard +0.05,
  trade_opinion_factor -0.05
- `maritime_port_authority` P: production_speed_naval_base_factor +0.10,
  navy_max_range_factor +0.05
- `maritime_tonnage_levy` C: dockyard_income_tax_modifier (md) +0.08,
  industrial_capacity_dockyard -0.05

**7 the military**

- `military_officer_pay_rise` P: army_morale_factor +0.05,
  personnel_cost_multiplier_modifier (md) +0.05
- `military_procurement_priority` P: military_factories_productivity
  (md) +0.05, civilian_factories_productivity (md) -0.02
- `military_promotion_autonomy` P: experience_gain_army_factor +0.05,
  political_power_factor -0.03
- `military_political_commissars` C: army_org_factor -0.05,
  drift_defence_factor +0.10; mutator: `internal_faction_coup_plot` frozen (step 7)

**8 defense industry**

- `defense_domestic_procurement` P: production_speed_arms_factory_factor
  +0.10, international_market_purchase_modifier (md) +0.05
- `defense_export_licenses` P: international_market_income_modifier (md)
  +0.10, trade_opinion_factor -0.03
- `defense_rnd_grants` P: production_factory_efficiency_gain_factor +0.05,
  military_industry_tax_modifier (md) -0.05
- `defense_contractor_audit` C: military_industry_tax_modifier (md) +0.08,
  military_factories_productivity (md) -0.05

**9 intelligence community**

- `intel_surveillance_powers` P: foreign_subversive_activites -0.10,
  stability_factor -0.02
- `intel_black_budget` P: decryption_factor +0.10,
  police_cost_multiplier_modifier (md) +0.05
- `intel_covert_action_authority` P: foreign_influence_modifier (md) +0.05,
  encryption_factor +0.05
- `intel_service_purge` C: political_power_factor +0.05,
  foreign_subversive_activites +0.10

**10 labour unions**

- `unions_collective_bargaining` P: social_cost_multiplier_modifier (md)
  -0.05, consumer_goods_factor +0.02
- `unions_strike_protection` P: production_factory_efficiency_gain_factor
  +0.05, stability_factor -0.02
- `unions_board_seats` P: political_power_factor +0.05,
  civilian_factories_productivity (md) -0.02
- `unions_strike_ban` C: industrial_capacity_factory +0.05, stability_factor
  -0.03; mutator: `protest_strength` +1/month (step 6)

**11 landowners**

- `landowners_estate_tax_relief` P: agriculture_district_income_tax_modifier
  (md) -0.05, stability_factor +0.02
- `landowners_tenancy_law` P: agricolture_productivity_modifier (md) +0.05,
  conscription_factor -0.02
- `landowners_land_registry` P: local_resources_factor +0.03,
  agriculture_district_worker_requirement_modifier (md) -0.05
- `landowners_land_reform` C: agriculture_district_income_tax_modifier
  (md) +0.08, stability_factor -0.02

**12 farmers**

- `farmers_price_supports` P: agricolture_productivity_modifier (md) +0.05,
  consumer_goods_factor +0.02
- `farmers_rural_credit` P: production_speed_agriculture_district_factor
  +0.10, agriculture_district_income_tax_modifier (md) -0.03
- `farmers_draft_exemption` P: monthly_population +0.02, conscription_factor
  -0.03
- `farmers_land_tax` C: agriculture_district_income_tax_modifier (md) +0.06,
  agricolture_productivity_modifier (md) -0.05

**13 communist cadres**

- `cadres_party_schools` P: political_power_factor +0.05,
  education_cost_multiplier_modifier (md) +0.03
- `cadres_nomenklatura_posts` P: bureaucracy_cost_multiplier_modifier
  (md) -0.05, corruption_cost_factor +0.10
- `cadres_mass_mobilisation` P: mobilization_speed +0.10, consumer_goods_factor +0.02
- `cadres_anti_corruption_purge` C: corruption_cost_factor -0.10,
  political_power_factor -0.05

**14 priesthood / 15 ulema / 16 clergy**

Same 4 policies, slug prefix `priesthood_`, `ulema_`, `clergy_`.

- `<f>_religious_schools` P: education_cost_multiplier_modifier (md) -0.05,
  research_speed_factor -0.03
- `<f>_morality_laws` P: stability_factor +0.03; mutator: party push weight
  x2 (step 6)
- `<f>_tax_exemption` P: political_power_factor +0.05,
  tax_gain_multiplier_modifier (md) -0.02
- `<f>_secularisation` C: research_speed_factor +0.03, stability_factor -0.03

**17 wahabi ulema**

- `wahabi_religious_schools` P: education_cost_multiplier_modifier (md)
  -0.05, research_speed_factor -0.03
- `wahabi_religious_police` P: stability_factor +0.03,
  police_cost_multiplier_modifier (md) +0.05
- `wahabi_charity_exemption` P: political_power_factor +0.05,
  tax_gain_multiplier_modifier (md) -0.02
- `wahabi_secularisation` C: research_speed_factor +0.03, stability_factor
  -0.03

**18 the donju**

- `donju_market_tolerance` P: production_speed_industrial_complex_factor
  +0.05, corruption_cost_factor +0.10
- `donju_trade_permits` P: resource_export_multiplier_modifier (md) +0.05,
  international_market_income_modifier (md) +0.05
- `donju_foreign_currency_shops` P: tax_gain_multiplier_modifier (md) +0.03,
  consumer_goods_factor -0.02
- `donju_market_closures` C: political_power_factor +0.05,
  consumer_goods_factor +0.03

**19 saudi royal family**

- `sarf_royal_stipends` P: stability_factor +0.03, social_cost_multiplier_modifier (md) +0.05
- `sarf_court_appointments` P: political_power_factor +0.05,
  bureaucracy_cost_multiplier_modifier (md) +0.05
- `sarf_family_council` P: drift_defence_factor +0.10, corruption_cost_factor +0.10
- `sarf_anti_corruption_detentions` C: tax_gain_multiplier_modifier (md)
  +0.04, stability_factor -0.03

**20 quds force**

- `quds_proxy_funding` P: send_volunteer_size +1, tax_gain_multiplier_modifier (md) -0.02
- `quds_training_camps` P: special_forces_cap +0.05, political_power_factor
  -0.02
- `quds_smuggling_networks` P: international_market_purchase_modifier
  (md) -0.05, trade_opinion_factor -0.05
- `quds_operations_freeze` C: trade_opinion_factor +0.10,
  foreign_influence_modifier (md) -0.05

**21 foreign jihadis**

- `jihadis_recruitment_drive` P: weekly_manpower +250, stability_factor
  -0.02
- `jihadis_frontline_autonomy` P: army_attack_factor +0.03, army_org_factor
  -0.02
- `jihadis_martyr_glorification` P: war_support_factor +0.05,
  trade_opinion_factor -0.05
- `jihadis_foreign_fighter_purge` C: stability_factor +0.03, war_support_factor -0.05

**22 wall street**

- `wall_street_deregulation` P: interest_rate_multiplier_modifier (md) -0.5,
  econ_cycle_upg_cost_multiplier_modifier (md) -0.05
- `wall_street_bailout_guarantee` P: econ_cycle_upg_cost_multiplier_modifier
  (md) -0.10, corporate_tax_income_multiplier_modifier (md) -0.03
- `wall_street_dollar_diplomacy` P: return_on_investment_modifier (md) +0.01,
  foreign_influence_modifier (md) +0.05
- `wall_street_financial_regulation` C: tax_gain_multiplier_modifier (md)
  +0.04, trade_opinion_factor -0.05

**23 chaebols**

- `chaebols_industrial_policy` P: industrial_capacity_factory +0.03,
  civilian_industry_tax_modifier (md) -0.05
- `chaebols_export_credits` P: resource_export_multiplier_modifier (md)
  +0.05, international_market_income_modifier (md) +0.05
- `chaebols_cross_shareholding` P: investment_cost_modifier (md) -0.10,
  corruption_cost_factor +0.10
- `chaebols_governance_reform` C: civilian_industry_tax_modifier (md) +0.08,
  industrial_capacity_factory -0.05

## Government bonuses (table E)

Active when a backed group rules. Strength ramps linearly with opinion:
`clamp((opinion - 50) / 30, 0, 1)`, so 0 at 50, 0.33 at 60 and 1.0 at 80+.
Values below are the
full-strength effect, written into the faction's dynamic modifier block
(step 4). This replaces the static `modifier` blocks on the old ideas,
removed at step 11.

- 1 SMBO: civilian_factories_productivity +0.10,
  production_speed_internet_station_factor +0.10
- 2 bankers: interest_rate_multiplier_modifier -1.0,
  investment_duration_modifier -0.10
- 3 fossil fuel: base_fuel_gain_factor +0.15,
  oil_export_multiplier_modifier +0.10
- 4 conglomerates: production_speed_industrial_complex_factor +0.10,
  resource_export_multiplier_modifier +0.10
- 5 oligarchs: political_power_factor +0.10, corruption_cost_factor -0.15
- 6 maritime: industrial_capacity_dockyard +0.10, dockyard_productivity +0.05
- 7 military: conscription_factor +0.05, training_time_army_factor -0.10
- 8 defense industry: license_purchase_cost -0.20,
  production_factory_efficiency_gain_factor +0.10
- 9 intelligence: decryption_factor +0.15,
  foreign_subversive_activites -0.15
- 10 unions: health_cost_multiplier_modifier -0.10,
  production_factory_start_efficiency_factor +0.10
- 11 landowners: agriculture_district_income_tax_modifier +0.10,
  agricolture_productivity_modifier +0.05
- 12 farmers: monthly_population +0.03, consumer_goods_factor -0.03
- 13 cadres: mobilization_speed +0.15, army_org_regain +0.10
- 14-17 religious: stability_factor +0.05, drift_defence_factor +0.15
- 18 donju: production_speed_industrial_complex_factor +0.10,
  consumer_goods_factor -0.03
- 19 saudi royal family: political_power_factor +0.10, stability_factor +0.05
- 20 quds force: send_volunteer_size +2, foreign_influence_modifier +0.10
- 21 jihadis: weekly_manpower +250, special_forces_cap +0.05
- 22 wall street: interest_rate_multiplier_modifier -1.0,
  economic_cycles_cost_factor -0.25
- 23 chaebols: receiving_investment_duration_modifier -0.25,
  industrial_capacity_factory +0.05

## Per-country state and tiers

| array / var                                                    | range        | meaning                                                            |
| -------------------------------------------------------------- | ------------ | ------------------------------------------------------------------ |
| `internal_faction_active`                                      | 3 ids        | the active factions, always `global.internal_faction_active_count` |
| `internal_faction_pool`                                        | ids          | available factions, rebuilt by `internal_faction_build_pool`       |
| `internal_faction_inactive`                                    | ids          | player-only display array: pool minus active                       |
| `internal_faction_opinion^id`                                  | 0-100        | replaces `<f>_opinion`, 50 neutral                                 |
| `internal_faction_influence^id`                                | 0-100        | clout                                                              |
| `internal_faction_target^id`, `internal_faction_inf_target^id` | 0-100        | last computed targets                                              |
| `internal_faction_policies`                                    | policy ids   | active privileges and crackdowns                                   |
| `internal_faction_policy_cooldown^id`                          | months, 0-12 | since the last policy change on that faction                       |
| `internal_faction_coup_plot`                                   | 0-100        | coup accumulator (step 7)                                          |

Every faction in the pool tracks influence; only active factions track opinion
(initialised to 50 for every id and kept when a faction drops out). The active
set is refreshed by `internal_faction_refresh_active` each monthly tick and after
a Support action: factions no longer in the pool leave, the highest-influence
available factions fill up to `global.internal_faction_active_count` (3), then
one challenger with influence at or above `global.internal_faction_active_threshold`
(25) that leads the weakest active faction by `@internal_faction_displace_margin`
(5) takes its slot.

Test presence with `is_in_array = { internal_faction_active = 7 }`.

Opinion tiers: hostile below 20, negative 20-39, indifferent 40-59, positive
60-79, enthusiastic 80 and up.

Influence tiers: marginal below 25, influential 25-59, powerful 60 and up.
The tiers are labels and gates; the influence-driven effects scale smoothly
through `internal_faction_influence_scale`: `0.5 + influence * 0.01`, so 0.5
at 0, 1.0 at 50 and 1.5 at 100. The threshold for displacing an active
faction is the marginal/influential boundary.

The old tier triggers overlap at 60 and 40 (`00_internal_factions_trigger.txt`);
the new `internal_faction_tier_*` triggers use the clean bands above.

## Opinion target formula

Epic 1.3, monthly, computed in step 2. Opinion 50 is neutral.

```
target = 50
       + party term        +15 backed group rules / -10 opposed group rules
                           (coalition partners: half weight of the average)
       + privileges        +10 each active for this faction, cap +20
       + crackdown         -15 while cracked down
       + rival privileges  -5 per privilege held by a faction that opposes
                           a group this one backs, cap -10
       + law term          table C, clamp -10..+10
clamp 5..95
opinion += (target - opinion) * global.internal_faction_drift_rate
```

`global.internal_faction_drift_rate` is set from `rule_internal_faction_tick_amount`,
ordinal: point_00 0, point_10 0.05, point_25 0.10, point_50 0.15, point_75
0.20. The rule's default option is point_50, so the drift rate defaults to
0.15 until the rule loc is relabelled in step 11. Focus, event, and decision
changes stay immediate shocks on top of the drift.

Privilege, crackdown and rival-privilege terms are added to
`internal_faction_compute_opinion_target` / `internal_faction_compute_influence_target` in step 5
(#4267) from the `internal_faction_priv_count` / `internal_faction_crackdown` temp arrays that
`internal_faction_monthly_tick` builds from `internal_faction_policies` each tick; influence drifts at
`@internal_faction_influence_drift_rate` = 0.10 regardless of the rule. The rival term reads
`global.internal_faction_rival`, a matrix computed once in `setup_global_arrays`:
`global.internal_faction_rival^(v * 24 + j)` is 1 when faction `j` holds a privilege that
opposes a policy group faction `v` backs (any group, not just the ruling one).

## Old-system quirks to remove at step 11

Found during exploration; step 11 removes the old system, so none of these
need a fix before then.

- `wahabi_ulema_dynamic_modifier` reads
  `CLER_education_cost_multiplier_modifier_var`
  (`05_internal_factions_modifiers.txt:180`), a cross-read from the clergy.
- `OLI_military_industrial_organization_funds_gain_var` and
  `DEF_*_assign_cost_var` are computed but never wired to anything.
- The `non_indifferent_<f>` triggers are always false.
- `change_all_internal_faction_opinion` and
  `set_to_max_internal_faction_opinions` both skip `iranian_quds_force`.
- `industrial_conglomerates` has no `available` block.
- `chaebols`, `wall_street`, and `the_donju` lack
  `_at_least_enthusiastic_opinion` triggers and entrench decisions.

## Data layer API (step 1)

Files: `common/scripted_effects/01_internal_factions_v3_effects.txt`,
`common/scripted_triggers/01_internal_factions_v3_triggers.txt`.

`internal_faction_init_arrays` creates the per-country arrays sized 24 (index 0 unused,
ids 1-23 match the faction id order used throughout this doc): `internal_faction_active`
(the 3 active ids), `internal_faction_opinion` (0-100 per id, 50 at creation), `internal_faction_influence`
(0-100 per id), `internal_faction_target` (0-100 per id, last computed opinion target),
`internal_faction_inf_target` (0-100 per id, last computed influence target).

Effects:

- `internal_faction_change_opinion` (internal_faction_id, temp_opinion): adds temp_opinion to
  `internal_faction_opinion^internal_faction_id` and clamps, only when internal_faction_id is active.
- `internal_faction_change_influence` (internal_faction_id, temp_influence): same for `internal_faction_influence^internal_faction_id`,
  for any faction, active or not; the modifier refresh only runs for an active one.
- `internal_faction_add_faction` (internal_faction_id): activates internal_faction_id, dropping
  the lowest-influence active id when the slots are full. Opinion and influence are not reset.
- `internal_faction_remove_faction` (internal_faction_id): drops internal_faction_id from `internal_faction_active`.
- `internal_faction_build_pool`: rebuilds `internal_faction_pool` from `internal_faction_is_available`.
- `internal_faction_find_weakest` / `internal_faction_find_challenger`: set the temp vars
  `internal_faction_low` (weakest active) and `internal_faction_high` (strongest available inactive, 0 when none).
- `internal_faction_refresh_active`: the activation pass described above; ends with
  `internal_faction_rebuild_inactive` for the player.
- `internal_faction_seed_factions` (no params): run directly after `setup_init_factions`.
  Sets every faction's influence to `global.internal_faction_base_influence` (plus a -10..10
  jitter under `rule_randomize_internal_factions`), then every held idea's faction keeps its
  old `<f>_opinion`, gains `@internal_faction_held_idea_influence` (20) and activates first,
  then `internal_faction_refresh_active` fills the remaining slots.
- `internal_faction_copy_factions` (nation_to_copy_from): copies all 23 `internal_faction_opinion` and
  `internal_faction_influence` entries and `internal_faction_active` from that country; mirrors opinion
  around 50 for factions aligned with the new ruling party's group, then runs the activation
  pass so factions unavailable to the new tag drop out.
- `update_internal_faction_dirty_variable`: bumps `global.internal_faction_ui_dirty` for the player only.

Triggers: `internal_faction_has_<token>` per faction (23, plus `internal_faction_has_religious_faction`
for ids 14-17); `internal_faction_tier_hostile/negative/indifferent/positive/enthusiastic`
and `internal_faction_influence_marginal/influential/powerful` on `internal_faction_opinion^internal_faction_id` /
`internal_faction_influence^internal_faction_id`; `internal_faction_is_available` (on `internal_faction_id`) reproduces the old idea
`allowed`/`available` gating, minus `internal_faction_swap_allowed`.

Base influence per faction is the seed order: a country without held ideas
starts with the three highest `global.internal_faction_base_influence` entries
among its available factions (ties keep id order).

Bridge: each old `change_<f>_opinion` effect now also calls
`internal_faction_change_opinion` with the raw `temp_opinion`, before `autocrats_opinion_change`
and outside the `has_idea` guard, so the new arrays move even for
rule-filled factions with no idea. The old `<f>_opinion` variable keeps
updating unchanged; the 2x autocrat multiplier is not applied to the bridge.

## Monthly tick (step 2)

`internal_faction_monthly_tick` runs from `MD_on_actions.txt`'s monthly `every_country`,
right after the old `monthly_tick_internal_factions_opinion`. It skips
countries with an empty `internal_faction_active`. It hoists the ruling policy group, the
six law terms (`internal_faction_mil_term`, `internal_faction_pol_term`, `internal_faction_edu_term`, `internal_faction_soc_term`,
`internal_faction_corp_term`, `internal_faction_pop_term`), the oil share, and the war flag once per
country, rebuilds `internal_faction_pool`, then for every faction in the pool runs
`internal_faction_compute_influence_target` and drifts `internal_faction_influence` toward
`internal_faction_inf_target` at `@internal_faction_influence_drift_rate`; for the active ones it
also runs `internal_faction_compute_opinion_target`, drifts `internal_faction_opinion` toward
`internal_faction_target` at `global.internal_faction_drift_rate` and ticks the policy
cooldown. Both values clamp to 0-100. It then runs `internal_faction_refresh_active`
before the party push and modifier feed, and bumps the player dirty var once at
the end, not per faction.

Temp variable names used across `internal_faction_monthly_tick`, `internal_faction_compute_opinion_target`,
`internal_faction_compute_influence_target`, and `internal_faction_compute_sector_score`: `internal_faction_v` (faction
id), `internal_faction_aff` (affinity index), `internal_faction_group`, `internal_faction_mil_term`, `internal_faction_pol_term`,
`internal_faction_edu_term`, `internal_faction_soc_term`, `internal_faction_corp_term`, `internal_faction_pop_term`, `internal_faction_oil_share`,
`internal_faction_war`, `internal_faction_sector`, `internal_faction_t`, `internal_faction_x`, `internal_faction_d`, `internal_faction_col`, `internal_faction_aff_col`,
`internal_faction_law`, `internal_faction_party`. Step 5 (#4267) adds `internal_faction_priv_count`, `internal_faction_crackdown`
(temp arrays sized 24, built each tick from `internal_faction_policies`), `internal_faction_pf`, `internal_faction_j`,
`internal_faction_r`, `internal_faction_y`, `internal_faction_cp`, `internal_faction_cost`, `internal_faction_pp`, `internal_faction_clear_id`, `internal_faction_appease_id`,
`internal_faction_ai_done`, `internal_faction_k`. Step 6 (#4268) adds `internal_faction_scale`, `internal_faction_push`, `internal_faction_best`,
`internal_faction_best_pop`, `internal_faction_pi`, `internal_faction_a`, `internal_faction_react`, `internal_faction_protest`, `internal_faction_funding`, `law_kind`,
`law_delta`. The activation pass adds `internal_faction_low`, `internal_faction_high`,
`internal_faction_gone` (temp array), `internal_faction_keep_id` and `internal_faction_seed_opinion`.
Later steps must not reuse these names for unrelated values within the
same call chain.

The modifier feed (step 4) adds its own reserved temp names: `internal_faction_s`
(opinion-scaled base), `internal_faction_g` (government bonus strength), `internal_faction_gov_aff`
(affinity index for the ruling party), `internal_faction_k` (a per-key scratch value inside
a single `internal_faction_dynmod_<id>` block), and `internal_faction_dm_id` (the faction id passed to
`internal_faction_attach_dynmod` and `internal_faction_detach_dynmod`).

## Prototype GUI (step 3)

Files: `common/scripted_guis/01_internal_factions_gui.txt`,
`interface/MD_internal_factions.gui`,
`common/scripted_localisation/01_internal_factions_scripted_loc.txt`,
`localisation/english/MD_internal_factions_v3_l_english.yml`. The window
carries `dirty = global.internal_faction_ui_dirty` and is gated by the country flag
`internal_faction_window_open`, toggled by `internal_faction_toggle_window`. Policies are a per-country
`internal_faction_policies` array holding policy id `(faction id - 1) * 4 + k` (k 1-3
privilege, 4 crackdown). The three privilege buttons dispatch to
`internal_faction_toggle_privilege` and the crackdown button to `internal_faction_toggle_crackdown`, each
enabled through the matching `internal_faction_can_grant/revoke/enact/lift_*` trigger. One
more button per active entry calls `internal_faction_appease`. Active rows carry the
vanilla `GFX_ongoing_generic_glow_yellow` glow (`internal_faction_entry_glow`) behind the
faction icon. Below the three active rows a scrollable `internal_faction_inactive_scroll`
lists `internal_faction_inactive` through `internal_faction_inactive_entry` (icon, name,
stance, influence bar and tier) with a Support button that calls
`internal_faction_support_faction`, enabled by `internal_faction_can_support`.
Per-entry display goes through scripted-loc
dispatchers on `v`: `internal_faction_tier_text_v`, `internal_faction_inf_tier_text_v`, `internal_faction_stance_v`,
`internal_faction_affinity_v`, and `internal_faction_policy_k_icon` per slot. The faction name uses
`[?global.internal_faction_token^v.GetTokenLocalizedKey]` directly, and the icon uses
`GFX_idea_[?global.internal_faction_token^v.GetTokenKey]`. Open buttons sit in the top bar
next to the EU button and on the politics tab next to the protests button.

## Modifier feed (step 4)

File: `common/scripted_effects/01_internal_factions_v3_modifier_feeds.txt`.
This is now the only writer of the vars in
`common/dynamic_modifiers/05_internal_factions_modifiers.txt`. The old
`apply_<f>_DYNMOD` effects and their call sites are gone from
`00_internal_faction_effects.txt`.

`internal_faction_apply_faction_modifiers` (param `internal_faction_id`) computes two numbers and then
dispatches to one of 23 `internal_faction_dynmod_<id>` blocks:

- `internal_faction_s`, the opinion-scaled base: `(internal_faction_opinion^id - 50)` times
  `internal_faction_scale` from `internal_faction_influence_scale` (0.5 at 0 influence,
  1.0 at 50, 1.5 at 100).
- `internal_faction_g`, the government bonus strength: 0 unless the ruling party's group
  is backed by the faction (`global.internal_faction_affinity`), then
  `clamp((opinion - @internal_faction_gov_start) / @internal_faction_gov_span, 0, 1)`
  with start 50 and span 30.
  Coalition partners are not weighted in, only the ruling party.

Each `internal_faction_dynmod_<id>` block writes one var per modifier key on the faction's
dynamic modifier: first the opinion-scaled vars (`set_variable = { VAR =
internal_faction_s }` then `multiply_variable` by the same k the old feed used), then the
two government-bonus keys from table E (added into an existing opinion-scaled
var through the `internal_faction_k` temp var, or set directly from `internal_faction_g` when the key has
no opinion-scaled var), then every remaining policy-only var is zeroed, then
the four policies from table D are applied with `is_in_array = { internal_faction_policies
= p }`, `p = (id - 1) * 4 + k` (k 1-3 privileges, 4 the crackdown). A key that
is shared by several sub-resources (the `local_resources_*_factor` keys, or a
policy that says `local_resources_factor`) always resolves to the block's one
shared local-resources var, never a per-resource one.

The intelligence community (id 9) keeps its DLC branch: with La Resistance,
the four `*_intel_factor` vars are opinion-scaled and decryption/encryption
are zeroed; without it, decryption/encryption are opinion-scaled and the four
intel vars are zeroed. The government bonus and policies for id 9 are added
after the branch, so they apply either way. The Quds Force (id 20) has no
`has_idea` guard, since it is only reached through `internal_faction_active`. Three ids (2,
4, 5) had an acceptance var keyed to `global.monthly_internal_faction_tick_rate`
in the old feed; that k is now the constant `@internal_faction_k_acceptance` (0.25).

Refresh points, all guarded by faction presence:
`internal_faction_apply_faction_modifiers` (one faction, on `internal_faction_id`) runs from
`internal_faction_change_opinion`, `internal_faction_change_influence`, `internal_faction_add_faction`, and
`internal_faction_seed_held_faction`; every action in `00_internal_faction_actions.txt`
reaches it through `internal_faction_change_opinion` or `internal_faction_change_influence`, so none of
them call it directly. `internal_faction_apply_modifiers` (loops `internal_faction_active` and calls the
above per faction) runs at the end of `internal_faction_monthly_tick` and `internal_faction_copy_factions`.

`internal_faction_attach_dynmod` and `internal_faction_detach_dynmod` (param `internal_faction_dm_id`, an if/else_if
chain on the faction id) add or remove the one dynamic modifier for that
faction, guarded by `has_dynamic_modifier` so they are safe to call when the
modifier is already in the right state. They are called from `internal_faction_add_faction`
(detach the replaced slot, attach the new one), `internal_faction_remove_faction`
(detach), `internal_faction_copy_factions` (attach for each copied faction), and the
game-rule reseed in `999_game_rules_on_actions.txt` (detach every active
faction before `clear_array = internal_faction_active`).

Known gap, not fixed here: a faction idea added mid-game through the old
`add_ideas` path attaches its dynamic modifier through the idea's own
`on_add`, without joining `internal_faction_active`. Its vars stay at 0 (or stale, if it
replaced a faction that dropped out) until step 11 replaces those
callers.

## Player actions and AI (step 5)

File: `common/scripted_effects/00_internal_faction_actions.txt`. Every action
checks its own `internal_faction_can_*` trigger from `01_internal_factions_v3_triggers.txt`
before doing anything, so the same gate covers both the GUI button and
`internal_faction_ai_monthly`.

Costs and cooldown lengths are registry vars set once in `setup_global_arrays`
(`global.internal_faction_cost_grant_pp`, `global.internal_faction_cost_grant_gdp_share`,
`global.internal_faction_cost_revoke`, `global.internal_faction_cost_crackdown`, `global.internal_faction_cost_lift`,
`global.internal_faction_cost_appease`, `global.internal_faction_cost_support` = 75,
`global.internal_faction_policy_cooldown_months` = 12, `global.internal_faction_active_count` = 3,
`global.internal_faction_active_threshold` = 25), so triggers, effects and tooltips all read
the same source. `999_game_rules_on_actions.txt` multiplies `global.internal_faction_cost_support`
by 0.25 when `rule_internal_faction_cost_reduction = yes`.

`internal_faction_grant_privilege` and `internal_faction_revoke_privilege` take a policy id and add or
remove it from `internal_faction_policies`, set `internal_faction_policy_cooldown^id`, and shift opinion
(`internal_faction_pay_privilege_cost` charges a GDP share from the treasury for economic
factions, category 1, or political power for the rest). `internal_faction_enact_crackdown`
and `internal_faction_lift_crackdown` do the same for the crackdown slot (`k = 4`),
also moving influence and stability. Crackdown enforcement
(`internal_faction_crackdown_enforcer_ready`) needs the Military (id 7) or the Intelligence
Community (id 9) active with opinion 20 or higher; cracking down on the
Military itself needs the Intelligence Community active with opinion 60 or
higher. `internal_faction_appease` shifts the target faction's opinion up and every other
active faction in the same category down. `internal_faction_toggle_privilege` and
`internal_faction_toggle_crackdown` are the GUI dispatch wrappers the buttons call, picking
grant/enact or revoke/lift from current state.

`internal_faction_support_faction` (inactive faction) adds `@internal_faction_support_influence`
(15) influence through `internal_faction_change_influence`, charges
`global.internal_faction_cost_support` political power and runs `internal_faction_build_pool`
plus `internal_faction_refresh_active` at once, so a faction pushed past the weakest active
one takes its slot without waiting for the tick. There is no manual swap: the
activation pass is the only way in or out of `internal_faction_active`.
`internal_faction_remove_faction` calls `internal_faction_clear_faction_state` on the faction
leaving `internal_faction_active`, dropping its policies and cooldown so a later return
starts clean; its opinion and influence are kept.

`internal_faction_ai_monthly` runs at the end of `internal_faction_monthly_tick` for AI countries only. It
prioritizes a coup response when `internal_faction_coup_plot` is above 50 and the Military
is active: crack down on the Military if it can afford to and the enforcer
condition holds, otherwise appease it. Failing that, with enough political
power it looks for one powerful (influence 60+) and hostile (opinion below 20)
active faction and grants it the first affordable privilege.

## Ecosystem hooks (step 6)

File: `common/scripted_effects/01_internal_factions_v3_ecosystem.txt`. Loc for the
tax-reaction tooltips lives in
`common/scripted_localisation/02_internal_factions_ecosystem_scripted_loc.txt` and
`localisation/english/MD_internal_factions_l_english.yml`. Constants: `@internal_faction_push_max`
0.001, `@internal_faction_push_gate` 20, `@internal_faction_law_shock` 2, `@internal_faction_tax_shock` 0.5, `@internal_faction_desire_weight`
0.5.

`internal_faction_influence_scale` (param `internal_faction_id`, sets temp `internal_faction_scale`) is the shared linear
influence multiplier, `@internal_faction_scale_base` 0.5 plus `@internal_faction_scale_per_influence` 0.01 per
influence point, called from the modifier feed, elections and law desires.

`internal_faction_party_push`, run from `internal_faction_monthly_tick` after the per-faction drift loop, gates
each active faction on `NOT internal_faction_influence_marginal` and opinion above 70 or below 30
(written as `50 +/- @internal_faction_push_gate` through the `internal_faction_push` temp var, never as literals),
then calls `internal_faction_party_push_faction` (param `internal_faction_v`). That helper scales
`@internal_faction_push_max * internal_faction_influence^internal_faction_v / 100` (doubled while a religious faction's morality
laws privilege is active: policy 54/58/62 for ids 14/15/16), picks the
affinity-matching party with the largest `party_pop_array` entry (excluding the ruling
party for a hostile faction), and calls `change_relative_party_popularity` on it.

`internal_faction_react_to_law` (params `law_kind` 1-6, `law_delta`) is called from every law and tax
write site: it reads the matching `global.internal_faction_pref_*` array for every active faction,
multiplies by `law_delta` and by `@internal_faction_law_shock` (laws) or `@internal_faction_tax_shock` (taxes), and
applies any non-zero result through `internal_faction_change_opinion` with an `internal_faction_react_tt` tooltip.
Hook sites: the 26 law idea `on_add` blocks (10 military, 5 police, 5 education, 6
social; bureau and health have no faction preference and are untouched), the 8
money-tab tax buttons, the 2 tax-automation writes, the 2 AI tax appliers in
`00_money_system.txt`, and the 2 `modify_*_tax_rate_effect` content effects, 40 call
sites in total. The 16-entry tax-reaction line list (`internal_faction_react_pop_up_0..3` and the
`pop_down`/`corp_up`/`corp_down` variants, in
`02_internal_factions_ecosystem_scripted_loc.txt`) duplicates the `@internal_faction_tax_shock` 0.5
factor as a literal, since scripted loc cannot read file constants; keep both in sync
if step 9 retunes the shock.

`internal_faction_compute_law_desires`, called first in `recalculate_law_desires`, writes
`internal_faction_desire_military/police/education/social` from every active faction backing the
ruling party's policy group, scaled by `internal_faction_influence_scale` and `@internal_faction_desire_weight`,
clamped to -1..1. `calculate_expected_*_spending` in `00_expected_spending_effects.txt`
add the matching var right before their own `round_variable` call. Health and bureau
have no law preference, so they get no desire var. The desire term lags the faction
opinion by one month, since `calculate_expected_spending` runs before
`recalculate_law_desires` each month.

`internal_faction_compute_protest_drift` (deterministic, only sets temp `internal_faction_protest`) sums, over
`internal_faction_active`, `internal_faction_influence^internal_faction_v / 25` for a hostile faction or a flat 1 for a negative
and powerful one, doubled for a mass faction (category 3), plus 1 more if the
`unions_strike_ban` policy (id 40) is active. `apply_protest_effects` adds it into the
live `protest_strength` tick; `MD_protests_calc_deterministic_drift`'s player-only
display block also calls it to fill `drift_factions_last`, folded into
`MD_protests_compute_drift_total` and cleared in `MD_protests_clear_display_vars`. The
protests panel (`interface/MD_protests_system.gui`) shows it as a 5th row,
`MD_drift_factions_row`, added to `MD_protests_drift_right` (now 153 tall, matching the
left column) below a separator added to `MD_drift_passive_row`.

`display_election_campaign_status` and `calculate_election_funding_from_opinion` in
`00_internal_faction_effects.txt` are rewritten to loop `internal_faction_active` instead of 23
`has_idea` checks, closing #1450; the per-faction funding step is scaled by
`internal_faction_influence_scale` and the total is rounded before the tooltip.

## Step map

One line per sub-issue in epic #4260, listing what each step builds.

- #4262 Data layer: id-indexed arrays, generic effects/triggers, a bridge
  from the old effects, and seeding.
- #4263 Monthly tick: opinion target and drift, influence target and drift,
  tiers.
- #4264 Prototype GUI.
- #4265 Consequences: influence-scaled modifiers, government bonus, policy
  effects.
- #4267 Player actions: policies, support, appease; AI routine.
- #4268 Ecosystem: party push, elections, laws, protests.
- #4269 Military coup chain.
- #4270 Events: presence gating and demands.
- #4272 AI tuning and observer pass.
- #4273 Final UI.
- #4274 Migration and cleanup.
