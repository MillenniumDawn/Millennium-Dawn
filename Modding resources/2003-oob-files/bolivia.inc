
##############################
# Country definition for BOL #
##############################

province =
{ id       = 832
  air_base = { size = 1 current_size = 1 }
}            # La Paz

country =
{ tag                 = BOL
  manpower            = 23
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 20
  capital             = 838
  diplomacy           = { }
  nationalprovinces   = { 836 833 838 832 828 827 839 }
  ownedprovinces      = { 836 833 838 832 828 827 }
  controlledprovinces = { 836 833 838 832 828 827 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
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
					1260
					1960
                                        1500 1510
                                        1300 1310
                                        1900 1910
                                        1000 1050
                                        1010 1060
					#Land Docs
					6100 6110 6120 6910 6600 6610
					6010 6020
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
					#Air Force
                                        4570
                                        4750
                                        4700
                                        4640

                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 9
    political_left    = 5
    free_market       = 7
    freedom           = 7
    professional_army = 5
    defense_lobby     = 3
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 6800 id = 1 }
    location = 832
    name     = "I Corps"
    division =
    { id            = { type = 6800 id = 2 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = infantry
      model         = 0      
    }
    division =
    { id            = { type = 6800 id = 3 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = infantry
      model         = 0      
    }
  }
}
