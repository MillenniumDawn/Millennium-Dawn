
##############################
# Country definition for GLD #
##############################

country =
{ tag                 = GLD
  # Resource Reserves
  energy              = 1200
  metal               = 300
  rare_materials      = 300
  oil                 = 300
  supplies            = 500
  money               = 30
  manpower            = 34
  capital             = 1002
  diplomacy           = { }
  nationalprovinces   = { 1002 1001 1000
                        }
  ownedprovinces      = { 1002 1001 1000
                        }
  controlledprovinces = { 1002 1001 1000
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
    democratic        = 8
    political_left    = 5
    free_market       = 7
    freedom           = 3
    professional_army = 1
    defense_lobby     = 2
    interventionism   = 4
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12258 id = 1 }
    location = 1002
    name     = "1st Corps"
    division =
    { id            = { type = 12258 id = 2 }
      name          = "1st Brigade"
      strength      = 100
      type          = mechanized
      model         = 1
    }
  }
}