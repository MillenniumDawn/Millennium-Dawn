
##############################
# Country definition for SCH #
##############################

country =
{ tag                 = SCH
  regular_id          = U06
  capital             = 532
  manpower            = 40
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 25
  diplomacy           = { }
  nationalprovinces   = { 532 530 533 372 }
  ownedprovinces      = { 532 530 533 372 }
  controlledprovinces = { 532 530 533 372 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
					2800 2810 2820 2830
					2600 2610 2620 2630
					2700 2710 2720 2730
					2500 2510 2520 2530
					2300 2310 2320 2330
					2400 2410 2420 2430
                                        2000 2050 2110
                                        2010 2060 2120
                                             2070
					#Army Org
					1960
					1260 1270
					1900 1910 1920 1930
					1800 1810 1820
					1110 1120
					1500 1510 1520 1530
					1400 1410 1420 1430
					1300 1310 1320 1330
                                        1000 1050 1110
                                        1010 1060 1120
                                             1070
					#Aircraft
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4900 4910 4920
                                        4000 4010 4020 4030
                                        4640 4650 4660
					#Land Docs
					6930
					6010 6020
					6600 6610
					6700 6710
					6100 6110 6120 6140 6160 6170
					6200 6210 6220 6240 6260 6270
					6300 6310 6320 6340 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9120
					9130 9140 9150 9200
					#Secret Weapons
					7010 7060 7070 7080
                                        7330 7310 7320
					
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 5
    free_market       = 8
    freedom           = 10
    professional_army = 1
    defense_lobby     = 2
    interventionism   = 1
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12231 id = 1 }
    location = 532
    name     = "Swiss Army"
    division =
    { id            = { type = 12231 id = 2 }
      name          = "1st Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 8
    }
    division =
    { id            = { type = 12231 id = 3 }
      name          = "11th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 8
    }
    division =
    { id            = { type = 12231 id = 4 }
      name          = "2nd Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 12231 id = 5 }
      name          = "4th Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 12231 id = 6 }
      name          = "5th Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 12231 id = 7 }
      name          = "7th Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 12231 id = 8 }
      name          = "9th Infantry Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
  }
  landunit =
  { id       = { type = 12231 id = 9 }
    location = 533
    name     = "Swiss Mountain Corps"
    division =
    { id            = { type = 12231 id = 10 }
      name          = "9th Mountain Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
    }
    division =
    { id            = { type = 12231 id = 11 }
      name          = "10th Mountain Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
    }
    division =
    { id            = { type = 12231 id = 12 }
      name          = "12th Mountain Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
    }
  }
}
