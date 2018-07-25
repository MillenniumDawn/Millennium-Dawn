
##############################
# Country definition for LAO #
##############################

country =
{ tag                 = LAO
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 9
  capital             = 1329
  diplomacy =
  { relation = { tag = WLL value = 200 access = yes }
  }
  nationalprovinces   = { 1306 1329 1332 }
  ownedprovinces      = { 1306 1329 1332 }
  controlledprovinces = { 1306 1329 1332 }
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
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 7
    political_left    = 10
    free_market       = 5
    freedom           = 2
    professional_army = 1
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 14000 id = 1 }
    location = 1329
    name     = "I Corps"
    division =
    { id            = { type = 14000 id = 2 }
      name          = "1st Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 14000 id = 3 }
    location = 1306
    name     = "II Corps"
    division =
    { id       = { type = 14000 id = 4 }
      name     = "2nd Division"
      strength = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 14000 id = 5 }
    location = 1332
    name     = "III Corps"
    division =
    { id       = { type = 14000 id = 6 }
      name     = "3rd Division"
      strength = 100
      type          = motorized
      model         = 0
    }
  }
}
