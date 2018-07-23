
##############################
# Country definition for COL #
##############################

province =
{ id       = 890
  naval_base = { size = 4 current_size = 4 }
  air_base = { size = 2 current_size = 2 }
}            # Medellin

country =
{ tag                 = COL
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 50
  manpower            = 69
  capital             = 813
  transports          = 15
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 803 812 813 890 867 819 868 }
  ownedprovinces      = { 803 812 813 890 867 819 868 }
  controlledprovinces = { 803 812 813 890 867 819 868 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120
					#Army Equip
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
                                        1500 1510
                                        1300 1310
                                        1400 1410
                                             1700
                                             1800
                                        1900 1910
                                        1260 1980
					#Land Docs
					6910
					6010 6020
					6600 6620
					6100 6110 6120 6160 6170 6150
                                        #Air techs
                                        4400 4410
                                        4640 4650
                                        4700
                                        4750
                                        4900
                                        #Air docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
                                        #Navy Techs
                                        3000 3010
                                        3100
                                        3590
                                        3700 3710
                                        3850 3860
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8400 8410
                                        8000 8010
                                        8500 8510
					
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 7
    free_market       = 6
    freedom           = 5
    professional_army = 3
    defense_lobby     = 5
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 8400 id = 1 }
    location = 813
    name     = "I Corps"
    division =
    { id            = { type = 8400 id = 2 }
      name          = "1st Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
    }
    division =
    { id       = { type = 8400 id = 3 }
      name     = "Colombian Army HQ"
      strength = 100
      type     = hq
      model    = 1
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id       = { type = 8400 id = 4 }
      name     = "7th Mobile Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = police
      brigade_model = 0
    }
    division =
    { id       = { type = 8400 id = 5 }
      name     = "4th Mobile Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = police
      brigade_model = 0
    }
    division =
    { id       = { type = 8400 id = 6 }
      name     = "12th Mobile Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = police
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 8400 id = 7 }
    location = 890
    name     = "II Corps"
    division =
    { id       = { type = 8400 id = 8 }
      name     = "2nd Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 8400 id = 9 }
      name     = "3rd Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8400 id = 10 }
    location = 803
    name     = "III Corps"
    division =
    { experience    = 10
      id            = { type = 8400 id = 11 }
      name          = "Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id            = { type = 8400 id = 12 }
      name          = "7th Airmobile Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id       = { type = 8400 id = 13 }
      name     = "6th Infantry Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  landunit =
  { id       = { type = 8400 id = 14 }
    location = 867
    name     = "IV Corps"
    division =
    { id            = { type = 8400 id = 15 }
      name          = "7th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 8400 id = 16 }
      name          = "5th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 8400 id = 17 }
    location = 867
    name     = "V Corps"
    division =
    { id            = { type = 8400 id = 18 }
      name          = "1st Mobile Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = police
      brigade_model = 0
    }
    division =
    { id            = { type = 8400 id = 19 }
      name          = "2nd Mobile Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = police
      brigade_model = 0
    }
    division =
    { id            = { type = 8400 id = 20 }
      name          = "3rd Mobile Brigade"
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
  { id       = { type = 8400 id = 300 }
    location = 890
    base     = 890
    name     = "Surface Fleet"
    division =
    { id    = { type = 8400 id = 301 }
      name  = "ARC Almirante Padilla"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8400 id = 302 }
      name  = "ARC Caldas"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8400 id = 303 }
      name  = "ARC Antioquia"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 8400 id = 304 }
      name  = "ARC Independencia"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 8400 id = 305 }
    location = 890
    base     = 890
    name     = "Submarine Fleet"
    division =
    { id    = { type = 8400 id = 306 }
      name  = "ARC Pijao"
      type  = submarine
      model = 2
    }
    division =
    { id    = { type = 8400 id = 307 }
      name  = "ARC Tayrona"
      type  = submarine
      model = 2
    }
  }
}
