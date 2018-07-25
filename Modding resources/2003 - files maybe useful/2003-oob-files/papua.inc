
##############################
# Country definition for PRK #
##############################


province =
{ id       = 1679
  naval_base = { size = 2 current_size = 2 }
}            # Port Moresby

country =
{ tag                 = PRK
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 19
  capital             = 1679
  transports          = 20
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 1666 1667 1668 1669 1670 1671 1672 1675 1676 1677 1678 1679 1680 1682 }
  ownedprovinces      = { 1666 1667 1668 1669 1670 1671 1672 1675 1676 1677 1678 1679 1680 1682 }
  controlledprovinces = { 1666 1667 1668 1669 1670 1671 1672 1675 1676 1677 1678 1679 1680 1682 }
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
    democratic        = 10
    political_left    = 8
    free_market       = 6
    freedom           = 6
    professional_army = 9
    defense_lobby     = 1
    interventionism   = 3
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12228 id = 1 }
    location = 1679
    name     = "Papua Defence Force"
    division =
    { id            = { type = 12228 id = 2 }
      name          = "1st Pacific Islands Regiment"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
  }
}
