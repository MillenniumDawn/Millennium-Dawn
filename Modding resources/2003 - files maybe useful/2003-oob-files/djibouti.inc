
##############################
# Country definition for DDR #
##############################

province =
{ id         = 1037
  naval_base = { size = 2 current_size = 2 }
}              # Djibouti

country =
{ tag                 = DDR
  puppet              = FRA
  control             = FRA
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 5
  capital             = 1037
  diplomacy           = { }

  nationalprovinces   = { 1037
                        }
  ownedprovinces      = { 1037
                        }
  controlledprovinces = { 1037
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
    democratic        = 6
    political_left    = 5
    free_market       = 5
    freedom           = 4
    professional_army = 3
    defense_lobby     = 5
    interventionism   = 1
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12257 id = 1 }
    location = 1037
    name     = "1st Corps"
    division =
    { id            = { type = 12257 id = 2 }
      name          = "1st Infantry Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
  }
}
