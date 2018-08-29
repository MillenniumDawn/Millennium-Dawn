
##############################
# Country definition for IRE #
##############################

province =
{ id         = 30
  naval_base = { size = 2 current_size = 2 }
  air_base = { size = 2 current_size = 2 }
}              # Dublin

country =
{ tag                 = IRE
  manpower            = 8
  regular_id          = U06
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  capital             = 30
  transports          = 39
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 27 26 25 24 30 29 28 }
  ownedprovinces      = { 27 26 25 24 30 }
  controlledprovinces = { 27 26 25 24 30 }
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
                                        2300 2310 2320
                                        2200 2210 2220
                                        2400 2410 2420
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2710
                                        2800 2810 2820
					#Army Org
                                        1500 1510 1520
                                        1300 1310 1320
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
                                        6110 6210
                                        6120 6220
					#Naval Docs
                                        8900 8910
                                        8950 8960
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 3
    free_market       = 8
    freedom           = 9
    professional_army = 10
    defense_lobby     = 1
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12700 id = 1 }
    location = 30
    name     = "Irish Army"
    division =
    { id            = { type = 12700 id = 2 }
      name          = "1st Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 12700 id = 3 }
      name          = "2nd Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 12700 id = 4 }
      name          = "4th Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
}
