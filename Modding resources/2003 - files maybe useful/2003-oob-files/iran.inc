
##############################
# Country definition for PER #
##############################

province =
{ id         = 1497
  naval_base = { size = 6 current_size = 6 }
}              # Bandar Abbas

province =
{ id         = 1826
    air_base = { size = 8 current_size = 8 }
}              # Esfahan

province =
{ id         = 1500
    air_base = { size = 4 current_size = 4 }
}              # Mashhad

province =
{ id         = 1498
      nuclear_reactor = 4
}            # Babolsar

country =
{ tag                 = PER
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 400
  capital             = 1502
  manpower            = 120
  transports          = 90
  escorts             = 0
  diplomacy           = { 
relation = { tag = USA value = -150 }
relation = { tag = ISR value = -200 }
relation = { tag = SYR value = 200 }
relation = { tag = VEN value = 150 }
relation = { tag = PAK value = 100 }
relation = { tag = U09 value = 100 }
relation = { tag = SUD value = 150 }
relation = { tag = U14 value = 100 }
relation = { tag = QUE value = 100 }
relation = { tag = U13 value = 120 }
relation = { tag = SAU value = -80 }
relation = { tag = IRQ value = -120 }
relation = { tag = U16 value = -50 }
relation = { tag = MLY value = 80 }
relation = { tag = INO value = 50 }
relation = { tag = IND value = 50 }
relation = { tag = LBY value = 120 }
}
  SpyInfo                = { country = "ISR" NumberOfSpies = 2 }
  SpyInfo                = { country = "PAK" NumberOfSpies = 2 }
  SpyInfo                = { country = "SAU" NumberOfSpies = 2 }
  SpyInfo                = { country = "LEB" NumberOfSpies = 3 }
  nationalprovinces   = { 1859 1787 1503 1502 1788 1789 1825 1498 1497 1499 1826 1501 1500 1496 1495 }
  ownedprovinces      = { 1859 1787 1503 1502 1788 1789 1825 1498 1497 1499 1826 1501 1500 1496 1495 }
  controlledprovinces = { 1859 1787 1503 1502 1788 1789 1825 1498 1497 1499 1826 1501 1500 1496 1495 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090 
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
					2200 2210 2220
					2600 2610 2620
					2800 2810 2820
					2700 2710 2720
					2300 2310
					2400 2410
					2500 2510
					2000 2010
					2050 2060
					#Army Org
					1960 1970
					1900 1910
					1260
					1800
                                        1000 1050
                                        1010 1060
					1500 1510
					1200 1210
					1300 1310
					1400 1410
					1700
					#Aircraft
                                        4700 4710
                                        4750 4760
                                        4800 4810
                                        4900
                                        4640 4650
                                        4400
                                        4550
                                        4000 4010 4020
                                        4100 4110 4120
					#Land Docs
					6010 6030 6040
					6930
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
					6200 6130 6260
					#Air Docs
					9010 9510
                                        9050 9130 9060 9070
                                        9090
                                        9100
                                        9110
                                        9120
					#Secret Weapons
					7010
                                        7330 7310
                                        7240
                                        7100
                                        #Navy Techs
                                        3000
                                        3100
                                        3700 3710 3720
                                        3590
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8400 8410
                                        8000 8010
                                        8500 8510
                                        8100
                                        8600
										
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 6
    political_left    = 2
    free_market       = 6
    freedom           = 2
    professional_army = 4
    defense_lobby     = 5
    interventionism   = 7
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12500 id = 1 }
    location = 1502
    name     = "I Artesh-ye Iran"
    division =
    { id       = { type = 12500 id = 2 }
      name     = "28th Mechanized Infantry Division"
      strength = 100
      type     = infantry
      model    = 2
    }
    division =
    { id            = { type = 12500 id = 3 }
      name          = "30th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12500 id = 4 }
      name          = "77th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12500 id = 5 }
    location = 1826
    name     = "II Artesh-ye Iran"
    division =
    { id       = { type = 12500 id = 6 }
      name     = "16th Armored Division"
      strength = 100
      type     = armor
      model    = 12
    }
    division =
    { id            = { type = 12500 id = 7 }
      name          = "81st Armored Division"
      strength      = 100
      type          = armor
      model         = 8
    }
    division =
    { id            = { type = 12500 id = 8 }
      name          = "84th Mechanized Infantry Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 12500 id = 9 }
      name          = "58th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12500 id = 10 }
    location = 1825
    name     = "23-Lashgare Takavar"
    division =
    { experience    = 5
      id       = { type = 12500 id = 11 }
      name     = "1st Brigade - 23rd Special Forces Division"
      strength = 100
      type     = bergsjaeger
      model    = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 5
      id       = { type = 12500 id = 12 }
      name     = "2nd Brigade - 23rd Special Forces Division"
      strength = 100
      type     = bergsjaeger
      model    = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 5
      id       = { type = 12500 id = 13 }
      name     = "3rd Brigade - 23rd Special Forces Division"
      strength = 100
      type     = bergsjaeger
      model    = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 12500 id = 61 }
    location = 1825
    name     = "65-Lashgare Takavar"
    division =
    { experience    = 5
      id       = { type = 12500 id = 62 }
      name     = "65th Airborne Special Forces Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 12500 id = 14 }
    location = 1498
    name     = "III Artesh-ye Iran"
    division =
    { id            = { type = 12500 id = 15 }
      name          = "88th Armored Division"
      strength      = 100
      type          = armor
      model         = 8
    }
    division =
    { id            = { type = 12500 id = 16 }
      name          = "40th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12500 id = 17 }
      name          = "64th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  # ##################################
  # Pasdaran - Revolutionary Guards
  # ##################################
  landunit =
  { id       = { type = 12500 id = 18 }
    location = 1500
    name     = "1st Pasdaran Airborne Corps"
    division =
    { id            = { type = 12500 id = 19 }
      name          = "55th IRGC Parachute Brigade"
      strength      = 100
      type          = paratrooper
      model         = 15
    }
  }
  landunit =
  { id       = { type = 12500 id = 20 }
    location = 1498
    name     = "Pasdaran Southern Operations Sector"
    division =
    { id            = { type = 12500 id = 21 }
      name          = "40th IRGC Armored Division"
      strength      = 100
      type          = armor
      model         = 7
    }
    division =
    { id            = { type = 12500 id = 22 }
      name          = "5th IRGC Mechanized Infantry Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id       = { type = 12500 id = 23 }
      name     = "3rd IRGC Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 12500 id = 24 }
      name     = "7th IRGC Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 12500 id = 25 }
      name     = "14th IRGC Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { experience    = 5
      id       = { type = 12500 id = 31 }
      name     = "45th Quds IRGC Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
    division =
    { experience    = 5
      id       = { type = 12500 id = 32 }
      name     = "25th Quds IRGC Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
  }
  landunit =
  { id       = { type = 12500 id = 33 }
    location = 1859
    name     = "Pasdaran Northern Op. Sector"
    division =
    { id       = { type = 12500 id = 34 }
      name     = "6th IRGC Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 12500 id = 38 }
      name     = "411th IRGC Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 12500 id = 39 }
      name     = "55th IRGC Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 12500 id = 40 }
    location = 1789
    name     = "Pasdaran Western Operations Sector"
    division =
    { id            = { type = 12500 id = 42 }
      name          = "17th IRGC Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12500 id = 45 }
      name     = "44th IRGC Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 12500 id = 46 }
      name     = "57th IRGC Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 12500 id = 47 }
    location = 1789
    name     = "Pasdaran Quds Force Corps"
    division =
    { experience    = 5
      id            = { type = 12500 id = 48 }
      name          = "35th Quds IRGC Commando Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { experience    = 5
      id            = { type = 12500 id = 49 }
      name          = "58th Quds IRGC Commando Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
  }
  landunit =
  { id       = { type = 12500 id = 50 }
    location = 1825
    name     = "1st Pasdaran Airmobile Corps"
    division =
    { id            = { type = 12500 id = 51 }
      name          = "29th IRGC Airmobile Brigade"
      strength      = 100
      type          = militia
      model         = 1      
    }
  }
  landunit =
  { id       = { type = 12500 id = 52 }
    location = 1496
    name     = "Pasdaran Eastern Operations Sector"
    division =
    { id            = { type = 12500 id = 53 }
      name          = "30th IRGC Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id       = { type = 12500 id = 54 }
      name     = "15th IRGC Mechanized Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
    division =
    { id            = { type = 12500 id = 55 }
      name          = "8th IRGC Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12500 id = 56 }
      name          = "25th IRGC Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12500 id = 57 }
      name          = "28th IRGC Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 12500 id = 200 }
    location = 1497
    base     = 1497
    name     = "Iranian Navy"
    division =
    { id    = { type = 12500 id = 201 }
      name  = "Alvand"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12500 id = 202 }
      name  = "Alborz"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12500 id = 203 }
      name  = "Sabalan"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12500 id = 206 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12500 id = 207 }
      name  = "2nd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 12500 id = 214 }
    location = 1497
    base     = 1497
    name     = "Submarine Fleet"
    division =
    { id    = { type = 12500 id = 215 }
      name  = "Tareq"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12500 id = 216 }
      name  = "Noor"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12500 id = 217 }
      name  = "Yunes"
      type  = submarine
      model = 4
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 12500 id = 100 }
    location = 1500
    base     = 1500
    name     = "1st Figther Wing"
    division =
    { id       = { type = 12500 id = 101 }
      name     = "11th Tactical Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12500 id = 102 }
      name     = "41st Tactical Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12500 id = 103 }
      name     = "31st Tactical Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 12500 id = 104 }
    location = 1500
    base     = 1500
    name     = "1st Ground Attack Wing"
    division =
    { id       = { type = 12500 id = 105 }
      name     = "2nd Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 12500 id = 106 }
      name     = "14th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 12500 id = 107 }
    location = 1826
    base     = 1826
    name     = "2nd Figther Wing"
    division =
    { id       = { type = 12500 id = 108 }
      name     = "21st Tactical Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 12500 id = 109 }
      name     = "32nd Tactical Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 12500 id = 110 }
      name     = "51st Tactical Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 12500 id = 111 }
    location = 1826
    base     = 1826
    name     = "3rd Figther Wing"
    division =
    { id       = { type = 12500 id = 112 }
      name     = "19th Tactical Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12500 id = 113 }
      name     = "23rd Tactical Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12500 id = 114 }
      name     = "44th Tactical Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 12500 id = 115 }
    location = 1500
    base     = 1500
    name     = "Air Transport Command"
    division =
    { id       = { type = 12500 id = 116 }
      name     = "1st Military Transport Squadron"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { type          = light_armor
    model         = 4
    date          = { day = 14 month = november year = 2003 }
    cost          = 10
    days          = 95
    id            = { type = 12500 id = 63 }
    name          = "11th IRGC Armored Brigade"
  }
}
