
##############################
# Country definition for TEX #
##############################

province =
{ id       = 1658
  naval_base = { size = 1 current_size = 1 }
}            # East Timor

country =
{ tag                 = TEX
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 1
  capital             = 1658
  diplomacy           = { }
  nationalprovinces   = { 1658 }
  ownedprovinces      = { 1658 }
  controlledprovinces = { 1658 }
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
    political_left    = 8
    free_market       = 5
    freedom           = 6
    professional_army = 9
    defense_lobby     = 3
    interventionism   = 5
  }
}
