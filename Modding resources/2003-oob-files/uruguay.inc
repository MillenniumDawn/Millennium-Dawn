
##############################
# Country definition for URU #
##############################

province =
{ id       = 849
  naval_base = { size = 2 current_size = 2 }
    air_base = { size = 2 current_size = 2 }
}            # Montevideo

country =
{ tag                 = URU
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  capital             = 849
  manpower            = 12
  transports          = 11
  escorts             = 0
  diplomacy           = { }
  nationalprovinces   = { 849 }
  ownedprovinces      = { 849 }
  controlledprovinces = { 849 }
  techapps            = {
                                        #Navy Techs
                                        3000
                                        3590
                                        3850 3860
                                        #Navy Doctrines
                                        8900 8910
                                        8950 8960
                                        8000 8010
                                        8500 8510
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 10
    political_left    = 6
    free_market       = 7
    freedom           = 9
    professional_army = 4
    defense_lobby     = 2
    interventionism   = 6
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 22500 id = 1 }
    location = 849
    name     = "I Corps"
    division =
    { id            = { type = 22500 id = 2 }
      name          = "1st Division"
      strength      = 100
      type          = infantry
      model         = 0
    }
    division =
    { id            = { type = 22500 id = 3 }
      name          = "2nd Division"
      strength      = 100
      type          = garrison
      model         = 0
    }
    division =
    { id            = { type = 22500 id = 4 }
      name          = "3rd Division"
      strength      = 100
      type          = garrison
      model         = 0
    }
    division =
    { id            = { type = 22500 id = 5 }
      name          = "4th Division"
      strength      = 100
      type          = garrison
      model         = 0
    }
  }
  # ###################################
  # NAVY
  # ###################################
  navalunit =
  { id       = { type = 22500 id = 300 }
    location = 849
    base     = 849
    name     = "Navy of Uruguay"
    division =
    { id    = { type = 22500 id = 301 }
      name  = "ROU Uruguay"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 22500 id = 302 }
      name  = "ROU General Artigas"
      type  = destroyer
      model = 0
    }
    division =
    { id    = { type = 22500 id = 303 }
      name  = "ROU Montevideo"
      type  = destroyer
      model = 0
    }
  }
  # ####################################
  # AIR FORCE
  # ####################################
  airunit =
  { id       = { type = 22500 id = 100 }
    location = 849
    base     = 849
    name     = "National Airforce"
    division =
    { id       = { type = 22500 id = 101 }
      name     = "1st Squadron"
      type     = cas
      strength = 50
      model    = 3
    }
  }
}
