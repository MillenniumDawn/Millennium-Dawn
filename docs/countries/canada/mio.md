# Millenium Dawn's Canadian Awakening
Canada hasn't seed a good dusting off since it's initial work at the beginning of the mod. Some stuff was added to it, but overall it's fairly empty. Especially when you compare it to other medium powers such as Sweden, France, or Ukraine.

# Starting small
## MIO
While some of Canada's military industry was brought on-board when MIOs were introduced, several are still missing and they expose great production gaps. While in my propositions I highlights some area of specialisations and bonuses, they are not meant to be only that. They must still offer common bonuses to their area of expertise. Here are some I want to see added:

### Implementation rules
1. Bonuses to corvettes, frigates, and destroyers always apply to both the "regular" version and the "stealth" version.
2. Screen ships are corvettes, and frigates.

## Colt Canada / Diemaco
The sole producer of Canada's standard issue firearms. It should reflect the evolution of Canadian service weapons, from the C7 to the C25, whilst passing by the machineguns. It's current state is good, but it misses content regarding the C25 and its options.

```mermaid
flowchart TD
    T0["Canadian Arsenal Successor<br/>Reliability +3%; MIO research +3%; design-team assign cost -15%"]
    T1["C7 Service Rifle<br/>Soft attack +5%"]
    T2["Centre of Excellence<br/>MIO funds gain +5%; design-team change cost -15%"]
    T3["C9 Light Machine Gun<br/>Defense +5%"]
    T4["Cold Hammer Forging<br/>Reliability +6%; production efficiency cap +10%"]
    T5["C8 Carbine<br/>Breakthrough +4%"]
    T6["Munitions Supply Program<br/>Production efficiency gain +10%; industrial-manufacturer assign cost -20%"]
    T7["C6 GPMG<br/>Soft attack +5%"]
    T8["M203 Grenade Launcher<br/>Hard attack +5%"]
    T9["C7A2 TRIAD Rails<br/>Soft attack +6%"]
    T10["C8SFW Heavy Barrel<br/>Breakthrough +5%; MIO funds gain +4%"]
    T11["Kitchener Plant<br/>Build cost -6%; production capacity +6%"]
    T12["Heroux-Devtek Era<br/>Production cost -8%; MIO size-up requirement -10%"]
    T13["Colt Acquisition<br/>MIO task capacity +1; MIO research +4%"]
    T14["C6A1 FLEX<br/>Hard attack +4%; production conversion speed +10%"]
    T15["C9A2 Upgrade<br/>Defense +4%; breakthrough +3%"]
    T16["MRR Modular Rifle<br/>Defense +5%; MIO research +3%"]
    T17["Lifecycle Sustainment<br/>Reliability +5%; production resource need -8%"]
    T18["EAGLE Launcher<br/>Hard attack +6%; design-team assign cost -10%"]
    T19["CMAR C25 General Services<br/>Soft attack +5%; defense +2%"]
    T20["CMAR C25 Full Spectrum<br/>Hard attack +5%; breakthrough +5%"]

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

**Bombardier Défense**: MIO dedicated to large and light aircrafts, as well as drones. Whilst IRL they are dedicated to large aircrafts, only having them do that seems too restrictive. I'd wrap into it their civilian expertise building light aircrafts to give some variety. Furthermore, IRL Canada is moving more and more towards light jet fighters (F-35 vs Gripen competition) over medium-sized ones. Would encourage players to lean into it.

```mermaid
flowchart TD
    B0["Bombardier Platform Heritage<br/>Large aircraft reliability +3%; air range +4%; MIO research +3%"]
    B1["Challenger Missionization<br/>Large aircraft surface detection +5%; reliability +4%"]
    B2["Global Endurance Tankage<br/>Large aircraft air range +6%; fuel consumption -5%"]
    B3["ISR Sensor Spine<br/>Large aircraft surface detection +6%; sub detection +5%"]
    B4["Maritime Patrol Package<br/>Large aircraft sub detection +6%; surface detection +5%"]
    B5["Medevac Rapid Reconfig<br/>Large aircraft reliability +5%; build cost -4%"]
    B6["Flex Production Cells<br/>Production efficiency gain +10%; production capacity +6%"]
    B7["Executive Jet Aerodynamics<br/>Light aircraft maximum speed +5%; air range +4%"]
    B8["UAV Data Relay Suite<br/>UAV air range +5%; air_defense +4%"]
    B9["Sovereign Multi-Role Fleet<br/>MIO task capacity +1; design-team assign cost -10%"]
    B10["Alliance Commercializer<br/>Large aircraft build cost -4%; production capacity +6%"]
    B11["Portfolio Rebranding Engine<br/>Large aircraft reliability +5%; fuel_consumption -2%"]
    B12["Cross-Border Final Assembly<br/>Large aircraft build cost -5%;"]
    B13["Trade-Law Firebreak<br/>MIO research +3%; design-team change cost -10%"]
    B14["Program Governance Transition<br/>MIO task capacity +1; MIO research +3%"]
    B15["Precision Strike Package<br/>Light aircraft air attack +6%; air superiority +5%"]
    B16["Maritime Killchain Suite<br/>Large aircraft naval strike attack +8%; naval strike targeting +6%"]
    B17["Stand-Off Strike Integration<br/>Large aircraft air bombing +7%; air ground attack +6%"]
    B18["Armed ISR Conversion<br/>UAV air attack +6%; air ground attack +5%"]
    B19["Joint Weapons Certification<br/>Light aircraft air attack +5%; large aircraft air bombing +5%"]
    B20["Expeditionary Strike Doctrine<br/>Large aircraft naval strike attack +7%; air superiority +4%"]

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
MIO specialized in helicopters. It's a large civilian manufacturer of helicopters, and is in charge of building and sustainement of the existing Griffon helicopter. Since it doesn't have a history of building dedicated gunships - and neither does the CAF operates them - I'd do as with Bombardier: make a case for light gunships.

```mermaid
flowchart TD
    H0["Civil Helicopter Legacy<br/>Helicopter reliability +4%; naval range +5%"]
    H1["Griffon Fleet Sustainment<br/>Helicopter reliability +5%; max organisation +4%"]
    H2["Hot-and-High Lift Package<br/>Helicopter naval speed +6%; fuel consumption -4%"]
    H3["Mission Pod Hardpoints<br/>Helicopter hg attack +6%; anti-air attack +4%"]
    H4["Shipborne Rotor Ops<br/>Helicopter surface detection +6%; sub detection +5%"]
    H5["Rescue Hoist Integration<br/>Helicopter surface_visibility -5%; naval range +5%"]
    H6["Modular Avionics Retrofit<br/>Build cost -5%; reliability +4%"]
    H7["Armed Escort Doctrine<br/>Helicopter hg attack +5%; armor value +4%"]
    H8["Northern Rotary Wing School<br/>Production efficiency gain +10%; MIO research +3%"]

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
    C0["Synthetic Training Core<br/>C2 reliability +4%; maximum speed +4%"]
    C1["Distributed Sim Network<br/>C2 build cost -5%; reliability +5%"]
    C2["Mission Rehearsal Suite<br/>C2 maximum speed +6%; reliability +4%"]
    C3["Avionics Procedure Labs<br/>Light aircraft reliability +4%; air range +3%"]
    C4["Joint Fires Digital Twin<br/>C2 maximum speed +5%; MIO research +3%"]
    C5["Pilot Conversion Pipeline<br/>Light aircraft maximum speed +4%; reliability +4%"]
    C6["Operator Certification Export<br/>MIO funds gain +8%; design-team change cost -10%"]
    C7["Whole-Fleet Readiness Model<br/>Production efficiency cap +8%; design-team assign cost -10%"]

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
Another Canadian giant. Probably the largest shipyards in Canada. Let's give it some some bonuses towards destroyers since that's what they are building.

```mermaid
flowchart TD
    %% Industrial foundation branch
    I0["National Surface Combatant Yard<br/>Destroyer build cost -4%; reliability +4%"]
    I1["Halifax Refit Discipline<br/>Frigate, and Destroyer max organisation +6%; reliability +5%"]
    I2["Modular Block Assembly<br/>Destroyer production capacity +8%; build cost -5%"]
    I5["Cold Weather Deck Systems<br/>Destroyer naval speed +6%"]
    I3["Aegis Integration Line<br/>All ship types anti-air attack +4%; armor +4%"]
    I4["ASW Mission Bay Standards<br/>Destroyer sub attack +7%; sub detection +6%"]
    I6["Atlantic Fleet Sustainment<br/>Destroyer naval range +9%; reliability +4%"]
    I7["Continuous Build Cadence<br/>Production efficiency gain +10%; production efficiency cap +8%"]
    I8["Shiplift Launch Complex<br/>Capital ship naval speed +4%; production output +5%"]

    %% National program and contracts branch
    I9["National Shipbuilding Strategy Monopoly<br/>Screen ship build cost -3%; MIO research +8%"]
    I10["AOPS Arctic Patrol Hull<br/>Corvette, frigate, and destroyer ship naval range +10%; armor +4%"]
    I11["River-class Destroyer Combat System<br/>Destroyer anti-air +7%; hg_attack +5%"]
    I12["Halifax Frigate Life Extension<br/>Frigate max organisation +6%; sub detection +5%"]
    I14["Missile Deck expansion<br/>Frigate, and destroyer hg_attack +6%; anti-air +5%"]
    I18["Destroyer Combat Systems Integration<br/>Destroyer anti-air +8%; surface detection +6%"]
    I15["MDA Drones<br/>Frigate surface detection +5%, sub detection +8%"]
    I16["Armed Helicopter drones<br/>Frigate sub_attack +6%"]
    I13["Arctic Offshore Surveillance Suite<br/>Corvette, frigate, destroyer, and cruiser ship sub detection +12%; surface visibility -4%"]
    I17["Icebreaker hulls<br/>Destroyer, and cruiser ship armor +8%; max organisation +5%"]

    %% Fleet readiness branch
    I19["Fleet Readiness Maintenance Node<br/>All ships max organisation +4%; refit speed +12%"]
    I20["NSS Contract Allocation<br/>Screen ship research +10%; production efficiency gain +10%"]


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
Shipyards, and another way to interact with the French hapiness by boosting investment into Quebec. Flavor-wise, I'd like to give them some bonuses towards negating weather impact on naval operations (naval detection, naval hit chance, naval speed, naval strike, positionning). This is due to their extensive work in the matter of building icebreakers and arctic capable warships.

```mermaid
flowchart TD
    %% Arctic escort capability branch
    D0["Arctic Shipyard Heritage<br/>Frigate reliability +4%; naval range +6%"]
    D1["Ice-Class Hull Geometry<br/>Frigate naval speed +6%; surface_visibility -8%"]
    D2["Winterized Sensor Masts<br/>Corvette, and Frigate surface detection +8%"]
    D3["Heavy Sea Stabilization<br/>Corvette, and Frigate lg attack +7%; anti-air attack +6%"]
    D4["Cold-Start Power Trains<br/>Corvette, and Frigate fuel consumption -5%; reliability +4%"]
    D6["Arctic Patrol Doctrine<br/>Frigate naval range +10%; max organisation +6%"]
    D7["Northern Escort Mastery<br/>Frigate sub attack +8%; anti-air attack +6%"]

    %% Program/contracts branch
    D8["Asterix Replenishment Conversion<br/>Support ship naval range +8%; build cost -5%"]
    D9["Combat Vessel Contracts<br/>Screen ship research speed +6%; task capacity +1"]
    D10["Frigate ASW Modernisation<br/>Frigate sub attack +8%; torpedo_attack +3%"]
    D11["Protecteur Class Contracts<br/>Repair ship naval range +8%; build cost -5%"]
    D14["Halifax Frigate Maintenance Contract<br/>Frigate max organisation +2%; reliability +5%"]
    D15["Polar Icebreaker Hull Engineering<br/>Support, and repair ship armor +6%"]
    D18["Polar Max Steel Cutting<br/>Support, repair, corvette, and frigate ship build cost -5%; production efficiency gain +6%"]

    %% Industrial yard modernization branch
    D5["Quebec Refit Throughput<br/>Production capacity +8%; production efficiency gain +10%"]
    D12["Lévis Modular Berths<br/>Screen ship production efficiency +7%; task capacity +1"]
    D13["Champlain Dry Dock Repair<br/>Screen ship reliability +4%; build_cost -2%"]
    D16["NSS Inclusion Framework<br/>MIO funds gain +8%; research bonus +5%"]
    D17["Quebec Capacity Expansion<br/>Production efficiency cap +2%"]

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
    L0["Secure Comms Backbone<br/>C2 reliability +4%; maximum speed +4%"]
    L1["Hardened Data Links<br/>C2 reliability +6%; build cost -4%"]
    L2["Distributed Sensor Fusion<br/>UAV air_attack +5%; air_range +4%"]
    L3["SATCOM Relay Nodes<br/>UAV air_range +6%; reliability +4%"]
    L4["EW Payload Interfaces<br/>UAV air_defence +5%; air_agility +4%"]
    L5["Battle Network Acceleration<br/>C2 maximum speed +6%; design-team assign cost -10%"]
    L6["Joint ISR Export Suite<br/>MIO funds gain +8%; MIO research +3%"]
    L7["Ultra-L3 Collaboration Stack<br/>Production efficiency gain +10%; industrial-manufacturer assign cost -20%"]

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
One of, if not the largest space-oriented company in Canada. They build satelites and spy stuff. They also make remote piloted aircraft systems and radars. Hitherto, bonuses for UAVs (light aircrafts kind), and we'll also lean into the whole rocketry thing with cruise missiles and SAM missiles.

```mermaid
flowchart TD
    M0["Space Systems Integrator<br/>UAV air_range +4%; reliability +4%"]
    M1["Radar Constellation Uplink<br/>UAV air_attack +5%; air_agility +4%"]
    M2["Remote Sensing Pipeline<br/>UAV air_range +6%; reliability +5%"]
    M3["Cruise Guidance Suite<br/>Guided missile reliability +6%; build cost -4%"]
    M4["SAM Tracking Logic<br/>SAM reliability +6%; build cost -3%"]
    M5["ISR-Ordnance Fusion<br/>UAV air_attack +5%; guided missile reliability +5%"]
    M6["Launch Vehicle Discipline<br/>Production efficiency cap +8%; MIO research +4%"]
    M7["Orbital-to-Tactical Killchain<br/>UAV air_range +5%; SAM reliability +5%"]

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
The newcomer star of utility vehicles and light armored vehicles. MIO for that will give bonuses to light and heavy utility vehicles and APC.

```mermaid
flowchart TD
    R0["Rapid Armored Utility Core<br/>Utility build cost -4%; reliability +4%"]
    R1["Modular APC Hulls<br/>Utility armor +6%; hardness +5%"]
    R2["Mine-Resistant Geometry<br/>Utility defense +7%; reliability +4%"]
    R3["Urban Mobility Package<br/>Utility maximum speed +7%; breakthrough +6%"]
    R4["Remote Weapon Station Fit<br/>Utility soft attack +6%; hard attack +5%"]
    R5["Fleet Sustainment Crates<br/>Utility supply consumption -6%; build cost -4%"]
    R6["Export Production Surge<br/>Production capacity +8%; production efficiency gain +10%"]
    R7["Heavy Utility Conversion<br/>Heavy utility armor +6%; defense +7%"]
    R8["Modern APC Standard<br/>Heavy utility breakthrough +7%; soft attack +6%"]

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