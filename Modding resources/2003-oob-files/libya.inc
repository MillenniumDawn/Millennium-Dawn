
##############################
# Country definition for LBY #
##############################

province =
{ id         = 932
  naval_base = { size = 4 current_size = 4 }
    air_base = { size = 4 current_size = 4 }
}              # Tripoli

country =
{ tag                 = LBY
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 40
  manpower            = 30
  capital             = 932
  transports          = 17
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 916 917 918 919 920 921 922 923 924 925 926 927 928 929 930 931 932 933 1015 1016 1017 1018 }
  ownedprovinces      = { 916 917 918 919 920 921 922 923 924 925 926 927 928 929 930 931 932 933 1015 1016 1017 1018 }
  controlledprovinces = { 916 917 918 919 920 921 922 923 924 925 926 927 928 929 930 931 932 933 1015 1016 1017 1018 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					#Army Equipment
                                        2000 2050
                                        2010
                                        2300 2310
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
					#Army Org
					1970
                                        1000 1050
                                        1010
                                        1500
                                        1200
                                        1300 1310
                                        1400 1410
                                        1900 1910
                                        1260
					#Aircraft
					4800 4700 4750
                                        4000 4010
                                        4100 4110
                                        4500 4570
                                        4400
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
					#Air Docs
					9010 9510
					9050 9060 9070
					#Secret Weapons
					7010
					7060
                                        #Navy Techs
                                        3000
                                        3590
                                        3850
                                        #Navy Doctrines
                                        8900
                                        8950
                                        8000
                                        8500
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 3
    political_left    = 6
    free_market       = 3
    freedom           = 1
    professional_army = 3
    defense_lobby     = 3
    interventionism   = 7
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 14500 id = 1 }
    location = 932
    name     = "I Corps"
    division =
    { id            = { type = 14500 id = 2 }
      name          = "Libya HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id            = { type = 14500 id = 3 }
      name          = "1st Armored Division"
      strength      = 50
      type          = armor
      model         = 11
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { experience    = 5
      id       = { type = 14500 id = 4 }
      name     = "1st Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = police
      brigade_model = 0
    }
    division =
    { experience    = 5
      id       = { type = 14500 id = 5 }
      name     = "2nd Commando Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
      extra         = police
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 14500 id = 6 }
    location = 919
    name     = "II Corps"
    division =
    { id            = { type = 14500 id = 7 }
      name          = "1st Mechanized Division"
      strength      = 50
      type          = infantry
      model         = 0
    }
  }
  landunit =
  { id       = { type = 14500 id = 8 }
    location = 930
    name     = "III Corps"
    division =
    { id            = { type = 14500 id = 9 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 14500 id = 10 }
    location = 933
    name     = "IV Corps"
    division =
    { id            = { type = 14500 id = 11 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 14500 id = 300 }
    location = 932
    base     = 932
    name     = "Surface Fleet"
    division =
    { id    = { type = 14500 id = 301 }
      name  = "Al Hani"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 14500 id = 302 }
      name  = "1st Transport Fleet"
      type  = transport
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 14500 id = 200 }
    location = 932
    base     = 932
    name     = "Tripoli Sector"
    division =
    { id       = { type = 14500 id = 201 }
      name     = "1203rd Squadron"
      type     = interceptor
      strength = 50
      model    = 1
    }
    division =
    { id       = { type = 14500 id = 202 }
      name     = "1025th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 14500 id = 203 }
      name     = "1032nd Fighter-Bomber Squadron"
      type     = tactical_bomber
      strength = 50
      model    = 1
    }
  }
  airunit =
  { id       = { type = 14500 id = 204 }
    location = 932
    base     = 932
    name     = "Hun Sector"
    division =
    { id       = { type = 14500 id = 205 }
      name     = "1st Fighter-Bomber Squadron"
      type     = tactical_bomber
      strength = 75
      model    = 1
    }
    division =
    { id       = { type = 14500 id = 206 }
      name     = "2nd Fighter-Bomber Squadron"
      type     = tactical_bomber
      strength = 75
      model    = 1
    }
    division =
    { id       = { type = 14500 id = 207 }
      name     = "1040th Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 14500 id = 208 }
    location = 932
    base     = 932
    name     = "Tripoli Sector 2"
    division =
    { id       = { type = 14500 id = 209 }
      name     = "1055th Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 14500 id = 210 }
      name     = "1075th Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 14500 id = 211 }
      name     = "1079th Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 14500 id = 212 }
      name     = "1032nd Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
}
