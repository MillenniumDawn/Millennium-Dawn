
##############################
# Country definition for NAM #
##############################

country =
{ tag                 = NAM
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 10
  capital             = 1110
  diplomacy           = { 
                        }
  nationalprovinces   = { 1109 1108 1107 1106 1110
                        }
  ownedprovinces      = { 1109 1108 1107 1106 1110
                        }
  controlledprovinces = { 1109 1108 1107 1106 1110
                        }
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
                                        #Army Equipment:
                                        2400 2410
                                        2200 2210 2220
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
                                        #Army Organisation:
                                        1300 1310
                                        1900 1910
                                        1260 1270
                                        1970
                                        #Army Doctrines:
                                        6100 6200
                                        6110 6210
                                        6160 6260
                                        6010
                                        6020
                                        6910
                                        6600
                                        6610
					#Secret Techs
                                        7330
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 8
    free_market       = 7
    freedom           = 3
    professional_army = 1
    defense_lobby     = 4
    interventionism   = 7
  }
}