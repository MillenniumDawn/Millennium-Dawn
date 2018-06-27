
##############################
# Country definition for U15 #
##############################

province =
{ id       = 1060
  air_base = { size = 2 current_size = 2 }
}            # Nairobi

country =
{ tag                 = U15
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 30
  manpower            = 50
  capital             = 1060
  transports          = 2
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1059 1060 1061
                        }
  ownedprovinces      = { 1059 1060 1061
                        }
  controlledprovinces = { 1059 1060 1061
                        }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140           5170      5190
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
                                        1260
                                        1960
					#Air Force
                                        4000 4010
                                        4640 4650
                                        4700
                                        4750
                                        4800
                                        4900
					#Air Force Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
                                        #Secret Tech:
                                        7330
					#Land Docs
					6600 6610
					6010 6020
					6910
					6100 6110 6120 6160
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 5
    free_market       = 7
    freedom           = 4
    professional_army = 3
    defense_lobby     = 3
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12207 id = 1 }
    location = 1060
    name     = "1st Corps"
    division =
    { id            = { type = 12207 id = 2 }
      name          = "1st Armor Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
    division =
    { id            = { type = 12207 id = 3 }
      name          = "2nd Armor Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
    division =
    { id            = { type = 12207 id = 4 }
      name          = "1st Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 12207 id = 5 }
    location = 1059
    name     = "2nd Corps"
    division =
    { id            = { type = 12207 id = 6 }
      name          = "4th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12207 id = 7 }
      name          = "2nd Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12207 id = 8 }
      name          = "6th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 12207 id = 100 }
    location = 1060
    base     = 1060
    name     = "1st Wing"
    division =
    { id       = { type = 12207 id = 101 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 50
      model    = 1
    }
  }
}
