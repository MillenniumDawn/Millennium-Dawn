
##############################
# Country definition for SAU #
##############################

province =
{ id       = 1808
  naval_base = { size = 2 current_size = 2 }
}            # Jiddah

province =
{ id       = 1821
  naval_base = { size = 4 current_size = 4 }
}            # Dammam

province =
{ id       = 1807
    air_base = { size = 10 current_size = 10 }
}            # Riyadh

country =
{ tag                 = SAU
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 300
  capital             = 1807
  manpower            = 60
  transports          = 64
  escorts             = 0
  diplomacy           = { 
relation = { tag = ISR value = -100 }
relation = { tag = USA value = 150 }
relation = { tag = U16 value = 180 }
}
  nationalprovinces   = { 1821 1818 1809 1808 1807 1805 1804 }
  ownedprovinces      = { 1821 1818 1809 1808 1807 1805 1804 }
  controlledprovinces = { 1821 1818 1809 1808 1807 1805 1804 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					5210 5220 5230 5240 5250 5260 5270 5280 5290
                                        #Army Equipment:
                                        2000 2050 2110
                                        2010      2120
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
                                        #Army Organisation:
                                        1000 1050 1110
                                        1010      1120
                                        1500 1510 1520
                                        1200 1210
                                        1300 1310 1320
                                        1400 1410
                                        1700 1710
                                        1800 1810
                                        1900 1910 1920
                                        1260 1270
                                        1970
					#Aircraft
                                        4700 4710 4720
                                        4750 4760 4770
                                        4800 4810
                                        4900 4910
                                        4000 4010
                                        4100 4110 4120 4130
                                        4500 4510 4520
                                        4570
                                        4400 4410
                                        4640 4650 4660
					#Land Docs
					6930
					6010 6020
					6600 6610
					6100 6110 6120 6140 6150 6160 6170
					6200 6210 6220 6240 6250 6260 6270
					#Air Docs
					9040
                                        9510 9520 9530 9540
                                        9050 9130
                                        9060 9140
                                        9070 9150
                                        9100 9180
                                        9120 9200
                                        #Navy Techs
                                        3000 3010 3020 3030
                                        3590
                                        3850 3860 3870 3880
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8000 8010
                                        8500 8510
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 1
    political_left    = 1
    free_market       = 6
    freedom           = 1
    professional_army = 10
    defense_lobby     = 8
    interventionism   = 3
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 18900 id = 1 }
    location = 1804
    name     = "I Corps"
    division =
    { id       = { type = 18900 id = 2 }
      name     = "4th Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 7
    }
    division =
    { id       = { type = 18900 id = 3 }
      name     = "8th Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 7
    }
    division =
    { id       = { type = 18900 id = 4 }
      name     = "12th Armored Brigade"
      strength = 100
      type     = light_armor
      model    = 8
    }
  }
  landunit =
  { id       = { type = 18900 id = 5 }
    location = 1809
    name     = "II Corps"
    division =
    { id       = { type = 18900 id = 6 }
      name     = "6th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 18900 id = 7 }
      name     = "8th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 18900 id = 8 }
      name     = "10th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 18900 id = 9 }
      name     = "11th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 18900 id = 10 }
      name     = "20th Mechanized Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
  }
  landunit =
  { id       = { type = 18900 id = 11 }
    location = 1821
    name     = "III Corps"
    division =
    { id       = { type = 18900 id = 12 }
      name          = "Saudi Army HQ"
      strength      = 100
      type          = hq
      model         = 1
      extra         = heavy_armor
      brigade_model = 2
    }
    division =
    { id            = { type = 18900 id = 13 }
      name          = "1st Airborne Brigade"
      strength      = 100
      type          = militia
      model         = 2      
    }
    division =
    { experience    = 10
      id            = { type = 18900 id = 14 }
      name          = "Royal Guard Regiment"
      strength      = 100
      type          = bergsjaeger
      model         = 13
      extra         = engineer
      brigade_model = 0
    }
  }
  landunit =
  { id       = { type = 18900 id = 15 }
    location = 1809
    name     = "National Guard"
    division =
    { id       = { type = 18900 id = 16 }
      name     = "1st Motorized Division"
      strength = 100
      type     = motorized
      model    = 1
      extra         = heavy_armor
      brigade_model = 1
    }
    division =
    { id       = { type = 18900 id = 17 }
      name     = "2nd Motorized Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 18900 id = 18 }
      name     = "3rd Motorized Division"
      strength = 100
      type     = motorized
      model    = 1
    }
    division =
    { id       = { type = 18900 id = 19 }
      name     = "4th Motorized Division"
      strength = 100
      type     = motorized
      model    = 1
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 18900 id = 300 }
    location = 1808
    base     = 1808
    name     = "Red Sea Fleet"
    division =
    { id    = { type = 18900 id = 303 }
      name  = "HMS Hofouf"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18900 id = 304 }
      name  = "HMS Abha"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18900 id = 305 }
      name  = "HMS Taif"
      type  = destroyer
      model = 1
    }
  }
  navalunit =
  { id       = { type = 18900 id = 306 }
    location = 1821
    base     = 1821
    name     = "Persian Gulf Fleet"
    division =
    { id    = { type = 18900 id = 301 }
      name  = "HMS Arriyad"
      type  = destroyer
      model = 1
    }
    division =
    { id    = { type = 18900 id = 302 }
      name  = "HMS Al Madinah"
      type  = destroyer
      model = 1
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 18900 id = 200 }
    location = 1807
    base     = 1807
    name     = "2nd Wing"
    division =
    { id       = { type = 18900 id = 201 }
      name     = "11th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18900 id = 202 }
      name     = "14th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18900 id = 203 }
      name     = "8th Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
    division =
    { id       = { type = 18900 id = 204 }
      name     = "3rd Squadron"
      type     = interceptor
      strength = 100
      model    = 1
    }
  }
  airunit =
  { id       = { type = 18900 id = 205 }
    location = 1807
    base     = 1807
    name     = "3rd Wing"
    division =
    { id       = { type = 18900 id = 206 }
      name     = "5th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 18900 id = 207 }
      name     = "21st Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 18900 id = 208 }
      name     = "18th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 18900 id = 209 }
      name     = "10th Squadron"
      type     = tactical_bomber
      strength = 100
      model    = 3
    }
  }
  airunit =
  { id       = { type = 18900 id = 210 }
    location = 1807
    base     = 1807
    name     = "5th Wing"
    division =
    { id       = { type = 18900 id = 211 }
      name     = "1st Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18900 id = 212 }
      name     = "27th Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
    division =
    { id       = { type = 18900 id = 213 }
      name     = "22nd Squadron"
      type     = multi_role
      strength = 100
      model    = 2
    }
  }
  airunit =
  { id       = { type = 18900 id = 214 }
    location = 1807
    base     = 1807
    name     = "4th Wing"
    division =
    { id       = { type = 18900 id = 215 }
      name     = "19th Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 18900 id = 216 }
      name     = "12th Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
    division =
    { id       = { type = 18900 id = 217 }
      name     = "7th Squadron"
      type     = multi_role
      strength = 100
      model    = 3
    }
  }
  # ###################################
  # Under Development
  # ###################################
  division_development =
  { id    = { type = 18900 id = 400 }
    name  = "HMS Makkah"
    type  = destroyer
    model = 3
    cost  = 5
    date  = { day = 17 month = august year = 2003 }
  }
}
