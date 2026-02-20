---
layout: default
title: "v1.7 \"Make Millennium Dawn Great Again\""
page_id: changelog-v1-7-make-millennium-dawn-great-again
toc: "off"
order: 8
---

# v1.7 "Make Millennium Dawn Great Again"

<details><summary>v1.7.5 - Hotfix</summary>

Balance:

- Now International Bankers are using new Foreign Modifiers (cost and duration)
- Rebalanced some generic focuses
- Ethiopian War ends with both ERI and ETH "demobilizing" (They go down to 2 and 3)
- Added additional focus to assist Ethiopia in economic management

Bugfixes:

- Fixed broken recruitment officers for some releasable nations like California, Texas, New England, CSA
- Fixed broken army icons for Armenia
- Auto-influence now correctly deletes a nation if it no longer exists
- Fixed broken EU focuses
- USoE should inheriting missile stocks, nuclear weapon stocks, satellites from member states
- Fixed a bug in Ethiopian focus "Request International Loans"
- Fixed a bug in the Influence Actions logging (?? vs ?)

Performance:

- Eliminated unneeded checks in influence system to optimize calls

Content:

- Ledger integration for players
- Added agriculture mechanics for various African nations
- Added literacy rate mechanic for all of Africa

Game Rules:

- Allowed the disabling of the ledger for more competitive play

Localization:

- Added Initial Investment Cost to all 15 investment projects
- Added a ID note in the investment decision descriptions for better debugging
- Added some Localisation for Spain

Performance:

- Eliminated unneeded checks in influence system to optimize calls
</details>

<details><summary>v1.7.4 - Jan Patch</summary>

AI:

- Made attempts to stop the AI making such dumb borders
- AI should no longer liberate countries that don't exist
- AI will return core territories of countries that _do_ exist
- AI is better setting up productions
- Russia is more dangerous at sea
- AI of China now begins to build military factories from start game
- Economic AI now takes into account stability in the country and the number of affordable factories with increasing taxes
- Economic AI active rule now puts priority to solve problems in the economy and corruption

Balance:

- Changed some starting Canadian modifiers
- Rebalanced peace conferences to cost more the higher the difficulty
- Rebalanced the Economic Cycle laws (less construction speed)
- Rebalanced the likelihood of the "Major Financial Instiutions" event occuring
- Rebalanced some of Swedish focuses

Bugfixes:

- Fixed Yamassoukro map error
- Disabled MD unique Embargo function in favour of the vanilla
- Fixed releasable tags now can use the equipment purchasing system
- 2017 start date should no longer crash without NSB
- Fixed position for ideological power button, now this one don't should cover autonomy line
- VLS Surface-attack 2015 now it's 2015 technology instead of 2010
- Fixed bug when Denmark could forcibly join countries to its faction
- Fixed wrong any other additional income for Iran when he has Black Market Exploits
- Now player can see why full requires for Armenian focus Uniting Opposition
- Fixed the Ukrainian civil war firing twice
- Fixed an event for an Spanish event not firing
- Fixed wrong years in Bomber Aircraft Tab

Content:

- Syrian attempts to cause an intifada will see ISR and PAL retain cores over Gaza
- Added auto-influencer functionality

Localization:

- Updated localization for Spain
- Updated localization for Canada
- Fixed missing localisation for Greek Focus "Foreign Relations"
- Fixed missing localisation for CnC equipment research bonus

Performance:

- Performance Improvements for Neighbour Effects (should make the game 2% faster)

Modding:

- Added new modifier "foreign_influence_auto_influence_cap_modifier"

</details>

<details><summary>v1.7.3 - Next Patch</summary>

Balance:

- Rebalanced several African nations starting positions to keep them from early game bankruptcy

Bugfixes:

- Fixed tank upgrades without NSB dlc (hopefully)
- Fixed bad localization call in Ivory Coast news event
- Fixed New Turkish Submarines using the wrong hull type
- Fixed display issue in the GDP/C dynamic research slot system
- Fixed 5-year-plan decision effects for resource gain efficiency and offices
- Fixed bad unit definitions in USA's
- Fixed Wagner Tank PMC Purchase
- Fixed decision visible for ZSR
- Fixed tooltip for ZSR nationalization

Content:

- Victor of the Ivory Coast Civil war should now become Ivory Coast again

Graphics:

- Added 4 new generic portraits
- Fixed Polish Portrait Errors

Localisation:

- Better localisation for 5-year-plan decisions

Performance:

- Removed unneeded dynamic calls in subideology window

Quality of Life (QoL):

- Debt/International Investment Container in Budget Tab now support the same functionality as the top bar
- New map modes: SCO (Shanghai Cooperation Organisation)

</details>

<details><summary>v1.7.2 - Halloweenie Patch</summary>

AI:

- Russia no longer attacks the countries of the former USSR if they are in NATO, until 2016
- Russia no longer attacks the countries of the former USSR if they have guarantors from China, until 2012
- Russia no longer attacks Azerbaijan if it has a guarantor from Turkey, until 2016
- AI now knows how to properly distribute military plants for aviation production
- AI received new army templates.
- AI will now pay off the full amount of their debt should they have the money available
- AI should now properly reject economic aid
- AI will now send his tank armies to the mountains less often. And in general, AI will now not send troops to slaughter in an unsuitable area
- A new game rule for economic AI, which removes restrictions on the adoption of economic laws

Balance:

- Updated the popularity drift from operatives
- Increased Defense for "No Turret" tank turret type: from 4 to 8
- Decreased conversion cost of "No Turret" tank turret type from 2.25 to 0.75
- Made tank hulls not producable by default (experimental change)
- Reduced Manipulate Politics influence cost from 10% to 5% loss to make it more useful
- Cost tweak to policies so they're slightly more expensive
- Adjusted some nations starting tax rates
- Balanced several italian modifiers, added a couple of recurring decisions

Bugfixes:

- Fixed NATO sharing group if NATO disabled due game rules
- Fixed Resource Exports disappearing if you lease factories
- Fixed missing upgrade for Air Superiority Fighters
- Fixed American Naval OOBs so they didn't get 2015 modules in 2000
- Fixed a CV MR text icon error
- Fixed missing localization for Production Cost Max modifiers
- Fixed PMC's trying to spawn units with non-existing c&c equipment
- Fixed wrong number of max planes in airwing menu (instead of 100 from vanilla now 50)
- Fixed broken localisation for revolts in Spain
- Fixed broken icon for focus Spread Right Wing Propaganda in Spanish Focus Tree
- Fixed issues with the North Korean Focus Tree
- Belize, Northern Cyprus, Cyprus, Bahrain, Hezbollah now have gifted income to avoid debt shit
- Fixed strange effects tooltip in event IMF Demands Land Reform
- Fixed missing technologies for Liechtenstein, Mexico and Germany
- Fixed decision to reduce autonomy don't disappear if you lost puppet
- Fixed prerequisites in decision Replace Saudi Arabia as Leader of the GCC
- Kuwait now don't should have completed focuses in 2000
- Fixed decision for China to reduce autonomy in Hong Kong
- Fixed Korean Unified idea It wasn't modifying correctly due to bad variable names
- Fixed Chinese Focus Zhejiang Megacity Project
- Removed Uzbekistani divisions in Kyrgyzstan in 2000 scenario
- Added bypass for British Focus Develop Infrastructure
- Fixed GCC Focus Mass Deportation
- Fixed Spanish communist everywhere decision (Commies needed to be in coalition to work)
- Fixed weird tooltips with influence changes (was 2 same countries)
- Fixed pending investment offer bug (You can no longer spam players with investments and they need to be accepted successively.)
- Fixed graphically bug where limited invested buildings would give you the false hope of being buildable at 10 when there can only be 5
- Fixed T-62 cannon and reloading type
- Fixed AWACS graphics for all nations
- Fixed the MBT7 for India
- Fixed the error spam from the peace conference
- Fixed an error spam due to a bad unicode character
- Fixed a bunch of non-MTG errors in the OOBs
- Fixed the 2017 SOV NSB file
- Fixed duplicate triggers about SCO ideas for Officer International Training law
- Fixed missing localisation for insult opinion modifier
- Fixed decision Move our Embassy to Jerusalem
- Fixed terror threat change for focus The Salafist Rise

Content:

- Increased cost to drill oil for China
- Increased cost to make anti DPP campaign
- Chinese Tourism Restricted idea now also should add additional expenses
- Buffed idea The Four Asian Tigers Legacy
- Various changes for GCC focus tree and decisions
- Various changes for Chinese focus tree, decisions and ideas
- Rebalanced some effects for Chinese STE decisions
- Modules and other minor techs now can have XP dumped on them for tech bonusesgi
- Added new Naval Doctrines for Bluewater and Greenwater Navy
- Rebalanced decisions to encourage/deport migrants for Gulf countries
- Updated Jamaican political parties
- New tags: CSM, FNC
- Ivory Coast & Senegal event chains
- New Political Party icons for most Arab Autocrats in Africa
- New political parties for SHA, MAU, LIB, SIE, GUI, BFA, GUB
- New starting political setups for AFG, AGL, BFA, CDI, GUB, GUI, LIB, LUR, MAU, NAM, SHA, and SIE
- New Equipment Purchasing System to replace decision menu (button can be found in political menu)

Focus Tree:

- Tweaks to the American Focus Tree
- Added Libertarian Tree within the Reformed Republic added content teased in 1.7's release
- Improved Generic Tree (Added new focuses and rebalanced some stuff)

Graphics:

- Changed the Office Sector building to be a light blue so it's more obvious when it is available
- Additional models for various countries and some bug fixes to them
- Fixed poorly sized portraits
- Added icons to ideas missing pictures

GUI:

- Better position for things in topbar
- Fixed the Ship Filters section in the naval production screen
- Fixed interface in Naval Intel Ledger
- Small interface tweaks in country view window

Localisation:

- Improve localisation for Rentier state - include information on when it will be removed
- Various improvements in EU focuses localisation
- Adjusted localisation for SOV cannons
- Some localisation fixes in User Interface

Modding:

- Introduced four new custom modifiers for content purposes

Performance:

- Optimized on_startup on action so the game should load in faster
- Optimized the Investment System UI so it should run smoother in game

Quality of Life (QoL):

- Added Project Count to International Investments Tooltip
- When laws are blocked it now shows you the duration until you can change again
- Added a scrollbar to technology description
- Rewrote most of the tooltips for the Investment System so requirements are more clear

</details>

<details><summary>v1.7.1 - Hotfix & BBA Compatibility</summary>

AI:

- Azerbaijani AI should no longer suicide into Iran
- Armenia should be more chummy with Russia
- Danish AI should be more chummy with Scandinavian nations
- Improved French Francosphere AI
- Ukrainian AI if it has a wargoal shouldn't suicide against Russia
- Russian AI now must choose Putin with historical/United Russia path
- Tweaked the Rejection AI for Economic Aid (Opinion matters)
- AI should be less likely to go jihadist as the Gulf Nations
- AI will no longer get submarine/ship defense companies if it has no dockyards
- Economic Aid AI should now be more relative to opinions vs scripted hard triggers
- Investment AI should now fall more on opinion and scripted some specific cases where they would be more likely to reject
- Restructured Russian AI for initial election to make Putin the only choice (only can be changed via game rule if you are on historical focus AI)
- AI will now use PMCs
- Improved the North Korean focus AI to focus more on reducing the Arduous March
- AI peace deals should result in annexation of cores and puppeting of the rest of the conquered land
- AI peace deals should see war winners seek to keep puppets close to their border if possible
- Custom AI peace deal behaviour for Roman Italy (ITA), Nationalist/Salafist Afghanistan (AFG) and IR Iran (PER)

Balance:

- Removed Local PMC decisions, as global are enough even in MP
- PMC decisions require 'No Step Back' dlc temporarily
- Made tank engines a bit faster
- Generic Defense companies buffed from giving 1% buff to around 6%
- Decrease unit xp combat bonuses from 25% per level to 15%
- Decrease air superiority effect on defense from 65% to 50%
- Revanchism idea in Generic Tree gives you +1 Volunteer size

Bugfixes:

- Fixed Spanish Carlists not coming to power properly when completing the decision "Install the Carlist Monarchy"
- Fixed Russian tech categories not applying to MTG stuff
- Fixed Scoping error in the Spanish Demand Andorra Events
- Fixed flag for South Korea in Equipment Purchasing decisions
- Better focus tree positions for Armenia, Greece and France to avoid some problems
- Fixed effects from technology Machine Learning
- Fixed increase by 0 terror threat in radicalization event
- Fixed Revoke Citizenship decisions for Spain (The culture group core was wrong)
- Fixed Cruiser Hull 2 (1985) having a bad tech year
- Fixed Operation Yellow Ribbon showing up in 2000
- Fixed Attacked influence opinion modifier, now should reduce by -10 opinion and should be 12 months
- Fixed permission type Friend for Volga-Don Canal, now Russia can move ships from Caspian Sea
- Now Russia should have Thermobaric Warhead from 2000 start date
- Fixed icon for Fuel in lend-lease window
- Fixed position for Artillery title in tech tree
- Fixed spamming remove idea Army of Yes-Men
- Fixed Foreign Data Kraken and Asylum Shopping ideas from game start if game rule disable EU is activated
- Fixed events about Donbas (was missed Luhansk state in uprising and return Donbas in Ukraine)
- Fixed revolt events for Spanish missions
- Fixed missing GFX for Saudi Prince, Paramilitary, Azerbaijani Wester Drift Idea
- Fixed carrier engineering blueprint
- Fixed missing technologies for Netherlands and Ukraine
- Karabakh now should have Non State Actor idea instead of Aspiring State
- Fixed research slots not correctly costing anything
- Fixed Ukraine leaving its own Baltic Black Sea faction
- Fixed bad calls in the Harsh Path of the Culture conflict for Spain
- Fixed all of the influence starting values so China can't instantly puppet Korea
- Fixed requests 2 ruling parties in Danish focus Restrict Immigration
- Fixed wrong data elections for Ukraine, Russia and Georgia
- Fixed bad call for MBT_3 and MBT_2 in Spain's licenses
- Fixed Russia and Iran having 2 recon companies in unit templates
- Fixed wrong network technologies for some countries after game start
- Fixed idea African Brain Drain, now this idea should be removed if country have 4k GDP per capita and at least higher education
- PMC decisions now will spawn actual tanks instead of hulls
- Fixed PMC available amount not updating when units are deleted
- Fixed Iranian Focus Tree crash
- Fixed check compliance and resistance for formable nations decisions and other small fixes for these decisions

Focus Trees:

- Redid Korea Unified Tree to get rid of negative debugs
- Rebalanced Japanese Tree so it's less painful to play
- Added more wargoals to give accurate Spanish Empire Borders
- Improved some availables in the Spanish Monarchist tree
- Added a protest mechanic to prevent Italy sitting on 0% stability
- Added a small reduction to reform expectance from some italian recurring decisions

Graphics:

- ideological powers have all their WIP icons replaced with custom GFX
- Updated the Spy portraits so now there are at least spies for every nation (need to add more generics)

GUI:

- Improved positions for social buttons
- Added MD version and release date in main menu
- Added Subscription window from vanilla

Localisation:

- Spanish localization improvements for the tree
- Fixed spelling/grammar for USA, Azerbaijan and Italy focus tree
- Fixed localisation for event Quebec Supports the Government
- Fixed localisation for Battleship technology
- Fixed missing title for module category about engines in naval designer
- Fixed localisation for Economic Exploitation action
- Updated Investment decision description to show active projects

Map:

- Handful of new states in Germany for Hamburg and Berlin
- Provincial fixes around the world per normal

Quality of Life (QoL):

- Explained how the education cost from research slots is calculated and added a utility script into the decision so you can see exactly how much it will increase cost by one slot.
- Re-Allowed Naval Engine Modules refitting, previously soft-blocked
- Reshuffled and rebalanced admiral traits
- Scrollbar for bookmarks, news events and focus descriptions, now you can have long text without any problems, also scrollbar should fix problem with long textes in other languages and invisible button in news events.
- No slowdown mode now integrated in Millennium Dawn with small changes

Other things:

- Game rule to disable formable nations

</details>

<details><summary>v1.7.0 "MMDGA"</summary>

AI:

- Improved Generic Tree AI
- Economic AI should now evaluate taxes and raise and lower as needed
- AI will produce better units
- AI will now invest in infrastructure
- AI will invest until 6% interest rate and then stop to focus on debt maintenance
- AI will now produce equipment more effectively to provide a more robust AI
- AI in Africa and Western ENG should no longer support the Nigerian Caliphate
- Nigeria has a couple additional AI strategies to be more dominant in the ECOAWS region
- Nigeria's AI should be a bit more dynamic now
- AI should be more aggressive at paying down debt
- Russia should have better war declaration AI

Balance:

- Econ Cycle Upgrade is now 7.50% of your current GDP
- Healthcare/Social Spending are now more expensive for lower GDP/C nations
- Rebalanced Cost and gain from certain Afghan focuses
- Rebalanced Afghanistan Tribal Culture to not be too punishing now that other PP
- Reduced influence from SCO decisions

Bugfixes:

- AFG "Claim Pakistani Paschustani" reworked
- Adjusted Special Forces Tree and NVG position
- AFG Our Nation Recovered Bug Taliban Could Not Complete Focus
- Generic Tree Infrastructure and Radar Station focuses can now be bypassed
- Generic Tree Interventionism avaliable for Salafist Outlook
- Reduced Riau Islands Starting Internet Station to 1
- Corrected Southern Illinois Incident Typo
- Demand the Return of the Crimea state corrected
- Capital of Georgia is now correctly labeled as Tbilisi
- Fixed land doctrines cost reduction in focus trees
- Fixed incorrect tag lookup for Moldova in faction checks
- Corrected a tech path retrieving a tech that doesn't exist
- Corrected some empty enable_equipments in warheads.txt
- Removed improper references in French localization to tags that do not exists
- Fixed Syrian focus "Close PKK Border"'s broken available
- Fixed Danish Neutral conservatism localization
- Fixed AI researching 2035 Helicopters in 2015
- Fixed Brazil and Vietnam non-MTG ships appearing in production
- Fixed two corvettes missing class for Philippines
- Fixed Saudi Panavia Tornado IDS to be the right aircraft
- Fixed electronics tree missing 2025
- Miscellaneous organisation
- Chile now has also Small Arms 1975
- Fixed duplicate localisation
- Patched Turkish Socialism leader
- Fixed manipulate politics as a non-aligned country giving salafist outlook
- Fixed improper tooltip in military aid section
- Fixed State will acquire it option in "A large foreign company buys domestic small business" event not having a cost
- Fixed Iranian Quds focus not giving a faction opinion increase
- Improved Serbia's starting position so there is no longer a debt war
- Fixed Shia Resistance Effect Typo idea
- Recall Volunteers no longer displays if Game Rule isn't enabled
- Fixed Double Saudi Royal Family Check in Diversify the Economy focus
- Fixed Investment Exploit where you find the cheapest state and then invest in other states with the lower cost
- Fixed the triggering of a non-existant event in 2017
- Corrected Exploit by Suspending Elections during Coalition Formation
- Corrected incorrect tag reference in custom factions
- Corrected incorrect tag reference in "The Military Takes Power" news event
- Afghanistan now gets Middle Eastern Portraits
- Attacking communists no longer makes them stronger. McCarty had my name on a list. DW I hated Animal Farm
- Fixed several tags not having factions. No longer were the perepetually stronger than normal!
- Religion for the Religion Law is now capitalized
- Fixed Highlight State Triggers in numerous decisions
- Fixed Investments not matching construction time
- Fixed Investment "10" from displaying incorrect information
- Fixed Satellite Screen from bricking MP games
- Albania no longer gets spammed on startup with USA Events
- Corrected Counter Terror events no longer showing the removal of values
- Fixed Germany volkswagen focuses
- Fixed scientific advances idea for generic tree
- Fixed French Canadian Happiness in 2017 (now Canada should have only 1 idea with Happiness)
- Some fixes for Greek content
- Skilled Staffer requires 18 or more units now to gain experience rather than 24
- Fixed missing icon for British Special Treatment
- Fixed missing icon for Bureaucratic Drain
- Fixed bad event picture in Britain Demands Special Treatment event
- Fixed Delete Influencer Check not properly deleting duplicate influencers
- Fixed missing tax rates for Somali National Alliance
- Fixed Liechtenstein wrong election date in 2017
- Polish focus trees now have normal position
- Fixed Afghan focus Hude Equipment Production
- Fixed problems with annexation of Osetia and Abkhazia
- Code improve and spelling/grammar fixes for Brasilian content
- Fixed Releasing Puppets having only 45% Domestic Influence
- Fixed Liberating influence scoping errors
- Fixed Puppeting during peace conference now gives influence to the actual overlord
- Fixed Ukrainian event to join CSTO, now Ukraine will join to CSTO, not giving and getting guarantees
- Fixed Steam link in game menu
- Fixed overlapping w/ the Research with XP button in tech windows
- No longer can you become NATO Aspirant as a subject
- Fixed decision to integrate Portugal for Spain, now Spain will get cores on every Portugal territory, not only some
- Fixed broken requests 30% influence in SCO in Chinese focus An Alliance to Rival NATO
- Now player don't should see EU decisions if EU disabled due to the game rules
- Fixed 0% influence in some countries
- Fixed Abdelaziz Bouteflika death in 2004

Content:

- New Tags: SPA, TLS
- Majors are now at the top of the list of game rules
- Nationalist Germany now can claim Liechtenstein
- Added initial missile stockpile to ITA
- Added initial missile stockpile to SPR
- Rebalance and restyling of the italian Mafia system
- Added new branches to the Italian focus tree: City of Rome, Church Relations, Media
- Added Technocratic governments to Italy with unique mechanics
- Complete rework of the Italian territorial claims, military and diplomatic branches of the focus tree
- Rebalance of Italian officer corps (nerfed, but improvable through new military focuses)
- Italian leaders no longer change upon losing elections, they can instead be replaced in a dedicated branch
- Added several new italian parties unlockable with leaders change focuses
- Rework of the italian policy system to be based on decisions that can be enacted and repealed infinitely
- Given access to policies to non-democratic italian paths, added democratic senate path and reworked overall branch
- Minor rework and additions to Italian Education, Debt, Administration and Industry branches
- Added several new options for integrative restoration across the whole mediterranean
- Updated romanization decisions with new states and added decisions for previously missing roman provinces
- Added rewards for completing all integrative restoration and all romanization decisions
- Rewrote calculations for italian reform expectance party drift and rebalanced various other effects
- Updated starting stockpile for Italy
- Restructured Brazil and Vietnam Navy
- Improved Influence GUI Localization in tooltips
- Tank Designer Compatibility
- Full Naval System Redesign
- Reworked cost of investments for Cyber Security Infrastructure, now it depends on the percentage of GDP
- Minor changes in CSTO faction
- Added Private Military Companies mechanic
- Added tooltip for russian focus The 2000 Elections to avoid future questions
- There are now unique Aces for various cultural groups
- Added ideological powers to all political parties
- 18 new formable nations, still without any country flags/names, but will be later
- New game rules to weaken countries
- Dynamic Research Slot System
- Gave SHB's leader some traits

Focus Trees:

- New/Improved Focus Trees: Spain, Armenia, Azerbaijan, Iran, United States and Italy
- Rebalanced Ethiopian, French, Danish, Russian and Nigerian trees
- Added search filters to the Finnish, EU, USoE and POTEF trees
- Norway's tree converted to a shared tree with the generic
- Expanded the Generic Tree's content

Graphics:

- 55 or so new models for various vehicles and tags
- New Graphics for the Alert & Fire Button in the missile UI

Modding:

- Added new modifiers for propaganda campaign cost modifiers
- Added new modifiers for economic project cost modifiers
- Added new scripts for adding and removing coalition members at ease
- Added new utility scripts for setting a new ruling party via effect

Performance:

- Implemented dirty variables to several scripted GUIs to improve runtime
- Missiles now have a dirty variable optimizing runtime
- Implemented dirty variables to Money UIs
- Improvement for Mircostates remove game rule, now this rule should remove more useless and small countries, especially in Pacific Ocean and Caribbean Sea
- Cleaned up more add_ai_strategy to optimized AI calls
- Added a game rule for disabling missile alert AI to save on performance for lower end PCs

Quality of Life (QoL):

- New map modes: GCC (Gulf Cooperation Council), ECOWAS (Economic Community of West African States)
- Added close button in Satellite Orbit window for convenience
- EU map mode now has unique colors for office holders

</details>
