
##############################
# Country definition for BEL #
##############################

province =
{ id         = 45
  naval_base = { size = 4 current_size = 4 }
}              # Ghent

province =
{ id         = 51
  air_base = { size = 4 current_size = 4 }
}              # Brussels


country =
{ tag                 = BEL
  regular_id          = U06
  capital             = 51
  manpower            = 10
  transports          = 53
  escorts             = 0
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  # NATO
  diplomacy =
  { relation = { tag = USA value = 100 }
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
    relation = { tag = SLV value = 200 access = yes }
    relation = { tag = SPA value = 200 access = yes }
    relation = { tag = TUR value = 200 access = yes }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 45 50 51 52 65 68 69 70 }
  ownedprovinces      = { 45 50 51 52 65 68 69 70 }
  controlledprovinces = { 45 50 51 52 65 68 69 70 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
                                        2300 2310 2320
                                        2400 2410 2420
					2800 2810 2820 2830
                                        2500 2510 2520 2530
                                        2700 2710 2720 2730
					2600 2610 2620 2630
                                        2000 2050 2110
                                        2010 2060 2120
                                             2070
					#Army Org
                                        1000 1050 1110
                                        1010 1060 1120
                                             1070
                                        1500 1510 1520
                                        1300 1310 1320
                                             1700 1710
                                             1800 1810
					1900 1910 1920 1930
					1260 1270
                                        1990
					#Aircraft
					4900 4910
					4800 4810
					4700 4710
					4750 4760
                                        4640 4650
                                        4400 4410
                                        4570
                                        4000 4010 4020
					#Land Docs
					6010 6020
					6930
					6600 6610 6700 6710
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					6300 6310 6320 6340 6350 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9090 9120
					9130 9140 9150 9170 9200
					9210 9220 9230 9250 9280
					#Secret Weapons
					7010 7060 7070 7080
					7310 7320 7330
                                        #Navy Techs
                                        3000 3010 3020
                                        3590
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8000 8010 8020
                                        8500 8510 8520
					
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 5
    free_market       = 7
    freedom           = 9
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 6400 id = 1 }
    location = 50
    name     = "I Corps"
    division =
    { id            = { type = 6400 id = 3 }
      name          = "Immediate Reaction Cell Command"
      strength      = 100
      type          = militia
      model         = 2
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 6400 id = 200 }
    location = 45
    base     = 45
    name     = "Royal Belgian Frigate Squadron"
    division =
    { id    = { type = 6400 id = 201 }
      name  = "BNS Wielingen"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 6400 id = 202 }
      name  = "BNS Westdiep"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 6400 id = 203 }
      name  = "BNS Wandelaar"
      type  = destroyer
      model = 1
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 6400 id = 100 }
    location = 51
    base     = 51
    name     = "1 Wing"
    division =
    { id       = { type = 6400 id = 101 }
      name     = "1 Escadron"
      type     = interceptor
      strength = 50
      model    = 2
    }
    division =
    { id       = { type = 6400 id = 103 }
      name     = "10 Escadron Tactique"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
 airunit =
  { id       = { type = 6400 id = 104 }
    location = 51
    base     = 51
    name     = "15 Wing de Transport Aérien"
    division =
    { id       = { type = 6400 id = 105 }
      name     = "15 Wing de Transport Aérien"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
}
