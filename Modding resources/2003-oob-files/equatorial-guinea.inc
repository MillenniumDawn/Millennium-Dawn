
##############################
# Country definition for EQA #
##############################

country =
{ tag                 = EQA
  # Resource Reserves
  energy              = 800
  metal               = 400
  rare_materials      = 200
  oil                 = 2000
  supplies            = 400
  money               = 300
  manpower            = 3
  transports          = 25
  escorts             = 0
  capital             = 1090
  diplomacy           = { }
  nationalprovinces   = { 1091 1090
                        }
  ownedprovinces      = { 1091 1090
                        }
  controlledprovinces = { 1091 1090
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
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 4
    political_left    = 5
    free_market       = 5
    freedom           = 3
    professional_army = 1
    defense_lobby     = 1
    interventionism   = 4
  }
}
