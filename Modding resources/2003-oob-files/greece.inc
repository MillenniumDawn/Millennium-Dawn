
##############################
# Country definition for GRE #
##############################

province =
{ id         = 401
  naval_base = { size = 8 current_size = 8 }
  air_base = { size = 8 current_size = 8 }
}              # Athens

province =
{ id         = 411
  air_base = { size = 4 current_size = 4 }
}              # Salonika

country =
{ tag                 = GRE
  regular_id          = U06
  manpower            = 20
  transports          = 150
  escorts             = 0
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  capital             = 401
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
    relation = { tag = USA value = 150 access = yes }
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
  nationalprovinces   = { 392 393 394 395 396 398 399 400 401 402 403 405 410 411 412 444 223 }
  ownedprovinces      = { 392 393 394 395 396 398 399 400 401 402 403 405 410 411 412 223 }
  controlledprovinces = { 392 393 394 395 396 398 399 400 401 402 403 405 410 411 412 223 }
  techapps            = { 
                                        #Industry:
                                        5010 5110 5210
                                        5020 5120 5220
                                        5030 5130 5230
                                        5040 5140 5240
                                        5050 5150 5250
                                        5060 5160 5260
                                        5070 5170 5270
                                        5080 5180 5280
                                        5090 5190 5290
                                        #Army Equipment:
                                        2000 2050 2110
                                        2010 2060 2120
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
                                        #Army Organisation:
                                        1000 1050 1110
                                        1010 1060
                                        1500 1510 1520
                                        1200 1210 1220
                                        1300 1310 1320
                                        1400 1410 1420
                                        1600
                                        1800 1810
                                        1900 1910 1920
                                        1260 1270
                                        1960
                                        #Army Doctrines:
                                        6100 6200 6300
                                        6110 6210
                                        6120 6220
                                        6130
                                        6140
                                        6160 6260
                                        6170 6270
                                        6010 6030
                                        6040
                                        6910 6920 6930
                                        6600
                                        6620
                                        #Airforce
                                        4000 4010 4020 4030
                                        4100 4110 4120 4130
                                        4550
                                        4570
                                        4400 4410
                                        4640 4650
                                        4700 4710 4720
                                        4750 4760 4770
                                        4800 4810 4820
                                        4900 4910
                                        #Air doctrine
                                        9050 9130 9210
                                        9060 9140 9220
                                        9070 9150 9230
                                        9090 9170 9250
                                        9100 9180
                                        9110 9190
                                        9120 9200 9280
                                        9510 9520 9530 9030
                                        #Secret tech
                                        7180 7190
                                        7240
                                        7330 7310 7320
                                        #Navy Techs
                                        3000 3010 3020
                                        3100
                                        3590
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
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 10
    free_market       = 7
    freedom           = 8
    professional_army = 2
    defense_lobby     = 6
    interventionism   = 7
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 11300 id = 1 }
    location = 403
    name     = "IV Army Corps"
    division =
    { id       = { type = 11300 id = 2 }
      name     = "12th Mechanized Division"
      strength = 100
      type     = infantry
      model    = 1
    }
    division =
    { id            = { type = 11300 id = 3 }
      name          = "20th Armored Division"
      strength      = 100
      type          = armor
      model         = 11
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id       = { type = 11300 id = 4 }
      name     = "16th Infantry Mechanized Division"
      strength = 100
      type     = infantry
      model    = 1
    }
    division =
    { id            = { type = 11300 id = 5 }
      name          = "50th Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 11300 id = 6 }
      name          = "29th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 11300 id = 7 }
    location = 401
    name     = "Hellenic Army"
    division =
    { id            = { type = 11300 id = 8 }
      name          = "Hellenic Army HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id       = { type = 11300 id = 9 }
      name     = "2nd Mechanized Division"
      strength = 100
      type     = infantry
      model    = 1
    }
    division =
    { id       = { type = 11300 id = 10 }
      name     = "71st Airborne Brigade"
      strength = 100
      type     = paratrooper
      model    = 14
    }
    division =
    { id       = { type = 11300 id = 11 }
      name     = "32nd Marines Brigade"
      strength = 100
      type     = marine
      model    = 11
    }
    division =
    { id       = { type = 11300 id = 12 }
      name     = "1st Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 11300 id = 13 }
    location = 410
    name     = "Crete Command"
    division =
    { id            = { type = 11300 id = 14 }
      name          = "5th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 11300 id = 15 }
    location = 392
    name     = "I Army Corps"
    division =
    { id            = { type = 11300 id = 16 }
      name          = "9th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 11300 id = 17 }
      name          = "24th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 3
    }
    division =
    { id            = { type = 11300 id = 18 }
      name          = "9th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 11300 id = 19 }
      name          = "10th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 11300 id = 20 }
      name          = "15th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 11300 id = 300 }
    location = 401
    base     = 401
    name     = "1st Fleet"
    division =
    { id    = { type = 11300 id = 301 }
      name  = "HS Kimon"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 11300 id = 302 }
      name  = "HS Nearchos"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 11300 id = 303 }
      name  = "HS Formion"
      type  = light_cruiser
      model = 0
    }
    division =
    { id    = { type = 11300 id = 304 }
      name  = "HS Hydra"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 11300 id = 305 }
      name  = "HS Spetsai"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 11300 id = 306 }
      name  = "HS Kountouriotis"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 11300 id = 307 }
      name  = "HS Bouboulina"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 11300 id = 308 }
      name  = "HS F464"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 11300 id = 309 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 11300 id = 310 }
      name  = "2nd Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 11300 id = 314 }
    location = 401
    base     = 401
    name     = "2nd Fleet"
    division =
    { id    = { type = 11300 id = 315 }
      name  = "HS Psara"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 11300 id = 316 }
      name  = "HS Salamis"
      type  = destroyer
      model = 2
    }
    division =
    { id    = { type = 11300 id = 317 }
      name  = "HS Elli"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 11300 id = 318 }
      name  = "HS Limnos"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 11300 id = 319 }
      name  = "HS Adrias"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 11300 id = 320 }
      name  = "HS Aegeon"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 11300 id = 321 }
      name  = "HS Navarino"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 11300 id = 322 }
      name  = "HS Ipiros"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 11300 id = 323 }
      name  = "3rd Transport Flotilla"
      type  = transport
      model = 0
    }
    division =
    { id    = { type = 11300 id = 324 }
      name  = "4th Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  navalunit =
  { id       = { type = 11300 id = 331 }
    location = 401
    base     = 401
    name     = "1st Submarine Fleet"
    division =
    { id    = { type = 11300 id = 332 }
      name  = "HS Glavkos"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 11300 id = 333 }
      name  = "HS Nereus"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 11300 id = 334 }
      name  = "HS Triton"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 11300 id = 335 }
      name  = "HS Proteus"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 11300 id = 336 }
      name  = "HS Poseidon"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 11300 id = 337 }
      name  = "HS Amfrititi"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 11300 id = 338 }
      name  = "HS Okeanos"
      type  = submarine
      model = 3
    }
    division =
    { id    = { type = 11300 id = 339 }
      name  = "HS Pontos"
      type  = submarine
      model = 3
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 11300 id = 200 }
    location = 401
    base     = 401
    name     = "1st Air Force"
    division =
    { id       = { type = 11300 id = 201 }
      name     = "110th Wing"
      type     = multi_role
      strength = 60
      model    = 0
    }
    division =
    { id       = { type = 11300 id = 202 }
      name     = "111th Wing"
      type     = multi_role
      strength = 60
      model    = 3
    }
    division =
    { id       = { type = 11300 id = 203 }
      name     = "114th Wing"
      type     = multi_role
      strength = 60
      model    = 3
    }
  }
  airunit =
  { id       = { type = 11300 id = 204 }
    location = 411
    base     = 411
    name     = "2nd Air Force"
    division =
    { id       = { type = 11300 id = 205 }
      name     = "115th Wing"
      type     = multi_role
      strength = 60
      model    = 3
    }
    division =
    { id       = { type = 11300 id = 206 }
      name     = "133rd Wing"
      type     = multi_role
      strength = 60
      model    = 3
    }
  }
  airunit =
  { id       = { type = 11300 id = 207 }
    location = 401
    base     = 401
    name     = "3rd Air Force"
    division =
    { id       = { type = 11300 id = 208 }
      name     = "116th Wing"
      type     = cas
      strength = 60
      model    = 0
    }
    division =
    { id       = { type = 11300 id = 209 }
      name     = "117th Wing"
      type     = multi_role
      strength = 60
      model    = 0
    }
    division =
    { id       = { type = 11300 id = 211 }
      name     = "134th Wing"
      type     = multi_role
      strength = 60
      model    = 0
    }
    division =
    { id       = { type = 11300 id = 213 }
      name     = "135th Wing"
      type     = multi_role
      strength = 30
      model    = 3
    }
  }
}
