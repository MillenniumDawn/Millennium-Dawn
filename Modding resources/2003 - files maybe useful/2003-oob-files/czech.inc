
##############################
# Country definition for CZE #
##############################

province =
{ id       = 469
  air_base = { size = 4 current_size = 4 }
}            # Prague

country =
{ tag                 = CZE
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 42
  capital             = 469
  # NATO
  diplomacy =
  { relation = { tag = BEL value = 200 access = yes }
    relation = { tag = BUL value = 200 access = yes }
    relation = { tag = CAN value = 200 access = yes }
    relation = { tag = USA value = 150 access = yes }
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
    relation = { tag = SLO value = 200 access = yes }
    relation = { tag = SLV value = 200 access = yes }
    relation = { tag = SPA value = 200 access = yes }
    relation = { tag = TUR value = 200 access = yes }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 471 472 466 467 470 469 468 474 475 }
  ownedprovinces      = { 471 472 466 467 470 469 468 474 475 }
  controlledprovinces = { 471 472 466 467 470 469 468 474 475 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
					2200 2210 2220
					2000 2010 2050 2060
					2400 2410 2420
					2300 2310 2430
					2500 2510 2520
					2600 2610 2620
					2800 2810 2820
					#Aircraft
					4800 4700 4750 4900
                                        4000 4010
                                        4400
                                        4640 4650
					#Army Org
					1000 1010 1050 1060
					1500 1510 1520
					1300 1310 1320
					1260
					1270
					1900 1910 1920 1960
					#Land Docs
					6100 6110 6120 6160
					6200 6210 6220 6260
					6910 6920
					6010 6020
					6600 6610
					#Air Docs
					9030 9510 9520 9530
					9050 9060 9070
					#Secret Weapons
					7010 7060 7070
					7310 7320 7330					
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 9
    free_market       = 7
    freedom           = 9
    professional_army = 10
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 8900 id = 1 }
    location = 475
    name     = "Ground Forces HQ"
    division =
    { id            = { type = 8900 id = 2 }
      name          = "4th Rapid Reaction Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 8900 id = 3 }
      name          = "7th Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 2
    }
  }
  landunit =
  { id       = { type = 8900 id = 4 }
    location = 467
    name     = "Territorial Defense Forces HQ"
    division =
    { id       = { type = 8900 id = 5 }
      name     = "21st Territorial Defense Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 8900 id = 100 }
    location = 469
    base     = 469
    name     = "22nd Wing"
    division =
    { id       = { type = 8900 id = 101 }
      name     = "22nd Squadron"
      type     = multi_role
      strength = 50
      model    = 1
    }
    division =
    { id       = { type = 8900 id = 103 }
      name     = "211th Squadron"
      type     = multi_role
      strength = 50
      model    = 1
    }
  }
}
