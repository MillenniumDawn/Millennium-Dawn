
##############################
# Country definition for U12 #
##############################

country =
{ tag                 = U12
  # Resource Reserves
  energy              = 1200
  metal               = 200
  rare_materials      = 200
  oil                 = 200
  supplies            = 200
  money               = 10
  manpower            = 30
  capital             = 993
  diplomacy           = { }
  nationalprovinces   = { 995 993
                        }
  ownedprovinces      = { 995 993
                        }
  controlledprovinces = { 995 993
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
					#Army Org
                                        1000
                                        1010
                                        1500
                                        1300
					1260
					1980
					1900
                                             1700
					#Air Docs
                                        9050
                                        9060
                                        9070
                                        9010
                                        9510
					#Air techs
                                        4700
                                        4750
                                        4640
                                        4570
					#Secret Techs
                                        7330
					#Land Docs
					6910
					6010 6020
					6600 6610
					6100 6110 6120 6160 6170
                        }
  policy =
  { date              = { year = 0 month = march day = 0 }
    democratic        = 5
    political_left    = 5
    free_market       = 6
    freedom           = 3
    professional_army = 1
    defense_lobby     = 3
    interventionism   = 1
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 12206 id = 1 }
    location = 993
    name     = "1st Ivoiran Army"
    division =
    { id            = { type = 12206 id = 2 }
      name          = "1st Airborne Cavalry Brigade"
      strength      = 100
      type          = militia
      model         = 1
    }
    division =
    { id            = { type = 12206 id = 3 }
      name          = "1st Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
    division =
    { id            = { type = 12206 id = 4 }
      name          = "2nd Brigade"
      strength      = 100
      type          = mechanized
      model         = 0
    }
  }
}