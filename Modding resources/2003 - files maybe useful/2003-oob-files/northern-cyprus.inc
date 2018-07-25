
##############################
# Country definition for ARA #
##############################

#####################
# Country main data #
#####################

country =
{ tag                 = ARA
  control             = TUR
  puppet              = TUR
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 8
  transports          = 20
  escorts             = 0
  capital             = 940
  diplomacy           = { }
  nationalprovinces   = { 940 }
  ownedprovinces      = { 940 }
  controlledprovinces = { 940 }
  techapps            = { 
                                        #Industry:
                                        5010 5110
                                        5020 5120
                                        5030 5130
                                        5040 5140
                                        5050 5150
                                        5060 5160
                                        5070 5170
                                        5080 5180
                                        5090 5190
                                        #Army Equipment:
                                        2400 2410
                                        2200 2210 2220
                                        2500 2510
                                        2600 2610
                                        2700 2710
                                        2800 2810
                                        #Army Organisation:
                                        1500 1510
                                        1300 1310
                                        1900 1910
                                        1260 1270
                                        1960
					#Land Docs
					6930 6010 6020 6600 6610
					6100 6110 6120 6160
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
  { id       = { type = 12280 id = 1 }
    location = 940
    name     = "Turkish Cypriot Security Force"
    division =
    { id            = { type = 12280 id = 2 }
      name          = "1st Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
}
