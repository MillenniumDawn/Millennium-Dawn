
##############################
# Country definition for SLO #
##############################

province =
{ id       = 477
  air_base = { size = 2 current_size = 2 }
}            # Banska Bystrica

country =
{ tag                 = SLO
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 20
  manpower            = 10
  capital             = 476
  # NATO
  diplomacy =
  { relation = { tag = BEL value = 200 access = yes }
    relation = { tag = BUL value = 200 access = yes }
    relation = { tag = CAN value = 200 access = yes }
    relation = { tag = CZE value = 200 access = yes }
    relation = { tag = DEN value = 200 access = yes }
    relation = { tag = EST value = 200 access = yes }
    relation = { tag = FRA value = 200 access = yes }
    relation = { tag = GER value = 200 access = yes }
    relation = { tag = GRE value = 200 access = yes }
    relation = { tag = HUN value = 200 access = yes }
    relation = { tag = ICL value = 200 access = yes }
    relation = { tag = ITA value = 200 access = yes }
    relation = { tag = LAT value = 200 access = yes }
    relation = { tag = LIT value = 200 access = yes }
    relation = { tag = LUX value = 200 access = yes }
    relation = { tag = HOL value = 200 access = yes }
    relation = { tag = NOR value = 200 access = yes }
    relation = { tag = POL value = 200 access = yes }
    relation = { tag = POR value = 200 access = yes }
    relation = { tag = ROM value = 200 access = yes }
    relation = { tag = USA value = 150 access = yes }
    relation = { tag = SLV value = 200 access = yes }
    relation = { tag = SPA value = 200 access = yes }
    relation = { tag = TUR value = 200 access = yes }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 478 477 490 476 }
  ownedprovinces      = { 478 477 490 476 }
  controlledprovinces = { 478 477 490 476 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
					2200 2210
					2300 2310
					2400 2410
					2500 2510
					2600 2610
					2700 2710
					2800 2810
                                        2000 2050
                                        2010 2060
                                             2070
					#Army Org
					1260
					1900 1910
					1500 1510
					1400 1410
					1300 1310
					1200 1210
					1800
                                        1000 1050
                                        1010 1060
                                             1070
					#Aircraft
					4800 4810
					4700 4710
					4750 4760
					4900 4910
                                        4000 4010 4020
                                        4400 4410
                                        4640 4650
					#Land Docs
					6910 6920
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170 6140 6150
					6200 6210 6220 6260 6270 6240 6250
					#Air Docs
					9030 9510 9520 9530
					9050 9060 9070 9120
					9130 9140 9150 9200
					#Secret Weapons
					7010 7060 7070
                                        7330 7310
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 5
    free_market       = 7
    freedom           = 8
    professional_army = 5
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 19500 id = 1 }
    location = 476
    name     = "I Corps"
    division =
    { id            = { type = 19500 id = 2 }
      name          = "1st Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 19500 id = 3 }
      name          = "2nd Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { experience    = 10
      id            = { type = 19500 id = 4 }
      name          = "5th Special Forces Regiment"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 19500 id = 200 }
    location = 477
    base     = 477
    name     = "1st Wing"
    division =
    { id       = { type = 19500 id = 201 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 50
      model    = 1
    }
    division =
    { id       = { type = 19500 id = 202 }
      name     = "2nd Squadron"
      type     = interceptor
      strength = 30
      model    = 2
    }
  }
}
