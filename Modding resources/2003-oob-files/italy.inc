
##############################
# Country definition for ITA #
##############################

province =
{ id         = 523
  naval_base = { size = 10 current_size = 10 }
}              # Taranto

province =
{ id         = 370
  air_base = { size = 6 current_size = 6 }
}              # Milan

province =
{ id         = 522
  air_base = { size = 4 current_size = 4 }
}              # Potenza


country =
{ tag                 = ITA
  regular_id          = U06
  manpower            = 70
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 150
  capital             = 515
  transports          = 180
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
    relation = { tag = USA value = 200 access = yes }
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
  nationalprovinces   = { 430 1887 368 369 370 371 378 379 512 531 513 514 515 516 517 518 519 520 521 522 523 524 525 526 534 }
  ownedprovinces      = { 430 1887 368 369 370 371 378 379 512 531 513 514 515 516 517 518 519 520 521 522 523 524 525 526 534 }
  controlledprovinces = { 430 1887 368 369 370 371 378 379 512 531 513 514 515 516 517 518 519 520 521 522 523 524 525 526 534 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
                                        2000 2050 2110
                                        2010 2060
                                             2070
					2300 2310 2320 2330
					2400 2410 2420 2430
					2200 2210 2220 2230
					2500 2510 2520 2530
					2600 2610 2620 2630
					2700 2710 2720 2730
					2800 2810 2820 2830
					#Army Org
                                        1000 1050 1110
                                        1010 1060
                                             1070
					1960
					1900 1910 1920 1930
					1260 1270
					1500 1510 1520 1530
					1200 1210 1220 1230
					1300 1310 1320 1330
					1400 1410 1420 1430
					1800 1810 1820
					1700 1710 1720
					1600 1610
					1650 1660
					#Aircraft
					4640 4650 4660 4670
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4900 4910 4920
					4570
					4400 4410 4420
                                        4000 4010 4020
                                        4100 4110 4120 4130
					4500 4510 4520
					#Land Docs
					6020 6030 6040
					6930
					6600 6610
					6700 6710
					6100 6110 6120 6130 6140 6150 6160 6170
					6200 6210 6220 6230 6240 6250 6260 6270
					6300 6310 6320 6330 6340 6350 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9450 9460
					9050 9060 9070 9090 9110 9120
					9130 9140 9150 9170 9190 9200
					9210 9220 9230 9280
					#Secret Weapons
					7010 7060 7070
					7180
                                        7330 7310 7320
                                        #Navy Techs
                                        3000 3010
                                        3100 3110 3120
                                        3400 3410 3420
                                        3590 3600
                                        3700 37700 3710 37710
                                        3850 3860 3870
                                        #Navy Doctrines
                                        8900 8910 8920
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020
                                        8500 8510 8520
                                        8100 8110 8120
                                        8600 8610 8620
                                        8300 8310 8320
                                        8800 8810 8820
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 4
    free_market       = 7
    freedom           = 9
    professional_army = 4
    defense_lobby     = 3
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12900 id = 1 }
    location = 378
    name     = "COMFOD 1"
    division =
    { id            = { type = 12900 id = 2 }
      name          = "'Poz. de Friuli' Cavalry Brigade"
      strength      = 100
      type          = cavalry
      model         = 3
    }
    division =
    { id            = { type = 12900 id = 3 }
      name          = "'Ariete' Tank Brigade"
      strength      = 100
      type          = light_armor
      model         = 7
    }
    division =
    { id            = { type = 12900 id = 4 }
      name          = "'Friuli' Brigade"
      strength      = 100
      type          = militia
      model         = 2
    }
    division =
    { id       = { type = 12900 id = 5 }
      name     = "'Folgore Para' Brigade"
      strength = 100
      type     = paratrooper
      model    = 15
    }
  }
  landunit =
  { id       = { type = 12900 id = 6 }
    location = 521
    name     = "COMFOD 2"
    division =
    { id            = { type = 12900 id = 7 }
      name          = "COMFOD HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id            = { type = 12900 id = 8 }
      name          = "'Pinerolo' Tank Brigade"
      strength      = 100
      type          = light_armor
      model         = 5
    }
    division =
    { id       = { type = 12900 id = 9 }
      name     = "'Garibaldi' Bersaglieri Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 12900 id = 10 }
      name     = "'Aosta' Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 12900 id = 11 }
      name     = "'Sassari' Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
    division =
    { id       = { type = 12900 id = 12 }
      name     = "'Granatieri Di Sardegna' Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 12900 id = 13 }
    location = 371
    name     = "Alpine Troop Command"
    division =
    { id            = { type = 12900 id = 14 }
      name          = "'Julia' Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 14
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id       = { type = 12900 id = 15 }
      name     = "'Taurinese' Brigade"
      strength = 40
      type     = bergsjaeger
      model    = 14
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 12900 id = 16 }
    location = 522
    name     = "Marine Corps"
    division =
    { id       = { type = 12900 id = 17 }
      name     = "'San Marco' Regiment"
      strength = 100
      type     = marine
      model    = 12
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 12900 id = 300 }
    location = 523
    base     = 523
    name     = "Giuseppe Garibaldi Strike Group"
    division =
    { id            = { type = 12900 id = 301 }
      name          = "NMM Giuseppe Garibaldi"
      type          = escort_carrier
      model         = 1
    }
    division =
    { id    = { type = 12900 id = 303 }
      name  = "NMM Luigi Durand de la Penne"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 12900 id = 304 }
      name  = "NMM Francesco Mimbelli"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 12900 id = 305 }
      name  = "NMM Maestrale"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 306 }
      name  = "NMM Grecale"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 307 }
      name  = "NMM Libeccio"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 308 }
      name  = "NMM Espero"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 309 }
      name  = "NMM Sagittario"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 310 }
      name  = "NMM Perseo"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 12900 id = 311 }
    location = 523
    base     = 523
    name     = "2nd Fleet"
    division =
    { id    = { type = 12900 id = 312 }
      name  = "NMM Audace"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 12900 id = 313 }
      name  = "NMM Ardito"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 12900 id = 314 }
      name  = "NMM Artigliere"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 315 }
      name  = "NMM Aviere"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 316 }
      name  = "NMM Bersagliere"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 317 }
      name  = "NMM Granatiere"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 318 }
      name  = "NMM Scirocco"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 319 }
      name  = "NMM Alliseo"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 320 }
      name  = "NMM Euro"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 12900 id = 321 }
      name  = "NMM Zeffiro"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 12900 id = 331 }
    location = 523
    base     = 523
    name     = "1st Amphibious Fleet"
    division =
    { id    = { type = 12900 id = 302 }
      name  = "NMM Vittorio Veneto"
      type  = transport
      model = 2
    }
    division =
    { id    = { type = 12900 id = 332 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12900 id = 333 }
      name  = "2nd Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 12900 id = 334 }
      name  = "3rd Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 12900 id = 335 }
    location = 523
    base     = 523
    name     = "1st Submarine Fleet"
    division =
    { id    = { type = 12900 id = 336 }
      name  = "NMM Primo Longobardo"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 12900 id = 337 }
      name  = "NMM Gianfranco Gazzana Priaroggia"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 12900 id = 338 }
      name  = "NMM Salvatore Pelosi"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 12900 id = 339 }
      name  = "NMM Guiliano Primi"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 12900 id = 340 }
      name  = "NMM Carlo Fecia Di Cossato"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 12900 id = 341 }
      name  = "NMM Leonardo Da Vinci"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 12900 id = 342 }
      name  = "NMM Guglielmo Marconi"
      type  = submarine
      model = 2
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 12900 id = 200 }
    location = 370
    base     = 370
    name     = "1st Ground Attack Wing"
    division =
    { id       = { type = 12900 id = 201 }
      name     = "6th Squadron"
      type     = tactical_bomber
      strength = 70
      model    = 0
    }
    division =
    { id       = { type = 12900 id = 202 }
      name     = "50th Squadron"
      type     = tactical_bomber
      strength = 70
      model    = 0
    }
    division =
    { id       = { type = 12900 id = 203 }
      name     = "51st Squadron"
      type     = tactical_bomber
      strength = 70
      model    = 0
    }
    division =
    { id       = { type = 12900 id = 204 }
      name     = "5th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 12900 id = 205 }
    location = 370
    base     = 370
    name     = "1st Air Force"
    division =
    { id       = { type = 12900 id = 206 }
      name     = "1st Transport Squadron"
      type     = transport_plane
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 12900 id = 207 }
    location = 522
    base     = 522
    name     = "5th Fighter Wing"
    division =
    { id       = { type = 12900 id = 208 }
      name     = "32nd Squadron"
      type     = multi_role
      strength = 55
      model    = 2
    }
    division =
    { id       = { type = 12900 id = 209 }
      name     = "36th Squadron"
      type     = multi_role
      strength = 55
      model    = 2
    }
    division =
    { id       = { type = 12900 id = 210 }
      name     = "37th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 3
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 12900 id = 400 }
    name  = "NMM Cavour"
    type  = escort_carrier
    model = 2
    cost  = 15
    date  = { day = 1 month = june year = 2007 }
  }
}
