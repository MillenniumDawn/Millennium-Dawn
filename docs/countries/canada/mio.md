# Millenium Dawn's Canadian Awakening
Canada hasn't seed a good dusting off since it's initial work at the beginning of the mod. Some stuff was added to it, but overall it's fairly empty. Especially when you compare it to other medium powers such as Sweden, France, or Ukraine.

# Starting small
## MIO
While some of Canada's military industry was brought on-board when MIOs were introduced, several are still missing and they expose great production gaps. While in my propositions I highlights some area of specialisations and bonuses, they are not meant to be only that. They must still offer common bonuses to their area of expertise. Here are some I want to see added:

### Implementation rules
1. Bonuses to `corvette`, `stealth_corvette`, `mio_cat_frigates`, and `mio_cat_destroyers` always apply to both the regular and stealth variants.
2. `screen_ships` include `corvette`, `stealth_corvette`, and `mio_cat_frigates`.

## Colt Canada / Diemaco
The sole producer of Canada's standard issue firearms. It should reflect the evolution of Canadian service weapons, from the C7 to the C25, whilst passing by the machineguns. It's current state is good, but it misses content regarding the C25 and its options.

```mermaid
flowchart TD
    T0["Canadian Arsenal Successor<br/>reliability +3%; mio_research +3%; design_team_assign_cost -15%"]
    T1["C7 Service Rifle<br/>soft_attack +5%"]
    T2["Centre of Excellence<br/>mio_funds_gain +5%; design_team_change_cost -15%"]
    T3["C9 Light Machine Gun<br/>defense +5%"]
    T4["Cold Hammer Forging<br/>reliability +6%; production_efficiency_cap +10%"]
    T5["C8 Carbine<br/>breakthrough +4%"]
    T6["Munitions Supply Program<br/>production_efficiency_gain +10%; industrial_manufacturer_assign_cost -20%"]
    T7["C6 GPMG<br/>soft_attack +5%"]
    T8["M203 Grenade Launcher<br/>hard_attack +5%"]
    T9["C7A2 TRIAD Rails<br/>soft_attack +6%"]
    T10["C8SFW Heavy Barrel<br/>breakthrough +5%; mio_funds_gain +4%"]
    T11["Kitchener Plant<br/>build_cost -6%; production_capacity +6%"]
    T12["Heroux-Devtek Era<br/>production_cost -8%; mio_size_up_requirement -10%"]
    T13["Colt Acquisition<br/>mio_task_capacity +1; mio_research +4%"]
    T14["C6A1 FLEX<br/>hard_attack +4%; production_conversion_speed +10%"]
    T15["C9A2 Upgrade<br/>defense +4%; breakthrough +3%"]
    T16["MRR Modular Rifle<br/>defense +5%; mio_research +3%"]
    T17["Lifecycle Sustainment<br/>reliability +5%; production_resource_need -8%"]
    T18["EAGLE Launcher<br/>hard_attack +6%; design_team_assign_cost -10%"]
    T19["CMAR C25 General Services<br/>soft_attack +5%; defense +2%"]
    T20["CMAR C25 Full Spectrum<br/>hard_attack +5%; breakthrough +5%"]

    T0 --> T1
    T0 --> T2
    T0 --> T3

    T1 --> T4
    T1 --> T5
    T2 --> T6
    T2 --> T12
    T2 --> T13
    T3 --> T7
    T3 --> T8
    T3 --> T15

    T4 --> T9
    T5 --> T10
    T5 --> T11
    T6 --> T11
    T7 --> T14
    T8 --> T18

    T9 --> T16
    T10 --> T16
    T11 --> T16
    T12 --> T17
    T13 --> T17
    T14 --> T18
    T15 --> T18
    T16 --> T19
    T19 --> T20

    T9 -.-|mutually exclusive| T10
    T12 -.-|mutually exclusive| T13
    T14 -.-|mutually exclusive| T15
```

### Bombardier
Bombardier - funilly enough has never built a bomber - is a Quebec based company that builds a wide variety of motor vehicles. They range from recreational aircrafts to large jet liners to snowmobiles. It also is a prime candidate to tie into the French Hapiness mechanics that is for now just flavor and is difficult to interact with.
Unfortunately I don't want to create a ground MIO *just* for utility vehicles, therefore I'd skip that part of their portfolio.

**Bombardier Défense**: MIO dedicated to `large_aircraft`, `light_aircraft`, and `uav`. While IRL they are dedicated to large aircrafts, only having them do that seems too restrictive. I'd wrap into it their civilian expertise building light aircrafts to give some variety. Furthermore, IRL Canada is moving more and more towards light jet fighters (F-35 vs Gripen competition) over medium-sized ones. Would encourage players to lean into it.

```mermaid
flowchart TD
    B0["Bombardier Platform Heritage<br/>large_aircraft.reliability +3%; air_range +4%; mio_research +3%"]
    B1["Challenger Missionization<br/>large_aircraft.surface_detection +5%; reliability +4%"]
    B2["Global Endurance Tankage<br/>large_aircraft.air_range +6%; fuel_consumption -5%"]
    B3["ISR Sensor Spine<br/>large_aircraft.surface_detection +6%; sub_detection +5%"]
    B4["Maritime Patrol Package<br/>large_aircraft.sub_detection +6%; surface_detection +5%"]
    B5["Medevac Rapid Reconfig<br/>large_aircraft.reliability +5%; build_cost -4%"]
    B6["Flex Production Cells<br/>production_efficiency_gain +10%; production_capacity +6%"]
    B7["Executive Jet Aerodynamics<br/>light_aircraft.max_speed +5%; air_range +4%"]
    B8["UAV Data Relay Suite<br/>uav.air_range +5%; air_defense +4%"]
    B9["Sovereign Multi-Role Fleet<br/>mio_task_capacity +1; design_team_assign_cost -10%"]
    B10["Alliance Commercializer<br/>large_aircraft.build_cost -4%; production_capacity +6%"]
    B11["Portfolio Rebranding Engine<br/>large_aircraft.reliability +5%; fuel_consumption -2%"]
    B12["Cross-Border Final Assembly<br/>large_aircraft.build_cost -5%"]
    B13["Trade-Law Firebreak<br/>mio_research +3%; design_team_change_cost -10%"]
    B14["Program Governance Transition<br/>mio_task_capacity +1; mio_research +3%"]
    B15["Precision Strike Package<br/>light_aircraft.air_attack +6%; air_superiority +5%"]
    B16["Maritime Killchain Suite<br/>large_aircraft.naval_strike_attack +8%; naval_strike_targeting +6%"]
    B17["Stand-Off Strike Integration<br/>large_aircraft.air_bombing +7%; air_ground_attack +6%"]
    B18["Armed ISR Conversion<br/>uav.air_attack +6%; air_ground_attack +5%"]
    B19["Joint Weapons Certification<br/>light_aircraft.air_attack +5%; large_aircraft.air_bombing +5%"]
    B20["Expeditionary Strike Doctrine<br/>large_aircraft.naval_strike_attack +7%; air_superiority +4%"]

    B0 --> B1
    B0 --> B2
    B0 --> B7
    B0 --> B8
    B1 --> B3
    B2 --> B4
    B1 --> B5
    B2 --> B5
    B3 --> B6
    B4 --> B6
    B7 --> B9
    B7 --> B15
    B8 --> B9
    B8 --> B18
    B5 --> B9
    B5 --> B17
    B6 --> B10
    B6 --> B16
    B10 --> B11
    B11 --> B12
    B11 --> B19
    B12 --> B13
    B15 --> B19
    B18 --> B19
    B16 --> B20
    B17 --> B20
    B9 --> B14
    B13 --> B14
```

### Bell Textron
MIO specialized in `helicopter`. It's a large civilian manufacturer of helicopters, and is in charge of building and sustainement of the existing Griffon helicopter. Since it doesn't have a history of building dedicated gunships - and neither does the CAF operate them - I'd do as with Bombardier: make a case for light gunships.

```mermaid
flowchart TD
    H0["Civil Helicopter Legacy<br/>helicopter.reliability +4%; naval_range +5%"]
    H1["Griffon Fleet Sustainment<br/>helicopter.reliability +5%; max_organization +4%"]
    H2["Hot-and-High Lift Package<br/>helicopter.naval_speed +6%; fuel_consumption -4%"]
    H3["Mission Pod Hardpoints<br/>helicopter.hg_attack +6%; anti_air_attack +4%"]
    H4["Shipborne Rotor Ops<br/>helicopter.surface_detection +6%; sub_detection +5%"]
    H5["Rescue Hoist Integration<br/>helicopter.surface_visibility -5%; naval_range +5%"]
    H6["Modular Avionics Retrofit<br/>build_cost -5%; reliability +4%"]
    H7["Armed Escort Doctrine<br/>helicopter.hg_attack +5%; armor_value +4%"]
    H8["Northern Rotary Wing School<br/>production_efficiency_gain +10%; mio_research +3%"]

    H0 --> H1
    H0 --> H2
    H0 --> H3
    H1 --> H4
    H2 --> H5
    H3 --> H7
    H4 --> H6
    H5 --> H6
    H6 --> H8
    H7 --> H8
```

### CAE
Another giant based in Quebec. It's main claim to fame is aircraft simulators production. I'd look into if it is possible to use a MIO to give passive boosts to a country. Otherwise, maybe investing into them could be made through decisions? If we go the MIO way, I'd also give them the Comms. & Coordinations line.

```mermaid
flowchart TD
    C0["Synthetic Training Core<br/>c2.reliability +4%; max_speed +4%"]
    C1["Distributed Sim Network<br/>c2.build_cost -5%; reliability +5%"]
    C2["Mission Rehearsal Suite<br/>c2.max_speed +6%; reliability +4%"]
    C3["Avionics Procedure Labs<br/>light_aircraft.reliability +4%; air_range +3%"]
    C4["Joint Fires Digital Twin<br/>c2.max_speed +5%; mio_research +3%"]
    C5["Pilot Conversion Pipeline<br/>light_aircraft.max_speed +4%; reliability +4%"]
    C6["Operator Certification Export<br/>mio_funds_gain +8%; design_team_change_cost -10%"]
    C7["Whole-Fleet Readiness Model<br/>production_efficiency_cap +8%; design_team_assign_cost -10%"]

    C0 --> C1
    C0 --> C2
    C1 --> C4
    C2 --> C5
    C2 --> C3
    C4 --> C6
    C5 --> C7
    C3 --> C7
```

### Irving Shipbuilding
Another Canadian giant. Probably the largest shipyards in Canada. Let's give it some some bonuses towards `mio_cat_destroyers` since that's what they are building.

```mermaid
flowchart TD
    %% Industrial foundation branch
    I0["National Surface Combatant Yard<br/>mio_cat_destroyers.build_cost -4%; reliability +4%"]
    I1["Halifax Refit Discipline<br/>mio_cat_frigates.max_organization +6%; mio_cat_destroyers.max_organization +6%; reliability +5%"]
    I2["Modular Block Assembly<br/>mio_cat_destroyers.production_capacity +8%; build_cost -5%"]
    I5["Cold Weather Deck Systems<br/>mio_cat_destroyers.naval_speed +6%"]
    I3["Aegis Integration Line<br/>all_ships.anti_air_attack +4%; armor_value +4%"]
    I4["ASW Mission Bay Standards<br/>mio_cat_destroyers.sub_attack +7%; sub_detection +6%"]
    I6["Atlantic Fleet Sustainment<br/>mio_cat_destroyers.naval_range +9%; reliability +4%"]
    I7["Continuous Build Cadence<br/>production_efficiency_gain +10%; production_efficiency_cap +8%"]
    I8["Shiplift Launch Complex<br/>capital_ship.naval_speed +4%; production_output +5%"]

    %% National program and contracts branch
    I9["National Shipbuilding Strategy Monopoly<br/>screen_ships.build_cost -3%; mio_research +8%"]
    I10["AOPS Arctic Patrol Hull<br/>corvette.naval_range +10%; mio_cat_frigates.naval_range +10%; mio_cat_destroyers.naval_range +10%; armor_value +4%"]
    I11["River-class Destroyer Combat System<br/>mio_cat_destroyers.anti_air +7%; hg_attack +5%"]
    I12["Halifax Frigate Life Extension<br/>mio_cat_frigates.max_organization +6%; sub_detection +5%"]
    I14["Missile Deck expansion<br/>mio_cat_frigates.hg_attack +6%; mio_cat_destroyers.hg_attack +6%; anti_air +5%"]
    I18["Destroyer Combat Systems Integration<br/>mio_cat_destroyers.anti_air +8%; surface_detection +6%"]
    I15["MDA Drones<br/>mio_cat_frigates.surface_detection +5%; sub_detection +8%"]
    I16["Armed Helicopter drones<br/>mio_cat_frigates.sub_attack +6%"]
    I13["Arctic Offshore Surveillance Suite<br/>corvette.sub_detection +12%; mio_cat_frigates.sub_detection +12%; mio_cat_destroyers.sub_detection +12%; cruiser.sub_detection +12%; surface_visibility -4%"]
    I17["Icebreaker hulls<br/>mio_cat_destroyers.armor_value +8%; cruiser.armor_value +8%; max_organization +5%"]

    %% Fleet readiness branch
    I19["Fleet Readiness Maintenance Node<br/>all_ships.max_organization +4%; refit_speed +12%"]
    I20["NSS Contract Allocation<br/>screen_ships.research +10%; production_efficiency_gain +10%"]

    I0 --> I1
    I0 --> I2
    I1 --> I3
    I1 --> I4
    I2 --> I5
    I3 --> I6
    I4 --> I6
    I5 --> I7
    I6 --> I7
    I7 --> I8

    I9 --> I10
    I9 --> I11
    I9 --> I12
    I10 --> I13
    I11 --> I14
    I14 --> I18
    I12 --> I19
    I18 --> I19
    I13 --> I17
    I13 --> I15
    I15 --> I16
    I19 --> I20
```

### Davie Shipbuilding
Shipyards, and another way to interact with the French hapiness by boosting investment into Quebec. Flavor-wise, I'd like to give them some bonuses towards negating weather impact on naval operations (`surface_detection`, `naval_hit_chance`, `naval_speed`, `naval_strike`, `positioning`). This is due to their extensive work in the matter of building icebreakers and arctic capable warships.

```mermaid
flowchart TD
    %% Arctic escort capability branch
    D0["Arctic Shipyard Heritage<br/>mio_cat_frigates.reliability +4%; naval_range +6%"]
    D1["Ice-Class Hull Geometry<br/>mio_cat_frigates.naval_speed +6%; surface_visibility -8%"]
    D2["Winterized Sensor Masts<br/>corvette.surface_detection +8%; mio_cat_frigates.surface_detection +8%"]
    D3["Heavy Sea Stabilization<br/>corvette.lg_attack +7%; mio_cat_frigates.lg_attack +7%; anti_air_attack +6%"]
    D4["Cold-Start Power Trains<br/>corvette.fuel_consumption -5%; mio_cat_frigates.fuel_consumption -5%; reliability +4%"]
    D6["Arctic Patrol Doctrine<br/>mio_cat_frigates.naval_range +10%; max_organization +6%"]
    D7["Northern Escort Mastery<br/>mio_cat_frigates.sub_attack +8%; anti_air_attack +6%"]

    %% Program/contracts branch
    D8["Asterix Replenishment Conversion<br/>support_ship.naval_range +8%; build_cost -5%"]
    D9["Combat Vessel Contracts<br/>screen_ships.research_speed +6%; mio_task_capacity +1"]
    D10["Frigate ASW Modernisation<br/>mio_cat_frigates.sub_attack +8%; torpedo_attack +3%"]
    D11["Protecteur Class Contracts<br/>repair_ship.naval_range +8%; build_cost -5%"]
    D14["Halifax Frigate Maintenance Contract<br/>mio_cat_frigates.max_organization +2%; reliability +5%"]
    D15["Polar Icebreaker Hull Engineering<br/>support_ship.armor_value +6%; repair_ship.armor_value +6%"]
    D18["Polar Max Steel Cutting<br/>support_ship.build_cost -5%; repair_ship.build_cost -5%; corvette.build_cost -5%; mio_cat_frigates.build_cost -5%; production_efficiency_gain +6%"]

    %% Industrial yard modernization branch
    D5["Quebec Refit Throughput<br/>production_capacity +8%; production_efficiency_gain +10%"]
    D12["Lévis Modular Berths<br/>screen_ships.production_efficiency +7%; mio_task_capacity +1"]
    D13["Champlain Dry Dock Repair<br/>screen_ships.reliability +4%; build_cost -2%"]
    D16["NSS Inclusion Framework<br/>mio_funds_gain +8%; research_bonus +5%"]
    D17["Quebec Capacity Expansion<br/>production_efficiency_cap +2%"]

    D0 --> D1
    D0 --> D2
    D1 --> D3
    D2 --> D4
    D2 --> D6
    D3 --> D7
    D4 --> D7
    D6 --> D14

    D8 --> D9
    D8 --> D11
    D11 --> D15
    D15 --> D18
    D9 --> D10
    D10 --> D14

    D5 --> D12
    D12 --> D13
    D13 --> D16
    D14 --> D16
    D16 --> D17
```

### L3Harris
Civilian-Military hybrid specialized in the production of secure communications systems and powerplant technologies. They are also an excellent potential MIO for light drones.
To avoid cramping too many companies in the comms. space, I'd give them flavor perks with collaboration work with Ultra Intelligence & Communications. It's a company specialized in comms. equipment and related remote technologies based in Canada.

```mermaid
flowchart TD
    L0["Secure Comms Backbone<br/>c2.reliability +4%; max_speed +4%"]
    L1["Hardened Data Links<br/>c2.reliability +6%; build_cost -4%"]
    L2["Distributed Sensor Fusion<br/>uav.air_attack +5%; air_range +4%"]
    L3["SATCOM Relay Nodes<br/>uav.air_range +6%; reliability +4%"]
    L4["EW Payload Interfaces<br/>uav.air_defense +5%; air_agility +4%"]
    L5["Battle Network Acceleration<br/>c2.max_speed +6%; design_team_assign_cost -10%"]
    L6["Joint ISR Export Suite<br/>mio_funds_gain +8%; mio_research +3%"]
    L7["Ultra-L3 Collaboration Stack<br/>production_efficiency_gain +10%; industrial_manufacturer_assign_cost -20%"]

    L0 --> L1
    L0 --> L2
    L0 --> L5
    L2 --> L3
    L2 --> L4
    L1 --> L5
    L3 --> L6
    L4 --> L6
    L5 --> L7
```

### Logistik Unicorps
They are THE light kit and clothing manufacturer for soldier and infantry in Canada. Unfortunately, they don't produce really anything visible in the gear that is produced in HOI4 nor MD. Therefore, I would have interactions with them done via decisions. They produce uniforms, socks, t-shirts, gloves, sleeping bags, raingear, boots, etc... I still have dozens of clothing pieces made from them and I am not about to run out even six years after leaving the Forces.

### MDA
One of, if not the largest space-oriented company in Canada. They build satelites and spy stuff. They also make remote piloted aircraft systems and radars. Hitherto, bonuses for `uav` and `guided_missile` will follow the same implementation pattern as the rest of the MIO tree: use the actual equipment and modifier keys from the game data instead of prose labels.

```mermaid
flowchart TD
    M0["Space Systems Integrator<br/>uav.air_range +4%; reliability +4%"]
    M1["Radar Constellation Uplink<br/>uav.air_attack +5%; air_agility +4%"]
    M2["Remote Sensing Pipeline<br/>uav.air_range +6%; reliability +5%"]
    M3["Cruise Guidance Suite<br/>guided_missile.reliability +6%; build_cost -4%"]
    M4["SAM Tracking Logic<br/>sam.reliability +6%; build_cost -3%"]
    M5["ISR-Ordnance Fusion<br/>uav.air_attack +5%; guided_missile.reliability +5%"]
    M6["Launch Vehicle Discipline<br/>production_efficiency_cap +8%; mio_research +4%"]
    M7["Orbital-to-Tactical Killchain<br/>uav.air_range +5%; sam.reliability +5%"]

    M0 --> M1
    M0 --> M2
    M0 --> M3
    M0 --> M4
    M1 --> M5
    M2 --> M5
    M3 --> M6
    M4 --> M6
    M5 --> M7
    M6 --> M7
```

### Roshel
The newcomer star of utility vehicles and light armored vehicles. MIO for that will give bonuses to `utility` and `heavy_utility` equipment categories and APCs.

```mermaid
flowchart TD
    R0["Rapid Armored Utility Core<br/>utility.build_cost -4%; reliability +4%"]
    R1["Modular APC Hulls<br/>utility.armor_value +6%; hardness +5%"]
    R2["Mine-Resistant Geometry<br/>utility.defense +7%; reliability +4%"]
    R3["Urban Mobility Package<br/>utility.max_speed +7%; breakthrough +6%"]
    R4["Remote Weapon Station Fit<br/>utility.soft_attack +6%; hard_attack +5%"]
    R5["Fleet Sustainment Crates<br/>utility.supply_consumption -6%; build_cost -4%"]
    R6["Export Production Surge<br/>production_capacity +8%; production_efficiency_gain +10%"]
    R7["Heavy Utility Conversion<br/>heavy_utility.armor_value +6%; defense +7%"]
    R8["Modern APC Standard<br/>heavy_utility.breakthrough +7%; soft_attack +6%"]

    R0 --> R1
    R0 --> R2
    R0 --> R3
    R1 --> R4
    R2 --> R5
    R3 --> R6
    R4 --> R7
    R5 --> R7
    R6 --> R8
    R7 --> R8
```

Sources:
- https://canadiandefencereview.com/directory/ : Directory of the defence industry

## Focus tree
### Naval
The submarine purchase issue of 2025-2026 was a big deal. Have a choice between two focuses between the historical German Type 212CD submarine purchase, and the alternative South Korean KSS-III submarine.