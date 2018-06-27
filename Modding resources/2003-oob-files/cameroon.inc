
##############################
# Country definition for CAM #
##############################

country =
{ tag                 = CAM
  # Resource Reserves
  energy              = 800
  metal               = 400
  rare_materials      = 200
  oil                 = 400
  supplies            = 400
  money               = 20
  manpower            = 60
  capital             = 1077
  diplomacy           = { }
  nationalprovinces   = { 1089 1077 1088 1087 1086
                        }
  ownedprovinces      = { 1089 1077 1088 1087 1086
                        }
  controlledprovinces = { 1089 1077 1088 1087 1086
                        }
  techapps            = {
                                        #Industry:
                                        5010
                                        5020
                                        5030
                                        5040
                                        5050
                                        5070
                                        5090
                                        #Army Equip:
                                        2400 2410
                                        2200 2210
                                        2500 2510
                                        2600 2610
                                        2800 2810
                                        #Army Org:
                                        1300 1310
                                        1900 1910
                                        1260
                                        1970
                                        #Army Doc:
                                        6100
                                        6110
                                        6160
                                        6010
                                        6020
                                        6600
                                        6610
                                        6910
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 4
    political_left    = 5
    free_market       = 6
    freedom           = 3
    professional_army = 1
    defense_lobby     = 2
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 13500 id = 1 }
    location = 1077
    name     = "Cameroon National Army"
    division =
    { id            = { type = 13500 id = 2 }
      name          = "1st Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 13500 id = 3 }
      name          = "2nd Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
    division =
    { id            = { type = 13500 id = 4 }
      name          = "3rd Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
}
