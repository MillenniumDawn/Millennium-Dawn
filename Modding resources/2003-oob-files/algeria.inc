
##############################
# Country definition for ALG #
##############################

province =
{ id         = 949
  naval_base = { size = 4 current_size = 4 }
  air_base = { size = 4 current_size = 4 }
}              # Algiers

country =
{ tag                 = ALG
  manpower            = 66
  transports          = 50
  escorts             = 0
  capital             = 949
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  diplomacy           = { }
  nationalprovinces   = { 942 943 944 945 946 947 948 949 950 951 952 953 970 1013 1014 }
  ownedprovinces      = { 942 943 944 945 946 947 948 949 950 951 952 953 970 1013 1014 }
  controlledprovinces = { 942 943 944 945 946 947 948 949 950 951 952 953 970 1013 1014 }
  techapps            = { 
					#Army Org
					1970
                                        1000 1050
                                        1010 1060
                                             1070
                                        1500 1510
                                        1200 1210
                                        1300 1310
                                        1400 1410
                                             1800
                                        1900 1910
                                        1260
					#Army Equip
                                        2000 2050
                                        2010 2060
                                             2070
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150      5170      5190
					#Land Docs
					6010 6020 6100 6200 6110 6120 6160 6170 6600 6610 6910
					#Air Docs
					9510 9010 9050 9060 9070
					#Secret Weapons
					7180
                                        #Navy Techs
                                        3000
                                        3590
                                        3700 3710 3720
                                        3850 3860
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8000 8010
                                        8500
                                        8400 8410
                                        #Air Force
                                        4000 4010 4020
                                        4100 4110
                                        4700 4710
                                        4750 4760
                                        4800 4810
                                        4900
                                        4640 4650
                                        4400
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 4
    political_left    = 6
    free_market       = 5
    freedom           = 3
    professional_army = 3
    defense_lobby     = 4
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 5200 id = 1 }
    location = 947
    name     = "Military Region I"
    division =
    { experience    = 5
      id            = { type = 5200 id = 2 }
      name          = "1st Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = police
      brigade_model = 0
    }
    division =
    { id            = { type = 5200 id = 3 }
      name          = "3rd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 5200 id = 4 }
      name          = "1st Armored Division"
      strength      = 100
      type          = armor
      model         = 13
      extra         = heavy_armor
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 5200 id = 5 }
    location = 970
    name     = "Military Region II"
    division =
    { id            = { type = 5200 id = 6 }
      name          = "2nd Armored Division"
      strength      = 100
      type          = armor
      model         = 7
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id            = { type = 5200 id = 7 }
      name          = "1st Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
      extra         = heavy_armor
      brigade_model = 0
    }
    division =
    { id            = { type = 5200 id = 8 }
      name          = "2nd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
      extra         = heavy_armor
      brigade_model = 0
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 5200 id = 300 }
    location = 949
    base     = 949
    name     = "Surface Fleet"
    division =
    { id    = { type = 5200 id = 301 }
      name  = "Mourad Rais"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 5200 id = 302 }
      name  = "Rais Kellik"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 5200 id = 303 }
      name  = "Rais Korfu"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 5200 id = 307 }
    location = 949
    base     = 949
    name     = "Submarine Fleet"
    division =
    { id    = { type = 5200 id = 308 }
      name  = "Rajs Hadi Mubarek"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 5200 id = 309 }
      name  = "El Hadi Slimane"
      type  = submarine
      model = 4
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 5200 id = 200 }
    location = 949
    base     = 949
    name     = "1st Air Force"
    division =
    { id       = { type = 5200 id = 201 }
      name     = "1st Fighter-Bomber Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 5200 id = 202 }
      name     = "2nd Fighter-Bomber Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 5200 id = 204 }
      name     = "2nd Interceptor Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 5200 id = 206 }
      name     = "3rd Interceptor Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 5200 id = 207 }
      name     = "4th Interceptor Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
}
