
##############################
# Country definition for WLL #
##############################

province =
{ id         = 1335
  naval_base = { size = 4 current_size = 4 }
}              # Nha Trang

province =
{ id       = 1337
  air_base = { size = 4 current_size = 4 }
}            # Ho Chi Mihn City

province =
{ id       = 1328
  air_base = { size = 6 current_size = 6 }
}            # Hanoi

country =
{ tag                 = WLL
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 160
  capital             = 1328
  transports          = 94
  escorts             = 0
  diplomacy =
  { relation = { tag = LAO value = 200 access = yes }
    relation = { tag = CMB value = 200 access = yes }
  }
  nationalprovinces   = { 1326 1328 1333 1334 1335 1337 1338 }
  ownedprovinces      = { 1326 1328 1333 1334 1335 1337 1338 }
  controlledprovinces = { 1326 1328 1333 1334 1335 1337 1338 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army equip
                                        2000 2050
                                        2010
                                        2300
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
					1980
					1260
                                        1000 1050
                                        1500
                                        1200
                                        1300 1310
                                        1400 1410
                                             1700
                                        1900 1910
					#Aircraft
					4800
                                        4700 4710
                                        4750 4760
                                        4000 4010
                                        4100 4110 4120
                                        4640 4650
                                        4500
                                        4400
					#Land Docs
					6910
					6010 6020
                                        6130
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
                                        8900 8910
                                        8950 8960
                                        8000 8010
                                        8500 8510
                                        #Secret Tech
                                        7330
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 7
    free_market       = 6
    freedom           = 2
    professional_army = 2
    defense_lobby     = 4
    interventionism   = 6
  }
  # ####################################
  # ARMY
  # ####################################
  landunit =
  { id       = { type = 22900 id = 1 }
    location = 1328
    name     = "I Corps"
    division =
    { id            = { type = 22900 id = 2 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 3 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 4 }
      name          = "3rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 5 }
      name          = "4th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 22900 id = 6 }
      name     = "5th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 22900 id = 7 }
    location = 1326
    name     = "II Corps"
    division =
    { id            = { type = 22900 id = 8 }
      name          = "6th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 9 }
      name          = "7th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 10 }
      name          = "8th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 11 }
      name          = "9th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 22900 id = 12 }
      name     = "10th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 22900 id = 13 }
    location = 1337
    name     = "III Corps"
    division =
    { id            = { type = 22900 id = 14 }
      name          = "11th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 15 }
      name          = "12th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 16 }
      name          = "13th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 17 }
      name          = "14th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 22900 id = 18 }
      name     = "15th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 22900 id = 19 }
    location = 1336
    name     = "IV Corps"
    division =
    { id            = { type = 22900 id = 20 }
      name          = "16th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 21 }
      name          = "17th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 22 }
      name          = "18th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 22900 id = 23 }
      name          = "19th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 22900 id = 24 }
      name     = "20th Infantry Division"
      strength = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 22900 id = 25 }
    location = 1340
    name     = "V Corps"
    division =
    { id            = { type = 22900 id = 26 }
      name          = "21st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 22900 id = 27 }
      name          = "22nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 22900 id = 28 }
      name          = "23rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 22900 id = 29 }
      name          = "24th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 22900 id = 30 }
      name     = "25th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 22900 id = 31 }
    location = 1339
    name     = "VI Corps"
    division =
    { id            = { type = 22900 id = 32 }
      name          = "26th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 22900 id = 33 }
      name          = "27th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 22900 id = 34 }
      name          = "28th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 22900 id = 35 }
      name          = "29th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 22900 id = 36 }
      name     = "30th Infantry Division"
      strength = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 22900 id = 37 }
    location = 1341
    name     = "VII Corps"
    division =
    { id            = { type = 22900 id = 38 }
      name          = "31st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 22900 id = 39 }
      name          = "32nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 22900 id = 40 }
      name          = "33rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  # ####################################
  # NAVY
  # ####################################
  navalunit =
  { id       = { type = 22900 id = 200 }
    location = 1335
    base     = 1335
    name     = "1st Fleet"
    division =
    { id    = { type = 22900 id = 201 }
      name  = "HQ Pham Ngu Lao"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 22900 id = 202 }
      name  = "HQ FF-002"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 22900 id = 203 }
      name  = "HQ FF-003"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 22900 id = 204 }
      name  = "HQ FF-004"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 22900 id = 205 }
      name  = "HQ FF-005"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 22900 id = 206 }
      name  = "HQ FF-006"
      type  = destroyer
      model = 1
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 22900 id = 100 }
    location = 1328
    base     = 1328
    name     = "1st Air Force"
    division =
    { id       = { type = 22900 id = 101 }
      name     = "1st Fighter Squadron"
      type     = multi_role
      strength = 50
      model    = 2
    }
    division =
    { id       = { type = 22900 id = 102 }
      name     = "2nd Fighter Squadron"
      type     = tactical_bomber
      strength = 65
      model    = 1
    }
    division =
    { id       = { type = 22900 id = 103 }
      name     = "3rd Fighter Squadron"
      type     = tactical_bomber
      strength = 65
      model    = 1
    }
    division =
    { id       = { type = 22900 id = 104 }
      name     = "4th Fighter Squadron"
      type     = tactical_bomber
      strength = 65
      model    = 1
    }
  }
  airunit =
  { id       = { type = 22900 id = 105 }
    location = 1337
    base     = 1337
    name     = "2nd Air Force"
    division =
    { id       = { type = 22900 id = 106 }
      name     = "5th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 22900 id = 107 }
      name     = "6th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 22900 id = 108 }
      name     = "7th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 22900 id = 109 }
      name     = "8th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 22900 id = 110 }
    location = 1328
    base     = 1328
    name     = "3rd Air Force"
    division =
    { id       = { type = 22900 id = 111 }
      name     = "9th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 22900 id = 112 }
      name     = "15th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
}
