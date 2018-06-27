
##############################
# Country definition for LAT #
##############################

country =
{ tag                 = LAT
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 100
  capital             = 197
  manpower            = 3
  transports          = 10
  escorts             = 0
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
    relation = { tag = USA value = 200 access = yes }
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
  nationalprovinces   = { 205 204 203 197 202 198 }
  ownedprovinces      = { 205 204 203 197 202 198 }
  controlledprovinces = { 205 204 203 197 202 198 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
                                        #Army Equip:
                                        2000
                                        2010
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
                                        #Land Docs
					6010 6020 
					6910
					6100 6110 6120
                                        6160
					6600 6610
					#Army Org
                                        1000
                                        1010
                                        1500 1510
                                        1300 1310
					1260
					1990
					1900 1910
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 5
    free_market       = 7
    freedom           = 8
    professional_army = 8
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12225 id = 1 }
    location = 197
    name     = "Latvian Army"
    division =
    { id            = { type = 12225 id = 2 }
      name          = "1st Light Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12225 id = 3 }
      name          = "2nd Light Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12225 id = 4 }
      name          = "3rd Light Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 12225 id = 5 }
      name          = "4th Light Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
  }
}
