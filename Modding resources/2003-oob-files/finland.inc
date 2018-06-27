
##############################
# Country definition for FIN #
##############################

province =
{ id         = 141
  naval_base = { size = 2 current_size = 2 }
}              # Turku

province =
{ id         = 147
  air_base = { size = 4 current_size = 4 }
}              # Turku

country =
{ tag                 = FIN
  regular_id          = U06
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  capital             = 142
  manpower            = 21
  transports          = 30
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 103 141 142 140 143 138 139 137 131 130 136 148 147 144 149 }
  ownedprovinces      = { 103 141 142 140 143 138 139 137 131 130 136 148 147 144 149 }
  controlledprovinces = { 103 141 142 140 143 138 139 137 131 130 136 148 147 144 149 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220
					2400 2410 2420
					2500 2510 2520
					2600 2610 2620
					2700 2710 2720
					2800 2810 2820
					#Army Org
					1990
					1900 1910 1920
					1300 1310 1320
					1260
					#Aircraft
					4900 4910
					4800 4810
					4700 4710
					4750 4760
                                        4100 4110 4120 4130
                                        4400 4410
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
					6200 6210 6220 6260 6270
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9120
					9130 9140 9150 9200
					#Secret Weapons
					7010 7060 7070 7080
					7310 7320 7330
                                        #Navy Techs
                                        3000
                                        3590
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8000 8010
                                        8500

                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 6
    free_market       = 8
    freedom           = 9
    professional_army = 3
    defense_lobby     = 2
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 10500 id = 1 }
    location = 140
    name     = "Läntinen Maanpuolustusalue"
    division =
    { id            = { type = 10500 id = 2 }
      name          = "Porin Prikaati"
      strength      = 100
      type          = cavalry
      model         = 2
    }
    division =
    { id            = { type = 10500 id = 3 }
      name          = "1. Panssariprikaati"
      strength      = 100
      type          = light_armor
      model         = 8
  }
  landunit =
  { id       = { type = 10500 id = 4 }
    location = 137
    name     = "Pohjoinen Maanpuolustusalue"
    division =
    { id            = { type = 10500 id = 5 }
      name          = "'Kainu' Prikaati"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
    division =
    { id            = { type = 10500 id = 6 }
      name          = "Jaeger Prikaati"
      strength      = 70
      type          = bergsjaeger
      model         = 13
    }
  }
  landunit =
  { id       = { type = 10500 id = 7 }
    location = 144
    name     = "Karjalan Maanpuolustusalue"
    division =
    { id            = { type = 10500 id = 8 }
      name          = "Karjalan Prikaati"
      strength      = 30
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 10500 id = 9 }
      name          = "Pohjois-Karjalan Prikaati"
      strength      = 50
      type          = bergsjaeger
      model         = 12
    }
  }
  landunit =
  { id       = { type = 10500 id = 10 }
    location = 142
    name     = "Itäinen Maanpuolustusalue"
    division =
    { experience    = 10
      id            = { type = 10500 id = 11 }
      name          = "'Utti' Jaeger Prikaati"
      strength      = 30
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 10500 id = 100 }
    location = 147
    base     = 147
    name     = "Karjalan Lennosto"
    division =
    { id       = { type = 10500 id = 101 }
      name     = "1. Lentue"
      type     = interceptor
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 10500 id = 103 }
      name     = "2. Lentue"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
  # #####################################
  # UNDER DEVELOPMENT
  # #####################################
  division_development =
  { id    = { type = 10500 id = 300 }
    name  = "FNS Hanko"
    type  = destroyer
    model = 2
    cost  = 3
    date  = { day = 22 month = june year = 2005 }
  }
  division_development =
  { id    = { type = 10500 id = 301 }
    name  = "FNS Porvoo"
    type  = destroyer
    model = 2
    cost  = 3
    date  = { day = 24 month = june year = 2006 }
  }
}

