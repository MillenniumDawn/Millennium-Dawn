##############################
# Country definition for NIC #
##############################

country =
{ tag                 = NIC
  manpower            = 10
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  capital             = 539
  transports          = 10
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 539 }
  ownedprovinces      = { 539 }
  controlledprovinces = { 539 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
                                        #Army Equip:
                                        2000
                                        2010
                                        2300
                                        2400
                                        2200 2210
                                        2500
                                        2600
                                        2700
                                        2800 2810
                                        #Land Docs
					6010 6020 
					6910
					6100 6110 6120
                                        6160
					6600 6610
					#Army Org
                                        1000
                                        1010
                                        1500
                                        1300
					1260
					1980
					1900
                                        #Secret Tech:
                                        7330
                        }
policy = {
        date = { year = 0 month = march day = 0 }
        democratic = 9
        political_left = 2
        free_market = 6
        freedom = 7
        professional_army = 10
        defense_lobby = 2
        interventionism = 5
    }
######################################
# ARMY
######################################

landunit = {
         id = { type = 16700 id = 1 }
         location = 539
         name = "I Corps"
         division = {
                  id = { type = 16700 id = 2 }
                  name = "1st Motorized Division"
                  strength = 100
                  type = motorized
                  model = 1
         }
    }
}
