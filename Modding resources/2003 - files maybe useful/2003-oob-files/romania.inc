
##############################
# Country definition for ROM #
##############################

province =
{ id       = 436
  naval_base = { size = 4 current_size = 4 }
}            # Constanta

province =
{ id       = 431
  air_base = { size = 4 current_size = 4 }
}            # Ploesti

country =
{ tag                 = ROM
  capital             = 424
  transports          = 34
  escorts             = 0
  manpower            = 39
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 15
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
    relation = { tag = USA value = 100 }
    relation = { tag = SLO value = 200 access = yes }
    relation = { tag = SLV value = 200 access = yes }
    relation = { tag = SPA value = 200 access = yes }
    relation = { tag = TUR value = 200 access = yes }
    relation = { tag = ENG value = 200 access = yes }
  }
  nationalprovinces   = { 424 425 431 426 495 496 498 427 428 429 432 436 433 230 434 1896 435 }
  ownedprovinces      = { 424 425 431 426 495 496 498 427 428 429 432 436 433 }
  controlledprovinces = { 424 425 431 426 495 496 498 427 428 429 432 436 433 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
					2200 2210
					2300 2310
					2400 2410
					2500 2510
					2600 2610
					2700 2710
					2800 2810
					2000 2010
					#Army Org
					1960
					1260
					1900 1910
					1700
					1800
					1000 1010
					1500 1510
					1400 1410
					1300 1310
					1200 1210
					#Aircraft
					4800 4700 4750
					4900
					4640
					4570
                                        4000 4010
					#Land Docs
					6910 6920
					6010 6020
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
					#Air Docs
					9020 9510 9520
					9050 9060 9070 9090 9120
					#Secret Weapons
					7010 7060 7070
					7310 7330
                                        #Navy Techs
                                        3000 3010
                                        3100 3110
                                        3700 3710 3720
                                        3590
                                        3850 3860
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
    democratic        = 9
    political_left    = 10
    free_market       = 6
    freedom           = 8
    professional_army = 8
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 18600 id = 1 }
    location = 428
    name     = "4th Corps"
    division =
    { id            = { type = 18600 id = 2 }
      name          = "Cluj Military Region"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 18600 id = 3 }
      name          = "81st Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 18600 id = 4 }
      name          = "15th Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 18600 id = 5 }
      name          = "61st Mountain Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = police
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 18600 id = 6 }
    location = 424
    name     = "1st Corps"
    division =
    { id            = { type = 18600 id = 7 }
      name          = "Bucharest Military Region"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 18600 id = 8 }
      name          = "2nd Airmobile Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
    division =
    { id            = { type = 18600 id = 9 }
      name          = "2nd Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 18600 id = 10 }
      name          = "34th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 18600 id = 11 }
      name          = "282nd Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id            = { type = 18600 id = 12 }
      name          = "2nd Mountain Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = police
      brigade_model = 0
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 18600 id = 300 }
    location = 436
    base     = 436
    name     = "Romanian Navy"
    division =
    { id    = { type = 18600 id = 301 }
      name  = "Marasesti"
      type  = light_cruiser
      model = 1
    }
    division =
    { id    = { type = 18600 id = 302 }
      name  = "Delfinul"
      type  = submarine
      strength = 15
      model = 4
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 18600 id = 200 }
    location = 431
    base     = 431
    name     = "1st Air Force"
    division =
    { id       = { type = 18600 id = 201 }
      name     = "861st Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18600 id = 202 }
      name     = "862nd Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 18600 id = 203 }
    location = 431
    base     = 431
    name     = "2nd Air Force"
    division =
    { id       = { type = 18600 id = 204 }
      name     = "951st Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18600 id = 206 }
      name     = "711th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18600 id = 207 }
      name     = "712th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
}
