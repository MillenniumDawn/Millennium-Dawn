
##############################
# Country definition for CAL #
##############################

province =
{ id       = 1288
  naval_base = { size = 4 current_size = 4 }
}            # Chittagong

province =
{ id       = 1286
  air_base = { size = 4 current_size = 4 }
}            # Comilla

country =
{ tag                 = CAL
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 268
  capital             = 1285
  transports          = 41
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1285 1286 1288 }
  ownedprovinces      = { 1285 1286 1288 }
  controlledprovinces = { 1285 1286 1288 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150      5170      5190
					#Army Equip
                                        2000 2050
                                        2010 2060
                                        2300 2310
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Org
					1980
                                        1000 1050
                                        1010 1060
                                        1500 1510
                                        1300 1310 1320
                                        1400 1410 1420
                                        1900 1910 1920
                                        1260 1270
					#Aircraft
					4700
                                        4750
                                        4800
                                        4000 4010
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160
                                        6200 6210 6220 6260
                                        6170 6270
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
    democratic        = 8
    political_left    = 5
    free_market       = 6
    freedom           = 5
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 6100 id = 1 }
    location = 1285
    name     = "I Corps"
    division =
    { id            = { type = 6100 id = 2 }
      name          = "9th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 6100 id = 3 }
      name          = "55th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id            = { type = 6100 id = 4 }
      name          = "11th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id       = { type = 6100 id = 5 }
      name     = "66th Infantry Division"
      strength = 100
      type     = motorized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 6100 id = 6 }
    location = 1286
    name     = "II Corps"
    division =
    { id       = { type = 6100 id = 7 }
      name     = "33rd Infantry Division"
      strength = 100
      type     = motorized
      model    = 2
    }
    division =
    { id            = { type = 6100 id = 8 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
  }
  landunit =
  { id       = { type = 6100 id = 9 }
    location = 1288
    name     = "III Corps"
    division =
    { id            = { type = 6100 id = 10 }
      name          = "24th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 2
    }
    division =
    { id       = { type = 6100 id = 11 }
      name     = "1st Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 6100 id = 300 }
    location = 1288
    base     = 1288
    name     = "1st Fleet"
    division =
    { id    = { type = 6100 id = 301 }
      name  = "BNS Khalid Bin Walid"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 6100 id = 302 }
      name  = "BNS Osman"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 6100 id = 303 }
      name  = "BNS Abu Bakr"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 6100 id = 304 }
      name  = "BNS Ali Haider"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 6100 id = 305 }
      name  = "BNS Umar Farooq"
      type  = destroyer
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 6100 id = 200 }
    location = 1286
    base     = 1286
    name     = "1st Air Force"
    division =
    { id       = { type = 6100 id = 201 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
}
