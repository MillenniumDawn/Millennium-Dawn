
##############################
# Country definition for EGY #
##############################

province =
{ id       = 906
  naval_base = { size = 4 current_size = 4 }
}            # Alexandria

province =
{ id       = 903
    air_base = { size = 8 current_size = 8 }
}            # Cairo

province =
{ id       = 1801
    air_base = { size = 4 current_size = 4 }
}            # Sharm el-Sheikh

country =
{ tag                 = EGY
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 70
  manpower            = 95
  transports          = 77
  escorts             = 0
  capital             = 903
  diplomacy           = { }
  nationalprovinces   = { 961 962 964 4 900 901 902 903 904 905 906 907 908 909 910 911 912 914 1800 1801 1019 1020 1021 1022 1023 1024 1025 1026 1027 }
  ownedprovinces      = { 961 962 964 4 900 901 902 903 904 905 906 907 908 909 910 911 912 914 1800 1801 1019 1020 1021 1022 1023 1024 1025 1026 1027 }
  controlledprovinces = { 961 962 964 4 900 901 902 903 904 905 906 907 908 909 910 911 912 914 1800 1801 1019 1020 1021 1022 1023 1024 1025 1026 1027 }
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
                                        #Army Equipment:
                                        2000 2050 2110
                                        2010
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
                                        #Army Organisation:
                                        1000 1050 1110
                                        1010
                                        1500 1510 1520
                                        1200 1210 1220
                                        1300 1310 1320
                                        1400 1410 1420
                                        1700
                                        1800 1810
                                        1900 1910 1920
                                        1260 1270
                                        1970
                                        #Army Doctrines:
                                        6100 6200
                                        6110 6210
                                        6120 6220
                                        6140
                                        6150
                                        6160 6260
                                        6170
                                        6010
                                        6020
                                        6910
                                        6600
                                        6620
                                        #Air Force:
                                        4000 4010 4020 4030
                                        4100 4110
                                        4400 4410
                                        4640 4650
                                        4700 4710 4720
                                        4750 4760 4770
                                        4800 4810
                                        4900 4910
                                        #Air Docs:
                                        9050 9130
                                        9060 9140
                                        9070 9150
                                        9090 9170
                                        9100
                                        9110
                                        9120
                                        9010
                                        9510
                                        #Navy Techs
                                        3000 3010
                                        3590
                                        3700
                                        3850 3860
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8400 8410
                                        8000 8010
                                        8500 8510
                                        #Secret Techs
                                        7330
                                        7310

                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 2
    political_left    = 5
    free_market       = 6
    freedom           = 2
    professional_army = 3
    defense_lobby     = 6
    interventionism   = 7
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 9600 id = 1 }
    location = 901
    name     = "Second Field Army"
    division =
    { id            = { type = 9600 id = 2 }
      name          = "8th Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 9600 id = 3 }
      name          = "1st Independent Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 9600 id = 4 }
      name          = "2nd Independent Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 9600 id = 5 }
    location = 900
    name     = "Third Field Army"
    division =
    { id            = { type = 9600 id = 6 }
      name          = "Sinai HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 9600 id = 7 }
      name          = "1st Armored Division"
      strength      = 100
      type          = armor
      model         = 15
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 9600 id = 8 }
      name          = "2nd Armored Division"
      strength      = 100
      type          = armor
      model         = 8
    }
    division =
    { id            = { type = 9600 id = 9 }
      name          = "3rd Armored Division"
      strength      = 100
      type          = armor
      model         = 8
    }
    division =
    { id            = { type = 9600 id = 10 }
      name          = "4th Armored Division"
      strength      = 100
      type          = armor
      model         = 15
    }
    division =
    { id            = { type = 9600 id = 11 }
      name          = "5th Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 9600 id = 12 }
      name          = "6th Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 9600 id = 13 }
      name          = "7th Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 9600 id = 14 }
      name          = "1st Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 9600 id = 15 }
      name          = "2nd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 9600 id = 16 }
      name          = "3rd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 9600 id = 17 }
      name          = "4th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
  }
  landunit =
  { id       = { type = 9600 id = 18 }
    location = 914
    name     = "Western Military Region"
    division =
    { id            = { type = 9600 id = 19 }
      name          = "3rd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }

  }
  landunit =
  { id       = { type = 9600 id = 20 }
    location = 903
    name     = "Central Military Region"
    division =
    { id            = { type = 9600 id = 21 }
      name          = "Cairo HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 9600 id = 22 }
      name          = "Republican Guard Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 7
    }
    division =
    { id            = { type = 9600 id = 23 }
      name          = "4th Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id       = { type = 9600 id = 24 }
      name     = "1st Airmobile Brigade"
      strength = 100
      type     = militia
      model    = 1
    }
    division =
    { id       = { type = 9600 id = 25 }
      name     = "1st Airborne Brigade"
      strength = 100
      type     = paratrooper
      model    = 14
    }
    division =
    { id            = { type = 9600 id = 26 }
      name          = "1st Commando Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 9600 id = 27 }
    location = 906
    name     = "Northern Military Region"
    division =
    { id            = { type = 9600 id = 28 }
      name          = "2nd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
  }
  landunit =
  { id       = { type = 9600 id = 29 }
    location = 1023
    name     = "Southern Military Region"
    division =
    { id            = { type = 9600 id = 30 }
      name          = "1st Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 9600 id = 300 }
    location = 906
    base     = 906
    name     = "1st Fleet"
    division =
    { id    = { type = 9600 id = 301 }
      name  = "Mubarak"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 9600 id = 302 }
      name  = "Taba"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 9600 id = 303 }
      name  = "Rasheed"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 9600 id = 304 }
      name  = "El Suez"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 9600 id = 305 }
    location = 906
    base     = 906
    name     = "2nd Fleet"
    division =
    { id    = { type = 9600 id = 306 }
      name  = "Sharm El-Sheikh"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 9600 id = 307 }
      name  = "Toushka"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 9600 id = 308 }
      name  = "El Aboukir"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 9600 id = 309 }
      name  = "Najim al Zafir"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 9600 id = 310 }
    location = 906
    base     = 906
    name     = "3rd Fleet"
    division =
    { id    = { type = 9600 id = 311 }
      name  = "Damyat"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 9600 id = 312 }
      name  = "Al Nasser"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 9600 id = 313 }
    location = 906
    base     = 906
    name     = "Submarine Fleet"
    division =
    { id    = { type = 9600 id = 314 }
      name  = "831"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 9600 id = 315 }
      name  = "842"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 9600 id = 316 }
      name  = "852"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 9600 id = 317 }
      name  = "858"
      type  = submarine
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 9600 id = 200 }
    location = 1801
    base     = 1801
    name     = "Mersa Matruh Airbase"
    division =
    { id       = { type = 9600 id = 201 }
      name     = "112nd Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 9600 id = 202 }
      name     = "104th Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 9600 id = 203 }
      name     = "102nd Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 9600 id = 204 }
    location = 1801
    base     = 1801
    name     = "Sinai Airbase"
    division =
    { id       = { type = 9600 id = 205 }
      name     = "222nd Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 9600 id = 206 }
      name     = "211th Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 9600 id = 207 }
      name     = "272nd Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 9600 id = 208 }
    location = 1801
    base     = 1801
    name     = "Sharm el-Sheikh Airbase"
    division =
    { id       = { type = 9600 id = 209 }
      name     = "33rd Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 9600 id = 210 }
      name     = "35th Fighter Brigade"
      type     = interceptor
      strength = 70
      model    = 2
    }
    division =
    { id       = { type = 9600 id = 211 }
      name     = "64th Fighter Brigade"
      type     = interceptor
      strength = 70
      model    = 2
    }
  }
  airunit =
  { id       = { type = 9600 id = 212 }
    location = 903
    base     = 903
    name     = "Cairo-West Airbase"
    division =
    { id       = { type = 9600 id = 213 }
      name     = "122nd Fighter Brigade"
      type     = interceptor
      strength = 80
      model    = 0
    }
    division =
    { id       = { type = 9600 id = 214 }
      name     = "111th Fighter Brigade"
      type     = interceptor
      strength = 80
      model    = 0
    }
    division =
    { id       = { type = 9600 id = 215 }
      name     = "172nd Fighter Brigade"
      type     = interceptor
      strength = 80
      model    = 0
    }
  }
  airunit =
  { id       = { type = 9600 id = 216 }
    location = 903
    base     = 903
    name     = "Cairo-East Airbase"
    division =
    { id       = { type = 9600 id = 217 }
      name     = "89th Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 9600 id = 218 }
      name     = "81st Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 9600 id = 219 }
      name     = "94th Fighter Brigade"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 9600 id = 220 }
    location = 903
    base     = 903
    name     = "Inshas Airbase"
    division =
    { id       = { type = 9600 id = 221 }
      name     = "236th Fighter Ground Attack Brigade"
      type     = multi_role
      strength = 60
      model    = 1
    }
    division =
    { id       = { type = 9600 id = 222 }
      name     = "228th Fighter Ground Attack Brigade"
      type     = multi_role
      strength = 60
      model    = 1
    }
  }
  airunit =
  { id       = { type = 9600 id = 223 }
    location = 903
    base     = 903
    name     = "Central Air Transport Command"
    division =
    { id       = { type = 9600 id = 224 }
      name     = "1st Air Transport Regiment"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
}
