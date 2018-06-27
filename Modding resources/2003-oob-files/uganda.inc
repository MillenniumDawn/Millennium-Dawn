
##############################
# Country definition for U18 #
##############################

province =
{ id       = 1064
  air_base = { size = 1 current_size = 1 }
}            # Kampala

country =
{ tag                 = U18
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 700
  supplies            = 5000
  money               = 10
  manpower            = 40
  capital             = 1064
  diplomacy           = { }
  nationalprovinces   = { 1064
                        }
  ownedprovinces      = { 1064
                        }
  controlledprovinces = { 1064 1072 1071
                        }
  techapps            = {
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 4
    political_left    = 7
    free_market       = 6
    freedom           = 3
    professional_army = 8
    defense_lobby     = 4
    interventionism   = 9
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12240 id = 1 }
    location = 1064
    name     = "The Ugandan People's Defense Force"
    division =
    { id            = { type = 12240 id = 2 }
      name          = "3rd Tank Brigade"
      strength      = 100
      type          = light_armor
      model         = 0
    }
    division =
    { id            = { type = 12240 id = 3 }
      name          = "1st Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12240 id = 4 }
      name          = "3rd Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12240 id = 5 }
      name          = "4th Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12240 id = 6 }
      name          = "5th Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 12240 id = 7 }
    location = 1071
    name     = "2nd Divisional Command"
    division =
    { id            = { type = 12240 id = 8 }
      name          = "17th Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12240 id = 9 }
      name          = "Rwenzori Mountain Alpine Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
    division =
    { id            = { type = 12240 id = 10 }
      name          = "Mbarara Mountain Alpine Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
  }
  # #####################################
  # AIR FORCE
  # #####################################
  airunit =
  { id       = { type = 12240 id = 100 }
    location = 1064
    base     = 1064
    name     = "1st Air Wing"
    division =
    { id       = { type = 12240 id = 101 }
      name     = "1st Squadron"
      type     = interceptor
      strength = 60
      model    = 1
    }
  }
}