
##############################
# Country definition for POL #
##############################

province =
{ id       = 303
  naval_base = { size = 2 current_size = 2 }
}            # Gdansk

province =
{ id       = 480
  air_base = { size = 4 current_size = 4 }
}            # Kielce

province =
{ id       = 306
  air_base = { size = 2 current_size = 2 }
}            # Bydgozcz

country =
{ tag                 = POL
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 100
  manpower            = 50
  transports          = 20
  escorts             = 0
  capital             = 485
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
    relation = { tag = USA value = 200 access = yes }
    relation = { tag = POR value = 200 access = yes }
    relation = { tag = ROM value = 200 access = yes }
    relation = { tag = SLO value = 200 access = yes }
    relation = { tag = SLV value = 200 access = yes }
    relation = { tag = SPA value = 200 access = yes }
    relation = { tag = TUR value = 200 access = yes }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 303 306 307 479 480 481 483 484 305 485 486 487 489 488 508 509 302 308 473 482 304 }
  ownedprovinces      = { 303 306 307 479 480 481 483 484 305 485 486 487 489 488 508 509 302 308 473 482 304 }
  controlledprovinces = { 303 306 307 479 480 481 483 484 305 485 486 487 489 488 508 509 302 308 473 482 304 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
					2300 2310 2320 2330
					2400 2410 2420 2430
					2500 2510 2520 2530
					2600 2610 2620 2630
					2700 2710 2720 2730
					2800 2810 2820 2830
					2000 2010
					2050 2060 2070
					#Army Org
					1990
					1260 1270
					1900 1910 1920
					1000 1010
					1050 1060 1070
					1500 1510 1520
					1200 1210 1220
					1300 1310 1320
					1400 1410 1420
					1800 1810 
					1700
					1600 
					#Aircraft
					4800 4810
					4700 4710
					4750 4760
					4640
                                        4000 4010 4020
                                        4640 4650
                                        4500
                                        4400 4410
					#Land Docs
					6930
					6600 6610
					6010 6020
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					6130
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9090 9120
					9130 9140 9150 9170 9200
					#Secret Weapons
					7010 7060 7070
                                        7330 7310
                                        #Navy Techs
                                        3000 3010
                                        3100
                                        3700 37700 3710 3720
                                        3590
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8400 8410
                                        8000 8010
                                        8500 8510
                                        8100
                                        8600
					
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 10
    free_market       = 7
    freedom           = 8
    professional_army = 5
    defense_lobby     = 3
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 18200 id = 1 }
    location = 485
    name     = "Dowództwo Wojsk Ladowych"
    division =
    { id            = { type = 18200 id = 2 }
      name          = "Dowództwo Wojsk Ladowych"
      strength      = 100
      type          = hq
      model         = 1
      extra         = heavy_armor
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 18200 id = 3 }
    location = 302
    name     = "12 Szczecinska DZ im. Boleslawa Krzywoustego"
    division =
    { id            = { type = 18200 id = 4 }
      name          = "2 BZ Legionów im. Marszalka Józefa Pilsudskiego"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id       = { type = 18200 id = 5 }
      name     = "7 Pomorska Brygada Obrony Wybrzeza"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 18200 id = 6 }
      name     = "12 BZ im. gen. broni Józefa Hallera"
      strength = 100
      type     = cavalry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 18200 id = 7 }
    location = 304
    name     = "16 Pomorska DZ im. Króla Kazimierza Jagiellonczyka"
    division =
    { id            = { type = 18200 id = 8 }
      name          = "15 Gizycka BZ im. Zawiszy Czarnego z Grabowa"
      strength      = 60
      type          = cavalry
      model         = 1
    }
    division =
    { id       = { type = 18200 id = 9 }
      name     = "20 Bartoszycka BZ im. Hetmana Polnego Litewskiego Wincentego Gosiewskiego"
      strength = 60
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 18200 id = 10 }
      name     = "9 BKPanc im. Króla Stefana Batorego"
      strength = 60
      type     = light_armor
      model    = 4
    }
  }
  landunit =
  { id       = { type = 18200 id = 11 }
    location = 485
    name     = "1 Warszawska DZ im. Tadeusza Kosciuszki"
    division =
    { id            = { type = 18200 id = 12 }
      name          = "1 Warszawska BPanc Tadeusza Kosciuszki"
      strength      = 100
      type          = light_armor
      model         = 4
    }
  }
  landunit =
  { id       = { type = 18200 id = 13 }
    location = 489
    name     = "21 Brygada Strzelców Podhalanskich"
    division =
    { id            = { type = 18200 id = 14 }
      name          = "21 Brygada Strzelców Podhalanskich"
      strength      = 100
      type          = cavalry
      model         = 1
    }
  }
  landunit =
  { id       = { type = 18200 id = 15 }
    location = 487
    name     = "3 Brygada Zmechanizowana Legionów"
    division =
    { id            = { type = 18200 id = 16 }
      name          = "3 BZ Legionów im. Romualda Traugutta"
      strength      = 100
      type          = cavalry
      model         = 1
    }
  }
  landunit =
  { id       = { type = 18200 id = 17 }
    location = 479
    name     = "6 Brygada Desantowo-Szturmowa"
    division =
    { id       = { type = 18200 id = 18 }
      name     = "6 Brygada Desantowo-Szturmowa"
      strength = 100
      type     = paratrooper
      model    = 14
    }
  }
  landunit =
  { id       = { type = 18200 id = 19 }
    location = 484
    name     = "25 Brygada Kawalerii Powietrznej"
    division =
    { id       = { type = 18200 id = 20 }
      name     = "25 Brygada Kawalerii Powietrznej"
      strength = 100
      type     = militia
      model    = 1
    }
  }
  landunit =
  { id       = { type = 18200 id = 21 }
    location = 308
    name     = "11 DKPanc im. Króla Jana III Sobieskiego"
    division =
    { id            = { type = 18200 id = 22 }
      name          = "10 BKPanc im. gen. broni Stanislawa Maczka"
      strength      = 100
      type          = light_armor
      model         = 5
    }
    division =
    { id            = { type = 18200 id = 23 }
      name          = "34 BKPanc im. hetmana wielkiego koronnego Jana Zamoyskiego"
      strength      = 100
      type          = light_armor
      model         = 5
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 18200 id = 200 }
    location = 303
    base     = 303
    name     = "3rd Ship Flotilla"
    division =
    { id    = { type = 18200 id = 201 }
      name  = "ORP Warszawa"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 18200 id = 202 }
      name  = "ORP General Kazimierz Pulaski"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18200 id = 203 }
      name  = "ORP General Tadeusz Kósciuszko"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 18200 id = 213 }
    location = 303
    base     = 303
    name     = "45th Auxiliary Vessel Squadron"
    division =
    { id    = { type = 18200 id = 214 }
      name  = "1st Transport Flottila"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 18200 id = 217 }
    location = 303
    base     = 303
    name     = "Submarine Squadron"
    division =
    { id    = { type = 18200 id = 218 }
      name  = "ORP Orzel"
      type  = submarine
      model = 4
    }
    division =
    { id    = { type = 18200 id = 219 }
      name  = "ORP Dzik"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 18200 id = 220 }
      name  = "ORP Wilk"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 18200 id = 221 }
      name  = "ORP Sokó"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 18200 id = 222 }
      name  = "ORP Sep"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 18200 id = 223 }
      name  = "ORP Kondor"
      type  = submarine
      model = 1
    }
    division =
    { id    = { type = 18200 id = 224 }
      name  = "ORP Bielik"
      type  = submarine
      model = 1
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 18200 id = 100 }
    location = 306
    base     = 306
    name     = "1st Tactical Aviation Brigade"
    division =
    { id       = { type = 18200 id = 101 }
      name     = "1st Tactical Air Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18200 id = 102 }
      name     = "8th Tactical Air Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 18200 id = 104 }
    location = 480
    base     = 480
    name     = "3rd Tactical Aviation Brigade"
    division =
    { id       = { type = 18200 id = 105 }
      name     = "6th Tactical Air Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18200 id = 106 }
      name     = "7th Tactical Air Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18200 id = 107 }
    location = 480
    base     = 480
    name     = "Central Air Transport Command"
    division =
    { id       = { type = 18200 id = 108 }
      name     = "1st Air Transport Squadron"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
}
