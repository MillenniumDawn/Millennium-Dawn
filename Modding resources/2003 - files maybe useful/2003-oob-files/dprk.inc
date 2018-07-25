
##############################
# Country definition for U09 #
##############################

province =
{ id       = 1392
  naval_base = { size = 6 current_size = 6 }
    air_base = { size = 10 current_size = 10 }
}            # Hamhung

province =
{ id       = 1201
    air_base = { size = 10 current_size = 10 }
}            # Pyongyang

province =
{ id         = 1393
      nuclear_reactor = 6
}            # Sinuiju

country =
{ tag                 = U09
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 1000
  supplies            = 1000
  money               = 40
  manpower            = 15
  capital             = 1201
  transports          = 40
  escorts             = 0
  diplomacy           = {
  relation = { tag = CHC value = 100 }
  relation = { tag = PER value = 80 }
  relation = { tag = WLL value = 80 }
  relation = { tag = PAK value = 80 }
  relation = { tag = MOZ value = 80 } 
  relation = { tag = RUS value = 25 }
  relation = { tag = USA value = -170 } }
  nationalprovinces   = { 1200 1201 1376 1391 1392 1393 1194 1195 1196 1197 1198 1199 }
  ownedprovinces      = { 1200 1201 1376 1391 1392 1393 }
  controlledprovinces = { 1200 1201 1376 1391 1392 1393 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110
					#Army Equip
					2000 2010
					2050
					2300 2310
					2400 2410
					2200 2210
					2500 2510
					2600 2610
					2700 2710
					2800 2810
					#Army Org
					1990
					1000 1010
					1050
					1260
					1900 1910				
					1500 1510
					1200 1210
					1300 1310
					1400 1410
					1800 
					#Aircraft
					4800 4700 4750
					4400
                                        4000 4010
                                        4100 4110
                                        4570
                                        4500
                                        4550
                                        4640 4650
					#Land Docs
					6910
					6600 6630
					6010 6030 6040
					6100 6110 6120 6140 6160 6170
					#Air Docs
					9010 9050 9060 9070 9090
                                        9510
					#Secret Weapons
					7010
					7020
					7060
                                        #Navy Techs
                                        3000
                                        3590
                                        3700 37700
                                        3850
                                        #Navy Doctrines
                                        8900
                                        8950
                                        8400
                                        8000
                                        8500
								
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 2
    political_left    = 10
    free_market       = 1
    freedom           = 1
    professional_army = 1
    defense_lobby     = 10
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 17000 id = 1 }
    location = 1200
    name     = "I Army Corps"
    division =
    { id            = { type = 17000 id = 2 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 3 }
      name          = "13th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 4 }
      name          = "31st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 5 }
      name          = "46th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 6 }
      name          = "U/I Light Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 8 }
    location = 1201
    name     = "II Army Corps"
    division =
    { id            = { type = 17000 id = 9 }
      name          = "3rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 10 }
      name          = "6th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 11 }
      name          = "8th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 12 }
      name          = "32nd Light Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 16 }
    location = 1200
    name     = "IV Army Corps"
    division =
    { id            = { type = 17000 id = 17 }
      name          = "26th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 18 }
      name          = "28th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 19 }
      name          = "33rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 20 }
      name          = "41st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 21 }
      name          = "23rd Light Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 24 }
    location = 1392
    name     = "V Army Corps"
    division =
    { id            = { type = 17000 id = 25 }
      name          = "5th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 26 }
      name          = "12th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 27 }
      name          = "25th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 28 }
      name          = "45th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 17000 id = 29 }
      name     = "75th Light Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 32 }
    location = 1391
    name     = "820th Army Corps"
    division =
    { id            = { type = 17000 id = 33 }
      name          = "U/I Armor Division"
      strength      = 100
      type          = armor
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 36 }
      name          = "15th Mechanized Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 17000 id = 37 }
      name          = "105th Armor Division"
      strength      = 100
      type          = armor
      model         = 11
      extra         = heavy_armor
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 17000 id = 38 }
    location = 1200
    name     = "806th Army Corps"
    division =
    { id            = { type = 17000 id = 41 }
      name          = "4th Mechanized Infantry Division"
      strength      = 100
      type          = infantry
      model         = 1
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id       = { type = 17000 id = 42 }
      name     = "7th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 45 }
    location = 1391
    name     = "815th Army Corps"
    division =
    { id            = { type = 17000 id = 46 }
      name          = "U/I Mechanized Infantry Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id       = { type = 17000 id = 49 }
      name     = "U/I Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 52 }
    location = 1201
    name     = "III Army Corps"
    division =
    { id            = { type = 17000 id = 53 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 54 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 55 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 56 }
      name          = "U/I PMTU Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 57 }
      name          = "U/I PMTU Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 58 }
      name          = "U/I Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 3
    }
  }
  landunit =
  { id       = { type = 17000 id = 59 }
    location = 1201
    name     = "VII Army Corps"
    division =
    { id            = { type = 17000 id = 60 }
      name          = "10th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 61 }
      name          = "20th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 62 }
      name          = "U/I PMTU Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 63 }
      name          = "U/I PMTU Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 64 }
      name          = "U/I PMTU Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 17000 id = 65 }
      name     = "U/I PMTU Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id            = { type = 17000 id = 66 }
      name          = "U/I Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
      extra         = heavy_armor
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 17000 id = 67 }
    location = 1201
    name     = "XII Army Corps"
    division =
    { id            = { type = 17000 id = 68 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 69 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 70 }
      name          = "U/I Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
      extra         = heavy_armor
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 17000 id = 71 }
    location = 1392
    name     = "U/I Army Corps"
    division =
    { id            = { type = 17000 id = 72 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 73 }
      name          = "U/I PMTU Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 74 }
      name          = "U/I PMTU Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 75 }
    location = 1392
    name     = "Pyongyang Defense Command"
    division =
    { id            = { type = 17000 id = 77 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 17000 id = 80 }
      name     = "KPA HQ"
      strength = 100
      type     = hq
      model    = 0
      extra         = sp_rct_artillery
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 17000 id = 81 }
    location = 1201
    name     = "VIII Army Corps"
    division =
    { id            = { type = 17000 id = 82 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 17000 id = 84 }
      name     = "U/I PMTU Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id            = { type = 17000 id = 85 }
      name          = "U/I Armored Brigade"
      strength      = 30
      type          = light_armor
      model         = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 86 }
    location = 1392
    name     = "IX Army Corps"
    division =
    { id            = { type = 17000 id = 87 }
      name          = "24th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 17000 id = 88 }
      name          = "42nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 17000 id = 89 }
      name     = "U/I PMTU Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 90 }
    location = 1392
    name     = "X Army Corps"
    division =
    { id            = { type = 17000 id = 91 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 17000 id = 92 }
      name     = "U/I PMTU Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 93 }
    location = 1201
    name     = "XI Army Corps"
    division =
    { id            = { type = 17000 id = 94 }
      name          = "U/I Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id       = { type = 17000 id = 95 }
      name     = "U/I PMTU Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 17000 id = 96 }
    location = 1392
    name     = "108th Mechanized Corps"
    division =
    { id            = { type = 17000 id = 97 }
      name          = "U/I Mechanized Infantry Division"
      strength      = 100
      type          = infantry
      model         = 1
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id            = { type = 17000 id = 100 }
      name          = "U/I Mechanized Infantry Division"
      strength      = 100
      type          = infantry
      model         = 1
      extra         = heavy_armor
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 17000 id = 103 }
    location = 1201
    name     = "425th Mechanized Corps"
    division =
    { id            = { type = 17000 id = 104 }
      name          = "U/I Mechanized Infantry Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 17000 id = 106 }
      name          = "U/I Mechanized Infantry Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id       = { type = 17000 id = 107 }
      name     = "2nd KPA HQ"
      strength = 100
      type     = hq
      model    = 0
      extra         = sp_rct_artillery
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 17000 id = 108 }
    location = 1201
    name     = "Sniper Combat Command"
    division =
    { id            = { type = 17000 id = 109 }
      name          = "4th Sniper Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 110 }
      name          = "11th Sniper Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 111 }
      name          = "2nd Sniper Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 112 }
      name          = "7th Sniper Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 113 }
      name          = "3rd Sniper Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 114 }
      name          = "18th Sniper Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
  }
  landunit =
  { id       = { type = 17000 id = 115 }
    location = 1201
    name     = "Special Forces Command"
    division =
    { id            = { type = 17000 id = 116 }
      name          = "1st Light Infantry Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id            = { type = 17000 id = 117 }
      name          = "3rd Light Infantry Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id            = { type = 17000 id = 118 }
      name          = "5th Light Infantry Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 119 }
      name          = "23rd Light Infantry Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 120 }
      name          = "22nd Light Infantry Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 121 }
      name          = "10th Light Infantry Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 122 }
      name          = "7th Light Infantry Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 123 }
      name          = "9th Light Infantry Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 17000 id = 124 }
      name          = "33rd Light Infantry Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 17000 id = 300 }
    location = 1392
    base     = 1392
    name     = "1st Fleet"
    division =
    { id    = { type = 17000 id = 301 }
      name  = "KPAN Najin"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 17000 id = 303 }
      name  = "KPAN Soho"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 17000 id = 305 }
      name  = "KPAN Pyongyang"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 17000 id = 306 }
    location = 1392
    base     = 1392
    name     = "1st Submarine Fleet"
    division =
    { id    = { type = 17000 id = 307 }
      name  = "KPAN SS-001"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 308 }
      name  = "KPAN SS-003"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 309 }
      name  = "KPAN SS-005"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 310 }
      name  = "KPAN SS-007"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 311 }
      name  = "KPAN SS-009"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 312 }
      name  = "KPAN SS-011"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 313 }
      name  = "KPAN SS-013"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 314 }
      name  = "KPAN SS-015"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 315 }
      name  = "KPAN SS-017"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 316 }
      name  = "KPAN SS-019"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 317 }
      name  = "KPAN SS-021"
      type  = submarine
      model = 0
    }
  }
  navalunit =
  { id       = { type = 17000 id = 318 }
    location = 1392
    base     = 1392
    name     = "2nd Submarine Fleet"
    division =
    { id    = { type = 17000 id = 319 }
      name  = "KPAN SS-002"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 320 }
      name  = "KPAN SS-004"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 321 }
      name  = "KPAN SS-006"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 322 }
      name  = "KPAN SS-008"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 323 }
      name  = "KPAN SS-010"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 324 }
      name  = "KPAN SS-012"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 325 }
      name  = "KPAN SS-014"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 326 }
      name  = "KPAN SS-016"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 327 }
      name  = "KPAN SS-018"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 328 }
      name  = "KPAN SS-020"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 17000 id = 329 }
      name  = "KPAN SS-022"
      type  = submarine
      model = 0
    }
  }
  navalunit =
  { id       = { type = 17000 id = 330 }
    location = 1392
    base     = 1392
    name     = "Transport Fleet"
    division =
    { id    = { type = 17000 id = 331 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 17000 id = 332 }
      name  = "2nd Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 17000 id = 200 }
    location = 1392
    base     = 1392
    name     = "1st Air Combat Division"
    division =
    { id       = { type = 17000 id = 201 }
      name     = "35th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 17000 id = 202 }
      name     = "37th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 17000 id = 203 }
      name     = "60th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 17000 id = 204 }
    location = 1392
    base     = 1392
    name     = "4th Air Combat Division"
    division =
    { id       = { type = 17000 id = 205 }
      name     = "55th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 17000 id = 206 }
      name     = "24th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 17000 id = 207 }
      name     = "71st Air Regiment"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 17000 id = 208 }
    location = 1392
    base     = 1392
    name     = "3rd Air Combat Division"
    division =
    { id       = { type = 17000 id = 209 }
      name     = "44th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 17000 id = 210 }
      name     = "41st Air Regiment"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 17000 id = 211 }
      name     = "76th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 17000 id = 212 }
    location = 1392
    base     = 1392
    name     = "2nd Air Combat Division"
    division =
    { id       = { type = 17000 id = 213 }
      name     = "11th Air Strike Regiment"
      type     = tactical_bomber
      strength = 75
      model    = 1
    }
    division =
    { id       = { type = 17000 id = 214 }
      name     = "39th Air Regiment"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 17000 id = 215 }
      name     = "62nd Air Regiment"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 17000 id = 216 }
    location = 1201
    base     = 1201
    name     = "8th Air Combat Division"
    division =
    { id       = { type = 17000 id = 217 }
      name     = "4th Air Regiment"
      type     = interceptor
      strength = 70
      model    = 2
    }
    division =
    { id       = { type = 17000 id = 218 }
      name     = "86th Air Regiment"
      type     = interceptor
      strength = 70
      model    = 2
    }
    division =
    { id       = { type = 17000 id = 219 }
      name     = "7th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 17000 id = 220 }
    location = 1201
    base     = 1201
    name     = "22nd Air Combat Division"
    division =
    { id       = { type = 17000 id = 221 }
      name     = "8th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 17000 id = 222 }
      name     = "94th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 17000 id = 223 }
      name     = "97th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 17000 id = 224 }
    location = 1201
    base     = 1201
    name     = "13th Air Combat Division"
    division =
    { id       = { type = 17000 id = 225 }
      name     = "43rd Air Regiment"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 17000 id = 226 }
      name     = "19th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 17000 id = 227 }
      name     = "15th Air Regiment"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 17000 id = 228 }
    location = 1201
    base     = 1201
    name     = "10th Air Combat Division"
    division =
    { id       = { type = 17000 id = 229 }
      name     = "4th Ground Attack Regiment"
      type     = cas
      strength = 70
      model    = 0
    }
    division =
    { id       = { type = 17000 id = 230 }
      name     = "6th Ground Attack Regiment"
      type     = cas
      strength = 70
      model    = 0
    }
  }
}
