
##############################
# Country definition for LEB #
##############################

province =
{ id         = 1794
  air_base = { size = 2 current_size = 2 }
}              # Beirut

country =
{ tag                 = LEB
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 40
  manpower            = 10
  transports          = 44
  escorts             = 0
  capital             = 1794
  diplomacy           = {    
}
  nationalprovinces   = { 3 562 1793 1794 }
  ownedprovinces      = { 3 562 1793 1794 }
  controlledprovinces = { 3 562 1793 1794 }
  techapps            = { 
                                        #Army Equip
                                        2000 2050
                                        2010 2060
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
                                        #Army Org
                                        1000 1050
                                        1010 1060
                                        1500 1510
                                        1300 1310
                                        1900 1910
                                             1700
                                             1800
                                        1260
                                        1960
                                        #Army Doc
					6010 6020 6910
					6600 6610
					6100 6110 6120 6160
                                        #Industry
                                        5010 5110
                                        5020 5120
                                        5030 5130
                                        5040 5140
                                        5050 5150
                                        5060
                                        5070 5170
                                        5080
                                        5090 5190
                                        #Air Force
                                        4000 4010
                                        4570
                                        4640
                                        4700
                                        4750
                                        4400
                                        #Air Docs
                                        9050
                                        9060
                                        9070
                                        9090
                                        9010
                                        9510
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 6
    political_left    = 5
    free_market       = 7
    freedom           = 4
    professional_army = 3
    defense_lobby     = 5
    interventionism   = 3
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 14300 id = 1 }
    location = 1793
    name     = "I Corps"
    division =
    { id       = { type = 14300 id = 2 }
      name     = "1st Mechanized Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
    division =
    { id       = { type = 14300 id = 3 }
      name     = "2nd Mechanized Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
    division =
    { id       = { type = 14300 id = 4 }
      name     = "3rd Mechanized Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
    division =
    { id       = { type = 14300 id = 5 }
      name     = "4th Mechanized Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
    division =
    { id       = { type = 14300 id = 6 }
      name     = "5th Mechanized Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
    division =
    { id       = { type = 14300 id = 7 }
      name     = "6th Mechanized Infantry Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
  }
  landunit =
  { id       = { type = 14300 id = 8 }
    location = 1794
    name     = "Special Forces Command"
    division =
    { experience    = 5
      id       = { type = 14300 id = 9 }
      name     = "1st Republican Guard Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
    division =
    { experience    = 5
      id       = { type = 14300 id = 10 }
      name     = "1st Special Forces Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
  }
}
