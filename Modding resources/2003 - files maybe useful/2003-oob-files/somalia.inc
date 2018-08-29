
##############################
# Country definition for SOM #
##############################

province =
{ id       = 1056
  naval_base = { size = 2 current_size = 2 }
    air_base = { size = 2 current_size = 2 }
}            # Mogadishu

country =
{ tag                 = SOM
  dissent             = 30
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  capital             = 1056
  manpower            = 60
  transports          = 64
  escorts             = 0
  diplomacy           = { 
relation = { tag = YEM value = -100 }
relation = { tag = EAF value = -150 }
relation = { tag = ETH value = -10 }
}
  nationalprovinces   = { 1034 1035 1036 1056 1055 1058 1054 }
  ownedprovinces      = { 1034 1056 1055 1058 }
  controlledprovinces = { 1034 1056 1055 1058 }
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
    freedom           = 1
    professional_army = 3
    defense_lobby     = 6
    interventionism   = 8
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12217 id = 1 }
    location = 1056
    name     = "I. Corps al-Somaliya"
    division =
    { id            = { type = 12217 id = 2 }
      name          = "1st Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12217 id = 3 }
      name          = "2nd Infantry Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
}