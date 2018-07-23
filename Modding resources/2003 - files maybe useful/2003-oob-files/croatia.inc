
##############################
# Country definition for CRO #
##############################

province =
{ id       = 384
  naval_base = { size = 2 current_size = 2 }
  air_base = { size = 2 current_size = 2 }
}            # Split

country =
{ tag                 = CRO
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 7
  transports          = 30
  escorts             = 0
  capital             = 382
  diplomacy           = { }
  nationalprovinces   = { 454 455 382 381 384 388 1400 1401 }
  ownedprovinces      = { 454 455 382 381 384 388 1400 1401 }
  controlledprovinces = { 454 455 382 381 384 388 1400 1401 }
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
					5210 5220
                                        #Army Equipment:
                                        2000 2050
                                        2010 2060
                                             2070
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
                                        #Army Organisation:
                                        1000 1050
                                        1010 1060
                                        1500 1510 1520
                                        1300 1310 1320
                                        1400 1410 1420
                                        1900 1910 1920
                                        1260 1270
                                        1960
                                        #Army Doctrines:
                                        6100 6200
                                        6110 6210
                                        6120 6220
                                        6160 6260
                                        6010
                                        6020
                                        6910
                                        6600
                                        6610
					#Secret Weapons
                                        7330 7310 7320
                                        #Air Force
                                        4000 4010
                                        4700
                                        4750
					#Air Docs
					9020 9510 9520
					9050 9060 9070 9090 9120
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 8
    free_market       = 6
    freedom           = 8
    professional_army = 4
    defense_lobby     = 4
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 8600 id = 1 }
    location = 454
    name     = "III Corps"
    division =
    { id            = { type = 8600 id = 2 }
      name          = "3rd Mechanized Guards Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
  }
  landunit =
  { id       = { type = 8600 id = 3 }
    location = 455
    name     = "I Corps"
    division =
    { id            = { type = 8600 id = 4 }
      name          = "2nd Guards Brigade 'Thunders'"
      strength      = 100
      type          = cavalry
      model         = 1
    }
  }
  landunit =
  { id       = { type = 8600 id = 5 }
    location = 1401
    name     = "IV Corps"
    division =
    { id            = { type = 8600 id = 6 }
      name          = "4th Guards Brigade 'Spiders'"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 8600 id = 7 }
      name          = "628th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 8600 id = 8 }
    location = 1401
    name     = "V Corps"
    division =
    { id            = { type = 8600 id = 9 }
      name          = "1st Guards Brigade 'Tigers'"
      strength      = 100
      type          = cavalry
      model         = 2
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 8600 id = 200 }
    location = 384
    name     = "21st Fighter Squadron"
    division =
    { id            = { type = 8600 id = 201 }
      name          = "21st Fighter Squadron"
      strength      = 50
      type          = interceptor
      model         = 1
    }
  }
}
