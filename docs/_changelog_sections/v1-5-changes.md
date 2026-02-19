---
layout: default
title: "v1.5 Changes"
page_id: changelog-v1-5-changes
toc: "off"
order: 6
---

# v1.5 Changes

<details><summary>v1.5.1 Hotfix</summary>

AI

- Improved AI Strategies and on_actions to fire less
- More improved AI logic for upgrading fleet design
- Greece shouldn't leave NATO now
- Added new Game rule for Potato PCs -- Expanded on the AI division limiter to be more limiting for PCs
- Expanded AI rules for investments to make it more likely to occur
- Tinkered with Debt AI to be more likely to take debt during war
- Iran should now historically send volunteers later on in 2018
- Improvements to Italian AI
- Expanded AI strategies
- Improved AI for moving up and down trade laws
- More AI management of money
- Improved AI unit production of ships
- AI should now use dynamic brigade/division templates. Whos ready for Skynet?
- Improvements to AI Production dynamics
- Canadian AI improvements
- Additional influence AI for NIG, SAF, RAJ, ARG
- More improvements to money AI
- America should no longer dump troops in Somalia for them to just die
- Added an AI decision for influence to try and get keep domestic influence up
- Toyed with the AIs likelihood to use the economic decisions
- Created an AI Strategy Plan for Nigeria so their game rules function better
- AI should be slightly more dynamic with trade agreements
- Corrected an AI issue where they would try to puppet nations that are already puppeted

Units/tech

- Increase fuel cost of Naval training
- Replaced trickleback bonus from body armor with recovery rate bonus
- Body armor buffs non-militia units a bit more now
- Nerfed resource requirements of the utility vehicles
- Reduced the speed of transport helicopters so the airborne units don't fucking ZOOM
- Reduced speed for Recon Tanks
- Aircraft nerfed
- Aligned support companies HP to batallions HP
- reduced IC cost increase from upgrades bought by XP for land units
- new starting division templates for Italy
- Nerfed gain from special forces tech/made them more expensive

Balance/Gameplay/Mechanics

- Buffed ISIS again to ensure they last longer than a few months
- Handful of Research Slot Balance to prevent the generic tree nations from having more than more industrialized nations
- Economic decisions now has a bankruptcy explanation as well as debt section
- New Game Rule to remove micronations
- Russia is more likely to chose options beside going putin if playing Ahistorical
- New War on Terror Stuff
- Islamic State no longer starts at full scale conflict with Kurdistan
- Nerfed Focus tree rewards for Brazil
- Balance to Italian Ideas and Focuses, especially non-democratic paths
- Balance to Mafia mechanics, moved basic decisions to events and added more
- Slight reduction for infrastructur
- Some math fixes are now redone
- Upped the penalty for researching ahead of time
- Reduced max tech sharing from bonus
- Added a month timer to economic/military aid so you can't spam puppet
- Balanced Canadian Subsidies
- Capitulations no longer generate world tension
- Some equipment now uses steel rather then aluminium.
- Total rebalance to all modules
- Buffed ships
- New revised bankruptcy mechanic
- Mexico should no longer fall apart 4 years into the game
- Military Officer training laws now increase general/admirals skills along with their level
- When treasury gets too negative now for both the player and AI it adds it back to debt and adds 25% more money to be in the positive again
- New Strengthen Nations game rules

Database

- Added 1965 utility vehicles to HUN in 2000
- Cleaned up some background stuff

Politics/Influence

- Rebalanced costs to influence decisions
- Changed Charles Taylor to Right-Wing Populist from Neutral Autocracy
- Added influence values for Liberian and Sierra Leonean rebels
- Made Armed Forces Revolutionary council a puppet of Taylor's Liberia to fix some weirdness with the wars
- The default subject level is now Satellite instead of Puppet (2nd highest autonomy level)
- Disabled Collaboration Governments
- The influence puppet action now makes the target an Associated State (highest autonomy level)
- Puppeting a country now gives them elections or removes them depending on the overlord

Content

- Added ceasefire for Ethiopian-Eritrean war to stop them fighting forever
- New Game Rules to Randomize Outlooks/Religion/Internal Factions
- New pictures and names for Italian vehicles
- Added custom name lists for Italian divisions and ships
- Syrian focus "Increase Exports" now raises your export law
- Simplified Syrian "Depose the Hashemites" focus coup chance calculation
- Syrian focuses for choosing between conscripted army and volunteer army now show correct effects
- After relations between Syria and Rojava break down, their NAP is disabled
- If Syria goes into civil war, it will get the Divided Syria idea and Lebanon will break free
- You no longer get double elections in Russia in 2000, instead you get the election event on the date of the actual election
- USA now needs to own Guantanamo Bay to setup the detention center
- Bonn Agreement now sets the leader correctly for Afghanistan

Graphics

- Updated Graphics for Coat of Arms
- Fixed a few broken shines
- Pictures for Italian events and custom logos for parties
- Fixed broken Indonesian Divided Icon/India Divided Icon

Bugfixes

- Fixed AI spamming Trade Agreement
- Localization fixes in One Child Policy
- Fixed released nations not being able to initialize custom political content
- Fixed issue in Greek tree where the clamp_variable was not correctly assigned
- Corrected Winnipeg's name
- Fixed Light Striker Fighter carrier category name not showing up
- Fixed a minor missing bracket in the Israeli tree
- Fixed nukes not producing
- Minor loc fixes in the Danish focus
- Fixed one of the nuclear reactors having a fuel cost
- Fixed Legacy Italian ship variants showing up for
- Localized Missing Tech Share Name for Israel
- More cleaning of the error log
- Fixed icon for Greek modifier
- Non-MTG variants should now only show up for non-MTG things
- Military Aid button requirements corrected
- Improved logic for manipulate politics so it actually removes 10% of the influence in the nation
- Corrected the name of the Saskatchewan class Frigate
- Fixed Nigerian Fleet crashing in 2000
- Cleaned up experience errors in Naval OoBs
- Fixed stuff being unable to convert in engine sections
- Releasable should now have politics/ability to invest
- Releasable now inherit the technology from releaser
- Fixed exploit with the invest and cancel bug
- Social Services tech gives a buff to rooting out resistance and entrenchment
- Fixed UI positioning of the puppet view in diplomacy
- Additional fixes to the MTG OoBs and tech balance
- Fix to the Italian carrier being a carrier rather then a heli operator
- Fixed AI Russia not following game rules
- Russia should now only go Putin when playing Historical
- The world will no longer randomly shift to preWW1 borders for no reason
- fixed releasable politics not initializing
- Corrected a handful of broken graphics
- Non-MTG legacy techs should no longer be given so no legacy ships should be present
- Greece should no longer go down other path if specified in the game rules
- Fixed texticons for units
- Fixed a handful of issues with influence actions
- Bill from Brussels should now fire after the first year
- POTEF election campaigning not disappearing fixed
- Fixed EU military exercises
- POTEF election campaigning re-enabling
- Integrating Finland and Greenland no longer gives you cores on the Galapagos and Ecuador
- Added tooltip to the Occupation of Lebanon idea
- Added a bypass for Russia's Novorossiya focus if Ukraine is a puppet of Russia
- Added missing anti-air attack from dual purpose light gun modules
- Turkey's util vehicles Ejder Yalcin changed from Otokar to Nurol
- Reworked money scripts so MP bug should now be fixed
- Flag compression redone
- all text icons in battles should now work as intended
- Added back Andorra's name
- Naval Defense Companies should now give buffs to Naval Units (The tooltips are going to be long. I am sorry)
- Ships should now cost money

Map

- New states in West Africa
- New Provincial Rework to Nigeria

Music

- Memories Without Colours and Firewall added

</details>

<details><summary>v1.5.0 'Economic Prowess & Man the Guns' - 1.10 compatible</summary>

AI

- Tweaked AI ratio of mils to civs to prevent frequent conversion
- Tweaked AI for Intelligence Agency
- Add AI division limiter
- Improved economic AI with tax rates
- Improved Economic AI with peace time decisions
- AI should now properly take and buy down debt
- Baltic countries no longer leave NATO immediately
- Overhaul of unit building AI
- New AI strategies to get the AI to manage their budgets better if they need to
- AI is now more likely to embargo other nations
- Trade AI - AI likely to make trade agreement
- Improved Influence/Investment AI for new nations
- Functioning AI for MTG ships
- Better AI for Fuel management
- AI uses more planes now
- better AI management to prevent influence spam
- Better Unit AI
- Improved combat AI to ensure proper wars
- Improved Trade AI. AI should be more likely to import oil in peace and during war to ensure fuel and a reason to actually have oil
- AI will now dynamically reject economic aid based on opinion and other factors
- AI Ukraine will now build units in 2017 start date to defend itself against Russia.

Bugfixes

- Fixed missing Algerian party icon
- Fixed missing texticon error with subunits
- Corrected Rwanda/Tanzania not having Commonwealth of Nations Ideas
- Fixed missing Malawi party
- Fix bailout event not updating interest rates
- Some minor fixes to 3D models
- Fix the Feedback Exploit to Tax Cost
- Fix names of Guatemala's leaders not showing up
- Fix Macedonia not having a core on its Eastern state
- Fix being unable to take the highest level corruption
- Fixed some general influence bugs
- Fixed several backend UI bugs
- Non-existent deleted weekly to improve performance of influence arrays as well to kill ghost influencers
- Fixes to Counter Terror Advisors decisions
- Texticons for various unit types should now show up properly
- Fixed being able to invest in lands you control

Decisions

- Fixed being able to sue Microsoft twice as USA
- Created cheat decision to max internal faction opinion
- Improved AI for Nigerian decisions
- Finalized Vehicle Equipment Purchasing
- Added additional checks to decisions
- New Influence Decisions to combat 1-3 influencers as well as improvements to influence decision AI
- Fixed support GCC membership decision showing up for a country that is already a member

Economy

- Increased resources for all nations across the globe: Particular focus on global exporters
- Economic decision to drop money on to spur growth
- Leasing decisions to recieve mils and civs when needed
- Rentier state and other resource driven economies now have more variability in income depending on exports
- Various techs now impact expenditures
- Additional factories for South America, Asia, and Africa. Particular focus around the regional powers.

Events

- Fixed Turkey Kurdish politics event spam
- Added Xinjiang rebellion event
- Made GCC countries less likely to veto initiatives
- In-Depth Italian Events

Focus Trees

- Made Nigerian tree compatible with Counter-Terror systems
- Fix Nigerian tree not properly deleting christian militias
- Moved Brazilian focuses so they no longer overlap
- United States of Europe Focus Tree
- Reworked Ethiopian Industrial tree
- Changed a handful of Ethiopian focus triggers
- Added Xinjiang SAR focus
- Fixed 'Alliance to Rival NATO' focus not creating a faction
- New Italian Tree
- New Canadian Tree
- United States of Europe (USoE) focus tree
- President of the European Federation (POTEF) focus tree
- New Extension to Brazils Focus Tree
- New Greece Tree
- New Israeli Tree (NOT FINISHED, PLAYABLE)

Gameplay/Mechanics

- Annexing Puppets Yields Cores on their core territory (prevents a uber aggressive nation conquering other countries and then annexing them to gain all cores on all their lands)
- Annexing Puppets forces you to inherit their treasury, debt and international investments
- Nukes are toggable now via the Game Rule
- Generals now can take 24 units rather then 15
- Max experience has been buffed to 1000 from 500
- Nerfed Biofuel refineries to cost 25000 from 45000
- European Council (Reworked Voting System, Voting Prediction)
- European Parliament
- European Union Budget
- Breach of European values
- Reworked EU Tutorial
- Reworked Influence Mechanics - Better balance with more AI usefulness, new military aid option
- Mexican Drug Cartels
- New Scripted Diplomatic Action - Trade Agreement
- New Mafia Mechanics
- Forambles: Arab Republic, Baltic Union, Central America, Gran Colombia, Scandinavia, Iberia
- New EU Council mechanics
- EU Parliament
- EU Budget
- Breach of EU value system
- POTEF election system
- Reduced influence gain from investments to prevent spam

Graphics

- Added missing Portuguese Portraits
- City graphics for all of Africa, Russia, Japan, China, Australia, New Zealand
- Graphics for some major landmarks like Mt Everest and Mt Kilimanjaro
- Additional Focus Icon Graphics added
- New Idea graphics
- Fixed Swiss portraits
- Fix to Spanish parties
- Metric fuckton of flags for you flag dweebs
- New Loading Screens

Localization

- Updated localization for Election Events
- Fixed typos in Game Rules
- Various focus tree localization improvements
- Updated Land Tech Doctrine Localization
- Updated localization for influence
- Various background loc improvements
- Internal faction opinion changes should display unique names now whenever doing the effect

Map

- New urban tiles and improvements to maps
- A large number of new states and fixes to some other states/provinces
- Fixed Botswana's Capital name
- A number of new landmark/City Graphics
- Fixes to some major cities not having Urban Terrain
- New straits!
- Fixes to Tunis' capital
- St Helena & Canary Islands now are present in their respective states
- Added Tags: SMA, MNC, LIC, CAS, CAL, TEX, ZAP, YUC, RGD, IOM, ETK, FGU, GAL, GRL, PAT, NAV, NEN, SAR, AND, SPL and SUL
- Corrections to some supply areas in Europe

Music

- Remastered Soldiers Without Guns, and Technology
- New Songs: Lost on The Hill, We Remember

Politics

- Dominican Party no longer shows up in Denmark
- Fix for Ukrainian Leaders now having the proper names
- East Timor is no longer radical Shiites
- Reworked Politics for Togo, Guatemala, Algeria, Ghana, Switzerland, Zambia
- Swiss Top 4 Parties now in coalition to more accurately represent the Swiss Federal Council

Tech Tree

- Added Nuclear Reactor tech allowed by Game Rule
- Added Construction, Fuel, Special Forces, Support Weapons trees to techs
- Rebalanced tech costs
- Improvements in tech tree localization
- New MTG Tree
- New Naval Doctrine

Units

- Units have received a comprehensive speed rework
- Costs are now more appropriate given new resource values
- Nerfed Maritime Patrol Aircraft
- Gave naval planes Scout Plane abilities
- Removed Engineer Tanks
- Fuel is now balanced according to new resources reworks
- MTG Compatibility

</details>
