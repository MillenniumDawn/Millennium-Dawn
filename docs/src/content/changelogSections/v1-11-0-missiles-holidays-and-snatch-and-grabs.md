---
title: v1.11.0 'Missiles, Holidays, and Snatch-and-Grabs'
page_id: changelog-v1-11-0-missiles-holidays-and-snatch-and-grabs
toc: 'off'
order: 12
---

# v1.11.0 'Missiles, Holidays, and Snatch-and-Grabs'

<details><summary>v1.11.2a - 2/20/25 Hotfix</summary>

v1.11.2a
Bugfixes:

- Fixed building 3D models bugging out on Linux/Mac/Steamdeck
- Fixed skyscrapers not appearing on the map
- Fixed Canard wingform giving 60% radar advantage instead of 6%
- Fixed the Energy Use modifier not properly working as intended causing very disparging numbers using game rules/"All Power Sources Energy Use" modifier
- Fixed an issue with Tajikistan not coring Badakhshan after the Badakhshan decisions were completed successfully
- Fixed "Spanish Tourism Industry" ideas giving the wrong amount of money once you are on the third layer of money
- Fixed the "Spanish Tourism Industry" ideas incorrectly allowing you to bypass the reason to get the money by having over 50% stability despite being at war
- Fixed Italian Mafia decisions not properly informing the player that the strength of a clan needs to be below 0.25 to be raided
- Fixed the requirement for arresting IS-KP leadership in Tajikistan being 7400% (intended to be 74%)
- Fixed an issue where you could invest into the F-35 program when it was already at 100%
- Fixed Eurofighter model/GFX not appearing for certain countries
- Fixed US AI still stacking Kuwait Naval base in certain conditions after Iraq's defeat
- Fixed bugs when germany form the useful
- Fixed German Weizsäcker event

</details>

<details><summary>v1.11.2</summary>
v1.11.2

Achievements:

- Fixed a Czech ribbon not following the standards for the difficulty

AI:

- Reworked how AI manages its spending - now mainly based on expected spending
- Reworked how AI manager its taxes - now uses simplified and more rigid model for more predictable results
- Adjusted the AI for the United Kingdom, Italy, France to not immediately intervene in Afghanistan as soon as there is WT and instead focus there when they support the US or if it's past 2002.6.1
- Enabled proper AI for the counter terror international system UI
- AI should stop being silly and trying to invest infrastructure in states with 5 infrastructure
- Added new gamerule - God Of War - allowing AI to use more meta templates and focus on player more
- AI will be less likely to conduct a Special Forces raid if you are not on the same continent, and they are not stronger than you
- Made AI more motivated to build rifles
- hardlocking italian ai from causing civil wars due to mismanagement when historical focus is on
- Added FIN/SWE fully to the historical nato path after 2023
- European Union AI should be more likely to push for expansion if any of the superpowers cause world tension (unify Europe against the others!)
- European Union members who are in NATO are more likely to accept fellow EU members into NATO

Balance:

- Reworked the math of the internal faction decision "Taxing Religious Institutions" so the money amount isn't that high
- Lower stability will now directly impact the productivity growth of a nation (up to -25% at 0% stability)
- Reduced the base yearly population growth of nations from 0.008 to 0.006 so it's not as exponential
- Increased the minimum radicalization required for "Youth Radicalization" to 20 from the 10 that was there before
- Stability now has a visible impact on counter terror minimum/maximum radicalization
- Updated AI templates for IFVs and APCs for years 2025 and 2035
- Added some extra requirements to Special Forces raids (Continental and intercontinental)
- Increased the nuclear energy construction speed and power generation starting from 2015 going forward
- Reduced the extremes of italian reform expectance and added a display of the yearly drift in its value
- Updated italian MIOs with new units and missiles
- Updated Admiral traits with new naval units
- Updated italian migrant focuses with the new migration mechanic
- Replaced the italian ageing population spirit with a new modifier where the malus to population growth changes dynamically

Bugfix:

- Fixed the Helicopter takes being unable to be researchable for people who own No Step Back but not By Blood Alone
- Fixed a flip flopped event for Hezbollah - Israel border war
- Fixed a Syrian focus not properly charging the user nation for the infrastructure
- Fixed Lichtenstein not showing up as a Potential EU member despite being able to join the EU
- Fixed the Romanian focus tree's continuous focus position covering up some decisions
- Fixed the "Encourage Productivity Growth" internal investment not actually improving your productivity
- Fixed scoping in special projects hopefully resolving all related crashes and errors
- Fixed the Syrian Focus "Road to Palmyra" randomly adding infrastructure to Mali
- Fixed the spamming error with has_idea when it should be has_government in Lybia
- Fixed the "Free States of America" only having the standard default last name
- Fixed the "Fire and Forget" special project not correctly showing up when it needs to
- Fixed some No Step Back SP AA and SP ARTY techs being visible in the lineup
- Fixed some references to the SCO not having additional checks for the other member types giving you the illusion of not being a SCO member
- Fixed a handful of minor bugs with the formable nations such as missing cores for some and accurate tooltips for others
- Fixed the Namer and Eitah AFV design decisions
- Fixed odd overlap in the air strategic window view causing some clipping problems/inability to click certain buttons
- Fixed China SCO focus "Military Technology Sharing" not properly checking if SCO members are emerging or not
- Union State - Now AI completes decisions on the integration of the Union State
- Fixed a bug in the focus branch of the Russian Liberals related to the Balance of Power
- Fixed the focus on investments in Kaliningrad in the Kasyanov branch (Russia)
- Missing national republics in the decisions on the liquidation of republics in the Zhirinovsky branch have been corrected (Russia)
- The Rosgardia branch has been fixed and the Zolotov trait has been fixed. (Russia)
- Fixed the mechanics of Integration into the Russian Economy and into the Russian Army for the subjects of the Russian Federation
- Branch of the Democratic Referendum in Russia has been fixed, now it works correctly
- Fixed bugs in the Russian military branch
- Some economic and military national spirits of Russia are now displayed correctly
- Fixed AMX-10P having wheeled suspension instead of tracks
- Fixed the range on the Arsenal Bird not being present
- Fixed countries being able to raid their own puppets
- Fixed countries being able to raid people they have non-aggression pacts with
- Fixed an issue with the F-35 purchase approval event firing for the wrong country
- Fixed the VOX leaders not showing up correctly in the leader list
- Fixed the production button glow being offset by a handful of pixels
- Fixed the "Analyzing" foreign investment glitch by adding a 90 day timeout for analyzing. This should stop any corruption but allow the game state to continue.
- Fixed the "Join NATO" option being bricked if a member state was annexed
- Fixed the 2005 Battleship/Battlecruiser hull being classified as a 1985 tech not appropriately applying year debuffs
- Fixed post-United countries not starting properly with the satellite/missile system dynamic modifiers
- Fixed the Italian decision "Stop Immigration" not allowing if you signed the treaty of benghazi
- Fixed operations on air wings not being able to be toggable properly
- Fixed leaving NATO twice as Italy if you dismantle parliament and then take the abandon the west focus giving you double relation debuffs to other NATO members
- Fixed nanoncellulose in medicine tech not having the right tech year
- Fixed a couple of states not being properly cored by the Neo Romanization decisions
- Fixed a number of issues with ISR leaders
- Fixed Czech political leaders not showing up properly
- Added nuclear technology as starting Czech technology
- Fixed countries mentioned in "satellite link up" focus effect that didn't get the Al manar national spirit after the focus is completed (Hezbollah focus tree)
- The syrian hafez succession decisions are no longer visible after hafez's death
- Fixed research boost for Polish IFV from the effect

Content:

- New Focus Trees: Tajikistan
- Improved Focus Trees: Germany
- Added a new special project "Helicopter Design Experiments"
- Added a cheat decisions for the European Union to force them to always vote yes
- Added new or updated MIOs to Argentina, Brazil, Mexico, Venezuela, Chile, Morocco, Egypt, Spain, Nigeria, Portugal to expand the options for nations military production and so on
- Added some new leader traits to VOX political leaders
- Moved 2015 battleship/cruiser hull to 2020
- BLR Political Rework - New Parties and Leaders

Ideological Powers:

- Modifiers in tooltips now have text icons
- Communists:
- 5-Year-Plans are no longer built from pieces, but you choose from a single type of 5-year plan. The modifiers have been increased in return
- Replaced Incompatible Economy (+50% Foreign Investment Cost) with Hard Labour (+15% Building Worker Requirement)
- Socialists:
- Welfare State now gives -15% bonus to health & social spending instead of a PP reduction for law changes
- Economic Interventionism no longer gives you additional decisions, instead you get a -25% PP and money cost for Internal Investments (+50% Renewable construction speed for greens)
- Peaceful Diplomacy no longer gives a construction speed buff but instead only the PP buff
- Liberals:
- Business Friendly now gives +10% corporate tax instead of just +10% office tax
- Anti-Military now gives -15% military/dockyard output instead of -25%
- Autocrats:
- Good Connections now gives oligarchs +10% resource export income rather than civilian factory income
- Replaced Unlimited Power (-25% Advisor Cost) with Power Through Strength (+25% Party Popularity Stability Modifier)
- Paramilitary unit decision for fascists no longer increases unit attrition
- Monarchists:
- Replaced Keep It In The Family (-15% corruption and internal faction cost) with Royal Decree (-15% Laws Cost)
- Fundamentalists:
- Sharia Law now gives +0.10 Outlook support instead of +0.05
- Foreign Fighters now gives you +300 weekly manpower rather than a repeatable decision

History:

- Improved multiples OOB/Stockpile
- Added many variants of rifles and other equipment

Graphics:

- Added dozens of new 3D models
- Made the AI more competent in choosing the right 3D model and GFX for their respective country.
- Added hundreds of equipment GFX
- Upscaled African/Middle East generals portrait
- Fixed the USNA flag being incorrectly compressed causing it to not properly grab the formable flag
- New and improved focus icons for CHI
- New and reworked portraits for ENG
- New icons for AGL parties

Music:

- Added 1 hour of ambient music. Reweighted the entire MD playlist
- Added around 40 minutes of weighted Middle Eastern music
- Added around 40 minutes of weighted Ukraine war music

Localization:

- Added thousand of lines for military equipment names
- Added more translations and fixed a number of localization strings
- Added "Political Power" to the Cost of X tooltips to be more clear
- Added "Treasury Cost" to the Economic Cycle Upgrade cost tooltip

Map:

- Redrew the map for the Baltic countries, Kaliningrad, Belarus, Ukraine, Moldova, Poland, Czechia, Slovakia, Hungary, Austria, Switzerland, Germany, France, Italy, Spain, Portugal, Morocco, Libya, Egypt, Lebanon, Syria, Iraq, Kuwait, Iran, Israel, Palestine, Jordan, Qatar, Bahrain, UAE, Oman, Yemen, Saudi Arabia and the Koreas

User Interface (QoL):

- Added toggles for Nuclear Power Plant and Fossil Fuel Power Plant for more control over your energy
- Added a highlight to all NATO member states who have not ratified your accession to NATO

</details>

<details><summary>v1.11.1b - 12/19 Hotfix</summary>
v1.11.1b

AI:

- AI should be more likely ratify NATO applicants if they are influenced by a NATO member, has high opinion and if any of their neighbors are emerging, nationalist or salafist
- USA should be more apt to declare operation enduring freedom if there is less than 25% threat or if they have not done so before Jan 2005
- SER will now seek to rebuild Yugoslavia in peace deals at half cost after completion of the appropriate focus

Balance:

- Reduced the passive counter intelligence gain from the "Counter-Intelligence" agency upgrade
- Increased the gained acreage for Brazil for the Amazon Rainforest system
- Added some triggers to the Brazilian content that you can't take decisions if you do not have the acreage to do it.
- Reparations amount paid will now be scaled based off of the victim country GDP instead of the attacker

Bugfix:

- Fixed the Internal Faction event "Communist Cadres & The Military Fight Over Ideology" having incorrect options and opinion boosts
- Fixed the "X Proposes Pre-emptive strike against Iran" event triggering twice for someone
- Fixed Ukraine being 20 years ahead in Anti Air weaponry for No Step Back users
- Fixed the Space Programs not showing up properly due to bad DLC checks
- Fixed the Productivity & Unemployment Dynamic Modifier having the wrong modifier
- Fixed the Chinese focus "String of Pearls"
- Fixed the starting crash for Linux users due to bad unicode characters in the new terrain pictures
- Fixed the Agricultural District Construction speed spazzing out at low and high productivity
- Fixed Indian Focus "Prepare Rebellion in Tibet" trigger to make the focus could work properly
- Fixed Sudan-South Sudan peace agreement event having the wrong text
- Fixed the Straits of Dover making ships teleport to Scotland

Content:

- Expanded Chinese Historical Tank/AFV Design Decision Category

Database:

- Changed Eurofighter, Gripen, Viggen, J-10, Rafale to use the Delta Wing Canard wingform

Graphics:

- Graphical Rework of North Korean and South Korean Parties
- Updated the Graphic library again to properly include the soviet aircraft carriers
- Adjusted some misplaced icons for decisions in the Amazon Rainforest decisions
- Fixed some graphical elements for Gronland, Reykjavik
- Fixed broken achievement icons for Brazil MD Achievements
- Fixed missing model for the Arleigh Burke class destroyer
- Fixed some ASCII characters breaking terrain pictures

Localization:

- Fixed a reference in the African Union decision category referencing billion instead of thousands
- Updated the loading tip for Bolivia to accurately represent it's current number of coups
- Flipped the colors of the "Internal Investments" Political Power and Monetary Cost Modifiers
</details>

<details><summary>v1.11.1</summary>
v1.11.1

Achievements:

- Added the achievement "There Are Two of Them?!" as Amazon have Amazon invest in the rainforest
- Added the achievement "The Rainforest Reborn" as Brazil have the Amazon's total acreage is over 3000
- Added the achievement "The New Communist South America" as Brazil have your Workers' Party Alignment be 100 and have all other South American nations be Left Wing Radical
- Added the achievement "The New Agricultural Baron" as Brazil have 150 commercialized agricultural districts and be a great power or superpower
- Added the achievement "Who needs them silly tree anyways?" as Brazil have every Amazon state have level 5 infrastructure, level 5 network infrastructure, and 25 Office Sectors, Civilian Industries, Commercialized Agricultural District, or Military Factories

AI:

- Fixed the AI not being able to recruit nor build facilities
- AI should no longer get a bonus due to some improvement in foreign influence handling
- Mutual Investment Treaties now reduce the AI's willingess to do the "Increase Autonomy" continuous focus
- AI should now avoid raiding you again if they have paid reparations to you
- AI will now evaluate what the assumption of debt will actually do to its interest rate
- Removed obsolete AI strategies that were causing the AI not to use PP for diplo actions
- AI should no longer spam you with overlord subsidies if you've declined
- The AI should be less likely to take debt if they are at 80% of GDP-Debt Ratio
- Raid AI has been reworked entirely
- South Korea should no longer invade North Korea if China is the overlord of North Korea
- Syria should now be more likely to take Integrate Lebanon if Lebanon is an autonomous state to make it easier
- Spain's AI should now more properly prioritize certain decisions to help their economic growth
- AI should now be more dynamic in their response to the ceasefire event from the Public War Weariness system
- AI should be more likely to try to trade for more fuel in peacetime to help their economies
- AI should be more likely to grant you a bailout if you share an outlook, or if you are on the same continent
- AI should be more likely to reject a bailout if they have less than five percent influence on you
- AI who build nuclear reactors and do not have the idea "Nuclear Energy" will now try to change their law so they can gain the energy
- AI should wait to do the European Parliament if they are a nation who cannot afford the PP requirements so the don't hard lock themselves into a bad situation
- The "Debt Assumption" AI should be less likely to take debt if the targets nation is less than theirs (i.e. brazil has 8% but Germany is 5% so Brazil doesn't want to take on Germany's debt)
- AI should not take the decision "Buy Technical Pickup" if they have a surplus of Utility Vehicle equipments or if they are at peace
- AI should wait until June 2000 before offering trade agreements and mutual investment treaties to have them save political power for the early game
- Expanded the Indian AI so they're more dynamic and should focus more towards their neighbors and becoming a bulwark against China
- The Syrian AI should now pursue to conclude the "Status of Lebanon" section of the tree more aggressively so they do not collapse economically
- AI should be a little less likely to push the "Combat Foreign Influence" button if they're a NATO or EU member and one of their top three have EU member or NATO member and none of the top three are SOV/CHI
- AI should be less likely to be so gung ho on Embargoes unless the nation is a warmonger
- Added additional checks to agri techs that will encourage the AI to take them if they have lower pop to free up workers
- The AI should now properly manage their power consumption rules to help them better balance their economy and try to maximize benefit on high power (tldr good to invest in power stuff since the AI will try to use the excess power like a player)
- The Russian AI has been reworked. Now he evenly performs focuses on the economy, the army and politics

Balance:

- Rebalanced breakthrough point generation for special project. Less passive gain from research, more from scientists
- Rebalanced Special project BP cost
- Rebalanced research time length for tank and air tree. Longer all around
- Moved DJI drone from 2000 to 2015
- Reduced military alliance research buff hard cap from 25% to 10%
- Reduced the taxing religious institutions income a little bit so it's not so terribly overpowered
- Reduced the frequency of the "Labour Unions Protest Migration"
- Clamp the "Religious Group Request in Government" pp to a maximum of 500
- Reduced some buffs from Iran's nuclear tree
- Reduced amount opinion lost from doing raids
- Reduced the amount of tension generated from multiples sources and slightly increased decay so small scale wars do not instantly rocket the world tension
- Removed the Surrender Limit from the nuclear ideas for the time being
- "Assume Debt" now requires the target nation to not have more than double your GDP
- Increased lethality of SAMs by ~15% and reduced IC cost for ~10%
- Reduced the opinion required for the Chinese focuses to make it easier to do focuses
- Slightly reduced the amount of workers required for civilian factories from 360 to 345k
- Rebalanced the "Military Advisors" traits so they now increase command power instead of reducing it
- Increased raid success rates slightly
- AI will now retaliate properly when raided (if it chooses to retaliate, you will be warned)
- Made the meme modules less strong (looking at you double barrel tank cannons and laser beamed cannons)
- Stopped the world from being so advanced in Nuclear Reactor tech they were 35 years ahead
- You can now send ceasefire agreements regardless of war support or surrender progress to avoid death wars
- The Special Project "Double Shot Rifle" applies breakthrough and defense to the equipment rather than the units
- Increased the time for Infrastructure, Air Bases, Strategic Fuel Reserves, and Network Infrastructure so they aren't built so quickly
- Change the American congress decisions from using Tax Cost Factor so heavily and instead added a civilian factory commitment to the project
- Focuses that give wargoals for India will now generate world tension
- Increased the money from Syria's Bakdash so they get a little more of boon from going that route
- Increased the Command Power cost of abilities to account for the larger command power cap
- Reduced the generated tension cap to 20 from 30 to when you can embargo a nation
- Intervention laws will now increase the embargo tension generated limit similar to the justification
- Increased breakthrough requirement for Super Heavy Tank Guns and Early Supercarriers from 1 to 2
- Added requirement to nuclear weapon special project that requires Germany not having the GER_no_nuclear flag to do the project
- Reduced the frequency of the "Labour Unions Protest Migrant Events"
- Changed the balance in the Sudanese civil war a bit more towards South Sudan so they don't get steamrolled so easily
- "Satisfy the Middle Class" focus in the generic focus tree now requires a GDP of 95 billion
- Changed some CZE national spirits to be permament, but decreased their effects

Bugfix:

- Fixed the Automatic Debt Repayment forcing you into the negatives
- Fixed the configurable UI display for resources and tax cost factor breaking
- Fixed an issue that caused crashing if you hovered over 2 Syrian focuses
- Augmented Vision techs now correctly show after completing their special project
- Fixed the missing icon for High Efficiency Engines doctrine
- Fixed tank guns requiring heavy tank turret to be always mounted
- Fixed the Space Program special projects not being researchable due to needing a DLC tech
- Fixed trigger for Poland checking for removed idea, bloating the logs
- Fixed Libyan Oil Nationalisation and Tribalism modifiers not being transferred correctly during civil war
- Fixed the "Remove Previous Kleptocrats" in Serbia not removing an idea it should
- Fixed the Armenian focus "Communism Codex" focus making you have no religion icon
- Fixed some effects forcing duplicate gov_coalition_array members causing you to have a ton more government coalition support then you should
- Fixed Afghanistan event "Afghanistan Appeals for Support" showing they'll get something for saying no
- Overlord subsides should now properly cancel if the subject no longer exists
- Fixed a spamming error with regards to the KHZ for a bunch of idle sounds
- Fixed the OLVs showing up properly in the production menu
- Fixed division limiter always being on, even if it was turned off
- Fix Islamabad terrain picture's wrong position
- Fix Bengkulu & Jambi not appearing in the terrain picture section
- Fixed the German focus tree being soft locked due to "Nuclear Power" idea being referenced rather than Nuclear Energy
- Fixed the AI causing a hard crash each time it tried to research "Space Weapons" special project
- Fixed missiles not being consumed when launching nukes
- Fixed Missile Silo raids not being available for players
- Fixed Special Forces raids not correctly displaying damage
- Fixed Long Range missiles for AA not being researchable
- Fixed BAN, CAM, SWI, CAN, and BRM not spawning with troops nor stockpiles with no DLC
- Fixed a hard crash with relation to the Splintering of the USA events due to Submarine ballistic launch missiles (will be added back once PDX fixes this bug)
- Fixed the "COMSAT" money multiplier bug where if you shift clicked it would only remove by 1 instead of 100
- Fix the Saudi focus "Fundamentalist Coup" not switching the player from Saudi Arabia to Al-Qaeda
- Fixed the "United Visegrad State Breakup" constantly showing up
- Fixed reactor grade fuel being consumed twice from stockpile
- Fixed the United States of Europe decision "Integrate New Members" decision adding the trait "military reorganization" that cannot be removed
- Fixed the "Balance of Power" button covering up the "increase autonomy" button if you're a subject
- Fixed the Command Power increase not properly being displayed in the Officer Corps UI
- Fixed the debt event "High Debt Causes Company to Leave" taking your last factory and targeting states without factories
- Fixed the Transnistrian event "Gagauzian Revolt" causing Moldova to lose its core and then give the territory to Romania when they win the war
- Fixed renewable energy not being properly variable and instead being fixed to one spot
- Fixed the internal investments not properly expanding the speed at which a building is built locally
- Fixed Buran decisions re-triggering over and over and corruption level bug
- Fixed 2017 startup crash since someone else did the work (No we are not supporting it this is just something so we don't have to listen to people who post and spam crash reports.)
- Fixed leaders for Cote D'Ivoire, Paraguay and Uruguay in 2017 scenario
- Fixed Communist Cadres internal faction not being visible for countries that actually have them
- Fixed Sudanese Civil War ending news event not firing
- The ideas of Drafted Women and Volunteer women will now switch to no women in military if you are on "abolished military"
- Fixed polish historical Rosomak APC having incorrect setup
- POL PiS party politicians are now correctly appearing in the game
- Fixed typos in CZE loc file

Content:

- New/Improved Focus Trees: Israel, Brazil, North Korea, Transnistria
- Added focus shortcuts for a bunch of different nations such as Venezuela, Israel, Brazil, France and China.
- Added several new Internal Faction Events
- Added an option to not condemn raids if you aren't the one being attacked (before you always lost opinion)
- Made the Great Man-Made River for Libya into a special project
- National Space Program for Botswana now adds a civilian facility and gives a boost to Space Program special project
- Added Cruise Missiles and SAM buildings back for non-Gotterdammerung owners, and associated special projects
- Added Stealth Destroyers, Frigates, and Corvettes for non-Man the Guns owners, and associated special projects
- Expanded Brazilian content and reworked some older mechanics to new standards
- Added a flavor event for the U.S. F-35 program
- Added several new events for raids
- Added levels of severity to raid damage on resource strikes, higher success will lead to harsher effects
- Added a couple decisions to Spain for them to expand resource output in specific states once they complete the mining focus for that region
- New F-35 Program Mechanic for NATO & Major-Non NATO Allies
- Germany's Focus "Tighten Borders" should now reduce the migration law when the focus is taken
- Spain has a new mini-tree for expanding High Speed rail within the country
- Added an event that warns the player when finishing nuclear reactor research to turn on nuclear power if they are non nuclear
- Added a few new decisions for the Communist Cadres/Landowners/Oligarchs
- Added new "Expand Mines" decisions to the Spanish tree to add some more dynamicism and more resource extraction
- Added new focuses to the generic tree
- The North Korean branch's rework : Economic and military focuses have been changed. The junta branch has been updated, the Korean issue branch has been updated
- Changes in the focuses of Transnistria. A new branch has been added - General Lebed
- Retweak the Chinese aircraft MIO to match reality
- Added China 2000 Equipment Production Line
- Added 4 new Polish Military Industrial Organizations
- New shortcuts for CZE and POL
- New effects in POL military tree, adding funds for new MIOs and little boosts

Database:

- Added "Nuclear Energy" to all of the nations who have nuclear reactors
- Re-enabled submarine based ICBMs
- Add back NIRBM to nations who previously had the tech
- Added 1 nuclear reactor to the state of "Sindh" in Pakistan
- France now starts with Nuclear Power Offensive due to their "Warning Shot" doctrine
- Added 1 nuclear reactor to the state of "Western Bulgaria" in Bulgaria
- Fixed Canada getting extra technology it shouldn't
- Reduced level of naval base in Sirte from 4 to 1
- Marked the Naval Nuclear Engineering special project as done for countries that already have researched nuclear engines
- Corrected initial setup for Pacific island countries

Game Rules:

- Fixed the AI Easy/Very Easy Energy options not allowing achievements

Graphics:

- Improved the Luxembourg City terrain picture
- Added an icon for twin barrel mortar conversion module
- Fixed some missing terrain pictures
- Added a new icon for "Renewable Energy Hotspot"
- Fixed the air wing icons being all kinds of goofy (rockets are no longer helicopters.)
- Fixed the mission icon for Sam Missiles being missing
- Fixed the mission icon for ballistic missiles being missing
- Modernized the air mission icon for nuclear strikes
- A dozen new models
- Pack of new GFX for military equipment
- Improved the AI logic so that it pick the correct equipment GFX, name, and model depending on the country
- Centered the Cheondo religion idea icon
- Fixed the missile tab icon being offset from the other buttons

Interface:

- You can now see expected spending level and whether you are over or underspending directly in the Government Expenditures idea selection

Localization:

- Fixed missing tooltip for Medium Naval Nuclear Engines
- Improved the localization of the "Serbia Asks for Investments" event
- Added displays to some Italian and Venezuelan focuses which just added reactor material without notifying the player
- Fixed the Spanish opinion changes no longer appearing as they should
- Adjusted raid localization so that it correctly identifies who attacked who
- Fixed an issue with localization for the Iranian nuclear tree if the U.S. does not exist
- Added localization for Stealth Frigates, Stealth Corvettes, and Misc Naval Vessels
- 1965 Infantry Equipment is now called the correct name

Map:

- Redrew the map for the Nordic countries, Benelux and the British Isles

Special Projects:

- Super Heavy Tank Turrets are now locked behind both "Large Gun Tech" & 4th Generation Tank Hulls
- Increased the Civilian R&D Breakthrough cost for "Thorium Nuclear Fuel"
- Added a resource cost to "Super Heavy Tank Turrets" to help make it more balanced
- "Fully Autonomous Computer Frameworks" has now moved to "Human Imitation AI"
- Moved "Double Cannons" module for AFVs from the hull tech into a special project and buffed the stats a little bit
- Transport helicopters no longer require a special project if you don't have BBA
- Stealth technology for aircraft is now locked behind a special project
- "Super Heavy Tank Turrets" now is unlocked by the MBT Tech 3 (2015) so those meme projects are more late game content
- Fire and forget missile special project+hypersonic missiles

Technology:

- AFV steel and aluminium armour is now unlocked by both AFV hulls and light tank hulls
- Separated 1965 Artillery and SP Artillery into their own techs
- All vehicle machine gun modules are now unlocked by Small Arms 1965
- Moved SPAA Battlestations and Optical Guidance modules under Tank Computer Systems
- Moved SPAA Chassis modules to corresponding utility vehicle, tank hull and AFV hull techs
- Made the naval tech tree and air tech tree a little more compact so you don't need seven monitors to see them completely
- Heavy guns for battleships and battlecruisers are now unlocked by the naval armament techs instead of the hull techs

User Interface:

- Added Interest Rate and Energy Balance as a percentage to the configurable UI
- Fixed misalignment between MIOs and nuclear policies
- Fixed facility list being cut-off at the bottom
- Fixed clippy
- Fixed the free floating UI in the construction menu and made it even
- Energy Decisions for Nuclear Energy won't show up any longer if you do not have any nuclear reactors or if you are producing double the enrichment fuel of your consumption
- The requirement per building can now be viewed in the Economic Preview menu in the various building tooltips
- Left click for the employment percentage amounts has now been flipped to increase rather than decrease
- Expanded the UI for Rockets to be two per row so it's easier to find the missile you're looking for
- Fixed the UI headers in the menu being slightly off with their top

</details>

<details><summary>v1.11.0</summary>
v1.11.0

Achievements:

- Added a tooltip to clean up the tooltips for the African Nation achievements

AI:

- Added an exception to the leave NATO for Spain so Unidas Podemos will leave NATO
- AI Russia should no longer do "Challenge NATO" focus if its already at war
- Improved the purchasing AI for nations who are buying reactor grade fuel ensuring some rivals aren't purchasing fuel from one another
- The AI will now liberate Kosovo, Montenegro, and Vojvodina in the peace deals
- Improved the AI's choice for intelligence agency upgrades to make them more competitive
- The AI should no longer increase taxation if they are making a surplus of greater than 0.05% of their GDP in addition to pre-existing checks
- AI will try to design and build special facilities
- AI will try to dynamically raid opponents using the new raid system
- The US will try to protect and support countries that are major non-NATO allies

Balance:

- Reduced the amount of money gained from "Taxing Religious Institutions" Internal Faction decision
- Changed Polish KTO Rosomak to APC in historical afv decisions
- Slightly increased the risk and network strength required to increase corruption
- Urban Terrain expert now gives supercity terrain bonuses
- Changed tension back from Elian Gonzalez Affair from 8 threat to 2.5 again
- Greatly reduced Czech productivity growth from focus tree
- Skoda vs. Volkswagen, German AI will now get less support points

Bugfix:

- Fixed the Airforce Manpower display in the ledger
- fixed the War in Darfur spamming and spiking world tension
- Fixed the assassination of Burhanuddin Rabbani spamming a bunch of news events everwhere
- Fixed the idea for Czechia "Debt Problem" not being removed when you have no debt
- Removed the duplicative Weaken Egypt in the difficulty settings
- Fixed the income displaying improperly for for Redirecting Money From Proxies for Iran
- Fixed missing portrait for Natasha Romanoff for the United States
- Fixed the Mirage F1CT being a delta-wing design when it should be Swept Wing
- Fixed Russian focus "Withdraw from the SCO" properly removing you from the SCO
- Fixed Russia not having Mig21 without BBA DLC
- Fixed AfD being shown improperly when the REP is still the Right Wing Populist party
- Fixed "Left NATO!" opinion modifier being given when you are not in NATO
- Fixed the "European Union Member" opinion modifier being left on when you are no longer in the European Union
- The monthly tick will now reduce your faction's effects properly as time goes on instead of staying maxxed out
- Fixed NATO nations being accepted by America if they are no longer in NATO
- Fixed BBA techs not being able to be stolen via La Resistance
- Fixed the Cartels "Investigate the Banks" decision showing that if it fails it'll lose political influence
- Fixed an option in Libya's event file incorrectly removing a different party from the coalition array
- Fixed Iran's Revolutionary game rules working as intended when set and have historical focus on
- Fixed long_name appearing in other countries for their party name after nation leaders are changed
- Fixed every former European Union member being able to take the "Constitute the New European Union" focus when not being the nation that formed it
- Fixed the Ledger Land Doctrine Level will now proper show the level in the ledger
- Fixed the Ledger Airforce Manpower will now properly sort in the ledger
- fixed the Ledger Tax Cost Factor will now properly sort in the ledger
- Fixed the EU laws not properly removing the European Debt Crisis idea
- Added missing "Add Maximum Amount" button to the international market screen when buying equipment
- Keynesianism additional expense is no longer visible for every country, only for CZE
- Libya no longer flips cosmetic tags between Libya and one of the releasables
- CZE hidden national spirit fixed
- CZE brigade formation focuses fixed
- CZE and SLO will no longer rush Czechoslovakia branch, focuses after Czechoslovakia recreation are now available only for the player, unless historical setting is off
- CZE and SLO are no longer able to change flag after turning into Czechoslovakia
- Petr Pavel Russian mission Diplomatic Delegation fixed
- Weekly stabitlity in "It's Legal" focus is now correctly set as one-time modifier
- "Jan Cerny Leadership" focus has now correct triggers
- Fixed TOP and KDU-CSL coalition focuses
- "Strengthen Eastern Flank" focus now bypass if CZE is in faction with Russia
- Demand territories focuses in Czechoslovakia branch will now add cores to that states for Czechoslovakia
- Czechoslovakia opinion modifiers loc fixed
- Fixed POL ukrainian focuses in Korwin-Mikke tree

Content:

- Created additional raids of all types so you can engage in non-conflict conflict and more
- Added a number of special projects for all types and modernized it to our timeline
- Reworked the contemporay missile system to use the new content and systems available in the newest DLC
- Added a new agricultural tech line to improve your Agricultural Industry and reduce your ag workers through passive means
- Added BWP Borsuk to Polish AI templates
- Added a notification event every time your corruption is increased via the La Resistance Operation
- Reworked the Iran Nuclear section of the tree to be more in-line with new content
- Coded a mini-mechanic for the Russian Sapce Shuttle "Buran"
- Special Facilities are integrated into the "Education Budget" and have a running cost which is additive to the education budget
- Added the Columbia disaseter and US shuttle launches content
- Implemented a variety of landmarks for various nations in the new system with the latest DLC
- Added a Gamerule for U.S. AI to inaugurate the historical president on the 20th of January each election year
- Non-recognised countries and non-state actors can no longer be major non-Nato allies
- Changed number of building requirements in the generic focus tree to require a certain amount of GDP instead to accomodate for non-vanilla buildings
- Added focuses to the generic focus tree for the creation of a research facility
- Skoda/Czech exclusive engine technologies are now increasing Skoda Productivity Growth by 0.01 point
- Libyan tribes will no longer be able to immediately revolt again once annexed. The revolt can only happen again once the area has been re-cored by Libya
- Added a decision to expand the nuclear sector in the ideological struggle menu for socialists

Database:

- Added Libya to the Strengthen/Weaken list
- Distributed starting rocket sites to countries with former buildings
- Distributed starting Order of Battles (OOBs) including new missile stockpiles
- Some technologies are now locked behind special projects for more niche sub-class technologies that are not common standard'
- Removed the air defense system as SAMs are now a missile unit that can be deployed at airbases
- Removed several redundant buildings and rebranded the "Missile Silo" as a catch-all for missile based assets
- Distributed starting special facilities to various countries
- Kurdistan no longer starts with both NSB and non-NSB SP Artillery
- Reduced Libya's military spending by one level at game start to help with budget
- Removed most of the airbases in Northern Mali

Graphics:

- Custom new scientists portraits to support the new special projects
- 10 new spy portraits for each culture group (~60 new spy portraits)
- Custom MD GFX for all raids
- New GUI look for Special Projects to make it more in-line with MD's timeframe
- New building models for a variety of building types including Anti-Air (SHORAD in-game), landmarks and more
- Hundreds of new icons for ground, air, and missiles for the new technology
- Infantry models overhaulted all around. They are now using an upgraded shader Uniform/skin variation also added to a handful of specific nations
- New ship and air models (10+ models)
- New models for missiles and so on during flight while using missiles (12+ new models)
- Added a variety of effects such as fire to buildings, tracers and more

Localization:

- Added additional tooltips to the older space system to make it easier to digest
- Removed localization from the doctrines that imply it'll cost money but doesn't actually cost money
- Fixed Viktor Zolotov having a typo in his name

Map:

- Added several mountain ranges and implemented them as impassable terrains

Performance:

- Removed a number of multi-loops from the missile system to streamline the process
- Removed a lot of bloat files and code lines from former systems to improve performance
- Optimized on actions so they are cleaner and have less hiccup when running on speed 5
- Startup time is faster now due to reduced and improved cleanup on checks

Sound:

- Added new sound effects to models

Quality of Life(QoL):

- Added an "Automatic Debt Repayment" option in the debt screen to automatically pay down your debt using 25% of the income you gain each week
- Adjusted the bottom right buttons shortcuts to be shift+x so you can still hotkey armies to 1-4
- Added focus tree shortcuts to the Spanish tree
- "Enrich Uranium" for nuclear fuel is available in the Energy UI now so you no longer need to pivot back and forth
- Moved "Utility Vehicles" to the Infantry Equipment line so there's a few less tabs to open

</details>
