---
layout: default
title: "v1.10.0 'The Lion of Brussels and Babylon'"
page_id: changelog-v1-10-0-the-lion-of-brussels-and-babylon
toc: "off"
order: 11
---

# v1.10.0 'The Lion of Brussels and Babylon'

<details><summary>v1.10.5</summary>

v1.10.5

Achievements:

- The Spanish focus "Solidify the Iberian Union" should now give you the needed country flag or conditions for the "Formed Iberia" decision
- Added achievement CzechosloGRANDia: "As Czechoslovakia, control all Czech, Slovakia and former Austro-Hungary territories, Silesia region and Zakarpattya state"
- Added achievement Czech Monopoly: "Have more §YŠkoda Factories§! and §YŠkoda Research Slots§! than §YIndustrial Complexes§! and §YResearch Slots§! at any time, while having at least 5 §YIndustrial Complexes§!"
- Added achievement One Man Army: "Train Petr Pavel to at least §Y75%§! in every §YTraining Card§! at the same time"
- Added achievement Afri-Net: "As an African nation ensure every African state has Network Infrastructure of at least 3"
- Added achievement Pan-African Highway: "As an African nation have a railway connection from Cairo to Cape Town"

AI:

- Added AI to Abkhazia to befriend South Ossetia
- AI should try to maximize internal faction opinion buffs in general to keep them more on the path
- Arabian States should befriend one another and become closer to one another via diplomatic options
- Increased the manpower from the Recruit Foreign Fighters decision from the factions
- The AI should now build Network Infrastructure when they research the next "G"
- Russian AI should no longer death war and declare conflict when already at war with NATO
- The AI should no longer instantly revoke the satellite access it grants and now will hold the access for three months before revoking
- Armenia's AI should now be more dynamic in the way they take war goal focuses so they don't suicide
- The AI should now be less likely to invest Fossil Power Plant if you are running heavy consumption, however, inversely they will be more likely to invest if you are running heavy restriction
- Made the AI a little more likely to join NATO and the European Union
- Implemented a hard block on the Become a NATO Aspirant for nationalist or salafist nations (if a European nation is somehow salafist I'd be surprised. Excluding you Bosnia.)
- Made the Spanish AI a little more apt at navigating it's focus tree
- Spanish AI should now recruit Foreign Legion and Regulares
- Italian AI should no longer power push characters if they have the Mafia idea
- Fixed the AI liberating stuff to Salafist. No, no, no silly western nations. ISIS shouldn't be stronger!
- The Salafist peace deal AI should liberate salafist nation's cores as long as they also do not claim or have a core on the state
- European Union AI should now vote closer to their overlord if they are a subject
- Russia AI is now using decisions more often
- The AI for nation's trying to assume your debt should no longer spam your top bar into oblivion
- Czech AI strategies to support more countries
- NATO countries are now more likely to ratify membership in the Alliance
- The AI of Bulgaria, Serbia, Kazakhstan, Kyrgyzstan and Tajikistan are now more often brought to power by various parties

Balance:

- Added additional internal factions effects to a variety of different trees
- Military spending now raises the minimum of "The Military" opinion
- All Intelligence Agencies upgrades will now give the "Intelligence Community" opinion
- Ideological powers decisions should now give opinion relating to the specific focus group that they impact
- Reduced the economic cycle upgrade cost from 7.5% to 5%
- Reduced the at war increase for the military expenditure by 20%
- Positive economic events are now more likely to happen if you have a high GDP Quarterly Growth Rate
- Increased the Western Outlook drift from European Union by a couple points
- Increased the stats of United Kingdom general Kevin O'Donoghue so he's not a private in terms of skill
- Added a small amount of AA to the HMG module for tanks
- USAID will now cancel if your GDP/c goes over 25k
- Reduced the Communist Cadres/The Military requirements for Communist Cadres
- Readjustated starting Polish artillery and C3 equipment
- Slightly increased the Fossil Fuels you get from "Russian Energy Resources" as Ukraine
- Improved and rebalanced some Armenian focuses to include more dynamic behavior depending on world situation
- Adjusted the limit for 1000 debt being taken to where you need 1500 GDP Total
- Added +100 weekly manpower to the Foreign Jihadists Internal Faction to make them stronger
- Belarus' Agriculture Idea now grants bonus income to Commercialized Agriculture Districts
- Slightly increased the income from all resource exports. Should make the resource income a bit more substantial for resource heavy nations
- Rebalanced the Untied State's mega spirits into multiple smaller spirits to make it more digestible when playing through the tree
- Rebalanced the Liberals Productivity to 0.75 to 0.50
- Rentier State now gives +15 opinion to Fossil Fuel Industry

Bugfix:

- Fixed the missing model errors from TOTA (added blank asset files)
- Fixed Larry Holmes being Larry Golmes by mistake
- Fixed the "Businesses in the East" not giving opinion when funding startup
- Fixed Hezbollah not giving APCs in your weekly income
- Fixed a missing icon in the Libyan tree
- Asking for a bailout from the African Monetary Fund now reduces your debt instead of adding to it
- Botswana's event to crown Mosadi Seboko now fires in the correct year
- Fixed Morocco's political leaders not working
- Fixed the HEU enrichment limitation not actually working
- Fixed internal faction event localization
- Fixed the Muslim Brotherhood events spamming
- Fixed missing flag for Andorra, Vatican City, and San Marino being unable to join the European Union
- Fixed Bonsnian army spirit providing 10 recovery rate instead on 0.1
- Fixed the Canadian history file giving you tech to non-BBA planes despite having the DLC
- If you leave NATO you should now lose the NATO Nuclear Sharing Group idea
- Fixed an issue with a national spirit not being removed for Indonesia
- Fixed Jack Layton being in the wrong party for Canada
- Fixed the broken display in the leasing section stopping working at 20 leased buildings
- Fixed a bug with liberating lands which would reset your tech and focus tree if you were given back your cores
- Fixed the inability to pay off all debt if you have under 1000 gdp
- Fixed Armenia being able to dismantle factions that it is in when forming new factions
- Fixed an AI Template category being available to players on game reload or when tag switching
- Fixed the cancellation of Germany Legacy and German War Reparations requiring you to be both Nationalist and Salafist
- Patrol boats missing stats
- Fixed the typo of Marie-George Buffet's name
- Fixed Boko Haram breaking the rest of the religious tree for Nigeria
- Fixed the cap of the Spanish Foreign Legion Tercio not properly updating as it was in the state scope
- Fixed the BMPT terminator having the No Turret module installed
- Fixed the Georges Leygues French ship from non-MTG having level 1 experience
- Fixed German air wing names for Spain
- Fixed the Scandinavian formable decisions not working appropriately
- Fixed Shanghai Cooperation Organisation States could can start military manoeuvres permanently after annexed the target country
- Former NATO members should no longer be NATO members if they're subjects
- Fixed the Effective Consumer Goods Factories for the Ledger
- Fixed unit leaders from other countries not being appropriately transferred during the formable nation formation
- Fixed random "Vacant" leaders being present in ELS, UZB
- Fixed M10 Booker having 2 machine guns
- Fixed the weird gets blank event as USA when getting the Housing Market Crash
- You should no longer be able to see the "Ask Debt Bailout from Your nation here" when you have no nations influencing you
- Shi'ism can now be spread in UAE, QAT and YEM
- Fixes to triggers to boosting Shi'ism in Iran
- Fixed the positioning of American cities so their city terrain picture is in the correct province
- Fixed an issue with ISI repeatedly triggering a civil war in Iraq
- Fixed an issue with the independence for Iraq not triggering
- Fixed an issue with an immortal Jay Garner in Iraq

Content:

- NEW/IMPROVED FOCUS TREES: Urals, Kuban, Romania, Gagauzia, Southern Republic, Czech Republic, PMC Wagner, Syria, Afghanistan
- Added additional decisions to a variety of different internal factions
- Added a decision to buy technical Pickups
- Added some new events to Internal Factions for the religious factions
- Added the ability to "Accept All Reactor Grade Fuel Purchases"
- Added 2 new air force MIOs for Poland
- Added content for the 2nd Sudanese Civil War, War in Darfur, Conflict in the Blue Nile and South Sudanese Civil War
- Reworked political parties and leaders for Sudan, South Sudan and Darfur
- New focus for Libya: Support South Sudan
- Added a failswitch that you won't get Muslim Brotherhood events if the civil war starts
- New focus for Indonesia: "Grasberg Mine Exploitation"
- You can now request Major Non NATO Ally status if you have over 100 opinion with the United States
- If you haven't set your nuclear status for Nuclear Energy when constructing Enrichment Facilities it will automatically set it and your production to LEU
- SCO member states expansion and tweak, now China could let more countries into the SCO, most of which are African Countries
- Adjusted the conditionals for China's Strengthen ASEAN Ties so it does not consider nations if they do not exist or do not have the ASEAN idea
- Added a new "Internal Investment" mechanic that you can use to encourage specific state based programs. Can be found when clicking on your owned and controlled states similar to International Investments
- Namelist for Russian squadrons
- Improved the Foreign Legion mechanic for Spain giving it a reform option to make them slightly stronger
- Added a claim to Gambia for the "Legacy of the Duchy" focus in Belarus
- Changed the Opinion modifier for East Asia Summit called "Attended East Asia Summit" from the news event
- Changed the claims for Greater Serbia correcting including Croatia and Bosnia
- Egypt can now boost Al-Nour Party
- Russia: Rework of the Zhirinovsky tree
- Russia: Rework System of Subjects
- Russia: Rework of the Military tree
- Russia: Mechanic of the Wagner PMCs have been removed, now Russia is creating a playable "country" of the Wagner PMCs in Southern Krasnodar
- Added two new "teaser focus trees" for New England, Cascadia, Lakota
- Added the Florida Uprising to the Post United content for USA
- Added the Rocky Mountain Resistance to the Post Untied content for USA
- Added the Reclamation Front for the Republic of Lakota to the Post United Content
- Added some additional content to the 2008 GFC making it bypassable now depending on choices made earlier in the game
- Free at Last in Serbia's tree now requires you to have full control of Montenegro so if you end up with it as an outside power you don't lose it
- Bohemia, Sumava, Mazowsze and Małopolska gained Hydroelectric Infrastructure
- Czech Republic focus tree, starting decision and national spirits
- Added Petr Pavel as a Czech Military High Command
- New default Czech division templates
- New starting military equipment production in Czech Republic to save your time
- Czech Party Leaders scripted gui
- Czech Petr Pavel scripted gui (no alt-history yet)
- Dozens of new Czech leaders, new Czech parties
- No Step Back DLC: Czech Republic has new technologies in Armor category, enabling new, better engine modules.
- OOB for Czech Republic
- Czech starting leader is now Václav Havel
- New Czech historical events triggered at certain dates
- Some of the Czech Army leaders gained new traits
- New shared research group, Volkswagen Group, has been created. Bonus was granted to every member (as for year 2000)
- New quote in loading screen, from Petr Pavel
- New Czech Republic bookmark entry
- New Syrian Republic bookmark entry

Database:

- ADJUSTED PRODUCTIVITY: MIC, KOS, KAR, KAC, SHN, WAA, ABK, JUB, CHE, SOM, RYU
- Added Precious Metals to Western Papua in Indonesia for the Grasberg Mine
- Added a couple new Swedish generals and admirals
- St. Pierre (French state) now matches closer to French Guyana in terms of Productivity

Game Rules:

- Add a new set of game rules for USA, USB, CSA, CAS, LKT focus tree behavior
- Added a "120" day option to the European Union cooldown
- Added a "Internal Faction Monthly Tick Rate" with 0.10/0.25/0.50/0.75 as options.
- You can now appropriately weaken Yemen in the game rules
- Czech game rules for historical and communist paths

Graphics:

- Reworked most of the decision menu pictures
- Additional conversions of PNGs to DDS for more optimized performance for players
- New models for the following nations:
  Europe:
  - United EU, Italy, Spain, France, Netherlands, Belgium, Germany, Poland, Denmark, Norway, Finland, Sweden, Armenia, Georgia, Greece, The 3 baltic state, Romania, Czech republic, Ukraine, Russia
    Middle East:
  - Israel, Turkey, Egypt, Syria,
    Asia:
  - India, Pakistan, Australia, Japan, Afghanistan
    North America:
  - USA, Canada
- New set of evolutive generic models for Eastern Europe, Africa, South America, Middle East, Asia
- Hundreds of tech and variant GFXs for multiple nations
- Fixed the broken icon for Panavia Germany
- Fixed the missing flag for the USNA
- Fixed the incorrect icons for the burst fire modes in the SPARTY modules
- Added a number of new city images for their urban terrain picture
- Updated part of the UI to be more modern and more "MD"
- Added a new loading screen for Indonesia from their turmoil in Aceh

History/OOBs:

- Multiple OOBs rebuilt
- Variant added to multiple nations, totaling in the hundreds

Localization:

- Fixed an error with Saddams Rage localization not appearing
- Redid political party names & descriptions for: PER, SAU, TUR, IRQ
- Add and Replace tooltips of Chinese focuses for more readability
- Fixed the localization for the "TAG" integrates TAG now properly
- Add Spanish Localization
- Fixed the Ideological Power incorrectly displaying the wrong productivity growth

Modding Resources:

- Added more detailed unit modifiers for main infantry battalions as well as org modifier for existing sub-unit modifiers
- Added two additional modifiers for the "Internal Investments" system

Ribbons:

- Added ribbon Kraj Královecký: "As Czech Republic, conquer Kaliningrad"

User Interface:

- Added an "Unemployment Rate" map mode
- You can now see your last quarter's GDP growth rate in the GDP tooltip
- You can now reduce the Employment Target of Commercialized Agriculture Districts
- Added a quick display of breach of European Union values when you're trying to join for the utility
- Added a decision to hide Foreign Influence modifiers from the decision category
- The menu for Foreign Influencer will now expand and shorten depending on the number of influencers
- Added a new State Investment screen when looking at owned states
- Fixed Network Infrastructure not properly displaying that it increases the speed of International Investments

Performance:

- Optimalized Polish events and fixed some styling
</details>

<details><summary>v1.10.4</summary>

v1.10.4

Balance:

- Made it so that if Syria is a puppet of Iraq, it cannot take the focus "Iraqi Divisons" which causes a civil war in Iraq
- Rebalanced the Magpul Magazine/Extended Magazine to be more balanced and more of a choice
- Rebalanced the doctrine "Squad Level Tactics" by giving it 2.5% more attack and defense to make it a more viable choice
- Each level of Railways in a state now gives 4% state level productivity growth
- Increased some of the internal faction buffs in the South Korea, Chinese, and Gulf State trees to make it easier
- Added "Net Migration Rate" value factor to low corruption and higher corruption lowers the net migration rate
- Made license slightly harder to get to prevent the USA accepting to share F-22/B-2 license at game start
- Made it so tht Hezbollah can no longer access the international weapons market (AAT)
- Adjusted land doctrine buffs, reducing all night attack and speed buffs
- Increased cost of land doctrine combat doctrines from 35 to 40 for pacing
- Tweaked some of the internal faction effects in North Korea Tree
- Tweaked North Korean focus "Constrain the Donju", which would give DPRK $100B with only 35 days

Bugfix:

- Fixed an issue with Iraq where the 'Uday Hussein' national spirit expired for no reason
- Fixed an issue with Iran where the revolution goes undone if you click a certain decision betwee March 2001 and June 2001
- Fixed an issue with Iran where the prime minister portraits were displayed incorrectly
- Fixed an issue with Iran where if you failed a debate, they wouldn't show up in the next one
- Fixed the Hezbollah raids being able to be only done once
- Fixed an unlocalized string in the Hezbollah raid
- Fixed the ledger and some money tooltips missing the Migration Control total
- Removed the duplicate initialization of city images causing a slowdown in the beginning of the game
- Fixed the Generic Tree "Neutrality" focus allowing you to go to isolation if you have the military internal faction
- Fixed the duplicate intelligence agency for COL
- Fixed Suicide Drone Costs

Content:

- Added "Overlord Subsidies" Diplomatic Action
- Changed the focus "New CAS Aircraft" to "Joint Strike Fighter"
- Added an option to keep Saddam after 2009, if you choose to do so, he will age & Get Alzheimer's
- Added 20 or so events relating to Saddam Hussein's Alzheimer's (If you keep him around)
- Added an event related to the Iowa battleships
- UK stockpiles, variants, and OOB has been reworked

Graphics:

- Map improved with community feedback
- Major overhaul of Iranian and UK models
- Added Swiss infantry

History:

- Reworked Iran starting techs and removed 2G from its provinces in 2000
- Added missing train tracks+supply hubs to the USA

Localization:

- Fixed the misspelling of the "Norwegian Armed Forces" in the Norwegian tree
- Fixed the misspelling of the "Reliance On Europe" opinion modifier

Performance:

- Consolidated some files so the startup time is quicker for the mod
- Optimized a number of minor textures from PNG to DDS to help the loadup time and in-game registration of icons

User Interface:

- Added the "Foreign Investment Limit" counter to the configurable display UI
- Added "Productivity" to the "Economy" tab of the Ledger
- Added a notification event for the European Union when the Council and Parliament are ready for session
</details>

<details><summary>v1.10.3</summary>

v1.10.3

Achievements & Ribbons:

- Added achievement Diamonds Are A Ruler's Best Friend: "Extract over 500 precious metals"
- Added achievement Botswana: "As Botswana, research Human Imitation AI"
- Added achievement Captain Planet is Done With Your Shit: "As Botswana, have 0 poachers and have the Kalahari Desertification at its lowest level"
- Added ribbon Naledi Ya Botswana: "Reduce AIDS infection to its lowest level"
- Added ribbon Botswana Defence Force Conduct Valour Cross: "Be at war with a country 5 times stronger than you"
- Added ribbon Botswana Police Medal for Meritorious Service: "Solve the Zimbabwean refugee crisis"
- Added ribbon Botswana Teachers Silver Jubilee Medal: "Increase the literacy rate to 90%"

AI:

- Made the AI for Africa more dynamic to ditch the CFA Franc
- Made the American AI more likely to intervene in Haiti when George Bush is in power
- Fixed the AI being unable to build enrichment facilities

Balance:

- INCREASED PRODUCTIVITY: NKO, CUB
- Reduced the amount of income from Agricultural Districts
- Increased the worker requirement from Agricultural Districts
- Increased the building cost for network infrastructure
- Added expected Administration Spending modifiers to the French ideas
- Increased the investment duration for all investment projects by 10% (they needed to be slightly slower anyways)
- Increased the Reduction of Workers in the AI tree in the Internet techs
- Added a penalty of energy consumption per office sector to represent the insane amount of energy for AI
- Added a Energy Use multiplier and Supply Consumption buff to Elite AI difficult
- Removed the Agricultural District/Agriculture income from the Farmers faction since it causes a double tax gain situation
- Conscription laws reduce migration rate on Partial Draft and Draft Army
- Limited the 1000 Debt button requiring you to have at least 1t in GDP to take 1t in debt
- Increased the likelihood of Ag District conversion events
- Retweaked Chinese PLA Business Ventures idea with new modifiers
- Internal faction opinion that is over fifty will now tick down towards 50
- Added more starting techs for POL in armor category and locked C3ISTAR equipment
- Removed the stability penalty, added productivity, reduced research penalty from Corruption
- Five Year Plan will now give Communist Cadres opinion
- Nationalizing assets from the Communists will give Communist Cadres Opinion
- Rebalanced some of China's Communist Cadres and Military gain to make it easier to do specific things
- Slightly increased manpower given by mobilization
- Made it so that you need to be friendly with Russia to pass through the Volga-Don Canal
- Changed weights of units for traits and icons

Bugfix:

- Fixed a couple focuses for France where the Stage: focuses were going to the wrong continent
- Fixed the migration mechanic giving inverse logic productivity
- African Investment Bank now gives +2% ROI instead of +200%
- You can now actually do the African Union focuses
- Fixed the Agricultural Districts getting ridiculous production buffs on high productivity
- Fixed the incorrect party description for Venezuela Military Junta being South Ossetian for some reason
- Fixed the Nigerian parties not properly showing their icon in coalitions
- Fixed the starting Mexican elections
- Botswana's Buy Gunships focus now correctly gives helicopters into stockpile
- Botswana's Replace F-4s focus now works even if you are a poor person without all DLC
- Fixed the debt button not being able to be clicked when you have "Incoming Financial Collapse"
- Fixed the double infrastructure for Kanto if you take Automotive Industries and then the Northern Expressways in the Japanese tree
- Fixed broken NSB focuses and a broken Armenian purchase focus
- Fixed an issue with Balance of Powers being hidden under autonomy GUI
- Fixed the CHE coring ARM decision
- Fixed the unit leader transfer issue in West Indies Federation decision
- Fixed an Libya decison trigger issue
- Fixed some typo between Cat*/CAT*
- Fixed the some swap_idea issues causing duplicate idea
- Fixed STATE_TRANSFER_ADD_CORES event, it should work now
- comoro_events script cleaning
- Changed the population in ledger from k(which actually is 10k) to M, ledger table can display the proper population now
- Fixed some city gfx missing
- Fixed the Libyan focus redundancy where you had to do both "Influence Kuwait" and "Influence Yemen"
- Fixed the Central Asian Focus Tree focus "National Council" allowing you to gain the popularity of people long dead
- Fixed an incorrect dependency in the Estonian Focus tree for the final military focus
- Fixed the European Union game rule not working as intended
- Fixed the migration mechanic incorrectly showing a different value on game start
- Fixed some Spanish decisions not showing up properly if you do not have elections
- Fixed infiltrated assets invaliding after a save game load
- Khamis Gaddafi will no longer be a rival to Mutassim if Mutassim is dead or exiled
- Fixed Libya's Increased Tourism applying twice
- Fixed the CV 2035 being unable to be unlocked for non-MTG
- Fixed the international system renting of specific PMCs self-influencing
- Fixed the inability to ban the Moderate Islamists as a non-Muslim nation (gotta ban the Islamists)
- Fixed Eastern Europe graphical culture wrongly assigned to Asian countries
- Fixed incorect Polish army general portraits
- Fixed a bug where the Iraqi flag was displayed incorrectly
- Fixed a bug where Kurdish soldiers were starting on Iraqi territory
- Fixed Jay Garner being captured by American forces instead of Saddam
- Fixed an issue where the Autonomy GUI would cover the Balance of Power GUI, the BoP should now be visible when you are a puppet

Content:

- Increased the priority of French decisions so they appear near the top rather than the bottom of the list
- Reworked Irans Parliament system
- Adjusted the Turkish PKK mechanic in order to allow you to end the insurgency if compliance is 100% in Kurdish states
- New event chain for Iraq if it goes down the Shi'ite path
- Reworked Botswana's anti-poaching mechanic to be less of a clickfest
- Reworked modifiers of Coal Powered Nation/Renewable Powered Nation for Botswana
- Rebalanced a lot of Botswana's tree (focus durations, monetary costs, bonuses etc.)
- Added Army General for POL
- Reworked Liberia's political parties, leaders and generals
- Hezbollah's Al-Mansar focus now also adds the idea to Palestine/Hamas
- Adjusted some Kazakh focuses to give ag districts instead of building slots
- The Ace Pilots can now be female
- Reworked Libya's Oil Nationalisation mechanic to make the economy a bit more stable

Database:

- Rebuilt KOR, JAP, CHI, and TAI OOB, stockpiles, and variants. Also UKR+IRQ OOB fixes
- Removed variant version numbering for most majors
- Rebalanced Vietnam's building placement so Ho Chi Minh city has buildings
- Added Geothermal Energy Production to the following tags: USA, MEX. KEN, ICE
- Large-scale replacement of PNG format to optimize operation efficiency
- Added accurate Division namelist to Russia+Korea
- Coptic Egypt can now take the "The Clergy" internal faction
- Revised most nations starting corruption

Graphics:

- About 60 3D models and texture
- Complete equipment GFX + 3D models update for China, South Korea, Japan, and Taiwan
- Partial equipment GFX + 3D models update for Poland, Czech, Kurdistan, Israel, Hezbollah, Iraq, Russia, USA
- 80+ high quality Aces portraits for Asia and USA
- Set of new landmarks. Eiffel tower: Golden Gate, Basil Cathedral, Christ Redeemer, Statue of Liberty, Capitol and Obelisk, Kabaah, Dome of the Rock, Great wall,
  Pyramids, Empire States Building, Okayama Castle, Himeji Castle, and Fujisan
- Set of new generic modern buildings. Airport, Naval Base, Supply Base, Factory

Localisation

- Major fixes and improvements to the Russian localization
- Improvements to localization in Ukrainian content
- Added a better tooltip for a trigger when Libya is not ruled by the Gaddafis
- Fixed a number of small typoes in the Nigerian focus tree and the events
- Fixed a option for the event issue showing the wrong localization in the Operation Secure Tomorrow event
- Added a trigger tooltip for Indonesia's Invest in our Policies focus
- Re-added missing loc strings in the German tree (They got deleted for some reason?)
  Map:
- Complete Graphical rework of the map
- Add Abu Musa Isles
- Add Western Timor
- River cross fix
- Russian Central Federal District revamp (complete)
- Add Huai River

Music:

- New radio station with 53 minutes of Asian themed music

Used Interface:

- Fixed the total number of employed persons for Commercialized Agriculture Districts not being present in the tooltip for Millions Worker per Sector
- Added the potential Renewable Energy Generation to the Power Energy Generation User Interface
- Added the European Parliament Voting Cooldown and European Council Voting Cooldown

</details>

<details><summary>v1.10.2</summary>

v1.10.2

Achievements:

- Added achievement Africa Paradis: "As an African country, form the United States of Africa and have a higher GDP than any European country"
- Added achievement Gaddafi? More like Gooddafi: "As Muammar Gaddafi, rule over a democratic Libya"
- Added achievement Gaddafi? More like Baddafi: "As Muammar Gaddafi, dismantle Libya"
- Added achievement No Gods or Kings. Only Man: "As Muammar Gaddafi, choose something different. Choose the impossible. Choose rapture"
- Added achievement F is for Family: "As Muammar Gaddafi, have all your children be either dead or exiled"
- Added achievement T-Posing: "As Libya, have Tibesti and the Tuareg State as subjects while they own all their core states"

AI:

- Improved building production AI getting the various nations to focus more on productivity buildings for longer term gain
- Enabled the AI to build the new Agriculture Districts
- The AI should now reject investment offers of buildings that require power if they have unfulfilled energy requirements
- Encouraged the AI to pass the Charter of Fundamental Rights first before other laws
- Disabled the AI for the Nuclear System for the time being until we rehash the Missile System
- Fixed the European Union AI from not providing IPA to EU Candidates (no not the beer)
- Turkey should be less likely to bail out Greece while it is in debt throes
- Improved the AI with Enrichment Facility rejection so they consider more factors
- Improved the AI for the research slots so they don't have open slots available
- The AI should now research SAM missiles to help them out a bit
- Improved the French AI when it comes to the Central African Republic Bush War in 2006 always escalating
- Improved AI for peace deals for China, Iraq, Kurdistan, Nigeria, Ukraine, Saudi Arabia, Serbia, Russia and America

Balance:

- Reduced the amount of fuel consumed by non-electric (population) sources
- Buffed the Fuel Silo storage from 100 to 200
- Adjusted MAD productivity
- Adjusted the GDP/c Monthly Population to always be positive
- Rebalanced some of the ideas for the European Union
- Rebalanced Greek focuses in the Economy tree to make it less of a pain in the ass
- Reduced base yearly population growth from 0.01 to 0.008 to accommodate for the migration system
- Reduced the Welfare law monthly population and spread it more evenly among the laws
- Reduced the Foreign Influence Modifier to America
- Removed the requirement of needing to have Corruption Level of 7 or lower to do deradicalization campaigns
- Removed the Internal Security requirement to conducting Police Raids on Terrorists
- Reduced and increased some POL national spirit modifiers and changed some of them to permanent spirits
- Country of Peace national spirit in POL can be reduced now in every political branch
- Added a clamp to all missile production types of 5k missiles at any given time since people can't practice self-moderation
- Capital Ships are 50% cheaper in peace deals
- Screen ships are 80% cheaper in peace deals
- You can no longer form both the United Arab Republic and the Arab-Maghreb Union at the same time
- Having the International Sanctions idea now prevents you from accessing the weapons market
- Added a 750 construction increase per level of network infrastructure to hamper some snowballing in later tiers
- Added a dedicated countermeasure slot to planes

Bugfix:

- Fixed an issue where the Base Fuel Gain of a nation wasn't quite accurate
- Fixed a visual display for the North Korean succession decisions
- Fixed a bug with Iran not having F-14 Tomcats in their stockpile (For BBA Players)
- Fixed a bug where the Petrov section wouldn't be able to remove the Corrupt Oligarchy
- Fixed the Haitian opinion modifier "Reparations Demanded" incorrectly applying to Haitian opinion of France
- Fixed the French NEPAD decision incorrectly decreasing construction speed
- Fixed a display error in the Money System showing that everyone was paying for the NEPAD sponsor when its really just France
- Fixed a Spanish error for the focus "Revised Military Interventionism" requiring more tension limit
- Fixed a Spanish error where it incorrectly reduced the Greens popularity in Environmental Deregulations
- Fixed a Spanish error where the focus "Reconnecting with Our Roots" would have no effect if you didn't have the labour unions
- Fixed a Spanish event error where it would incorrectly show you that you're getting the event "Blaming the ETA" despite you blaming the Islamists
- Fixed a NATO decision error where you can join NATO Nuclear Sharing despite already Nuke Sharing
- Fixed a NATO decision error where you can gain opinion of America as America
- Fixed a crash when anyoned tried to puppet Israel upon it's capitulation
- Fixed Counter Terror "Coordinate Decapitation Strikes" LAR Operation
- Fixed Auto-Influenced countries continuing to remain in the list despite not existing
- Fixed the Spanish Airbus Helicopters MIOs not being associated to the right parent MIO
- Fixed being able to integrate Formable nations without owning everything required for the formable
- Fixed the Counter Terror advisors remaining after war declarations
- Fixed a display issue in the CT system not showing Threat Level/Radicalization min/max
- Fixed a crash related to puppeting a non-Arab country as the UAR
- Removed double Kosovo from the Bookmarks
- Fixed the Small Arms Manufacturer being available to Greece
- Fixed the European Parliament Timer not working as intended
- Fixed the idea ETA not being present on game start for Spain
- Fixed a localization error where the Hezbollah Border War with Israel would give you Shia related descriptions despite being Israel
- Fixed bug that Chinese didn't have SPAA in 2000s
- Fixed Polish military tech boosts not working with NSB and BBA dlcs
- Fixed Polish focuses that add buildings to bypass when building cannot be added
- Fixed Polish Visegrad branch not available when annexed requested countries earlier
- Fixed French CNES popularity public support
- Fixed Kosovo focus making you get negative euroscepticism
- Fixed the Keystone Pipeline instantly finishing
- Fixed a spamming error regarding the has_idea and has_country_flag EU_candidate
- Fixed the Serbian decision "Appeal to Nationalist" providing democratic support instead of nationalist
- Fixed Iraq's focus effect "Outlaw Opposition" which would ban Ba'ath Party
- Fixed being able to take debt while the mission "Incoming Financial Collapse" is active
- Fixed the Spanish regarding the Gibraltar Referendum Rock event not giving options
- Fixed a bug where the home country of PMCs could not hire PMCs within their country
- Fixed a missing leader for the SNA in their current event
- fixed a missing event for Denmark regarding purchasing Fighters
- Fixed the agricultural events where you could embargo yourself
- Fixed a number of provincial errors in various focus trees
- Fixed a division template being created after a unit creation in the Central Asian tree
- Fixed Egyptian Helicopter Operator purchase from France causing crashes
- Fixed visual issue in Economic Preview menu where it included subject military factories.
- Fixed energy and defense cost calculation to not include subject military factories for the overlord.
- Fixed the Central African Republic event firing more than once a month
- Fixed Crete starting at 0% taxes when released
- Fixed Libya starting with too low GDP
- Fixed the Tuareg State not having any techs when released
- Fixed a influence bug where you could spread influence and gain influence at the same time with the auto influence report off
- Fixed the missing parent class for the Futuristic Integrated Missile Radar Control for MTG ships
- Fixed that Chinese Focus "End US Hegemony" requirements cannot be properly met
- Fixed that Chinese Focus "Support Negotiations" Requirements cannot be properly met after Taliban's defeat
- Fixed the ability to have undercover agents go negative in the mafia system
- Fixed the additional income from fertilizers for Egypt not showing in the economic tab.
- Fixed Houthi Yemen not having the right employment values causing them to have 0% GDP when spawned from the Iranian focus tree
- Fixed the Indian Maoist rebellion mechanic.

Content:

- NEW TREES: Libya, Tibesti, African Union (Shared)
- NEW REWORKED/IMPROVED: Ukraine, Crimea, Donetsk People's Republic, Greece
- New building "Commercialized Agriculture District"
- New Internal Factions events and decisions
- Decoupled the Corruption Events from their old pulse and mixed them with the other random events. It should make it a bit less spammy
- Added "The Eurozone Debt Crisis" event chain spurred from the USA Global Financial Crisis
- Added "Migration Rate" mechanic to the game
- Added a new law "Migration Law"
- Updated content for nations to the new Migration Mechanics
- Added the "Migration Crisis of Europe" to the game
- Added the idea "The Casino City for the Rich" fot Monaco
- Added the "Naval Power of the Continent" mini-mechanic to the power ranking system
- Added the "Campaign for Lower Government Spending" decision
- Added an event in 2010 regarding the formation of Constellis
- Added four new releasables: Cyrenaica, Fezzan, Tibesti & Tripolitania
- Added new country leader traits: Skilled Lobbyist, Inexperienced General, Scholarly Challenged, Substance Abuser, Playboy Lifestyle, Aviation Engineer, Agrarian Expert & Convicted Criminal
- Added African Union mechanics to accompany the shared tree
- Added a discourage population decision for those who want to make their country have less people pre-maritally holding hands

Game Rules:

- Removed the "Disabled AI Missile Alert" game rule
- Added a game rule so you can have the AI start with 250, 500, or 1000 political power
- Added a game rule so you can adjust the voting cooldown for the European Union

Graphics:

- Enlarged previously broken diplo actions backgrounds so that they fit the buttons accurately
- Added event images to the European Union events
- Added missing icons for the Private Military Companies in the International System screen
- Dozens of new models: USA, Russia, France, Germany, Denmark, Norway
- Complete Ukrainian ground models lineup
- Lots of bugfixes and 3D improvements
- more than a hundred new GFX for the air designer
- New GFX for ship hull icons

History

- Algeria now guarantees Sahrawi at game start
- Added historical number of SCUDs to Libya
- Removed corvette Ain al Gazala and submarines Al Badr & Al Fatah from Libya
- Added a attack helicopter company to Libyan Republican Guard unit
- Removed the 32nd 'Khamis' Brigade from Libya
- Morocco and South Sudan no longer start as African Union members
- The Tuareg State now spawns as Non-aligned instead of Salafist if released
- Added starting influence into the Tuareg State
- Improved OOBs of USA, Russia, France, Germany

Localization:

- Add Polish and Brazilian Portuguese localization to MD
- Added descriptions to the remaining Private Military Companies
- Major fixes and improvements to the Russian localization
- Fixed missing localization in the International Systems screen
- Added country specific division leader ranks to all countries that currently have focus trees
- Fixed the T-134 being drunk instead of being a bear (changed the hull name)
- Improved the Kenyan parties and added descriptions to each of them

Map:

- USA province level revamp
- Russian Central Federal District revamp(section)
- Morocco revamp
- River cross fix
- State rework in Sudan: Split Kordofan into North and South Kordofan, split Blue Nile into Blue Nile and White Nile

Modding Resources:

- Added two modifiers "Base Migration Rate Value" and "Migration Rate Value Factor" for the Migration System
- Added a modifier "Migration Control Cost Modifier" for the new Migration Control law
- Added new modifiers for the Commercialized Agriculture District to impact their tax rate, worker percentage

Performance:

- Optimized On Actions a bit more cleaning up some of the events
- Fixed some performance heavy events which should help daily ticks
- Reduced some logging statements so you don't have a 2.0 bajillion game.log after a year of a gameplay

Ribbons

- Added ribbon Libyan Order of the Republic: "Fulfill your service to the state of Libya by playing until 2020"
- Added ribbon Libyan Order of the Jihad: "Have a GDP/capita higher than 50k as Libya"
- Added ribbon Libyan Order of the Grand Conqueror: "Ally yourself with a Superpower or a Great Power"
- Added ribbon Libyan Order of Military Merit: "Rverse history and win a war against Egypt and Chad"

Sound:

- NEW VOICELINES: BRA, POR, MEX, AST, GRE, KUW

Quality of Life(QoL):

- Reformatted the Energy UI so it is more clear with additional and pertinent information
- Added the version number to the loading screen so you can unfuck your version before it loads all the way in
- Polish tree now reposition itself after hiding socialist and conservative branches and after hiding communist/nationalist branches.
- Added a take a 1000b in debt button to the debt buttons

</details>

<details><summary>v1.10.1</summary>

AI:

- Fixed the historical AI inaccuracy where the Communist Party of Cuba wouldn't take the Pro-LGBT Policies
- Cleaned up an Operation Enduring Freedom AI strategies so they're more performant friendly
- Added a two week delay to the EU AI from proposing a new law giving the player an opportunity to put their own laws up to vote
- Added a two week delay to the EU AI from proposing a new Euro Council law to give the player a chance
- Fixed the American AI trying to garrison the US Naval Base despite leaving it
- Fixed the European Union AI from immediately taking Offices giving no chance to players to return
- Fixed the AI of Myanmar always bankrupting immediately
- Made the AI less likely to propose trade agreements/debt/mutual investment treaty while it needs political power

Balance:

- Removed the armor value from "NextGen Design Mindset" since helicopters typically don't have armor
- Reduced default influence gain from 2% flat to 1.5% flat
- Reduced SOV tank stockpiles
- Increased the construction time for a number of building types
- Increased the PP cost for Proposed Trade Agreements
- Made Chechen slightly stronger. They now start with insurgency doctrines.

Bugfixes:

- Fixed all of the intro focuses bypassing for Serbia
- USAID will cancel if the USA no longer exists
- Fixed kosovo uprising focus for Serbia having incorrect party checks
- Fixed several localization errors in the Iraqi tree
- Fixed missing bypasses in the "Era of Saddam" focuses for Iraq
- The Kuwait Naval base will now be given to Iraq if they win the war against the U.S.
- Fixed an issue with the Iranian parliament event firing twice
- Fixed the French Aggressive Expansionism being non-functional due to a typo
- Fixed the colorization of Monthly Productivity Growth in the the Corporate Tax Rate being red when it is positive
- Added Belarus to the SCO Map Mode
- Fixed the localization error for the "Central African Republic Requests Support" to France
- Fixed the display error in European Council Voting
- Fixed the crash from the Egypt buying a carrier variant
- Fixed the positioning of the European Union GUI opening button so no overlap for players without La Resistance
- Fixed French focus about cooperation with the FSA
- Fixed the Merc SpecOps SandLine Unit template having a weird gap
- Fixed some missing localization for a couple random research bonuses
- Fixed game rules giving the illusion that they work
- Fixed broken tooltips in the Italian tree
- Fixed the 2007 EU Enlargement requiring a different law then it should
- Fixed the French focus tree for the extremists not being able to go the aggressive expansion position
- Fixed United Arab Republic autonomies disappearing after uniting it
- Fixed a bug with the U.S. not being able to annex its puppets
- Fixed equipment designer GUIs to be compatible with current update
- Fixed variable reference in EU
- Fixed a bunch of incorrect productivity values for nations
- Counter Terror "African/ME/Asia Influencer" now updates every time a recalculate is done
- Fixed a display bug with the Ba'ath party for Iraq
- Fixed an issue with the post war focuses for Iraq being unavailable if the U.S. collapsed
- Fixed the inability to be added to a Permanent Investment Target list for an AI nation
- Fixed an issue with Iraq continuously inviting France to their economic union
- Fixed Paradrop bug with aircraft
- Fixed a bug with quadcopter drones. No more internal bays for you!
- Fixed GFX bug with land doctrines
- Fixed a bug with Kosovo being unable to appease Serbs
- Fixed a bug when forming the USoE; the treasury should now actually gain money, and the Earth's orbit is no longer a wall of overflow satellites
- Fixed doctrine bug on long basic training
- Fixed a bug with air doctrine Dedicated Air Force Manufacturing: it no longer will super stack on small plane variants
- Fixed a bug in MIOs that was allowing overstacking of production debuffs
- Added missing General Dynamic company for US APCs
- Added missing XP to USN/USMC planes
- Fixed an error with US squadrons for players without BBA
- Fixed a graphic error linked to ships blinking/rotating

Content:

- The Communist Party of Cuba can now take the pro-LGBT policies
- Added HLS, SMA, MNC, ADO, and LIC to the possible European Member States
- Added a "Propose Mutual Investment Treaty" mechanic which should allow you to request AI nations to invest in you as well as gain a buff for investing in other nations
- Adjusted quadcopter production values to fix cost issues
- Improved French OOB, added 50 brigade names to their library
- Refined French and Russian starting stockpile

Graphics:

- Added unique graphics to the "Pillar of Counter Terrorism" and "French Foreign Legion" idea icons
- Added new Franch plane model for non-BBA players which already implement into BBA in 1.10.0
- New models for Germany
- New models for France
- Added some missing models/gfx to the NSB library

Game Rules:

- Added 1% and 1.5% for Influence Spread Gain to Game Rules

Localization:

- Added new and improved localization to the European Union
- Improved the localization for the Diplomatic Actions

Performance:

- Cleaned up more European Union display scripted localization that was not needed

Quality of Life (QoL):

- Added a notification to notify the player that an European Office is available
- Expanded the information available for each resolution
- Added a flow chart to the MD Wiki which is now viewable in game via the new "?" button

</details>

<details><summary>v1.10.0</summary>

Achievements:

- Added achievement It's All Françafrique to Me: "As France have all of Africa under your control"
- Added achievement the Return to Charlesfort & Ft. Saint Louis: "As Bourbon Monarchist France occupy South Carolina & Texas"
- Added achievement Truly Better than Napoleon: "Before the year 2010 have London, Moscow, Stockholm, Istanbul, Rome, Madrid, Cairo and Tunis under your control"
- Added achievement Ils sont le fléau des gens occupés: "As France become the sole superpower"
- Added achievement He who has iron, has bread.: "As Communist France have maximum spending on all laws except Police and Military, and all existing countries in Europe also be communist and subjects of France."
- Added achievement U AR Great: "United either the United Arab Republic or the Federation of Arab Republics"
- Added achievement Lawrence of Arabia: "As the United Kingdom, send volunteers to the United Arab Republic or the Federation of Arab Republics"
- Added achievement In fact, anyone outside of America is technically an A-rab: "As the United Arab Republic or the Federation of Arab Republics, be the only country in addition to the United States to exist"
- Added achievement Are You Sure That's Enough?: "Control at least 90% of Arab GDP before unifying the Arabs"
- Added achievement But In The Interest of Full Disclosure, I have to say, I hate A-rabs: "Defeat the United Arab Republic or the Federation of Arab Republics in a war"

AI:

- Reworked AI stockpile, production, and target templates
- Removed AI dump decisions to monthly tick - should increase performance negligibly
- Hezbollah should now send volunteers to Shia countries properly
- Added additional AI strategies to Greece for them to behave more logical
- Added new Naval Equipment AI Designs for North Korea
- Updated North Korean Naval AI to change fleet composition upon Reunification (They should go for a more Blue water navy than a Green Water Navy)
- Added Difficulty Based AI to European Union to the AI
- Improved AI for France so they should act more like France and not just chill in Europe
- Fixed Special Forces Doctrines AI not properly taking SF doctrines
- After the expiration of a office the AI will wait two weeks to give some room for the player to take an office
- The AI will now move to a different EU law if they recently failed a law
- AI will now try to push for the historical expansions of the EU on historical AI
- France should now intervene in Afghanistan alongside the other coalition partners

Balance:

- Increased Strength losses in combat by (around 2 times greater), to make losses more realistic and decrease amount of 0 losses in combat
- Added a Monthly Productivity Growth penalty to high corporate tax rate
- It is now a blocker that if you have 15% Chinese/Russian influence you can't join the European Union
- Government Popularity now provides Drift Defence Factor of more defence the more popular you are
- Decrease expected military spending for Emerging conservatives and neutral liberals by 0.5 - from 3 to 2.5 and from 2 to 1.5 respectfully
- Medium military spending(level 4) is now maximum expected spending during peace
- Gigantic military spending(level 6) is now maximum expected military spending during war
- Removed the treasury requirement from the Espionage system so you can bankroll it like other decisions
- Lower power ranking now has a penalty to Foreign Influence when influencing abroad (Superpower can influence anywhere without any reductions)
- Added additional game rule sliders for a number of new countries
- Added Army Personnel Cost increase to Night Vision techs
- Reworked the French OOB so it's closer to IRL strength. (Note: Conscripts and reservists not represented)
- Added a monthly Domestic Independence Tick to make Influence slightly harder
- Russian troops now start in siege position around Grozny
- Add the ability to bankroll the enrichment facility
- Changing government for Salafist on electing a Salafist
- Adjusted air base sizes by half (50 per level)
- Adjusted Wir Wing Sizes to (50 from 100 per wing)
- Changed lethality in air combat to account for Air Wing size adjustment
- Combined the naval techs for guns to streamline some MTG research (saves about a year, go figure ship go research)
- Increased the amount of money earned from international market purchases
- Low/High Price Points for the market are now implemented. Low decreases the cost by 20%, and high increases by 20%

Bugfixes:

- Fixed a bug when the opinion modifiers reached 100 or -100 due to an incorrectly configured decay
- Better focus filters for Wagner.
- Fixed Rojava Libertarian party name showing up as ROJ.Neutral_Libertarian
- Fixed AI not getting 2035 light tank hull template
- Fixed the event description of the Korean focus "Demand an End to America's Presence"
- Tweaked effect of the focuses of South Korean Aircraft caused by BBA dlc
- Fixed the focus effect of the United Korea Military Tree
- Fixed Polish event for Russia
- Fixed a requirement for Turkish spirit "Party Rumours" being visible to everyone in the political tab
- Fixed the Orchestrate Coup operation improperly checking for Salafist when it should check for nationalist
- Fixed Enrichment Facility bug not building three enrichment facility
- From now on "Putin Systimatic Protest" will remove in liberal Medvedev path
- Fixed Polish AI choosing conservatives political branch right before branch disappearing, causing AI to stuck forever on unfinished focus
- Fixed an error with the autonomy levels for parties nations that let them bypass country flags set in place for independence requirements
- Fixed wrong tt for China Mars colony focus
- Fixed the Infiltrated Asset tokens disappearing
- Fixed invalid starting templates for France and Ukraine
- Added a upper limit to HEU/LEU to a max KG of 2000000
- Fixed Maphilindo not being able to integrate Malaysia
- Fixed the Opinion Modifiers for Singapore not properly degrading
- Fixed a broken Austrian party icon config
- Fixed the starting setup for the releasable Kashmir
- Fixed the Export Value being "code language" until you click another screen
- Fixed no EU tree show up for Bulgaria
- Fixed some EU tree position to avoid collision
- Fixed wrong Bangladesh province error
- Fixed a Singaporean logic error in the focus tree
- Fixed a broken European Parliament icon
- Fixed Black Sea country trade path dead lock error
- Fixed Canada getting a free bumping to Neo Imperialism
- Fixed Armenian focus about NATO integration
- Fixed PLZ-05 from historical decisions having incorrect modules
- Fixed AI designing non-producible PLZ-05
- Fixed Canada leaving NATO if they are neutral
- Fixed Polish AI getting stuck while doing focuses
- Fixed Polish AI leaving CSTO in Korwin path
- Fixed employment modifiers not working correctly for offices
- Fixed Quebec completely erasing CAN cores on rebelling
- Fixed display error in GDP/C tooltip
- Fixed Malaysia being counted as a Middle Eastern nation instead of Asian in regards to power ranking
- Removed duplicate equipment variants from Egypt
- Added Answer events for Indian Proposal to U.S. to remove Pakistan from MNNA list Event
- Fixed a Somali nation starting with the wrong ruling party
- Fixed an inconsistency with the Senegalese Civil War
- Fixed AZE focus tree giving western drift instead of neutrality one
- Added attack helicopter category to land unit special forces recon doctrine
- Prevent North Korea from going down the nuclear focus tree unless certain conditions are met
- Fixed being able to get income from expenses
- Removed Finnish unique names from Japanese CV fighters.
- Fixed duplication of namelists on SOV Ships
- Fixed a Spanish event not firing properly for the Princess Cristina mini-crisis
- Added clamps for the percent so it's kept within 0 and 1 where 1 is 100% so as to not avoid outerbounding
- Fixed a number of bugs in focus trees related to planes
- Removed generic MIOs from nations that should have their own MIOs
- Fixed the missing text icon for attack helicopter battalions
- Fixed Iranian units being deleted during the civil war
- Fixed the Parliament no triggering correctly for Iran
- Fixed a continuous event firing after the revolution for Iran
- Fixed the Deals with China/Deals with Russia focus in VEN having the opinion being inversed
- Fixed a missing icon in the Syrian national spirits
- Cleaned up a tooltip for a San Marino investments to make it clearer

Content:

- NEW TREES: Kharkiv PR, Odessa PR, Serbia, Montenegro, Kosovo, Vojvodina, Cuba, Free States of America, Iraq
- NEW REWORKED/IMPROVED TREES: Donetsk PR, Transnistria, Lugansk PR, Belarus, Denmark, Norway, France, United States of America, Iran
- NEW TAGS: RYU, VOJ, CAB, LAG
- The Union state of Russia and Belarus gives more national spirits during the annexation
- Some decisions have been removed from the mechanics of the Russian subjects
- Remove TFV DOD WTT DLC Conditions due to PDX change
- Improved the content of the European Union and her laws
- Removed the Majority/Unanimity voting law types from the European Union
- Integrating a nation through Formable Nations will grant access to generals
- Annexing through puppet influence/annex will now grant access to the integrated nation
- Iceland and Greenland can now form the formable "Unite the Nordic People"
- Added extra tags which AI will use to divide Russia in case it loses war
- Added mechanic to reunify russia in case it becomes divided - expect it to come to other nations as well
- Merge MD PLA general resetting submod
- Reworked the United Arab Republic mechanic
- Subjects that default on their loans no longer get invaded by everybody, instead their overlord pays half the bill
- Standardised political parties in Arab countries so that Syrian and Iraqi Ba'athist always occupy the same slots
- Added new entries to historical vehicles decisions
- Improved Ethiopian tree relating to Somalia, allowing them to intervene in the region
- Added events to Somalia to make the Civil War more accurate
- Reworked the Somali starting leaders a bit so they're more accurate and gave them some traits
- Added the Casamance Event Chain to Senegal (very basic coverage of the content)
- Added new French Leaders/traits for existing leaders and several new generals
- Added content for Haiti and events leading to the Haitian 2004 coup
- Added the Second Ivorian Civil War
- Added the Central African Bush War/Central African Republic War
- Adjusted some of the Swedish tree with some benefits/adjusted the days on the focuses
- Custom Productivity setup for FRA
- Added Israeli Ship Namelists
- Added the Malian Civil War/Tuareg Rebellion
- Completely revamped US variants, starting production, and OOB
- Improved Russia equipment variants
- Improved France equipment variants
- Complete USA namelist rework
- Rebalanced and slightly tweaked Ethiopian-Eritrean war
- Add agame rule for Germany focus
- Reworked Moroccan politics and political leaders
- Reworked land doctrines for greater variation and more replayability
- Reduced air wing sizes for aircraft. Small / Medium to 50, Large to 25
- Adjusted air combat stats for air battle
- Adjust cost of aircraft frames and modules
- Removed interal weapons module for planes; added indivual internal weapon pylons
- Reduced air base size from 100 per level to 50 per level
- Condensed naval gun technologies for normal naval guns into a singular tech path
- Added the Casablanca bombing event to Morocco
- Reworked Land Doctrines to a newer more improved style
- Added quad-copter drones to MD
- Removed internal weapons module and replaced with individual weapon pylons.
- Added modifiers for income and cost from selling and buying on international market
- Added SigSauer to Switzerland
- Added three new continuous focuses: Temporary Intelligence Agents, Nuclear Energy Investments, Encourage Foreign Investments

Game Rules:

- Added a new "Enable Monthly Domestic Independence Tick" game rule
- Added a new "Monthly Domestic Independence Tick Amount" game rule

Graphics:

- Added the "Toofan MRAP" for Iran (2005 Inf EQP)
- Replaced the unit model for Russia
- SOV Political Rework (Reworked parties and leaders for SOV. New parties for Russia's breakaway tags and dynamic parties for potential Federal Subjects of Russia)
- Changed the order of the Chinese aircraft models to match the reality
- GFX Rework for USA, Russia, Italy
- Partial GFX Rework for France
- Half a dozen new rifle models
- More than 50 new plane models
- About 40 new ground models
- More than 15 new ship models
- New set of infantry for the Middle East
- 3 animated helicopters added each with their own unique sound
- Vehicle designer models and GFX rebuilt from the ground up
- Optimized the performance of many models
- Made key text icons more legible
- New ERI leaders and portraits
- Added party icons to much of the Western African tags
- Additional french models
- Reworked Law & Spending GFX

Localization:

- Added missing loc for tech categories research speed bonus
- Rewrote a number of the tooltips available in the European Union content focusing on usability
- Removed a large number of unused localization from the European Union files
- Add Simplified Chinese localization support
- Added a small tooltip improvement to the "hide/show" money button
- Romanized Iraqi political parties to be in Arabic
- Romanized Saudi political parties to be in Arabic
- Romanized Turkish political parties to be in Turkish
- Romanized Pakistani political parties to be in Urdu
- Romanized Azeri political parties to be in Azeri-Turkish
- Romanized Turkmen political parties to be in Trukhmen-Turkish
- Romanized Tajik political parties to be in Bukharian-Farsi
- Added new descriptions to the Ethiopian tree
- Added new descriptions to the French tree
- Updated the event loc for the Senegalese/Ivory Coast civil war events
- Re/Localised ETH and ERI political parties
- Fixed typos in a number of the technology descriptions
- Fixed and improved the localization in parts of the Comorosian content

Map:

- Revamp Iran region
- Revamp Somalia region
- Revamp Quebec
- Revamp Western Africa
- Revamp Japan
- Revamped Iraq
- Revamp Nederland
- Revamp Greenland
- Adjustment in Afghanistan
- Adjustment in Taiwan Strait
- Adjustment Qing dynasty border in province level
- Add Guardafui Channel
- Add Tai lake
- Add Biwa lake
- Separate Kuril isles to two part
- Grant a navy base for Lithuania
- Add Alaska railway
- Minor adjustment

Performance:

- Improved the hourly and daily tick rates of the mod by optimizing the European Union's decision categories
- Improved the load time configuration
- Simplified on actions so they're a bit quicker for lower end pcs
- Cleaned up some redundant stuff to help optimize save games to prevent corruption

Quality of Life (QoL):

- Added a game rule for colored puppets (disabled by default)
- Added Foreign Influence, Foreign Influence Auto Cap and Foreign Influence Defense to Configurable Toolbar
- Added shortcuts to a number of User Interfaces
- Improved the Expected Laws screen by adding a clearer informational on the main screen
- Moved all of the Middle Eastern music (Arabic, Israeli, etc) to the new music station "Breeze of the East"
- Added Euroscepticism to Configurable Toolbar
- Added a decision under the "Political Decisions" menu to auto-decline all corruption offers

User Interface:

- Reworked the Research Slot system to be a Custom GUI
- Reworked the European Union system into a Custom GUI
- Added a new music station "Breeze of the East" to encompass M.E. related music

</details>
