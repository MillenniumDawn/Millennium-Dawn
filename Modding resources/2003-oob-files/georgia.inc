
##############################
# Country definition for GEO #
##############################


province =
{ id       = 1848
  air_base = { size = 2 current_size = 2 }
}            # Batum

country =
{ tag                 = GEO
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 90
  manpower            = 10
  capital             = 1850
  diplomacy           = { 
    relation =
    { tag        = ALS
      value      = -150
    }
    relation =
    { tag        = PRI
      value      = -150
    }
 }
  nationalprovinces   = { 2605 1845 1848 1850 2606 2602 }
  ownedprovinces      = { 2605 1848 1850 2606 }
  controlledprovinces = { 2605 1848 1850 2606 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
                                        2000 2050
                                        2010 2060
                                        2300 2310 2320
                                        2400 2410 2420
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Org
                                        1000 1050
                                        1010 1060
                                        1500 1510 1520
                                        1300 1310 1320
                                        1900 1910 1920
                                        1260 1270
                                        1960
					#Aircraft
					4800 4700 4710 4750 4760 4900
					4550 4560
                                        4640 4650
					#Land Docs
					6910
					6600 6610
					6010 6020
					6100 6110 6120 6160
					#Air Docs
					9010 9510
					9050 9060 9070
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 7
    political_left    = 5
    free_market       = 6
    freedom           = 6
    professional_army = 3
    defense_lobby     = 2
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 11000 id = 1 }
    location = 1850
    name     = "I Corps"
    division =
    { id       = { type = 11000 id = 2 }
      name     = "1st Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 11000 id = 3 }
      name     = "2nd Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 11000 id = 4 }
      name     = "3rd Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 11000 id = 5 }
    location = 1848
    name     = "II Corps"
    division =
    { id            = { type = 11000 id = 6 }
      name          = "4th Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 11000 id = 200 }
    location = 1848
    base     = 1848
    name     = "1st Air Force"
    division =
    { id       = { type = 11000 id = 201 }
      name     = "1st Squadron"
      type     = cas
      strength = 50
      model    = 0
    }
    division =
    { id       = { type = 11000 id = 202 }
      name     = "2nd Squadron"
      type     = cas
      strength = 50
      model    = 1
    }
  }
}
