---
title: v1.12.x Hotfixes (Every Tank an Upgrade)
page_id: changelog-v1-12-0-every-tank-an-upgrade-hotfixes
order: 13
hidden: true
---

# v1.12.x Hotfixes (Every Tank an Upgrade)

> Looking for the base release notes? See [v1.12.0 'Every Tank an Upgrade'](/changelogs/v1-12-0-every-tank-an-upgrade/).

## v1.12.3b
### AI
- The Zombie AI should now properly build Zombie units ontop of their spawning numbers
- AI should be less likely to propose trade agreements or investment treaties as a non power or minor power (save their PP for more important work)
- AI should be less likely to propose trade agreements or investment treaties as if they are not on the same continent and they are a regional power or below
- AI should be more likely to propose trade agreements or investment treaties if they are on the same continent
- AI will no longer offer investment treaties or trade agreements if they have a pending bankruptcy mission (this was a super rare case)
- MD AI should now look to fill out more faction offices now for things such as Head of Cybersecurity etc
- Increased the likelihood of recruiting scientists for the AI so they aren't as stunted research wise (still will need work to ensure they're working the right direction)
- The European Union AI should now be more likely to issue Pre-Accession programs during the tick for it
- Increased the AI priority for saving political power to join the European Union
- Fixed the AI not properly expanding its research slots via the Research menu
- AI democratic nations now should be less likely to raid other nations if they have added less than 5% world tension
- AI should no longer revoke satellite access within 6 months minimizing them from instantly rejecting
- Fixed the AI rejecting satellite access if Russia is in the EU and has satellite access to an EU member
- AI will be more likely to send satellites in the event they are an influencer in your nation
### Bugfix
- Fixed the Zombies not building units due to the productivity system
- Fixed the decision for Rwanda taking the historical flag in 2001 (gotta love five year old bugs)
- Fixed the Wehrbereichkommando name list not working as expected when recruiting additional units
- Removed out of place Swedish general portraits
- Fixed the Iranian focus "The Mountains of Iran" requiring the wrong focus allowing you to do it much sooner than expected
- Fixed the Swedish focus "Eurasian Rail Link" having weird line configuration due to requiring a focus lower than it
- Fixed the Swedish focus "Vattenfall Energy Link to Germany" only requiring Sweden to own Sjaelland. Made it so any ally or Denmark can own it as well to make it easier to do that focus
- Fixed the Swedish focuses "Transatlantic Economic Forum" and "Cybershield" allowing you to reject your own initiative
- Fixed an oversight in various Swedish focuses using the "Is a Puppet" trigger instead of "Is a subject" as it is not fully inclusive all subject types
- Fixed the Arsenal Bird not being deployable so that late game shitpost now works
- Fixed Hamas not being correctly setup as it did not start with OOB
- Fixed a bug in the raids where they were getting significantly more funds back then expected
- Fixed a large number of issues with part of the BBA conversion using the older references hull types causing issues with dozens of bonuses and equipment
- Fixed people being double charged for Attack Helicopters, Tanks and Air Assault Battalions
- Fixed Ranger unit not being counted for money system
- Added missing ship types to be counted for money system
- Fixed the German event "Public Park Damaged by Armored Vehicles"
- Fixed CZE Skoda Superb bills ideas not properly removing themselves when paying off the bills
- Fixed CZE Increase Eastern Trade focus not possible to complete as Czechoslovakia
- Fixed the God of War not properly giving Army, Air, Naval Experience every month
- Fixed the weird gap in the "Pansarregementen" division template
- Fixed a handful of issues regarding female leaders of all types randomly bugging
### Balance
- Rebalanced the organization of the zombie units so they play a little differently rather then having permanent organization
- Zombies in the Zombie game mode should now spawn more units depending on the difficulty
- You can now set 8 Headquarters instead of 3 for naval headquarters
- Netherlands no longer can achieve mega stonks of 30%+ ROI from the Grey Dilemma decisions
- Modified the Iranian infantry brigade template (Tip-e Piade Nezam) to be manned by light infantry and not motorized
- Reduced the naval dominance required for sea zones by 15% so it is easier to achieve naval dominance in areas
- Increased the naval dominance gain from Frigates from 20 to 25
- Increased the naval dominance gain from Stealth Frigates from 25 to 30
- Made the Railguns for ships more devastating in ship to ship combat and slightly reduced their IC cost so they're more worthwhile to incorporate on heavier ship classes
- Slightly increased the Pre-Accession Program Political Power gain to 400 from 360
- Reduced the Air Wing Volunteer cap in several nations who currently had unlimited air volunteers
- Replaced a pointless doctrine cost reduction in American focus "Adaptive Tactics" with mastery gain
- Increased the interest reduction in Swedish Focusses
- Increased the multiplication cost of nuclear reactors as they're much stronger due to the naval dominance mechanic now
- Reduced the amount paid in Raid Reparations to 2% from 3%
- Clamped the total amount of billed reparations to $150 Billion
- Changed modules of Polish naval vessels to better reflect their real life counterparts from 2000
- All support companies should now impact speed as they should
- God of War now grants mastery for the AI when they have doctrines
- Non-AAT defense companies values are standardized at Level 5 bonus (7.5% of their respective bonus) while retaining their old custom bonus due to reducing the complexity of the old defense companies
- Made some non-AAT defense companies worth taking now that are at least as good as the generic ones
### Content
- Added a Zombie outbreak random event that triggers to spread Zombies around the world to make the game mode more interesting
- Serbia won't start the 3rd Balkan War when historical is on
- "Complete the Bothnia Line" Swedish Focus gives a research bonus to all rail tech instead of high-speed rail
- Artillery Doctrine Track Mastery can also be gained by MLRS now
- Changed Norway Mining Tooltips in the Focus Tree
- Changed Events in Swedish focus tree to gain them instantly instead of 7 days
- Russia can actually see the focus tree for the European Union now
### Database
- Adjusted the F-15E Strike Eagle to have 2 Medium Hardpoints instead of 1 Medium Hardpoints and 1 CAS Hardpoint
- Made the "Change Flag" decision for Country Flag Decisions more flexible for the USA and other tags
- You can now mount VLS into all auxiliary slots on the Battlecruisers like God intended
- All starting naval bases of 8 and higher have a naval headquarters assigned
- Added the module "Refueling 2" to the Su-24M and Mig-31 Foxhound so they have extra
- Added on-game-start production for military Iranian equipment
- Made some Swedish Equipment Obsolete to give the player a clearer start on equipment
- Mechanised Marine gives mastery to the Mechanized doctrine track
- Changed Israel's starting intervention law from limited to Regional
- AI, 3D Printing, and Nanofibers tech provide Civilian Specialization (breakthrough points) for researching those techs
- Removed all unused non-AAT designer companies traits that were not used
### Documentation
- Reformatted the Code Resource on the website to be more approachable for submodders and developers
- Added MIO Company and Trait Code Stylization Guide for developers and others who are looking to contribute to MD
### Graphics
- Assigned the USA b6 icon temporarily to the Arsenal Bird
- Assigned generic icons for the Arsenal Bird until we have more custom graphics created for them
- Fixed a missing icon in Myanmar's tech tree for infantry equipment
- Fixed a missing icon for the Repair and Support ships when looking at them in the naval screen and on map
### Localization
- Fixed the "Canonization of the Romanov Family" having two identical text for options
- Added a description to the Kenyan "Social Democratic Party of Kenya"
- Fixed the localization in the Kursk Submarine Disaster stating the August date
- Updated Swedish modifier localisation so the effects are more clear in the focus tree
- Removed the work 'Factory' for Military and Civilian Research category
- Fixed missing tooltip for "Strike Operations Focus" Swedish Focus
### Map
- Added a new state for the Australia Capital Territory
- Rebalanced Ukraine resources so it is more accurately represented with their resource placement
- Slightly reduced German starting steel to be more reliant on outsiders for resource requirements
### Performance
- Removed an every state call at the startup of the game to improve load time performance for the Hydroelectric configuration for the energy system
- Reduced the every country calls on monthly to speed up the monthly tick
### User Interface
- Fixed some missing unit details in the naval screens regarding Naval Dominance and Support values
- Fixed the broken buttons in the faction rules being unable to select additional faction rules
- Fixed conflicting UI in the ship menu with the new ship classes added
- Fixed missing national spirit icons for Sweden
- Added some spacing in Swedish focusses for better view at the focus rewards
- Fixed some issues with the Unit Leader interface namely around missing sorting buttons when promoting a unit leader
- Added the missing containers about factions commanders that was causing some issues



## v1.12.3a
### Bugfix
- Fixed being able to send a ceasefire to the Zombies via the Public War Weariness
- Fixed the generic Military Industrial Organizations using the wrong hull types
- Fixed the broken "War in Europe" game rule where it would send a ton of events at the beginning of the game
- Fixed the Zombies puppeting nations during the game rule which causes the Zombies to break
### Database
- Added a failsafe for the Zombies to annex subject nations if they do ever somehow have subjects
### Game Rules
- Added a game rule for the Zombie game rule for allowing all or no majors into the zombie coalition
### Localization
- Fixed the missing faction localization for the Anti Zombie Coalition faction



## v1.12.3
### AI
- Improved the conditions for NATO joining on historical game mode so nations do not randomly join who shouldn't
- Improved the AI selection for their grand doctrines
- Improved the flow of the European Union law selection when on the "Historical Game Mode" option
- Improved the AI supporting or rejecting specific European Union measures when on the historical game rule
- Ensure the AI is more likely to reduce Population and Corporate tax if they have less than 25% GDP to Debt Ratio
- Ensure that the AI is more likely to reduce Population and Corporate tax if they have than 5% interest with positive income
- AI controlled US will now properly scrap the Iowa class battleships when playing on historical
- AI controlled Bulgaria will now not start a war with Macedonia when playing on historial
### Bugfix
- Replaced Singapore's local_building_slots_factor with global_building_slots_factor allowing for the idea bonus to give a bonus
- Fixed Spain not starting with its navy as it should
- Fixed not gaining income from the sale of missile equipment on the International Market
- Fixed naval invasions not being able to be upgraded by techs
- Fixed naval invasions not being able to have more than x amount of divisions in a particular invasion
- Fixed Bavaria, Sicily, East Turkmenistan, Montenegro, Vojvodina, and Free Syrian Army not being correctly configured when released via national content
- Fixed Chinese STE missions and moved them to an idea
- Fixed German Paravia MIO not being able to use for medium planes
- Fixed EU voting breaking after annexing the country that proposed the law
- Fixed decreasing EU Global Call Rate not taking political power
- Fixed EU Global Call Rate not changing all countries' Call Rates
- Annexing an EU country should stop any ongoing votes
- Fixed a broken clamp variable that would error for Max Stored Energy causing some small internal issues w/ the storage energy system
- Fixed a broken Swedish Event that did not correctly spawn a unit
- Fixed the Fiji tree erroring for a removing a dynamic modifier regarding Fijian Ethnic Tensions, Homelessness, and Emigration Crisis
- Fixed a Cuban event making Russia give itself military access causing some intermittent save game corruption
- Fixed the North Korean event "North Korea Asks For Protection" causing China to sometimes try to give double guarantees
- Fixed the Sudanese event "Uprising in El Fasher" trying to trigger uprisings that it can't trigger
- Fixed the Islamic Emirate of Kurdistan being double subjected
- Fixed a number of Iraq events that were incorrectly not spawning units as they should due to a missing unit template
- Fixed released tags starting with a massive amount of research speed and their satellite system broken
- Fixed the Network Satellite Civilian percentage of coverage for the Communication Satellites showing up as an overflow variables
- Fixed a bug where the Union of South American Nations required the Rhineland instead of Curaco
- Actually fixed the Iranian and Lebanese support focuses for Hezbollah properly giving you money
- Fixed a bug in the Indian tree for the national focus "Dealing with European Companies" to properly
- Fixed the major crash for games at high world tension (the issue was due to template failover from vanilla being missed in MD)
- Swedish MIO Ericsson now uses a modern icon
- Fixed a potential issue with the overflow of gdp/c and productivity due to divide by zero
- Fixed the faction button for NCNS owners not fitting properly
- Fixed the Austro-Hungarian highlight state trigger not properly displaying all nations as they should be highlighted
- Fixed the Austro-Hungarian formable nation not being able to be properly annexed
- Fixed female leaders showing up with blank/no portrait (Thanks Davey!)
- Fixed the Marine Commando special effect not properly working and applying damage to the state on naval invasions
- Fixed the issue where if you changed away from a doctrine you were unable to pick that doctrine type again without manually clearing things
- Fixed a spamming issue in the doctrine menu when viewing the doctrine tracks
- Fixed an issue with the minimum default garrison law causing a small error in validation on game start
- Fixed the Iowa Class event not properly triggering for the United State
- Fixed the container not allowing you to add a "Faction Goal" due to a misconfiguration on a vanilla container
- Fixed the Influence decisions for attacking the largest influencer not working as expected causing some issues about not giving you the full -5%
- Fixed North Korea being double charged political power for decisions
- Fixed Chechnya not being puppeted by the AI Russia
- Fixed the Swedish getting an infinite money glitch when annexing Norway due to the code improperly referencing Norway instead of Sweden
- Fixed the event "Swedish Investment in Our Banking Sector" showing an error regarding influence
- Fixed some Chinese internal factions sometimes lying about the opinion required for some of the focuses
- Fixed German Demand of American Island events. Not you get informed as Germany what America does
- Fixed Sweden's focus "Form a Royal Circle" which sends an event to itself
### Balance
- The Post-Crisis Fiscal Decisions event now makes the Labour Union unhappy instead of happy
- Removed an error involving the Abkhazian focus "Free Education" referencing a non-existent idea
- Made the Venezuela oil decisions fire only once so you can't get permanent oil from the decisions
- The internal faction decision "Subsidize Workers Wages" should now increase social spending to accurately represent subsidies
- Major powers can now create factions as well
- Added the support company nerf to the SP Arty, SP Rocket Arty, and SP AA batteries that were currently missing them making them as effective as the regular battalion
- Adjusted the Armenian focus "Excavating Deep Resources" to give 6 oil and 6 steel while also only requiring Excavation 5 so it's not so late game
- Applying to the EU requires less than 15% Euroscepticism
- Reduced the cost of suicide drones to 45 with 15% increases in IC per level
- Set the manpower level of Kamikaze Drones to 1 to minimize their manpower cost
- Opened up the ability to use different types of missiles in raids
- Rebalanced missile tech bonuses based on generation
- Extended the length of time the state modifier Nuclear Fallout from 365 days to 1095 (shouldn't be so short term)
- Significantly reduced the bonuses Iraq receives from winning the 2nd Gulf War
- Set the base chance for female leaders to be 5% assuming your national laws support having female leaders
- Improve the balance of the Chinese tree with "The Military" and "Communist Cadres" internal faction so it doesn't soft-lock you out of content
- Slightly reduce the total equipment cost for all equipment types
- Slightly reduce the total time for equipment to get delivered across the board from the International Market
- Reduced the contribution gain for "Supporting with Scientists" for factions
- Increased the Faction contribution score for being the leader so it's more substantial
- Clamped the total amount of consumption if you manage to get over 100% bonuses to nuclear consumption so you don't get free fuel
- Norway asking for oil investments, also gives a benefit to the country wanting to invest. Instead of giving money and not gaining anything
- Slightly reduced the starting position of the cartels in the Philippines
### Content
- Added Latvian political parties with expanded descriptions and flavor text (thanks to Pakman who wrote these some time ago!)
- Added a time for battery park for construction and added a shift click option for 3 to be built at once
- Added an automated buy fuel button for the Energy GUI "Buy Fuel from the Market"
- Russia can now join the EU via the new 4 Extended Enlargement Framework Laws
- Freedom of Russia Legion can join the EU via the Internal Enlargement Law
- Added a new Eastern country category to the EU
- In order to start a vote in the EU Parliament or Council, there must be an EU Commission President
- Ukraine, Belarus, Russia and Freedom of Russia Legion are part of the Eastern countries category
- Merged POTEF several POTEF ideas into a dynamic modifier
- Added an Eastern Doctrine branch to POTEF tree
- Revamped the Parliament MEP calculations
- Reworked the EU Budget to be periodic and have AI engage in it more
- Added Minimum Call Rate to EU Budget. Allows for adjusting the minimum Call Rate for every country during MFF Drafts
- Added triggers for a few EU parties to change their names and logos at specific dates
- You can rejoin the EU after leaving it
- Added the Swedish communist party to the left wing tree and the eastern alignment tree
- When you now launch a coup for Shia government it'll switch your religion to Shia
- The requirements for Debt Assumption if the nation if the nation is your subject are reduced and only require you to have positive opinion
- Added an event for the canonization of the Romanov family as a nice little flavor event for Russia
- Added a new opinion modifier for State Visit to Vietnam
- Added an event for the crash of the Su-37 in Russia
- Hid additional national focuses custom factions behind visible always no so they don't show up when they're not supposed to
- Added a new game rule for gameplay "Zombie Mode" based off of the Doomsday Series submod for Millennium Dawn
- CV90 platform changes. CV9030 exists as license for Finland, Switzerland and Norway. CV9035 exists as license for Denmark and the Netherlands
- Two new Swedish events handling Visby Corvettes and CV90 BILL
- Sweden now starts with the Patria XA-185 and XA-203. Named Patgb 185 and Patgb 203.'
- Sweden has new MIOs. Alvis Hägglunds - Strv. Focused on MBTs and light tanks. Alvis Hägglunds - Strf. Focused on IFVs and APCs. Saab Bofors Dynamics AA manufacturer. Bofors Weapon Systems AT manufacturer. Saab Bofors Dynamics - Gevärsfaktoriet as Infantry manufacturer.
- Increased amount of Swedish cities across their states. Alongside changed resources and state buildings
- Made it so the German v fall decisions do not ensure you are unable to do nuclear things if you have done the focus "German Nuclear Program"
- Modernized the Uzbek Karakalpakstan and adjusted some of the tooltips to display the current opinion of the Uzbek and Karakalpak
- Added the "Holy See" idea to the Papacy so they do not bankrupt themselves constantly and get income from the Christian nations of the world
- New monarchist branch for Czechia
- 2 new game rules for Czechia
- New monarchist party and its leaders for Czechia
- New alliance, The New Entente, possible to form by king-ruled Czechia
- Added the sale of the Kee-Lung Class Destroyer to Taiwan for the United States Foreign Policy decisions
- Internal Factions minimum opinion for monthly tick is now relative to your ideas (if an idea adds +10 opinion the monthly tick won't go below 60)
- Adjusted the number of dockyards, military factories and technologies start for North Korea so it is less awful then normal
- Changed the German military national spirit to the dynamic modifiers if possible to have it better grouped in the UI
- Changed all German changing modifiers tooltip for better readability
- Created default preset for MIOs for SOV and USA
### Database
- Removed the ahistorical "7th MARDIV - 35th Marine Regiment" from the United States
- Fixed the namelist of the Marine Regiments being properly ordered with the correct number denomination, no more 34rd
- Added a new Battleship and Battlecruiser for 2045
- T-80B/BV should now have Late Cold War Medium Tank guns
- Add Wallis and Futuna, Tristan Da Cunha, Tokelau, Niue, Norfolk Island, Cook Islands to the content.
- Enormous number of EU variables, gui elements and localisation keys renamed
- Removed all/most code related to EU002 law and other redundant EU code
- Changed all EU party names for easier dynamization in meta effects/triggers
- SOV and CHI influence in EU countries has been seperated
- Moved the unlock of the Assault Cannon modules to the assault cannon techs
- Comprehensive improvements to the Russian OOB such as changes for cast turrets for various vehicles, armor, and more as well as adjustments to ships for better accuracy
- Fixed the Isle of Mann not correctly starting with a religion idea when released
- The Russian "Sierra" class is now properly a nuclear submarine
- Added another enrichment facility to the United States to stabilize early game nuclear fuel production for the USA
- Changes for Sweden. Ikv 91 changed from HAT to light tank. Gripen no longer has A2A refueling. Gripen is now called Gripen A. No longer starts with Visby Class. Pbv 302 now has it's turret. 9 new characters. Piranha III APC's from Switzerland were removed. Stridsvagn 122 now uses level 3 smoke launchers. Stidsvagn 121 now starts with gen 1 thermals.
  Bv 206 is now exclusively an APC. Changed order of utility vehicles, now it's Personlastterängbil 903 - Terrängbil 11/13 - Terrängbil 14 - Terrängbil 15. Land rover removed. Now has better represented HAT, with the Pvtrgb-B RBS-55 and Pvrbv-551. Now starts with Lvkv 9040A, Grkpbv 90 and the improved Strf 9040B. No longer starts with medium airframe techs.
  No longer starts with Attack helicopter, both tech and Mo Bo-155 attack helicopter variants. Swedish equipment now starts with MIO's assigned to the things that can/should have it. Infantry equipment has been changed around to better represent their IRL equivalent.
- Sweden now uses the Regiment System. They still start with the same amount of units. But these are now more closely based on how Swedish units looked. Following "Battle Order"'s batallion breakdown of Swedish armored forces alongside existing documentation.
- Shifted all 3 variants of the Harrier to the Medium Hardpoint so they can be used as naval strike craft
- Converted the Ratel 90 from Light Tank to IFV
- Integrated the new Energy Infrastructure and Industrial Infrastructure buildings
- Enabled the "Support Ship" and "Repair Ship" from vanilla for better supporting units for the ships
- Added an opinion buff to the civil war that comes out of the influence coup mechanic
- Expanded the number of ship names for the United States Navy with a variety of additional ships such as decommissioned ships and otherwise
- Increased the size of your total amount of stockpile to 2 billion from 2 million due to backend upgrades from PDX
- Expanded the political landscape of the Philippines with greater detail and leaders
- Expanded the number of generals and advisors in the Philippines
### Game Rules
- Removed the "Change Legacy Doctrines" game rules since they no longer exist in the traditional manner
- Set "Recall Volunteers" to default to yes since Paradox makes the recall actually take time for the troops to return now
- Created a new game rule for "Allow Enforce Peace" diplomatic action
- Fixed a tooltip for the "Historical Event Trigger" to explain they are still randomized but not perfectly on time for specific events only
### Graphics
- Removed idea description images for now until we have a more consistent use case for them
- Fixed graphics for various variants that were relying on the generic afv profiles
- Added new operative graphics and additional generals for the Indian subcontinent
### Localization
- Fixed the event "Nord Stream" and "Nord Stream 2" having two "agrees" instead of an agree and decline
- Fixed a number of "Unknown promotion" errors in the error log during runtime
- Renamed the religious idea "Christian" to "Western Christian" to more accurately portray it
- Changes made to Swedish MIO names. Aligning them more closely to what they were in 2000.
- Fixed some missing localization in the doctrines for some of the unit categories like Light Fighters and All Aircraft
- Fixed default focus tree search filter typo (`FOCUS_FILTER_MILITARY_EQUIPMENT` -> `FOCUS_FILTER_EQUIPMENT`).
- Added a tooltip for the V Fall events stating that if you do them you are unable to change your nuclear status
### Performance
- Reduced duplicate code across on actions which should hopefully optimize various actions throughout the game
- Removed a number of non-essential code from the Space System which should minimize the size of save game files
- Optimized the on startup scripts by removing unneeded every country calls reducing the load time for people
### User Interface
- Fixed some containers showing all 6 digits for the decimals (will be a overtime process)
- Added an additional openable display to the EU UI, currently accessible only in the Parliament tab, which shows MEPs per country
- EU Parliament Party Influence buttons are now green if they're available to click
- Added an Average Economy display to the EU Budget window
- Added a new tooltip to the Satellite Orbit screen and tooltips to be more clear about hwo to change the satellite orbit view
- Removed all placeholders in the doctrine section and created unique GFX for each tab
- Increased the size of the buildings in the construction menu and added missing buildings GFX
- Added tooltips for buildings to see what their production speed modifier is in the construction menu.
- Changed state view to align new building state modifier with the dynamic modifiers.
- Added a display in the Energy screen to show you how much power the reactor or fossil fuel power plant will produce
- Added the "Stored Energy" to the Counter UI under the "Energy Balance" header



## v1.12.2a 11/22/2025 - Hotfix A
### AI
- If Estonia has a wargoal and they're less than on-par strength to Russia they won't declare war on Russia
- Estonia should try to actively pursue more relations with Latvia and Lithuania, vice-versa
- Increased the desire for nations with lots of nuclear reactors to try and build additional enrichment facilities
### Bugfix
- Fixed broken drop downs in the air UI menus for change day night, aggressiveness showing blank menus instead of the correct options
- Fixed a crash due to a missing button for legacy faction menus
- Fixed missing frames around officer corps leader
- Added different effects to "Expanding The Public Sector" Focus of Germany to prevent no effects given
- Fixed some triggers for news events for NATO
- Reduced cost of taking Chechen states for Russia
- Fixed the LAR operation "Steal Naval Blueprint" consuming a civilian token instead of a naval token
- Removed a Man the Guns check in the game rules for "Take over Faction"
- Fixed the internal faction "Industrial Conglomerates" not properly initializing when switched during the game
### Balance
- Dramatically increased the base Energy Production so the Lack of Power modifier should not appear
- Reduced the vanilla energy consumption mechanic closer to 0 to help with Lack of Power sometimes appearing in game
- Reduced the amount of ROI you can get via the focus tree for Sweden. Damn Swedes and their savvy investments
### Content
- Added a new diplomatic action "Negotiate Operative Release" allowing you to pay some money and political power for the release of a captive operative
- Adjusted the triggers for Threat of Terrorism for India so you don't get locked out of the tree if for some reason America cannot do Operation Enduring Freedom
### Database
- Fixed some minor discrepancies with Swedish starting variants
- Rebalanced the starting Swedish party popularity to their most recent election result (as of 2000)
- Added 1 enrichment facility to India
- The 2K12 Kub now has off vehicle radar and 2 missile pack instead of the incorrect on vehicle radar and 4 missile pack
- Lowered the generation of World Tension
- Updated the Ecuadorian OOB to be more accurate w/ light tanks and some missing self propelled systems
- Removed the defunct Super Heavy Tank Barrel special project (removed in favor of the reworked ammo system for tanks)
- Gave the United States another enrichment facility
- Cleaned up some unused variables in the Coptic system for Egypt
- Fixed the event "A Royal Visit with Strategic Intent?" not correctly giving influence
### Factions
- Added a new long term NATO goal "NATO Economic Development" asking you to get every member state to 25k GDP/c
### Game Rule
- Added a game rule for people who want to freely change internal factions without downloading a submod (express content prohibiting it will still block it)
### Graphics
- Set a default temp icon for Naval Headquarters so its easy for people to see
- Fixed "Agent K" not properly having his leader portrait populate
- Fixed missing Ranger Division icon (Credits to WHACK)
- Fixed broken portraits for the Indian generic generals when they get promoted
### Localization
- Fixed some missing localization in the faction tooltips
- Fixed missing Localisation for German HDW Traits
- Rewrote the alert for "Insufficient Energy" to tell players to dismiss. It is not actually there but should relieve people's stress.
- Fixed the Swedish "Crypto Income" mechanic not displaying properly in the Additional Income section
- Added a tooltip for the Swedish "Allow Crypto" focus to notify people of the Cryptocurrency Mechanic so they don't get spoked by the sudden destruction of their economy
### User Interface
- Fixed the broken Intelligence Agency buttons and UI
- Removed the non-working Missile Doctrine button
- Fixed a missing icon for "unit_med_cas_fighter_icon_small"
- Adjusted the air doctrines positions in the officer corps view
- Fixed the tiny faction logo in the politics UI view



## v1.12.2 11/20/2025 - HOI 1.17 Compatch
### Achievements
- Added new achievements "Waa-shington State" and "Make America Libertarian Again"
### AI
- Cleaned up some references to add_ai_strategy to be more performance friendly
- Added a check to ensure that Erdoğan and Turkey do not leave NATO as an extra safety measure
### Bugfix
- Fixed a bug where the United States would receive an event about a SHORAD project it proposed to NATO members (The U.S. was not supposed to receive it)
- Fixed a bug where NATO members were unable to reject the SHORAD project proposal from the United States
- Fixed a bug where France "Stage" focuses were not properly checking for their respective regions
- Removed a bugged event that was causing other nations get an idea that is meant for Armenia/Georgia
- Fixed an issue where Italy would send an event to Egypt that had an improperly targeted state for the oil deal adding oil to Argentina instead of Egypt
- Fixed a bug where the Greenland capital was set to the impassable state instead of the correct state which has Nuuk
- Fixed a bug where the POTEF focus for German Doctrine incorrectly asking for an AND condition of Bayern and Germany instead of OR
- Fixed an issue where Italy's NIMBYs could suddenly start benefiting the government more than it should
- Fixed a bug where the Syrian Civil War from the Arab Spring would not unlock the post-civil war focuses for Syria
- Fixed a bug where China's economic focuses for developing various regions did not accommodate for subjects such as the SARs
- Fixed a bug with the Arab Spring mechanic where the "Extensive Welfare State" idea was not properly reducing the Arab Spring change
- Introduced a degree of randomness to when the Arab Spring protest events spawn for each nation after the mission timeout so the world doesn't get spammed with events at the same time
- Fixed a bug where Singapore's opinion modifiers were not properly decaying and instead were increasing the opinion
- Removed duplicate defines that were in the defines
- Fixed the achievement "Perot Meritorious Service Award" not properly triggering due to a bug in the tooltip looking for neutral conservatism instead of neutral autocracy
- Fixed the Soviet division name "98th Guards Airborne Division" not properly being set to 98 and instead taking the name of 96th
- Fixed the SCO GUI not properly being displayed and instead showing the dynamic lists twice
- Fixed the Iraqi event "Iraqi Forces Storm our Embassy" not properly creating a unit for the Iraqi forces
- Fixed the Russian Event regarding Alexander Lebed dying triggering when Alexander Lebed is in control of PMR
- Fixed the Arab Spring events about army mutinies happening when the Arab Spring has been completed
- Fixed the cosmetic tag for the Maghreb Federation not properly being set which was causing it to not properly show the flag
- Fixed the Singaporean ideas using the wrong building slots factor modifier causing it to not properly work
- Fixed the Israeli focus "The Oslo Accord" not properly requiring you to complete the focus "The Regulation Act" soft-locking you on the sub tree
- Fixed the Hezbollahi idea "Increased Iraninan Support" not properly giving money as expected
- Fixed broken tooltips for Burmese Insurgency mechanic regarding influence
- Fixed a broken localization for the United States Foreign Policy with it stating something about africa when it's in respects to resetting relations with Russia
- Fixed other countries then HOL and BEL receiving Belgium and Dutch characters traits
- Changed ai weights to Russian focusses, preventing them going to war without bordering NATO or Ukraine without preperation
- Added missing starting coalition members for Netherlands
- Remove unintended double polical power gain penalty when monarch is blocking laws in The Netherlands
- Added bypass triggers for VOC focusses when the country is the puppet of the Netherlands
- Fixed wrong bypass triggers for Dutch WIC focus tree branch. Now it properly bypasses when the country doesn't exist, or you already own the state.
- Fixed Dutch Liberal Society modifier not giving the reduction cost to economic focusses
- Fixed numerous fixes for the VOC content for the Netherlands
- Fixed Dutch Mars event chain not giving rewards or penalties
- Fixed German MIO's not being selectable for their equipment groups, while having traits for it
- Added tooltip to inform player how the Dutch PvdA Leader gets elected
- Fixed the lingering configuration of the European Union on nation states that retain configuration from the European Union post-civil war
- Fixed the constant civil wars if you disable the Libyan Triablism mechanic and have less than 10% opinion for any of the breakaway tags
- Fixed the broken influence actions in the Libya focus tree when the conditions for the targets are not valid
- Fixed the broken Spanish Empire cosmetic tag going away
- Fixed a broken influence target in the Syrian national focus tree for the focus "Chinese Anime"
- Removed a broken event in the German tree referencing GER_cold_war.26
- Fixed two Iranian Parliament missions giving some impossible requests if a IRQ or SYR do not exist
- Fixed Dutch focusses and events not giving production lines for naval ships
- Fixed Iraq scientist not being available after event
- Fixed a broken influence tooltip in the Syrian "Anime Industry Boom"
- Preventing Belarusian civil war when there is no police funding
- Prevent Romania start world war 3 when Historical is on
- Added visibility condition check to Spanish `Install the Carlist Monarchy` decision
- Removed global stability penalty for news event `United States Not So United?`
- Fixed unexpected combatants increments to both sides when using the Serbian `Attack Montenegrin Militants` decisions.
- Fixed Incorrect state transfer and tech inherit for Catalunya independent event.
- Fixed hard coded welfare decrease.
- Fixed the USA getting the event about increasing it's military spending for NATO
- Fixed Vadim Corneliu Tudor reincarnating after his daughter gets retired, damn Transylvanian
- Fixed Indian subcontinent breakaways having Chinese portraits instead of Indian ones
- Added a check to ensure that Belarus exists for America to be able to do the Belarus Democracy Reauthorization Act
- Fixed USA being able to do the Belarus Democracy Reauthorization Act without having any influence or network strength
### Balance
- Reduced the stability penalty for the "Nuclear Power (Offensive)" idea from -0.15 to -0.10
- Reduced the cost from Somali Pirate event from 25 billion to 15 billion and instead of 5 convoys, you only lose 2 convoys
- removed the regional power requirement from the Space Programs for civilian projects
- Reduced the cost of the special project facilities from 50,000 to 45,000
- Changed the modifier for the "Global Diplomacy" ideas for Singapore from send_volunteer_factor to send_volunteer_size so you can send more volunteers
- Made the Bolivian focus "Purchase Russian Aircraft" purchase MiG-29 Fulcrum instead of Tu-160 since these are more realistic for Bolivia
- Added more factors to the various economic events (too many random little changes to help fluctates the events and make some often unsee ones a little more likely to come up)
- Reduced some of the Italian productivity modifiers so it's not so substantial where they end up passing USA just by being Italy
- Added a check that Bosnia needs to be at peace to take the focus allowing them to join NATO
- Fixed non-Arabic countries finding their way to being able to be invited to the UAR
- Increased the penalty of using VOC or WIC occupation laws
- Having increased healthcare spending (Level 3+, low corruption, and government popularity) should now reduce your Arab Spring protests
- Increased the amount of oil gained via the focus tree for VEN to better represent their large-scale/sized oil reserves
- Adjusted the trade opinion so it's more penalizing on trade opinion factor with the trade laws
- Adjusted the penalties for Dutch non-selfsufficient idea
- Added additional triggers to Dutch Space Focusses
- Added a additional trigger for allowing a nation to go to Neo Imperialism if you have the intervention idea
### Content
- New Content For MP Under Game Rule to Speed games up
- NEW/IMPROVED FOCUS TREE: Sweden, South/North Korea
- NEW MIO TREE: Romania, Brazil, Australia, China and Japan
- Added new decisions for Bolivia to allow them to develop their oil reserves
- Added "Robert Hanssen" as an operative for the Russians to use with American citizenship
- Added an event for Venezuela where Hugo Chavez dies and Nicolás Maduro becomes the president (Requires Hugo Chavez to be in power at the time)
- Added a date trigger for the United States event "Lehman Brothers Collapse" to be any time after 2005.1.1
- Added new content for North and South Korea as well as a new Sub Tree for North Korea
- Added new decisions for Venezuela to further exploit more of your oil reserves
- Changed Chinese STE decision to a mission so there is less micromanagement. Also added a new mission, which was not visible do to a wrong trigger.
- Added a bypass for "Recognize Novorossiya" so the Russian tree doesn't get soft locked when Ukraine is invaded earlier and before the NOV rebellion
### Database
- Added 16 Su-24MRs to the Ukrainian stockpile in 2000
- Added 2 missing Marine Regiments to the USA in 2000
- Changed the starting economic cycle for the USA to "Stable Growth"
- Added 2 enrichment facilities to France
- Changed the 9k33 OSA to properly have the battlestation it should have
- Added the Mid Air Refueling module to AMX Ghibli (International)
- Changed the T72A so it has an Cold War Battlestation instead of an Early Cold War Battlestation
- Added Modern A2A Weapons tech to Ukraine due to their company Artem designing a lot of the advanced Russian missiles
- Added Highlight states for all Formable Countries, making easier to see which states you need
- Added tooltips for Dutch Focus trees to let you see the reward when sending an event to a country
- Sorted the Country AI behavior Game rules to alphabetic order
- Changed CAT_naval_misc to CAT_naval_modules for clearer information
- Changed CAT_naval_eqp to CAT_naval_all for clearer information
- Reclassified the S3-Viking as the more modern version of the plane type over the S-2 Tracker
- Added new generic general portraits for Indian subcontinent nations
### Game Rules
- Added a new game rule to disable the AI from puppeting other nations via the influence system
- Added a new game rule to disables aggressive features for Western nations
### Graphics
- Converted all PNG assets to DDS to better optimize for lower end machines
- Fixed a broken graphic for Belarus in their utility vehicle graphics
- Created new MIO Trait icons
- Created new Organisation select icons
- Restructured the MIO selection screen
- Fixed Czechia having access to the T72M2 Moderna and Slovakia having the T72M4CZ
- Added missing Special Project GFX
### Localization
- Removed a confusing statement in the Arab Spring events where it mentioned caretaker governments but was using the name of the former leader instead
- Fixed the localization for the Transport Helicopter Equipments
- Improved the localization for the influence tooltip for when a nation is trying to influence
- Fixed the missing localization for the Cuban focus "Talks with Colombia"
- Improved the grammar and structure for some Serbian events
- Fixed the localization for the Indian events about communist rebellions not properly referencing India
- Fixed the name of "Megawati Sukarnoputri" being incorrect for the Indonesian politician
### Map
- Moved Al-Amarah north of Basrah instead of its currently inaccurate position
### Performance
- Numerous improvements and cleanup on old and antiquated systems making them more in line with modern standards
- Removed a large number of unused assets and localization optimizing load times
- Removed a series of country flags and arrays that were not being used further optimizing the save file
### User Interface
- Fixed a broken UI element when trying to design Self-Propelled Artillery as Russia

  

## v1.12.1b 8/22/25 Hotfix
### AI
  - AI is less likely to continue to combat influence if their highest influence has a very positive opinion (+100)
  - Improved some of the AI handling of the buying and selling of reactor grade fuel
### Balance
- Rebalanced the purchase of reactor grade fuel from 500 units to 2500 so you buy a larger amount of fuel so you do not need to do it as much
- Reduced the time to deliver for International Markets to 45 days from 60 days
### Bugfix
- Fixed the US Event "United States Offer SHORAD Projects" not properly giving influence to the right nation
- Fixed the Algerian character "Fatima Zohra Ardjoune" not properly showing up in the GUI
- Fixed the country flag decisions this time for real (they broke just a few days ago)
- Fixed the USA decision "Moving in on Africa" not properly checking for China
- Fixed the Iranian Majles being able to object to law changes despite them being abolished
- Fixed the Russian destroyer variant Talwar Class having a module that was available in 2015
- Fixed two influence triggers for the Belarusian Union State mechanic displaying the wrong name
- Fixed an influence trigger in the Belarusian Union State mechanic where it states 70% influence but in reality was looking for 80%
- Fixed Dutch decisions not being visible after taking the "Economic Revitalization of the Dutch Caribbean" focus
- Fixed Dutch country leader switching when House of Orange is in power and King/Queen is abdicating
- Fixed Dutch events and decisions giving building to random states instead of random owned states
- Fixed Dutch focus "Global Vision" not giving ruling party popularity
- Fixed Dutch event for Peru ending up in Iran
- Fixed Dutch annexing themself when Germany or Austria accepts unification
- Fixed Influence triggers for VOC focusses
- Fixed Dutch "Proclaim Fourth Reich" not being available when conditions are met
- Fixed Strength Ratio requierments in Dutch focusses
- Fixed Neur Market cancelling without any reason so the focus works as expected
- Fixed Dutch event ending up in Belgium. Old habbit
- Fixed Dutch Grey Society decisions not being able to take when decision got cancelled.
- Fixed change party function placing a salafist party in emerging
- Fixed change party function showing the wrong next ruling party
- Fixed the Iranian spirit "Firm Control" cancelling despite meeting the proper requirements
- Fixed the Iraqi army not disbanding in the instance of a defeat in the 2nd Gulf War
- Fixed the Iraqi provisional authority not transferring power from Jay Garner to Paul Bremer
### Content
- The idea "Fight With Communism" will now cancel if you become Emerging Outlook as either Lithuania, Latvia, Estonia, Finland or Poland
- Added the idea "Fight With Communism" to Lithuania, Latvia, Estonia and Finland
- Added a decision to allow anyone to join BRICS as long as India has formed BRICS
- Added Unit and Ship name lists for the Netherlands
- Changed starting focus for Dutch Fascist, needing them to be in power instead of starting a civil war
- Buffed the monthly population gain for Dutch Agriculture economy path
- Locked Dutch Groningen Branch in Regional Economy branch if you don't have oil searches
- Buffed nationalist drift when having Willem-Alexander in High-Command in the Netherlands
- Netherlands now start with lvl 3 agricultre tech
- Removed trasury cost for "Expand Tullip Exports"
- Add small stability bonusses in the Monarchist and Fascist branch in the Dutch focus tree.
- Added an option to relocate the capital to Nanjing for Taiwan in their event
### Database
- Added a new trait "Former Interior Minister" to Abdiqasim Salad Hassan for Somalia
- Changed the starting national leader of Somalia to Ali Mahdi Muhammad
- Added the traits "Career Politican" and "Writer" to the Indian leader "Atal Bihari Vajpayee"
- Changed some starting resources and buildings in the Netherlands
- Iraqi division templates associated with the Ba'athist regime will be disbanded upon defeat
### Game Rules
- Added a new game rule to disable the Muslim Brotherhood Civil Wars if you do not want them to happen
- Added allow achievements to several more game rules that do not impact the game flow fundamentally, but are just nice haves
### Graphics
- Fixed the Algerian character "Fatima Zohra Ardjoune" having the improper small portrait
- Added a small generic library of transport helicopters for the new unified equipment designer for each tier. More in-depth icon library will come in the future along with models
- Fixed Missing Personal Union Autonomy State GFX
- Fixed Dutch Missing Utility Research GFX
- Added MD Division icons for custom division icon
- New GFX for International Market menu
### Localization
- Added remaining sub unit modifier localization
- Fixed missing localisation for Dutch decisions and national spirits
- Fixed Historical Ship Name list missing loc
- Fixed Dutch focus "Smart Dairy Farming" missing localisation
- Fixed Dutch MIO trait missing localisation
### User Interface
- Fixed the special project window for different projects having bad overlap with longer descriptions
- Fixed the special project window for projects that have multiple options not being properly aligned and having a large amount of overlap
- Fixed the Economic Numbers overlap in the diplomacy window for people who do not own the La Resistance DLC


## v1.12.1a 8/15/25 Hotfix
### AI
  - Moved more add_ai_strategy to the ai_strategy file for better performances
  - Expanded the AI for Ukraine to be more reactionary to the Russian nation if they're justifying or have a wargoal against them
### Bugfix
- Fixed the Spanish decision "Canarios Targeted Subsidies" not properly checking for the right core for the Canary Islands
- Fixed the migration laws not properly being displayed in the tooltip for their cost
- Fixed the USA decision "Investments in Our Backyard" not properly triggering for Brazil, Colombia, and Argentina
- Fixed the American foreign event "Russia Agrees to Our initiative" giving money instead of taking it away
- Fixed 2025 stealth corvette being labelled as a regular corvette
- Fixed stealth corvettes and frigates not having names
- Fixed German MBDA MIO tree not being able to complete
- Fixed Dutch Damen MIO tree not being able to complete
- Fixed Dutch government fall event triggering when completed the purple election
- Fixed missing Dutch Characters
- Fixed Dutch Grey Society decisions being available when already having a decision active and will cancel when ruling party switched
- Fixed Dutch ideas not giving an effect.
- Fixed Dutch UN Mission to Ehiopia to work as intended
- Fixed Dutch monarchy events give western support instead of nationalist
- Fixed German duplicate state modifier for Mines
- Fixed ideas cancelling which doesn't made sense
- Fixed Dutch description when NATO is disabled for non-selfsufficient army spirit
- Fixed Arctec Focus tooltip for unlocking the MIO
- Fixed German MIO missing localisation
- Fixed Dutch focus giving money instead of taking
- Fixed Dutch focus not giving transport helicopter focus for NSB owners
- Fixed Dutch Defensievisie not being deleted when you complete the last focus
- Fixed missing localization for U.S. casaulty report event in Afghanistan
- Fixed an issue where the U.S. was unable to continue with OEF if the Taliban existed (this was a requirement for the previous iteration of the insurgency mechaniC)
- Fixed an issue where Iraq would capitulate even if it won
### Content
- Added a new opinion modifier when you send intervention forces to one nation, all hostile nations will gain a -50 opinion modifier with the root nation
- Added a new opinion modifier when you send intervention forces to one nation all of their allies will gain a +25 opinion modifier with the root nation
- Added random events for the Canary Islands similar to other Spanish regions
- Added a revolt against Spain mission for the Canary Islands if their opinion gets too low like the other Spanish regions
- Added tooltips for events and choices that inflect (un)locks for Germany and Netherlands
### Game Rules
- Added a new game rule to disable the CSTO
- Added a new game rule allowing you to change around your legacy doctrines
### Graphics
- Fixed various missing National Spirit GFX

  

## v1.12.1
### AI
- The AI will not pursue a debt war if a nation is guaranteed by a NATO member or CSTO member
- The AI will not pursue a debt war if the capital is in russia they need to have a state in either of the strategic regions bordering the Atlantic or Mediterranean (prevents them from fighting in wars)
- The AI will not pursue a debt war if they or an ally do not possess a naval base in the neighboring strategic regions
- The AI will be more likely to pursue a debt war if they have over 60% influence on the target nation
- The AI will not declare a debt war if they do not have naval superiority over the other nation
- The AI will be more likely to invade you for defaults on higher difficulty
- Further reduced the importance of Strategic Bombing for the AI so it stops being stupid
- Blocked the Greek AI from unifying Cyprus on historical focus mode
- Fixed the AI not properly checking things in the purchase Reactor Grade fuel event chain
- Enabled the AI to be able to use the International Systems GUI once again after refactoring it
- Fixed a part of the AI for the Libyan Special Project not referencing the correct variable
- The NATO AI should no longer have nations that join NATO on historical unless they are a historical nation that joins it
- PMR AI should now be more likely to take the focuses now to integrate Moldova so it's not as unstable long term now
### Balance
- Increased the penalties for taking the "Nuclear Power (Offensive)"
- Increased the cost of Enosis for the Greek decision from 50 to 150
- Increased the starting strength of the Islamic State and the Free Syrian Army when it spawns
- Slight change Panama Canal`s position
- Make Saint Kitts and Nevis at right position
- Increased the amount of oil added to the states in the USA decision "Open Public Lands for Fracking" from 2 to 6
- Increased the gain for the trade autonomy decision from -0.08 to -0.12
- Reduced the time to execute the USA decision "Execute Operation Enduring Freedom (OEF)" from 30 to 15 days
- Increased the cost of MBTs in the international market from 0.022 to 0.032
- Added a reliability penalty to the Double Barrel Tank Cannon and increased the soft and hard attack of the module so the cost is more worthwhile
- Added back a small anti-air bonus to the HMG modules
- African Literacy Rate now has a larger impact on the literacy rate of a nation for Africa
- Added a penalty to the literacy rate for countries with high corruption
### Bugfix
- Bulgarian & Serbian arms deal has been removed and replaced with a international market income modifier of 20%
- West Side Boys name change to be accurate name
- Fixed the Italian focus "Relinquish Power to the Pope" not properly transferring subjects to the Holy See
- Fixed being able to send yourself "Bailouts" if you have somehow become an influencer of yourself
- Fixed the Nigerian mission "Religious Civil War" not properly concluding when you have converted everything
- Fixed the Brazilian achievement "The New Communist South America" not properly triggering due to a mistake in the alignment check
- Fixed the Fijian AI Behavior not properly setting the global flag for either game rule
- Fixed the Somali Civil War global flags not being properly set for it's conclusion
- Fixed the USA decision "Open Public Lands for Fracking" adding oil to the wrong state
- Fixed the Sudanese Ribbon "End the Second Sudanese Civil War" not properly triggering due to a bug in what flag was triggered
- Fixed the combat tactics for random different combat tactics not properly being set
- Fixed Georges Leygues Class destroyer definition in OOB MTG (from "frigate" to "destroyer")
- Fix the Indian focus "Brazilian Industrial Partnership" not properly giving influence to Brazil
- Fixed German Focus Tighten Borders decreasing migration law instead of increasing it
- Fixed the country flag decisions not showing up properly as well as optimized their checks
- Fixed the APC/IFVs not properly being added to the division template after researching specific techs
- Fixed the Iraq decision "Aramco Control" not properly triggering when you have 90% to 99.98% control
- Fixed theLibyan focus "Islam Over Libya" not properly giving influence to a random country and sometimes giving influence to itself
- Fixed the Ethiopian focus "Eritrean Annexation" not properly removing the "Eritrean Friction" idea if you have it from the Eritrean integration efforts decisions
- Fixed the Ethiopian focus "Annex Eritrea" not properly adding the core of Eritrea to Ethiopia for the islands off of the coast of Eritrea
- Fixed the Indonesian focus "Purchase Rafale" not properly giving the Rafale M to Indonesia when the decision is taken
- Fixed the Indian on actions for religious group independence continuously spitting out the nations despite them being reconquered. They now can only declared independence once from India.
- Fixed an issue where Iraq would not win against the U.S. upon capturing the Kuwaiti naval base
- Fixed the Energy Game Rules causing a breaking issues when turning off power plants
- Fixed the Iraqi event "Anbar Tribal Council" tagging ad infinitum when ISIS has risen and the state 557 changes hands
- Fixed Israeli event "A proposal of sorts" not giving influence to the proper nations
- Fixed a weird bug where if you influence puppeted and then annexed a country, the country would gain Libyan tribal traits
- Fixed the UAR achievement "Are you sure that's enough?" not properly checking the GDP share
- Fixed the Libyan Ribbons not properly checking if you have beat Egypt and Chad
- Fixed a bug where "Has Power Ranking of at least Regional Power" did not include Regional Power.
- Fixed MTG naval OOB for France showing a destroyer class as frigate in "definition"
- Fixed German bugs in focus tree and events.
- Fixed German party stuff and balance
### Content
- NEW FOCUS TREE: Netherlands, Bolivia
- REWORKED/IMPROVED: Singapore
- Remove the 2017 start date and related files since we are no longer maintaining it
- Influence Economic Aid now no longer requires you to be a top 7 influencer and you can send aid to other countries
- Moved the political power costs for the Greek decisions from the effect to the cost trigger so they actually show their cost
- Reworked the Arab Spring mechanics to be more robust and enjoyable to play
- Reworked the "Cheap Loans from the IMF" decision to be more robust and require you to balance your budget without requiring you to pay down your debt
- All focuses that create factions now requires a nation to be independent before creating it so you do not have a situation that a puppet randomly creates a faction
- Refactored the Indian "Identities of India" mechanic to be more code standardized and easier to maintain as well as fixed a number of minor bugs with it
- Added a foreign policy decision category for the United States
- Added a mechanic regarding the Ba'athist on the loose following the Iraq invasion
- Reworked the Afghan-Taliban Insurgency mechanic
- Added country-specific flavor to Pakistan
- Added country-specific flavor to Palestine
- Added a decision & event to relocate your capital as Taiwan if you reclaim the mainland
- Improved effects on Taiwanese decisions
- Added scientists to Iran
- Reworked MIO for Germany
### Database
- Ukraine no longer starts with the "Naval Guns 2025" and "Cooled IR Systems" tech in 2000
- The French VAB now uses the wheeled suspension instead of the torsion bar suspension
- Converted the triggering of the "Death of Hafez al-Assad" event to be closer to the historical date when triggering the game rule
- Added the starting 2 camouflage technologies for Romania
- Removed radar station in Clabria and added one in Sicily and one in Puglia lvl.2
- Modified port and airport lvls to improve realism in Italy
- Updated naval OOB for Italy accordingly to map modifications and realism
### Game Rules
- Added two new custom game rules for Syria to allow you to force the historical civil war from the Arab Spring as well as the Islamic State spawn
- Converted the "Historical 9/11 Trigger" game rule to "Historical Events Trigger" to allow for more flexibility in the future
- Added a custom game rule to resolve "border gore" following a peace deal (with this option enabled, you will no longer have 40 Russia's if they lose)
### Graphics
- Fixed the engine type slot icons for the various tank chassis for custom nation blueprints
- Reworked the internal policies, laws, and statistics icons to be sleeker
- Fixed the helicopters showing up as tanks in the equipment designer for some nations
- Added a new icon for the "MLRS Battalioon"
- Added some 3d ships models for ITA, FRA and GER
- Fixed CV90 3d model clipping
### Localization
- Improved the localization for the Greek decision mechanic for Cyprus
- Added some QOL of tooltips and expanded localization for the various international system buttons
- Fixed the debt display not rounding when there is too many digits in the debt top bar
- Fixed the coalition tooltips not having their NOT flag
- Fixed the missing localization for the United Arab Republic achievements and tooltips
### Map
- Slight adjustment to the Riau Islands near Singapore/Indonesia
- Add Antigua and Barbuda to the game
- Make Panamal Canal its own state for future Panama Canal content
- Add a new state to Afghanistan called Qalat for the upcoming American Foreign Policy content
- Add Anjouan as a state
- Fixed Italian map building location, mainly ports and ariports
### Performance
- Reduced the amount of variables and flags that are saved into the save game file optimizing it
- Removed a number of scripted localization that were not referenced anywhere reducing some old and antiquated code bloat
### User Interface
- Added back the International Market Cost display for the international market window
- Refactored the Nuclear Strikes tooltips so they're easier to read and understand
- Removed floating "Armour_TITLE_WEAPONS" text from the tech tree
- Added several national focus filters to Iran and reassigned existing filters to improve playability.

  

