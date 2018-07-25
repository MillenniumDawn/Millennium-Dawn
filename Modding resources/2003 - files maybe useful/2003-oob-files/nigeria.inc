
##############################
# Country definition for NIG #
##############################

province =
{ id       = 1008
  naval_base = { size = 2 current_size = 2 }
}            # Lagos

province =
{ id       = 1009
    air_base = { size = 4 current_size = 4 }
}            # Kaduna

country =
{ tag                 = NIG
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 60
  manpower            = 180
  transports          = 46
  escorts             = 0
  capital             = 1009
  diplomacy           = { }
  nationalprovinces   = { 999 1007 1008 1009 1010 1011 1012 1085 1145 }
  ownedprovinces      = { 999 1007 1008 1009 1010 1011 1012 1085 1145 }
  controlledprovinces = { 999 1007 1008 1009 1010 1011 1012 1085 1145 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
                                        #Army Equip:
                                        2000
                                        2010
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
                                        1000
                                        1010
                                        1500 1510
                                        1200 1210
                                        1300 1310
                                        1400 1410
                                                  1600
                                                  1650
                                             1700
                                             1800
					1260
					1980
					1900 1910
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9090
                                        9010
                                        9510
					#Air techs
                                        4700
                                        4750
                                        4640
                                        4570
                                        4000 4010
					#Secret Techs
                                        7330
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
                                        #Navy Techs
                                        3100 3110
                                        3590
                                        3850 3860
                                        #Navy Doctrines
                                        8900
                                        8950
                                        8000
                                        8500
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 7
    political_left    = 5
    free_market       = 6
    freedom           = 4
    professional_army = 10
    defense_lobby     = 2
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 16900 id = 1 }
    location = 1009
    name     = "1st Mechanized Force"
    division =
    { id            = { type = 16900 id = 2 }
      name          = "1st Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
  landunit =
  { id       = { type = 16900 id = 3 }
    location = 1008
    name     = "2nd Mechanized Force"
    division =
    { id            = { type = 16900 id = 4 }
      name          = "2nd Mechanized Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id       = { type = 16900 id = 5 }
      name     = "3rd Armored Division"
      strength = 100
      type     = armor
      model    = 8
    }
    division =
    { id       = { type = 16900 id = 6 }
      name     = "81st Marine Division"
      strength = 100
      type     = marine
      model    = 16
    }
  }
  landunit =
  { id       = { type = 16900 id = 7 }
    location = 1010
    name     = "82nd Airborne Division"
    division =
    { experience    = 5
      id       = { type = 16900 id = 8 }
      name     = "1st Brigade - 82nd Airborne Division"
      strength = 100
      type     = bergsjaeger
      model    = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 5
      id       = { type = 16900 id = 9 }
      name     = "2nd Brigade - 82nd Airborne Division"
      strength = 100
      type     = bergsjaeger
      model    = 13
      extra         = engineer
      brigade_model = 0
    }
    division =
    { experience    = 5
      id       = { type = 16900 id = 10 }
      name     = "3rd Brigade - 82nd Airborne Division"
      strength = 100
      type     = bergsjaeger
      model    = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 16900 id = 300 }
    location = 1008
    base     = 1008
    name     = "Nigerian Navy"
    division =
    { id       = { type = 16900 id = 301 }
      name     = "NNS Ekum"
      type     = light_cruiser
      strength = 100
      model    = 1
    }
    division =
    { id    = { type = 16900 id = 302 }
      name  = "1st Transport Flotilla"
      type  = transport
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 16900 id = 200 }
    location = 1009
    base     = 1009
    name     = "1st Air Force"
    division =
    { id       = { type = 16900 id = 201 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 16900 id = 202 }
      name     = "2nd Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
}
