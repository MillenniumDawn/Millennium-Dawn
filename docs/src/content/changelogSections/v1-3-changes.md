---
title: v1.3 Changes
page_id: changelog-v1-3-changes
toc: 'off'
order: 4
---

# v1.3 Changes

<details><summary>v1.3.2 Hotfix</summary>

Events

- Positive events should now correctly fire (Birb accidentally deleted them like a dingus)

Focus Tree

- Stabilize Food Supply focus now correctly increases opinion for Ethiopia

Gameplay/Mechanics

- Fixed remaining issues with GDP/c upgrades
- Drifts should now correctly update on economic cycles
- Drifts from low stability neighbors now should be checked weekly if stability is lower then 35%

Graphics

- New event pictures
- New focus icons
- Fixes to tech tree icons. Mainly industrial/engineering
- Reorganization of focus icons (backend update)
- Corrected missing portraits for Lesotho and Trinidad
- Fixed missing portraits for Uruguay

Map

- Added Awdal and Khatumo states for Somalia

OoB

- Changed Navy from Portuguese to Spanish

Tech

- Gave Humanoid Robots an effect

</details>

<details><summary>v1.3.1 Hotfix</summary>

Decision

- Fixed USA Cabinet Member Decision

Focus Tree

- Fix for Burmese focus prerequisites being bugged out if rebels are annexed
- Fix for Russian Annexation of Crimea. They receive a core now

Gameplay/Mechanics

- Subsidizing reintegration of child soldiers properly deducts money from treasury
- GDP/C upgrades now function as before

Graphics

- Tech icons fix so they no longer disappear

Operations

- Steal tech operations now function properly referencing appropriate techs

Tech

- Fix the ability to build equipment via research

</details>

<details><summary>v1.3.0 'La Resistance and Friends'</summary>

AI

- AI now should correctly create intelligence agencies
- Peacetime AI will now research industrial/engineering tech
- Additional AI strategies to make SWE aggressive/nationalist AI smarter
- AI now should no longer take generic if they have a better/unique defense company
- AI will be more likely to take their starting ideology path
- AI for Air Doctrines so certain nations will prioritize their historic routes
- CHI Red Dawn Strategy added a few more steps to ensure CHI has necessary opinion from Communist Cadres to take desired focuses
- New SAU strategy that focuses on building up economy and unifying GCC before shifting to Global Jihad.
- Added a AI weighting exceptions to the gdp checks for China so that CHI won't ignore most research options
- Added AI weighting to pay attention to how far ahead of time techs are, so they won't waste years trying to get techs early
- AI will now embargo countries dynamically
- New AI strategy to prevent CSTO from joining Chechen War and spiking world tension
- AI will now correctly budget and maintain dynamic laws based on ruling party
- AI should no longer ratchet military spending to max
- AI should be less likely to convert military factories
- AI should produce the most up-to-date aircraft models now (some aircraft slightly more powerful as a result)

Stability

- Slight tweaks to some EU events to optimize triggering
- Optimization to load order

Decisions/Diplo Actions

- Enabled politics decisions again
- Removing elections now correctly not changes your leader
- Created Embargo and Recall Intervention Forces
- Afghan decisions fixed provinces trigger
- Jihadist manpower decision to recruitment
- Islamic State can no longer send ceasefire

Balance

- Lower construction cost on Mils/Dockyards (Reduced to 65k from 90k)
- Fixed manpower requirements on Carriers. More in line with historical figures
- Added Transport and Attack heli 3 to USA at 2000 date
- Distribution of training laws
- Biofuel refineries now cost the same as CIC and produce fuel worth 5 oil
- Fuel silos no longer require building slots
- Mobile radio masts give local construction speed instead of research
- Economic events happen less frequently now
- Aircraft should now be more resilient against AA
- Adjusted some techs values to give more varied modifiers
- Buffed influence gain from Influence Things
- Reduced cost for laws

Focus Tree

- Poland, Saudi, USA and Nigerias dockyard focuses no longer give landlocked states Mils/Dockyards
- Added Mil/Defense industry opinion buffs to German Bundeswehr reforms
- Chinese and Gulf focus trees have tooltips to show the benefits gained from swapping an internal faction
- Added a Salafist branch for Generic Muslim Nations

Gameplay/Mechanics

- Expanded the Counter-Terror system to Sub-Saharan Africa and Central Asia
- Air strike decision for states to target jihadists in their own territory at Severe Threat and higher
- Terror threat now increases as a result of being puppeted by a non-Muslim nation rather than being in a state of war
- Arab Spring System: over time tension will increase in Arab states as a result of economic troubles, corruption and a lack of social spending that will eventually boil over into mass demonstrations
- ISIS will now emerge if Syria is embroiled in civil war and the Invasion of Iraq has occurred
- Corruption now pertains to political power gain, and easier to influence
- Help system on tabs to help players navigate systems better
- Division names for Belgium
- Improved unit traits to match better for a modern setting
- Positive Economic Events (increased consumer confidence and stock market boom)
- Improvements to the Public War Weariness system
- New war event on declaration for flavor
- New descriptions for Computing Technologies

Intelligence Agencies

- Agencies reworked to fit modern context
- New operation to raise corruption in a targeted country
- Counter-Terror operations involving intel collection, air strikes and special forces raids that can be used against on-map jihadists

Bugfixes

- New Zealand has elections again
- Operatives won't gain media personality
- defense companies should now work as intended
- Fixed Early_APC not properly unlocking armor_Bat and armor_Comp unit types (there was a typo - armour instead of armor)
- Fixed German Imperial Ambition Subtree seek non-aligned instead of nationalist
- Fixed techs pointing to non-existent techs
- Anti-Bully event target correction
- Germany now correctly gets Drone Equipment
- Typo in Equipment corrected
- Korean Defence Companies now should have the right loc string
- Iran will no longer lose cores on Khuzestan and Balochistan if uprisings spawn there
- Fixed Shia uprising events in the Gulf repeating
- Fixed American Recession Events
- Fixed American Microsoft decision calling up an incorrect event
- Lebanon and Libyas Fascist parties now correctly show up
- Fixed some OOB inaccuracies
- Fixed canceling investments didnt give you all your money back
- Fixed you wouldn't lose influence when you cancel the investment
- Fixed that you would only lose part of your int investment when you cancel

UI & Graphics

- New soldier models for USA, UK, Canada, Australia, New Zealand, Japan, France, Germany
- New flags for Nigeria (Boko Haram and Nationalist)
- New flags for Republic of Arabia
- New GCC graphics
- Converted laws to use list view
- Some unique operatives for CHI, SOV, and USA
- Handful of Generic Operatives for nations. No blank portraits anymore
- New graphics for agency upgrades
- Focus filter icons for influence, insurgency, mafia
- Integration of Tolis' submod and additional equipment GFX. New tech tree icons!!!
- New Focus Graphics
- Stateview now fits all buildings
- Unique terrain pictures for major cities around the world

Map

- Map fixes to the Caucasus and Ukraine

Politics

- Reworked politics for Benin

Music

- Added Israeli music

</details>
