
##############################
# Country definition for SCO #
##############################

province =
{ id       = 897
  naval_base = { size = 2 current_size = 2 }
}            # Antigua

country =
{ tag                 = SCO
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  manpower            = 10
  capital             = 897
  transports          = 59
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 897 807 806 805 }
  ownedprovinces      = { 897 807 806 805 }
  controlledprovinces = { 897 807 806 805 }
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
    political_left    = 3
    free_market       = 7
    freedom           = 8
    professional_army = 10
    defense_lobby     = 1
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 11900 id = 1 }
    location = 897
    name     = "I Corps"
    division =
    { id       = { type = 11900 id = 2 }
      name     = "1st Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  landunit =
  { id       = { type = 11900 id = 3 }
    location = 897
    name     = "II Corps"
    division =
    { id       = { type = 11900 id = 4 }
      name     = "2nd Infantry Division"
      strength = 100
      type     = motorized
      model    = 0
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 11900 id = 100 }
    location = 897
    base     = 897
    name     = "Caribbean Navy"
    division =
    { id    = { type = 11900 id = 101 }
      name  = "Almirante Juan Alejandro Acosta"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 11900 id = 102 }
      name  = "Separacion"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 11900 id = 103 }
      name  = "Calderas"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 11900 id = 104 }
      name  = "Prestol Botello"
      type  = destroyer
      model = 0
    }
  }
}
