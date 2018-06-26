
##############################
# Country definition for KYG #
##############################

country =
{ tag                 = KYG
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 20
  manpower            = 10
  capital             = 1429
  diplomacy           = { 
    relation = 
    { tag       = RUS 
     value      = 150 
     access     = yes 
     guaranteed = { day = 22 month = march year = 2003 }
    }
    relation = 
    { tag       = UZB 
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
    relation = 
    { tag       = CHC 
     value      = 150 
     access     = yes 
     guaranteed = { day = 22 month = march year = 2003 }
    }
}
  nationalprovinces   = { 1428 1429 }
  ownedprovinces      = { 1428 1429 }
  controlledprovinces = { 1428 1429 }
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
					#Army Equipment
                                        1000 1050
                                        1010
                                        1500 1510
                                        1200 1210
                                        1300 1310
                                        1400 1410
                                        1900 1910
                                        1260
                                        1960
					#Land Docs
					6600 6610
					6010 6020
					6910
					6100 6110 6120 6160 6170
					#Air Docs
					9010 9510
					9050 9060 9070
					#Secret Weapons
                                        7330 7310
					#Air Force
                                        4400 4410
                                        4100 4110
                                        4550
                                        4640 4650
                                        4700
                                        4750
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 4
    political_left    = 6
    free_market       = 7
    freedom           = 3
    professional_army = 2
    defense_lobby     = 4
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 13900 id = 1 }
    location = 1429
    name     = "I Corps"
    division =
    { id            = { type = 13900 id = 2 }
      name          = "1st Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 13900 id = 3 }
      name          = "2nd Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { experience    = 10
      id            = { type = 13900 id = 4 }
      name          = "Special Forces Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 12
    }
  }
}
