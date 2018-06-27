
##############################
# Country definition for CHL #
##############################

province =
{ id       = 840
  naval_base = { size = 4 current_size = 4 }
    air_base = { size = 4 current_size = 4 }
}            # Santiago

country =
{ tag                 = CHL
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 40
  capital             = 840
  manpower            = 31
  transports          = 47
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 864 861 860 856 840 839 841 842 }
  ownedprovinces      = { 864 861 860 856 840 839 841 842 }
  controlledprovinces = { 864 861 860 856 840 839 841 842 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
                                        2000 2050 2110
                                        2010 2060 2120
                                             2070
                                        2300 2310 2320
                                        2400 2410 2420
                                        2500 2510 2520
                                        2200 2210 2220
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Org
                                        1000 1050 1110
                                        1010 1060
                                             1070
                                        1500 1510 1520
                                        1300 1310 1320
                                        1400 1410 1420
                                        1900 1910 1920
                                        1260 1270
                                        1960 1970
					#Aircraft
					4570
                                        4000 4010
                                        4640 4650
                                        4400 4410
					4700
					4750
					4800
					4900
					#Land Docs
					6010 6020 6910 6920 6930 6600 6620
					6100 6110 6120 6160 6170
                                        6200 6210 6220 6260
					#Air Docs
					9020 9520
					9050 9060 9070
					#Secret Weapons
					7010 7060 7070
					7180
                                        #Navy Techs
                                        3000 3010
                                        3100
                                        3590
                                        3700 3710
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
    democratic        = 9
    political_left    = 4
    free_market       = 7
    freedom           = 9
    professional_army = 5
    defense_lobby     = 5
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 8200 id = 1 }
    location = 839
    name     = "1st Region"
    division =
    { id       = { type = 8200 id = 2 }
      name     = "1st Armored Cavalry Regiment"
      strength = 100
      type     = light_armor
      model    = 3
    }
  }
  landunit =
  { id       = { type = 8200 id = 3 }
    location = 839
    name     = "2nd Region"
    division =
    { id       = { type = 8200 id = 4 }
      name     = "1st Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8200 id = 5 }
    location = 840
    name     = "4th Region"
    division =
    { id       = { type = 8200 id = 6 }
      name     = "2nd Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { experience    = 5
      id            = { type = 8200 id = 7 }
      name          = "1st Spec. Op. Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 8200 id = 8 }
    location = 856
    name     = "8th Region"
    division =
    { id       = { type = 8200 id = 9 }
      name     = "3rd Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8200 id = 10 }
    location = 860
    name     = "10th Region"
    division =
    { id       = { type = 8200 id = 11 }
      name     = "4th Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8200 id = 12 }
    location = 839
    name     = "12th Region"
    division =
    { id       = { type = 8200 id = 13 }
      name     = "5th Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 8200 id = 200 }
    location = 840
    base     = 840
    name     = "Chilean Navy"
    division =
    { id    = { type = 8200 id = 201 }
      name  = "Blanco Encalada"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8200 id = 202 }
      name  = "Cochrane"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 8200 id = 203 }
      name  = "Condell"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 8200 id = 204 }
      name  = "Lynch"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 8200 id = 205 }
      name  = "Ministro Zenteno"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 8200 id = 206 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 8200 id = 207 }
      name  = "2nd Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 8200 id = 209 }
    location = 840
    base     = 840
    name     = "Submarine Fleet"
    division =
    { id    = { type = 8200 id = 210 }
      name  = "Thompson"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 8200 id = 211 }
      name  = "Simpson"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 8200 id = 212 }
      name  = "O'Brien"
      type  = submarine
      model = 2
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 8200 id = 100 }
    location = 840
    base     = 840
    name     = "1st Air Brigade"
    division =
    { id       = { type = 8200 id = 101 }
      name     = "1st Aviation Group"
      type     = tactical_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 8200 id = 103 }
      name     = "4th Aviation Group"
      type     = interceptor
      strength = 30
      model    = 1
    }
    division =
    { id       = { type = 8200 id = 104 }
      name     = "12th Aviation Group"
      type     = tactical_bomber
      strength = 100
      model    = 0
    }
  }
}
