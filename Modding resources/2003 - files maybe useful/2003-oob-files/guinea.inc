
##############################
# Country definition for GUI #
##############################

country =
{ tag                 = GUI
  # Resource Reserves
  energy              = 400
  metal               = 200
  rare_materials      = 200
  oil                 = 200
  supplies            = 400
  money               = 10
  manpower            = 30
  capital             = 987
  diplomacy           = { }
  nationalprovinces   = { 991 990 989 987 983
                        }
  ownedprovinces      = { 991 990 989 987 983
                        }
  controlledprovinces = { 991 990 989 987 983
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
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 5
    political_left    = 5
    free_market       = 6
    freedom           = 3
    professional_army = 1
    defense_lobby     = 4
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12203 id = 1 }
    location = 987
    name     = "1st Army"
    division =
    { id            = { type = 12203 id = 2 }
      name          = "4th Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12203 id = 3 }
      name          = "3rd Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12203 id = 4 }
      name          = "1st Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
  }
}
