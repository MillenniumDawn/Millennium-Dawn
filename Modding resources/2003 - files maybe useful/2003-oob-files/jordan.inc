
##############################
# Country definition for JOR #
##############################

province =
{ id       = 1796
    air_base = { size = 4 current_size = 4 }
}            # Amman

country =
{ tag                 = JOR
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 13
  capital             = 1796
  diplomacy           = { }
  nationalprovinces   = { 537 1796 1802 1803 407 1892 1893 1894 }
  ownedprovinces      = { 537 1796 1802 1803 407 1892 1893 1894 }
  controlledprovinces = { 537 1796 1802 1803 407 1892 1893 1894 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
                                        #Army Equip:
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
					1260
					1970
					1900 1910
					#Air Docs
                                        9050 9060
                                        9060
                                        9070
                                        9010
                                        9510
					#Air techs
                                        4700 4710 4720
                                        4750 4760 4770
                                        4640 4650
                                        4570
                                        4000 4010 4020 4030
					#Secret Techs
                                        7330 7310
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
					6200 6210 6220
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 5
    political_left    = 5
    free_market       = 7
    freedom           = 3
    professional_army = 8
    defense_lobby     = 8
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 13300 id = 1 }
    location = 1796
    name     = "I Corps"
    division =
    { id       = { type = 13300 id = 2 }
      name     = "1st Armored Division"
      strength = 100
      type     = armor
      model    = 11
    }
    division =
    { id       = { type = 13300 id = 3 }
      name     = "2nd Armored Division"
      strength = 100
      type     = armor
      model    = 11
    }
    division =
    { id       = { type = 13300 id = 4 }
      name     = "1st Mechanized Division"
      strength = 100
      type     = infantry
      model    = 1
    }
    division =
    { id       = { type = 13300 id = 5 }
      name     = "2nd Mechanized Division"
      strength = 100
      type     = infantry
      model    = 1
    }
  }
  landunit =
  { id       = { type = 13300 id = 6 }
    location = 1802
    name     = "II Corps"
    division =
    { id       = { type = 13300 id = 7 }
      name     = "3rd Mechanized Division"
      strength = 100
      type     = infantry
      model    = 1
    }
    division =
    { id       = { type = 13300 id = 8 }
      name     = "1st Motorized Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 13300 id = 200 }
    location = 1796
    base     = 1796
    name     = "1st Air Force"
    division =
    { id       = { type = 13300 id = 201 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 75
      model    = 1
    }
    division =
    { id       = { type = 13300 id = 202 }
      name     = "6th Squadron"
      type     = interceptor
      strength = 75
      model    = 1
    }
    division =
    { id       = { type = 13300 id = 203 }
      name     = "7th Squadron"
      type     = interceptor
      strength = 75
      model    = 1
    }
  }
  airunit =
  { id       = { type = 13300 id = 204 }
    location = 1796
    base     = 1796
    name     = "2nd Air Force"
    division =
    { id       = { type = 13300 id = 205 }
      name     = "17th Squadron"
      type     = interceptor
      strength = 50
      model    = 2
    }
    division =
    { id       = { type = 13300 id = 206 }
      name     = "9th Squadron"
      type     = interceptor
      strength = 50
      model    = 2
    }
    division =
    { id       = { type = 13300 id = 207 }
      name     = "9th Squadron"
      type     = interceptor
      strength = 100
      model    = 3
    }
  }
}
