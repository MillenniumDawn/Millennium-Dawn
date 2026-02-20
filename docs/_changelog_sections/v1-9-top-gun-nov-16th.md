---
layout: default
title: "v1.9 'Top Gun' -- Nov 16th"
page_id: changelog-v1-9-top-gun-nov-16th
toc: "off"
order: 10
---

# v1.9 'Top Gun' -- Nov 16th

<details><summary>v1.9.6</summary>

Balance:

- Rebalanced the "Family Planning" cont. focus to 60% Monthly Pop, 40% Social Spending Increase
- Rentier State spirit now cancels if GDP from resource exctraction is below 20% AND resource exports
  income is less than 30% of Pop and Corp taxes combined (and you're not at war). The resource exports income requirement is the new addition.
- Delayed Polish ZKP-P events

Bugfixes:

- Fixed Central Asian investment events giving influence "backwardly"
- Fixed the International Investments rejection not working
- Fixed missing technology for the English Manpads tech tree for non-NSB owners
- Made Syrian tree of 2000 and 2017 unified in one file. Now after civil war is over, economic focuses will not dissapear. + Made branches visible.
- Remove all invalid technology tags for bonus
- Fixed central asian debt reducing focus giving 2 billion dollars instead of 20.
- Fixed AZE tree's economy branch being locked.
- Fixed Polish AI to loose Balance of Power and Communist Revolution

Content:

- NEW SHIP NAMELISTS: BAN, MAY
- Add Mari El Republic, Republic of Mordovia, Udmurt Republic, Chuvash Republic to the game
- Small rework of the SMO focuses in focus tree of Russia
- Rework of the PMC Wagner Tree
- Small update on the mechanics of the Warsaw Pact

Localization:

- Fixed U.S. Petro Dollar from being "Petrodollari" to "Petro Dollar"
- Corrected instances of "Civil War" being "Civilwar" in the Iranian tree
- Fixed a number of minor typoes in the tech trees

Map:

- Regroup Russian North Caucasian Federal District, Southern Federal District, Volga Federal District, Far Eastern Federal District, Northwestern Federal District, Siberian Federal District, Ural Federal District
- Make all Federal subjects of Russia(republics/autonomous oblast/autonomous okrugs/krais) got their own state
- Regroup Iraq states
- Separate Iran Kurdistan to three state
- Add one state for Cuba
- Minor adjustment

</details>

<details><summary>v1.9.5</summary>

AI:

- Simplified AI strategies, so it spends resources more naturally
- Made CHI/SOV/USA AI less willing to make unarmored divs
- Made AI less likely to spam Light Infantry units
- Late game AI should focus on armored units more
- Improved AI templates

Database:

- NEW UNIT NAME LISTS: AST, AFG, ARM, AZE, SPR
- Shifted 2000's non-MTG variants for ENG from 2017 to 2000 where they belong

Game Rules:

- Added a "Starting National Debt" game rule that will allow you to remove starting national debt
- Added "Red Dream" AI behavior for Poland to take communist path and Korwin/Wałęsa AI behavior to choose UPR/ChDRP trees

Balance:

- Decrease space taken in convoys by artillery, apcs, ifvs, tanks
- Reduced the time for holding "Emergency Elections" from 2 years to 1 year
- US Aid has been made cancelable on certain conditions as well as making you easier to influence by America
- Adjusted Prime Minister decisions in Iran so that you can't spam all of the decisions at once
- Increase combat width for all tiles by around 20%, Urban tiles are now almost twice combat width
- Added spirit Fight With Communism for Poland to prevent boosting communist parties without taking communist path

Bugfixes:

- Fixed "balkanized" shards of countries having non working economy and politics
- Fixed loc issue causing RAJ border war tension not showing up
- Made clamping of RAJ/PAK border wars on_monthly always instead of on change, should result in more smooth values
- Fixed incorrect coloring in the Labour Unions buff for Social Spending/Healthcare spending
- Fixed the last slot in both research slots not properly showing up
- Fixed the hidden ideas by mistake in the generic tree
- Readded the petro dollar because I don't know how to read the changes I make sometimes
- Fixed Australian leader name Alexa Ann McDonough
- Fixed Central Asian event crash
- Added Jack Layton as a leader for CAN
- Added Kostadin Kostadinov as a leader for BUL
- Fixed Estonian events improperly firing in 2000 for Albania
- Removed reward from auto-complete "New Alyiev" focus
- Fixed LPDs not being deployable on non-MTG
- Fixed the spamming of errors in the log regarding "Unknown Trigger Type", funny a graphic isn't a trigger? No, no one? Okay, I'll see myself out
- Fixed a handful of random errors for non-MTG regarding ship tech and non-available ship variants
- Fixed the Generic tree plane buffs not properly applying to the techs
- Fixed 8-cell SLCM VLS not being researchable if you are poor (I mean, do not own MTG)
- Fixed an edge case where you could have investment days go negative
- Fixed the modifier for investment_duration improperly increasing the days
- Fixed a missing idea check that is supposed to be an array regarding Unrecognized States
- Reworked the US-ROK alliance against North Korea's attack, it won't kick the US from the NATO now.
- Fixed the effect of the North Korea focus "Develop Food Factories"
- Fixed the passive GCC Unity threat not properly growing at tensions of 25%, 50%, 75%
- Fixed a bad variable call in the influence decision AI
- Fixed diplomatic actions not properly giving opinion buffs
- Fixed the "Attempted Coup on Us!" modifier going more negative instead of getting better over time
- Fixed the Arab League Member opinion modifiers not being properly being given (Sorry Mongolia, your Arabic dreams are no more)
- Fixed Ukraine not having 1985 anti-vessel missiles, but having them in designs
- Fixed South China Sea border conflict desicions mistake
- Fixed China Mars City event chain mistake
- Fixed the Iranian revolutionary content not giving access to IMIDRO, IROST, and Military focus trees
- Fixed the Artesh not appearing after Iranian Civil War
- Fixed the monarchist tree in Iran locking out half-way through
- Fixed the 'All the Shahs Men' focus not having any effects in Irans tree
- Fixed infantry models clipping into APC's
- Fixed KOR having 2025 artillery on game start
- Fixed channel and straight issue

Content:

- NEW TREES: Transnistria, Egypt, San Marino
- Added more foci to the German military tree
- New 'Balance of Power' mechanic for German militarization
- Updated Greece tree to add new effects + spirits, shortened focus times & fixed several bugs.
- Moved Venezuelan cartel tree to a more obvious position
- Fix focus in Finland's branch on joining the CSTO. Now Finland is asking for money instead of territories
- Some of the focuses in the Russian branch have been moved
- Now Russia is attacking Islamist Chechnya if it is starting revolutions in the Caucasus
- Added new PMC's to PMC Mechanic
- Added historical AFV designs for SOV, USA, GER, CHI, JAP, POL, UKR, ISR
- Reworked communist tree for Poland is out, alongside with Red Europe Pact faction and Department of Foreign Influence sub-branch
- PO and PiS focus trees in Poland can now be completed with social democratic PPS party in power if some requirements are met
- Added Game Rules for Transnitria

Graphics:

- NEW TECH ICONS: CAN
- Integrated some models from 'GEO Modern Models Mod for Millennium Dawn' (Thank you, Khahketi Kartli!)
- Added pictures to empty decisions categories (PMC, Missiles, & Political to note a few)
- Updated the background of the vanilla UI to be more consist with the MD style
- Poland's UPR party flag and missing focus icons are fixed

Localization:

- Improved Russian localization
- Fixed the Peruvian Submission focus name typo
- Fixed some typoes in the plane designer
- Updated the Arab League Member description
- Fixed a typo in the Game Rules "Sinagpore" to "Singapore"
- Fixed several unlocalized strings in the Greek tree

Map:

- Make Najrani Desert a separate state
- Make South Spratlys border with North Spratlys
- Add one new state in Cuba
- Some Germany state adjustment
- Eastern Iraq adjustment for US-Iraq war
- Minor adjustment

Modding Resources:

- Added automatic decision gfx generation to gfx_entry_generator.py
- Renamed starter Polish corvettes to ORP Grom and ORP Kaszub

Performance:

- Polish starter democratic branch will be hiding after choosing alt-history and vice-versa

</details>

<details><summary>v1.9.4</summary>
 - Droid's fuckup that he failed to fix even with a hotfix
</details>

<details><summary>v1.9.3</summary>

AI:

- Fixed some AI pathing in the Bulgarian tree regarding historical accuracy
- AI Bulgaria should no longer just instantly leave the CSTO if they choose to join willingly

Balance:

- Added a research speed debuff to Russia in the "Broken Economy" idea that decreases per level
- Boosted the Netherland's oil production in Oost-Nederland due to their natural gas production
- Rebalance combat stats for units & modules - more soft attack focus, tanks should have more breakthrough, but less defense
- Decrease recovery rate for all units by around 50%, decrease recovery rate bonus from cnc equipment
- Non power countries now will always have the lowest expected military spending
- Remove suppression bonuses from support units
- Add +0.5 suppression bonus to anti-mine afv module
- Simplified market calculations a bit as part of AAT fix

Bugfixes:

- Fixed (hopefully) most of AAT market related crashes
- Fixed an Indonesian bug where the focus prerequisite was not correct
- Fixed the focus "Support the Little Guys" in the Bulgarian tree
- Removed the duplicate Fighter Production Bonus in the French tree
- Fixed the "Abdication of Juan Carlos" event not properly switching Juan to Felipe for Western Autocracy
- Fixed the icons of "League of the Arduous March"
- Fixed the effect of the Korean focus "The C-295" and "Korea Aerospace Industries"
- Tweaked the require of the Korean focus "Offensive Approach"
- Fixed the tech "Fire Control System" mistake of Korea(South)
- Fixed research slot decision not properly checking the higher group of research slots
- Fixed insane buff from the repealing of the Jus Soli decision
- Fixed an issue with the Azeri 'Oppositions Broadcats' focus
- Fixed an issue in Afghanistan Taliban insurgency decision
- Fixed Canadian "Russian Arms Contracts" focus from improperly canceling due to improper conditionals
- Fixed cartels not disappearing properly preventing America from doing War on Terror stuff
- Fixed POL Balance of Power
- Fixed missing UPR party icon for Poland
- Fixed POL Visegrad tree not available as Polish European Federation
- Fixed "UH-60 Black Hawk" focus reward from attack to transport helicopter
- Polish focus "Artillery Modernization With The West" no longer requires to have NATO Member idea, which caused problems for players playing without NATO
- Fixed gaining income from expenses
- Fixed China having non-designable AA with NSB dlc
- Fixed the National Assembly Election Problem of R.o.Korea

Content:

- Added some bypass conditions in the Bulgarian diplomacy tree
- Rebalanced some things w/ the French tree
- Added a couple new events to Spain for some more content
- Fixed an issue with the Azeri 'Oppositions Broadcats' focus
- Rebalanced and retweaked some effect and time of the focuses of North Korea
- Make AcePilots events minor to avoid disturbration
- Make some event for China end war against Taiwan and Outer Mongolia with default result.
- Regroup greater China region news event
- Added a 100 day cool-down for those that resolve disasters in the Indonesian 'Disasters' Mechanic
- Buffed Indonesian PP gain
- Added focus for Russia - Foreign Intelligence Service
- Malorossiyan Russian Liberation Army(MOA) can now be created without launching a special military operation
- Added new mechanics of the Russian-Ukrainian War
- Added new trees for the Democratic Russia branch: Mikhail Kasyanov, Grigory Yavlinsky, A Just Russia
- Rework of the Democratic Russia foreign policy tree
- Improved mechanics of the Warsaw Pact
- Added new generals for LPR

Graphics:

- Added the Aircraft Icon Fix submod which gives more accurate plane icons (Thanks Wolfpack!)
- Fixed icons for Hezbollah

Music:

- Added "War in Kashmir"

Localization:

- Improved Russian localisation
- Updated French localization for the mod (Thank you, Zorkan!)
- Localized the description of the idea "Fighter Production Bonus"
- Fixed typoes in the Missile GUi with respect to the word Launcher
- Changed description for Polish decision "Buy AA Missiles" to better fit it's reward

Map:

- Add Orenburg Oblast of Russia
- VP Optimization
- River error fix
- Channel and strait fix
- Make Jan Mayen separate from Iceland

</details>

<details><summary>v1.9.2</summary>

AI:

- Fixed AI underflow from the International Market

Balance:

- Increased the workforce reductions from the AI tree
- Added additional research slots to help developing countries catch up
- Rebalanced the Spanish agricultural section to actually give benefits to agriculture
- Increased the buffs from the Autonomous Communities for Spain
- All of the culture opinions for Spain now provide a productivity modifier
- Added a productivity modifier to the generic idea Public Service Investment
- Rebalanced the Danish clean energy initiatives to make it a bit stronger
- Added productivity to the Education Spending
- As you annex a nation you now gain their enrichment facilities
- Removed the give Hezbollah factories decisions

Bugfixes:

- Fixed the Japanese "Kikai-ka Ryodan" hole in the template
- Fixed the Generic Focus "Economic Measures" taking away your 20% resource export income
- Fixed the Danish idea Last Bastions of Corruption were not being removed
- Fixed Comorosian idea for vanilla Export
- Deleted empty Indian focus "Bharat Sarkar"
- Fixed Indian idea for Local market trade
- Fixed the Investment System remove from array error
- Fixed the crashing issues relating to the market
- Fixed Fire in Baku Iran focus not being valid
- Fixed the Pahlavi tree in Iran having a bad prerequisite
- Fixed Hezbollah raid issues
- Fixed is_locked in Ukrainian focuses
- Fixed the AKP tree in Turkey being unavailable

Content:

- NEW FOCUS TREE: South Ossetia
- Added a "Canarios Targeted Subsidies" decision to Spain
- Adjusted conditions for Venezuela focuses
- Added "Petro Dollar" idea back to America
- Adjusted Turkey focus time lengths to be shorter

Database:

- Adjusted the "End Game" victory screen to spawn in 2100 instead of 2070
- Added renewable energy hotspots to Spain, Portugal, Morocco, Tunisia, Algeria and France in areas they hadn't already had one
- Added a Renewable Energy hotspot map mode
- Added hydroelectric power to Spain and Portugal

Localisation:

- Removed the localization in Assume Debt referring to influence.
- Added descriptions to the Danish political parties
- Added a description to the Missile Button similar to the other top bar buttons
- Fixed a number of typoes in the Spanish content
- Fixed typoes in the Venezuela tree
- Fixed typoes in some influence decisions and content
- Fixed Indian localization issues
- Added a tooltip extension to fuel to tell people to look at their energy screen for their fuel consumption.

UI:

- Added a "Average Worker Fulfillment" to the Economic Preview screen

</details>

<details><summary>v1.9.1</summary>

AI:

- Improved the AI navigation of the Generic tree to make it more optimal in padding its economic issues
- Improved the Bulgarian AI's navigation through her economic tree
- AI America and otherwise should not willingly accept corruption from Cartel Events
- AI should be more likely to accept assume debt since it's not a penalty
- AI Iran is more willing to fix it's economy
- Assume Debt AI now includes the value of a nation's interest rate since they are being given free debt assistance
- Improved the AI for the Internal Faction events so they're more intelligent of the choices
- AI Belarus is more willing to fix it's economy
- Adjusted some NATO joining AI
- Fixed the Greek AI from leaving NATO on historical focus
- AI now has the ability to invest fossil powerplants when the target country is negative energy balance, more likely the more negative it is
- AI now has the ability to invest renewable powerplants when the target country is negative energy balance, more likely the more negative it is and will only invest in it over fossil plants when you have lots of renewable power generation bonuses
- AI will dynmaically use the international market based on their economy size and if they are under threat of war or not
- Old MD EP system AI has been removed

Balance:

- Improved Tooltips for Germany to help explain mechanics better
- Removed Turkic Council spirit being given without acceptance.
- Rebalanced the German Renewable dynamic modifiers
- Rebalanced the Spanish Renewable spirits to be better
- Increased the worker requirement for China to offset their insane monthly pop growth
- Added a receiving investment duration/cost to Public Service Investment
- Booned the generic tree "Our Place" from 8% to 10% domestic independence
- Increased Combat Foreign Influence decision to 4% domestic from 2%
- Increased the energy boons from Bulgaria's economic sector spirit
- Fixed stability in the "Dual Currency Period" in DPR and LPR
- Reduced the war time mobilization by ~6% so it's a bit cheaper
- Buffed air attack of long-range missiles weapon module for SPAA designer by 15%.
- Increased the likelihood of positive economic growth events to help those nations in depression so people are aiming towards Stagnation as the main economic
- Infrastructure Investiture project now provides Network Infrastructure construction bonus
- Rebalanced cont focuses a little bit to be stronger
- Rebalanced the GDP/C scaling on the modifier "Monthly Population" to make managing Unemployment easier (Max penalty should be at 60k and it softens the penalty on poorer nations)
- Doubled the time of Military Aid influence action as to push out the influence gain more
- Fascists and Salafi Jihadists can go to Total War without needing to demobilize
- Increase the Ulema/Clergy/Priesthood Stability to 15% and their political power gain to 30% at max opinion
- Removed the "Max factories in State" from the Farmers
- Added Agriculture Productivity and Agriculture Tax Income to Farmers, having the faction gives you a flat 5% workers in agriculture
- Internal factions across the board have been rebalanced including new modifiers from a variety of different areas
- Increased the Unemployment Threshold modifier from Social Budget
- Rebalanced the "Small Company Lists Shares on Exchange" to scale to 4% of GDP instead of 5 flat
- Added starting productivity to Oceanic microstates
- Fixed effects in the Aviation branch of Russia
- Removed the national spirit in the weakened army in the Ukrainian branch
- Significantly reduced the amount of Mafia events you get as Turkey
- Rebalanced the Energy Sector section in the Generic Tree
- Made some tweaks to the Indian tree to make it a big more balanced and utilize newer modifiers
- Maoists rebels in India now reduce productivity in the state
- Rebalanced a number of Greek ideas and focuses
- Rebalanced Switzerland focus effects and ideas
- The minimum bailout you can ask is no $1 billion instead of $0 billion
- India's Petrol Refineries focus now gives Oil instead of Renewable Energy Infrastructure
- Boosted the construction speed of Renewables within the first 15 years of the game
- The "Intelligence Community" now provides benefits to those who have LAR
- Made the Cartel Mechanics more difficult based no your difficulty
- Decrease and rebalance expected spending somewhat
- Added an option for queuing 3 Enrichment Facilities at a time to help the QOL
- Removed the extra 90 day cooldown on building Enrichment Facility
- Rebalanced American Foreign Influence Defense penalty so America doesn't give up it's entire economy to foreign powers
- Reduced aircraft heavy naval weapons strength
- Adjusted Sweden's starting plane designs

Bugfixes:

- Fixed GEO going alt-history too much.
- Replaced ARM, BUL, GEO ideas and fixed bugs related to them.
- Added a "Do Not Cheat" message to people getting spammed by expired ideas on Germany. Stop cheating to overthrow the Republic!
- Fixed the inability to gain Urban Assault Specialists by fighting in Supercities
- Fixed "Governorates" in Russia Nationalist's tree
- Fixed a bug that prevents the branch of the Oligarchs of Russia from becoming Westerners
- Added stealth destroyers to MIO's with destroyers traits
- Fixed Chinese/Indian border was getting "stuck"
- Fixed German Bundeswehr Reform decisions not finishing if you got above 100% reform and not 100% exactly.
- Fixed Frigates not being able to utilize Nuclear Reactors (damn it birb)
- Fixed Renewable Energy Infrastructure being limited to 3
- Focuses that increase military spending not won't push you into needing to immediately demobilizing
- Fixed Salafist coup issues where you couldn't overthrow a country despite having 100% Salafist (haha pink typo)
- Fixed unit leaders dying but remaining an advisor
- Fixed Wagner Focuses in DPR and VTB
- Fixed the Ottoman path for Turkey not being made available
- Fixed the Turkish focus "Air Superiority Fighters" not giving a bonus to players with BBA
- Fixed the Hindus and Christians Butt Heads flipped option issue
- Fixed the Random Seed issue with the Maoist Indian decisions
- Fixed the Attempted to Coup Us! gaining negative opinion
- Fixed Turkish focus prerequisite where you couldn't go down the CHP path if you did "Maintain Headscarve Ban"
- Fixed China Mars city building event chain.
- Fixed the minimum days on missile production to always be 1
- Fixed an AI check in the influence actions for influence
- Fixed the Indian Join NATO to going to the faction leader if USA is not in NATO
- After forming Scandinavia, Integrate Finland decision becomes visible immediately like for other countries (even though Finland is not part of Scandinavia >:| )
- In order to start forming the North Sea Empire, you need to own the British Isles, not Finland
- Replaced a number of is_puppet checks to is_subject check to fix DLC compatibility
- Fixed the issues where Turkey/Iran/Ethiopia couldn't annex their puppets. Wow! That was fun!
- Fixed bugs related to the Union State of Russia and Belarus
- fixed one of the slots of medium aircraft not allowing medium GP hardpoints
- fixed a bunch of countries starting with nonBBA technologies when playing with BBA
- fixed a bunch of countries not having air forces at game start for non-BBA players
- fixed Russia not having an air force at game start for BBA players
- fixed initial aircraft carrier tech referencing an unavailable nonBBA tech while BBA loaded
- Fixed being able to send all designed equipment for dirt cheap convoy costs

Content:

- Added some bypasses to some focuses in the Conservative tree in Spain
- Added a debt refactor focus so the AI can "absolve" some of their debt
- Added a "Family Planning Cont Focus" increasing Welfare Spending cost and increasing population growth
- Added Nuclear Reactor to the investment system
- Added cosmetic tags for Turkish Kurdistan that will dynamically change with Turkish formables
- Added two new focuses for Myanmar to help their economic situation
- United Turkic States formable can no longer be formed by Tajikistan and Tajikistan can't be integrated into it
- Added two new economic events
- Rebalanced the triggering of economic events so people don't stay dying in depression
- Regroup China events, make country event and news event separate, Render unto Caesar
- Effects of some national spirits of Belarus have been changed
- Now there is an opportunity to play for the Prigozhin Uprising
- Removed MD Equipment Purchasing System, archived. May it rest in peace
- Added the International Market. It's in now. Please stop screaming about it.

Database:

- Changed the starting debt and treasury of KYR/TAJ
- Halved Nepalese debt to make them less dead

Graphics:

- Added a new token for patrol boat and heavy frigate
- Added missing supply hub 3D models
- Added missing icon for Peacekeeping Missions idea
- Changed event picture for news event China Vows Revenge
- Fixed the Intelligence Agency Icons for Brazil and Turkey

Music:

- Added "Mopikel - Technologies for Peace"
- Added "Mopikel - Industrial destruction"

Localisation:

- More cleanup in the loc files to remove unused localization
- Fixed typo in the air wing screen saying 50 planes vs 100
- Fixed typos for the word "Infrantry" to "Infantry"
- Fixed typos in the Bashkiria Focus Tree
- Fixed typos in the MIO Traits
- Fixed a ton of typos in the Tech files
- Fixed more typoes in the FIJ tree
- Fixed the Train 2030 typo
- Fixed grammatical errors in the Equipment loc file
- Fixed light tank gun being called medium tank gun
- Fixed collision in the Chechnya Focus Tree
- Fixed USA_all_aboard_amtrak desc
- Fixed Marine Commando Battalion desc
- Added party descriptions for Kazakhstan, Kyrgyzstan and Uzbekistan
- Updated Russian translation, added full translation of Germany into Russian
- Capitalized all of Self-Propelled Artillery and Self-Propelled AA in template designer
- Fixed and improved employment level button tooltips
- Improved tooltips surrounding battery parks/ energy storage
- Added party descriptions for Kazakhstan, Kyrgyzstan and Uzbekistan
- Updated Russian translation, added full translation of Germany into Russian
- Fixed several typos and missing localization across English localization files
- Fixed some typoes and standardized the english in the Myanmar tree

Modding Resources

- Added "State Renewable Power Generation Modifier"
- Added "Battery Park Storage Size Modifier"
- Added "Foreign Influence Coup Success Factor"

UI:

- Created a Productivity map mode so you can see the productivity of states easier
- Added total debt to the Debt tooltip
- Fixed an overlapping tooltip in the UI for the Expected Spending
- Expected Spending screen shouldn't be open on observe mode
- Added a tooltip to the Enrichment Facility button

</details>

<details><summary>v1.9.0 - 'Top Gun'</summary>

Achievements:

- Montenegro can now earn the Twogoslavia achievement
- Achievement "Gang is Back Together" can now be earned by JAP and ITA as well
- New Ribbon for Fiji: "Innovation Station"
- Several new and reworked ribbons for the United States

AI:

- AI will now use the MD Weapon Market - for now, only partially land equipment
- The AI will now respond more dynamically to Increasing Autonomy to help make it less CBT
- Made the AI more likely to suppress subjects if they have the ability to do so
- Made the AI more dependent on difficult for their focus on integrating subjects
- AI should now be more likely to accept trade agreements if they're a subject of the offering nation
- AI should no longer offer projects in states with full building slots
- AI should now more actively build infrastructure and network Infrastructure
- AI should now build trains and trains when they're okay on everything else
- AI countries who join the CSTO should no longer immediately leave the CSTO
- Georgian AI will now do the political focuses
- AI should now be a bit more aggressive in taking intelligence agency upgrades
- AI should pursue trade agreements a bit more aggressively post-2001
- AI should no longer spam militia
- AI should now be more aggressive when expanding its military if it is too small
- AI should now be more focused on making units rather than building stockpile
- AI should now be able to use more types of units
- Reduced the AI willingness to invest in Civilian Industry
- AI should no longer invest in projects that are greater than 700 days in duration
- Influence in a nation now plays more of a factor in accepting trade agreements
- NATO members should be more likely to reject Russia's trade agreements
- AI should be more likely to ratify historical nations for NATO
- Sweden and Finland should pursue joining NATO if Russia invades Ukraine or if they have caused more then 10% tension
- AI now also invests mils, docks, and network infrastructure (not just civs, infrastructure, and offices)
- AI now considers many more factors (like global and economic situations) when choosing which investment offer and which state to give a country
- AI now considers its military industry and decides what kind of air force to build based on its industry
- AI should be more aggressive with their air force
- Improved AI strategies for Poland
- AI should not build marines if it does not have dockyards
- SOV USA and CHI AI should not spam as many units they can't support
- AI should be more aggressive with their air force
- AI should be more trade-friendly with nations overseas
- AI should now properly respond when a nation takes a focus that grants a war goal on them
- AI should now select investment targets a bit more dynamically so they're not just doing random investments
- AI should no longer spam one country with a ton of investments (should make growth harder and spread investments over a larger group of nations)
- Syrian AI should be better at managing its debt now
- AI should more intelligently take corruption events
- Fixed the AI for North Korea forgetting to end the Arduous March
- POL AI will now more antagonize Russia and keep improving relations with CZE, SLO and HUN
- Improved AI for tech research for majors and minors
- The AI should no longer power buy MIOs causing them to bankrupt themselves
- Fixed the British AI always ceding the Falklands in ahistorical games
- The AI should no longer invest more infrastructure then you can have in a particular state
- AI should now longer take corruption offers if they are major/great/superpower
- AI India should occupy border regions if they're hostile
- AI India should more dynamically respond to its region and changes in the region

Balance:

- Azerbaijan is now Neutral state with Neutral Autocracy party
- Implemented global shared building slots in construction tech
- Starting factories and offices have been rebalanced due to changes in the GDP system
- Power ranking provides a reduction of interest of up to -1% as a superpower
- Removed the stability penalties from Nuclear Power and reduced Phase Out to 5% Stability
- Added production factory start efficiency growth and efficiency growth to difficulty
- Increased the income from Afghanistan Opium ideas by double to make it a more lucrative change
- You can add up to 10x the cost of missiles to speed up production
- Decreased Armored Infantry bonuses in plains and desert - from 15% to 5% to attack and defense
- Russian "Plausible deniability doctrine" will now bypass if player is already on Global Interventionism
- Russian "The Final Strike" focus will now bypass if Ukraine does not exist or is a puppet
- Decreased base reinforce rate from 10% to 5%
- Military spending now grants max production efficiency instead of factory output - total values unchanged
- Most if industrial techs now grant more factory output - but do not give max production efficiency - total values unchanged
- Bureau Laws now grant more Political Power Gain at a rate of 0.25 per level
- Bureau Laws now cost about 20% more so it's not so insignificant
- Nuclear Reactor techs should now give a progressive 5% construction speed to Nuclear Reactors starting with ABWR tech
- Rebalanced all equipment within foreign arms market (by changing price, quantity, and duration) to be roughly equal in terms of cost efficiency and production/IC they provide over time (resulting in most land equipment being buffed as it was much worse than buying air equipment).
- Nerfed Interrogation Techniques/Psychological Warfare/Diplomatic Training clamping their buffs at 50%
- Agency upgrades now take 100 days
- Most of weapon upgrades now increase production cost - usually by around 3% per level
- Decreased reliability penalty for many weapon upgrades
- Decreased reliability gain from reliability weapon upgrade
- Rebalanced existing weapon upgrades to make then more viable
- Removed unused weapon upgrades for trucks
- Removed attrition for Ukraine's "Home Of Chernobyl Zone" state modifier
- Removed Naval Doctrines from Operations for LAR
- Changed the IC cost of Train Equipment by -20%
- Removed the Tech Metal requirement from Trains and replaced it with Precious Metals
- Rebalanced the Joint Oil Ventures idea to provide 10% Resource Gain Efficiency and Resource Exports Multiplier and -5% in Corporate Tax
- Adjusted the infrastructure bonus in the investment system to give 15% buff to construction (matches it to normal construction) from the 10% (Bird forgot a variable to update icri)
- Adjusted the chances of success failure and coup in a nation
- Increased the Trade Opinion given from the "Propose Trade Agreement"
- Improved the logic for the investment system
- Reduced the stability penalty from "Our Neighbors Effect on Us"
- Reduced the stability penalty from "Government Popularity since Last Election" from -0.50 to -0.20 Max
- Removed all set_stability references in history files
- Buffed North Korea's "Hermit Kingdom" and added a Foreign Influence Defense Modifier
- Increased the starting corruption law of SWE/NZL/CAN/DEN to make them have "Slight Corruption"
- Corruption event that gave 200PP now has a dynamic PP reward depending on the power status of your country
- Adjusted air combat to be more lethal, both in air to air combat, and disrupted combat
- Increased air accident changes for aircraft with low reliability
- Adjusted air wing sizes for performance and combat balance
- Changed Agility to Radar Advantage
- Changed how air combat is calculated. Radar Advantage is significantly more important than most other stats now.
- Increased supply provided from air supply
- Entire US focus tree effects rework and reformatted under the new scripted modifiers system for ease of coding and readability
- Better divided the Societal Spirits of the US to be more digestible to read
- Adjusted some of the Internal Faction Events for more rewarding (or not) and allowed more to trigger more frequently
- Changed economic exploitation pp cost to 75 from 150
- Removed permanent stability loss from defaulting debt
- Set minimum factories required for consumer goods to 0
- Removed defence debuff from civil war military modifier
- Changes to naval system, with tweaks specific to CWIS and point defense systems
- Added a war stability buff to ISIS's starting Jihadist Islamic State idea
- Increased the autonomy reduction from the influence of decisions
- Increased the IC cost for convoys
- Rebalanced starting convoys to give a 100 x 25 per dockyard, and 1 train per every factory to help nations contend with their supply and energy needs
- Arab states get a little bit more money from exported oil and some more oil and more stability
- Rebalanced the academy laws to reduce the number of overall special forces one can have
- Rebalanced UAE's Little Sparta idea to give you less Special Forces overall
- All countries start with a set of "free" trait points relative to their MIO size
- Nation's now start with MIO's of different size depending on some conditions such as being in NATO, starting with defense industry, or their power ranking
- Increased the time available for Indonesia's disaster mechanic
- Changed Rentier State cancel trigger from too high corporate taxes to too low GDP share from resources
- Changed Nigeria's rentier state content to be related to the idea "Blood Oil"
- Removed 5% construction bonus from network infrastructure in favor of 5% local productivity (new system) growth bonus, per level
- Increased the higher carrier ratio positioning penalty
- Tweaked naval to air unit targeting
- Reduced the positioning gained from satellites because it could get OP way too quick
- When civil war starts, and country has less then 5 units, additional locked units will be spawned (to make in 5 total). They will be disbanded on war end
- Reduced opinion gain from Recently Invested from the investment system
- Fixed the decay on Gave Economic Aid and Granted Bailout so they aren't just perma buffs to opinion
- Dialed back the bonuses to the AI on Elite, Hard and Normal due to improvements in Economic Handling

Bugfix:

- Fixed Armenian SA-2 GOA buying focus giving money instead of taking it
- Fixed Armenian focuses not bypassing with certain conditions
- Fixed carrier over stacking for Light Carriers (stupid fucking bug)
- Fixed a bug in the tooltip for Socialism's banning button tooltip
- Fixed Fan the Flames in Baku focus in Iranian tree (There was a tooltip error in the requirements).
- Fixed the GDP/GDP overflow from too many buildings
- Fixed an error in the Sphere of Influence focus for Iran
- Fixed an exploit where you could swap missile production to a newer version and gain the newer missile
- Bunkers, Coastal Bunker, Railways, and some other provincial buildings now get infrastructure construction buffs
- Fixed an error in the Spanish tree regarding the Andaluces not being properly removed
- Fixed missing domestic tag for Macau, to fix wrong flag issue
- Fixed Macau party name display error
- Fixed USA Marine template having a 'hole' in it
- Fixed ENG armor template having two recon companies
- Fixed Ukrainian "Deploy Ter Defense Brigade" decision not deploying units
- Fixed South Korea would let USA join the alliance called "US-ROK Alliance" no matter USA is in NATO or not
- Added Religion, Rates and Internal Factions for Chinese S.A.R.
- Fixed a missing clear variable for Cartels making them pesky cartels coming back
- Fixed non-MTG English frigates being destroyers
- Fixed having Simeon 2 and Island Warlord traits for random characters
- Correct 2017 CHI & MON leader
- Fixed missing localization for the Kamikaze drone
- Fixed missing for ENG, GER, & FRA in the Equipment purchasing system
- Fixed the Suez Canal Authority and Partial Control of Suez ideas not properly removing/being added
- Fixed an Italian event kicking back the Cartels preventing you from removing them again
- Fixed being able to fire missiles without a strike type thus dealing no damage
- Fixed the missile system giving blank/no damage reports after the first missile strike
- Fixed the Indian intelligence agency icon not working properly
- Fixed Korea join UNSC Event
- Fixed Georgia not doing political stuff
- Fixed an error where a state modifier was granted to the wrong state for Indonesia's "Back No One" path
- Fixed a localization error in the description of a Swedish political party
- Fixed the AI immediately revoking satellite access after giving it to another nation
- Fixed investment durations not being properly calculated
- Fixed regional powers with no investment targets from checking whether they could send investments
- 1% fee on debt borrowed is also now taken when debt is borrowed automatically, not just manually
- Fixed Chinese templates causing a crash
- Fixed Chinese Type-89 having unmanned turret instead of default
- fixed economic exploitation not properly taking political power
- Fixed China not having armor MIOs
- Fixed a missing check for the Coup button
- Fixed China's "ban solo travel" decision
- Fixed max opinion from Improve Relations value being 50 instead of 100
- Fixed bankruptcy events taking your last civ
- Fixed ISIS spawning with no tax rates
- Fixed getting influence on yourself from the Combat Biggest Influencer decisions
- Fixed Indonesian buildings not actually giving you a building slot
- Fixed modifier icons not showing up in construction speed modifiers
- Fixed Polish voivodeships names
- Polish party UPR is now in nationalist section, instead of neutrality
- Fixed some Commonwealth of Nation member country without Commonwealth idea
- Fixed a number of smaller errors in the Indonesia tree to improve the flow of the content
- fixed a bugged define where you can just one tap ships much more frequently then otherwise should
- Fixed Austrian party icons from being broken and not visible
- Fixed Albanian party icons from being broken and not visible
- Fixed the duration of an investment being able to go negative if you had a really low construction speed
- Fixed an Internal Faction events being fired for Intelligence Community and Oligarchs
- Fixed is_puppet_of requirement to being is_subject_of requirement in the Economic Exploitation check
- Fixed the decay on Recently Invested from the investment system
- Fixed a weird edge case bug where if you banned all parties but fell below your election threshold you would elect "Western Autocracy" instead
- Fixed Chinese focus "Expand Abroad" from locking you out if you decide to go mass global exports too early
- Fixed missing helicopter technology for Ukraine
- Fixed Bangladesh not being able to boost Islamic parties
- Fixed the remove Saudi Aid decision not showing up for non-Middle Eastern nations
- Fixed ASEAN nation's not being able to use the cartel mechanics when they should be able to
- When India get no core on Aksai Chin, the border conflicts decision between China and India over Aksai Chin will not show up

Content:

- NEW FOCUS TREES: Turkey, Estonia, India, Fiji, Malorossiya, Bashkiria, Wagner(Sahel Confederation), DPR, Central Asian Shared Tree, Venezuela, Hezbollah
- REWORKED/IMPROVED FOCUS TREES: Germany, Iran, Denmark, United States, Poland, Russia, Belarus, Chechnya
- NEW NAMELISTS: EST, LAT, LIT, POL, VEN, HEZ, FIJ, PER, TUR
- New Naval Doctrine "Jeune Ecole" which focuses on light ships (Unlocks the two new unit types, Heavy Frigate and Patrol Boat)
- All new air doctrines for JSEAD, Light Aircraft, and strategic destruction
- All new specialized special forces doctrines for Paras, Airborne, and Air Assault
- Added new unique Italian MIOs and some content related to them
- Reworked Cyprus mechanic
- Adjusted several Greek focuses & decisions to match with the new Cyprus mechanic rework
- New Parliament (Majlis) mechanic for Iran
- Banning parties now prevents a party from being elected
- Now you will have 180 days cooldown after invoking Article 50 in EU (to prevent use again Article 50)
- New interaction event chain between Revolutionary Iran and Ba'athist Iraq
- Decoupled the Missile System from requiring civilian industry to produce missiles (it is now only money)
- Rebalanced a number of Canadian ideas to make the energy/economic stronger
- Implemented a system for Energy and building energy consumption
- Implemented a system for unemployment/labour rate.
- Implemented a system for productivity
- Changed the function of how Nuclear Reactors/Nuclear Material is produced
- Canada has some more buffs to certain focuses
- Adapted all trees to the new energy/economic rework
- Fossil Fuel Building is investable
- Add 9th Jebtsundamba Khutuktu event&decision chain to accelerate the progress of Outer Mongolia SAR establishment
- Add Scarborough Shoal dispute, with CHI focus, decision and event adaptation
- Add decision for CHI to develop southwest hydroelectricity Projects and high speed railway
- Add Natuna Isle focus for CHI, with event adaptation
- Patch new added China focus to ai_strategy_plans
- Small tweak for Japan Focus to add correct claim and goal for invade mainland China
- New terrain type: supercity - combat width 141 plus 47 per extra attack direction, existing units updated for new terrain
- Add new combat phase for Urban and Supercity tiles
- Added an Air Base to Northern Finland
- Updated and corrected USA Naval starting Fleet for 2000
- Updated and corrected CAN Naval starting Fleet for 2000
- Added proper and accurate upcoming ship names for US Navy
- Updated USA Army starting Divisions and designs to reflect proper data (old set up was using 2003 Invasion of Iraq info for starting divisions)
- Reworked political parties for Albania, Austria, Haiti, Scotland, Wales
- Added an Investment Auto-Reject Feature
- Added a game rule to enable the help GUI so we stop getting reports about it
- Added Office Construction Speed for Captain trait
- Add icon for Democrats party of Mongolia
- Add a small trait for Chinese Leader Jiang Zemin
- Disabled techs with decryption/encryption if you have LAR DLC
- Added an "Assume Debt" diplomatic action where you can take on 25% of another nation's debt
- Added an autonomy bonus if you grant a bailout to your puppet
- Granting a bailout gives you some opinion now
- Add seven TAG for republic of Federal subjects of Russia: Adygea, Altai, Ingushetia, Karachay-Cherkessia, Karelia, Khakassia, Komi
- Add four TAG for Autonomous Okrug of Federal subjects of Russia: Chukotka, Khanty–Mansi, Yamalo-Nenets, Nenets
- Add Gagauzia TAG for Moldova
- Add Karakalpakstan TAG for Uzbekistan
- Add Wagner TAG for Wagner(Sahel Confederation)
- Add Badakhshan TAG for Tajikistan
- Add Sikkim,Khalistan,Kashmir,Kamtapur,Manipur,Meghalaya,Ladakh TAG for India
- Add North Shan state,Rakhine State,Chin State TAG for Myanmar
- Add Faroe Islands TAG for Denmark
- Arrange flag of new added TAG
- Regroup Pacific minor countries, make Federated States of Micronesia at right place.
- Add Palau, Kiribati, Marshall Islands, Tuvalu, Vanuatu, Tonga, Nauru to the game
- Convert Polynesia(PLY) to Samoa(SAM)
- Slight adjust exist Pacific minor countries
- Finish China Moon base building event chain, and make it as a precondition of focus CHI_mission_to_mars
- Finish China Mars city building event chain, and make it as a precondition of focus CHI_mars_colony, slight increase focus`s reward
- Iran's revolutionary focus tree has been reworked entirely
- Added weapon upgrades for Infantry equipment, CNC equipment and trucks
- Made the Ba'athis Iraqi's Right-Wing populists instead of military junta
- Made the Sadrist neutral conservative instead of Right-Wing populists
- Added new Expected Spending and protests mechanic
- Updated Royal Navy, US Navy, and Canadian Navy to properly reflect naval OOBs as of year 2000
- Custom autonomy level for Danish crown holdings
- Reworked politic setup for Denmark
- Completely reworked the print money button, making it useful in certain situations
- Added Plane Designer and all associated airframes / modules
- Reformatted Libertarian, Reform, Green & Progressive Party trees into a more fluid focus tree layout, 60 day completion, 40 focus count
- Expanded political, military and economical content for Poland
- Added a core to New Caledonia for France
- Added new foci to the Generic Focus Tree for labour mechanics and the energy sector
- All trees should now prompt a "x is justifying against us" tooltip if they're taking a focus that gives them a war goal on the target
- Added a focus called Debt Refactoring to Bulgaria to help them from being tag-teamed by America and Russia
- Added light tanks, tank destroyers and armoured cars designer
- Added self propelled anti air vehicles designer
- Added mp decisions to delete starting units and set tech level to USA
- Added idea "The Rubber Baron of Africa" to Côte d'Ivoire
- Added a demobilization mission if you have Huge Mil Spending or Higher without an ongoing war
- Added starting opinion modifies of Large Commercial Relations and Historic Friends to POR and ENG
- Added a starting guarantee relationship for POR/ENG. NATO still supersedes
- Tony Blair now has some unique traits such as Career Politician and judiciary
- Added a new continuous focus called "Bread & Circuses" to help boost productivity growth
- Removed older decisions regarding sending volunteers to certain places
- Added a small sub tree for Singapore to deal with energy content
- Added modifiers for workforce to Migrant Workers mechanic to Singapore
- Added state specific wind power modifiers according to realistic values
- Finland can join NATO via their focus tree if they choose Sweden or Germany now

Database:

- Changed America's starting trade law
- Changed Saudi Arabia's starting trade law
- Reduced a number of nation's starting military spending for overall game stability
- Added the USS Missouri to the Decommissioned Battleships Flotilla for the USN
- Adjusted the starting OOB for Venezuela
- Added Rentier State as a starting idea to Bolivia, Cameroon, Papua New Guinea, Sierra Leone & Uzbekistan
- Removed Rentier State as a starting idea from Algeria, Australia, Congo, Indonesia, Iran, Kurdistan, Nigeria, Norway & South Africa
- Removed starting military access for NATO members since they're a faction and if you leave NATO you probably don't want NATO troops in your country anymore

Game Rules:

- Added a game rule to allow you to block AI from using the Increase Autonomy cont. focus
- Added scrollbars to weaken/strengthen countries with the newest game content.

Graphics:

- NEW INFANTRY (3D) MODELS: IRQ, POL, BOS, SAU, RAJ, SPR, UKR, PER (Revolutionary), BRA, MEX, TAI, GRE, AFG, TAJ, BLR, & VEN
- Major countries should no longer have SOV gfx for AFV and SPART hulls in tech tree
- Fixed some missing graphics from Ukraine
- New political icons for ALB DEN CZE CYP KOS MNT POR SER SLO SOV MLW COL FIJ VEN NCY
- Added M10 Booker as 2025 light tank for USA
- Added a new graphic background for the MIO research screen
- New political leaders, focus tree icons and balance of power icons for Poland
- Fixed a number of missing Denmark graphics for event pictures

Localization:

- Cleaned up a number of non-used localization
- Added a tooltip to the "Subjects" header so you can understand what exactly is going on with your subjects
- Fixed loc for SPY window
- Fixed a number of small typos and that in the missile system
- Added a number of descriptions to Canadian ideas
- Ukrainian "Deploy Ter Defense Brigade" now shows current number of trained brigades
- Added expanded descriptions to the Military Spending Laws to explain where the estimated law cost comes from
- Corrected Alfonso Portillo's name being misspelled
- All laws should now have descriptions of some kind to give them some additional flavour
- Corrected a typo in the Time to Complete Investment
- Corrected some capitalizations in a Nepalese event
- Updated debt tooltip to mention that a 1% fee associated when borrowing debt (manually and automatically)
- Corrected debt tooltip to say you can't manually borrow after 20%, not 25%
- Fixed a typo regarding the Greek Vehicle MIO
- All generic tree foci should be localized now
- Corrected misspellings for Poland
- International Investment Reinvestment enabled loc now turns green when enabled
- Fixed typo in cartel decision from Propganada to Propaganda
- Wrote additional descriptions for Danish ideas and focuses
- Fixed the tooltip for Salafi Jihadism and Muslim Brotherhood not telling you a hidden conditional
- Fixed some typoes in the influence decisions and events
- Fixed several localization errors.
- Cleaned up spelling in most english localization files

Map:

- Added a new terrain supercity (this represents large megacities such as Los Angeles, Shanghai, Delhi)
- Add Lienchiang( Matsu )
- Adjustment for state border and VP
- Add Eg river and Khovsgol Lake
- Separate Chongming island from Shanghai city province
- Fix Sweden province problem
- Fix river cross in Himalaya region
- Adjust the population in Kashmir region
- Add forest for North Iran
- Adjustment for San Marino population
- Small adjustment for Kosovo
- Terrain changes in Northern Iraq
- Changed the colours of the following tags so they're easier on the eyes: SNA, IND, KAC, SHN, KAR, WAA, BRU, FIJ, QTF, SEL,TUA, SCO, WAS
- Remap western UKR to fit Austria-Hungary border
- Remap Himalaya region and India northeast region
- Remap middle POL to fit 2nd Reich border
- Remap Pamir range and Fergana region border
- Regroup strategic regions, port some new regions from maintree to avoid amphibious invading problem
- Add shark infested for some sea region. Beware, Admirals!
- Create separate Sevastopol Bay from Crimea, and adjustment for strategic region
- Separate Java Isle to four states to fit current administration border
- Separate Nauru and Kiribati
- Create Tonga

Modding Resources:

- Added a quick "ban_party_scripted_call" quick script
- Added a quick "unban_party_scripted_call" quick script
- Added 15 modifiers for speeding up the production of missiles
- Added two new effects "one_random_fossil_fuel_powerplant" and "two_random_fossil_fuel_powerplant"
- New modifiers for productivity
- New modifiers for energy system
- Added modifiers for each individual resource type export income
- Added scripted effects for every 'number'_random_'building'. You can use 'number'_state_'building' in state scope to add building to that state.

Performance:

- Reduced the number of scripted loc calls to improve runtime performance
- Implemented a refresh variable for the subideology screen
- Implemented a meta_effect yearly trigger to optimize the on_monthly
- Removed a number of not needed on_actions to help optimize the monthly tick

Sound:

- NEW VOICELINES: SPR, TUR, FRA, ITA, SOV, RAJ, ENG, USA, GER, & CHI
- Adjusted the Armenian voicelines so that they aren't earraping you
- Removed the Pandur rocket noise, which would fire repeatedly even when zoomed out

UI:

- Subideology screen now closes with the political tab vs free floating
- All Attack/Boost/Allow/Ban buttons are visible always so you can always view why or why you can't click a button
- Added and implemented blueprint graphics for a large number of nations, including; Germany, America, Ghana, Israel, France, Italy, Poland, Brazil, China, and the UK
- Added a customizable counter UI that lets you display a whole variety of things on your screen at all times conveniently (like net income, specific resources, and casualties). All thanks go to stjern from the total war mod for letting us use it!!
- Added a container that displays the Resources to Market value in the Trade Screen
- Added additional in the Investment Offer event to show you more details such as the duration of the project
- Added priority to North Korean decisions so it's higher in the list so it's not lost in a sea of generic decisions
- Fixed the UI bug with Navy Experience not filling out its text box
- Fixed the display issue with the auto-influence cap
- Tethered the Ideological powers screen to close with the political vs free floating
- Introduced a dirty variable to help performance on the ideological powers screen
- Added a "Disable Monthly Auto-Influence Report" monthly event if required
- Added a display for your auto-influence nations in the influence decisions

</details>
