
##############################
# Country definition for SIE #
##############################

country =
{ tag                 = SIE
  # Resource Reserves
  energy              = 400
  metal               = 200
  rare_materials      = 200
  oil                 = 200
  supplies            = 400
  money               = 10
  manpower            = 20
  capital             = 988
  diplomacy           = { }
  nationalprovinces   = { 988
                        }
  ownedprovinces      = { 988
                        }
  controlledprovinces = { 988
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
    democratic        = 7
    political_left    = 5
    free_market       = 5
    freedom           = 3
    professional_army = 1
    defense_lobby     = 2
    interventionism   = 4
  }
}
