
##############################
# Country definition for ICL #
##############################

province =
{ id         = 1
  naval_base = { size = 1 current_size = 1 }
    air_base = { size = 2 current_size = 2 }
}              # Reykjavik

country =
{ tag                 = ICL
  # Resource Reserves
  energy              = 100
  metal               = 100
  rare_materials      = 90
  oil                 = 400
  supplies            = 100
  money               = 10
  manpower            = 0
  capital             = 1
  transports          = 40
  escorts             = 0
  diplomacy           = { 
relation = { tag = NOR value = 200 }
relation = { tag = USA value = 200 access = yes }
                        }
  nationalprovinces   = { 1 }
  ownedprovinces      = { 1 }
  controlledprovinces = { 1 }
  techapps            = {
                                        #Industry:
                                        5010 5110
                                        5020 5120
                                        5030 5130
                                        5040 5140
                                        5050 5150
                                        5060 5160
                                        5070 5170
                                        5080 5180
                                        5090 5190
                                       #Army Equip:
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2710
                                        2800 2810 2820
					#Army Org
					1260 1270
					1990
					1900 1910 1920
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
					#Air techs
                                        4700 4800
                                        4750
					#Secret Techs
                                        7330 7310 7320
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6160
					6200 6260
					#Naval Docs
                                        8900 8910
                                        8950 8960
                        }
  policy =
  { democratic        = 10
    political_left    = 9
    freedom           = 8
    free_market       = 10
    professional_army = 10
    defense_lobby     = 1
    interventionism   = 6
  }
}
