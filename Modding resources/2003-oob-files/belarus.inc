
##############################
# Country definition for BLR #
##############################

province =
{ id       = 212
  air_base = { size = 10 current_size = 10 }
}            # Minsk

country =
{ tag                 = BLR
  regular_id          = RUS
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 30
  capital             = 212
  diplomacy           = { }
  nationalprovinces   = { 209 240 210 211 212 213 214 217 218 220 221 222 225 226 272 503 504 507 1874 }
  ownedprovinces      = { 209 240 210 211 212 213 214 217 218 220 221 222 225 226 272 503 504 507 1874 }
  controlledprovinces = { 209 240 210 211 212 213 214 217 218 220 221 222 225 226 272 503 504 507 1874 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080
					5110 5120 5130 5140 5150 5160 5170 5180
					#Army Equip
                                        2000 2050
                                        2010 2060
                                        2400 2410 2420
                                        2300 2310 2320
					2200 2210 2220
                                        2500 2510 2520
					2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Org
					1990
                                        1000 1050
                                        1010 1060
                                        1500 1510 1520
                                        1300 1310 1320
                                             1700 1710
                                             1800 1810
                                        1900 1910 1920
                                        1260 1270
					#Aircraft
                                        4700 4710 4720
                                        4750 4760 4770
                                        4900 4910
                                        4640 4650
                                        4550
                                        4500 4510
                                        4100 4110
                                        4000 4010 4020 4030
					#Land Docs
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240      6260 6270
					6010 6020
					6910
					6600 6610
					#Air Docs
					9010 9510 9120
					9050 9060 9070 9090
					9150 9160 9170 9190
					#Secret Weapons
					7010 7060 7070
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 10
    free_market       = 2
    freedom           = 2
    professional_army = 2
    defense_lobby     = 2
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 6300 id = 1 }
    location = 209
    name     = "28th Army Corps"
    division =
    { id            = { type = 6300 id = 2 }
      name          = "6th Guards Motor Rifle Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 6300 id = 3 }
      name          = "11th Guards Motor Rifle Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 6300 id = 4 }
      name          = "50th Guards Motor Rifle Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
  }
  landunit =
  { id       = { type = 6300 id = 5 }
    location = 221
    name     = "5th Army Corps"
    division =
    { id            = { type = 6300 id = 6 }
      name          = "30th Guards Motor Rifle Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 6300 id = 7 }
      name          = "31th Guards Motor Rifle Brigade"
      strength      = 100
      type          = cavalry
      model         = 2     
    }
    division =
    { id            = { type = 6300 id = 8 }
      name          = "5th Tank Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
  }
  landunit =
  { id       = { type = 6300 id = 9 }
    location = 212
    name     = "28th Army Corps"
    division =
    { id       = { type = 6300 id = 10 }
      name     = "38th Assault-Landing Brigade"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id            = { type = 6300 id = 11 }
      name          = "11th Individual Mobile Brigade"
      strength      = 100
      type          = militia
      model         = 2      
    }
    division =
    { experience    = 10
      id            = { type = 6300 id = 12 }
      name          = "5th Spetznaz Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 5700 id = 100 }
    location = 212
    base     = 212
    name     = "Belarusian Air Force"
    division =
    { id       = { type = 5700 id = 101 }
      name     = "1st Interceptor Regiment"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 5700 id = 102 }
      name     = "2nd Interceptor Regiment"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 5700 id = 103 }
      name     = "1st Strike Regiment"
      type     = tactical_bomber
      strength = 30
      model    = 2
    }
    division =
    { id       = { type = 5700 id = 104 }
      name     = "2nd Strike Regiment"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 5700 id = 105 }
    location = 212
    base     = 212
    name     = "Air Transport Brigade"
    division =
    { id       = { type = 5700 id = 106 }
      name     = "1st Air Transport Squadron"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
}
