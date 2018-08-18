
##############################
# Country definition for GAB #
##############################

country =
{ tag                 = GAB
  control             = FRA
  puppet              = FRA
  # Resource Reserves
  energy              = 800
  metal               = 400
  rare_materials      = 200
  oil                 = 400
  supplies            = 400
  money               = 10
  manpower            = 9
  capital             = 1092
  diplomacy           = { }
  nationalprovinces   = { 1092
                        }
  ownedprovinces      = { 1092
                        }
  controlledprovinces = { 1092
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
    democratic        = 4
    political_left    = 5
    free_market       = 5
    freedom           = 3
    professional_army = 1
    defense_lobby     = 3
    interventionism   = 1
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12262 id = 1 }
    location = 1092
    name     = "1st Corps"
    division =
    { id            = { type = 12262 id = 2 }
      name          = "1st Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
  }
}
