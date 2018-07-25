
##############################
# Country definition for SLV #
##############################

country =
{ tag                 = SLV
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 30
  manpower            = 5
  capital             = 380
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
    relation = { tag = SLO value = 200 access = yes }
    relation = { tag = USA value = 150 access = yes }
    relation = { tag = SPA value = 200 access = yes }
    relation = { tag = TUR value = 200 access = yes }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 380 1169 1173 }
  ownedprovinces      = { 380 1169 1173 }
  controlledprovinces = { 380 1169 1173 }
  techapps            = {
                                        #Industry:
                                        5010 5110
                                        5020 5120
                                        5030 5130
                                        5040 5140
                                        5050 5150
                                        5060 5160
                                        5070 5170
                                        5080 5180
                                        5090 5190
					5210 5220
                                        #Army Equipment:
                                        2000 2050
                                        2010 2060
                                             2070
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
                                        #Army Organisation:
                                        1000 1050
                                        1010 1060
                                        1500 1510 1520
                                        1300 1310 1320
                                        1400 1410 1420
                                        1900 1910 1920
                                        1260 1270
                                        1960
                                        #Army Doctrines:
                                        6100 6200
                                        6110 6210
                                        6120 6220
                                        6160 6260
                                        6010
                                        6020
                                        6910
                                        6600
                                        6610
					#Secret Weapons
					7010 7060 7070 7080
					7180
                                        #Air Force
                                        4000 4010
                                        4700
                                        4750
					#Air Docs
					9020 9510 9520
					9050 9060 9070 9090 9120
                                        #Navy Techs
                                        3000 3010
                                        3700 37700
                                        3590
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
    democratic        = 10
    political_left    = 5
    free_market       = 8
    freedom           = 9
    professional_army = 9
    defense_lobby     = 3
    interventionism   = 7
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12229 id = 1 }
    location = 380
    name     = "Slovenska vojska"
    division =
    { id            = { type = 12229 id = 2 }
      name          = "1. Brigada"
      strength      = 70
      type          = mechanized
      model         = 2
    }
    division =
    { id            = { type = 12229 id = 3 }
      name          = "72. Brigada"
      strength      = 70
      type          = cavalry
      model         = 2
     
    }
  }
}