
##############################
# Country definition for MON #
##############################

province =
{ id       = 1404
  air_base = { size = 2 current_size = 2 }
}            # Ulan Bator

country =
{ tag                 = MON
  # Resource Reserves
  energy              = 200
  metal               = 200
  rare_materials      = 100
  oil                 = 200
  supplies            = 500
  money               = 10
  manpower            = 5
  capital             = 1404
  nationalprovinces   = { 1420 1419 1434 1436 1437 1438 1399 1404 1385 }
  ownedprovinces      = { 1420 1419 1434 1436 1437 1438 1399 1404 1385 }
  controlledprovinces = { 1420 1419 1434 1436 1437 1438 1399 1404 1385 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					#Army Org
					1260
                                        1000 1050
                                        1010 1060
                                        1300 1310
                                        1400 1410
                                        1500 1510
                                        1900 1910
                                        1970
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
					4800 4700 4710 4750 4760
                                        4000 4010 4020
                                        4640 4650
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
    democratic        = 10
    political_left    = 10
    free_market       = 6
    freedom           = 8
    professional_army = 1
    defense_lobby     = 3
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 15800 id = 1 }
    location = 1404
    name     = "I Corps"
    division =
    { id            = { type = 15800 id = 2 }
      name          = "1st Motorized Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 15800 id = 3 }
      name     = "2nd Motorized Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 15800 id = 200 }
    location = 1404
    base     = 1404
    name     = "1st Air Force"
    division =
    { id       = { type = 15800 id = 201 }
      name     = "1st Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
}
