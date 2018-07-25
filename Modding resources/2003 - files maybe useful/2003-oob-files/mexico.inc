
##############################
# Country definition for MEX #
##############################

province =
{ id         = 756
  naval_base = { size = 4 current_size = 4 }
   air_base = { size = 2 current_size = 2 }
}              # Merida

province =
{ id         = 743
  naval_base = { size = 4 current_size = 4 }
}              # Culiacàn

province =
{ id       = 744
  air_base = { size = 4 current_size = 4 }
}            # Durango

country =
{ tag                 = MEX
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 60
  capital             = 752
  transports          = 57
  escorts             = 0
  manpower            = 150
  diplomacy           = { }
  nationalprovinces   = { 756 755 754 753 752 751 750 747 749 745 742 741 744 743 740 739 737 738 }
  ownedprovinces      = { 756 755 754 753 752 751 750 747 749 745 742 741 744 743 740 739 737 738 }
  controlledprovinces = { 756 755 754 753 752 751 750 747 749 745 742 741 744 743 740 739 737 738 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equip
                                        2000 2050 2110
                                        2010 2060
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Org
					1970 1980
                                        1000 1050 1110
                                        1010 1060
                                        1500 1510 1520
                                        1200 1210 1220
                                        1300 1310 1320
                                        1400 1410 1420
                                             1700
                                             1800 1810
                                        1900 1910 1920
                                        1260 1270
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
                                        6200 6210 6220      6250 6260
					#Secret Weapons
					7010 7060 7070
					7180
                                        7330 7310
					#Air Force
                                        4570
                                        4000 4010
                                        4400 4410
                                        4640 4650
                                        4700 4710
                                        4750 4760
                                        4800 4810
                                        4900 4910
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9090
                                        9120
                                        9510 9520 9020
                                        #Navy Techs
                                        3000
                                        3100
                                        3590
                                        3850 3860
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8000 8010
                                        8500 8510
                                        8100 8110
                                        8600 8610
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 4
    free_market       = 7
    freedom           = 8
    professional_army = 3
    defense_lobby     = 1
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 15600 id = 1 }
    location = 752
    name     = "I Corps"
    division =
    { id            = { type = 15600 id = 2 }
      name          = "1st Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 4
    }
    division =
    { id            = { type = 15600 id = 3 }
      name          = "1st Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id       = { type = 15600 id = 4 }
      name     = "2nd Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id       = { type = 15600 id = 6 }
      name     = "5th Airborne Brigade"
      strength = 100
      type     = paratrooper
      model    = 14
    }
    division =
    { id       = { type = 15600 id = 7 }
      name     = "Presidential Guard Brigade"
      strength = 100
      type     = bergsjaeger
      model    = 12
    }
  }
  landunit =
  { id       = { type = 15600 id = 8 }
    location = 749
    name     = "II Corps"
    division =
    { id       = { type = 15600 id = 9 }
      name     = "1st Armored Cavalry Regiment"
      strength = 100
      type     = light_armor
      model    = 3
    }
  }
  landunit =
  { id       = { type = 15600 id = 10 }
    location = 738
    name     = "III Corps"
    division =
    { id       = { type = 15600 id = 11 }
      name     = "1st Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
  }
  landunit =
  { id       = { type = 15600 id = 12 }
    location = 754
    name     = "V Corps"
    division =
    { id       = { type = 15600 id = 13 }
      name     = "3rd Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
    division =
    { id       = { type = 15600 id = 14 }
      name     = "2nd Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 0
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 15600 id = 300 }
    location = 756
    base     = 756
    name     = "1st Fleet"
    division =
    { id    = { type = 15600 id = 301 }
      name  = "ARM Allende"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 15600 id = 302 }
      name  = "ARM Abasolo"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 15600 id = 303 }
      name  = "ARM Netzahualcoyotl"
      type  = light_cruiser
      model = 0
    }
  }
  navalunit =
  { id       = { type = 15600 id = 304 }
    location = 743
    base     = 743
    name     = "2nd Fleet"
    division =
    { id    = { type = 15600 id = 305 }
      name  = "ARM Victoria"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 15600 id = 306 }
      name  = "ARM Bravo"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 15600 id = 307 }
      name  = "ARM Galeana"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 15600 id = 308 }
      name  = "ARM Manuel Azueta"
      type  = light_cruiser
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 15600 id = 200 }
    location = 744
    base     = 744
    name     = "1st Wing"
    division =
    { id       = { type = 15600 id = 201 }
      name     = "1st Air Transport Squadron"
      type     = transport_plane
      strength = 100
      model    = 0
    }
  }
  airunit =
  { id       = { type = 15600 id = 202 }
    location = 756
    base     = 756
    name     = "2nd Wing"
    division =
    { id       = { type = 15600 id = 203 }
      name     = "401st Air Squadron"
      type     = interceptor
      strength = 40
      model    = 1
    }
    division =
    { id       = { type = 15600 id = 204 }
      name     = "402nd Air Squadron"
      type     = tactical_bomber
      strength = 70
      model    = 0
    }
  }
}
