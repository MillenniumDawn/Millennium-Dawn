---
title: v1.12.0 'Every Tank an Upgrade'
page_id: changelog-v1-12-0-every-tank-an-upgrade
order: 13
---

# v1.12.0 'Every Tank an Upgrade'

> Looking for v1.12.1+ hotfixes? See [v1.12.x Hotfixes](/changelogs/v1-12-0-every-tank-an-upgrade-hotfixes/).

## v1.12.0d - 7/02/25 Hotfix

v1.12.0d
### AI
- The AI should now actually deploy planes when at war with the United States (China and Russia were the worst offenders.)
### Balance
- Increased the benefit of the "Improve Local Infrastructure" internal investment from 15% to 20% for all infrastructure types
- By default you can no longer sending investments to countries while you have the "Bankruptcy Incoming" mission active
- Added requirement for Transnistria to be independent to complete focuses with wargoals to prevent early WWIII from happeneing
- Command Power has replaced Army Experience in the PKK mechanic for Turkey
### Bugfix
- Fixed the broken display for the "Storm the Tulkarm Fort" decision not showing up with the right information
- Fixed the Israel "The Passover Massacre" operations when failed Gaza Strip becomes overlord of Israel and instead changed it so that Israel becomes the overlord over the Gaza strip
- Fixed the "Resource Exports" not properly taking into account subjects when calculating your resource export income
- Fixed the "Rafale Planes" focus not properly giving the Rafale M to India
- Fixed the broken Romanian tooltips for the economic focuses
- Fixed the stealth corvette techs not properly being limited to 2025 and instead being able to research without a tech research penalty
### Database
- Added a new scripted trigger "is_autonomy_that_cannot_change_level" to check if a country has a special autonomy level that cannot be changed
- Changed Destroyers back to being Capital Ships instead of Screen Ships. This will be reverted in a future naval rework
- Removed older "anti_air artillery" type from ship classes for the older missile system
- Removed a ton of duplicate equipment variants for the "Error Stop" variant so the game should start a bit faster
- Russia no longer starts with the "Naval Guns 2025" tech in 2000. Silly time travelers
### Game Rules
- Added a new Game Rule "Disable Investment Bankruptcy Lock" that allows you to send investments to countries while you have the "Bankruptcy Incoming" mission active
### Graphics
- Updated the icon for the Nigerian Idea "Blood Oil"
### Localization
- Changed all the vehicle hull names from "Light Tank" to "Armored Hull"
- Added a tooltip to the first "Armored Vehicle Hull" tech that explains you only need to research this
### Performance
- Improved the performance of how the on actions are triggered for civil wars so there is less idea drag



## v1.12.0c - 6/27/25 Hotfix

v1.12.0c
### AI
- The AI with generic focus tree should no longer take continuous focus "Increase Autonomy" if they have special (i.e. can't upgrade) autonomy level
- AI should no longer try to increase its autonomy level if it has same ideology as overlord and current autonomy level is not too low (lower than sattelite)
- AI will take into account interest rates before paying reparations following a raid
- AI who do not have the "Nuclear Energy" idea will no longer build enrichment facilities
- AI should no longer try to build nuclear enrichment facilities if they do not have more than 5 nuclear reactors (i.e. don't enrich your own if you don't need to.)
- Fixed the AI strategy plans for China not working as expected
- Improved the AI for Nigeria handling its religious conversion mechanic
- AI is likely to go to war over debt if the target is in a major faction (CSTO, NATO)
- Iranian AI will be more likely to stir trouble in Yemen
### Balance
- Moved the added manpower from the Automatic Loading System to the Manual Loading System for tanks
- For now the Russian Army Focus "Opportunity To Buy Off The Army" will give 0.015b weekly income per 10 million population instead of fixed income of 0.150b weekly
- Made the United Kingdom focus "Towards The Right" remove the "Part of the 1st World" idea
- Added an influence requirement to launch the coalition of the willing attack on Iran
- Rebalanced Turkey's army anger modifiers
- Reduced the amount of reparations paid; down from 10% of GDP/PP to 3%
- Rebalanced modifiers from Iran's prime minister decisions
- Rebalanced modifiers from Iran's presidential decisions
- Made the Coaxial Engines for Helicopters jump by 5 KM/H per generation
- Removed the piercing value from the Modern Smoothbore ATGM and better laid out the ATGM hard attack by increments of 4
### Bugfix
- Fixed the Weaken Libya and Weaken Venezuela modifiers not properly weakening the countries
- Fixed having no scrollbar in special project window
- Fixed having no priority buttons for equipment in Production Tab
- Fixed requiring 7 Billion of Total GDP instead of 7 Trillion for Chinese Economic Focus "Focus On Strategic Industries"
- Fixed reducing domestic independence for Russian Economic Focus "Chaika"
- Fixed swapped rewards from Improved Wireless Communication special project
- Fixed Chechnya becoming a puppet if you successfully white peace with Russia
- Fixed Chechnya having Ramzan Kadyrov instead of his father for 1 day until focus "Ahmat Kadyrov"
- Fixed the Nigerian event "Nigeria Seeks Foreign Grants" not properly giving influence to the country that grants the money
- Fixed the Brazilian focus "Integrate UNASUL" not properly adding the UNASUL faction to the country that completes the focus
- Fixed the Destroyers for non-MTG owners being unable to deploy
- Fixed the Iraqi focus "Russian Investments" display not giving the proper influence
- Fixed a bug where Eastern European countries could apply to the F-35 program without being in NATO or a Major Non-NATO Ally
- Fixed a bug where Hezbollah gets annexed by Israel if it wins the 2006 war
- Fixed a bug where the portrait of an Iranian Prime Minister was not displayed properly in the GUI
- Fixed broken Kasyanov ideas in Russian Focus Branch PARNAS
- Fixed being unable to research helicopter technologies for non-BBA owners
- Fixed the Spanish focus "Hispanidad" giving influence on yourself as Spain
- Fixed the "Sectarian Groups Start to Seek Independence" mission in Syria cycling without actually triggering
- Fixed a number of minor issues w/ Linux being unable to find specific graphics files due to file case sensitivity
- Fixed the Bosnian decision "Unite Yugoslavia" not properly annexing the right nations
### Content
- Added an option to blacklist countries from re-applying to the F-35 program as the United States
- Tabled Iran's MEK mechanic
- Added an event for the end of the Nigerian "Religious Civil War Mission" if you are able to successfully convert everything without the Islamic civil war triggering
- Added 8 new American leaders to extend presidential cycles for another 16 years (4 DEM, 4 REP)
- Added an option to mend ties with the United States as I.R. Iran
### Database
- Added the starting spirit of "Nuclear Energy" to Iran
- Blocked the "Electronic Government" special project from being visible for other nations other than Iran
- Adjusted some triggers in Iran to require Intel instead of Influence
- Gave Poland the "Missile Experimentation" special project and Early SAMs/SAM 1 so they can deploy their starting missiles
- Changed Helicopters from requiring the "Aircraft Project" special project to requiring the "Helicopter Project" special project
- Added a new strengthen/weaken setting for the Czech Republic
- Adjusted the Hezbollahi Focus "Steal the Bastards" to require the United States has to have declared war on Iraq, has Iraq as a subject or has military access to them
### Localization
- Some minor localization fixes for Russian and its subjects content
- Added missing localization to two Iranian national spirits
- Rewrote the entire Russian localization file for better grammar and readability
### Graphics
- Fixed some inconsistencies in the VLS naval tech icons for the Naval Designer



## v1.12.0
v1.12.0
### AI
- Rewrite the influence AI to closer to the investment AI where it evaluates by country context
- Fixed the AI not wanting to take European Parliament measures due to them having a lone factor of 0
- Improved the AIs performance when evaluating whether to push for laws or decisions
- Improved the AI's willingness to naval invade other countries if they are within range
- German AI improved, US and GB will keep troops in Germany, until called back or leave fraction
- The Debt Assumption AI now has a 90 day cooldown to prevent it from being spammed
- The Nigerian AI should be more intelligent in exploring their focus tree to better assuage their economic issues
- Added some new AI modifiers to make them more likely to support particular EU laws when they're in the council
- Improved the AI so they are moore likely to actually take decisions and laws as appropriate

3D models:

- Added 150+ new infantry models and textures
- Added dozens of new vehicles and texture variations for them
- Added dozens of new ships. Hull visual model progression also added.
### Balance
- Adjusted the political power from 100 to 150 when you succeed in fixing the bankruptcy
- Improved the EuroArmy Brigade so it's not nearly as shit for the European Union
- Reduced the industrial cost of the heavy guns by half of the cost
- Added a negative foreign influence modifier as you increase your intervention law from anything over isolation
- Adjusted the EU-Turkey Deal to not be able to be done unless Turkey is not in the European Union (no it does not block any law progression)
- Rebalanced the Fossil Fuel Industry vs Renewable Energy choice in the Brazilian focus tree in the economic tree
- Added a clamp so the minimum possible workforce that can be in a country is 0.01 in total
- Added some Western Support to the NATO member idea and some defensive stability and war support to better represent it being a defensive alliance
- Reduced the speed penalty of the Double Barrel and Laser Beam cannon
- Rebalanced some of the Ethiopian decisions so they add influence to Ethiopia from china but reduces costs on Ethiopia for expanding infrastructure
- Halved the Maximum Survivability and Dispersed Dispositions land doctrine Experience Loss by half to 7.5 from 15%
- Increased the migration rate from the open borders idea by 10%
- Added tourism income to the Kaaba for whomever controls it to represent the massive amount of tourism and pilgrims to the area
- Pre-Accession Assistance now cancels once you become a member of the European Union
- Adjusted Utility Vehicles doctrines that have a armor value to have a hardness value as Utility Vehicles do not have armor
- Fixed the broken Bosnian ideas that gave you insane amount of division recovery rate
- Some Likud focuses now only increase corruption when leader has corruptible trait
- Added starting intelligence agency to Israel
- Reduced the productivity modifier of Agriculture Districts by 10% from the Modernized GMO
- Made 2035 Cruise Missiles worth using in general
- Reduced the time for the missile experimentation project down
- China no longer starts with 2025 Light Guns technologies for ships
- Increased SAM air superiority per wing from 5 to 15.
- Added a 2% boost to Air-Ground-Attack on the BBA radar upgrade, to represent ground search radars
- Made the German Soldiers Popularity mechanic for the War on Terror a little more random but a little easier to manage
### Bugfix
- Fixed a German MIO giving piercing despite Small Arms not having Piercing
- Fixes German Content Bugs, like License production, and minor stuff
- Fixed the wrong colour in the display names in the laws
- Fixed the Romanization decision not properly adding cores to the new states in Morocco
- Fixed the Ideological Power for Communists actually increase worker requirement by 25% instead of the intended 15%
- Fixed Cuban focus "Revive Cuban Metallurgy" having a hidden effect that adds the industrial complex
- Fixed a random Serbian division starting in the southern Indian Ocean
- Fixed the infinite political power exploit giving infinite political power when you have international investments reinvestment going
- Fixed the spamming error from the Syrian on actions
- Fixed the "Complete Full Use" not actually being able to be taken if you are on Neo-Imperialism instead of Global Interventionism
- Fixed the "Air Space Incursion" event showing up if you haven't researched anything that unlocks SHORAD Sites
- Fixed the "Restoration" focus for Brazil not actually setting your name to Empire of Brazil
- Fixed "tech_info_special_description_bottom_margin" spamming in the error log
- Fixed the buttons in the navies menu not properly changing when selected for aggressiveness, splitting for repain and otherwise
- Fixed immigration not scaling properly with unemployment
- Fixed the "Workers Party Alignment" decisions not showing up properly in the decision menu
- Fixed the Total Workforce modifier from GDP/C getting too low and causing the workforce to go extremely negative
- Fixed Israel focus "Manama Economic Conference" not being able to be taken if Palestine is not a subject
- Fixed Socialism not meeting the same requirements as other subideologies for boosting
- Fixed the boost triggers showing up with Turkish ideas despite you tnot being Turkish
- Fixed the Ethiopian focus "Secure the Eritrean Border" being locked if you integrate/own all of Ertirea without them existing
- Fixed the Ethiopian decisions regarding rail investments looping indefinitely
- Removed the generic.dds portrait error for all of the political leaders
- Fixed the airforce cost calculation being too high due to the stockpile being duplicated
- Fixed the Israeli ideas not properly impacting the proper variable for the Israeli money system
- Fixed the nationalist drift for Fascist Demagogue instead of salafist
- Fixed being unable to take "Gigantic Spending" idea due to it missing the trigger "Is at War"
- Fixed the Carlist monarchs not properly taking charge in Spain when you choose the absolutist focus tree path
- Fixed El Salvador not starting with a legacy land doctrine
- Fixed various instances where random choice in decisions was always giving same outcome
- Added Bypass to Chinese focus "The Bear's Backyard" and "End US Hegemony", Preventing China could complete these focus even though the US and Russia have been puppeted
- Fixed requirements in german focus
- Fixed German Equipment events
- Fixed the Russian Debt Negotiation event not actually modifying the debt of the Central Asian state that requests the renegotiation
- Fixed the "Integrate Bosnia" decision showing up for Serbia even though they already have cores on the states
- Fixed Lahak intelligence idea giving +100 air volunteer cap
- Fixed many incorrect Israeli focus prerequisites (especially in the foreign policy part)
- Fixed last stage of negative Eddaic Ghost idea being impossible to remove
- Fixed Jewish Might focus tree - missing war goal, state claims, incorrect army size requirement
- Fixed Israeli political ideas being removed during election and coalition forming
- Fixed many Israeli political ideas not being removed when their party left government
- Fixed AI weights for Israeli China vs. USA focuses
- Fixed Israeli focuses transferring UAV, add BBA support (China, India, Kurds, Armenia, Azerbaijan)
- Fixed Israeli navy focuses - add non-MTG support, fix subs spawn location
- Fixed Israeli airfield focuses being switched
- Fixed Israel aircraft focuses, add BBA support
- Fixed several Israel focuses and events that cancel Non-aggresion Pact instead of giving it
- Fixed Israel getting resource rights twice (diamonds focuses)
- Fixed Israeli Taba conference focus
- Fixed several Israeli ideas giving absolute modifiers instead of factor
- Fixed Israeli Arish Ashkelon focus firing event for Iran instead of Egypt
- Fixed Israeli Hezbollah/Lebanon focuses requiring intelligence with = rather than >
- Fixed wrong prerequisite focus on Israeli Daniel's Lion cage
- Fixed Keep Ammonia giving techs Israel already starts with
- Fixed Move Tankers South removing random (and at the start non-existing) nuclear power plants
- Fixed wrong tag in Israeli Green Blue deal
- Fixed wrong scope in Israeli Netanyahu populist focuses
- Fixed Israeli Travel to Brazil focus calling wrong event
- Many miscellaneous Israel focus tree fixes
- Fixed the net nuclear fuel display showing there is consumption when nuclear power is disabled
- Fixed the "Man the Guns" DLC not being properly checked for when using special forces raids against naval bases with respects to landing craft techs
- Fixed the air doctrine focus in Ethiopia giving the wrong category of doctrine reduction (silly Ethiopia airplanes are in the sky!)
- Fixed Tajikistan not properly being able to do the Khorugh Accord decision
- Fixed the duplicate weight in various raids causing it to make the weights be redundant
- Fixed the EU vote events not being hidden when minor popup is stopped
- Fixed Bill Clinton staying as the leader
- Fixed the "Facility Drone Strike" raid not properly showing up for facilities even if a player has the required suicide drones
- Fixed the Cuban High Command "Ulises Rosales del Toro" not having any trait
- Removed a bug where the expected military spending modifier was not being applied properly and instead applied the expected military spending modifier to the Non Power and No Military ideas
- Fixed a weirdness issue with the European Empire USoE focus having a bunch of swapping parties.
- Fixed POL focus WB Warmate not granting tech bonuses for BBA owners.
- Improved POL social media focuses tooltips
- Improved POL focus C-130 Hercules
- Several fixes for Polish-Ukrainina war escalation, triggering now only in offensive war against Ukraine and when UPR party is in power.
- Early Submarine Engine is now researched on start for POL
- Fixed POL missile focuses, removed ALCM focus
- Replaced requirement for Visegrad focuses to not require countries to be the same ideology as Poland, instead they cannot be at war with each other
- Fixed POL Purchase of Foreign Board Aircraft not giving planes.
- Fixed CZE brigade deployment focuses not deploying brigades
### Content
- NEW/IMPROVED TREES: Armenia, Nigeria, Iran
- NEW TAGS/COUNTRIES ON MAP: People's Union Of Kurdistan (PUK), Islamic Emirate Of Kurdistan (IEK)
- Ecuador's starting leader Jamil Mahuad with the lawyer trait
- Galicia, Silesia, Andalucia, Canary Islands, Basque, Bavaria and Greenland can now join the EU via Internal Enlargement
- New game rules for countries : Estonia, Romania, Poland
- Minor changes in the military tree of Greece
- Added a new Internal Investment for Brazil that allows them to reduce the penalty of the Amazon Rainforest Conservation System in local states impacted by it
- Removed restriction for the "Space Program" special project being limited to regional power and above
- Added state modifier "Graveyard of Empires" for Afghanistan
- Added new balance of power for Syrian Democratic path
- Adjusted and improved various parts of the Syrian Focus tree
- Added Conditional Peace Deals as a system for peace deals to prevent forever wars
- Removed the outlook requirement from the "Assure Intellectual Freedoms" focus in the generic focus tree
- Added a new Shanghai Cooperation Organization members list GUI
- Expanded the list of SCO member countries
- Re-added the J-10 series historical design for China, unlocked by decisions now
- Added more options to the Economic Aid event granting more influence for more money and is now based on GDP over debt
- simplyfied german oob
- add visby-class as steath corvette
- improve german navy focus tree
- Added state highlights for Serbia's "Integrate Bosnia" decisions
- Changed many timed, inconsequential Israeli focuses into permanent ones (usually tied to party)
- Reworked Israel events so that relations as well as Israeli influence in the target country matter
- Improved Restoring Yamit - allows to transfer Sinai if Egypt is subject of Israel
- Bulgaria: Focus trees of the Army, Diplomacy, and Economics have been reworked
- The United Kingdom "Improve our Small Ships" focus now also reduces the costs of corvettes and frigates
- The United Kingdom naval focuses now gives additional naval experience to the country
- Added new Nigerian focus effects and added some more dynamics to make the tree a bit more competitive
- Added several new generals to Israel
- The Swiss should no longer join NATO while the have the neutrality ideas
- Removed the mutually exclusives in the Romanian focus tree for the Romanian economic focuses as they didn't need to be ME in the resource sections
- Created Unified Vehicle Designer. All ground vehicle designs now come off a singular hull, and the designer now works in line with the base HOI4 designer.
- Removed armored air assault subunit.
- Reworked PKK Mechanic for Turkey
- Flavor decisions for Kurdish unification in the Peshmerga region
- Removed Turkish Cypriot & Kurdish tree until a more comprehensive rework is ready
- Renamed the POL "Modernization Of Su-25" focus to "Extend MiG-29 Fleet" and changed its effects.
### Database
- Adjusted the European Debt Crisis timer has been adjusted to 900 days to better allow for time to pass the required laws
- Adjusted the Naval Doctrines to include stealth corvettes and stealth frigates
- Added FAO, BAY, BSH, CHU, CRM, DON, DPR, DRP, FAO, GGZ, HPR, HZG, KAE, KLM, KOM, KSH, LAG, LPR, LRP, MEL, MLR, MOV, NEE, OPR, PRP, RSK, RUS, SIL, SPA, TAT, TRA, VOJ, VRP, VTB, WLC to European country group trigger
- Added ADJ, ADY, DAG, GOR, IKR, ING, KCC, KBK, KUB, SAZ, TLS to Middle Eastern country group trigger
- Added ALT, ARK, BDA, BRY, CHS, CKK, CSB, ESB, FAR, HWI, KAM, KHM, KAS, KHA, KHS, KRP, LAD, MAN, MEG, RYU, SIB, SIK, TUV, URA, YAK, YAM to Asian country group trigger
- Added ARC, ASK, FLA, IDH, KAN, LKT, NYK, UDT, USB to American country group trigger
- Added ARC, ASK, CAL, CAS, CMB, CSA, FLA, GLC, IDH, LKT, NEN, NYK, TEX, UDT, USB to North American group trigger
- Added RGD, SLA, TAM, TRC, YUC, ZAP, STL to Central American group trigger
- Added FGU, PAT, SPL, SUL to South American group trigger
- Added ADJ, ADY, CHE, DAG, GOR, ING, KBK, KCC, KUB to Caucasus group trigger
- Added HWI to Oceania group trigger
- Added ASK, CKK, GRL, KAE, KOM, NEE, QUE, SIB, YAK, YAM to Arctic group trigger
- Added CNR to Spanish Speaking group trigger
- Added all Russian Subject tags to Russian Proficient group trigger
- Adjusted the Kosovar tax rates to 25% for population and 15% to corporate tax rate
- Expanded the number of political parties that can go up to Neo-Imperalism (democracies can't intervene in the same way and invade whatever but they can still invade nations who cause tension with no other tension requiremments)
- Added Amapá and Roraima to the Amazon States (oversight as they are most certainly in the Amazon)
- North Korea no longer can use the "Hold Elections" decision
- Added vanilla (non-DLC) starting techs Israel was missing
- Adjusted the maximum number of quick wings for deployment from 3 to 8
- Added a new scripted effect to clear the EU vote variables when a vote fails to cleanup (effect is called EU_emergency_vote_clear)
### Graphics
- Fixed the "Combined Defense Industries" idea icon from missing from the generic ideas
- Fixed bad file path errors in graphics in the error log when using Mac/Linux/Steamdeck
- Fixed multiple Israeli ideas missing icon
### Localization
- Fixed a missing localization for a intervention law for the Greens for Isolation
- Improved the system explanation for Brazil's Amazon Conservation System so it's easier to understand what to do
- Improved and rewrote a lot of the Syrian focus tree localization to be more well written and additional lroe
- Bunch of Israeli English localization fixes
### Map
- Updated the map for Yugoslavia, Romania, Albania, Bulgaria, Greece, Turkey, Cyprus, the Caucasus and Southern Russia

Quality of Life (QoL):

- Added a decision that allows you to disable raid event notifications of raids that do not pertain to you
- Added Unemployment Rate to the Economy Overview when clicking on nations
### Performance
- Removed some redundant code in the European Union scripted effects
- Rewrite the Nepalese on actions to not allow other checks to check whether they're Nepal or Maoist Nepal
- Improved the performance of the on_actions on monthly so they're about 15% faster per month
### Sound
- Added unit voice-lines to Ukraine
- Added unit voice-lines to Saudi Arabia
- Redid unit voice-lines for Iraq


