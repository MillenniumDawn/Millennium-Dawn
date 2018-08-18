
##############################
# Country definition for SIA #
##############################

province =
{ id       = 1343
  naval_base = { size = 6 current_size = 6 }
    air_base = { size = 6 current_size = 6 }
}            # Bangkok

country =
{ tag                 = SIA
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 1000
  oil                 = 500
  supplies            = 500
  money               = 50
  capital             = 1343
  manpower            = 103
  transports          = 126
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1348 1347 1345 1343 1342 1331 1330 1344 1303 }
  ownedprovinces      = { 1348 1347 1345 1343 1342 1331 1330 1344 1303 }
  controlledprovinces = { 1348 1347 1345 1343 1342 1331 1330 1344 1303 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
					2200 2210 2220
					2800 2810 2820
					2600 2610 2620
					2700 2710 2720
					2400 2410 2420
					2300 2310 2320
                                        2000 2050 2110
                                        2010 2060
                                             2070
					2500 2510 2520
					#Army Org
					1900 1910 1920
					1260 1270
					1700
					1800 1810
                                        1000 1050 1110
                                        1010 1060
                                             1070
					1500 1510
					1200 1210
					1300 1310 1320
					1400 1410 1420
					1600 1650
                                        1980
					#Aircraft
					4800 4810
					4700 4710
					4750 4760
					4900 4910
                                        4000 4010 4020
                                        4570
                                        4400 4410
                                        4640 4650
					#Land Docs
					6930
					6010 6030 6040
					6600 6610
					6100 6110 6120 6130 6140 6150 6160 6170
					#Air Docs
					9020 9510 9520
					9050 9060 9070 9120
					9130 9140 9150
					#Secret Weapons
					7180
                                        7330 7310
                                        #Navy Techs
                                        3000 3010
                                        3400 3410
                                        3590
                                        3850 3860
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8000 8010
                                        8500 8510
                                        8300
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 6
    free_market       = 7
    freedom           = 7
    professional_army = 3
    defense_lobby     = 2
    interventionism   = 6
  }
  # ####################################
  # ARMY
  # ####################################
  landunit =
  { id       = { type = 21300 id = 1 }
    location = 1343
    name     = "First Army Area"
    division =
    { id            = { type = 21300 id = 2 }
      name          = "Royal Thai Army HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 21300 id = 3 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 21300 id = 4 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 21300 id = 5 }
      name          = "9th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 21300 id = 6 }
      name          = "11th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 21300 id = 7 }
      name          = "3rd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id       = { type = 21300 id = 8 }
      name     = "1st Mechanized Cavalry Division"
      strength = 100
      type     = infantry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 21300 id = 9 }
    location = 1343
    name     = "Special Operations Command"
    division =
    { experience    = 10
      id            = { type = 21300 id = 11 }
      name          = "1st Special Operations Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { experience    = 10
      id            = { type = 21300 id = 12 }
      name          = "2nd Special Operations Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { experience    = 10
      id            = { type = 21300 id = 13 }
      name          = "3rd Special Operations Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { experience    = 10
      id            = { type = 21300 id = 14 }
      name          = "4th Special Operations Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { experience    = 10
      id            = { type = 21300 id = 15 }
      name          = "5th Special Operations Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { experience    = 10
      id            = { type = 21300 id = 16 }
      name          = "6th Special Operations Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 21300 id = 17 }
      name          = "1st Marine Brigade"
      strength      = 100
      type          = marine
      model         = 11
    }
    division =
    { id            = { type = 21300 id = 18 }
      name          = "2nd Marine Brigade"
      strength      = 100
      type          = marine
      model         = 11
    }
  }
  landunit =
  { id       = { type = 21300 id = 19 }
    location = 1331
    name     = "Second Army Area"
    division =
    { id            = { type = 21300 id = 20 }
      name          = "3rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 21300 id = 21 }
      name          = "6th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 21300 id = 22 }
      name          = "12th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 21300 id = 23 }
      name          = "1st Armored Division"
      strength      = 100
      type          = armor
      model         = 8
    }
  }
  # ####################################
  # NAVY
  # ####################################
  navalunit =
  { id       = { type = 21300 id = 200 }
    location = 1343
    base     = 1343
    name     = "Royal Thai Navy"
    division =
    { id    = { type = 21300 id = 201 }
      name  = "HTMS Chakri Nareubet"
      type  = escort_carrier
      model = 1
    }
    division =
    { id    = { type = 21300 id = 202 }
      name  = "HTMS Naresuan"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21300 id = 203 }
      name  = "HTMS Taksin"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21300 id = 204 }
      name  = "HTMS Chao Phraya"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21300 id = 205 }
      name  = "HTMS Bangpakong"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21300 id = 206 }
      name  = "HTMS Kraburi"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21300 id = 207 }
      name  = "HTMS Saiburi"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 21300 id = 208 }
      name  = "HTMS Phutthayofta Chulaok"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 21300 id = 209 }
      name  = "HTMS Phutthaloetla Naphalai"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 21300 id = 210 }
    location = 1343
    base     = 1343
    name     = "1st Amphibious Fleet"
    division =
    { id    = { type = 21300 id = 211 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 21300 id = 212 }
      name  = "2nd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 21300 id = 100 }
    location = 1343
    base     = 1343
    name     = "1st Wing"
    division =
    { id       = { type = 21300 id = 101 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 70
      model    = 1
    }
    division =
    { id       = { type = 21300 id = 102 }
      name     = "21st Squadron"
      type     = interceptor
      strength = 70
      model    = 1
    }
    division =
    { id       = { type = 21300 id = 103 }
      name     = "6th Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 21300 id = 104 }
      name     = "3rd Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
}
