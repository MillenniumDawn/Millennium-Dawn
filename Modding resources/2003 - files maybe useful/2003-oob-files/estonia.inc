
##############################
# Country definition for EST #
##############################

province =
{ id       = 194
  naval_base = { size = 1 current_size = 1 }
}            # Tallin

country =
{ tag                 = EST
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 100
  manpower            = 6
  capital             = 194
  transports          = 43
  escorts             = 0
  # NATO
  diplomacy =
  { relation = { tag = BEL value = 200 access = yes }
    relation = { tag = BUL value = 200 access = yes }
    relation = { tag = CAN value = 200 access = yes }
    relation = { tag = CZE value = 200 access = yes }
    relation = { tag = DEN value = 200 access = yes }
    relation = { tag = USA value = 200 access = yes }
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
  nationalprovinces   = { 193 194 195 196 199 }
  ownedprovinces      = { 193 194 195 196 199 }
  controlledprovinces = { 193 194 195 196 199 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150      5170      5190
                                        #Army Equip:
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Org
                                        1300 1310 1320
                                        1260 1270
					1990
					1900 1910 1920
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9020
                                        9510 9520
					#Air Force
                                        4640
                                        4700
                                        4750
					#Land Docs
					6930 6010 6020
					6600 6610
					6100 6110 6160 6170
                                        6200 6210
					#Navy
                                        3000
                                        3850
                                        3590
					#Navy Docs
                                        8900
                                        8950
                                        8000
                                        8500
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 5
    free_market       = 8
    freedom           = 8
    professional_army = 6
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
    landunit =
  { id       = { type = 10000 id = 1 }
    location = 194
    name     = "Estonian Army"
    division =
    { id       = { type = 10000 id = 2 }
      name     = "1st Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 10000 id = 200 }
    location = 194
    base     = 194
    name     = "Estonian Navy"
    division =
    { id    = { type = 10000 id = 201 }
      name  = "EML Admiral Pitka"
      type  = destroyer
      model = 0
    }
  }
}
