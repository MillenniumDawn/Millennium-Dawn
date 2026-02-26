---
title: v1.6 - 1.11 Compatibility and Economic Rework
page_id: changelog-v1-6-1-11-compatibility-and-economic-rework
toc: 'off'
order: 7
---

# v1.6 - 1.11 Compatibility and Economic Rework

<details><summary>v1.6.3 Minor Patch</summary>

AI:

- Investment AI will no longer offer you projects that exceed 730 days
- Disabled Anti Bully Decisions for AI (They didn't use it anyways)
- Armenian/Azerbaijan Hostile Relations added
- Armenia will try and protect Artaskh
- Tweaked the ability for the AI to build offices
- Expanded their desire for industrial strength above all (Should build up longer)
- Expanded some AI strategies for South Africa to be more domineering over the local African minors
- Switzerland will protect and befriend it's Alpine Brothers
- Eritrean AI will now be more cautious against Ethiopian in Ethiopian-Eritrean conflict
- Fixed some issues with some AI frontlines for RAJ, UKR and CHI
- Introduced AI Ship Limiter
- Added "Tick" checks so the AI won't decrease and increase taxes in the same week
- AI will strike back when nuked
- On DoW AI will set its nuclear weapons on alert
- Made Danish AI not able to form the kalmer union on historical, and not choose wacky political parties on historical.

Bugfixes:

- Fixed Steam Link leading to outdated steam page
- Fixed social buttons positioning for all resolutions
- Fixed Brazilian idea "Crippled Currency" from not always being removed
- Brazil should no longer support Ukraine via Employment Projects
- Fixed Ukrainian event not properly displaying localization
- Removed broken tooltip from IMF events
- Fixed Carrier model shading
- Fixed the 2015 UAV showing up as a tu22
- Fixed issue w/ Operative Portraits coming up as blanks
- Fixed Natural Orator spy trait giving useless effects
- Game rules localisation fixes
- Corporate Tax Cost localisation clarification
- Fixed firing ground-launched missiles form foreign launch points
- USoE integrate new members decision reseach slot bug fixed
- Denmark can now get planes from SOV/USA aka, denmark.4001
- Fixed nationalist limited support for POL giving too much of a bonus
- Most of focuses for POL in 2017 will now bypass instead of completion to prevent unhistorical results
- Fixed Hejaz not being cored by UAR after SAU is integrated
- Fixed coalition partner drifts not being applied correctly
- Fixed Outlooks having popularity but all of the subparties being at 0% popularity
- Fixed change of laws in events "US Requests Help With Taliban" and "Joining the Invasion of Iraq?"
- Fixed Russian focus "Federalise Union State"
- Winston Peters no longer has duplicate traits.
- You can no longer hold elections as a nation without elections via political decisions
- Fixed GCC Permit Activism and End Censorship Fault Triggers
- Syria can no longer invite you to their non-existent faction if you don't have the Jerusalem Defence Pact
- Fixed North Korea never accepting the South Korean peace offer
- Countries that reject Mercosur invitation won't get a second chance
- Fixed Burmese Set Politics not working as intended
- Xinjiang and Tibet now start with the correct political setup when released
- Jihadist autonomy levels are now exclusive to Jihadists
- Guarantees are now correctly cancelled when a country switches Outlooks, not just ruling party
- Xinjiang is no longer called S.A.R if puppeted by someone else
- Removed Schröder and Merkel from the German cloning program
- Fixed some countries starting with 4 internal factions
- Fixed Somali National Alliance not having basic laws
- Network Infrastructure now properly decrease building time in for investments
- Network Infrastructure no longer will immediately cancel
- Network Infrastructure building description will now show you the amount per building level
- Fixed Investment Decisions scoping to the wrong fuck off state
- Spelling and localisation improvements in the Syrian focus tree
- Fixed clipping in the tech research
- Chaebols will properly display it's opinion
- Event wot.25 will give results now
- Gulf states will now unban Caliphate parties if they do Jihad
- New England no longer broken
- Libya's Airforce Chief should now give you air buffs
- Fixed Sudanese and Congolese Templates being non-deletable
- Even more event picture fixes (even more even more)
- Clarification of Tighten/Federalize the Union State effects
- Cleaned up Defense Spending tooltip. (No more broken tooltip! Yeah!)
- Removed redundant/unused localization in MD_laws for Russian/English localization
- FCA Has Flag
- Fixed missing name in Yemen's Subideologies
- Fixed Missing Event Image for GCC Arms Sales Event
- Fixed inability to remove "IMF Debts" national spirit form Brazil
- SOV will now be allowed to station troops in PMR & ABK without "exile" in 2000 start

Content:

- USA, SOV, CHI, ENG, FRA, RAJ, JAP, ITA, SPR, PER, KOR, TAI, ISR, NKO, TUR, GER, UKR, BRA, PAK, EGY missile technology setup
- All countries now start with reworked generals and advisors
- Updated Turkish political parties, leaders and starting political setup in preparation for more Turkish content
- Temporarily disabled Narco State/Mafia State content which is causing perpetual civil wars in South America
- Minor additions + some quality of life changes to the Italian Tree
- Rework of the Italian mafia system with new decisions, focuses, qol changes and rebalancing of existing stuff
- Minor Eritrean-Ethiopian war content
- Rebalanced Investment Stats so it should be a bit quicker and some of the smaller buildings are longer to construct
- Reworked Counter Terror system
- Reworked Influence System
- Kicking out the Assad's as Syria replaced Shia conservatism/liberalism mechanic with the corresponding Sunni mechanic
- Reorganised the Syrian focus tree to be a bit more compact
- Syria's civil war chance after the Damascus Spring depends how much popularity various Assads have gained before the revolution
- New/Reworked Focus Tree: Liechtenstein, Generic
- New Music: 22/02/2022
- Stability from budget laws has been reduced
- Reintroduced starting factions and reworked faction mechanics
- New Supported Language: French

Graphics:

- New Russian Infantry Model
- New Czech and Slovakian models
- T-90, BTR-80, BMP-3, BMP-2 Russian models
- Added planes to the deck of the Russian AC model
- All generic nations now have plane models based off their equipment types
- DirectX 11 Compatibility is now supported for all image types
- Added missile gfx: CHI ALCM, NKO ICBM

Units:

- Bosnian templates are no longer non-deletable
- Replaced "Trucks" with "Utility Vehicles" in various supply tooltips

Economy:

- Semi-Consumption Economy can no longer be taken by a "Rentier State"
- Subjects can now ask for debt relief only from the IMF or their Overlord

Performance:

- Optimised Party Popularity calculations
- Optimized budget law creation
- Optimised Textures so mod weight is significantly lower than before

Map:

- Gave Mongolia it's rightful clay from China
- Added Xinjiang core to Aksai Chin
- Provincial rework to Northern Australia
- Split Central Anatolian State in two for Turkey
- Added new states in Armenia, Georgia, Azerbaijan, and Artaskh

Modding:

- Special Purpose Payload now ready for modding

</details>

<details><summary>v1.6.2</summary>

AI:

- Baltics shouldn't leave NATO if neutral

Bugfixes:

- Fixed GROM image for Poland focus tree
- Brazilian 2017 Election Killswitch fixed
- Liechtenstein state name is now correctly name
- Fixed LEB being named "test"
- Fixed vanilla custom icons not being present
- "Assert Control" focus in North Korea will now correctly annex the Korean civil war nation
- Declare Independence for Hong Kong should now end puppet status properly, also removes Basic Law, Lack of Universal Suffrage and One Country Two Systems national spirits
- Fixed LIC, MNC, and ADO ability to have buildings
- Fixed a hole in the Syrian Republican Guard template
- Fixed Syrian debt negotiation exploit
- Fixed BAE Aerospace icon
- Insult event pictures fixed
- Fixed integrate decision Yemen for Saudi Arabia
- Fixed SCO event picture pathing
- Updated Botswana national focus tree for NSB limitations
- Updated EU scripted effects for NSB limitations
- Updated Italy events for NSB limitations
- Made it so the 'Ukrainian Revolution' mission will fire everytime you go over 15 Chance of Revolt not just once and altered the variables to better the pacing of random stability events
- Fixed Syrian Civil War peace event firigng too early
- Fixed TAI being unable to be puppeted as anyone other than CHI
- BRA UNASUL focuses fixed™
- Fixed TUR.Neutral_Social missing localization
- Fixed some event pathing errors & overlaps (part 2 electric fixaloo)
- Fixed some Greek event triggers and tokens
- Fixed Poland not having the AA it needed
- Serbia has internet once again
- Romanian internet is fixed
- Fixed a Nuking Container Issue
- Fixed Negative Campaign Event not showing up properly
- Switched out some Brazilian vehicle graphics
- Fixed Brazilian stockpile lacking equipment or having erroneous equipment
- Brazilian corporate tax and debt percentage to more accurately reflect real-life levels
- Fixed some Brazilian issues, made focuses clearer
- Fixed Ukrainian Event "Cooldown of 2001 Protests" now showing the correct text

Content:

- Reworked Officer Corps for CZE, GRE, FRA, NKO, SWS, SOO, TAB, SYR, SOO, SWA, NKR, NIC, NCY, NAM, MRT, PAP, MOZ, MNC, PAL PRU, PAN, PAR, PHI, NEP, MNT, SUR, NGR, SLO, SRI and 6 releasable tags
- GRE-CYP Enosis event chain allows for Akrotiri's return under correct conditions

Database

- Added Nagmachon (IFV 1995) to Israel in 2000 bookmark
- Updated Israel's population to match real life numbers
- Patched remaining goals_shine.gfx errors
- Switched loadup scenario to be 2000 vs 2017
- Increased Greece's starting military spending level by 1
- Changed Greece's starting convoys 150 -> 400
- Futuristic Nuclear Reactors now has the proper historical year of 2015
- Fixed Victory Points databasing (They should now be correctly sorted into their state files)
- Minor nations now start with $3.0 Billion in treasury for balancing purposes
- Increased Nigerian oil to better represent their oil reserves
- Fixed double power ranking setting
- Cleaned redundant variables from Canada
- Corrected the name of a Swedish politician

Graphics:

- New models for Mig21, Mig23, Su17, Su24, Mig29, Su27, Su33, Su57, and correction to the tu160 models
- f111 aardvark model added for USA
- F14 Model Replaced to match USA Tech Tree Icon (F15)
- J15, Type 003 Aircraft Carrier, and ZBD-97 for China model added
- Brazilian tank model added
- APC and IFV models switched around to correctly match icons (APC Battalions previously showed as IFV models)
- Optimized current in game models to have a lower and more light weight impact on game runtime
- Custom city graphics for Austria, France, Germany, Netherlands, Italy, Monaco, Spain, and Switzerland
- French focus Total SA now has an icon
- Train Graphics
- Updated general portraits for China, Germany and Russian
- Updated some portrait from Swedish politician

Localization:

- ALCM launch button trigger tooltip rework
- Fixed Possessive in French focus Napoleon's Dream

Map:

- New Outer Donbas state for Ukraine
- Added additional maps
- Fixed provincial issues in Sierre Leone

Modding:

- added instructions for map changes to Millennium_Dawn\history\states\#readme.txt

</details>

<details><summary>v1.6.1</summary>

AI:

- Removed minors from mockup missile defense AI (including HLS & SMA)
- Improved project AI so they should now be more willing to put other buildings in project queues
- Improved logging of AI Investment targets so Bird can make better AI (Bird fix AI)
- Added a AI check for the AI to ignore taking debt if they fit well within targeted budgets
- The AI will be more likely to keep their policies in line with their focus trees
- AI will now use 'revert ideas' decisions for Poland
- Fixed and added historical AI for the nordic countries
- The Nigerian AI should no longer ping pong between Islamic and Christian religious paths
- Ukrainian AI should no longer bum rush the Baltic-Black Sea Union every game
- Sanity checks for Korea. They shouldn't take their wargoals for JAP or USA if they're currently at war with South Korea

Bugfixes:

- Civilian Folder Horizontal Scrollbar patched
- Fixed diplomatic actions UI issues for resolutions smaller than 1920x1080
- Fixed policies UI for resolutions smaller than 1920x1080
- Bosphorus strait fixes (map & missile launch triggers)
- Strait icon not covered from missile buttons anymore
- Updated Housing Crisis Effect for "Cool Down the Markets"
- Fixed Somalia Civil War issues and converted cleanup events to an on_action
- Fixed increasing tax rates giving their proper popularity changes
- Fixed the missing leaders for San Marino
- Fixed agencies being listed as the Iraqi Falcon Intelligence Cell
- Fixed exploit adding additional nuclear warheads to ongoing production
- Fixed Canadian Infrastructure sections
- Removed Rail Guns from Frigates
- Added ability to have ESM on newer (2005 and newer) Destroyers
- Fixed Ukrainian spirit "Ukraine without Kuchma" not disappearing
- Fixed Ukrainian Donbass Civil War Events Triggering improperly
- Fixed Tsaryov not being NOV's leader on civil war
- Fixed America's Great Recession event not properly ending.
- Fixed Communist Cadres not showing up if communist
- Fixed Brazilian election issue
- Fixed Nigerian ideas not giving full benefit
- Fixed Ukrainian Orthodox Church being takeable w/o the requisite focus
- Fixed Ukrainian Strong Republic not getting the strong republic idea
- Fixed La Resistance Portrait not showing up
- Fixed resources strip showing incorrect icon when missing resources
- Added ISR APC tech & 1985 MR tech
- Deleted Aircraft tech from UAE (2017)
- Fixed Lithuanian state name Siauliai
- Fixed focus icons not displaying for communist path for Poland
- Fixed Polish State Run Economy main cycle failing even if all requirements are fullfilled
- Fixed localisation for Polish State Run Economy main cycle notification
- Reduced monthly cycle for State Run Economy to 29 days (with mission re-enabling it should now be 30 days)
- Fixed Polish focuses not constructing correct amount of refineries
- Fixed MR & STK certification not working, MR & STK can now be used for ALCM
- Added Japanese Core to Okinawa Base
- Improved Ukrainian Novorossiya Trigger
- Tweaked the decisions for Ukraine
- Nigerian decisions tweaked
- Fixed a Nigerian deadlock in the Boko Haram path
- Fixed broken division template in LAR Triggers
- Fixed Ethiopian missions always being active
- Fixed portraits not displaying properly for LAR agents
- Fixed American event paying yourself for demanding Sudan reparations
- Can boost parties for non-Muslim nations if you have the salafist game rule enabled
- Fixed Air & Missile Defense Auto Deploy not updating stats
- Fixed Air & Missile Defense minus buttons add more missiles than deployed to inventory
- Changed coup by influence math so anything above 1 GDP/C isn't immune to coups
- Corrected russian state name Veliky Novgorod
- Fixed MBT pictures for India
- Fixed MIC, SML, SHA, ABK, and TAL not having starting tax rates causing them to go bankrupt early game
- Nigerian Foreign Investments and Neighborly Expansion should no longer scope to Nigeria
- Removed reference to a vanilla event from LAR
- Patched economic cycle events. Negative events should now be much more likely to occur
- Patched internal faction The Bazaar immediately plummeting to 0 when taking any kind of opinion option
- Fixed nuclear doctrine triggers for fire button not working correctly
- Fixed nuclear test not working correctly
- Fixed satellite access adding wrong stats, when own sat system is higher

Content:

- Added option to Stock Market Crash to "bailout" to give you a player option
- More factions dislike when the Stock Market Crash
- Added Ukrainian Event to cooldown the 2001 protests
- Added German ship names
- Rebalanced some Nigerian focuses
- Syrian Civil War named threat is now 5 tension rather than 2 allowing for volunteers
- Cut the PKK system (System for Turkey needs to be completely reworked)
- Added an event for nuclear tests

Database:

- Added AA Upgrade 3 to Russia
- Removed minors from on start up SAM sites and SAM tech (including HLS & SMA)
- Officer rework for MIC, MLC, MLD, MLT, MLW
- Added Early Helicopter to Nigeria
- Updated Israeli Aircraft Names
- Updated Isreali starting Techs
- Removed some UAE starting Techs

Focus Tree:

- Revealed hidden North Korean tree branches
- Reduced negative modifiers from Arduous March so you can actually research something (in 8000 days :kek:)

Graphics:

- Updated Investment System Icons to new building icons

Localization:

- Fixed a typo in alert button
- Fixed a typo in Trajectory Tooltip
- Updated localization for Investment System
- Fixed grammar and spelling for the print money tooltip
- Fixed type in Eau Claire, WI
- Fixed typo in Turkish city
- The new content has been translated into Russian.

OOBs:

- Fixed FREMM-FR class not having VLS

Performance:

- Optimised Syria's events
- Additional optimization to event runs

Military:

- Removed Power Projection mechanic
- Strike Fighter now are fighter cas tactical_bomber scout_plane
- Multi Role Fighter now are fighter interceptor cas tactical_bomber scout_plane
- CV Multi Role Fighter now are fighter interceptor cas tactical_bomber naval_bomber
- Balance changes to CAS damage and survivability
- Updated Defines to help balance Air-to-Ground stats
- Increased Air-to-Air damage for Aircraft
- Adjusted Terrain Penalties for CAS damage
- Adjust Air Combat Damage scale to more closely align with Vanilla numbers
- Adjusted Defines for Positional Values and Stacking values to penalize Death Stacking Navies

UI:

- Replaced hoi_22typewriter font with hoi_18mbs for missiles UI
- Fixed strategic priorities overlapping visuals
- Added click options +10%, 50%, 100% to nuclear energy/nuclear material buttons
- GDP and GDP/C is now viewable on diplomacy screen in treasury and income tooltips
- Fixed overlap in strategic priorities screen
- Nuclear warhead production +10/-10/+100/-100 click options added
- QOL Update Missiles Launch Control Center: salvo & duration automatically set to 1 when selecting a missile
- Fixed policies screen to view the policies on lower resolutions

Economy:

- Capped max negative population growth from GDP/C to -100% from -115%
- Taking control of the Panama Canal and the Suez Canal from their original owner will now give income
- Changed Power Ranking calculation to prevent overflow making everyone a non-power

Map:

- Fixed unit locations in Western Tibet

</details>

<details><summary>v1.6.0</summary>

AI:

- Implemented Country Specific Civilian Industrial Targets for CHI, USA, ITA, FRA, UKR
- Implemented a generic country industrial target for generic minor, regional, large, and major nations
- AI is now willing to trade away 35% of their factories for resources
- Expanded the AI for the naval powers {Any nations with navies now have targeted AI for vessel construction and breakdowns}
- Removed the Afghan and Tajikistan AI to build dockyards. (yes this was a weird thing)
- Tweaked the way the Ukrainian AI handles event options
- Improved AI for economic budgeting
- AI is now much more anti-debt than before
- Taliban should no longer suicide on Afghanistan
- America now should no longer abandon Kuwait Naval Base when at war with Iraq (hecking Bush)
- North Korea/Korea should not invade the other if they are guaranteed by superpowers
- Added investment AI for South Africa

Balance:

- Balanced Refitting IC cost of modules
- Balanced IC cost of many modules, especially ESMs
- Added new module choices to many slots, especially ESMs
- Various minor changes to mtg modules
- Buff to carrier wings
- Tweak to CHI Xi's part focuses
- increased sub spotting
- Buffed resource to factory ratio
- Rebalanced the LAR Agency system
- Increased factory requirements for research-related focuses in the generic tree
- Increased Naval Attack and Targeting for Aircraft
- Slightly nerfed AA stats on Naval Modules (needs testing)
- Increased Air Attack stats on Aircraft
- General balance to dockyards
- Rebalanced Ethiopian railway decisions
- Rebalanced China's STE decision to not give infinite Research Slots
- Reduced MD's LAR operatives to 10 from 16
- Shore bombardment is now capped at -100% vs -200%
- Nerfed Close Air Support
- Buffed Anti-Air
- Buffed Naval Bombing from aircraft
- When you financially collapse subjects are released
- No longer can manually take debt when interest rate is greater than 20%
- Engineer companies have greater entrenchment
- Tension from puppeting is now reduced
- Yearly tick down for tension increased from 1.2 to 1.8

Bugfixes:

- Fixed some naval variant errors
- Fixed the subideology scripted GUI spamming an error whenever selected/hovered
- Fixed the musical compression to be 44.1KHz for Firewall, Memories Without Colour, and Lost on The Hill
- Fixed Italian 2017 equipment not loading
- Performance improvements to hourly checks for the EU Tree (should yield a large performance boost to many users)
- Fixed Canadian events not triggering properly
- Fixed a 3D Model spam
- Fixed Carrier techs not having the general category of Carrier
- Non MTG ships should now spawn properly
- Tweaked some localization
- Nationalist Bosnia will now correctly show up in event texts
- Prerequisite tooltip for CHI focus "The Persian Link" now shows correct state names
- Fixed several issues within the Brazilian Tree
- Fixed missing technologies in some releasable tags
- Fixed Carrier Event chain for China
- Fixed some localization issues within the Election event chain
- Fixed UK decision icons not showing up
- Fixed stats changes for equipment variants overlapping in the upgrade window
- Fixed/updated some SCO content
- Fixed research start year for C5ISTAR Equipment
- Fixed leader for Salafist Kurdistan
- CAN Provincial Infrastructure decisions won't appear when infrastructure in the state is at max level
- GRA Western conservative party now has a name
- Fix some typo in localization and terrain name
- Fixed Italian focus spamming you with 200+ "NATO Leaves"
- Fixed Vilinus terrain image error
- Fixed Dockyard being created in Copenhagen province (caused some issues with crashing)
- Fixed missing LibyaNews.1.a localization
- Fixed MTG VLS category
- Fixed MTG modules localization
- Fixed treasury change for The Retirement Reform focus for Denmark
- Fixed the picture for King Frederik The 10th of Denmark
- Fixed Ukraine focus Reduction of the State to decrease centralization instead of increasing it
- Fixed Andorra localization for its political parties
- Fixed the on actions for Canada OP Yellow Ribbon
- Fixed GFX texture paths for air
- Fixed generic focus tree naval base to add building slot
- Fixed ideas for Brazil
- Fixed a lot on the Brazil focus tree
- Fixed saudi_royal.4 event
- Fixed events for the Gulf and EU
- Fixed focus four Gulf focuses that didn't add building slots and one that didn't change treasury after adding building
- Fixed US Push The Ban Through event
- Fixed the investment system so you can't invest for free using released countries
- Fixed Pakistan Defence Companies that were available to Norway
- Fixed UNASUL members to be the correct members and not the whole South America continent
- Fixed Paracel Sea spelling
- Fixed Poland missing research on the techtree for 2017
- Fixed Kilkis to be capitalized
- Fixed event texture paths
- Fixed decision texture paths
- Fixed goals texture paths
- Fixed skills of Brazil commander Augusto Rademaker
- Fixed non-MTG ships appearing when using MTG on India and Brazil
- Added localization for Polish Lithuanian commonwealth
- Fixed state category updating
- Fixed Nigeria & Ukraine localization
- Removed duplicate localization for EU, France, Japan, UK, Denmark, Greece, Canada, Brazil, USA, Italy, Germany
- Fixed Botswana event localization
- Fixed typo's, readability
- Corrected grammar and spelling mistakes
- Fixed China nuclear power localization
- Fixed Chubu state localization
- Fixed localization of Ukraine defense companies
- Fixed Brazil.35, Brazil.19 and Brazil.21 event text
- Fixed cartel.12 event text
- Fixed the temporary tax cuts decision
- Fixed USA.31 event text
- Fixed influence coups math
- Fixed LAR Operatives Linguist stuff not working correctly
- Fixed Ukrainian militia decisions
- Fixed the way Ethiopian railway decisions work
- Fixed broken Ukrainian party icon
- Fixed Naval Lists not have localization
- Fixed Angolan Civil War Event that makes Afghanistan become Angola
- Fixed clear portrait on default operatives
- Fixed Zhirinovsky Monarchist Effect not properly gaining National Populist Support
- Fixed missing portrait for Rosario Crocetta
- Fixed Confederate States having non-MTG techs w/ MTG enabled
- Fixed loosing research solts when forming the United States of Europe; gained Techs now don't popup anymore
- Fixed German Legacy is now removed with focus Constitute the new European Nation
- Fixed Operatives no longer generating properly

Content:

- New Gamerule to control duration of influence mechanics cooldown
- Made Cyber Warfare decisions for Non-LAR Players (will convert and add on to LAR systems)
- Evergiven Blocking the Suez Event Chain
- New idea "PLA Business Ventures" and "Decline of PLA Business Ventures" for End PLA Business
- Leader term limits implemented for relevant countries
- Jihadist border crossings restricted to countries that have the counter-terrorism mechanic
- Jihadist border crossing event descriptions updated to show a bit more information
- Added AI behavior for Italy in gamerules
- Removed Rio Pact and Budapest Memorandum
- Added a code to cancel all given and received guarantees when changing Outlooks
- New Internal Faction events
- New Economic Events
- Complete Rewrite and expansion to Investment System and Economic System
- Complete Rewrite and expansion to Internal Faction System
- _insert trollface here_ kek
- New Missile System (Yeaaaa babyyyyy)
- Changed how Ukrainian random events trigger
- Limited the Generic Civilian Factories Focuses to be done at peace only
- Added base equipment capture rate: 5%
- Reworked officers and officers corps for MD
- Starting Reactors are given to most nations who have them

Database:

- Cleaned texticons.gfx of vanilla ideas
- Archived unused decisions for greater load-up speed
- Archived unused localization files

Focus Trees:

- New Trees: Botswana, North Korea, South Korea, Poland, Afghanistan
- Redid the UK industrial tree to better match the targeted regions
- Expanded and Reworked Danish Tree (Wherever that is)
- New look for Norwegian focus tree (better icons and structural improvements)
- Removed Israel focus tree and more since it isn't done yet
- Added new syrian 2000s focus tree branch for damascus spring's aftermath
- Ukraine tree rebalanced and improved
- minor updates to the Italian tree
- Brazilian tree expansion with additional content for Lula and tweaks to other sections
- Expanded AI desire to lead to war w/ focuses that give war goals

Graphics:

- Implemented a new particle GFX effect for Airplanes
- Added new Asian/Middle East/African city graphics
- Add a icon for MillenniumDawn Game
- Tons of new focus icons
- Moved subjects, exiles, Collaboration and money screen opener below the current ruling party screen
- Replaced Australian PM John Howard image with better one
- Additional Graphics for European cities
- Agency icons for Iraq, and a new CIA icon
- Implemented the following new models: F4, F14, F15c, F15ex, F16, RQ-170, B1, B2, C-5, Eurofighter, M2000, M-5, J11, J16, Sharp Sword UAV, H-6k, Q-5, MIG-23, TU-160, SU-25
- New icons for Light guns
- Fixed an icon issue w/ the American naval tree

Localization:

- Russian language support

Map:

- Corrections to map
- Added new states for Brazil

OoBs/Units:

- Tweaked some ship classes
- Added Destroyer Hull 4 to France in 2000 to make the OoBs work correctly
- Additional Destroyer Names for China
- Removed Horizon Class Destroyers from France 2000 oob
- Updated Italian ship designs
- Added missing corvettes to 2017 Italian OoBs
- Added additional naval name lists for 25 nations across the globe
- Removed airborne IFVs and APCs (equipment) and replaced them with regular versions
- Removed Interceptor fighters
- Added Finish Missile Boats (Rauma and Hamina Class) (MTG)
- Added Skjold Class equipment variant (MTG)
- Tweaked Denmark, Norway and Sweden and Danish ships to be more realstic in terms of equipment (MTG)
- Added the Blekinge Class (A26) new submarine for Sweden (MTG)
- Tweaked ships of Australia, Brazil, Canada, UK, France, Germany, Netherlands, Pakistan, India, Russia, Taiwan, Turkey, Ukraine, USA and Venezula, that had anti-submarine motars but should have torpedoes IRL and more (MTG)
- Tweaked some unit spawn positions in FIN, NOR, SWE to be correct
- Added reconnaissance for Special Forces
- Locked Ukraine's militias from being deleted
- Removed NH90 and Eurocopter Tiger from production and stockpile for France and Germany in 2000 bookmark
- Removed Scorpene Class submarines from Chile in 2000 (MTG only)
- Removed HMS Ledbury fom the UK in 2017
- Added FREMM-FR class to France in 2017

Performance:

- Improved tech tree performance by cutting down possible tech paths
- Reduced some AI has_game_rule calls
- Removed the AIs ability to see some blank non-AI related decisions
- Less NATO related checks
- Restructured some on_actions to be a little quicker
- Full scale optimization of internal faction system
- 45% performance improvement to general runtime
- Changed Ukrainian Events to fire using on_actions rather than MTTH
- Changed Brazilian Events to fire using on_actions rather than MTTH

Techtree:

- Removed air IFV and APC techs
- Removed links between IFVs and recon tanks
- Artillery, AA and AT tech trees are now linear
- Legacy doctrines can no longer be researched
- Cut links between various non-MTG ship techs

</details>
