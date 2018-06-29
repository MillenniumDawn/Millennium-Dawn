
##############################
# Country definition for TRK #
##############################

province =
{ id       = 1490
  air_base = { size = 4 current_size = 4 }
}            # Ashgabat

country =
{ tag                 = TRK
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 7
  capital             = 1490
  diplomacy           = { }
  nationalprovinces   = { 1490 1491 }
  ownedprovinces      = { 1490 1491 }
  controlledprovinces = { 1490 1491 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equipment
                                        2000 2050
                                        2010 2060
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Equipment
                                        1000 1050
                                        1010 1060
                                        1500 1510 1520
                                        1200 1210 1220
                                        1300 1310 1320
                                        1400 1410 1420
                                        1900 1910 1920
                                        1260 1270
                                        1970 1960
					#Land Docs
					6600 6610
					6010 6020
					6910
					6100 6110 6120 6160 6170
					6200 6210 6220 6260 6270
					#Air Docs
					9010 9510
					9050 9060 9070
					9150 9160 9170
					#Secret Weapons
                                        7330 7310
					#Air Force
                                        4400 4410
                                        4100 4110 4120
                                        4550
                                        4500 4510
                                        4640 4650
                                        4700 4710
                                        4750 4760
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 2
    political_left    = 8
    free_market       = 5
    freedom           = 1
    professional_army = 2
    defense_lobby     = 5
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 21900 id = 1 }
    location = 1490
    name     = "Turkmen Army"
    division =
    { id            = { type = 21900 id = 2 }
      name          = "2nd Motor Rifle Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 21900 id = 3 }
      name          = "3rd Motor Rifle Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 21900 id = 4 }
      name          = "11th Motor Rifle Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 21900 id = 5 }
      name          = "22nd Motor Rifle Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 21900 id = 200 }
    location = 1490
    base     = 1490
    name     = "1st Air Force"
    division =
    { id       = { type = 21900 id = 201 }
      name     = "1st Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21900 id = 202 }
      name     = "2nd Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 21900 id = 203 }
      name     = "3rd Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 21900 id = 204 }
      name     = "4th Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 21900 id = 205 }
      name     = "5th Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
}
