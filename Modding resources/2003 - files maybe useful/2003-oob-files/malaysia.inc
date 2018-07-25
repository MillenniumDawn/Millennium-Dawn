
##############################
# Country definition for MLY #
##############################

province =
{ id         = 1351
  naval_base = { size = 6 current_size = 6 }
}              # Kuantan

province =
{ id       = 1352
    air_base = { size = 4 current_size = 4 }
}            # Kuala Lumpur

country =
{ tag                 = MLY
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 90
  manpower            = 77
  capital             = 1352
  transports          = 100
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1349 1350 1351 1352 1644 1646 1647 }
  ownedprovinces      = { 1349 1350 1351 1352 1644 1646 1647 }
  controlledprovinces = { 1349 1350 1351 1352 1644 1646 1647 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Org
					1980
                                        1500 1510 1520
                                        1300 1310 1320
                                        1400 1410 1420
                                                  1600
                                             1700 1710
                                             1800 1810
                                        1900 1910 1920
                                        1260 1270
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					#Secret Weapons
					7180
                                        7330 7310
                                        #Navy Techs
                                        3000 3010 3020
                                        3700 3710 37710
                                        3590
                                        3850 3860 3870
					#Air Force
                                        4000 4010 4020 4030
                                        4570
                                        4400 4410
                                        4640 4650
                                        4700 4710 4720
                                        4750 4760 4770
                                        4800 4810
                                        4900 4910
					#Air Docs
                                        9050 9130
                                        9060 9140
                                        9070 9150
                                        9090 9170
                                        9120
                                        9510 9520 9020
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8400 8410
                                        8000 8010
                                        8500 8510
					
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 6
    political_left    = 5
    free_market       = 7
    freedom           = 4
    professional_army = 10
    defense_lobby     = 5
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12226 id = 1 }
    location = 1352
    name     = "Malaysian Army"
    division =
    { id            = { type = 12226 id = 2 }
      name          = "Malay HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 12226 id = 3 }
      name          = "1st Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12226 id = 4 }
      name          = "2nd Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12226 id = 5 }
      name          = "3rd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 12226 id = 6 }
      name          = "10th Parachute Brigade"
      strength      = 100
      type          = paratrooper
      model         = 14
    }
  }
  landunit =
  { id       = { type = 12226 id = 7 }
    location = 1644
    name     = "II Corps"
    division =
    { id            = { type = 12226 id = 8 }
      name          = "4th Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { experience    = 5
      id            = { type = 12226 id = 9 }
      name          = "1st Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 12226 id = 200 }
    location = 1351
    base     = 1351
    name     = "23rd Frigate Squadron"
    division =
    { id    = { type = 12226 id = 201 }
      name  = "KD Jebat"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 12226 id = 202 }
      name  = "KD Lekiu"
      type  = destroyer
      model = 2
    }
  }
  navalunit =
  { id       = { type = 12226 id = 203 }
    location = 1351
    base     = 1351
    name     = "24th Frigate Squadron"
    division =
    { id    = { type = 12226 id = 204 }
      name  = "KD Lekir"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12226 id = 205 }
      name  = "KD Kasturi"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 12226 id = 206 }
    location = 1351
    base     = 1351
    name     = "Royal Transport Fleet"
    division =
    { id    = { type = 12226 id = 207 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12226 id = 208 }
      name  = "2nd Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 12226 id = 100 }
    location = 1352
    base     = 1352
    name     = "1st Air Division"
    division =
    { id       = { type = 12226 id = 101 }
      name     = "6th Squadron"
      type     = tactical_bomber
      strength = 70
      model    = 0
    }
    division =
    { id       = { type = 12226 id = 102 }
      name     = "19th Squadron"
      type     = interceptor
      strength = 50
      model    = 2
    }
    division =
    { id       = { type = 12226 id = 103 }
      name     = "18th Squadron"
      type     = interceptor
      strength = 50
      model    = 3
    }
  }
}
