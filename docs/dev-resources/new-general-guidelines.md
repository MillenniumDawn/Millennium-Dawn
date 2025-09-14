## New General Creation
**General Amount**

The amount of generals a country starts with should mainly be relative to the size of its starting military. This would mean a handful of leaders, that are easy to pick from and compare with each other.

I would recommend the following; No. of Generals = \[ROUND(No_of_units/15) + 1\] + \[IsMajor\] + \[IsInFaction\] + \[IsNATO\]

No. of Field Marshals = ROUND(No_of_generals/3)

Examples of amounts;

* USA: 9 Generals, 3 Field Marshals
* Germany: 4 Generals, 1 Field Marshal
* Russia: 8 Generals, 3 Field Marshals
* Iran: 9 Generals, 3 Field Marshals
* China: 11 Generals, 4 Field Marshals
* India: 7 Generals, 2 Field Marshals

**General Skill**

General starting skill should follow similar lines as issue #69

* 1-2: Generals of civil war factions
* 2-3: Africa
* 3-4: Middle East and Asia
* 4-5: Eastern Europe, South America
* 5-6: Western countries

Exceptions can and should be made in case of more famous generals (eg. Qassem Soleimani).

Each new level of a general adds 3 skill points. So a level X general should have a total of (X-1)\*3 + 4 skill points.

**Abilities**

Possible changes needed to current abilities. Current abilities and effects;

* Force Attack: 20% Attack, 25% Breakthrough, -100% Org Damage Taken, 60% Strength Damage Taken, 20% War Support Reduction, Can't Retreat
* Last Stand: 20% Defence, 25% Entrenchment, -100% Org Damage Taken, 60% Strength Damage Taken, 20% War Support Reduction, Can't Retreat
* Staff Office Plan: 400% Planning Speed
* Siege Artillery (needs Fortress Buster trait): 20% Fort Attack, 200% Fort Damage
* Glider Planes (needs Paratroopers trait): 100% Paratroopers per plane, 200% More Organisation on Drop, 50% AA Defence on Drop
* Naval Invasion Planning (need Amphibious trait): 50% Faster Naval Invasion Planning Speed
* Probing Attack (needs Skirmisher trait): Won't Lose Dig-in Bonus on Attack, -20% Attack
* Makeshift Bridges (needs Improvisation Expert trait): -50% River Crossing Penalty, 40% River Attack
* Extra Supplies (needs Logistics Wizard trait): +168 Days of Supply Grace


## Conversion Guide
A tutorial to convert old generals/admirals into the new style:

1. Start the 2000 bookmark as the country you're working on (I'm using Abkhazia as example)

2. Open the console and type "imgui on" and "imgui show characters". You should get a bar with the text "Characters" on it on your screen. By clicking the arrow you get a  window like below. If nothing happens, type "imgui off" and then "imgui on"
![hoi4_12](/uploads/2382a2df47954870901da2fea9edccab/hoi4_12.png)

3. Click the "Write Current Nation Characters" button

4. This will create two files in your HoI4 documents folder (the same folder that has your HoI4 mod folder). Copy the file from character_export/characters/ folder into Millennium_Dawn/common/characters folder. Copy the "recruit_character" lines from character_export/history/country file into the country's history file in Millennium_Dawn/history/countries folder. Place the lines below the create_country_leader entry of the 2000 bookmark

![image](/uploads/259ebd3172d2619400ee045db54961e9/image.png)

5. The exported files will have entries for the starting political leaders and the generic leaders for other Outlooks. Remove these entries from the character file and the recruit_character lines for them from the country history file. Leave only the entries for generals/admirals into the files.

6. Most countries will have too many generals when you do the export. Open the Excel file Generals_worksheet.xlsx from Millennium_Dawn/Modding resources/Generals Rework/ folder and find your country in the list. This file has calculations on how many generals the country should start with. The "No of Gens 1" and "No of FMs 1" tell you how many generals and field marshals the country should have in the 2000 bookmark. "No of Gens 2" and "No of FMs 2" tells you how many they should have in the 2017 bookmark.

From the exported generals, choose the amount of generals and field marshals needed (whichever bookmark has more) and remove the rest. DO NOT MAKE HEADS OF STATE, DEFENCE MINISTERS ETC. GENERALS!

7. Assign each general a skill level according to

* 1-2: Generals of civil war factions
* 2-3: Africa
* 3-4: Middle East and Asia
* 4-5: Eastern Europe, South America
* 5-6: Western countries

The total amount of skill points (attack_skill etc.) the general should have in total is (level - 1) * 3 + 4, with every skill being at least 1. Also assign traits to the generals if you want (these are all listed in the Trait List tab of the Generals_worksheet file).
![image](/uploads/3fd68824a1e2216db70740687a8f4967/image.png)

Here, Abkhazia's general is level 4, so the total amount of skill points is (4 - 1) * 3 + 4 = 13. I've also given him the mountaineer trait.

8. For admirals, take the number of ships the country has, divided that by 15 and round to the nearest whole number and choose that many admirals. Skill level and individual skills are chosen like you'd do for generals.

9. If the country has no generals or admirals from the old system, then they need to be created from scratch following the same principles as above. If the country has no ships, no admirals need to be made.

10. Organize the recruit_character commands in the history file. If the amount of leaders increases between bookmarks, recruit some of the characters in the 2017 bookmark entry and not the 2000 entry. If the amount of leaders decreases, use retire_character to remove some of the leaders between bookmarks. You can also have a completely different set of leaders of each bookmark, but this is not necessary, except in cases of radical regime change or civil war (such as Iraq).

11. Create High Command and branch chief characters. These can be some of the generals you made earlier or completely separate characters. For Army Chief, Navy Chief and Air Chief it is recommended to use one or more historical army chiefs of staff, navy chiefs of staff or airforce chiefs of staff. If the country has no navy, a navy chief isn't needed. However, even if the country doesn't have an air force, at least one Air Chief has to be premade in-game as these can't be generated by the player mid-game.

Below is an example of what the advisor entry looks like in a file

![image](/uploads/4640a3cb69bef1ef69100774fcedccf3/image.png)

Anatoly Zaitsev has been made a possible member of High Command in addition to being a general

slot = Which advisor position the character goes into

idea_token = Unique identifier for the character. Use firstname_lastname

ledger = army/air/navy, depending on the trait given. Only for high_command position

allowed = same as in other ideas, use original_tag = TAG

traits = the trait of the advisor (see Trait List), X in the trait name is level, 1 (specialist), 2 (expert), 3 (genius)

cost = how expensive the character is, can leave at 100 for all

ai_will_do_factor = add to all entries, can just use factor = 1 in all

You can also use visible = { } for the advisors. This means that the character will only become visible in game after certain triggers. For example I made Anatoly Khrulyov as an Army Chief for Abkhazia, but he will only be visible if Abkhazia is a subject of Russia. You can also use available = { } if you want the character to be visible to the player but can't be chosen until certain conditions are met

12. Make sure that each character has a small and large portrait defined. Use pathing similar to the Abkhazia example. The large portrait is 156x210 (same as any leader portrait), the small portrait is 38x51 and can be made just by scaling the large portrait down.
![image](/uploads/88d0c0c3ba669d27143403d542576bd0/image.png)

13. After creating all advisors, add their recruit_character entries into the country history file 2000 bookmark (unless you want to have different characters for different bookmarks).

14. If there are any portraits left over from deleting the old generals and admirals, move them to gfx\leaders\portrait_dump folder

15. Once you've done a country, mark it with 'X' in the Generals_worksheet

If you get lost or need help, you can look at Abkhazia's files for exmaple, or ask help on Discord.
