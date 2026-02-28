---
title: Beta Changelog
description: Changelog for the Beta Test Mod.
---

## Purpose of this Page

This page lists out all of the BETA test mod changes.

Achievements:

- [SOV] Added "Back in the U.S.S.R." achievement - reconquer all former Soviet territories
- [SOV] Added "From Russia With Nukes" achievement - become a superpower with 100+ nuclear weapons
- [RAJ] Added "Superpower by 2020" achievement - become a superpower before 2020
- [RAJ] Added "Tech Support Hotline" achievement - build 100 office parks
- [JAP] Added "Rising Sun Redux" achievement - have Korea, China, and Taiwan as subjects
- [JAP] Added "Nintendo World Domination" achievement - become the only superpower
- [NKO] Added "Kim's Dream" achievement - subjugate and annex South Korea
- [NKO] Added "The Missiles Actually Work!" achievement - become a superpower with 10+ nukes
- [KOR] Added "K-Pop World Domination" achievement - become a superpower
- [KOR] Added "Gangnam Style" achievement - reach 75k GDP per capita
- [TUR] Added "Neo-Ottoman Empire" achievement - control former Ottoman territories
- [TUR] Added "Kebab Removes YOU" achievement - defeat Serbia in a war
- [POL] Added "Poland Can Into Space!" achievement - become a superpower
- [POL] Added "Winged Hussars 2: Electric Boogaloo" achievement - own Moscow
- [MEX] Added "La Reconquista" achievement - reclaim Texas, California, New Mexico, Arizona
- [MEX] Added "Make Mexico Great Again" achievement - have higher GDP than USA
- [CAN] Added "Sorry, Eh?" achievement - become a superpower
- [CAN] Added "The North Remembers" achievement - own Alaska
- [AST] Added "Down Under on Top" achievement - become a great power or superpower
- [AST] Added "Emu War Veteran" achievement - have more than 50 divisions
- [GRE] Added "This Is Sparta!" achievement - capitulate Iran
- [GRE] Added "Alexander's Return" achievement - control Iran, Egypt, Afghanistan, Pakistan
- [PER] Added "Persian Empire Reborn" achievement - control historical Persian territories
- [PER] Added "The Nuclear Option" achievement - develop nuclear weapons
- [SWI] Added "Not So Neutral" achievement - be in a faction or at war
- [SWI] Added "Bank of the World" achievement - reach 150k GDP per capita
- [SWE] Added "IKEA World Domination" achievement - become a great power
- [NOR] Added "Oil Rich Viking" achievement - reach 100k GDP per capita
- [FIN] Added "Winter War Rematch" achievement - capitulate Russia
- [ITA] Added "Roman Empire 2.0" achievement - control France, Spain, Egypt, Tunisia, Libya
- [ENG] Added "Brexit Means Brexit" achievement - leave EU and become superpower
- [ENG] Added "The Sun Never Sets Again" achievement - reconquer former British Empire
- [ENG] Added "Rule Britannia" achievement - have 500+ ships
- [INS] Added "The Spice Must Flow" achievement - become a great power
- [INS] Added "Nusantara Rising" achievement - become a superpower
- [SAU] Added "Oil Tycoon" achievement - reach $1 trillion GDP
- [SAU] Added "Guardian of the Holy Cities" achievement - lead a 10+ member faction
- [VIN] Added "Charlie Don't Surf" achievement - capitulate USA
- [VIN] Added "Ho Chi Minh's Dream" achievement - have Cambodia and Laos as subjects
- [ARG] Added "Las Malvinas Son Argentinas" achievement - own Falkland Islands
- [ARG] Added "Don't Cry For Me, Argentina" achievement - become superpower
- [EGY] Added "Walk Like an Egyptian" achievement - become great power or superpower
- [EGY] Added "Pharaoh's Return" achievement - control ancient Egyptian territories
- [CUB] Added "Viva la Revolucion!" achievement - control Central America
- [CUB] Added "Cuban Missile Crisis 2.0" achievement - at war with USA while having nukes
- [VEN] Added "Bolivarian Revolution" achievement - control Colombia and Ecuador
- [VEN] Added "Maduro Survives" achievement - become great power after 2020
- [NIG] Added "Giant of Africa" achievement - become superpower
- [NIG] Added "Nollywood Global" achievement - great power with 50+ office parks
- [SAF] Added "Rainbow Nation Superpower" achievement - become superpower
- [SAF] Added "Mandela's Legacy" achievement - democratic great power
- [PAK] Added "Jinnah's Vision" achievement - become superpower
- [PAK] Added "Cricket Superpower" achievement - higher GDP than India
- [ISR] Added "Iron Dome Tested" achievement - become great power
- [ISR] Added "Greater Israel" achievement - control Lebanon, Syria, Sinai
- [SER] Added "Remove Kebab" achievement - capitulate Turkey
- [SER] Added "Serbia Strong" achievement - control former Yugoslavia
- [ROM] Added "Dracula's Domain" achievement - control Greater Romania
- [ROM] Added "Vlad's Revenge" achievement - capitulate Turkey
- [BLR] Added "Last Dictator of Europe" achievement - non-democratic great power
- [BLR] Added "Lukashenko Forever" achievement - keep Lukashenko until 2025
- [PHI] Added "Mabuhay!" achievement - become great power or superpower
- [PHI] Added "Archipelago Empire" achievement - have Indonesia as subject
- [SIA] Added "Land of Smiles" achievement - become great power
- [SIA] Added "Muay Thai Master" achievement - control Southeast Asian neighbors
- [DEN] Added "Viking Revenge" achievement - own Britain
- [DEN] Added "Kalmar Union Restored" achievement - control Kalmar territories
- [NZL] Added "Kiwis on Top" achievement - become great power
- [NZL] Added "Lord of the Rings IRL" achievement - have Australia as subject
- [KAZ] Added "Very Nice!" achievement - become great power
- [KAZ] Added "Greatest Country in the World" achievement - become superpower
- [ETH] Added "Lion of Judah" achievement - become superpower
- [ETH] Added "Never Colonized, Never Will Be" achievement - have Italy as subject
- [BAN] Added "Bengal Tiger" achievement - become great power
- [BAN] Added "Textile Empire" achievement - higher GDP than Pakistan

AI:

- [RAJ] Added AI behavior for handling Naxalite-Maoist insurgency (Issue #330)
- AI India now prioritizes insurgency suppression decisions
- AI escalates priority when multiple states reach Severe level
- AI unlocks Operation Green Hunt after 2009
- Moved more add_ai_strategy to the ai_strategy file for better performances
- AI USA should no longer send volunteers to Somalia outside of their civil war
- Fixed a broken AI strategy for Egypt which was incorrectly referencing LBA instead of EGY
- The Serbian AI should no longer suicide itself into other post-Yugoslavia nations
- Improved AI decision-making for Libyan tribal mechanics to prevent civil wars (Issue #153)
- [LBA] Improved AI handling of Gaddafi family stability mechanics (Issue #231)
- AI now proactively uses TV speech and lawsuit decisions based on family instability level
- Reduced family instability decay rate from -0.25 to -0.20 per family member
- This prevents the Gaddafi civil war from triggering earlier than expected
- AI oil development decisions now use balanced thresholds (45%/25% vs previous 70%/40%)
- AI tribal placate decisions now use escalating urgency weights with cross-referencing
- AI now avoids placating one tribe if it would endanger others (prevents creating new crises)
- AI prioritizes the "Decentralize State" decision when multiple tribes are struggling
- The AI should no longer immediately accept a propose trade agreement or mutual investment treaty if you just cancel
- San Marino's AI should be a bit more intelligent in handling their economic content so they don't bankrupt as quickly or as often
- Fixed AI investment logic stacking all factories in single best region (Issue #114)
- Added strong penalties per existing building (25x multiplier) to spread investments across states
- Added pending project penalties (40x multiplier) to prevent spam-investing same region
- Added randomization to state selection to break ties between similar states
- POL AI should no longer be able to start Visegrad branch on historical focuses
- The Indonesian AI should now be more likely on historical to release Timor Leste
- Fixed AI USA abandoning the guarantee of Taiwan in the early game
- Removed all old naval AI, and adjusted it to work in the new Goals / Objectives system
- Added a large volume of new ship designs, provided to us, to improve AI ship designs
- Minor nations should no longer assume faction leadership from majors (can't defend it so don't be the leader)
- AI should now considered whether they're either economically or militarily stronger then the faction leader before trying to assume faction leadership
- Conditional peace deals has been improved to be more robust and less cheesy
- Difficulty of the game will now play a factor in the AI calculation
- SCO, Axis of Resistance now give a negative value for the major faction
- The USA should no longer deploy the the Enhanced Forward Brigade and the S Brigade to Turkey well before the Russians have caused any tension
- The USA should be more likely to guarantee South Korea assuming they are democratic
- If the GFC has reached the USA the European Union AI will start working more actively towards economic reforms to better support all EU member states
- Added designed naval taskforce AI. This should get the AI to design better task forces, and deploy them in ways that make more sense, and avoid deathstacking
- Added new naval AI strategies for the AI, based around establishing naval dominance and performing more convoy raiding
- Adjust microchip production strategies
- Encouraged the AI to be more likely to build fuel silos to increase their fuel storage
- Hid the European Union from the AI who are not likely to ever interact with it helping some of the tick rate/speed
- The AI for the European Union GUI should now only check the menu every 3 days to help prioritize performance
- If the AI is currently in a deficit and/or on the verge of economic collapse they will slow their combating of influence to save their political power for other actions
- Fixed the Canadian focus "New North American Oil Treaty" not working as expected and not properly adding the ideas that needed to be added
- Investor AI should now be more likely to invest in renewables if it were to help you reduce your independence from foreign oil
- Cleaned up redundant and not useful AI strategies that were never able to be achieved in the first place
- Integrated the AI Attache mod for AI interacting with the AI Attaché's
- Credit: AI Rework: Attaché's https://steamcommunity.com/sharedfiles/filedetails/?id=3164040395

Balance:

- [RAJ] Complete rework of Naxalite-Maoist insurgency system (Issue #330)
- Renamed all "hoxaists" references to historically accurate "naxalite" terminology
- Rebalanced initial state severities for 2000 start (pre-PWG-MCC merger period)
- Reduced modifier penalties: Severe now -35% recruitable/-40% resources (was -50%/-60%)
- Removed insurgency from non-historical states (Karnataka, Uttaranchal, Gorkhaland)
- Core states (Chhattisgarh, Jharkhand, Telangana) now start at Moderate instead of Severe
- Converted MTTH-based events to on_monthly_RAJ triggers for better performance
- Adjusted some ideas in Germany which was giving a pointless < 0.01 democratic drift causing no actual impact or change
- Reduced the penalties from the starting spirit "American Militarism"
- Fixed an influence exploit by proposing, the AI accepting, then canceling the trade agreement giving you near infinite influence
- Fixed F-35 program still requiring NATO/MNNA status when opened to the world (Issue #286)
- Fixed coalition party removal exploit that allowed gaining infinite political power by spamming remove decisions (Issue #285)
- Significantly reduced the "The Green Card Program" productivity growth factor from 50% to 15%
- North korea Land Facility Was Swapped for a Nuclear facility
- North Korea Capital got level 2 now infrastructure
- Added New Mastery All Across the Focus tree related to their appropriate type for North Korea
- Added MIO Benefits for North Korea
- Added a Starting Nuclear Reactor for North korea without any entrenchment facility
- Added Entrenchment facility in the Focuses for North Korea to Balance out some stuff and help players Have Easier Start
- Updated Restore Pleven Focus to give bonuses for Bulgarian fuel
- Increased the time it takes to complete to do the "Nuclear Warhead Program" special project
- Increased the income from "Sell Political Positions" internal faction decisions
- Reduced the political power loss from the Communist Cadres "The Communist Cadres Requests Governmental Concessions"
- Added basic SAM technology (SAM and SAM0) to 34 countries that had SAM systems by 2000 with systems introduced no later than 1965:
  Albania, Algeria, Armenia, Austria, Azerbaijan, Belarus, Belgium, Bulgaria, Cuba, Czech Republic, Denmark, Estonia,
  Finland, Georgia, Greece, Hungary, Iraq, Kazakhstan, Latvia, Lithuania, Malaysia, Moldova, Netherlands, Norway,
  Romania, Serbia, Slovakia, Syria, Switzerland, Thailand, Turkmenistan, Uzbekistan, Vietnam, South Africa
- Added pre-existing intelligence agency upgrades for major powers reflecting their Y2K capabilities (Issue #120):
  USA (CIA/NSA): World-leading cryptography and decryption, strong military intelligence, operative training
  UK (MI6/GCHQ): Excellent cryptography, good HUMINT and military intelligence
  Russia (FSB/SVR): Strong counter-intelligence and HUMINT (inherited KGB), commando training
  Israel (Mossad/Unit 8200): Strong HUMINT and covert operations, good cryptography
  France (DGSE/DST): World-leading economic intelligence, good counter-intelligence
  China (MSS): Developing agency with focus on counter-intelligence and economic espionage
- Nerfed the amount of economic bonuses you could get as Iran
- Extended the time you have the "Recently Joined the WTO" idea for China
- Increased the trade opinion, political power gain and gave a little bit of emerging drift to the SCO member ideas
- Increased the Oil gained from the South China Sea decisions so they're more worth their cost
- Increased the naval max range factor from the support ships
- Added "International Aid" national spirit for Kosovo providing weekly income from UNMIK, USAID, and EU aid programs (Issue #230)
- Rebalanced nearly all military technology to have more modernized tech rely on Microchips and Composites, rather than Tech/Precious Metals
- Adjust piercing stats on doctrines to be make them more reasonable
- Stat changes to several subunits, to lead to more balanced combat and allow players more options for division design
- Adjusted IC cost of electrical infrastructure and industrial complexes
- Slightly reduced the lower bound and increased upper bound of political power to -300 and 2500 respectively
- Increased the political power cost for putting supportive scientists in place to 50 from 25
- Reduced the likelihood of generals dying in combat significantly
- Significantly buffed naval dominance across all ship hulls. It should be far easier to obtain naval dominance with smaller fleets now, and as a bonus, they AI should play smarter now
- Gave the "Rubber Baron of Africa" idea for the Ivory Coast additional rubber generation
- Provided additional Militias to the Syrian side of the conflict in the Arab Spring Civil War to slow the conflict
- Gave the Civil War debuff to the Arab Spring Civil War to help slow the conflict
- Increased MIO fund size requirement from 500 to 800 and increased the factor from 50 to 75 to make it slower (this is also to pair with the QOL implementation of Vanilla's update automagically)
- Increased the build time of infrastructure to make it harder to get to level 5
- Adjusted application of stats from naval modules. Majority of stats will now come off add_average, with lower amounts coming off add
  NOTE: This will result in ships needing to upgrade weapons generationally for the best effects, while also allowing single module upgrades to still have a decent effect
- Tweaked naval combat defines further for balance (Bird is a nerd for making me do this, <3 bird!)
- Adjusted naval engines. Turbine engines now have the highest fuel consumption, while Diesel engines consume a lesser amount, to better balance the engine choices.
- Turbine engines speed buffed to match nuclear engines; nuclear engines biggest advantage is now range and fuel consumption
- Reduced the cost of internal investments so they're more likely to be taken
- Increased the research costs for missiles across the board and satellites
- Economic cycle productivity modifiers change from -3/+3 to -4/+3.5
- Rentier State modifier now gives -1.5 productivity nerf to reflect how oil-based economies struggle to invest in other sectors
- Each renewable tech now multiplies power output by 130% instead of adding 30%, boosting power output into the late game
- Africa literacy rate debuffs strengthened (productivity 4x, education costs 2x), so AI needs more time to develop
- African Union reforms strengthened to offset the literacy debuffs, allowing player to still achieve rapid development of African nations
- Technology productivity bonuses reduced by 50%, AI and late-game computing tech bonuses massively buffed
- Reduced Microchip production per-building from 24 to 20
- Reduced Microchip production gain per-building off techs from 2 to 1
- Added per-level construction cost increase to microchips (+2500 per level)
- You can no longer take more debt than you have GDP fixing debt exploits where you have low GDP and could take 100b in debt despite having less than that in GDP
- The Military Internal Faction now provides a reduction to required tension for generating a wargoal by up -25% at 100 opinion
- Reduced the cost of convoys by 400 IC from 1500 IC
- CUB AI should no longer try bakrupting itself via focus tree
- Reduced the base cost of railways to 3750 per additional level instead of 5000
- Softened the workforce modifiers curve when exceeding 100k GDP/c debuff to total workforce to -50% at 200k GDP/c instead of -85% at 100k GDP/c
- TOS-1 for Russia is now a 2nd Generation Rocket Hull to match being built off of the t72 hull
- Removed the equipment capture from specific land subunits and put them at the global level so no more 10000000000% equipment capture rate per division

Bugfix:

- Fixed influence monthly exploit - auto-influence now applies cooldown on activation to prevent abuse of late-month toggle (Issue #378)
- Fixed investment exploit allowing players to bypass treasury checks while game is paused by adding runtime validation (Issue #374)
- [JAP] Fixed missing interface files for Japan in the Tank Designer - created new \_jap.gui files for all tank chassis types using USA layout (Issue #349)
- Fixed ship experience gain modifiers not showing ship type in tooltips (Issue #354)
- All naval unit experience modifiers now display their ship type (e.g., "Destroyer Training Experience Gain")
- Added missing submarine training/combat experience gain modifiers
- Affected ships: submarines, carriers, cruisers, destroyers, frigates, corvettes, battleships, etc.
- Fixed broken variant upgrade for Artillery 2005 by renaming non-NSB artillery technologies to avoid name collision with equipment (Issue #334)
- [BLR] Fixed factory locations in Belarus focuses - factories now build in correct provinces (Issue #236):
- Pinskdrev now builds civilian factory in Brest oblast (was random)
- Hi-Tech Park now builds office in Minsk (was random)
- Delta City Business Center now builds office in Minsk (was random)
- Minsk Tractor Plant now builds civilian factory in Minsk (was random)
- 558 Aircraft Repair Plant now builds military factory in Brest oblast (was civilian in random location)
- Peleng now builds civilian factory in Minsk (was random)
- Minotor-Service now builds military factory in Minsk (was random)
- [BLR] Removed spurious fossil fuel powerplants from 12 Belarus focuses that incorrectly added powerplants alongside factories
- [BLR] Restored missing civilian factory to BASF Societas Europaea focus
- [BLR] Added missing description for Peleng focus
- Added missing intelligence agency advisors for spymaster role (Issue #110)
- Fixed SAM missile icons not matching their equipment variants in deployment UI (Issue #218)
- Fixed Linux runtime crashes caused by parsing errors (Issue #176)
- Fixed configurable display showing 0 for all resources and added microchips/composites support (Issue #288)
- Net resource calculation now properly uses produced + imported - exported - consumed
- Added microchips and advanced composites as new resource options in the topbar counter
- [ARM] Fixed Active Diplomacy focus auto-bypassing when in any faction instead of only when faction leader (Issue #203)
- [ARM] Fixed Embrace Left-Wing Origins focus not adding labour_unions if Bosses Elimination was completed first (Issue #203)
- Renamed "special forces" subdoctrine directory to "special_forces" to fix Linux path parsing
- Fixed NATO faction being disbanded when USA (or any faction leader) leaves NATO - leadership now transfers to another member (Issue #94)
- Fixed investment system allowing AI to offer investments for buildings when pending projects would already max out capacity (Issue #99)
- Fixed the Strv 121 tank model showing invisible due to missing entity definition (Issue #139)
- Fixed Big Ben and other landmark buildings not displaying due to missing GFX sprite definitions (Issue #140)
- Fixed the Chechen event "Chechnya Offers Us a Cooperation Agreement" only having position opinion options
- Fixed the Libyan decision "Dig for Iron Ore in Wadi Ash-Shati"
- Completely refactored Afghanistan Almond/Pomegranate investment mechanics to fix infinite money exploit (Issue #156)
- Changed returns from population-based (exploitable) to GDP-based (balanced 20% profit margin)
- Added investment limit of 5 uses per type to prevent spam-clicking
- Increased cooldowns from 21/40 days to 90 days
- Increased investment duration from 1/7 days to 30 days
- Fixed the color of Zimbabwe being broken due to an extra space inbetween the numbers for its color selection
- Fixed the Cuban leader Alvaro Lopez Miera spawning without a portrait
- Fixed the gap in the Swedish division template "Infanteriregement"
- Fixed the broken Railway effects from the event Belgium Declines/Accepts HSL Zuid Collaboration event
- Fixed some Somali portraits sometimes not being added correctly
- Fixed the broken doctrines not showing up for rangers or airborne
- Fixed Monaco not being able to see the European Union decision screens
- Fixed Czechia land army icons and Starostve party icon
- Fixed the Quick Selection count being broken
- Fixes For North Korea Not able to Trade at game start
- Fixes for North Korea Side of the Unification not being able to Unify Ever
- Disabled North Korea from Retiring Leader to Avoid breaking the Focuses and blocking you from Choosing one of the Kim brothers
- Removed a spamming error in the error log regarding the "Israeli Settlements" idea which no longer exists
- Fixed an Ecuadorian politician not correctly being parsed due to a missed placed comment
- [PER] Fixed Kermanshah's Oxygen mission checking wrong province (12773 instead of city province 16155) (Issue #234)
- Fixed the Zusana design not being correctly parsed on game start
- Fixed a spamming error regarding the MNF when they're not quite existing yet
- Fixed the Swedish Division Name List "Amfiberegemente" being available to all countries
- Fixed the Swedish event "A New Mandate, A Military Path" incorrectly spawning a unit causing an error in the error log
- Fixed the edge case with Chinese and Russian influence when trying to join the European Union
- Fixed Chinese Aggression being clamped to 0 when sending a military access agreement
- Added another failsafe for the weird edge cases where the Zombies just stopped attacking (damn mechanics)
- Fixed Tajikistan changing their flag under the Rahmon regime to an alternate flag
- Fixed Panavia MIO selection for medium aircraft so it can actually be used with the Tornado
- Fixed the missing Air Force Academy spirit icons
- Fixed duplicates in .yml localization files
- Pakistani Taliban is now correctly setup when they are spawned
- Foreign SAM Missiles Can Now Be Deployed
- Fixed Bulgaria being double charged for Renewable Energy in several fixes
- Fixed a gap where the Eritrea Transitional Government could negotiate operative release when they should be blocked
- Bulgarian focus Jorjy's KGB faction fixes
- Fixed the tax cost modifier missing from the Iranian Economy Spirit
- [PER] Fixed Kermanshah's Oxygen mission checking wrong province (12773 instead of city province 16155) (Issue #234)
- [PER] Fixed "General Max Army Size" modifier from Concessions to the Army focus not working (Issue #235)
- [PER] Added distinct color to Axis of Resistance faction to differentiate from CSTO on F10 map mode (Issue #342)
- Removed the double definition of support in Motorized Recon Company
- Fixed Dutch Focus "Modernize MRAD" not being available while having the tech that was needed. Also added a bypass when all you states are maxed out on Anti-Air
- Fixed an issue where an internal faction check in various nations (most noticeable in China) would allow you to take a decision or focus despite it not having enough opinion
- Fixed a number of idea not properly applying their bonus properly for attack helicopter equipments
- Fixed Errors for Non-AAT owners trying to complete MIO traits.
- Fixed 'Increasing Military Capabilities' Venezualan National Spirit to be canceled when completing the focus giving it
- Fixed Headquarters units to now provide buffs to proper divisions of their type
- Fixed an issue with the Chinese history file causing them to have duplicates of all of their variants and equipment stockpile additions
- Fixed several dozens instances of where you would end up with multiple definitions of transport helicopters causing duplicates in the tech building menu
- Fixed the Spanish focus "Our Celtic Brothers" being impossible to take due to the parent focuses being mutually exclusive
- Fixed a rare issue where a common effect would show that Corruption Level 2 would be replaced with Level 4 but you had Level 3
- Fixed the United States, China and Russia strategic bombers not being able to be used in nuclear raids due to the missing starting nuclear consent module
- Fixed an improper check in the on actions when declaring war to properly setup the Iraq War
- Fixed several events in Singapore not being localized or functioning as correct due to typoes in the variant names
- Fixed being able to do the Internal Investments for Local Conservation Efforts in any state as Brazil even though it should've been limited to the Amazon states
- Fixed the ability of Israel to influence nations that are being boycotting them fully or politically
- [HOL/LIC] Fixed missing portrait texture errors (Issue #333)
- HOL: Fixed case mismatch in Wim Kok portrait reference (wim_kok.dds → Wim_Kok.dds)
- [PER/SER/BOL] Fixed create_unit parsing errors (Issue #331)
- Iran decisions: Added missing space in division template strings
- Serbia/Bolivia focuses: Changed invalid start_experience_base to start_experience_factor
- [BUL] Fixed border training event having no valid options during civil wars (Issue #332)
- Changed event option triggers from tag to original_tag to match decision's allowed block
- Fixed broken upgrades for transport helicopters that are not designable (bba and non-BBA)
- Fixed the Bolivian decisions for exploring oil reserves being repeatable when they shouldn't be
- Fixed a bug where you were getting more popularity for the cartels from doing decisions then you should've been screwing over most cartel nations party popularity
- Fixed the war weariness not properly giving the penalties as expected and not properly cleaning itself up after the end of the war
- The German Green parties now should correctly be able to be taken if Greens are in coalition or in power
- Fixed a German focus requiring an absurd number of divisions to complete the focus
- Fixed an auto influence issue where an nation will stay in an auto influencer array causing you to spend political power on nations that do not exist
- Fixed the Republic of Africa stealing subjects when it's forming
- Fixed the poorly written tooltip for the Israeli decisions about having troops in the West Bank
- Fixed several events giving the "EF-2000 Typhoon" now will correctly give the "Typhoon Tranche 1" for Denmark, Turkey, and the Gulf States
- Fixed Libyan traits from the Gaddafi Family mechanics not properly removed and added for various traits
- Fixed various issues with San Marino in the national focus and decisions
- Fixed the dozer, dozer, dozer, dozer tanks where you could simply turtle your way to victory by building a glorified tank dozer blade. Bob the builder would be proud of you for this.
- Fixed Wrong Tech Bonus names. Now they show where the bonusses have been earned
- Fixed German Modernise Equipment decision not giving random rewards
- Fixed a Belarusian focus being hidden behind the "Church Reforms" focus
- Fixed a Lichtenstein bug where you would get scammed out of 3.5 billion
- Fixed Iraqi civil war tags not being properly setup on release
- Iraq can no longer vote to join the invasion against itself in the post 9/11 content
- Fixed a display issue with the Arab Spring not showing you the government popularity impact on the growth of the Arab Spring
- Fixed a screwed up trigger for the "Prominence in Flanders" decisions for the Dutch mechanic not properly switching to toggled
- Fixed a Libyan unit parsing error where they are not correctly referencing a division template that it should be
- Fixed an overflow bug with workers at very high GDP/c causing your economy to constantly be in flux (thank you wandoubill)
- Added a minimum clamp of 0.00001 to workers to prevent extreme casing where you could end up with negative people employed (even your baby was employed!)
- Fixed an issue where Serbia was trying to double non-aggression pact causing errors in the log
- Fixed an issue where Jerusalem Light Rail and Tel Aviv applied to the incorrect states
- Fixed a bug with a Russian event not properly referencing the equipment for the TOS-1 causing it not to be added when the event is selected
- Fixed the AT guns being unable to be placed on airplanes in the designer variants
- Removed older bankrupcy idea that did not match the current bankruptcy system causing discrepancies in the economic system
- Fixed the Tajik faction bug where if you say no you join the faction anyways
- Fixed SWE infantry template having incorrect layout
- Fixed an issue where SHORAD sites were never actually being properly factored into your Military Spending
- Fixed an issue with Iranian Aid not properly giving you income as it should for the second tier of the idea

Content:

- [RAJ] Added new Naxalite-Maoist insurgency mechanics (Issue #330)
- New focus: Counter-Insurgency Operations in military branch
- New decisions: Integrated Development Initiative, Surrender & Rehabilitation Program
- New decisions: Operation Green Hunt (unlocks after 2009), SAMADHAN Doctrine (unlocks after 2017)
- New decisions: Salwa Judum (2005-2011), Red Corridor Road Connectivity
- 9 new events: PWG-MCC Merger, Major Maoist Attack, Mass Surrender, Leadership Elimination,
  Tribal Displacement Protests, Operation Green Hunt Success, Naxal-Free Milestone,
  Dantewada Ambush (2010), Sukma Attack (2017)
- 5 new national ideas: Red Corridor Crisis, Operation Green Hunt Active, SAMADHAN Doctrine,
  Naxal-Free India, Salwa Judum Active
- [NIG] Added Niger Delta Revolt content (Issue #381)
- New focus branch: Military Solution / Address Niger Delta / Negotiate Peace paths
- New focuses: NDDC Reform, Amnesty Program, Oil Revenue Sharing, Niger Delta Resolved
- New decisions: Joint Task Force Operations, Negotiate with Militants, Implement Amnesty,
  Oil Revenue Sharing Agreement, Environmental Cleanup, Request International Mediation
- 20+ new events: MEND Formation (2006), Oil Platform Attacks, Foreign Worker Kidnappings,
  Pipeline Sabotage, International Pressure, Presidential Amnesty Program (2009),
  Militants Surrender, Amnesty Failure, Niger Delta Avengers Emergence (2015-16),
  State of Emergency, Crisis Resolution
- 10 new national ideas: Niger Delta Crisis (3 tiers), Amnesty Program, Failed Amnesty,
  Niger Delta Avengers, NDDC Reformed, Oil Revenue Sharing, Joint Task Force, Crisis Resolved
- Historical accuracy: 33% oil reduction during peak conflict, 2009 amnesty mechanics
- [SOV] Added decision for Russia to transform CSTO into offensive alliance (Issue #269)
- Allows Russia to call CSTO members (including puppets) into offensive wars
- New decision category "CSTO Management" for Russia when leading CSTO
- News event notifies all countries of the alliance restructuring
- [GENERIC] Renamed North American formable from "United States of North America" to "North American Federation" (Issue #268)
- [BUL] Enhanced "Embracing Orthodoxy" focus to add Anti-LGBTQ Stance national spirit (Issue #284)
- [BUL] Added nationalist drift bonus to Orthodox National Values national spirit
- [BUL] Added Dobruja (state 284) to The Fourth Bulgarian Kingdom integration decisions
- The Generic focus "Military Education Reform" now gives a +1 skill level to all generals while also increasing your education law for unit leaders
- The Generic tree will now actually give doctrinal benefits and are now updated to the newest system for doctrines
- The Vatican can join the European Union as a nation with no elections (only circumstance for this)
- Added the ability to to "Energy Load Share" with a select nation
- Note: If you are receiving energy load sharing you will only be able to have one nation sharing to you for now (is subject to change prior to full release)
- New Content for North Korea and Balances Related with the New DLC
- New Even for North Korea Related to Submarine Engines
- Added a new raid for the United States to capture Nicolás Maduro
- Created unique replacement ideas for each country and updated all 4 focus references (USA_chrisitian_influence)
- Introduced priority to the Chinese decisions so custom content is closer to the top of the decisions panel
- Introduced priority to the GCC decisions and other unique and custom mechanics
- Added "Understrength" battalions, to allow more flexibility with division design, and to enable unified designer to work properly
- Added Synthetic Refineries as buildable buildings
- Added Microchips and Composites as produceable resources.
- Added Microchip Plants, Composite Plants, and additional technologies and special projects related to their construction and usage
- Raid wargoals are now no longer permanent, they will be available for 120 days so you can't cheese getting a free wargoal
- The USA in the 9 Dash Line content will no longer get a permanent wargoal against China if they choose to go to war and hang onto it.
- Refactored the Global Financial Crisis and added additional content to the War on Terror
- [SIA/CBD] Added Cambodian-Thai Border Conflict mechanics (2008-2011 Preah Vihear crisis)
- New decision category: Preah Vihear Border Dispute for Thailand and Cambodia
- Thailand can escalate tensions and launch border incursions
- Cambodia can protest, counter-attack, and appeal to the ICJ
- ASEAN mediation path available for both nations
- ICJ ruling mechanics with accept/reject options
- Border clash system using HOI4's border war mechanics
- Multiple resolution paths: diplomatic, military, or international court
- Added additional economic events to the United States
- Added 2 new internal investments options in "Local Coastal Infrastructure" and "Local Fortification Efforts"
- Add Civilian Population & Offices consumption of microchips
- Added designer hints to all naval modules, to assist with naval ship design.
- Added dynamic resource pricing for exported resources. Resource value will now change based on the available resources exported for trade.
- Comprehensive improvements to the Georgian tree and new decisions and events to improve the experience
- Added more technologies base around microchip production, to allow nations multiple options to increasing their production of chips
- Added "The Great Chip Race" mechanic to Taiwan, allowing them to try and scale their microchips production against the growth of China
- Added "The Great Chip Empire" to Taiwan, giving them advantages in microchip production.
- Added "Taiwan Semiconductor Manufacturing Company Ltd" as an MIO, giving Taiwan bonuses to their chip production and research for microchip aspects
- Added a resource storage system for stockpiling resources with the "Strategic Resource Reserves"
- Added a "Close Embassy" and "Reopen Embassy" diplomatic action
- Added the "2014 Aswan Tribal Conflict" to Egypt
- Russia's "Annexation of Crimea" is made more flexible so as to increase the options available to the Russian player
- Power Ranking system now is calculated 2 times a year (May and November) for performance-oriented purposes
- Extended the Generic tree for more economic and military options

Database:

- Land drone technologies now properly give the Ranger Light Recce company recon bonuses like all other recon units
- Added 160 Scud GLCMs to Ukraine
- China now starts with the "Microprocessor" tech
- Adjusted productivity for nations to be more accurate to the development of regions and GDP as a percentage of their national GDP

Factions:

- Added a new faction goal "Establish an Airborne Corps"
- CSTO should now accurately be blocked to just the joining of Post-Soviet States
- Fixed the faction goal "Establish a Marine Corps" requiring a unit type that simply does not exist
- Fixed the faction goal "Crush Democracy" being available to everyone including democracies
- CSTO faction goal "Secure Central Asia" can now be completed when they are subjects themselves

Graphics:

- Fixed a handful of missing texticons for various unit definitions such as Stealth Corvettes, Stealth Destroyers, Stealth Frigates and more unit types
- Fixed the missing models for the Repair Ships and Support Ships
- Fixed a missing text icon for the CV MR Fighter, CV Light Strike Fighter when looking at unit types
- Added new diplomatic request icons for "Propose Subsidies to Subject", "Propose/Request Energy Load Sharing", "Negotiate Operative Release", "Enforce Peace"
- Integrated 81_evan's Iraqi flag submod to improve the flag selection for Iraq
- Fixed the missing icon for the "Chinese Electric Car" ideas
- Fixed a broken text icon for the La Resistance Espionage system not showing the mission icons
- Fixed a broken text icon for the "Spotting" modifier which would spam quite a few times
- Fixed a portrait error for Cuba's "Alvaro Lopez Miera" when promoting them to an advisor
- Fixed a portrait error for Izzat Ibrahim al-Douri when creating the country leader
- Fixed Erna Solberg sometimes being a man instead of her expected portrait
- Adjusted the F4 models so that they aren't the same size as aircraft carriers
- Integrated the colored railways for the supply map mode so they're easier to discern the railways
- Credits to jumpropeTravesty1974 for their mod that we integrated.
- Added additional portraits for generic scientists and otherwise

Game Rules:

- Added a new game rule for Enabling/Disabling Energy Load Sharing system
- Added a new game rule for the price per GW for the Energy Load Sharing system
- The Game Rule annex microstates for the Oceania tags will now annex into Fiji so you can play w/ the tree (yes I know this is a buff to them)
- Fixed the Game Rule for disabling "Domestic Independence" not working as expected

Localization:

- Adjusted some of the wording in the Serbia joins the United Nation event so it doesn't say Yugoslavia when Serbia still exists
- Fixed all 148 missing or placeholder descriptions in the Georgian focus tree (Issue #149)
- Previously fixed 58 empty/placeholder descriptions
- Added 90 completely missing descriptions for focuses that had no \_desc entries
- Fixed the tooltips for the Bulgarian Energy Companies focuses showing that they are giving a debuff when they're giving a bonus
- Introduced more flavorful text for the satellite access diplomatic actions
- Removed the weird gap in additional income or additional expenses that came from the market contracts
- Fixed a number of missing additional income and additional expenses that were missing from the tooltips so you can actually see those bonuses

Map:

- HMNB Clyde is now properly represented with a Level 8 Naval Base + Naval Headquarters for the UK's Nuclear Submarines deployment
- Updated the tech metals available on game start for Armenia from 7 to 20
- Regroup Jubaland into a several states and provinces to support new Somali content
- Added a new state for Guadalcanal, Timor Leste and renamed Timor Leste to Loro Munu in support of the Timor Leste Crisis content

Map Modes:

- Reworked the coloring of the SCO map modes to have distinct colors for each type (observers purple, possible non-member or observers are yellow) for easier view
- Removed junk map modes that were lingering in the files and not adding anything

Performance:

- Converted more add AI strategy to save performance in the long term and reduce the save games
- Optimized some early European Union initialization to be more performant in the early game when loading histories
- Refactored the power ranking system so it's 33% faster on the weekly ticks to improve tick speed
- Improved the weekly tick by reordering/shifting content around and reducing the check count to better optimize the mod
- Moved the European Union's checking of EU breach of values to monthly
- Moved a check for the social conservatism and optimized a check for the Gulf Countries
- Moved some more checks for the counter terror to monthly for more performance
- Refactored a number of history files so they reduce their number of "Has DLC Checks" on loadup for more performant load times
- Made the Space System update on response only rather then every week since nothing happens on every week
- Shifted the renewable energy calculation to the monthly tick for better performance
- Shifted the Ideological Power subsystem to on demand updates rather than weekly checks and a fallback for monthly
- Removed the final batch of Mean Time to Happen legacy events to optimize the game better during runtime
- Removed logging that was not useful to reduce the amount of information being rendered and output to the game
- Removed and reduced significant numbers of any_country/every_country calls in the mod in various places
- Moved all productivity state variables into the history/states so as to not do additional scope expansion
- Removed logs for unneeded functions such as news events, technologies, and other redundant logging
- Removed redundant sort influence and applied the error correction at the beginning prior to sort
- Improved optimization of custom guis by adding dirty vars to ensure they're not constantly refreshing
- Reduced a significant number of weekly/monthly math and replaced with more performant streamlined math to allow for faster ticks
- Replaced inline every_country, random_country with more performance freidnly alternatives where applicable
- Simplified scripted localization calls in the background to support faster running tick rates
- Refactored the map mode colorization math to improve the speed at which they're rendered for users
- Disabled the calculation for workers if you don't have a building (displays are still calculated). Crazy how if you have no workers you don't need to calculate 0.
- Adjusted math for productivity modifiers to calculate as they need to rather than every tick
- Converted country group triggers to script constant checks for better performance
- Converted more work for the African Union to be more performance friendly and reduce the majority of the calls to be more optimized
- Further optimized the AI strategies to stablilize the ticks and reducing redundant AI strategies
- Disabled more AI strategies for non-important nations for market access and otherwise
- Removed some dynamic modifiers from being present on game start if they are not needed

Quality of Life:

- You can now push your Election Threshold to 0% instead of the minimum 1% in the Subideology screen
- Disabled the XP cost for assigning MIOs to design team so you can use the update automatically button
- Added a political decision to block only foreign election notifications so you don't need to block all news events
- Added shortcuts to MD specific menus in various menus to be more accessible
- Added a startup event to help direct and support new players (simple for now will likely be redone into a proper helper)
- Added a container as part of the topbar to show a percentage of energy unfufillment for quick visibility into your Energy situation

Sound:

- Ensured that voicelines for various nations are saved in the proper format as to prevent nonsense errors in the logs

User Interface:

- Fixed the doctrine's text being unreadable due to a black font on a black interface
- Fixed the Faction Goal popup being off center and weird in the UI
- Modernized the trade GUI to MD's stylization
- Reduced precision in several menus so you do not see 5 decimal points in areas where it does not matter
