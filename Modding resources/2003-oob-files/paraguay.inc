
##############################
# Country definition for PAR #
##############################

country =
{ tag                 = PAR
  # Resource Reserves
  energy              = 1000
  metal               = 1000
  rare_materials      = 500
  oil                 = 500
  supplies            = 500
  money               = 10
  capital             = 837
  manpower            = 11
  diplomacy           = { }
  nationalprovinces   = { 837 846 }
  ownedprovinces      = { 837 846 }
  controlledprovinces = { 837 846 }
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
					1960
					1900
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
    democratic        = 9
    political_left    = 5
    free_market       = 6
    freedom           = 6
    professional_army = 2
    defense_lobby     = 2
    interventionism   = 5
  }
  # #####################################
  # ARMY
  # #####################################
  landunit =
  { id       = { type = 17900 id = 1 }
    location = 837
    name     = "I Corps"
    division =
    { id            = { type = 17900 id = 2 }
      name          = "1st Mechanized Brigade"
      strength      = 100
      type          = cavalry
      model         = 0
    }
  }
  landunit =
  { id       = { type = 17900 id = 3 }
    location = 846
    name     = "II Corps"
    division =
    { id            = { type = 17900 id = 4 }
      name          = "1st Garrison"
      strength      = 100
      type          = garrison
      model         = 7
    }
  }
}
