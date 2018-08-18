
##############################
# Country definition for U05 #
##############################

country =
{ tag                 = U05
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 11
  capital             = 1132
  diplomacy           = { }
  nationalprovinces   = { 1132
                        }
  ownedprovinces      = { 1132
                        }
  controlledprovinces = { 1132
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
                                        2400
                                        2200
                                        2500
                                        2600
                                        2800
                                        #Army Org:
                                        1300
                                        1900
                                        1260
                                        1980
                                        #Army Doc:
                                        6100
                                        6110
                                        6160
                                        6010
                                        6020
                                        6600
                                        6610
                                        6910
                                        #Secret Tech:
                                        7330
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 8
    political_left    = 6
    free_market       = 6
    freedom           = 3
    professional_army = 1
    defense_lobby     = 2
    interventionism   = 3
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12260 id = 1 }
    location = 1132
    name     = "1st Corps"
    division =
    { id            = { type = 12260 id = 2 }
      name          = "1st Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
  }
}