
##############################
# Country definition for RSI #
##############################

country =
{ tag                 = RSI
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 700
  supplies            = 5000
  money               = 50
  manpower            = 20
  capital             = 1063
  diplomacy           = { }
  nationalprovinces   = { 1063 1073
                        }
  ownedprovinces      = { 1063
                        }
  controlledprovinces = { 1063 1073 1144 1127
                        }
  techapps            = {
					#Industry
					5010 5020 5030 5040 5050 5060 5070 5080 5090
                                        #Army Equip:
                                        2000
                                        2010
                                        2300
                                        2400
                                        2200 2210
                                        2500
                                        2600
                                        2700
                                        2800 2810
                                        #Land Docs
					6010 6020 
					6910
					6100 6110 6120
                                        6160
					6600 6610
					#Army Org
                                        1000
                                        1010
                                        1500
                                        1300
					1260
					1980
					1900
                                        #Secret Tech:
                                        7330
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 4
    political_left    = 5
    free_market       = 5
    freedom           = 3
    professional_army = 8
    defense_lobby     = 5
    interventionism   = 9
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12242 id = 1 }
    location = 1073
    name     = "Specialised Units Command"
    division =
    { id            = { type = 12242 id = 2 }
      name          = "1st Spec. Ops. Brigade"
      strength      = 100
      type          = bergsjaeger
      model         = 11
    }
  }
  landunit =
  { id       = { type = 12242 id = 3 }
    location = 1073
    name     = "Cyangungu Military Camp"
    division =
    { id            = { type = 12242 id = 4 }
      name          = "17th Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12242 id = 5 }
      name          = "9th Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 12242 id = 6 }
    location = 1127
    name     = "Rally for Congolese Democracy"
    division =
    { id            = { type = 12242 id = 7 }
      name          = "1st RCD Brigade"
      strength      = 100
      type          = garrison
      model         = 7
    }
    division =
    { id            = { type = 12242 id = 8 }
      name          = "2nd RCD Brigade"
      strength      = 100
      type          = garrison
      model         = 7
    }
  }
  landunit =
  { id       = { type = 12242 id = 9 }
    location = 1144
    name     = "1st Rwandan Army"
    division =
    { id            = { type = 12242 id = 10 }
      name          = "4th Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12242 id = 11 }
      name          = "5th Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
  landunit =
  { id       = { type = 12242 id = 12 }
    location = 1063
    name     = "2nd Rwandan Army"
    division =
    { id            = { type = 12242 id = 13 }
      name          = "2nd Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
    division =
    { id            = { type = 12242 id = 14 }
      name          = "8th Division"
      strength      = 100
      type          = motorized
      model         = 0
    }
  }
}
