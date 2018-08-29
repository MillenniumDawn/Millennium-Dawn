
##############################
# Country definition for U13 #
##############################
province =
{ id       = 1039
    air_base = { size = 2 current_size = 2 }
}            # Asmarra

country =
{ tag                 = U13
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 800
  money               = 50
  manpower            = 15
  capital             = 1039
  transports          = 10
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1033 1038 1039 1037
                        }
  ownedprovinces      = { 1033 1038 1039
                        }
  controlledprovinces = { 1033 1038 1039
                        }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
                                        #Army Equip:
                                        2000
                                        2010
                                        2300
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
                                        1000
                                        1010
                                        1500
                                        1300 1310
                                        1400 1410
					1260
					1970 1960
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
                                        4640 4650
                                        4000 4010 4020
                                        4100 4110 4120
                                        4550
                                        4400
					#Secret Techs
                                        7330
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 2
    free_market       = 6
    freedom           = 4
    professional_army = 3
    defense_lobby     = 10
    interventionism   = 9
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12213 id = 1 }
    location = 1039
    name     = "Eritrea National Army"
    division =
    { id            = { type = 12213 id = 2 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id            = { type = 12213 id = 3 }
      name          = "23rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12213 id = 4 }
      name          = "3rd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
    division =
    { id            = { type = 12213 id = 5 }
      name          = "4th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12213 id = 6 }
      name          = "5th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12213 id = 7 }
      name          = "6th Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12213 id = 8 }
      name          = "Eritrea Operational HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 12213 id = 9 }
    location = 1033
    name     = "2nd Corps"
    division =
    { id       = { type = 12213 id = 10 }
      name     = "17th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12213 id = 11 }
      name     = "11th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12213 id = 12 }
      name     = "7th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12213 id = 13 }
      name     = "8th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12213 id = 14 }
      name     = "9th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
    division =
    { id       = { type = 12213 id = 15 }
      name     = "19th Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 12213 id = 16 }
    location = 1033
    name     = "Armored Corps"
    division =
    { id       = { type = 12213 id = 17 }
      name     = "6th Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 0
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 12213 id = 100 }
    location = 1039
    base     = 1039
    name     = "1st Wing"
    division =
    { id       = { type = 12213 id = 101 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 40
      model    = 2
    }
    division =
    { id       = { type = 12213 id = 102 }
      name     = "2nd Squadron"
      type     = multi_role
      strength = 40
      model    = 2
    }
  }
}