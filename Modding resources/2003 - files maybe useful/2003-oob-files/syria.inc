
##############################
# Country definition for SYR #
##############################

province =
{ id       = 1862
  naval_base = { size = 4 current_size = 4 }
}            # Aleppo

province =
{ id       = 1863
    air_base = { size = 10 current_size = 10 }
}            # Hims

country =
{ tag                 = SYR
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 34
  capital             = 1792
  transports          = 120
  escorts             = 0
  diplomacy           = {     
    relation = 
    { tag        = LEB 
      value      = 120
       access    = yes 
      guaranteed = { day = 22 month = march year = 2003 }
    }
}
  nationalprovinces   = { 941 241 505 1899 1792 1861 1862 1863 1795 }
  ownedprovinces      = { 941 241 505 1899 1792 1861 1862 1863 }
  controlledprovinces = { 941 241 505 1899 1792 1861 1862 1863 }
  techapps            = {
                                        #Navy Techs
                                        3000
                                        3700
                                        3590
                                        3850
                                        #Navy Doctrines
                                        8900
                                        8950
                                        8400
                                        8000
                                        8500
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
                                        #Army Org
                                        1000 1050
                                        1010
                                        1500 1510
                                        1200 1210
                                        1300 1310
                                        1400 1410
                                        1900 1910
                                        1260
                                        1970
                                        #Army Doc
                                        6100
                                        6110
                                        6120
                                        6160
                                        6170
                                        6010
                                        6020
                                        6910
                                        6600
                                        6630
                                        #Industry
                                        5010
                                        5020
                                        5030
                                        5040
                                        5050
                                        5060
                                        5070
                                        5080
                                        5090
                                        #Air Force
                                        4000 4010 4020
                                        4100 4110
                                        4570
                                        4550
                                        4640 4650
                                        4700 4710
                                        4750 4760
                                        4900
                                        #Air Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510

                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 1
    political_left    = 4
    free_market       = 4
    freedom           = 1
    professional_army = 1
    defense_lobby     = 7
    interventionism   = 8
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 20900 id = 1 }
    location = 1792
    name     = "I Corps"
    division =
    { id            = { type = 20900 id = 2 }
      name          = "I Corps HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = sp_rct_artillery
      brigade_model = 2
    }
    division =
    { id            = { type = 20900 id = 3 }
      name          = "1st Armored Division"
      strength      = 100
      type          = armor
      model         = 11
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 20900 id = 4 }
      name          = "3rd Armored Division"
      strength      = 100
      type          = armor
      model         = 8
    }
    division =
    { id            = { type = 20900 id = 5 }
      name          = "5th Armored Division"
      strength      = 100
      type          = armor
      model         = 8
    }
    division =
    { id            = { type = 20900 id = 6 }
      name          = "4th Mechanized Division"
      strength      = 50
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 20900 id = 7 }
      name          = "1st Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 20900 id = 8 }
      name          = "2nd Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 20900 id = 9 }
      name          = "Republican Guard Division"
      strength      = 100
      type          = armor
      model         = 11
      extra         = heavy_armor
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 20900 id = 10 }
    location = 1862
    name     = "II Corps"
    division =
    { id            = { type = 20900 id = 11 }
      name          = "6th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 0
    }
    division =
    { id            = { type = 20900 id = 12 }
      name          = "8th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 1
    }
    division =
    { id            = { type = 20900 id = 13 }
      name          = "10th Mechanized Division"
      strength      = 50
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 20900 id = 14 }
      name          = "3rd Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  landunit =
  { id       = { type = 20900 id = 15 }
    location = 1794
    name     = "Lebanon Force"
    division =
    { id            = { type = 20900 id = 16 }
      name          = "1st Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = police
      brigade_model = 0
    }
    division =
    { id            = { type = 20900 id = 17 }
      name          = "2nd Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = police
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 20900 id = 18 }
    location = 1792
    name     = "Special Forces Command"
    division =
    { id            = { type = 20900 id = 19 }
      name          = "3rd Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = engineer
      brigade_model = 0
    }
    division =
    { id            = { type = 20900 id = 20 }
      name          = "4th Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = police
      brigade_model = 0
    }
    division =
    { id            = { type = 20900 id = 21 }
      name          = "5th Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
      extra         = police
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 20900 id = 22 }
    location = 1792
    name     = "III Corps"
    division =
    { id       = { type = 20900 id = 23 }
      name     = "9th Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 3
    }
    division =
    { id       = { type = 20900 id = 24 }
      name     = "11th Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 3
    }
    division =
    { id       = { type = 20900 id = 25 }
      name     = "7th Mechanized Division"
      strength = 50
      type     = infantry
      model    = 0
    }
    division =
    { id            = { type = 20900 id = 26 }
      name          = "4th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 20900 id = 300 }
    location = 1862
    base     = 1862
    name     = "Syrian Navy"
    division =
    { id    = { type = 20900 id = 301 }
      name  = "Al Hirasa"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 20900 id = 302 }
      name  = "1-580"
      type  = destroyer
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 20900 id = 200 }
    location = 1863
    base     = 1863
    name     = "1st Wing"
    division =
    { id       = { type = 20900 id = 201 }
      name     = "980th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20900 id = 202 }
      name     = "12th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20900 id = 203 }
      name     = "8th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 20900 id = 204 }
    location = 1863
    base     = 1863
    name     = "68th Wing"
    division =
    { id       = { type = 20900 id = 205 }
      name     = "819th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 20900 id = 206 }
      name     = "685th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 20900 id = 207 }
      name     = "677th Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 20900 id = 208 }
    location = 1863
    base     = 1863
    name     = "64th Wing"
    division =
    { id       = { type = 20900 id = 209 }
      name     = "945th Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20900 id = 210 }
      name     = "77th Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20900 id = 211 }
      name     = "54th Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20900 id = 212 }
      name     = "827th Squadron"
      type     = multi_role
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 20900 id = 213 }
    location = 1863
    base     = 1863
    name     = "4th Wing"
    division =
    { id       = { type = 20900 id = 214 }
      name     = "943rd Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20900 id = 215 }
      name     = "946th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20900 id = 216 }
      name     = "698th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 20900 id = 217 }
      name     = "695th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 20900 id = 218 }
    location = 1863
    base     = 1863
    name     = "17th Wing"
    division =
    { id       = { type = 20900 id = 219 }
      name     = "5th Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 20900 id = 220 }
      name     = "699th Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
}
