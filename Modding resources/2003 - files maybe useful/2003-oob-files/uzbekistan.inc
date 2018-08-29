
##############################
# Country definition for UZB #
##############################

province =
{ id       = 1427
  air_base = { size = 2 current_size = 2 }
}            # Tashkent

country =
{ tag                 = UZB
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 30
  manpower            = 46
  capital             = 1427
  diplomacy           = {  
   
    relation = 
    { tag       = RUS 
     value      = 150 
     access     = yes 
     guaranteed = { day = 22 month = march year = 2003 }
    }
    relation = 
    { tag       = CHC 
     value      = 150 
     access     = yes 
     guaranteed = { day = 22 month = march year = 2003 }
    }
    relation = 
    { tag       = KYG 
     value      = 150 
     access     = yes 
     guaranteed = { day = 22 month = march year = 2003 }
    }
    relation = 
    { tag       = KAZ 
     value      = 150 
     access     = yes 
     guaranteed = { day = 22 month = march year = 2003 }
    }
}
  nationalprovinces   = { 1427 1487 1488 1489 1584 1585 }
  ownedprovinces      = { 1427 1487 1488 1489 1584 1585 }
  controlledprovinces = { 1427 1487 1488 1489 1584 1585 }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
					#Army Equipment
                                        2000 2050
                                        2010 2060
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Equipment
                                        1000 1050
                                        1010 1060
                                        1500 1510 1520
                                        1200 1210 1220
                                        1300 1310 1320
                                        1400 1410 1420
                                        1900 1910 1920
                                        1260 1270
                                        1970
					#Land Docs
					6600 6610
					6010 6020
					6910
					6100 6110 6120 6160 6170
					6200 6210 6220 6260 6270
					#Air Docs
					9010 9510
					9050 9060 9070
					9150 9160 9170
					#Secret Weapons
                                        7330 7310
					#Air Force
                                        4400 4410
                                        4000 4010 4020
                                        4550
                                        4500 4510
                                        4640 4650
                                        4700 4710
                                        4750 4760
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 2
    political_left    = 4
    free_market       = 3
    freedom           = 2
    professional_army = 3
    defense_lobby     = 1
    interventionism   = 5
  }
  # ####################################
  # ARMY
  # ####################################
  landunit =
  { id       = { type = 22600 id = 1 }
    location = 1427
    name     = "I Corps"
    division =
    { id            = { type = 22600 id = 2 }
      name          = "17th Air Assault Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
    division =
    { id            = { type = 22600 id = 3 }
      name          = "Uzbek Army HQ"
      strength      = 100
      type          = hq
      model         = 0
      extra         = heavy_armor
      brigade_model = 1
    }
  }
  landunit =
  { id       = { type = 22600 id = 4 }
    location = 1584
    name     = "III Corps"
    division =
    { id            = { type = 22600 id = 5 }
      name          = "1st Motor Rifle Brigade"
      strength      = 100
      type          = mechanized
      model         = 2
    }
    division =
    { id            = { type = 22600 id = 6 }
      name          = "2nd Motor Rifle Brigade"
      strength      = 100
      type          = mechanized
      model         = 2
    }
    division =
    { id            = { type = 22600 id = 7 }
      name          = "3rd Motor Rifle Brigade"
      strength      = 100
      type          = mechanized
      model         = 2
    }
    division =
    { id            = { type = 22600 id = 8 }
      name          = "4th Motor Rifle Brigade"
      strength      = 100
      type          = mechanized
      model         = 2
    }
    division =
    { id            = { type = 22600 id = 9 }
      name          = "5th Motor Rifle Brigade"
      strength      = 100
      type          = mechanized
      model         = 2
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 22600 id = 100 }
    location = 1427
    base     = 1427
    name     = "1st Air Force"
    division =
    { id       = { type = 22600 id = 101 }
      name     = "1st Squadron"
      type     = cas
      strength = 100
      model    = 0
    }
    division =
    { id       = { type = 22600 id = 102 }
      name     = "2nd Squadron"
      type     = interceptor
      strength = 100
      model    = 2
    }
  }
}
