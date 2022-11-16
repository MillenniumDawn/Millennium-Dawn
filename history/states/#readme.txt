#read this if you plan on modding states in any capacity
#
#if you create a new state, remember these key things:
 # transfer resources, factories, population etc accordingly (ex. if you split a state in two)
 # set the correct state_category according to the population (see the list at the bottom)
 # victory points be put in the correct state file
 # make sure provinces don't overlap in two different states
 # buildings are corrected in nudge, that goes for unitstacks aswell if provinces are altered
 # if the game crashes on start up ask for help (its most likely air bases in wrong prov)
 # read the error log for any mentions of the former or new state added
#
#if you mod in an existing state make sure that:
 # everything said above is correct
 # be more hesitant if your changes gives the country controlling the state more longterm advantages, as balance can be rubbed in favour to one country for something like adding an extra naval factory.
#
#if you create or mod coastal states you need to add/mod the respective missile launch point triggers for the coastal state and all adjacent seazones
# examples when you need to modify the missile launch point triggers:
#	- you have a state with a coastline to one seazone, now you change the map so that the coastline of the state covers two seazones
#	- you have a state with a coastline to two seazones, now you change the map so that the coastline of the state only covers one seazone
#	- you add a new state with a coastline
#	- you remove a state with a coastline
#	- you split a state with a coastline into two states
#	- you merge two states with a coastline into one
#	- every other change to states with coastline that adds or removes adjacent seazones
#	- you change the seazones with islands or coastlines
# how you do this:
 # there are 5 files that have to be adapted in \common\scripted_triggers
 # MD_missile_sea_launch_points.txt
 # MD_missile_sea_launch_points_attack_sub.txt
 # MD_missile_sea_launch_points_CV.txt
 # MD_missile_sea_launch_points_defense.txt
 # MD_missile_sea_launch_points_sub.txt
 # there is a example at the top of each file, you either have to adept the existing scripted triggers or add new ones in all five files
# please also add your changes to the list at the bottom of this file
#
#ledger for aprox. what state_category per number of pop a state should have
 # state_00 for <300,000 inhabitants
 # state_01 for 300,000 - 800,000 inhabitants
 # state_02 for 800,000 - 1,500,000 inhabitants
 # state_03 for 1,500,000 - 2,500,000 inhabitants
 # state_04 for 2,500,000 - 3,800,000 inhabitants
 # state_05 for 3,800,000 - 5,200,000 inhabitants
 # state_06 for 5,200,000 - 6,800,000 inhabitants
 # state_07 for 6,800,000 - 8,500,000 inhabitants
 # state_08 for 8,500,000 - 10,500,000 inhabitants
 # state_09 for 10,500,000 - 13,000,000 inhabitants
 # state_10 for 13,000,000 - 16,000,000 inhabitants
 # state_11 for 16,000,000 - 19,000,000 inhabitants
 # state_12 for 19,000,000 - 23,000,000 inhabitants
 # state_13 for 23,000,000 - 27,000,000 inhabitants
 # state_14 for 27,000,000 - 34,000,000 inhabitants
 # state_15 for 34,000,000 - 42,000,000 inhabitants
 # state_16 for 42,000,000 - 52,000,000 inhabitants
 # state_17 for 52,000,000 - 65,000,000 inhabitants
 # state_18 for >65,000,000 inhabitants
#


### MISSILE MAP CHANGES ###
#
# state coastline changes after 1.6.1
# e.g. 9999 - added seazone AAA, removed seazone BBB
# state ID - changes
#
# 2022-04-04 - Bluehunter
# Merged provinces from 1030 to 1029. 1030 became "Outer Donbas".
#
# 2022-05-23 - Angriest Bird
# State 1039 "Shirvan" added and State 713 loses two provinces.
#
#