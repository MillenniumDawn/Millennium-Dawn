
##############################
# Country definition for SPA #
##############################

province =
{ id       = 357
  naval_base = { size = 8 current_size = 8 }
    air_base = { size = 4 current_size = 4 }
}            # Barcelona

province =
{ id       = 332
  naval_base = { size = 4 current_size = 4 }
}            # Oviedo

province =
{ id         = 339
  air_base = { size = 4 current_size = 4 }
}              # Valladolid

country =
{ tag                 = SPA
  regular_id          = U06
  manpower            = 65
  transports          = 120
  escorts             = 0
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 20
  capital             = 341
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
    relation = { tag = SLV value = 200 access = yes }
    relation = { tag = USA value = 200 access = yes }
    relation = { tag = TUR value = 200 access = yes }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 334 332 333 339 338 341 343 346 347 349 350 351 352 353 354 342 355 340 330 331 356 329 357 535 963
                          348 957 954
                        }
  ownedprovinces      = { 334 332 333 339 338 341 343 346 347 349 350 351 352 353 354 342 355 340 330 331 356 329 357 535 963
                          957 954
                        }
  controlledprovinces = { 334 332 333 339 338 341 343 346 347 349 350 351 352 353 354 342 355 340 330 331 356 329 357 535 963
                          957 954
                        }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
					#Army Equip
					2200 2210 2220
					2800 2810 2820
					2600 2610 2620
					2700 2710 2720
					2400 2410 2420
					2300 2310 2320
                                        2000 2050 2110
                                        2010 2060 2120
                                             2070
					2500 2510 2520
					#Army Org
					1260 1270
					1900 1910 1920
					1500 1510 1520
					1400 1410 1420
					1300 1310 1320
					1200 1210 1220
                                        1000 1050 1110
                                        1010 1060 1120
                                             1070
					1800 1810
					1700
					1600 1650
					#Aircraft
					4800 4810 4820
					4700 4710 4720
					4750 4760 4770
					4900 4910
                                        4000 4010 4020
                                        4100 4110 4120 4130
					4400 4410 4420
                                        4640 4650
					#Land Docs
					6010 6030 6040
					6930
					6600 6610
					6100 6110 6120 6130 6140 6150 6160 6170
					6200 6210 6220 6230 6240 6250 6260 6270
					#Air Docs
					9040 9510 9520 9530 9540
					9050 9060 9070 9090 9110 9120
					9130 9140 9150 9170 9190 9200
					9450 9460
					#Secret Weapons
					7010 7060 7070 7080
					7180
                                        7330 7310 7320
                                        #Navy Techs
                                        3000 3010 3020
                                        3100 3110 3120 3130
                                        3400 3410
                                        3700 3710 37710 3720
                                        3590
                                        3850 3860 3870 3880
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
    political_left    = 5
    free_market       = 7
    freedom           = 9
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 7
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 20100 id = 1 }
    location = 352
    name     = "Rapid Reaction Force"
    division =
    { id       = { type = 20100 id = 3 }
      name     = "6th Parachutist Brigade"
      strength = 100
      type     = paratrooper
      model    = 15
    }
    division =
    { id       = { type = 20100 id = 4 }
      name     = "7th Airmobile Infantry Brigade"
      strength = 100
      type     = militia
      model    = 1
    }
    division =
    { id       = { type = 20100 id = 5 }
      name     = "13th Spanish Legion Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
    division =
    { id       = { type = 20100 id = 6 }
      name     = "2nd Spanish Legion Brigade"
      strength = 100
      type     = mechanized
      model    = 2
    }
  }
  landunit =
  { id       = { type = 20100 id = 7 }
    location = 338
    name     = "1st Mechanized Army"
    division =
    { id            = { type = 20100 id = 8 }
      name          = "3rd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 1
    }
  }
  landunit =
  { id       = { type = 20100 id = 10 }
    location = 331
    name     = "Mountain Force"
    division =
    { id            = { type = 20100 id = 11 }
      name          = "62nd Mountain Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
    division =
    { id            = { type = 20100 id = 12 }
      name          = "66th Mountain Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
    division =
    { id            = { type = 20100 id = 13 }
      name          = "51st Mountain Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
    division =
    { id            = { type = 20100 id = 14 }
      name          = "52nd Mountain Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 13
    }
  }
  landunit =
  { id       = { type = 20100 id = 15 }
    location = 357
    name     = "Marines Command"
    division =
    { id            = { type = 20100 id = 16 }
      name          = "1st Marine Brigade"
      strength      = 100
      type          = marine
      model         = 11
    }
  }
  landunit =
  { id       = { type = 20100 id = 17 }
    location = 965
    name     = "Canary Isles Command"
    division =
    { id            = { type = 20100 id = 18 }
      name          = "Canary Isles Garrison"
      strength      = 100
      type          = garrison
      model         = 7
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 20100 id = 200 }
    location = 332
    base     = 332
    name     = "1st Fleet"
    division =
    { id    = { type = 20100 id = 201 }
      name  = "SPS Principe de Asturias"
      type  = escort_carrier
      model = 1
    }
    division =
    { id    = { type = 20100 id = 202 }
      name  = "SPS Santa Maria"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 20100 id = 203 }
      name  = "SPS Victoria"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 20100 id = 204 }
      name  = "SPS Numancia"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 20100 id = 205 }
      name  = "SPS Reina Sofia"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 20100 id = 206 }
      name  = "SPS Navarra"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 20100 id = 207 }
      name  = "SPS Canarias"
      type  = destroyer
      model = 2
    }
  }
  navalunit =
  { id       = { type = 20100 id = 208 }
    location = 357
    base     = 357
    name     = "2nd Fleet"
    division =
    { id    = { type = 20100 id = 209 }
      name  = "SPS Alvaro de Bazan"
      type  = light_cruiser
      model = 3
    }
    division =
    { id    = { type = 20100 id = 210 }
      name  = "SPS Baleares"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 20100 id = 211 }
      name  = "SPS Andalucia"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 20100 id = 212 }
      name  = "SPS Cataluna"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 20100 id = 213 }
      name  = "SPS Asturias"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 20100 id = 214 }
      name  = "SPS Extremadura"
      type  = destroyer
      model = 0
    }
  }
  navalunit =
  { id       = { type = 20100 id = 230 }
    location = 357
    base     = 357
    name     = "1st Amphibious Fleet"
    division =
    { id    = { type = 20100 id = 231 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 20100 id = 232 }
      name  = "2nd Transport Fleet"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 20100 id = 233 }
      name  = "3rd Transport Fleet"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 20100 id = 235 }
    location = 357
    base     = 357
    name     = "1st Submarine Fleet"
    division =
    { id    = { type = 20100 id = 236 }
      name  = "SPS Galerna"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 20100 id = 237 }
      name  = "SPS Siroco"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 20100 id = 238 }
      name  = "SPS Mistral"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 20100 id = 239 }
      name  = "SPS Tramontana"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 20100 id = 240 }
      name  = "SPS Delfin"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 20100 id = 241 }
      name  = "SPS Tonina"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 20100 id = 242 }
      name  = "SPS Marsopa"
      type  = submarine
      model = 0
    }
    division =
    { id    = { type = 20100 id = 243 }
      name  = "SPS Narval"
      type  = submarine
      model = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 20100 id = 100 }
    location = 339
    base     = 339
    name     = "Madrid Central Air Command"
    division =
    { id       = { type = 20100 id = 101 }
      name     = "12th Group"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 20100 id = 102 }
    location = 357
    base     = 357
    name     = "Seville Straits Air Command"
    division =
    { id       = { type = 20100 id = 103 }
      name     = "14th Group"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20100 id = 104 }
      name     = "11th Group"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 20100 id = 106 }
      name     = "15th Group"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 20100 id = 108 }
      name     = "46th Group"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 20100 id = 300 }
    name  = "SPS Almirante Juan de Borbon"
    type  = light_cruiser
    model = 3
    cost  = 5
    date  = { day = 2 month = november year = 2003 }
  }
  division_development =
  { id    = { type = 20100 id = 301 }
    name  = "SPS Blas de Lezo"
    type  = light_cruiser
    model = 3
    cost  = 5
    date  = { day = 20 month = september year = 2004 }
  }
  division_development =
  { id    = { type = 20100 id = 302 }
    name  = "SPS Mendez Numez"
    type  = light_cruiser
    model = 3
    cost  = 5
    date  = { day = 11 month = july year = 2005 }
  }
  division_development =
  { id    = { type = 20100 id = 303 }
    name  = "SPS S-81"
    type  = submarine
    model = 4
    cost  = 7
    date  = { day = 27 month = august year = 2005 }
  }
}
