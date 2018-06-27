##############################
# Country definition for COS #
##############################

country =
{ tag                 = COS
  manpower            = 0
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 25
  capital             = 540
  transports          = 10
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 540 }
  ownedprovinces      = { 540 }
  controlledprovinces = { 540 }
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
                                        2200 2210
                                        2500
                                        2600
                                        2700
                                        2800 2810
                                        #Army Org:
                                        1900 1910
                                        1980
                                        #Army Doc:
                                        6100
                                        6110
                                        6160
                                        6010
                                        6020
                                        6600
                                        6610
                                        6910 6920 6930
                        }
policy = {
        date = { year = 0 month = march day = 0 }
        democratic = 10
        political_left = 5
        free_market = 7
        freedom = 9
        professional_army = 1
        defense_lobby = 1
        interventionism = 3
    }
}