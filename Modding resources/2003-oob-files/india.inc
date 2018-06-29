
##############################
# Country definition for IND #
##############################

province =
{ id         = 1457
  naval_base = { size = 8 current_size = 8 }
  air_base = { size = 10 current_size = 10 }
}              # Calcutta

province =
{ id         = 1515
  naval_base = { size = 8 current_size = 8 }
  air_base = { size = 10 current_size = 10 }
}              # Madurai

province =
{ id         = 1465
  naval_base = { size = 6 current_size = 6 }
}              # Rajkot

province =
{ id       = 1469
  air_base = { size = 10 current_size = 10 }
}            # New Delhi

province =
{ id         = 1511
      nuclear_reactor = 6
}            # Bangalore


country =
{ tag                 = IND
  # Resource Reserves
  nuke                = 9
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 150
  manpower            = 1100
  capital             = 1469
  transports          = 180
  escorts             = 0
  diplomacy           = {
    relation = { tag = CAL value = 50 }
    relation = { tag = PAK value = -180 }
    relation =
    { tag        = NEP
      value      = 170
      access     = yes
      guaranteed = { day = 22 month = march year = 1003 }
    }
    relation = { tag = GER value = 100 }
    relation = { tag = FRA value = 100 }
    relation = { tag = ENG value = 100 }
    relation = { tag = ITA value = 100 }
    relation = { tag = SPA value = 100 }
    relation = { tag = MAD value = 120 access = yes }
    relation = { tag = MOZ value = 120 access = yes }
 }
  nationalprovinces   = { 1465 1466 1479 1476 1478 1477 1469 1470 1471 1472 1468 1467 1464 1463 1474 1460 1459 1457 1458 1461 1508 1462 1505 1506 1507
                          1509 1510 1511 1512 1513 1514 1515 1518 1519 1284 1287 1454 1878 1456 1455
                        }
  ownedprovinces      = { 1465 1466 1479 1476 1478 1477 1469 1470 1471 1472 1468 1467 1464 1463 1474 1460 1459 1457 1458 1461 1508 1462 1505 1506 1507
                          1509 1510 1511 1512 1513 1514 1515 1518 1519 1284 1287 1454 1878 1456 1455
                        }
  controlledprovinces = { 1465 1466 1479 1476 1478 1477 1469 1470 1471 1472 1468 1467 1464 1463 1474 1460 1459 1457 1458 1461 1508 1462 1505 1506 1507
                          1509 1510 1511 1512 1513 1514 1515 1518 1519 1284 1287 1454 1878 1456 1455
                        }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220
					2000 2010
					2050 2060
					2110
					2300 2310 2320
					2400 2410 2420
					2500 2510 2520
					2600 2610 2620
					2700 2710 2720
					2800 2810 2820
					#Army Org
					1000 1010 1050 1060
					1980
					1900 1910
					1260
					1800
					1500 1510
					1200 1210
					1300 1310
					1400 1410
					1700
					#Aircraft
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4900 4910
					4640
					4570
                                        4000 4010 4020
                                        4100 4110 4120 4130
                                        4400 4410
                                        4550
                                        4600 4610
					#Land Docs
					6930
					6010 6030 6040
					6600 6620
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					#Air Docs
					9020 9510 9520
					9450 9460
					9050 9060 9070 9090 9100 9110 9120
					9130 9140 9150 9170 9180 9190 9200
					#Secret Weapons
					7010
					7020 7030 7040 7050
					7060 7070
					7100 7110
					7180 7190 7200
                                        7330 7310
                                        #Navy Techs
                                        3000 3010 3020
                                        3100 3110
                                        3400
                                        3590 3600
                                        3700 37700 3710 37710 3720
                                        3800
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410
                                        8000 8010 8020
                                        8500 8510 8520
                                        8100 8110 8120
                                        8600 8610 8620
                                        8300 8310
                                        8800
                        }
	blueprints = { 1150 2150 3900 3810 3820 }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 10
    free_market       = 7
    freedom           = 7
    professional_army = 8
    defense_lobby     = 4
    interventionism   = 7
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12300 id = 1 }
    location = 1476
    name     = "Northern Command"
    division =
    { id       = { type = 12300 id = 2 }
      name     = "NORCOM"
      strength = 100
      type     = hq
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12300 id = 3 }
    location = 1474
    name     = "IX Corps"
    division =
    { id       = { type = 12300 id = 4 }
      name     = "26th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 12300 id = 5 }
      name     = "29th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 12300 id = 6 }
      name     = "2nd Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 4
    }
    division =
    { id       = { type = 12300 id = 7 }
      name     = "3rd Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 4
    }
    division =
    { id       = { type = 12300 id = 8 }
      name     = "4th Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 4
    }
  }
  landunit =
  { id       = { type = 12300 id = 9 }
    location = 1474
    name     = "XIV Corps"
    division =
    { id       = { type = 12300 id = 10 }
      name     = "3rd Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id            = { type = 12300 id = 11 }
      name          = "1st Brigade - 8th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
    division =
    { id            = { type = 12300 id = 12 }
      name          = "2nd Brigade - 8th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
    division =
    { id            = { type = 12300 id = 13 }
      name          = "3rd Brigade - 8th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
  }
  landunit =
  { id       = { type = 12300 id = 14 }
    location = 1474
    name     = "XV Corps"
    division =
    { id            = { type = 12300 id = 15 }
      name          = "19th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12300 id = 16 }
      name     = "28th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 12300 id = 17 }
    location = 1476
    name     = "XVI Corps"
    division =
    { id            = { type = 12300 id = 18 }
      name          = "10th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12300 id = 19 }
      name     = "25th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 12300 id = 20 }
      name     = "39th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 12300 id = 21 }
    location = 1478
    name     = "Western Command"
    division =
    { id       = { type = 12300 id = 22 }
      name     = "WESTCOM"
      strength = 100
      type     = hq
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12300 id = 23 }
    location = 1478
    name     = "II Corps"
    division =
    { id            = { type = 12300 id = 24 }
      name          = "14th Armor Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
    division =
    { id            = { type = 12300 id = 25 }
      name          = "1st Armored Division"
      strength      = 100
      type          = armor
      model         = 19
    }
    division =
    { id            = { type = 12300 id = 26 }
      name          = "14th RAPID Division"
      strength      = 100
      type          = infantry
      model         = 0
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 12300 id = 27 }
      name          = "22nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12300 id = 28 }
      name     = "U/I Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 29 }
      name     = "U/I Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12300 id = 30 }
    location = 1478
    name     = "X Corps"
    division =
    { id            = { type = 12300 id = 31 }
      name          = "6th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
    division =
    { id            = { type = 12300 id = 32 }
      name          = "24th RAPID Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 12300 id = 33 }
      name          = "18th RAPID Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 12300 id = 34 }
      name          = "16th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12300 id = 35 }
      name     = "U/I Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 36 }
      name     = "U/I Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12300 id = 37 }
    location = 1478
    name     = "XI Corps"
    division =
    { id            = { type = 12300 id = 38 }
      name          = "55th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
    division =
    { id            = { type = 12300 id = 39 }
      name          = "23rd Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
    division =
    { id            = { type = 12300 id = 40 }
      name          = "7th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12300 id = 41 }
      name          = "9th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12300 id = 42 }
      name          = "15th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id       = { type = 12300 id = 43 }
      name     = "U/I Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 44 }
      name     = "U/I Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12300 id = 45 }
    location = 1505
    name     = "Southern Command"
    division =
    { id       = { type = 12300 id = 46 }
      name     = "SOUTHCOM"
      strength = 100
      type     = hq
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 47 }
      name     = "50th Parachute Brigade"
      strength = 100
      type     = paratrooper
      model    = 15
    }
  }
  landunit =
  { id       = { type = 12300 id = 48 }
    location = 1479
    name     = "XII Corps"
    division =
    { id            = { type = 12300 id = 49 }
      name          = "340th Mechanized Brigade"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id       = { type = 12300 id = 50 }
      name     = "11th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id            = { type = 12300 id = 51 }
      name          = "12th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12300 id = 52 }
    location = 1466
    name     = "XXI Corps"
    division =
    { id            = { type = 12300 id = 53 }
      name          = "33rd Armored Division"
      strength      = 100
      type          = armor
      model         = 12
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id            = { type = 12300 id = 54 }
      name          = "36th RAPID Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
    division =
    { id            = { type = 12300 id = 55 }
      name          = "54th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12300 id = 56 }
    location = 1471
    name     = "Central Command"
    division =
    { id       = { type = 12300 id = 57 }
      name     = "CENTCOM"
      strength = 100
      type     = hq
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12300 id = 58 }
    location = 1472
    name     = "I Corps"
    division =
    { id            = { type = 12300 id = 59 }
      name          = "4th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12300 id = 60 }
      name          = "1st Brigade - 6th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
    division =
    { id            = { type = 12300 id = 61 }
      name          = "2nd Brigade - 6th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
    division =
    { id            = { type = 12300 id = 62 }
      name          = "3rd Brigade - 6th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
    division =
    { id            = { type = 12300 id = 63 }
      name          = "31st Armored Division"
      strength      = 100
      type          = armor
      model         = 12
      extra         = heavy_armor
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 12300 id = 64 }
    location = 1457
    name     = "Eastern Command"
    division =
    { id       = { type = 12300 id = 65 }
      name     = "EASTCOM"
      strength = 100
      type     = hq
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12300 id = 66 }
    location = 1284
    name     = "III Corps"
    division =
    { id            = { type = 12300 id = 67 }
      name          = "23rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12300 id = 68 }
      name          = "1st Brigade - 57th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 69 }
      name          = "2nd Brigade - 57th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 70 }
      name          = "3rd Brigade - 57th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
  }
  landunit =
  { id       = { type = 12300 id = 71 }
    location = 1284
    name     = "IV Corps"
    division =
    { id            = { type = 12300 id = 72 }
      name          = "1st Brigade - 2nd Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 73 }
      name          = "2nd Brigade - 2nd Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 74 }
      name          = "3rd Brigade - 2nd Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 75 }
      name          = "1st Brigade - 5th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 76 }
      name          = "2nd Brigade - 5th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 77 }
      name          = "3rd Brigade - 5th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 78 }
      name          = "1st Brigade - 21st Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 79 }
      name          = "2nd Brigade - 21st Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 80 }
      name          = "3rd Brigade - 21st Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
  }
  landunit =
  { id       = { type = 12300 id = 81 }
    location = 1456
    name     = "XXXIII Corps"
    division =
    { id            = { type = 12300 id = 82 }
      name          = "1st Brigade - 17th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 83 }
      name          = "2nd Brigade - 17th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 84 }
      name          = "3rd Brigade - 17th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 85 }
      name          = "1st Brigade - 20th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 86 }
      name          = "2nd Brigade - 20th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 87 }
      name          = "3rd Brigade - 20th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 88 }
      name          = "1st Brigade - 27th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 89 }
      name          = "2nd Brigade - 27th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12300 id = 90 }
      name          = "3rd Brigade - 27th Mtn Division"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 12300 id = 300 }
    location = 1465
    base     = 1465
    name     = "Western Fleet"
    division =
    { id    = { type = 12300 id = 301 }
      name  = "INS Viraat"
      type  = escort_carrier
      model = 0
    }
    division =
    { id    = { type = 12300 id = 302 }
      name  = "INS Mysore"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 12300 id = 303 }
      name  = "INS Mumbai"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 12300 id = 304 }
      name  = "INS Rajput"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 12300 id = 305 }
      name  = "INS Rana"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 12300 id = 306 }
      name  = "INS Ranvijay"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 12300 id = 307 }
      name  = "INS Talwar"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12300 id = 308 }
      name  = "INS Trishul"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12300 id = 309 }
      name  = "INS Brahmaputra"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12300 id = 310 }
      name  = "INS Beas"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12300 id = 311 }
      name  = "INS Gomati"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 12300 id = 330 }
    location = 1465
    base     = 1465
    name     = "Western Fleet Submarines"
    division =
    { id    = { type = 12300 id = 331 }
      name  = "INS Vagli"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 12300 id = 332 }
      name  = "INS Karanj"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 12300 id = 333 }
      name  = "INS Shankush"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 12300 id = 334 }
      name  = "INS Shalki"
      type  = submarine
      model = 2
    }
  }
  navalunit =
  { id       = { type = 12300 id = 335 }
    location = 1457
    base     = 1457
    name     = "Eastern Fleet"
    division =
    { id    = { type = 12300 id = 336 }
      name  = "INS Delhi"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 12300 id = 337 }
      name  = "INS Ranjit"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 12300 id = 338 }
      name  = "INS Ranvir"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 12300 id = 339 }
      name  = "INS Himgiri"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12300 id = 340 }
      name  = "INS Dunagiri"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12300 id = 341 }
      name  = "INS Vindhyagiri"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12300 id = 342 }
      name  = "INS Godavari"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 12300 id = 343 }
      name  = "INS Ganga"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 12300 id = 363 }
    location = 1457
    base     = 1457
    name     = "Eastern Fleet Transports"
    division =
    { id    = { type = 12300 id = 364 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12300 id = 365 }
      name  = "2nd Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12300 id = 366 }
      name  = "3rd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 12300 id = 374 }
    location = 1457
    base     = 1457
    name     = "Eastern Fleet Submarines"
    division =
    { id    = { type = 12300 id = 375 }
      name  = "INS Shankul"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 12300 id = 376 }
      name  = "INS Shishumar"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 12300 id = 377 }
      name  = "INS Sindhugosh"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 378 }
      name  = "INS Sindhudvaj"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 379 }
      name  = "INS Sindhuraj"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 380 }
      name  = "INS Sindhuvir"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 381 }
      name  = "INS Sindhuratma"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 382 }
      name  = "INS Sindhukesari"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 383 }
      name  = "INS Sindhukirti"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 384 }
      name  = "INS Sindhuvijay"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 385 }
      name  = "INS Sindhurajshak"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 386 }
      name  = "INS Sindhushastra"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 12300 id = 387 }
      name  = "INS Vela"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 12300 id = 388 }
      name  = "INS Vagir"
      type  = submarine
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 12300 id = 200 }
    location = 1515
    base     = 1515
    name     = "Central Air Command"
    division =
    { id       = { type = 12300 id = 201 }
      name     = "40th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 12300 id = 202 }
      name     = "11th Fighter Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 12300 id = 203 }
      name     = "18th Fighter Squadron"
      type     = multi_role
      strength = 80
      model    = 2
    }
  }
  airunit =
  { id       = { type = 12300 id = 204 }
    location = 1515
    base     = 1515
    name     = "40th Figther Wing"
    division =
    { id       = { type = 12300 id = 205 }
      name     = "66th Fighter Squadron"
      type     = multi_role
      strength = 80
      model    = 2
    }
    division =
    { id       = { type = 12300 id = 206 }
      name     = "22nd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 12300 id = 207 }
      name     = "37th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 12300 id = 208 }
    location = 1515
    base     = 1515
    name     = "20th Fighter Wing"
    division =
    { id       = { type = 12300 id = 209 }
      name     = "21st Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12300 id = 210 }
      name     = "14th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12300 id = 211 }
      name     = "16th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 12300 id = 212 }
    location = 1457
    base     = 1457
    name     = "Eastern Air Command 1"
    division =
    { id       = { type = 12300 id = 213 }
      name     = "29th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12300 id = 214 }
      name     = "2nd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12300 id = 215 }
      name     = "3rd Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 12300 id = 216 }
    location = 1457
    base     = 1457
    name     = "27th Ground Attack Wing"
    division =
    { id       = { type = 12300 id = 217 }
      name     = "33rd Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 218 }
      name     = "6th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 219 }
      name     = "8th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 220 }
      name     = "15th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 12300 id = 221 }
    location = 1469
    base     = 1469
    name     = "Western Air Command 1"
    division =
    { id       = { type = 12300 id = 222 }
      name     = "8th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12300 id = 223 }
      name     = "7th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12300 id = 224 }
      name     = "12th Fighter Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 12300 id = 225 }
    location = 1469
    base     = 1469
    name     = "Western Air Command 2"
    division =
    { id       = { type = 12300 id = 226 }
      name     = "19th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 227 }
      name     = "43rd Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 228 }
      name     = "55th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 12300 id = 229 }
      name     = "25th Ground Attack Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 12300 id = 230 }
    location = 1515
    base     = 1515
    name     = "Central Air Transport Command"
    division =
    { id       = { type = 12300 id = 231 }
      name     = "1st Air Transport Squadron"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 12300 id = 400 }
    name  = "INS Shivalik"
    type  = destroyer
    model = 2
    cost  = 5
    date  = { day = 29 month = august year = 2003 }
  }
  division_development =
  { id    = { type = 12300 id = 401 }
    name  = "INS Betwa"
    type  = destroyer
    model = 1
    cost  = 5
    date  = { day = 2 month = february year = 2006 }
  }
}
