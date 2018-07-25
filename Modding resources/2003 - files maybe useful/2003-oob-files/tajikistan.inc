
##############################
# Country definition for TAJ #
##############################

country =
{ tag                 = TAJ
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 14
  capital             = 1485
  diplomacy           = { }
  nationalprovinces   = { 1485 }
  ownedprovinces      = { 1485 }
  controlledprovinces = { 1485 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					#Army Equipment
                                        2000 2050
                                        2010
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Equipment
                                        1000 1050
                                        1010
                                        1500 1510
                                        1200 1210
                                        1300 1310
                                        1400 1410
                                        1900 1910
                                        1260
                                        1960
					#Land Docs
					6600 6610
					6010 6020
					6910
					6100 6110 6120 6160 6170
					#Air Docs
					9010 9510
					9050 9060 9070
					#Secret Weapons
                                        7330 7310
					#Air Force
                                        4400 4410
                                        4100 4110
                                        4550
                                        4640 4650
                                        4700
                                        4750
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 4
    political_left    = 4
    free_market       = 4
    freedom           = 3
    professional_army = 3
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 21100 id = 1 }
    location = 1485
    name     = "I Corps"
    division =
    { id       = { type = 21100 id = 2 }
      name     = "1st Motor Infantry Division"
      strength = 100
      type     = motorized
      model    = 2
    }
  }
}
