
##############################
# Country definition for CMB #
##############################

country =
{ tag                 = CMB
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 20
  manpower            = 28
  transports          = 20
  escorts             = 0
  capital             = 1340
  diplomacy =
  { relation = { tag = WLL value = 200 access = yes }
  }
  nationalprovinces   = { 1336 1339 1340 1341 }
  ownedprovinces      = { 1336 1339 1340 1341 }
  controlledprovinces = { 1336 1339 1340 1341 }
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
    democratic        = 6
    political_left    = 6
    free_market       = 6
    freedom           = 4
    professional_army = 1
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 7500 id = 1 }
    location = 1340
    name     = "I Corps"
    division =
    { id       = { type = 7500 id = 2 }
      name     = "1st Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 7500 id = 3 }
      name     = "2nd Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 7500 id = 4 }
    location = 1341
    name     = "II Corps"
    division =
    { id       = { type = 7500 id = 5 }
      name     = "1st Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
  }
  landunit =
  { id       = { type = 7500 id = 6 }
    location = 1339
    name     = "III Corps"
    division =
    { id       = { type = 7500 id = 7 }
      name     = "3rd Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 0
    }
    division =
    { id       = { type = 7500 id = 8 }
      name     = "4th Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 0
    }
  }
}
