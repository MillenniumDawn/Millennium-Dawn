
##############################
# Country definition for U03 #
##############################

country =
{ tag                 = U03
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 3
  capital             = 1896
  diplomacy           = { }
  nationalprovinces   = { 1896 }
  ownedprovinces      = { 1896 }
  controlledprovinces = { 1896 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					#Army Org
					1260
                                        1000 1050
                                        1010 1060
                                        1300 1310
                                        1500 1510
                                        1900 1910
					#Army Equip
					2200
                                        2000 2050
                                        2010 2060
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Aircraft
					4800 4700 4750
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160
					#Air Docs
					9010 9510
					9050 9060 9070
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 5
    political_left    = 10
    free_market       = 3
    freedom           = 4
    professional_army = 3
    defense_lobby     = 1
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12281 id = 1 }
    location = 1896
    name     = "1st Motor Rifle Force"
    division =
    { id            = { type = 12281 id = 2 }
      name          = "1st Motor Rifle Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 12281 id = 3 }
      name          = "2nd Motor Rifle Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 12281 id = 4 }
      name          = "3rd Motor Rifle Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 12281 id = 5 }
      name          = "4th Motor Rifle Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
}
