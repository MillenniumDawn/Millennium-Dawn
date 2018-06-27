
##############################
# Country definition for ALS #
##############################

country =
{ tag                 = ALS
  regular_id          = RUS
  # Resource Reserves
  energy              = 1200
  metal               = 300
  rare_materials      = 300
  oil                 = 300
  supplies            = 500
  money               = 10
  manpower            = 6
  capital             = 1845
  diplomacy           = { }
  nationalprovinces   = { 1845 }
  ownedprovinces      = { 1845 }
  controlledprovinces = { 1845 }
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
                                        1300 1310
                                        1900 1910
                                        1260 1270
                                        1960
                                        #Army Doctrines:
                                        6100 6200
                                        6110 6210
                                        6160 6260
                                        6010
                                        6020
                                        6910
                                        6600
                                        6610
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 4
    free_market       = 7
    freedom           = 5
    professional_army = 4
    defense_lobby     = 6
    interventionism   = 1
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12286 id = 1 }
    location = 1845
    name     = "Abkhazian Self Defence Forces"
    division =
    { id       = { type = 12286 id = 2 }
      name     = "1st Guards Rifle Brigade"
      strength = 100
      type     = cavalry
      model    = 2
    }
    division =
    { id       = { type = 12286 id = 3 }
      name     = "4th Rifle Brigade"
      strength = 100
      type     = mechanized
      model    = 1
    }
  }
}