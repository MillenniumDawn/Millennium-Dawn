
##############################
# Country definition for FRA #
##############################

province =
{ id         = 32
  naval_base = { size = 10 current_size = 10 }
}              # Brest

province =
{ id         = 365
  naval_base = { size = 8 current_size = 8 }
}              # Toulon

province =
{ id         = 1692
  naval_base = { size = 1 current_size = 1 }
}              # Noumea

province =
{ id         = 56
  air_base = { size = 3 current_size = 3 }
 rocket_test = { size = 2 current_size = 2 }
}              # Paris

province =
{ id         = 318
  air_base = { size = 6 current_size = 6 }
}              # Dijon

province =
{ id         = 529
      nuclear_reactor = 6
}            # Besancon


country =
{ tag                 = FRA
  regular_id          = U06
  capital             = 56
  # Resource Reserves
  nuke                = 30
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 60
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
    relation = { tag = USA value = 100 }
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
    relation = { tag = U11 value = 100 access = yes }
    relation = { tag = U10 value = 150 access = yes }
    relation = { tag = U08 value = 100 access = yes }
    relation = { tag = SIB value = 100 access = yes }
    relation = { tag = RHO value = 100 access = yes }
    relation = { tag = OTT value = 150 access = yes }
    relation = { tag = MEN value = 100 access = yes }
    relation = { tag = MAD value = 100 access = yes }
    relation = { tag = GUI value = 100 access = yes }
    relation = { tag = GAB value = 150 access = yes }
    relation = { tag = CAM value = 100 access = yes }
    relation = { tag = BEN value = 100 access = yes }
    relation = { tag = CON value = 100 access = yes }
    relation = { tag = VIC value = 100 access = yes }
    relation = { tag = U12 value = 150 access = yes }
    relation =
    { tag        = DDR
      value      = 150
      access     = yes
    }
  }
  nationalprovinces   = { 18  32  33  34  35  36  37  38  39  40  41  42  43  44  53  54  55  56  57  58  59  60  61  62  63  64  72  73  316 317 318
                          319 320 321 322 323 324 325 326 327 328 358 359 360 361 362 363 364 365 366 367 527 528 529
                        }
  ownedprovinces      = { 18   32   33   34   35   36   37   38   39   40   41   42   43   44   53   54   55   56   57   58   59   60   61   62   63  
                          64   72   73   316  317  318  319  320  321  322  323  324  325  326  327  328  358  359  360  361  362  363  364  365  366 
                          367  527  528  529  875  898  899  1135 1687 1691 1692 1751
                        }
  controlledprovinces = { 18   32   33   34   35   36   37   38   39   40   41   42   43   44   53   54   55   56   57   58   59   60   61   62   63  
                          64   72   73   316  317  318  319  320  321  322  323  324  325  326  327  328  358  359  360  361  362  363  364  365  366 
                          367  527  528  529  875  898  899  1135 1687 1691 1692 1751
                        }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220 2230
					2000 2010
                                        2050 2060 2070
					2110 2150
					2300 2310 2320 2330
					2400 2410 2420 2430
					2500 2510 2520 2530
					2600 2610 2620 2630
					2700 2710 2720 2730
					2800 2810 2820 2830
					#Army Org
					1980 1970 1960
					1260 1270
					1000 1010
                                        1050 1060 1070
					1150
					1500 1510 1520 1530
					1200 1210 1220 1230
					1300 1310 1320 1330
					1400 1410 1420 1430
					1700 1710 1720
					1900 1910 1920 1930
					1800 1810 1820
					1600 1610
					1650 1660
					#Aircraft
					4100 4110 4120 4130
					4000 4010
					4640 4650 4660 4670
					4600 4610
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4400 4410
					4300 4310
					4900 4910 4920
					4500 4510
					#Land Docs
					6010 6030 6050 6070 6080
					6930
					6600 6620
					6700 6720
					6100 6110 6120 6130 6140 6150 6160 6170
					6200 6210 6220 6230 6240 6250 6260 6270
					6300 6310 6320 6330 6340 6350 6360 6370
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9090 9110 9120
					9130 9140 9150 9170 9190 9200
					9210
					9450 9460
					#Secret Weapons
					7010
					7020 7030 7040 7050
					7060 7070 7080
					7100 7110 7120
					7180 7190 7200
                                        7330 7310 7320
                                        #Navy Doctrines
                                        8900 8910 8920 8930
                                        8950 8960 8970
                                        8400 8410 8420
                                        8000 8010 8020 8030
                                        8500 8510 8520 8530
                                        8100 8110 8120
                                        8600 8610 8620
                                        8200
                                        8700
                                        8300 8310 8320
                                        8800 8810 8820
                                        #Navy Techs
                                        3000 3010 3020 3030
                                        3100 3110 3120
                                        3400 3410 3420
                                        3590 3600
                                        3700 37700 3710 37710 3720
                                        3800 3810 38810 3820 38820
                                        3850 3860 3870 3880
                                        3900 3910 3920
                        }
  blueprints          = { 3610 }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 6
    free_market       = 7
    freedom           = 9
    professional_army = 10
    defense_lobby     = 4
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 10600 id = 1 }
    location = 57
    name     = "1ère Corps"
    division =
    { id            = { type = 10600 id = 2 }
      name          = "2ème Brigade Blindée"
      strength      = 100
      type          = light_armor
      model         = 11
    }
    division =
    { id            = { type = 10600 id = 3 }
      name          = "Quartier Général de Compiègne"
      strength      = 100
      type          = hq
      model         = 1
      extra         = heavy_armor
      brigade_model = 2
    }
  }
  landunit =
  { id       = { type = 10600 id = 4 }
    location = 529
    name     = "2ème Corps"
    division =
    { id            = { type = 10600 id = 5 }
      name          = "7ème Brigade Blindée"
      strength      = 100
      type          = light_armor
      model         = 11
    }
  }
  landunit =
  { id       = { type = 10600 id = 6 }
    location = 55
    name     = "3ème Corps"
    division =
    { id            = { type = 10600 id = 7 }
      name          = "1ère Brigade Mecanisée"
      strength      = 100
      type          = cavalry
      model         = 3
    }
  }
  landunit =
  { id       = { type = 10600 id = 10 }
    location = 363
    name     = "5ème Corps"
    division =
    { id            = { type = 10600 id = 11 }
      name          = "6ème Brigade Légère Blindée"
      strength      = 100
      type          = cavalry
      model         = 3
    }
  }
  landunit =
  { id       = { type = 10600 id = 12 }
    location = 35
    name     = "1er Corps de Marine"
    division =
    { id            = { type = 10600 id = 13 }
      name          = "9ème Brigade De Marine"
      strength      = 100
      type          = marine
      model         = 12
    }
  }
  landunit =
  { id       = { type = 10600 id = 14 }
    location = 56
    name     = "1er Corps Aéroporté"
    division =
    { id            = { type = 10600 id = 15 }
      name          = "11ème Brigade Parachutiste"
      strength      = 100
      type          = paratrooper
      model         = 16
    }
  }
  landunit =
  { id       = { type = 10600 id = 16 }
    location = 328
    name     = "Forces Spéciales"
    division =
    { experience    = 15
      id            = { type = 10600 id = 17 }
      name          = "Brigade des Forces Spéciales"
      strength      = 100
      type          = bergsjaeger
      model         = 14
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 10600 id = 18 }
    location = 527
    name     = "1er Corps de Montagne"
    division =
    { id            = { type = 10600 id = 19 }
      name          = "27ème Brigade D'Infanterie De Montagne"
      strength      = 100
      type          = bergsjaeger
      model         = 14
    }
  }
  landunit =
  { id       = { type = 10600 id = 20 }
    location = 1037
    name     = "Corps de Djibouti"
    division =
    { experience    = 15
      id       = { type = 10600 id = 21 }
      name     = "13è Brigade Légion Etrangère"
      strength = 100
      type          = bergsjaeger
      model         = 14
    }
    division =
    { id       = { type = 10600 id = 22 }
      name     = "5ème Brigade D'Infanterie De Marine"
      strength = 100
      type     = marine
      model    = 12
    }
  }
  landunit =
  { id       = { type = 10600 id = 23 }
    location = 875
    name     = "Corps de Guyane"
    division =
    { experience    = 15
      id       = { type = 10600 id = 24 }
      name     = "3è Régiment Légion Etrangère"
      strength = 30
      type          = bergsjaeger
      model         = 14
    }
  }
  landunit =
  { id       = { type = 10600 id = 25 }
    location = 1135
    name     = "Corps de la Réunion"
    division =
    { id       = { type = 10600 id = 26 }
      name     = "2è Régiment Parachutiste"
      strength = 30
      type     = paratrooper
      model    = 16
    }
  }
  landunit =
  { id       = { type = 10600 id = 27 }
    location = 1692
    name     = "Forces Armées de Polynésie"
    division =
    { id       = { type = 10600 id = 28 }
      name     = "1er Régiment D'Inf. Marine Pacifique"
      strength = 30
      type     = marine
      model    = 12
    }
  }
  landunit =
  { id       = { type = 10600 id = 29 }
    location = 1751
    name     = "Forces Armées de Tahiti"
    division =
    { id       = { type = 10600 id = 30 }
      name     = "2è Regiment D'Inf. Marine Pacifique"
      strength = 30
      type     = marine
      model    = 12
    }
  }
 # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 10600 id = 200 }
    location = 32
    base     = 32
    name     = "Flotte Atlantique"
    division =
    { id    = { type = 10600 id = 202 }
      name  = "FS Tourville"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 10600 id = 203 }
      name  = "FS Primauguet"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 10600 id = 204 }
      name  = "FS Latouche-Treville"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 10600 id = 205 }
      name  = "FS Ventose"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 10600 id = 206 }
      name  = "FS Germinal"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 10600 id = 210 }
      name  = "FS Siroco"
      type  = transport
      model = 2
    }
    division =
    { id    = { type = 10600 id = 211 }
      name  = "FS Flotte de Transport"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 10600 id = 212 }
    location = 365
    base     = 365
    name     = "Flotte Méditerranéenne"
    division =
    { id    = { type = 10600 id = 213 }
      name  = "FS Duquesne"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 10600 id = 214 }
      name  = "FS Cassard"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 10600 id = 215 }
      name  = "FS Georges Leygues"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 10600 id = 216 }
      name  = "FS Dupleix"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 10600 id = 217 }
      name  = "FS Montcalm"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 10600 id = 218 }
      name  = "FS Jean de Vienne"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 10600 id = 219 }
      name  = "FS La Fayette"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 10600 id = 220 }
      name  = "FS Courbet"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 10600 id = 221 }
      name  = "FS Aconit"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 10600 id = 222 }
      name  = "FS Guepratte"
      type  = destroyer
      model = 3
    }
  }
  navalunit =
  { id       = { type = 10600 id = 230 }
    location = 365
    base     = 365
    name     = "Flotte Sous-Marine de Méditerranée"
    division =
    { id    = { type = 10600 id = 231 }
      name  = "FS Casablanca"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 10600 id = 232 }
      name  = "FS Emeraude"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 10600 id = 233 }
      name  = "FS Amethyste"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 10600 id = 234 }
      name  = "FS Perle"
      type  = submarine
      model = 14
    }
  }
  navalunit =
  { id       = { type = 10600 id = 235 }
    location = 365
    base     = 365
    name     = "Flotte de Transport de Méditerranée"
    division =
    { id    = { type = 10600 id = 236 }
      name  = "FS Foudre"
      type  = transport
      model = 2
    }
    division =
    { id    = { type = 10600 id = 237 }
      name  = "FS Flotte de Transport"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 10600 id = 240 }
    location = 1692
    base     = 1692
    name     = "Flotte du Pacifique"
    division =
    { id    = { type = 10600 id = 241 }
      name  = "FS Prairial"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 10600 id = 242 }
      name  = "FS Nivose"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 10600 id = 243 }
      name  = "FS Vendermaire"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 10600 id = 244 }
      name  = "FS Flotte de Transport"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 10600 id = 246 }
    location = 1037
    base     = 1037
    name     = "Flotte de l'Océan Indien"
    division =
    { id    = { type = 10600 id = 247 }
      name  = "FS Floreal"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 10600 id = 248 }
      name  = "FS Flotte de Transport"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 10600 id = 249 }
    location = 1037
    base     = 1037
    name     = "Groupe de Combat Charles de Gaulle"
    division =
    { id            = { type = 10600 id = 250 }
      name          = "FS Charles de Gaulle"
      type          = escort_carrier
      model         = 2
    }
    division =
    { id    = { type = 10600 id = 251 }
      name  = "FS De Grasse"
      type  = light_cruiser
      model = 2
    }
    division =
    { id    = { type = 10600 id = 252 }
      name  = "FS Jean Bart"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 10600 id = 253 }
      name  = "FS Surcouf"
      type  = destroyer
      model = 3
    }
    division =
    { id    = { type = 10600 id = 254 }
      name  = "FS La Motte-Picquet"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 10600 id = 255 }
      name  = "FS Rubis"
      type  = submarine
      model = 14
    }
    division =
    { id    = { type = 10600 id = 256 }
      name  = "FS Saphir"
      type  = submarine
      model = 14
    }
  }
  navalunit =
  { id       = { type = 10600 id = 257 }
    location = 32
    base     = 32
    name     = "Force Océanique Stratégique"
    division =
    { id    = { type = 10600 id = 258 }
      name  = "FS Triomphant"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 10600 id = 259 }
      name  = "FS Téméraire"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 10600 id = 260 }
      name  = "FS Vigilant"
      type  = heavy_cruiser
      model = 2
    }
    division =
    { id    = { type = 10600 id = 261 }
      name  = "FS Terrible"
      type  = heavy_cruiser
      model = 2
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 10600 id = 100 }
    location = 56
    base     = 56
    name     = "12ème Escadrille"
    division =
    { id       = { type = 10600 id = 101 }
      name     = "4ème Escadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 10600 id = 102 }
      name     = "7ème Escadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 10600 id = 103 }
      name     = "2ème Escadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 10600 id = 104 }
    location = 56
    base     = 56
    name     = "30ème Escadrille"
    division =
    { id       = { type = 10600 id = 105 }
      name     = "1er Escadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 10600 id = 106 }
      name     = "3ème Escadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 10600 id = 107 }
      name     = "11ème Escadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 10600 id = 108 }
    location = 318
    base     = 318
    name     = "4ème Escadrille"
    division =
    { id       = { type = 10600 id = 109 }
      name     = "14ème Escadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 10600 id = 110 }
      name     = "45ème Escadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 10600 id = 111 }
      name     = "18ème Escadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 10600 id = 112 }
    location = 318
    base     = 318
    name     = "7ème Escadrille"
    division =
    { id       = { type = 10600 id = 113 }
      name     = "9ème Escadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 10600 id = 114 }
      name     = "8ème Escadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 10600 id = 115 }
      name     = "21ème Escadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 10600 id = 116 }
    location = 318
    base     = 318
    name     = "2ème Escadrille"
    division =
    { id       = { type = 10600 id = 117 }
      name     = "23ème Escadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 10600 id = 118 }
      name     = "49ème Escadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 10600 id = 119 }
      name     = "55ème Escadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 10600 id = 120 }
    location = 56
    base     = 56
    name     = "Escadrille de Transport Aérien"
    division =
    { id       = { type = 10600 id = 121 }
      name     = "34ème Escadron"
      type     = transport_plane
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 10600 id = 122 }
      name     = "27ème Escadron"
      type     = transport_plane
      strength = 100
      model    = 2
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 10600 id = 300 }
    name  = "FS Mistral"
    type  = transport
    model = 3
    cost  = 22
    date  = { day = 11 month = march year = 2004 }
  }
  division_development =
  { id    = { type = 10600 id = 301 }
    name  = "FS Tonnerre"
    type  = transport
    model = 3
    cost  = 22
    date  = { day = 3 month = june year = 2005 }
  }
}
