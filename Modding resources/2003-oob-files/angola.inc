
##############################
# Country definition for ANG #
##############################

province =
{ id       = 1096
  air_base = { size = 4 current_size = 4 }
  naval_base = { size = 2 current_size = 2 }
}            # Luanda

country =
{ tag                 = ANG
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 40
  transports          = 60
  escorts             = 0
  capital             = 1096
  diplomacy           = { 
    relation = { tag = CHC value = 150 } }

  nationalprovinces   = { 1094 1096 1097 1100 1101 1102 1103
                        }
  ownedprovinces      = { 1094 1096 1097 1100 1101 1102 1103
                        }
  controlledprovinces = { 1094 1096 1097 1100 1101 1102 1103
                        }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					#Army Org
                                        1000 1050
                                        1010
                                        1500 1510
                                        1300 1310
                                        1400 1410
                                             1700
                                             1800
                                        1900 1910
                                        1260
                                        1200
					1980
					#Army Equip
                                        2000 2050
                                        2010
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Land Docs
					6100 6910 6600 6610 6010 6020
                                        6140
                                        6150
                                        6170
                                        #Air Docs
                                        9510 9010
                                        9050
                                        9060
                                        9070
                                        9090
                                        #Air Techs
                                        4000 4010
                                        4100 4110 4120
                                        4550
                                        4400
                                        4700 4710
                                        4750 4760
                                        #Secret Techs
                                        7330

                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 4
    political_left    = 8
    free_market       = 4
    freedom           = 3
    professional_army = 1
    defense_lobby     = 6
    interventionism   = 7
  }
  # #####################################
  # ARMY
  # #####################################
 landunit =
  { id       = { type = 12201 id = 1 }
    location = 1096
    name     = "Angolan Army Command"
    division =
    { id            = { type = 12201 id = 2 }
      name          = "1st Angolan Army HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 1
      experience    = 25
    }
  }
  landunit =
  { id       = { type = 12201 id = 3 }
    location = 1096
    name     = "1st Mechanized Corps"
    division =
    { id            = { type = 12201 id = 4 }
      name          = "1st Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 1
      experience    = 25
    }
    division =
    { id            = { type = 12201 id = 5 }
      name          = "6th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
      experience    = 25
    }
    division =
    { id            = { type = 12201 id = 6 }
      name          = "7th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 3
      experience    = 25
    }
    division =
    { id            = { type = 12201 id = 7 }
      name          = "3rd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
      extra         = heavy_armor
      brigade_model = 1
      experience    = 25
    }
}
 landunit =
  { id       = { type = 12201 id = 8 }
    location = 1094
    name     = "1st Corps"
    division =
    { id            = { type = 12201 id = 9 }
      name          = "3rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12201 id = 10 }
      name          = "4th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12201 id = 11 }
      name          = "5th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12201 id = 12 }
      name          = "23rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12201 id = 13 }
      name          = "11th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12201 id = 14 }
      name          = "8th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  # #####################################
  # NAVY
  # #####################################
  navalunit =
  { id       = { type = 12201 id = 200 }
    location = 1096
    base     = 1096
    name     = "Amphibious Fleet"
    division =
    { id    = { type = 12201 id = 201 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 12201 id = 100 }
    location = 1096
    base     = 1096
    name     = "1st Wing"
    division =
    { id       = { type = 12201 id = 102 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 12201 id = 103 }
      name     = "2nd Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 12201 id = 104 }
    location = 1096
    base     = 1096
    name     = "2nd Wing"
    division =
    { id       = { type = 12201 id = 105 }
      name     = "3rd Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 12201 id = 106 }
      name     = "4th Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 12201 id = 107 }
      name     = "5th Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
}