
##############################
# Country definition for BUR #
##############################

province =
{ id       = 1299
  naval_base = { size = 2 current_size = 2 }
}            # Rangoon

province =
{ id       = 1296
  air_base = { size = 4 current_size = 4 }
}            # Mandalay

country =
{ tag                 = BUR
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 133
  transports          = 37
  escorts             = 0
  capital             = 1296
  diplomacy =
  { relation = { tag = CHC value = 200 }
  }
  nationalprovinces   = { 1289 1290 1291 1292 1295 1296 1297 1298 1299 1300 1301 1302 1304 1346 1877 1898 }
  ownedprovinces      = { 1289 1290 1291 1292 1295 1296 1297 1298 1299 1300 1301 1302 1304 1346 1877 1898 }
  controlledprovinces = { 1289 1290 1291 1292 1295 1296 1297 1298 1299 1300 1301 1302 1304 1346 1877 1898 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					#Army Equip
                                        2000
                                        2010
                                        2300 2310
                                        2400 2410
					2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
                                        1000
                                        1010
					1300 1400
                                        1500
                                        1200
					1980
                                        1900 1910
					1260
					#Aircraft
					4750 4700
                                        4000 4010
                                        4570
                                        4640
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
					#Air Docs
					9010 9510
					9050 9060 9070
                                        #Navy Techs
                                        3000 3010
                                        3590
                                        3850 3860
                                        #Navy Doctrines
                                        8900
                                        8950
                                        8000
                                        8500
					
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 1
    political_left    = 5
    free_market       = 4
    freedom           = 1
    professional_army = 9
    defense_lobby     = 3
    interventionism   = 1
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 7400 id = 1 }
    location = 1299
    name     = "I Corps"
    division =
    { id            = { type = 7400 id = 2 }
      name          = "Myanmar Central HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 1
    }
    division =
    { id       = { type = 7400 id = 3 }
      name     = "1st Armored Division"
      strength = 100
      type     = armor
      model    = 8
    }
    division =
    { id            = { type = 7400 id = 4 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 7400 id = 5 }
      name     = "2nd Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 7400 id = 6 }
      name          = "3rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 7400 id = 7 }
      name          = "4th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 7400 id = 8 }
      name     = "5th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 7400 id = 9 }
      name          = "6th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 7400 id = 10 }
    location = 1302
    name     = "II Corps"
    division =
    { id       = { type = 7400 id = 11 }
      name     = "7th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 7400 id = 12 }
      name     = "8th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 7400 id = 13 }
      name          = "9th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 7400 id = 14 }
      name          = "10th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 7400 id = 15 }
      name          = "11th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 7400 id = 16 }
      name     = "12th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 7400 id = 17 }
    location = 1346
    name     = "III Corps"
    division =
    { id            = { type = 7400 id = 19 }
      name          = "13th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 7400 id = 20 }
      name     = "14th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 7400 id = 21 }
      name     = "15th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 7400 id = 22 }
      name          = "16th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 7400 id = 23 }
      name          = "17th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 7400 id = 24 }
      name     = "18th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 7400 id = 25 }
    location = 1301
    name     = "IV Corps"
    division =
    { id       = { type = 7400 id = 26 }
      name     = "4th Motorized Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id            = { type = 7400 id = 27 }
      name          = "21st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 7400 id = 28 }
      name     = "22nd Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 7400 id = 29 }
      name     = "23rd Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 7400 id = 30 }
      name          = "27th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 7400 id = 31 }
    location = 1304
    name     = "V Corps"
    division =
    { id       = { type = 7400 id = 32 }
      name     = "19th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 7400 id = 33 }
      name     = "20th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 7400 id = 300 }
    location = 1299
    base     = 1299
    name     = "Myanmar Navy"
    division =
    { id       = { type = 7400 id = 301 }
      name     = "Aung Zay Ya"
      strength = 10
      type     = destroyer
      model    = 1
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 7400 id = 200 }
    location = 1296
    base     = 1296
    name     = "501st Airbase"
    division =
    { id       = { type = 7400 id = 201 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 85
      model    = 0
    }
    division =
    { id       = { type = 7400 id = 202 }
      name     = "4th Squadron"
      type     = interceptor
      strength = 85
      model    = 0
    }
    division =
    { id       = { type = 7400 id = 203 }
      name     = "14th Squadron"
      type     = interceptor
      strength = 85
      model    = 0
    }
  }
  airunit =
  { id       = { type = 7400 id = 204 }
    location = 1296
    base     = 1296
    name     = "88th Airbase"
    division =
    { id       = { type = 7400 id = 205 }
      name     = "7th Squadron"
      type     = interceptor
      strength = 80
      model    = 1
    }
    division =
    { id       = { type = 7400 id = 206 }
      name     = "18th Fighter Squadron"
      type     = interceptor
      strength = 80
      model    = 1
    }
    division =
    { id       = { type = 7400 id = 207 }
      name     = "2nd Ground Attack Squadron"
      type     = tactical_bomber
      strength = 50
      model    = 0
    }
  }
}
