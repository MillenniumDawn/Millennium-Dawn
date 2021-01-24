#read this if you plan on modding states in any capacity
#
#if you create a new state, remember these key things:	
 # transfer resources, factories, population etc accordingly (ex. if you split a state in two)
 # set the correct state_category according to the population (see the list at the bottom)
 # victory points be put in the correct state
 # make sure provinces don't overlap in two different states
 # buildings are corrected in nudge, that goes for unitstacks aswell if provinces are altered
 # if the game crashes on start up ask for help (its most likely air bases in wrong prov)
 # read the error log for any mentions of the former or new state
#
#if you mod in an existing state make sure that:
 # everything said above is correct
 # be more hesitant if your changes gives the country controlling the state more longterm advantages, as balance can be rubbed in favour to one country for something like adding an extra naval factory.
#

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