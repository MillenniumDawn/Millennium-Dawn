##############################
# Country definition for PAN #
##############################

province =
{ id         = 889
  naval_base = { size = 2 current_size = 2 }
}              # Colon

country =
{ tag                 = PAN
  manpower            = 5
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  capital             = 889
  transports = 15
  escorts = 0
  diplomacy           = { }
  nationalprovinces   = { 888 889 }
  ownedprovinces      = { 888 889 }
  controlledprovinces = { 888 889 }
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
        political_left = 10
        free_market = 7
        freedom = 8
        professional_army = 1
        defense_lobby = 1
        interventionism = 4
    }
}