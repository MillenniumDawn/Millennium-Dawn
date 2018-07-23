
##############################
# Country definition for VEN #
##############################

province =
{ id         = 811
  naval_base = { size = 4 current_size = 4 }
   air_base = { size = 4 current_size = 4 } 
}              # Caracas

country =
{ tag                 = VEN
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 20
  capital             = 811
  manpower            = 49
  transports          = 65
  escorts             = 0
  diplomacy           = {
relation = { tag = PER value = 150 }
relation = { tag = CHC value = 150 } 
relation = { tag = CUB value = 200 }
}
  nationalprovinces   = { 804 802 810 811 869 870 871 }
  ownedprovinces      = { 804 802 810 811 869 870 }
  controlledprovinces = { 804 802 810 811 869 870 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equipment
                                        2000 2050
                                        2010 2060 2070
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Equipment
                                        1000 1050
                                        1010 1060 1070
                                        1500 1510 1520
                                        1200 1210 1220
                                        1300 1310 1320
                                        1400 1410 1420
                                        1900 1910 1920
                                        1260 1270
                                        1980
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
                                        4000 4010
                                        4570
                                        4100 4110
                                        4640 4650
                                        4700 4710
                                        4750 4760
                                        #Navy Techs
                                        3000 3010
                                        3700 3710
                                        3590
                                        3850 3860
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8400 8410
                                        8000 8010
                                        8500 8510
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 10
    free_market       = 4
    freedom           = 4
    professional_army = 3
    defense_lobby     = 3
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 22800 id = 1 }
    location = 811
    name     = "Military Region One"
    division =
    { id       = { type = 22800 id = 2 }
      name     = "4th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 22800 id = 3 }
      name     = "1st Armored Cavalry Division"
      strength = 100
      type     = armor
      model    = 8
    }
  }
  landunit =
  { id       = { type = 22800 id = 4 }
    location = 804
    name     = "Military Region Two"
    division =
    { id       = { type = 22800 id = 5 }
      name     = "1st Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 22800 id = 6 }
    location = 811
    name     = "Military Region Four"
    division =
    { id       = { type = 22800 id = 7 }
      name     = "3rd Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 22800 id = 8 }
    location = 870
    name     = "Military Region Five"
    division =
    { id       = { type = 22800 id = 9 }
      name     = "2nd Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 22800 id = 300 }
    location = 811
    base     = 811
    name     = "Venezuelan Navy"
    division =
    { id    = { type = 22800 id = 301 }
      name  = "ARV Mariscal Sucre"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 22800 id = 302 }
      name  = "ARV Almirante Brion"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 22800 id = 303 }
      name  = "ARV General Urdaneta"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 22800 id = 304 }
      name  = "ARV General Soublette"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 22800 id = 305 }
      name  = "ARV General Salom"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 22800 id = 306 }
      name  = "ARV Almirante Garcia"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 22800 id = 307 }
      name  = "ARV 1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 22800 id = 308 }
      name  = "ARV 2nd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 22800 id = 309 }
    location = 811
    base     = 811
    name     = "Submarine Fleet"
    division =
    { id    = { type = 22800 id = 310 }
      name  = "ARV Salabo"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 22800 id = 311 }
      name  = "ARV Caribe"
      type  = submarine
      model = 2
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 22800 id = 200 }
    location = 811
    base     = 811
    name     = "Air Force of Venezuela"
    division =
    { id       = { type = 22800 id = 201 }
      name     = "16th Fighter Squadron"
      type     = multi_role
      strength = 50
      model    = 1
    }
    division =
    { id       = { type = 22800 id = 202 }
      name     = "11th Fighter Squadron"
      type     = interceptor
      strength = 65
      model    = 1
    }
    division =
    { id       = { type = 22800 id = 203 }
      name     = "4th Ground Attack Squadron"
      type     = tactical_bomber
      strength = 65
      model    = 0
    }
  }
}
