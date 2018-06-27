
##############################
# Country definition for ARM #
##############################

country =
{ tag                 = ARM
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 15
  manpower            = 6
  capital             = 1856
  diplomacy           = { }
  nationalprovinces   = { 1856 1847 }
  ownedprovinces      = { 1856 1847 }
  controlledprovinces = { 1856 1847 }
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
					1960
                                        1500 1510
                                        1300 1310
                                        1900 1910
                                        1000 1050
                                        1010
					#Land Docs
					6600 6610
					6100 6110 6120 6160
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 7
    political_left    = 2
    free_market       = 6
    freedom           = 6
    professional_army = 3
    defense_lobby     = 4
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 5600 id = 1 }
    location = 1856
    name     = "I Corps"
    division =
    { id       = { type = 5600 id = 2 }
      name     = "1st Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id            = { type = 5600 id = 3 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 5600 id = 4 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 5600 id = 5 }
      name     = "3rd Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
}
