
##############################
# Country definition for NOR #
##############################

province =
{ id       = 110
  naval_base = { size = 6 current_size = 6 }
}            # Haakonsvern - Bergen

province =
{ id         = 124
  air_base = { size = 4 current_size = 4 }
}              # Bodø - Mo i Rana

country =
{ tag                 = NOR
  regular_id          = U06
  energy              = 1000
  metal               = 500
  rare_materials      = 500
  oil                 = 1500
  supplies            = 500
  money               = 500
  manpower            = 10
  transports          = 100
  escorts             = 10
  capital             = 107
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
    relation = { tag = USA value = 150 access = yes }
    relation = { tag = POL value = 200 access = yes }
    relation = { tag = POR value = 200 access = yes }
    relation = { tag = ROM value = 200 access = yes }
    relation = { tag = SLO value = 200 access = yes }
    relation = { tag = SLV value = 200 access = yes }
    relation = { tag = SPA value = 200 access = yes }
    relation = { tag = TUR value = 200 access = yes }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 107 108 109 110 111 116 117 118 124 125 128 129
}
  ownedprovinces      = { 107 108 109 110 111 116 117 118 124 125 128 129 }
  controlledprovinces = { 107 108 109 110 111 116 117 118 124 125 128 129 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
                                        #Army Equip
                                        2000 2050 2110
                                        2010 2060 2120
                                             2070
                                        2300 2310 2320
                                        2400 2410 2420
                                        2500 2510 2520
                                        2700 2710 2720
					2200 2210 2220
					2600 2610 2620
					2800 2810 2820
					#Army Org
					1260 1270
                                        1300 1310 1320
                                        1500 1510 1520
                                             1800 1810
					1900 1910 1920
					1990
					#Aircraft
					4800 4810
					4700 4710
					4750 4760
                                        4000 4010 4020
                                        4640
                                        4400
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6160
					6200 6210 6220 6260
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9110 9120
					9130 9140 9150 9190 9200
					#Secret Weapons
					7180
                                        7330 7310 7320
                                        #Navy Techs
                                        3000 3010 3020 3030
                                        3700 37700 3710 3720
                                        3590
                                        3850 3860 3870 3880
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020
                                        8500 8510 8520
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 5
    free_market       = 7
    freedom           = 9
    professional_army = 3
    defense_lobby     = 3
    interventionism   = 7
  }
  # ####################################
  # ARMY
  # ####################################
  landunit =
  { id       = { type = 17100 id = 1 }
    location = 128
    name     = "Hæren"
    division =
    { id       = { type = 17100 id = 2 }
      name     = "6. Divisjonskommando"
      strength = 100
      type     = hq
      model    = 2
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id       = { type = 17100 id = 3 }
      name     = "Brigade Nord"
      strength = 100
      type     = cavalry
      model    = 2
    }
  }
  landunit =
  { id       = { type = 17100 id = 4 }
    location = 111
    name     = "Brigade Sør"
    division =
    { id       = { type = 17100 id = 5 }
      name     = "Brigade Sør"
      strength = 100
      type     = cavalry
      model    = 3
    }
  }
  # ####################################
  # NAVY
  # ####################################
  navalunit =
  { id       = { type = 17100 id = 200 }
    location = 110
    base     = 110
    name     = "Kgl. Norske Marine"
    division =
    { id    = { type = 17100 id = 201 }
      name  = "HNoMS Bergen"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 17100 id = 202 }
      name  = "HNoMS Narvik"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 17100 id = 203 }
      name  = "HNoMS Trondheim"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 17100 id = 204 }
    location = 110
    base     = 110
    name     = "1. Undervannseskadre"
    division =
    { id    = { type = 17100 id = 205 }
      name  = "HNoMS Ula"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 17100 id = 206 }
      name  = "HNoMS Utsira"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 17100 id = 207 }
      name  = "HNoMS Utstein"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 17100 id = 208 }
      name  = "HNoMS Utvær"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 17100 id = 209 }
      name  = "HNoMS Uthaug"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 17100 id = 210 }
      name  = "HNoMS Uredd"
      type  = submarine
      model = 4
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 17100 id = 100 }
    location = 124
    base     = 124
    name     = "Bodø Hovudflystasjon"
    division =
    { id       = { type = 17100 id = 101 }
      name     = "331-skvadronen"
      type     = interceptor
      strength = 80
      model    = 2
    }
    division =
    { id       = { type = 17100 id = 103 }
      name     = "332-skvadronen"
      type     = interceptor
      strength = 80
      model    = 2
    }
    division =
    { id       = { type = 17100 id = 104 }
      name     = "338-skvadronen"
      type     = interceptor
      strength = 80
      model    = 2
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 17100 id = 300 }
    name  = "HNoMS Fridtjof Nansen"
    type  = destroyer
    model = 3
    cost  = 4
    date  = { day = 12 month = august year = 2005 }
  }
  division_development =
  { id    = { type = 17100 id = 301 }
    name  = "HNoMS Roald Amundsen"
    type  = destroyer
    model = 3
    cost  = 4
    date  = { day = 12 month = august year = 2006 }
  }
  division_development =
  { id    = { type = 17100 id = 302 }
    name  = "HNoMS Otto Sverdrup"
    type  = destroyer
    model = 3
    cost  = 4
    date  = { day = 12 month = august year = 2007 }
  }
  division_development =
  { id    = { type = 17100 id = 303 }
    name  = "HNoMS Helge Ingstad"
    type  = destroyer
    model = 3
    cost  = 4
    date  = { day = 12 month = august year = 2008 }
  }
  division_development =
  { id    = { type = 17100 id = 304 }
    name  = "HNoMS Thor Heyerdahl"
    type  = destroyer
    model = 3
    cost  = 4
    date  = { day = 12 month = august year = 2009 }
  }
}
