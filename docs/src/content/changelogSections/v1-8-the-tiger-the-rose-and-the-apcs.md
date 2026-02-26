---
title: v1.8 'The Tiger, The Rose, and the APCs'
page_id: changelog-v1-8-the-tiger-the-rose-and-the-apcs
toc: 'off'
order: 9
---

# v1.8 'The Tiger, The Rose, and the APCs'

<details><summary>v1.8.8 - 1.13 Compatch</summary>

Bugfix:

- 1.13 compatibility

Content:

- Disabled Vanilla International Market
- Converted MD's Defense Companies to MIOs

Database:

- Removed an unusued Equipment Type "Engineering Equipment"
- Removed an unusued Equipment Type "Land Drone Equipment"
</details>

<details><summary>v1.8.7 - Patch</summary>

AI:

- AI should now try to have globalized export economy if it has mp optimization idea
- Improved AI focuses so the AI should research more effectively
- AI should now research Special Forces, Trains, Light Drones, and more
- Added more AI will do triggers to help keep the AI from researching 2045 shit in 2030
- AI should no longer research Naval Tech if they don't have dockyards
- AI on harder difficulties gets a research reduction now to assist in keeping them competitive

Balance:

- Rebalanced some of the focuses for Myanmar in the military tree
- MP optimization annexation decisions will no longer annex countries if they are controlled by players
- Rebalanced Speed of Tanks,APC,IFV and SP ART equipment to prevent extreme late game speed
- Rebalanced some designer companies bonuses to provide more adequate modifiers based on quipment type
- Rebalanced Armenian post-2008 economy tree.
- Removed pp requirement from diplomatic focuses.
- Tweak the requires of Democracy Focuses of China
- Reduced Desperate Defender's dig in speed
- Rebalanced the Manipulate Politics button
- Upped the weight on End of Cartels so the event fires sooner
- Buffed End of Cartels a little bit
- Tactic swap frequence increased from 36 to 24
- Land unit training xp gain increased from 0.0025 to 0.0035 - should be around 40% faster training
- Max AA damage reduction decreased from 0.95 to 0.90
- Removed railway gun bombardment from "elevated engineer corps" spirit, replaced with +10% max entrenchment
- All army spirits reducing xp gain reduced from -50% to -10%
- Increased bonuses provided by corruption events
- Decrease damage done to planes by strat bomber by 10 times
- Decrease overall damage of strat bombing from 45 to 20

Bugfix:

- Fixed localization errors in the Iranian revolutionary tree
- Fixed party icon not appearing for one of the Iranian parties
- Fixed invisible army XP icon for ukrainian decision to "Reform the army"
- Fixed still having British Special Treatment once you left EU
- Fixed missing shared slots for Myanmar's dockyards
- Fixed a focus in Myanmar's tree that didn't give you the naval bases
- Fixed the Lehman Brothers Event Doubling Up costs
- Fixed Reclaim Eritrea focus for Ethiopia requiring ERI to be a puppet
- Fixed typo in Early Cold War Assault Cannon
- Reducing taxes as France should in fact now reduce taxes
- Fixed Japanese faction bugs in the tree
- Fixed Kurdistan fighting NATO like One Punch Man
- Fixed Shepard's Party Icon for the USA
- Annex oceania decision now actually annexes whole oceania
- Creating and joining faction via mp decisions will now correctly remove you from NATO/CSTO
- Fixed Libya not getting annexed by mp decisions
- Fixed UK having non-nsb arty tech with NSB dlc
- Fixed UK not getting correct "Saxon"
- Fixed carrier wing bug related to overstacking
- Fixed Duplicate Italian leader on Padania secession
- Fixed 127mm gun IV bug that prevented module usage
- Fixed typo in an Italian utility vehicle name
- Fixed Georgian Communist tree focus requiring itself.
- Fixed S.A.Rs cannot use its current flag and name
- North Korea leader in 2017 is historic now
- Blue Water Expert and Green Water Expert are now earnable
- Desperate Defender can now be earned while defending
- Fixed the display for a focus effect in the French tree showing the wrong thing
- Redid the French space program income. It should no longer bug after ten launches
- Fixed division names from focus Flames in Baku!
- Fixed Donbass war still being active when Ukraine capitulates
- Fixed an exploit in the Investment System
- Fixed GCC focus "Regional Upheaval"
- Now brazilian focus "Anti Corruption Measures" will be bypassed if you already have very low corruption
- Fixed having NATO membership applications for USA if they are not NATO member, now any major country in NATO will have applications instead.
- Cartel decisions should now cancel when you get end of the cartel event so them pesky
- Fixed SOV units having invisible SP AA brigade
- Fixed gap in one of SOV unit templates
- Fixed Musandam Invasion requesting the non-MTG tech.
- Fixed Battlecruisers and Battleships being free

Content

- Revolutionary Iran will no longer start with IRGC generals, instead new generals will be given
- New Italian starting division templates, added 2 missing Italian brigades
- Added small decision to ask for Donbass reintegration in case Ukraine is Russian puppet
- Redid German division templates for more accurate representation
- Fixed name prefix for Chinese Navy.
- Expanded Namelist for New Zealand Navy and Mexican Navy.
- Added Names for Burma, Thailand, Indian, Portugal, Bosnia, Syria, Iceland, Romania, Poland, Norway, Latvia and Lithuania Navy Ships

Localisation:

- 38th Parallel Decision's title Localisation reworked
- Fixed typo in Spanish ideas for Deindustrialization
- Fixed typo in the Aux Electrical Engine tech and module
- Added a display for the Equipment Purchasing system for people to see the current procurement time
- Clarified how to cancel a auto influenced nation
- Fixed the loc for the Debt War to make more sense

UI:

- Added a shift click to the auto-influencing button to clear all currently influenced nations at once

</details>

<details><summary>v1.8.6 - July</summary>

Bugfixes:

- Fixed the Auto-Influence only influencing the first one
- Fixed the Auto-Influence not correctly applying spread_influence
- Fixed Kim's Successor Focuses, which lead North Korea can change its leader normally after Daddy Kim's death
- Fixed UNSC decision trigger of Unified Korea
- Fixed Russian loc
</details>

<details><summary>v1.8.5 - June</summary>

AI:

- Fixed the AI investing in states that are below 50k pop or inhospitable
- Expanded the AIs ability to determine if a low pop state is worth investing in
- Changed some AI evaluation for states to make them more in relevant places
- Infrastructure investments now considers a states resources to determine if it needs an investment
- AI will evaluate whether a state has a free building slots
- AI will evaluate whether to invest fuel silos
- Ukraine now should finish LPR + DPR in case SOV does not exist
- Ukraine now may pick up a fight with Russia if its strong enough
- AI Comoros should no longer pursue the French focuses at the end of the tree
- Indonesian AI will be more likely to combat Salafism
- Tweaked AI behavior for Finland so they don't declare war on Russia

Balance:

- Most countries now will no longer lack basic equipment on start - they still may lack AFVs etc
- Rework division templates for: FRA, ITA, GER, CHI, JAP, POL, SPR, SOV, UKR, ARM
- Added civilian techs for most countries of 1st and 2nd world
- Remove the pp cost of "The End of Arduous March"
- Removed more influence requirements for Ukrainian tree
- Balanced Iranian political power & stability gain being excessive
- You now need to get 50 opinion with a EP seller to purchase equipment
- Aceh will now have an option to join Indonesia, rather than being fully annexed
- The national spirit which gave a -95% attack debuff against Aceh for Indonesia is now visible (Was hidden before)
- Increased the PP gain from refusing Economic Aid timer (90 days to 180 days)

Bugfix:

- Fixed the auto influencers automatically deleting when you set one
- Fixed Korean unification event for Unity Government/South Lead unification
- Fixed Azerbaijan hunta event firing multiple times, setting incorrect party in power, and referring incorrect leader in description
- Fixed Kim's Successor Focuses, which lead North Korea can change its leader normally after Daddy Kim's death
- Fixed ability to get Azov brigade as Ukraine with emerging/non-aligned outlook
- Removed Bill Clinton from leader list so he stops being immortal
- Fixed Ukrainian Revive the Ukrainian Navy naval base not being built properly
- Fixed Great Lakes Confederation having a core in Portugal
- Fixed Agency Icons not working properly
- Fixed a crash in Singapore's Operation Enticement
- Corrected spelling errors in Indonesian content
- Wahids impeachment should now function correctly
- Fixed a display error in the Spanish tree for the Monarchists
- Fixed a bug that merged all italian starting afv versions of a same type into one
- Fixed egyptian oil deal italian focus wrong state bug
- Fixed a situation that could prevent you from receiving a roman expansion casus belli

Content:

- When a civil war triggers, both sides now get a debuff to slow down quick civil wars. The debuff will slowly go away
- Reorganized Iranian Political Tree & added 2 new paths
- Added new GUIs for Iranian decisions & mechanics
- Add Macau SAR to the game
- Significantly increased complexity of Italian Civil Wars through modifiers that slow down the fight and the spawning of volounteers
- Added more decisions to Italy to interact with internal factions
- Updated Starting Italian armored vehicles templates, added otomatic as a suboptimal (but sexy) unique tank design
- Added more decisions to fight mafia and slighlty rebalanced mafia power drift
- Added one more italian enviromental policy

Graphics:

- New political icons for SLO
- Fixed the white box issue for people using DX11/OpenGL
- Fixed Iranian 3D Infantry model from glowing (Should be orange camo now)
- Fixed the compression on agency icons so they should now function in-game properly
- Fixed quality issues in the tank profiles for the designer
- Fixed intelligence agency logo for Indonesia
- Fixed the UI bug for the advisor trait type

Localisation:

- Renamed "2nd Generation tank hull" to "2nd/3rd Generation tank hull" so I am left at peace at once
- Fixed Advanced Heavy Howitzer description
- Japanese localisation adapted(Even we have no Japanese localisation file at this moment)

Map:

- Modified state layouts for Chad, Burkina Faso, Mali and Niger in preparation for Libyan content
- Add Macau and Kalmykia
- Adjustment for Israel and Palestine
- Fixed a character in province number 13537
- Fixed "Isfahan" province being called "Ishafan" in central Iran

GUI:

- Combined the integrated/naval air defense system and removed the missile system ideas from the ideas.
- Added a display in the Integrated Air Defense tab with the modifier
</details>

<details><summary>v1.8.4 - Hotfix</summary>

AI:

- The AI should no longer leave when presented with the hammer and sickle (fifth international)
- Revolutionary Iran AI will no longer be confined to just Tehran and 12 divisions

Bugfix:

- Fixed a number of minor nations not having the right starting techs preventing them from being playable
- Fixed EU ideas being left over despite having left the EU for Poland
- Subscription box should no longer cover up for people with smaller monitors
- Iranian Democratic path should now correctly fire election events
- Iranian opposition parties should no longer be illegal after the revolution
- Axis of Resistance countries should no longer be in love with Post-Revolutionary Iran
- As Pan-Iranist Iran, you should be able to form the Iranic-Federation if you got cores without the mechanic
- The MEK should no longer be locked out of the 2nd half of the Iranian economy tree
- Fixed some localization for Iran
- Fixed the Nuclear Branch being locked for Iran
- Azerbaijan Compromise decision should now work correctly for post-revolutionary Iran (If Azerbaijan was lost during the revolution)
- Healthcode focus for Iran should no longer be unavailable
- The cap on auto influencers should no longer decrease randomly
- Fixed the Bulgarian Mechanized Brigade having a empty slot in support companies and being able to assign corvettes to the slo
- Fixed broken economy branch and ideas for Russia
- Fixed Annextion Events for Russia
- Fixed military decisions for Russia
- Fixed Wagner decisions for Russia
- Fixed Bat'ka Idea for Belarus
- Removed decisions in the Poznyak branch in Belarus related to the parliament
- Fixed broken auto-influence cap
- Fixed auto-influenced nations over 3 being removed
- Fixed auto-influenced nations not having their cooldown applied properly
- Fixed the fifth international not properly forming
- Fixed overlapping focuses for Ethiopia
- Fixed auto-influence hitting base gain vs base cost
- Fixed being able to exploit auto-influence. It now has a 30 day commitment, no money back guarantee
- Fixed Bulgaria being NATO and CSTO member in the same time
- Fixed ukranian azov decision being able to fire multiple times
- Fixed ukranian 'finish Novorossiya' decision tagreting NOV and not DPR+LPR
- Fixed Donbass war getting stuck in case of counterattack - hopefully

Balance

- Rebalanced Political Power/Stability gain as opposition Iranian paths, it should no longer be excessive
- The MEK path as Iran should now give you puppets on countries you start revolutions in through the tree
- Added more requirements for Pan-Iranist focuses
- Rebalanced Russian economic and political ideas
- Rebalanced Russian Mechanics of National projects
- Now in the branch of Chechnya, Kadyrov is mandatory as the ruler of the country only at the very end
- National Project decisions for Russia reworked and rebalanced
- Changed unit templates to better represent actual units for: SOV, UKR
- Created T-64BV tank variant and moved it to UKR to allow for proper tank conversion

Content

- Added new agency for Alt-History Iranian paths, you will no longer just get fossil fuel industry when you dissolve VAJA
- New tooltips for Iranian Political content to list out requirements
- Improved the Cold War of the Gulf Mechanic for Monarchists/Democratic Iran so that it is worth doing
- There may be turmoil in Afghanistan once they are annexed by the Pan-Iranist through the Iranic Unity mechanic
- New War-Goal focuses for all Iranian Political Paths
- Added new tooltips to the United States events regarding the Reformed Republic
- Removed all decisions from Chechnya
- Removed all communists decisions from Abkhazia
- New focuses for the Communist and Nationalist branches of Abkhazia
- Removed ECOWAS map mode as it doesn't do much.

Database:

- Added CV-67 to the USN. Slightly upgraded Kitty Hawk class carrier

Graphics:

- Added new loading screens for BLR, BUL, CHE, COM, SOV and PER
- Fixed a broken focus icon in Poland for Linux users

Localization:

- Fixed typos in Polish division templates
- Fixed an Iranian focus description
- Fixed typo in the Ukrainian templates
- Fixed a few typoes in the Ukrainian decisions/ideas
- Added missing localisation for Russian focuses
- Fixed missing loc for Central American formable nation

Modding Resources:

- Added 4 new color formatting keys n - Navy Blue, l - Light Blue, P - Deep Pink, p - Hot Pink

User Interface:

- Added a new "Open Economy Button" in the main screen
- Better position for ruling party info in diplomatic window (neccesary for Russian language)

</details>

<details><summary>v1.8.3 - May Patch</summary>

Achievements:

- Removed ironman requirement based on poll
- Added "A New Begonia Leaf" as China recover Outer Mongolia, Taiwan and South China Sea region.
- Added "Full House of S.A.R" as China have all possible S.A.R at the same time.
- Added "Project National Glory" as Republic of China restore the Mainland, Outer Mongolia, and South China Sea region and all other claimed state to our control.
- Fixed Belgium being one of the potential nations to form Central America

AI:

- AI should now dynamically consider Japan's focus tree alliances
- AI should now no longer leave the faction from Japan immediately once they accept
- AI Bosnia should no longer go to civil war in like two minutes

Balance:

- Changed Bosnia's starting military spending and gave it additional stability to help

Bugfix:

- Corrected localization error in trigger for achievements
- Fixed "Farmers Push for Biofuel Investment" having a incorrect faction opinion change
- Fixed auto influence being unable to be ended without pp
- Fixed the FCA being able to be achieved
- Fixed Jose Maria Anzar not having his traits
- Fixed the Singaporean Trade focuses having a broken prerequisite
- Fixed peace conference crash (this was due to a overloading a flag strip)

Content:

- NEW FOCUS TREES: Abkhazia, Bulgaria, Comoros, Chechnya, Russia, Iran
- Added idea "Arms Exporter" to Singapore to buff the Arms Exporter focus
- Reworked Auto-Influence to be the primary functionality for "Spread Influence"
- Auto-Influence now costs -1.50 Political Power daily vs a lump sum at the end of the month
- Influence Map Mode now shows who is being auto-influenced
- Improved some formables to require all the nations be owned by the founding nation before integration begins
- New focus tree for Iranian Political content, including a tree for Monarchy, Democracy, Nationalist & Leftists.
- Additional content for Belarus
- Reworked War In Donbas - now it is a series of border wars, not all-out war
- Added new Russia related content to Ukraine
- Added army reform mechanic for Ukraine
- Ukraine will now spawn volunteer divisions should it come under war
- Rebalanced few focuses in Ukrainian focus tree
- Removed "Stability of the regime" mechanic
- Ukraine will now not lack that much of basic equipment on game start
- Additional content for Belarus and restructuring of the miltiary tree

Localization:

- Improved the localization of click/right click with icons
- Adds icons to all of the modifiers in MD
- Fixed typo in Construction Process Reforms in Polish idea

Map:

- NEW TAG: BRY, BSH, CRM, DAG, DPR, KBK, KLM, LPR, TAT, TUV, and YAK
- Denmark map adjustments around Copenhagen
- Reworked Yemen map for upcoming content
- Several victory point fixes
- River crossing fixes

Misc:

- Added game rule for MP sessions to balance out countries via offmap factories
- Added game rule to disable generals having a chance of getting killed in battle

</details>

<details><summary>v1.8.2 - Hotfix</summary>

Achievements:

- Achievements are now ironman required

AI:

- Korea DPR AI Path "kim Jong-un" could get achievement normally

Balance:

- Generals now can die in combat: 0.3% chance to die if battle is lost, 0.1% if battle is won
- Reckless trait now makes general 20% more likely to die in combat
- Cautious trait now makes general 20% less likely to die in combat
- Officer training now influences how generals are likely to die in combat - from +40% more likely to -45% less likely - lower education means higher chance of dying
- Rebalanced Ukranian oob, less modern arty, more guns and apcs
- Rebalanced the idea "Personal Freedoms" to give Democratic Drift +0.05 from 0.01, 5% flat stability and 10% Political Power Gain

Bugfixes:

- Fixed Mali getting relations as the clear East Asian nation it is from Indonesia
- Fixed unvisible cheat decisions if you switched to another country via console command tag XXX
- Fixed attacking, banning, boosting shiites (from now should be unavailable only if you are PER and you have Reformists or Principalists)
- Fixed Gulf's support decisions, now you can't spam support. Also reduced cooldown from 60 to 50.
- Fixed Heavy Engineer company giving 50% defense bonus in hills
- Removed unused stats for AS fighters and STR bombers to not confuse players
- Fixed cartels coming back with more cocaine after being defeated

Content:

- Added some new cheat decisions (add 50, 100, 500 and 1000 billions in money, add 100000, 250000, 500000, 1000000 manpower)

Game Rules:

- Temporarily removed the Hard Economic AI option, it needs some further tweaking. If you wish for a harder experience play on Elite for the time being

Graphics:

- Added all available 3D models to the IFV designer
- Added all available 3D models to the APC designer
- Added all available 3D models to the MBT designer
- Added all available 3D models to the SPARTY designer
- Expanded the number of 2D icons available to the IFV/APC/MBT/SPARTY designers

Localization:

- Fix the "Seek UN Security Council Seat" of Unified Korea
- Improved a number of files localization grammatically

Modding Resources:

- Added four new modifiers: Office Park Tax Modifier, Civilian Industry Tax Modifier, Military Industry Tax Modifier, and Naval Dockyard Tax Modifier

</details>

<details><summary>v1.8.1 - Hotfix</summary>

Achievements:

- Updated description for The Only Superpower to include China

AI:

- AI should now be more likely to ratify new NATO members if they are a top three influencer
- AI should now be more likely to ratify new NATO members if the ratifier has a high opinion of them
- AI USA should now have some more available political power to help them do things

Balance:

- Shortern time for some Bosnian focuses
- Equipment purchasing weapon price rebalanced
- Slight balancing to the Belarusian tree
- Rebalanced "Pro-LGBT Stance" idea in Spain and Singapore
- Reduced ratification of NATO aspirants to 25 from 50
- Increased the IC cost of the Kamikaze Drones

Bugfixes:

- Fixed Nepal chnaged orthodox with hindu
- Fixed Bosnia focus national unity by added event effects into focus
- Disabled event set for the United States that slipped into master by mistake
- Fixed CIS/EU Decision for Georgia
- North Korea Kim Jong Un game rule is now default
- Fixed Indonesian tree referencing Austria instead of Australia
- Fixed Indonesia having influence in Indonesia
- Fixed fertilizer system for the Belarusian tree
- Fixed opinion modifier reference for Singapore "Grand Prix" event
- Fixed Research Bonus from Navy Power Project officer corp not applying research bonuses to carrier hulls
- Fixed Event that says "Bosnia will be known as Bosnia focus tree" (Now cores should be given and tag as been placed in hidden effect)
- Fixed Australasia with replacing country flag is_NZL with is_ANZ.
- Fixed Air Incursions opinion modifier ticking negative forever
- Fixed Broke Trade Agreement opinion modifier ticking negative forever
- Fixed Nationalized Companies opinion modifier ticking negative forever
- Fixed Nationalist Assets opinion modifier ticking negative forever
- Fixed getting cores on UK via CANZUK decisions integration
- Several fixes for decisions of formable nations (was wrong checking IDs states, kekw)

Content:

- Added an event option to Singapore to repeal Migrant Actions

Localization:

- Fixed the Missile Tooltip showing the incorrect action
- Colorized some tooltips in the Missile UIs for clearer looks
- Fixed tooltip in the EU decisions to correctly show 4% instead of 0.04% in raise Global Europe
- Reworded a British event so its options make more sense
- Fixed a missing localization key in Formables/Achievements
- Fixed missing localization for Bosnian Civil War

Game Rules:

- Added a game rule to make 9/11 happen on 9/11
- AI restrictions allow you to earn achievements
- Enable AI Division Limiter allow you to earn achievements

Graphics:

- Added a number of APC/IFV for the designer for people to design what they want. If you want a Soviet APC model on your American design go for it.

UI:

- Cleaned up some titles and formatting so the Recon/Utility Trucks section is not free floating weird

</details>

<details><summary>v1.8.0 - 'The Tiger, The Rose, and the APCs'</summary>

Achievements:

- A variety of new custom modded achievements (challenge runs) to take earn and play various gameplay styles
- A variety of new ribbons for some short game ideas or general strategic goals for a nation
- Added statistic support for Career Profile
- Added achievement Rise of the Maltesers: "As Malta Unify the EU"
- Added achievement Bosnian Artillery is Guided by God: "As Bosnia control or puppet the owner of the holy cities of Mecca & the Vatican."
- Added achievement Sword of the Balkans: "As Srpska become a regional power and have more than 24 divisions"
- Added achievement Twogoslavia: "As any of the former nations of Yugoslavia, unite all of them and form Yugoslavia"
- Added achievement Salafist Sopranos: "Erik'ya ibn al-Marhosi is a Marxist kleptocratic Salafist Christian fundamentalist who now rules Armenia."
- Added achievement Armenian Empire: "Armenia finally reached It's absolute borders, Tigranes the Great would've been proud."
- Added achievement UNO Reverse Pashinyan: "Unlike the real counterpart, your Pashinyan unified Artsakh with Armenia and stood still on his patriotism."
- Added achievement Demirchyan's Wet Dream: "Transcaucasia is finally unified under Soviet rule by Armenian Communists, truly, glory to red october!"
- Added achievement Varazdat Armataptugh: "In the name of the Gods, the true way of living is restored in Armenia."
- Added achievement Shadow of Sevres: "As Armenia reclaim the states of Van and Northeast Anatolia."
- Added achievement Serbia je Kosovo: "As Kosovo, either own Central Serbia and Eastern Serbia or have Serbia as a subject."
- Added achievement Gang is Back Together: "As Nationalist Germany be in faction with Japan and Italy with both of them being Nationalist."
- Added achievement Ukraine Uno Reverse: "As Ukraine without being in a faction, capitulate Russia whilst at war."
- Added achievement The Only Survivor: "As any nation that is not the United States, become a superpower and be the only superpower."
- Added achievement Quite Literally the EU: "Every European nation is a member of the European Union."
- Added achievement Who was in Paris?: "As Niger control Île-de France"
- Added achievement Head of the Tigers: "As a Western-Aligned Singapore have Hong Kong, South Korea, and Taiwan as subjects before 2004."
- Added achievement A New Singaporean Empire: "As a Military Junta in Singapore control Beijing, Delhi, Tokyo and Jakarta."
- Added achievement Rise of Singapore: "As Singapore become a superpower."
- Added achievement The Pirate King of Singapore: "As the Oligarchs own the states of Jamaica, Bahamas, Sud-Haiti, Jeju, and Bari."
- Added achievement Democracy is Overrated: "As a Western Autocrat Spain bring the Fascists into your coalition after you have completed The New Elections."
- Added achievement The Glory of the Spanish Empire: "As the monarchists in Spain own and control the states of Mexico, Cundinamarca, Miranada, Coastal Peru, Central Chile, Pampas, and Southern Luzon before 2010"
- Added achievement Form Maphilindo: "Form the unified state of Maphilindo as Singapore, Indonesia, Brunei, Philippines, Malaysia, or Aceh."
- Added achievement Form the United States of North America: "Form the United States of North America as Mexico, Canada or the United States."
- Added achievement Form the Benelux: "Form Benelux as Netherlands, Luxembourg or Belgium."
- Added achievement Form the West Indies Federation: "Form the West Indies Federation as Dominica, St. Kitts, St. Vincent, Grenada, Barbados, Trinidad & Tobago or Jamaica."
- Added achievement Form the Maghreb Union: "Form the Maghreb Union as Algeria, Libya, Mauritania, Morocco, Sahrawi, or Tunisia."
- Added achievement Reform the Austro-Hungarian Empire: "Form the Austro-Hungarian Empire as Austria, Hungary, Slovenia, Czechia, Slovakia, or Croatia."
- Added achievement Form the Peru-Bolivian Confederation: "Form the Preuvian-Bolivian Confederation as either Peru or Bolivia."
- Added achievement Form CANZUK: "Form CANZUK as Australia, Canada, New Zealand or the United Kingdom."
- Added achievement Form Antillean Confederation: "Form the Antillean Confederation as the Dominican Republic, Haiti, Puerto Rico or Cuba."
- Added achievement Form Rio de la Plata: "Form Rio de la Plata as Paraguay, Bolivia, Chile, Uruguay or Argentina."
- Added achievement Form North Sea Empire: "Form the North Sea Empire as the United Kingdom, Sweden, Denmark or Norway."
- Added achievement Form the Visegrad Union: "Form the Visegrad Group as Poland, Czechia, Slovakia or Hungary."
- Added achievement Form the Andean Federation: "Form the Andean Federation as Colombia, Peru or Bolivia."
- Added achievement Form Indochina: "Form Indochina as Vietnam, Cambodia, or Laos."
- Added achievement Form the United Turkic Territories"Form the United Turkic Territories as Kazakhstan, Uzbekistan, Turkmenistan, Tajikistan or Kyrgyzstan."
- Added achievement Form Union of South American Nations: "Form the Union of South American Nations as Brazil, Venezuela, Argentina, Peru, Ecuador, Guyana, Colombia, Chile, Trindad & Tobago or French Guyana."
- Added achievement Form Australasia: "Form Australasia as Australia or New Zealand."
- Added achievement Form Iberia: "Form Iberia as Spain or Portugal"
- Added achievement Form Gran Colombia: "Form Gran Colombia as Colombia, Venezuela or Ecuador."
- Added achievement Form Central America: "Form Central America as Belize, Guatemala, El Salvador, Honduras, Nicaragua, Costa Rica, or Panama."
- Added achievement Form the Baltic States: "Form the Baltic States as Estonia, Latvia or Lithuania."
- Added achievement Form Scandinavia: "Form Scandinavia as Sweden, Denmark, Norway or Finland."
- Added ribbon A Modern Step: "Thanks for playing Millennium Dawn!"
- Added ribbon Conquer Taiwan: "Conquer Taiwan as the People's Republic of China. The island will be ours once more."
- Added ribbon Reclaim Ambazonia: "Reclaim Ambazonia from Cameroon. A post-colonial dispute that was never settled."
- Added ribbon Seize Sahrawi: "Take back our breakaway state of Sahrawi."
- Added ribbon Reclaim Western Sahara: "Take back Western Sahara from the Moroccans"
- Added ribbon Return Abkhazia and South Ossetia: "The republic of Abkhazia should return to Georgia."
- Added ribbon End the Angolan Civil War: "End the Angolan civil war as one of the factions."
- Added ribbon End the Somali Civil War: "As either the Somali Federal Government or the Somali National Alliance end the Somali civil war."
- Added ribbon Armenian Rule 34: "Order the Rule 34 as Kocharyan."
- Added ribbon Another Statue of Christ: "Build the christ statue as Tsarukyan."
- Added ribbon Polish-Hungarian Commonwealth of Armenia: "Bring the Polish-Hungarian pretender on Armenian throne."
- Added ribbon Army of S.S.: "Conquer Azerbaijan as Serzh Sargsyan."
- Added ribbon I hate the antichrist: "Play as truly neutral Armenia and annex Artsakh, Western Armenia and Azerbaijan."
- Added ribbon Manifest Destiny: "From beyond the shining seas shows the shining light that is democracy and at its helm rest the watchful eagle standing proudly over its destiny."
- Added ribbon Novel Campaigner: "From the rags of the political ring a new star rises."
- Added ribbon Ahh Not Again...: "Took an extended Holiday and enjoyed the Pierogi and Kotlet that much, we're moving back in....again...."
- Added ribbon Seize the Riau Islands: "Take the strategic Riau Islands from Indonesia."
- Added ribbon Federation of Malaysia: "Malaysia is a subject of Singapore"
- Added ribbon The Financial Center of Asia: "Have at least 15 Office Sector constructed in your nation."
- Added ribbon End the Second Sudanese Civil War: "End the Second Sudanese Civil War as either Sudan or South Sudan."
- Added ribbon End the Nepalese Civil War: "End the Nepalese Civil War as either Nepal or Maoist Nepal."

AI:

- Changed how investment AI works: AI will now prefer to invest into allies and countries with good relations
- AI will now adjust its investment targets more as the game progresses
- China is greatly strengthened. Now, at the beginning of the game it will kill some garbage divisions. Also, now China’s priority is military factories and increased military spending. Don’t expect an easy stroll through China.
- Russia is strengthened. There will be infantry. There will be tanks. There will be aviation. There will be an end game for someone
- Production priorities have been completely redesigned. There will be no more distortions. AI seeks to fill the warehouses, first replenishing the equipment, further based on its future army
- Economic AI (if included) seeks to rid the country of corruption and economic crisis. New mechanics will force the AI to save its political power and use taxes only when absolutely necessary.
- Countries around the Caspian Sea no longer build shipyards. Exception - Iran
- The damn transport helicopters should now leave the Al alone. Now AI seeks to build up to 800 transport helicopters.
- UK AI focuses more on small ships (corvettes)
- USA AI Wants More AS-Fighters
- For all AI infantry divisions are given higher priority. They are better protected on difficult terrain
- Reduced the percentage of AI making a puppet of another country (Earlier AI expected 89% impact on the country. Now 81%.)
- Fix USA going Guerilla Warfare. They should now take Network Centric Warfare
- Fixed Custom Naval AI nations producing the generic class vessels
- Improved the AI's technologies picks
- Fixed American AI not properly prioritizing the construction technologies
- NATO should now grow more dynamically based on the AI conditions (2004 ascension should happen in late 2003 to early 2004, etc)
- Serbia should befriend Russia as long as they're not Western and Russia is not western
- AI should no longer overfill the carriers rendering them useless
- AI should be more likely to up corporate tax rates now to help offset spinning treasury issues
- AI will now remove excess equipment from stockpile
- France should support CDI in the First Ivorian Civil War
- Burkina Faso/Liberia should support FNC in the First Ivorian Civil War
- Brazil should now be more protective over South America via befriending/support
- Denmark now has sanity checks to not invade Sweden/Norway if they are in NATO/EU
- Added office target for France
- AI should no longer invest in areas that are not connected by land to the capital (sorry Hawaii jk)
- AI should now invest in Network Infrastructure
- Added states to be ignored from investment lists
- AI will now remove excess equipment from stockpile to not get broke
- Additional AI peace deal behaviours, should see less partitions nationally, with belligerents focusing on forming outlook puppets
- When playing as CHE, SOV AI will not take your state but will instead puppet you
- Added a (very) basic player led peace conferences game rule in order to not let AI do what they want during wars a player is a part of
- Added custom path AI for Switzerland
- Area default priorities no longer check if America has its capitol in Africa and other weird scenarios like that
- North Korea won't war with Japan and the United States weirdly
- AI now should design tanks, APCs, IFVs, SPARTs
- Added a small AI strategy for Brazil to "rival" Argentina and vice versa for more interesting geopolitical content in SA
- China should take their regional/global influence branches a bit later to make them focus on internal growth early game

Balance:

- AI has a stronger bonus on harder difficulties for players who want stronger AI
- Non State Actors research debuff decreased 50% -> 20%, resource gain debuff is now removed, but now has -5% tax gain modifier
- Major Financial Institution Fails econ event now is a bit less punishing
- Blood Diamond Trade idea: Switched -10% stability/+0.50 daily PP to +10% stability/-0.25 daily PP
- Reduced stability drop from AIDS
- Saudi Aid to Mosques idea now gives +5% stability
- Child Soldiers give +5% war support
- USAID idea now gives +5% stability
- GUAM member idea now gives +5% stability
- Police spending now also reduces required garrisons up to 40%
- French idea "Free Market" increases trade law
- DNA Fingerprinting reduces Police Cost by 10%
- Customized difficulties now give economic bonuses to the strengthened nation (for masochists)
- Rebalanced existing unit medals
- New medals for: China, Germany, Iran, Russia
- Increased resource cost for some tank modules
- Increased upgrade impacts for light AT and light AA, rebalance upgrades for all equipment
- Rebalanced GCC focus tree: reduced days cost for most focuses, some small changes in effects and also bug-fixes.
- Air assault units (paradroppable and on helicopters) now will have base +5% breakthrough
- SpecOps unit will now have buff for extra 5% of soft/hard attack and defense as well as 10% breakthrough bonus
- Decrease completion time on some of China's focuses
- Now China will deploy Varyag (Liaoning) in Dalian instead of getting production this carrier.
- Block releasing ETK and TIB nations via Occupied Territories for China until specific focuses is completed.

Combat Balance Changes:

- Batallions now provide different supression: militia has lowest, motorised and light tank provide highest
- Increased training speed for air and land units
- Different recon units now provide different amounts of 'recon' - heavier units provide more
- Introduced new battle phase - recon - all land combat will start with it,
  both sides will deal decreased damage during it (eventually battle will progress into main phase)
- Rebalanced terrain modifiers for all units
- Increased river crossing penalties to make marines more viable
- Decreased speed for 'foot' units - militia, infantry, specops - 8 -> 4 km/h
- Increased impact of general's impact on recon skill 0.05 -> 0.5 per level
- Units now have 10 levels (instead of 5)
- Unit level bonus for land units decreased from 15% to 5% per level

Bugfixes:

- Fixed the paradropping bug (changed minimum required planes from 50 to 25 thus allowing paradropping)
- Added a faction creation to UNASUL for temp fix
- Fixed the events firing for Albania firing on startup
- Fixed some graphical artifacts for Weapon Market
- Fixed Army icons (yes, should be finally fixed)
- Fixed missing helicopter tech for Kenya
- Added a call to clear the auto influencer array if -50 PP or more
- Catalonia should no longer take Lisbon when declaring independence from Spain
- Fixed Revoke Andalucian Citizenship decision
- Fixed the Spanish Monarchs not coming to power properly
- Fixed the Spanish tree's 70% or higher focuses from working incorrectly
- Fixed the IMF Demands Taxes pushing your taxes outside of the 50% limit
- Fixed the Environmental Imperialism Oceania calling the wrong continent
- Corrected a TAG error for a remove_from_faction effect in the GULF tree
- Fixed errors in the Brazilian Templates being larger than the UI
- Removed a call to a non-existent event in the Japanese tree
- Corrected a Formable Nations trigger using FRU instead of FGU
- Fixed Heydar Aliyev coming back from the grave when his son get wooped
- Changed United Koreas Economy effects to better reflect the focus name
- Fixed the name lists of nations so the AI should use them
- Fixed Blackwater pmc having incorrect equipment
- Fixed land doctrine giving bonuses for non-existing units
- Fixed land doctrine giving negative supply consumption
- Korean units should no longer have invisible batallions in templates
- Fixed missing localization for one of opinion modifiers for Cartels
- Fixed Ukrainian orthodox church idea
- Fixed some missing localization for Equipment Purchasing
- Fix becoming a member of GCC if you are ISIS cunt
- Fixed bug where you could place new orders from seller countries that no longer exist
- Fixed some background issues with the ship designer UIs
- Fixed the name of the United States of North America to North American Caliphate when salafist
- Fixed the Ukrainian Education Reform icon being in other trees
- Fixed electoral event for Armenia
- Fixed Chinese missile technology not being functional
- Fixed Wimax/LTE UI Error
- Fixed missing party icon from Greens in Israel

Content:

- NEW FOCUS TREES: Belarus, Bosnia, Georgia, Indonesia, Singapore, Iran
- New equipment designers: APC, IFV, SPART
- Reworked Public War Weariness triggering
- Added new mechanic: Corruption opportunities: over the course of the game player (and AI) will get events -
  this events, if accepted, will give different positive(or mixed) timed effects but will have a chance to increase corruption further
  frequency of events depends on corruption level (greater corruption = events happen more often). Oligarchs interest group or
  having oligarchs in government will increase chance of receiving events, but will increase chance of increasing corruption from events as well.
- Added a small new decision for Japan to revoke Article 9 if situation arises
- Added Hermit Kingdom idea to North Korea to make them fall down the gutter not as fast
- Political party additions for Uzbekistan, Turkmenistan, Tajikistan, Kazakhstan, Azerbaijan, Georgia, Mongolia, Vatican State, Liechtenstein, Switzerland, United States
- Reworked Cartel system for all of SA and South East Asia
- Added intelligence agencies to many nations across the globe
- Reworked Libyan politicians, parties and starting laws
- Reworked Singaporean politicians, parties and starting laws
- Reworked Filipino politicians and parties
- New traits for Cambodia's starting leader "Samdeck Akka Moha" and "Ex Khmer Rouge Soldier"
- Added idea to Cambodia "Dominance of the CPP"
- Added French idea "The Francosphere" to assist in projecting influence abroad
- Debt Consolidation Continuous Focus: -1.50 Political Power Daily, -2.5% Interest Rate, -10% Foreign Influence Defense Modifier
- Increased Tax Levies; -1.50 Political Power Daily, -0.10% Weekly Stability, 10% Tax Gain Multiplier Modifier
- Deleted useless "End of Switzerland" focus
- Added Network Infrastructure focus to generic tree
- Added event chain to end the South Sudanese war in 2004-2006
- Added Diplomacy tree for Unified Korea
- Reworked Arudous March content for Korea DPR
- Fixed the prerequisite of Korea's focus "Install the Yusin Dictatorship"
- Re-enabled PMC content for players without NSB DLC
- Add more tank cannon generations for late game
- Removed all equipment production and licenses from game start
- Rebalanced North Korean, South Korean and Unified tree
- Added some starting relations for Georgia, Armenia, India, Abkhazia, South Ossetia, Azerbaijan
- New leaders for Georgia, Singapore
- Added 8 "Third Party" paths for the United States in the Reformed Republic tree: Libertarian, Reform, Constitutionalists, Nationalist Front, Greens, Progressives, Red Democracy/Robin Party, Shepard's Party
- United States tree now dynamic loads to help performance in the larger tree
- Rebalanced of the initial work of the United States content
- Danish military mini-mechanic added
- Canadian focus "A Nation of Diversity" now removes the "Large Far Right Movement" idea to help Canada be less nationalistic
- Add one sub-branch for PRC Regional Influence to annexation of Mongolia or create Outer Mongolia SAR, and related Mongolia region development goal.
- Add one path for PRC to end ROC after victory in civil war

Game Rules:

- Added New AI path: Korea DPR, United States, Spain, Switzerland, Ukraine
- Reorganized game rules around categories
- Added options for chaos peace deals and player led peace conferences
- Added game rules for better MP performance and scenario set-up

Database:

- Reduced starting debt of Angola, DRC, Guinea-Bissau, Korea DPR & Liberia
- Reduced starting military spending of Congo, Libya, North Korea, Pakistan & Yemen
- Added unit/ship/plane namelist for Japan and Libya
- Added Libyan starting influence to a bunch of African countries
- Updated Belarusian equipment

Economy:

- Increased cost of Internal Security Spending by 15%, increased stability gained per level by 40%
- Replaced PP cost for high military spending at peace time with negative stability modifier that is removed during war-time
- Replaced offensive/defensive war stability modifier from healthcare spending with a modifier for reducing war support loss from casualties
- Increased income from Blood Diamond Trade idea from $0.020 -> $0.040. Also added income tooltip to idea
- Adjusted Serbia's debt due to the starting debt spiral
- Added a reinvest international investment feature

Graphics:

- Reworked all tech icons
- Added a unique icon for Combat Service Support company
- Added a unique icon for Helicopter Combat Service Support company
- Added a unique icon for Light Armor Battalion
- Political party icons Abkhazia, Uzbekistan, Turkmenistan, Tajikistan, Kazakhstan, Azerbaijan, Georgia, Mongolia, Vatican State, Liechtenstein, Kyrgyzstan, Belarus, the Netherlands, Luxembourg, Albania
- Added unique icons for the nations with unique intelligence agencies
- Added House of Bernadotte icon
- New flags for Belarus, Georgia, Armenia
- Added 16 new loading screen
- Missile graphics for the Swedish missile systems
- Updated Swedish agency logo
- Added a model for the Aero 29
- Added a model for the Aero 39
- Added a model for the Yak 130
- Added a model for the Mig 29
- Added a model for the Su-27
- Added a model for the Yak 38
- Added a model for the Yak 141
- Added a model for the Harrier
- Added a model for the M109
- Added a model for the Su-17
- Added a model for the Su-7
- Added a model for the Su-24
- Added a model for the Su-25/39
- Added a model for the Mig 21
- Added a model for the Mig 23
- Added a model for the Mirage 2000
- Added a model for the Mirage 5
- Added a model for the F4 phantom
- Added a model for the Gerald R Ford carrier
- Added a model for the Indian Hal Tejas mr fighter
- Added a model for the Qaher F-313
- Added a model for the AN225
- Added a model for the Type 052D destroyer
- Added a model for the US b21 raider model
- Added a model for the US f5 model
- Added a model for the Chengdu j10
- Added a model for the Chinese J-14
- Added a model for the US zumwalt stealth destroyer
- Added a model for the us seawolf and ohio class submarine models
- Added a model for the US arleigh burke destroyer
- Added a model for the US ticonderoga cruiser
- Added a model for the US Ohio class missile submarine
- Added a model for the Chinese Type 055 cruiser/stealth destroyer
- Added a model for the Chinese Type 054 frigate
- Added a model for the Iranian missile corvette model
- Added a model for the F313
- Added a model for the Shahed 136
- Added a model for the H20
- Added a model for the JH7
- Added a model for the Type 055
- Added a model for the littoral combat ship
- Added a model for the oliver-hazard perry frigate
- Added a model for the QBZ 191
- Adjusted the models for J15, F18, US LCS model, J-31, J-20

Localization:

- Improved localization in the Armenia, Nigerian & Korea DPR tree
- Completed all of the localization for the Spanish tree
- Localization improvements for internal factions
- Localization for the formable nation decisions

Map:

- NEW TAGS: Alaska (ASK), Adjara (ADJ), Silesia (SIL), Vitebsk (VTB), Hawaii (HWI), Lakota (LKT), New York (NYK), Puerto Rico (PTR), Union of Desert (UDT)
- Add Delaware and Rhode Island state.
- Revamp Ukraine as current administration
- Revamp Belarus as current administration
- Add Galicia as state for Austria-Hungary creation.
- Add Liancourt Rocks as state.
- Separate China manchuria state for Balhae creation.
- Separate Hulunbuir from Inner Mongol
- Adjust Afghanistan and Pakistan border to fit actuality status.
- Adjust Norway and Russia border to fit actuality status.
- Adjust Ukraine and Russia border to fit actuality status.
- Adjust Yemen`s state border to fit actuality status.
- Adjust Gilgit-Baltistan`s state border to fit actuality status.
- Adjust Azad Kashmir`s state border to fit actuality status.
- Adjust Aksai Chin`s state border to fit actuality status.
- Adjust Chinese state Guangdong and Fujian border to fit actuality status.
- Add Oki Isle.
- Add Ulleung Isle.
- Add Isle of Youth.
- River cross fix.
- VP & Railway position fix.
- Revamp Gdansk region,add Gdynia and Sopot.
- Change Berlin terrain.
- All inland lake ownership removed.
- Create Hulunbuir lakes.
- Create Uvs lake.
- Correct Zaysan lake position.
- Fix Tioman Island invisible error.
- Fix Cuba isle error.
- Fix Marajo isle error.
- Fix Gdansk three city position.
- Adjustment of Ireland isle.
- Adjustment of altai region state border
- Add two province in Nepal.
- Added 1 CIC in Tripoli
- Reworked Libya's province and state layout
- New state for New Cairo
- New state in Georgia for Armenian autonomous region content

Modding Resources:

- Added a "set_improved_trade_agreement" effect to set up trade agreement diplo actions
- Added a flag to disable new investments for country content
- Added a "change_permanent_investment_target" effect to allow you to add yourself to nations investment targets
- Added one_anti_air, two_anti_air, one_random_network_infrastructure, two_random_network_infrastructure, one_fuel_reserve, two_fuel_reserve
- Improved functionality of the modify_corporate_tax_rate_effect/modify_population_tax_rate_effect
- MD Code Resource has more documented resources for Millennium Dawn team members and submodders (You're welcome)

Music

- Added "Mopikel - Back from Hell, alive"
- Added "Mopikel - Ambush"
- Added "War in Ossetia"
- Added "They are coming"
- Added "The last one"
- Added "Escape from Hell"
- Added "Covert ops"
- Added "Broken"

Performance

- Reworked the Public War Weariness system to be less performance intensive
- Optimized some AI area priorities. North Americans no longer check if their capital is in Africa. I know Karen's love toto but come on!
- The mechanism for calculating the number of missiles and other things is checked on weekly (it was on daily)
- Optimized EU focuses so they're not repeatedly calling multiple every_country calls

GUI

- Small improvements in missiles GUI
- Now you will see custom effects in some missiles techs
- Improved the debt repay button to pay down debt from what you have available in the treasury

</details>
