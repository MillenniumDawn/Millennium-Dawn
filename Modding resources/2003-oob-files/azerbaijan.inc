
##############################
# Country definition for AZB #
##############################

country =
{ tag                 = AZB
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 15
  manpower            = 13
  capital             = 1907
  diplomacy           = { }
  nationalprovinces   = { 1858 1907 2 }
  ownedprovinces      = { 1858 1907 2 }
  controlledprovinces = { 1858 1907 2 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					#Army Equip
                                        2000 2050
                                        2010
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
					1260
                                        1000 1050
                                        1010
                                        1500 1510
                                        1200 1210
                                        1300 1310
                                        1400 1410
                                        1900 1910
                                        1960
					#Land Docs
					6010 6020
					6600 6610
					6910
					6100 6110 6120 6160
					#Secret Weapons
					7010 7060		
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 4
    free_market       = 6
    freedom           = 4
    professional_army = 3
    defense_lobby     = 3
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 5900 id = 1 }
    location = 1907
    name     = "I Corps"
    division =
    { id            = { type = 5900 id = 2 }
      name          = "1st Motorized Division"
      strength      = 100
      type          = mechanized
      model         = 0      
    }
    division =
    { id            = { type = 5900 id = 3 }
      name          = "2nd Motorized Division"
      strength      = 100
      type          = motorized
      model         = 0      
    }
    division =
    { id       = { type = 5900 id = 4 }
      name     = "1st Infantry Division"
      strength = 100
      type     = infantry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 5900 id = 5 }
    location = 1847
    name     = "II Corps"
    division =
    { id       = { type = 5900 id = 6 }
      name     = "2nd Infantry Division"
      strength = 100
      type     = infantry
      model    = 0
    }
  }
}
