
##############################
# Country definition for CYP #
##############################

province =
{ id       = 444
  air_base = { size = 1 current_size = 1 }
  naval_base = { size = 1 current_size = 1 }
}            # Cyprus

#####################
# Country main data #
#####################

country =
{ tag                 = CYP
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 8
  transports          = 30
  escorts             = 0
  capital             = 444
  diplomacy           = { }
  nationalprovinces   = { 444 940 }
  ownedprovinces      = { 444 }
  controlledprovinces = { 444 }
  techapps            = { 
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
					5110 5120 5130 5140 5150 5160 5170 5180 5190
                                        #Army Equip:
                                        2000 2050 2110
                                        2010 2060 2120
                                             2070
                                        2300 2310 2320
                                        2400 2410 2420
                                        2200 2210 2220
                                        2500 2510 2520
                                        2600 2610 2620
                                        2700 2710 2720
                                        2800 2810 2820
					#Army Org
                                        1000 1050 1110
                                        1010 1060 1120
                                             1070
                                        1500 1510 1520
                                        1300 1310 1320
                                        1260 1270
					1960
                                        1900 1910 1920
					#Land Docs
					6910 6920 6010 6020 6600 6610
					6100 6110 6120 6160
					6200 6210 6220 6260
                        }

  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 6
    free_market       = 7
    freedom           = 9
    professional_army = 5
    defense_lobby     = 3
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12221 id = 1 }
    location = 444
    name     = "Cypriot Army"
    division =
    { id            = { type = 12221 id = 2 }
      name          = "4th Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 2
    }
    division =
    { id            = { type = 12221 id = 3 }
      name          = "20th Armored Brigade"
      strength      = 100
      type          = light_armor
      model         = 8
    }
  }
}