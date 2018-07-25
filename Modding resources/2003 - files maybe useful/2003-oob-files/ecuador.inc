
##############################
# Country definition for ECU #
##############################

province =
{ id       = 815
  naval_base = { size = 2 current_size = 2 }
  air_base = { size = 2 current_size = 2 }
}            # Quito

country =
{ tag                 = ECU
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 30
  capital             = 815
  manpower            = 23
  transports          = 31
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 814 815 817 }
  ownedprovinces      = { 814 815 817 }
  controlledprovinces = { 814 815 817 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
                                        #Army Equip:
                                        2000
                                        2010
                                        2300 2310
                                        2400 2400
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
                                        1000
                                        1010
                                        1500 1510
                                        1300 1310
					1260
					1980
					1900 1910
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
					#Air techs
                                        4700 4710
                                        4750 4760
                                        4640
                                        4570
                                        4000 4010 4020
					#Secret Techs
                                        7330
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
                                        #Navy Techs
                                        3000
                                        3590
                                        3700 3710
                                        3850 3860
                                        #Navy Doctrines
                                        8900
                                        8950
                                        8400
                                        8000
                                        8500
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 8
    free_market       = 6
    freedom           = 6
    professional_army = 3
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 9500 id = 1 }
    location = 815
    name     = "I Corps"
    division =
    { id            = { type = 9500 id = 2 }
      name          = "1st Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 9500 id = 3 }
      name          = "2nd Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 9500 id = 4 }
      name          = "13th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 9500 id = 5 }
      name          = "5th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 9500 id = 6 }
      name          = "Ecuadorian Army HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = heavy_armor
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 9500 id = 7 }
    location = 817
    name     = "II Corps"
    division =
    { experience    = 5
      id            = { type = 9500 id = 8 }
      name          = "9th Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id            = { type = 9500 id = 9 }
      name          = "17th Jungle Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
    division =
    { id            = { type = 9500 id = 10 }
      name          = "19th Jungle Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 9500 id = 11 }
      name          = "21st Jungle Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
  }
  landunit =
  { id       = { type = 9500 id = 12 }
    location = 814
    name     = "III Corps"
    division =
    { id       = { type = 9500 id = 13 }
      name     = "3rd Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 9500 id = 14 }
      name     = "9th Infantry Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
    division =
    { id       = { type = 9500 id = 15 }
      name     = "11th Armored Cavalry Brigade"
      strength = 100
      type     = light_armor
      model    = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 9500 id = 300 }
    location = 815
    base     = 815
    name     = "1st Fleet"
    division =
    { id    = { type = 9500 id = 301 }
      name  = "BAE Presidente Eloy Alfaro"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 9500 id = 302 }
      name  = "BAE Moran Valverde"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 9500 id = 303 }
      name  = "BAE Shyri"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 9500 id = 304 }
      name  = "BAE Huancavilca"
      type  = submarine
      model = 2
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 9500 id = 100 }
    location = 815
    base     = 815
    name     = "Ecuadorian Air Force"
    division =
    { id       = { type = 9500 id = 101 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 50
      model    = 2
    }
    division =
    { id       = { type = 9500 id = 102 }
      name     = "2nd Squadron"
      type     = interceptor
      strength = 50
      model    = 1
    }
    division =
    { id       = { type = 9500 id = 103 }
      name     = "3rd Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 0
    }
  }
}
